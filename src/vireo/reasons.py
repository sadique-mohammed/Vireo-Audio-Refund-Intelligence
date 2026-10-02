import difflib
import hashlib
import json
import os
import random
import re
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ValidationError

from src.vireo import config as C

TEXT_COLUMNS = ["canonical_id", "customer_message", "agent_notes", "refund_reason_code", "replacement_issued"]
OTHER = "OTHER_UNCLEAR"


class ModelOutput(BaseModel):
    reason: Literal[tuple(C.LABELS) + (C.UNCERTAIN,)]
    replacement_sent: Literal["yes", "no", "unclear"]
    evidence: str
    certainty: Literal["high", "medium", "low"]


class FatalProviderError(Exception):
    pass


class ProviderUnavailable(Exception):
    pass


_AMOUNT = re.compile(r"(?i)(?:\brs\.?|\binr\b|\u20b9)\s*\d+(?:,\d{2,3})*(?:\.\d+)?|\(\s*\d{2,6}\s*\)")
_ORDER_ID = re.compile(r"(?i)\bVR\d{6}\b")
_CUSTOMER_ID = re.compile(r"\bC\d{6}\b")
_SIGN_OFF = re.compile(r"(?:^|\s)(?:~|//|--?)[A-Za-z]{2,12}\s*$")
_CLOSERS = ("thanks", "regards", "rgds", "sincerely", "faithfully", "revert", "cheers", "thx", "response")


def _is_closer(word):
    word = re.sub(r"[^a-z]", "", word.lower())
    return len(word) >= 3 and word != "than" and bool(difflib.get_close_matches(word, _CLOSERS, n=1, cutoff=0.82))


def strip_sign_off(message):
    """Cut a customer message at its closing phrase (thanks, regards, please revert...) so the name after it never leaves the machine. Typos are tolerated."""
    words = list(re.finditer(r"\S+", message))
    for match in words[-6:]:
        if _is_closer(match.group()):
            return message[: match.start()].rstrip(" ,\n")
    return message


def scrub(text, notes=False):
    text = _AMOUNT.sub("[AMOUNT]", text)
    text = _ORDER_ID.sub("[ORDER]", text)
    text = _CUSTOMER_ID.sub("[CUSTOMER]", text)
    text = _SIGN_OFF.sub("", text) if notes else strip_sign_off(text)
    return text.strip()


_REPLACEMENT_TERM = re.compile(r"(?i)replac|\brplc\b|\brepl\b|\b(?:new|fresh)\s+(?:unit|set|pair|piece|one|buds)\b|\bre-?ship(?:ped)?\b|\brma for new\b")
_SENT_TERM = re.compile(r"(?i)ship|dispatch|\bsent\b|sending|raised|approved|issued|given|going out|arranged|\balso\b|\bboth\b|\+|\bas well\b|under rma|one-time")
_NEGATION = re.compile(r"(?i)reject|declin|not (?:applicable|required|needed|eligible)|out of stock|did not want|opted for (?:refund|rfnd)|preferred (?:refund|rfnd)|(?:refund|rfnd) only|explained policy")
_CLAUSE_SPLIT = re.compile(r"[.;|\n]+|\s--\s|->")


def rules_replacement(notes):
    clauses = [c for c in _CLAUSE_SPLIT.split(notes) if _REPLACEMENT_TERM.search(c)]
    if not clauses:
        return "no"
    if any(_NEGATION.search(c) for c in clauses):
        return "no"
    if any(_SENT_TERM.search(c) for c in clauses):
        return "yes"
    return "unclear"


def rules_reason(code):
    return C.CODE_MAP.get(code, OTHER)


def load_prompt(version=None):
    version = version or C.PROMPT_VERSION
    template = (C.PROMPTS_DIR / f"{version}.txt").read_text(encoding="utf-8")
    taxonomy = re.sub(r"(?m)^Example:.*\n?", "", C.TAXONOMY_PATH.read_text(encoding="utf-8")).strip()
    template = template.replace("[[TAXONOMY]]", taxonomy)
    return version, template, hashlib.sha256(template.encode("utf-8")).hexdigest()


def render(template, code, message, notes):
    return template.replace("[[ORIGINAL_CODE]]", code).replace("[[CUSTOMER_MESSAGE]]", message).replace("[[AGENT_NOTES]]", notes)


def active_model_id():
    """Return a human-readable model identifier for the active provider."""
    return f"groq/{C.GROQ_MODEL}"


def model_tag():
    """Return a cache-tag that uniquely identifies the provider+model+settings."""
    return f"groq/{C.GROQ_MODEL}|thinking={C.THINKING_LEVEL}"


def cache_key(tag, prompt_hash, code, message, notes):
    payload = json.dumps([tag, prompt_hash, code, message, notes], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_cache(path):
    entries = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if parse_output(entry.get("text", "")) is None:
                continue
            entries[entry["key"]] = entry
    return entries


def parse_output(text):
    try:
        return ModelOutput.model_validate_json(text)
    except (ValidationError, ValueError, TypeError):
        return None


def _normal(text):
    return " ".join(text.lower().split())


def evidence_verified(evidence, message, notes, label):
    if not evidence.strip():
        return label == C.UNCERTAIN
    return _normal(evidence) in _normal(f"{message} {notes}")


_JSON_SCHEMA_INSTRUCTION = """

Respond with ONLY a JSON object matching this exact schema:
{"reason": "<one label from the taxonomy>", "replacement_sent": "yes|no|unclear", "evidence": "<short quote from ticket>", "certainty": "high|medium|low"}

Valid reason labels: """ + ", ".join(C.LABELS + [C.UNCERTAIN]) + """
Do NOT wrap the JSON in markdown code fences. Output raw JSON only."""


def require_groq_key():
    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("GROQ_API_KEY"):
        raise SystemExit("VIREO_PROVIDER=groq needs GROQ_API_KEY in the environment or in a .env file")


def groq_provider(prompt):
    """Call the Groq API (OpenAI-compatible) via urllib."""
    api_key = os.environ["GROQ_API_KEY"]
    payload = json.dumps({
        "model": C.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a classification engine. Respond with JSON only."},
            {"role": "user", "content": prompt + _JSON_SCHEMA_INSTRUCTION},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": C.MAX_OUTPUT_TOKENS,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "curl/7.68.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        code = exc.code
        if code in (400, 401, 403, 404):
            raise FatalProviderError(f"Groq {code}: {exc.read().decode()}") from exc
        raise
    text = body["choices"][0]["message"]["content"]
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    u = body.get("usage", {})
    usage = {
        "prompt_tokens": u.get("prompt_tokens", 0),
        "output_tokens": u.get("completion_tokens", 0),
        "thinking_tokens": 0,
        "total_tokens": u.get("total_tokens", 0),
    }
    return text, usage


def call_with_backoff(provider, prompt):
    last = None
    delays = (0,) + tuple(C.RETRY_DELAYS)
    for attempt, delay in enumerate(delays, 1):
        if delay:
            # honour Retry-After header from 429 responses when available
            retry_after = getattr(last, 'retry_after', None)
            if retry_after:
                wait = float(retry_after) + random.uniform(0, C.RETRY_MAX_JITTER)
            else:
                jitter = random.uniform(0, C.RETRY_MAX_JITTER)
                wait = delay + jitter
            err_code = getattr(last, 'code', '') or type(last).__name__
            print(f"  retry {attempt}/{len(delays)} in {wait:.1f}s (HTTP {err_code})", file=sys.stderr, flush=True)
            time.sleep(wait)
        try:
            return provider(prompt)
        except FatalProviderError:
            raise
        except urllib.error.HTTPError as exc:
            exc.retry_after = exc.headers.get('Retry-After')
            last = exc
        except Exception as exc:
            last = exc
    raise ProviderUnavailable(str(last))


def fetch(jobs, provider, cache, cache_path, workers):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    failed = 0
    total = len(jobs)
    print(f"  fetch: {total} calls with {workers} worker(s)", file=sys.stderr, flush=True)
    with open(cache_path, "a", encoding="utf-8") as sink, ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        # Groq handles bursts but may 429 if TPM is exceeded (handled by backoff).
        inter_call_delay = 0.3
        for i, (key, prompt) in enumerate(jobs.items()):
            futures[pool.submit(call_with_backoff, provider, prompt)] = key
            # stagger submissions slightly to avoid burst-firing into rate limits instantly
            if i < total - 1 and workers > 1:
                time.sleep(inter_call_delay)
        for done, future in enumerate(as_completed(futures), 1):
            try:
                text, usage = future.result()
            except ProviderUnavailable:
                failed += 1
                print(f"  [{done}/{total}] FAILED (exhausted retries)", file=sys.stderr, flush=True)
                continue
            except FatalProviderError as exc:
                for pending in futures:
                    pending.cancel()
                raise SystemExit(f"AI call rejected, run stopped: {exc}") from exc
            entry = {"key": futures[future], "model_id": active_model_id(), "thinking_level": C.THINKING_LEVEL, "text": text, "usage": usage}
            cache[entry["key"]] = entry
            sink.write(json.dumps(entry, ensure_ascii=False) + "\n")
            sink.flush()
            print(f"  [{done}/{total}] ok", file=sys.stderr, flush=True)
    return failed


def classify_tickets(tickets, mode="cache", provider=None, cache_path=C.CACHE_PATH, workers=C.WORKERS):
    version, template, prompt_hash = load_prompt()
    tag = model_tag()
    cache = {} if mode == "rules" else load_cache(cache_path)
    keys, jobs = [], {}
    for t in tickets[TEXT_COLUMNS].itertuples(index=False):
        message, notes = scrub(t.customer_message), scrub(t.agent_notes, notes=True)
        key = cache_key(tag, prompt_hash, t.refund_reason_code, message, notes)
        keys.append((key, message, notes))
        if mode != "rules" and key not in cache and key not in jobs:
            jobs[key] = render(template, t.refund_reason_code, message, notes)
    hits_before = sum(1 for key, _, _ in keys if key in cache)
    failed = 0
    if mode == "live" and jobs:
        if provider is None:
            require_groq_key()
            provider = groq_provider
            print(f"  provider: {active_model_id()}", file=sys.stderr, flush=True)
        failed = fetch(jobs, provider, cache, cache_path, workers)

    rows, used = [], {}
    for t, (key, message, notes) in zip(tickets[TEXT_COLUMNS].itertuples(index=False), keys):
        entry = cache.get(key)
        parsed = parse_output(entry["text"]) if entry else None
        code_label = C.CODE_MAP.get(t.refund_reason_code)
        if entry:
            used[key] = entry["usage"]
        if parsed:
            label, replacement, evidence, certainty = parsed.reason, parsed.replacement_sent, parsed.evidence, parsed.certainty
            verified = evidence_verified(evidence, message, notes, label)
            source = "llm"
        else:
            label, replacement, evidence, certainty, verified = rules_reason(t.refund_reason_code), rules_replacement(t.agent_notes), "", "", False
            source = "rules" if mode == "rules" else "rules_fallback"
        rows.append({
            "ticket_id": t.canonical_id,
            "source": source,
            "label": label,
            "replacement_sent": replacement,
            "certainty": certainty,
            "evidence": evidence,
            "evidence_verified": verified,
            "code_label": code_label or "",
            "rules_label": rules_reason(t.refund_reason_code),
            "rules_replacement": rules_replacement(t.agent_notes),
            "replacement_flag": t.replacement_issued,
            "model_id": active_model_id() if source == "llm" else "",
            "prompt_version": version if source == "llm" else "",
            "prompt_hash": prompt_hash if source == "llm" else "",
        })
    classes = pd.DataFrame(rows)
    stats = {
        "mode": mode,
        "provider": C.PROVIDER,
        "model_id": active_model_id(),
        "thinking_level": C.THINKING_LEVEL,
        "prompt_version": version,
        "prompt_hash": prompt_hash,
        "tickets": len(classes),
        "cache_hits": hits_before,
        "cache_misses": len(classes) - hits_before,
        "calls_made": len(jobs) - failed if mode == "live" else 0,
        "calls_failed": failed,
        "source_counts": classes["source"].value_counts().to_dict(),
        "usage_calls": len(used),
        "prompt_tokens": sum(u["prompt_tokens"] for u in used.values()),
        "output_tokens": sum(u["output_tokens"] for u in used.values()),
        "thinking_tokens": sum(u["thinking_tokens"] for u in used.values()),
        "total_tokens": sum(u["total_tokens"] for u in used.values()),
    }
    return classes, stats


def summary_line(stats):
    counts = ", ".join(f"{k}={v}" for k, v in sorted(stats["source_counts"].items()))
    if stats["mode"] == "rules":
        return f"AI: mode=rules (no model used) sources[{counts}]"
    line = f"AI: mode={stats['mode']} model={stats['model_id']} prompt={stats['prompt_version']} cache_hits={stats['cache_hits']} cache_misses={stats['cache_misses']} sources[{counts}]"
    fallback = stats["source_counts"].get("rules_fallback", 0)
    if fallback:
        line += f" WARNING: {fallback} tickets have no model answer and use the rules baseline; run `make run-live` with a key to fill the cache"
    return line
