import pandas as pd

from src.vireo.config import SOURCE_RULES

AUDIT_COLUMNS = ["raw_ref", "ticket_id", "step", "field", "old", "new", "rule_id", "delta_paise"]


def canonicalize(valid):
    df = valid.copy()
    source = df["source_system"].str.strip()
    created = pd.to_datetime(df["created_at"].str.strip(), format="%Y-%m-%d %H:%M")
    raw_amount = df["refund_amount_inr"].str.strip()

    df["canonical_id"] = df["ticket_id"].str.strip()
    df["month"] = created.dt.strftime("%Y-%m")
    df["quarter"] = created.dt.year.astype(str) + "Q" + created.dt.quarter.astype(str)
    df["has_refund"] = raw_amount != ""
    raw_int = raw_amount.where(df["has_refund"], "0").astype("int64")
    divisor = source.map(lambda s: SOURCE_RULES[s]["unit_divisor"]).astype("int64")
    df["amount_paise"] = raw_int * 100 // divisor
    df["naive_paise"] = raw_int * 100
    df["normalization_rule_id"] = source.map(lambda s: SOURCE_RULES[s]["rule_id"])

    changed = df[df["has_refund"] & (divisor != 1)]
    audit = pd.DataFrame({
        "raw_ref": changed["source_file"] + ":" + changed["source_row"].astype(str),
        "ticket_id": changed["ticket_id"],
        "step": "canonicalize",
        "field": "refund_amount_inr",
        "old": changed["refund_amount_inr"].str.strip(),
        "new": changed["amount_paise"].astype(str),
        "rule_id": changed["normalization_rule_id"],
        "delta_paise": changed["amount_paise"] - changed["naive_paise"],
    }, columns=AUDIT_COLUMNS)
    return df, audit
