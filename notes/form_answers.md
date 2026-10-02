# Final Submission Form Answers

## What did you build, and what business outcome does it move?

I built an AI-free deterministic financial ledger to solve the reconciliation crisis (explaining the gap between the ₹2.3 crore raw figure and the ₹67 lakh canonical figure), coupled with an AI extraction layer.

**Business goal:** Reduce the refund rate from **20.1% back to 19.0%**, the H1 2025 level. At the recent ticket volume, this represents approximately **₹73,000 less refund value per quarter**. This is an opportunity estimate, not a guaranteed saving.

## What does one run cost?

$0.00. I migrated the pipeline to the Groq free tier using `openai/gpt-oss-120b`. The LLM processes only the 2,340 refund tickets (at roughly 900 input tokens and 100 output tokens per ticket). Processing a full month of 569 refund tickets is completely free under their current tier limits. The results are cached so offline/rerun latency and costs are $0.

## How do you know it works?

**Financial pipeline: 40 tests passed, ₹67.1 lakh canonical refund total, ₹0 reconciliation residual. AI: 16/16 live smoke calls succeeded, but 2,324/2,340 delivered classifications currently use rules fallback, so final AI accuracy has not been established.**

## Did you change, narrow, or push back on the requested approach?

I pushed back on Arjun's desire to rank agents by "who is giving away money" as the refund rate is tied to the team's functional design (e.g., Returns Desk naturally has a 50% refund rate). I also narrowed the AI layer to strictly read text; money computations are entirely segregated from the LLM to guarantee deterministic outputs.

## What is wrong with what you are handing us?

The sample of 120 labels gives wide intervals (±8-10 points), and having a single labeler limits objectivity on edge cases. I could not verify if over-refunded orders are data artifacts or actual duplicate payouts.

## What did you leave out, and why that rather than something else?

I explicitly left out Laya/Jev, complex RAG, agentic LLM flows, and a UI dashboard. The core business problem is financial reconciliation, which requires a robust, reproducible data pipeline rather than a web app or complex AI orchestrations that hallucinate.

## Anything you built or found that nobody asked for?

- Found the large gap between the raw export total and the canonical refund total.
- Identified duplicate migration records and legacy money-unit issues.
- Found refund + replacement / double-dip candidates for investigation.
- Added an audit trail so Finance can trace adjustments back to source records.

## What did you use AI for?

- Used **GPT and Claude** for planning, reviewing the architecture, and challenging design decisions.
- Used **Antigravity** for coding and implementation.
- AI helped speed up planning and implementation.
- Some AI suggestions were over-engineered and led to unnecessary work.
- I discarded unnecessary abstractions and simplified the system around the actual data and assignment requirements.

## GitHub

https://github.com/sadique-mohammed/Vireo-Audio-Refund-Intelligence

## Screen recording

## Three things for Monday handoff

- Start with `README.md` and run the pipeline; the ledger is the financial source of truth.
- AI only classifies ticket text; it **does not change refund amounts or reconciliation**.
- Check `board_pack`, `eval_report`, `review_queue`, and `bridge.csv` for business results, AI quality, exceptions, and reconciliation.

## Honest hours spent

9 hours.
