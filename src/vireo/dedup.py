import pandas as pd

from src.vireo.canonicalize import AUDIT_COLUMNS
from src.vireo.config import SOURCE_RANK

DEDUP_RULE_ID = "exact_ticket_id_dedup"


def deduplicate(df):
    ranked = df.assign(_rank=df["source_system"].str.strip().map(SOURCE_RANK))
    ranked = ranked.sort_values(["canonical_id", "_rank", "source_row"], kind="stable")
    keep = ~ranked.duplicated("canonical_id", keep="first")
    kept = ranked[keep].drop(columns="_rank").sort_values("canonical_id", kind="stable")
    removed = ranked[~keep].drop(columns="_rank").sort_values("source_row", kind="stable")
    audit = pd.DataFrame({
        "raw_ref": removed["source_file"] + ":" + removed["source_row"].astype(str),
        "ticket_id": removed["ticket_id"],
        "step": "dedup",
        "field": "row",
        "old": removed["source_system"],
        "new": "removed_duplicate",
        "rule_id": DEDUP_RULE_ID,
        "delta_paise": -removed["amount_paise"],
    }, columns=AUDIT_COLUMNS)
    return kept, removed, audit


def amount_conflicts(df):
    spread = df.groupby("canonical_id")["amount_paise"].nunique()
    return sorted(spread[spread > 1].index)
