import re
from datetime import datetime

import pandas as pd

from src.vireo.config import KNOWN_STATUS, SOURCE_RULES

REQUIRED_COLUMNS = [
    "ticket_id", "created_at", "status", "channel", "customer_id", "order_id",
    "product_sku", "assigned_team", "agent_id", "refund_amount_inr",
    "refund_reason_code", "replacement_issued", "customer_message",
    "agent_notes", "source_system",
]


def row_problems(row):
    found = []
    if not re.fullmatch(r"TK-\d{6}", row["ticket_id"].strip()):
        found.append("ticket_id_pattern")
    try:
        datetime.strptime(row["created_at"].strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        found.append("created_at_unparseable")
    amount = row["refund_amount_inr"].strip()
    code = row["refund_reason_code"].strip()
    if bool(amount) != bool(code):
        found.append("code_amount_mismatch")
    digits = bool(re.fullmatch(r"[0-9]+", amount))
    if amount and not digits:
        found.append("amount_not_digits")
    rule = SOURCE_RULES.get(row["source_system"].strip())
    if rule is None:
        found.append("unknown_source_system")
    elif digits and int(amount) % rule["unit_divisor"]:
        found.append("amount_not_whole_rupees")
    if row["status"].strip() not in KNOWN_STATUS:
        found.append("unknown_status")
    return ";".join(found)


def validate(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    problems = df.apply(row_problems, axis=1) if len(df) else pd.Series([], dtype=str)
    bad = problems != ""
    quarantined = df[bad].copy()
    quarantined["quarantine_reason"] = problems[bad]
    return df[~bad].copy(), quarantined
