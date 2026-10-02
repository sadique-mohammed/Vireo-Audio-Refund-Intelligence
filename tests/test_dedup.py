import pandas as pd

from src.vireo.canonicalize import canonicalize
from src.vireo.dedup import amount_conflicts, deduplicate
from src.vireo.validate import REQUIRED_COLUMNS, validate


def build(*rows):
    data = []
    for i, overrides in enumerate(rows):
        base = {c: "" for c in REQUIRED_COLUMNS}
        base.update(ticket_id="TK-240001", created_at="2025-02-03 10:15", status="resolved",
                    source_system="helpdesk", refund_amount_inr="1500", refund_reason_code="CANCEL",
                    source_file="t.csv", source_row=i + 2)
        base.update(overrides)
        data.append(base)
    valid, _ = validate(pd.DataFrame(data))
    canonical, _ = canonicalize(valid)
    return canonical


def test_pair_keeps_helpdesk_and_removes_legacy_copy():
    df = build({"source_system": "legacy_fd", "refund_amount_inr": "150000"}, {"source_system": "helpdesk"})
    kept, removed, audit = deduplicate(df)
    assert list(kept["source_system"]) == ["helpdesk"]
    assert list(removed["source_system"]) == ["legacy_fd"]
    assert list(audit["delta_paise"]) == [-150000]
    assert amount_conflicts(df) == []


def test_three_rows_of_one_ticket_keep_exactly_one():
    df = build({"source_system": "legacy_fd", "refund_amount_inr": "150000"}, {"source_system": "helpdesk"}, {"source_system": "legacy_fd", "refund_amount_inr": "150000"})
    kept, removed, _ = deduplicate(df)
    assert len(kept) == 1 and len(removed) == 2 and kept.iloc[0]["source_system"] == "helpdesk"


def test_different_ticket_ids_are_never_merged():
    df = build({}, {"ticket_id": "TK-240002"})
    kept, removed, _ = deduplicate(df)
    assert len(kept) == 2 and removed.empty


def test_disagreeing_amounts_are_reported():
    df = build({"source_system": "legacy_fd", "refund_amount_inr": "150100"}, {"source_system": "helpdesk"})
    assert amount_conflicts(df) == ["TK-240001"]


def test_dedup_is_idempotent():
    df = build({"source_system": "legacy_fd", "refund_amount_inr": "150000"}, {"source_system": "helpdesk"}, {"ticket_id": "TK-240002"})
    kept, _, _ = deduplicate(df)
    again, removed, _ = deduplicate(kept)
    assert len(again) == len(kept) and removed.empty
