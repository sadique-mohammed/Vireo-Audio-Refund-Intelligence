# Notes: decisions, known issues, status

Figures come from `outputs/numbers.json`. Policy sections refer to `support-policy.pdf` v3.2.

## Money (code only, no AI)

1. **Legacy amounts are paise.** `legacy_fd` amounts are divided by 100. All 775 legacy amounts are multiples of 100, and in the 125 duplicated pairs that carry money the legacy value is exactly 100 times the helpdesk value. Policy section 9 says the legacy tool used its own unit. The divisor lives in `SOURCE_RULES` in `config.py`. Reading every amount as rupees gives the raw ₹230,124,081.
2. **Integer paise everywhere.** No float touches a money sum.
3. **Duplicates: exact `ticket_id`, helpdesk copy kept.** 638 ids repeat, always one helpdesk row plus one legacy row. If a pair ever disagrees on the amount, the run stops.
4. **Scope is refund tickets.** 2,340 deduplicated tickets have a refund amount. Tickets with no amount are excluded, not counted as zero. The run stops if ledger + duplicates + quarantined + excluded does not equal the raw row count.
5. **Quarantine, never guess.** `validate.py` holds out malformed rows. No real row is quarantined today.
6. **The bridge computes its residual** (raw sum, quarantine, legacy rescale, duplicates, canonical). The run stops if it is not zero. It is zero.
7. **The two quoted figures are checked for consistency, not reproduced.** Finance's "well over a crore a quarter" matches reading the raw column as rupees (₹3.8 crore average, above one crore in the quarters that contain legacy rows). The helpdesk's "around ₹11 lakh" matches the canonical average of ₹11.2 lakh.
8. **Periods follow `created_at`** (IST as exported). The data has no refund date. Open and pending tickets (115, ₹317,314) stay in the ledger.
9. **Ownership is `assigned_team`** (policy section 9). 190 refund tickets differ from the agent's roster team; both are kept. People appear by id. Tier 2 is never compared with Tier 1 (policy section 6).
10. **Order integrity is report only.** Direct `order_id` join only; 798 refund tickets have no `order_id`. 98 orders are refunded more than their value across several tickets (₹250,054). Nothing here changes the ledger.

## AI (reads text only)

11. **Twelve labels plus an abstain** (`taxonomy.md`). The agent's code is a hint, not the answer: 43% of refund rupees sit under the catch-all GW-OTHER.
12. **What the model sees:** customer message, agent notes, the original code and the taxonomy. Amounts, order ids, customer ids, agent sign-offs and customer sign-off names are removed first. Evidence quotes are checked against that same scrubbed text (`evidence_verified`).
13. **Configured live provider:** Groq's OpenAI-compatible API, default model `openai/gpt-oss-120b`, JSON output, temperature 0.1. The current implementation does not call Gemini. The cache key includes the model tag and thinking-level setting; the latter is retained from earlier experiments and is not sent as a Groq setting.
14. **The cache is a file in the repo** (`cache/llm_cache.jsonl`, append-only). `make run` reads it and never calls the network. A ticket not in the cache gets the rules baseline and `source=rules_fallback`, and the run prints a WARNING. On the shipped cache, `cache_misses` must be 0.
15. **Failure handling:** transient errors retry with 1, 2, 4, 8 second waits. A 400, 401, 403 or 404 stops the run at once, so a bad key or model id cannot burn through 2,340 retries. A reply that is not valid JSON, or has a label outside the list, is not trusted: it is not used and is retried on the next `make run-live`.
16. **The rules baseline** for replacements is a set of keyword patterns from the agent notes, with a negation winning over a positive phrase. Its count is an estimate until checked against human labels.

## Known issues

- The live model call has not been independently verified for this submission. Tests use stub providers. Run `make smoke` with a valid Groq key before relying on live labels.
- Until the cache is filled, `make run` labels every ticket from rules.
- Replacement counts from keyword rules are not validated against human labels.
- The roster join expects one row per agent (true today; a second row stops the run).
- Evidence matching ignores case and spacing but not punctuation.
- Sign-off scrubbing cuts at a closing phrase in the last six words (thanks, regards, please revert, with typos). A name written with no closing phrase would not be cut. The test `test_no_customer_name_reaches_the_model` checks all 2,340 refund tickets against `customers.csv`.
- A closing word inside the last six words of a message can cut a few real words (for example "no response"). This does not affect any amount.

## Left out on purpose

Human-review queue and gate, audit-trail CSVs, run manifest, data-profile script, fuzzy deduplication, CSAT, SLA credits, handle time, and a frontend. None was in the brief.

## Status against the brief

| item | status |
| --- | --- |
| Tool runs from the README | Built. `make run` and `make test` pass offline. |
| Monthly refunds by reason and by agent, total reconciles | `reason.csv`, `agent.csv`, `bridge.csv`. Built and tested. |
| Both quoted figures bridged to one total | `bridge.csv`, `board_pack.md`. Built and tested. |
| AI reads text, code decides money | `tests/test_ai_isolation.py`. |
| Business goal as a number in ₹ | Not started. Needs the live cache first. |
| Accuracy and error examples | Not started. Needs the live cache and about 50 hand labels. |
| Memo, recording, form | Not started. |
