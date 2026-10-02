# Vireo Audio refund summary

Period: 2025Q1 to 2026Q2 (6 quarters, by ticket creation date, IST as exported). All money in rupees.

## Business Goal

Reduce the refund rate from 20.1% back to 19.0%, the H1 2025 level. At the recent ticket volume, this represents approximately ₹73,000 less refund value per quarter. This is an opportunity estimate, not a guaranteed saving.

## Headline

- Canonical refund total: ₹6,709,932 (₹67.1 lakh) on 2,340 refund tickets.
- The raw export read as rupees sums to ₹230,124,081 (₹23.0 crore). The gap is explained line by line below, with a computed residual of ₹0.
- Average per quarter: canonical ₹11.2 lakh; raw export ₹3.8 crore.

## Reconciliation bridge

| step                                            | rule_id               | rows_with_amount   | amount_inr   |
|:------------------------------------------------|:----------------------|:-------------------|:-------------|
| Raw export read as rupees (naive sum)           | raw_sum               | 2,465              | 230,124,081  |
| Quarantined rows removed                        | validation_failure    | 0                  | 0            |
| Legacy_fd amounts rescaled from paise to rupees | legacy_fd_div_100     | 775                | -223,053,138 |
| Duplicate rows removed                          | exact_ticket_id_dedup | 125                | -361,011     |
| Canonical refund total (ledger)                 | ledger_sum            | 2,340              | 6,709,932    |
| Unexplained residual (computed)                 | residual              | 0                  | 0            |

## The two reported figures

- Finance said the export sums to well over a crore a quarter. The raw export averages ₹3.8 crore a quarter and is above one crore in 3 of 6 quarters (2025Q1, 2025Q2, 2025Q3). That is consistent with Finance reading `refund_amount_inr` as rupees. It does not hold from 2025Q4, when no legacy rows exist.
- The helpdesk said refunds run around ₹11 lakh a quarter. The canonical average is ₹11.2 lakh, +1.7% from 11. That is consistent with the helpdesk figure. The exact method behind either report is not known, so this is consistency, not reproduction.

## By quarter

| quarter   | tickets_total   |   refund_tickets | refund_rate   | avg_refund_inr   | canonical_inr   | raw_export_inr   |
|:----------|:----------------|-----------------:|:--------------|:-----------------|:----------------|:-----------------|
| 2025Q1    | 1,053           |              212 | 20.1%         | 2,875            | 609,583         | 61,049,992       |
| 2025Q2    | 1,388           |              253 | 18.2%         | 2,875            | 727,422         | 72,879,635       |
| 2025Q3    | 1,843           |              405 | 22.0%         | 2,980            | 1,207,091       | 92,028,618       |
| 2025Q4    | 2,678           |              542 | 20.2%         | 3,003            | 1,627,575       | 1,627,575        |
| 2026Q1    | 2,361           |              455 | 19.3%         | 2,766            | 1,258,438       | 1,258,438        |
| 2026Q2    | 2,277           |              473 | 20.8%         | 2,706            | 1,279,823       | 1,279,823        |

## By month

| month   |   tickets_total |   refund_tickets | refund_rate   | refund_inr   |
|:--------|----------------:|-----------------:|:--------------|:-------------|
| 2025-01 |             302 |               58 | 19.2%         | 141,048      |
| 2025-02 |             324 |               63 | 19.4%         | 177,938      |
| 2025-03 |             427 |               91 | 21.3%         | 290,597      |
| 2025-04 |             452 |               79 | 17.5%         | 250,089      |
| 2025-05 |             489 |               86 | 17.6%         | 217,464      |
| 2025-06 |             447 |               88 | 19.7%         | 259,869      |
| 2025-07 |             522 |              119 | 22.8%         | 356,986      |
| 2025-08 |             590 |              125 | 21.2%         | 367,821      |
| 2025-09 |             731 |              161 | 22.0%         | 482,284      |
| 2025-10 |             870 |              185 | 21.3%         | 575,637      |
| 2025-11 |             948 |              186 | 19.6%         | 575,984      |
| 2025-12 |             860 |              171 | 19.9%         | 475,954      |
| 2026-01 |             762 |              153 | 20.1%         | 449,868      |
| 2026-02 |             765 |              139 | 18.2%         | 372,797      |
| 2026-03 |             834 |              163 | 19.5%         | 435,773      |
| 2026-04 |             720 |              154 | 21.4%         | 402,265      |
| 2026-05 |             812 |              149 | 18.4%         | 426,737      |
| 2026-06 |             745 |              170 | 22.8%         | 450,821      |

## By reason code as recorded by agents

| refund_reason_code   |   refund_tickets | refund_inr   | share   |
|:---------------------|-----------------:|:-------------|:--------|
| GW-OTHER             |              991 | 2,907,036    | 43.3%   |
| RETURN-QC-OK         |              452 | 1,181,386    | 17.6%   |
| DUP-PAYMENT          |              321 | 884,586      | 13.2%   |
| CANCEL               |              222 | 612,950      | 9.1%    |
| DOA-REPL             |              147 | 471,190      | 7.0%    |
| WTY-BUYBACK          |               89 | 289,154      | 4.3%    |
| PRICE-ADJ            |               71 | 207,073      | 3.1%    |
| LOST-TRANSIT         |               47 | 156,557      | 2.3%    |

## By team (first-assigned team on the ticket)

| assigned_team          |   tier | tickets_total   |   refund_tickets | refund_rate   | refund_inr   | avg_refund_inr   | share_of_refund_inr   |
|:-----------------------|-------:|:----------------|-----------------:|:--------------|:-------------|:-----------------|:----------------------|
| Returns Desk           |      1 | 1,161           |              633 | 54.5%         | 1,732,192    | 2,736            | 25.8%                 |
| Billing                |      1 | 1,600           |              604 | 37.8%         | 1,601,340    | 2,651            | 23.9%                 |
| Chat Frontline         |      1 | 3,229           |              362 | 11.2%         | 1,093,167    | 3,020            | 16.3%                 |
| Logistics              |      1 | 2,054           |              349 | 17.0%         | 1,087,079    | 3,115            | 16.2%                 |
| Email Frontline        |      1 | 1,965           |              204 | 10.4%         | 576,560      | 2,826            | 8.6%                  |
| Voice Frontline        |      1 | 1,000           |              113 | 11.3%         | 342,233      | 3,029            | 5.1%                  |
| Escalations & Warranty |      2 | 591             |               75 | 12.7%         | 277,361      | 3,698            | 4.1%                  |

## Order integrity (report only, not in the ledger)

- Refund tickets with an order id: 1,542. Without one: 798 (not checked).
- Tickets refunding more than the order value: 0.
- Orders refunded more than their value across several tickets: 98, excess ₹250,054.

## Reading the ticket text

**⚠️ LIMITATION:** The vast majority of classifications currently rely on the `rules_fallback` baseline. Final AI accuracy has not yet been established across the full dataset.

- Source of labels: llm 16, rules_fallback 2,324.
- Replacement estimate from keyword rules*: 360 refund tickets. The helpdesk flag marks 166.

*Estimate from keyword rules, not validated against human labels.
