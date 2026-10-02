import pandas as pd

LEDGER_COLUMNS = [
    "ticket_id", "created_at", "month", "quarter", "status", "channel", "order_id",
    "product_sku", "assigned_team", "agent_id", "refund_reason_code",
    "replacement_issued", "source_system", "source_row", "amount_paise",
    "normalization_rule_id",
]


def build_ledger(kept, removed, quarantined, raw_rows):
    ledger = kept[kept["has_refund"]].copy()
    excluded = kept[~kept["has_refund"]]
    accounted = len(ledger) + len(removed) + len(quarantined) + len(excluded)
    if accounted != raw_rows:
        raise AssertionError(
            f"row conservation failed: raw {raw_rows} != ledger {len(ledger)} + duplicates "
            f"{len(removed)} + quarantined {len(quarantined)} + excluded {len(excluded)}"
        )
    if ledger["canonical_id"].duplicated().any():
        raise AssertionError("ledger holds a repeated ticket_id")
    return ledger.sort_values("canonical_id", kind="stable"), excluded
