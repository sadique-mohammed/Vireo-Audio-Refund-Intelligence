# Vireo Audio Refund Intelligence

AI reads the ticket text. Code decides the money.

Finance and the helpdesk quote very different refund totals. This repo builds one reconciled refund ledger from `data/raw/`, bridges both quoted figures to it, and adds an AI reading of each refund ticket (why it was raised, and whether a replacement also went out). The ledger is built before the AI runs and is byte-identical with or without it.

**Current estimated refund + replacement rate: 15.6%. The proposed goal is to reduce this toward <1%, with an estimated replacement-cost opportunity of ₹65k–₹133k per quarter. These figures are estimates and need validation.**

## Run

Python 3.11 or newer. The supplied files are already in `data/raw/`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make run
make test
```

`make run` works offline with no API key. It reads `cache/llm_cache.jsonl`. A ticket that is not in the cache gets the rules baseline (`source=rules_fallback`), and the run prints one summary line with `cache_misses` and a WARNING if any ticket has no model answer.

| command | what it does |
| --- | --- |
| `make run` | Full pipeline, cache only. Never calls the network. |
| `make run-live` | Same, but calls Groq for tickets missing from the cache and appends the answers to the cache. Needs `GROQ_API_KEY` in the environment or in `.env` (see `.env.example`). Safe to rerun: cached tickets are skipped, and unparseable cache entries are retried. |
| `make smoke` | Sends 16 tickets (2 per reason code) to the model and prints what came back. Fills the same cache. Run it before `make run-live`. |
| `make test` | Golden-number, dedup, AI-layer and AI-isolation tests. No network. |
| `make clean` | Deletes generated files in `outputs/`. Leaves `cache/` alone. |

## Outputs

`make run` writes these to `outputs/`.

| file | content |
| --- | --- |
| `ledger.csv` | One row per refund ticket. Amounts in integer paise. |
| `bridge.csv` | Raw sum to canonical total, with a computed residual. |
| `reason.csv` | Month by agent reason code by text reason, with share of month. |
| `agent.csv` | Month by agent id (with team, tier, site, shift). |
| `classifications.csv` | Per ticket: label, replacement result, evidence, source. |
| `double_dip_exceptions.csv` | Tickets where the replacement flag or the text says a replacement went out with the refund. |
| `numbers.json` | Every figure used in the board pack. |
| `board_pack.md` | Rendered from `numbers.json`. |

## Layout

```text
src/vireo/   load, validate, canonicalize, dedup, ledger, reconcile, integrity, reports,
             reasons (AI layer), board_pack, pipeline
taxonomy.md  label definitions used by the prompt
prompts/     versioned prompt
cache/       model answers, one JSON line each
scripts/     smoke_live.py
tests/       golden numbers, dedup, AI layer, AI isolation
NOTES.md     decisions, known issues, status
```

## Rules the code keeps

1. Amounts, scope, dates, joins, deduplication, totals and reconciliation are deterministic.
2. The AI sees ticket text and the agent's reason code. It never sees amounts, agent names, customer ids or customer sign-off names.
3. AI output cannot change the ledger. `tests/test_ai_isolation.py` checks the bytes under rules, a stub model and a failing model.
4. Every raw row is accounted for (ledger, duplicate, quarantined or excluded), or the run stops.
5. The reconciliation residual is computed. It is never forced to zero.

## Privacy

`data/raw/` holds customer data. Do not publish it.
