import pandas as pd

from src.vireo.config import SOURCE_RULES
from src.vireo.dedup import DEDUP_RULE_ID

LEGACY_RULE_ID = SOURCE_RULES["legacy_fd"]["rule_id"]


def naive_paise(frame):
    amounts = frame["refund_amount_inr"].str.strip()
    digits = amounts.str.fullmatch(r"[0-9]+")
    return int((amounts[digits].astype("int64") * 100).sum())


def reconcile(raw, quarantined, audit, ledger):
    legacy = audit[audit["rule_id"] == LEGACY_RULE_ID]
    dupes = audit[audit["rule_id"] == DEDUP_RULE_ID]
    lines = [
        ("Raw export read as rupees (naive sum)", "raw_sum", int(raw["refund_amount_inr"].str.strip().ne("").sum()), naive_paise(raw)),
        ("Quarantined rows removed", "validation_failure", int(quarantined["refund_amount_inr"].str.strip().ne("").sum()) if len(quarantined) else 0, -naive_paise(quarantined) if len(quarantined) else 0),
        ("Legacy_fd amounts rescaled from paise to rupees", LEGACY_RULE_ID, len(legacy), int(legacy["delta_paise"].sum())),
        ("Duplicate rows removed", DEDUP_RULE_ID, int((dupes["delta_paise"] != 0).sum()), int(dupes["delta_paise"].sum())),
    ]
    canonical = int(ledger["amount_paise"].sum())
    residual = canonical - sum(line[3] for line in lines)
    lines.append(("Canonical refund total (ledger)", "ledger_sum", len(ledger), canonical))
    lines.append(("Unexplained residual (computed)", "residual", 0, residual))
    bridge = pd.DataFrame(lines, columns=["step", "rule_id", "rows_with_amount", "amount_paise"])
    bridge["amount_inr"] = bridge["amount_paise"] / 100
    return bridge, residual
