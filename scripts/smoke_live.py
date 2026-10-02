import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.vireo import reasons
from src.vireo.config import RAW_DIR
from src.vireo.load import load_tickets
from src.vireo.pipeline import run_financial


def main():
    ledger = run_financial(load_tickets(RAW_DIR / "tickets.csv")).ledger
    sample = ledger.groupby("refund_reason_code").head(2)[reasons.TEXT_COLUMNS]
    classes, stats = reasons.classify_tickets(sample, mode="live")
    columns = ["ticket_id", "source", "label", "replacement_sent", "certainty", "evidence_verified"]
    print(classes[columns].to_string(index=False))
    print(reasons.summary_line(stats))
    print({k: stats[k] for k in ("calls_made", "calls_failed", "prompt_tokens", "output_tokens", "thinking_tokens")})


if __name__ == "__main__":
    main()
