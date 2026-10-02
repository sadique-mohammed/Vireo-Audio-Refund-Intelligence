# AI Tool / Model Disclosure

| Tool / Model | Used for                  | Helped with | Failed / wasted time on | Discarded | Cost |
| ------------ | ------------------------- | ----------- | ----------------------- | --------- | ---- |
| GPT + Claude | Planning and architecture | Design      | Over-engineered flows   | Complex RAG| $0   |
| Antigravity  | Coding and implementation | Speeding up | Rate limit debugging    | UI/Dashboards| $0   |

## Development use vs product use

### Development assistance

**GPT + Claude:** planning and architecture.
**Antigravity:** coding and implementation.
AI helped with exploration and implementation, but some approaches were over-engineered and spent too much time checking the full dataset instead of isolating the issue with a smaller sample. I discarded that extra complexity.

### Submitted product

The product exclusively relies on `groq/openai/gpt-oss-120b` (or equivalent open-weights models) using extremely fast inference APIs. The application caches responses heavily to minimize API calls. It pulls the prompt from `reason_v1` or `reason_v2` and strictly enforces negative constraints and JSON adherence.

## Cost calculation

**Inference cost:** $0.00 paid API cost for the delivered run because Groq's free tier was used.
