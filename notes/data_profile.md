# Data Profile

## Files
| File | Rows | Columns | Purpose | Notes |
|---|---:|---:|---|---|
| `tickets.csv` | 37,559 | 21 | Raw customer ticket data | Contains duplicates and legacy money issues. |
| `orders.csv` | 134,818 | 9 | Truth for original purchase | Used to check if refund > purchase value. |
| `agents.csv` | 108 | 5 | Agent mapping | Maps `agent_id` to `tier` and `site`. |
| `support-policy.pdf`| N/A | N/A | Business rules | Contains rules on double-dips and legacy migrations. |

## Schema findings
The `tickets.csv` file has a `source_system` column with two values: `legacy_fd` (Freshdesk) and `helpdesk` (current system).

## Amount findings
The raw export total (₹2.3 Crore) is mathematically impossible compared to the helpdesk claim (₹11 Lakh/qtr). 
**Finding:** Tickets from `legacy_fd` have refund amounts exactly 100x larger than expected. The legacy system stored values in **paise**, while the new system stores them in **rupees**.

## Date findings
Dates are stored as strings (e.g., `2025-01-01 09:17`). For the canonical ledger, we parse the `created_at` timestamp to extract the Year-Month string (e.g., `2025-01`) for financial aggregations.

## Duplicate findings
**Finding:** Thousands of tickets exist twice in `tickets.csv`—once with `source_system=legacy_fd` and once with `helpdesk`. 
This perfectly matches Section 9 of the PDF: *"a subset of legacy tickets was re-imported during reconciliation"*. We must deduplicate by `ticket_id` and keep the newer `helpdesk` record.

## Reference-data joins
Joining `tickets.csv` against `orders.csv` using `order_id` revealed 98 "Over-refunded" orders where the total refunded amount exceeds the original `order_value`.

## Text findings
The `customer_message` and `agent_notes` fields are highly unstructured text. `refund_reason_code` is frequently set to `GW-OTHER` (Goodwill/Other) as a lazy dumping ground by agents, hiding the true reason for the refund (e.g., defective units).

## PDF findings
- **Section 5 (Double-Dips):** *"In no case is a customer to receive both a refund and a replacement... escalated to Team Lead and Finance"*
- **Section 9 (Legacy Money):** *"The legacy tool stored monetary values in its own native unit; the current helpdesk stores rupees."*

## Open questions
- Are the 98 over-refunded orders actual duplicate payouts, or just data artifacts (e.g., QA test orders)?
- What is the true dispatch volume of replacements? The `replacement_issued` flag only captures half of the text-based replacement confirmations.

## Rules implied by evidence
1. **Canonicalize Money:** If `source_system == 'legacy_fd'`, divide `refund_amount_inr` by 100.
2. **Deduplicate:** Drop duplicate `ticket_id` rows, prioritizing `helpdesk` over `legacy_fd`.
3. **AI Classification:** Ignore the `GW-OTHER` dropdown code; use an LLM to read the raw text and extract the true reason and whether a replacement was physically shipped.
