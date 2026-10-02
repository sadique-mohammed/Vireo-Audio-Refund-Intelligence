# Final Submission Form Answers

## What did you build, and what business outcome does it move?
I built an AI-free deterministic financial ledger to solve the reconciliation crisis (explaining the gap between the ₹2.3 crore raw figure and the ₹67 lakh canonical figure), coupled with an AI extraction layer. 

**Current estimated refund + replacement rate: 15.6%. The proposed goal is to reduce this toward <1%, with an estimated replacement-cost opportunity of ₹65k–₹133k per quarter. These figures are estimates and need validation.**

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
I discovered that the internal "replacement_issued" flag is severely broken, catching only half of the actual instances (7% vs 15.6%) where a replacement was shipped alongside a refund. AI reading the notes found the true total.

## What did you use AI for?
The AI (`groq/openai/gpt-oss-120b`) was used exclusively to read `customer_message` and `agent_notes` to categorize the true reason (because GW-OTHER was used as a generic dump) and extract evidence if a physical replacement was also sent. 

## GitHub
https://github.com/vireo/refund-intel-demo

## Google Drive
N/A

## Screen recording
[Insert your Loom/Drive Link here]

## Three things for Monday handoff
1. Review the generated `bridge.csv` to trace the ₹6.71M reconciliation.
2. Review `double_dip_exceptions.csv` to take immediate action on the ~₹1.3 lakh quarterly leak.
3. Confirm if the over-refunded orders discovered are genuine duplicate payouts or data artifacts.

## Honest hours spent
5 hours.
