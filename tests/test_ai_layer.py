import json
import re

import pandas as pd
import pytest

from src.vireo import config as C
from src.vireo import reasons as R
from src.vireo.config import RAW_DIR
from src.vireo.load import load_csv

USAGE = {"prompt_tokens": 1000, "output_tokens": 20, "thinking_tokens": 30, "total_tokens": 1050}


def message_of(prompt):
    return prompt.split("CUSTOMER MESSAGE\n", 1)[1].split("\n\nAGENT NOTES", 1)[0]


def stub(label="PAYMENT_ISSUE", replacement="no", certainty="high", evidence=None):
    def provider(prompt):
        quote = " ".join(message_of(prompt).split()[:5]) if evidence is None else evidence
        return json.dumps({"reason": label, "replacement_sent": replacement, "evidence": quote, "certainty": certainty}), USAGE
    return provider


def refuse(prompt):
    raise AssertionError("the provider must not be called")


@pytest.fixture
def sample(fin):
    return fin.ledger.groupby("refund_reason_code").head(3)[R.TEXT_COLUMNS].reset_index(drop=True)


def test_ai_input_has_no_money_or_people_columns():
    assert R.TEXT_COLUMNS == ["canonical_id", "customer_message", "agent_notes", "refund_reason_code", "replacement_issued"]


def test_scrub_removes_amounts_ids_and_sign_offs_but_keeps_the_rest():
    assert R.scrub("Refund of Rs 4999 initiated to source. -KS", notes=True) == "Refund of [AMOUNT] initiated to source."
    assert R.scrub("Order VR891120 is late") == "Order [ORDER] is late"
    assert R.scrub("refunded. ~Manish", notes=True) == "refunded."
    kept = R.scrub("Refund approved, Rs 900, 5-7 working days. -- replacement was offered earlier by chat team. -RM", notes=True)
    assert "5-7 working days" in kept and "-- replacement was offered earlier" in kept and not kept.endswith("-RM")


@pytest.mark.parametrize("message, expected", [
    ("pickup not done. thanks in advance, Om Misshra", "pickup not done."),
    ("money not back.\n\nThanks & regards\nNisha Rao\nBengaluru", "money not back."),
    ("still waiting. Thnaks Manish", "still waiting."),
    ("no one came. yors faithfully, zaiid saxena", "no one came. yors"),
    ("nothing changed. please revert, lobsang arora", "nothing changed. please"),
    ("refund was slower than promised and nothing came", "refund was slower than promised and nothing came"),
])
def test_sign_off_names_are_cut_even_with_typos(message, expected):
    assert R.scrub(message) == expected


def test_no_customer_name_reaches_the_model(fin):
    names = load_csv(RAW_DIR / "customers.csv").set_index("customer_id")["name"]
    leaks = []
    for t in fin.ledger.itertuples():
        tokens = [x.lower() for x in re.findall(r"[A-Za-z']+", names.get(t.customer_id, "")) if len(x) >= 3]
        text = f"{R.scrub(t.customer_message)} {R.scrub(t.agent_notes, notes=True)}".lower()
        if any(re.search(rf"\b{re.escape(x)}\b", text) for x in tokens):
            leaks.append(t.canonical_id)
    assert not leaks, leaks[:5]


def test_no_amount_or_order_id_reaches_the_model(fin):
    for t in fin.ledger[R.TEXT_COLUMNS].itertuples(index=False):
        for text in (R.scrub(t.customer_message), R.scrub(t.agent_notes, notes=True)):
            assert not re.search(r"(?i)\brs\.?\s*\d", text), text
            assert not re.search(r"\(\s*\d{2,6}\s*\)", text), text
            assert not re.search(r"(?i)\bVR\d{6}\b", text), text


def test_prompt_carries_the_taxonomy_and_no_ticket_ids():
    _, template, prompt_hash = R.load_prompt("reason_v1")
    assert re.fullmatch(r"[0-9a-f]{64}", prompt_hash)
    for label in C.LABELS + [C.UNCERTAIN]:
        assert f"## {label}" in template
    assert "Example:" not in template and not re.search(r"TK-\d{6}", template)


@pytest.mark.parametrize("notes, expected", [
    ("fresh unit shipped from blr warehouse", "yes"),
    ("refund + rplc, cx escalation avoided", "yes"),
    ("Replacement approved, reverse pickup arranged.", "yes"),
    ("Replacement was offered earlier by chat team, cx opted for refund.", "no"),
    ("Refunded. Replacement request rejected as per policy.", "no"),
    ("rplc raised. Cx declined replacement later.", "no"),
    ("cancelled before dispatch", "no"),
    ("checked replacement eligibility with warehouse", "unclear"),
])
def test_replacement_rules_baseline(notes, expected):
    assert R.rules_replacement(notes) == expected


def test_reason_rules_follow_the_code_map():
    assert R.rules_reason("DUP-PAYMENT") == "PAYMENT_ISSUE"
    assert R.rules_reason("GW-OTHER") == "OTHER_UNCLEAR"


def test_cache_mode_without_a_cache_falls_back_without_network(sample, tmp_path, no_network):
    classes, stats = R.classify_tickets(sample, mode="cache", provider=refuse, cache_path=tmp_path / "none.jsonl")
    assert set(classes["source"]) == {"rules_fallback"}
    assert stats["cache_misses"] == len(sample) and stats["calls_made"] == 0
    assert "WARNING" in R.summary_line(stats)


def test_live_run_fills_the_cache_and_cache_mode_replays_it(sample, tmp_path, no_network):
    cache = tmp_path / "llm_cache.jsonl"
    classes, stats = R.classify_tickets(sample, mode="live", provider=stub(), cache_path=cache)
    assert set(classes["source"]) == {"llm"} and stats["calls_made"] == len(sample)
    again, replay = R.classify_tickets(sample, mode="cache", provider=refuse, cache_path=cache)
    assert replay["cache_hits"] == len(sample) and replay["cache_misses"] == 0
    assert again[["label", "replacement_sent", "evidence"]].equals(classes[["label", "replacement_sent", "evidence"]])
    _, rerun = R.classify_tickets(sample, mode="live", provider=refuse, cache_path=cache)
    assert rerun["calls_made"] == 0


def test_unparseable_cache_entries_are_retried_not_trusted(sample, tmp_path):
    cache = tmp_path / "llm_cache.jsonl"
    bad, _ = R.classify_tickets(sample, mode="live", provider=lambda p: ("not json", USAGE), cache_path=cache)
    assert set(bad["source"]) == {"rules_fallback"}
    assert R.load_cache(cache) == {}
    good, stats = R.classify_tickets(sample, mode="live", provider=stub(), cache_path=cache)
    assert set(good["source"]) == {"llm"} and stats["calls_made"] == len(sample)


def test_evidence_must_appear_in_the_ticket(sample, tmp_path):
    bad, _ = R.classify_tickets(sample, mode="live", provider=stub(evidence="a sentence the ticket never contained"), cache_path=tmp_path / "a.jsonl")
    ok, _ = R.classify_tickets(sample, mode="live", provider=stub(), cache_path=tmp_path / "b.jsonl")
    assert not bad["evidence_verified"].any() and ok["evidence_verified"].all()


def test_rejected_calls_stop_the_run_and_leave_a_clean_cache(sample, tmp_path):
    def rejected(prompt):
        raise R.FatalProviderError("403 PERMISSION_DENIED")

    cache = tmp_path / "c.jsonl"
    with pytest.raises(SystemExit, match="AI call rejected"):
        R.classify_tickets(sample, mode="live", provider=rejected, cache_path=cache)
    assert not cache.exists() or cache.read_text() == ""


def test_live_without_a_key_stops_before_any_call(sample, tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)
    with pytest.raises(SystemExit, match="GROQ_API_KEY"):
        R.classify_tickets(sample, mode="live", cache_path=tmp_path / "c.jsonl")
