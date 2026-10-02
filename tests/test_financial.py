import json
from pathlib import Path

import pytest

from src.vireo import reports
from src.vireo.config import RAW_DIR
from src.vireo.integrity import order_integrity
from src.vireo.load import load_csv

HERE = Path(__file__).parent
GOLDEN = json.loads((HERE / "golden_numbers.json").read_text())

BRIEF = {
    "raw_rows": 12238,
    "unique_tickets": 11600,
    "duplicates_removed": 638,
    "duplicates_with_amount": 125,
    "refund_tickets": 2340,
    "quarantined": 0,
    "naive_raw_sum": 230124081,
    "legacy_rescale": -223053138,
    "duplicates": -361011,
    "canonical": 6709932,
    "quarterly": {"2025Q1": 609583, "2025Q2": 727422, "2025Q3": 1207091, "2025Q4": 1627575, "2026Q1": 1258438, "2026Q2": 1279823},
    "open_pending": (115, 317314),
    "over_refunded": (98, 250054),
    "gw_other": (991, 2907036),
}


@pytest.fixture(scope="module")
def orders():
    return load_csv(RAW_DIR / "orders.csv")


def test_golden_file_equals_the_brief():
    g = GOLDEN
    assert (g["raw_rows"], g["unique_tickets"], g["duplicates_removed"], g["duplicates_with_amount"]) == (12238, 11600, 638, 125)
    assert (g["refund_tickets"], g["quarantined"]) == (2340, 0)
    assert g["bridge_inr"] == {"naive_raw_sum": 230124081, "legacy_rescale": -223053138, "duplicates": -361011, "canonical": 6709932}
    assert g["quarterly_inr"] == BRIEF["quarterly"]
    assert (g["open_pending_refund_tickets"], g["open_pending_refund_inr"]) == BRIEF["open_pending"]
    assert (g["orders_over_refunded"], g["orders_over_refunded_excess_inr"]) == BRIEF["over_refunded"]
    assert g["tickets_refund_above_order_value"] == 0
    assert (g["reason_code_inr"]["GW-OTHER"]["tickets"], g["reason_code_inr"]["GW-OTHER"]["inr"]) == BRIEF["gw_other"]


def test_row_counts(fin):
    assert len(fin.raw) == GOLDEN["raw_rows"]
    assert len(fin.kept) == GOLDEN["unique_tickets"]
    assert len(fin.removed) == GOLDEN["duplicates_removed"]
    assert int((fin.removed["amount_paise"] > 0).sum()) == GOLDEN["duplicates_with_amount"]
    assert len(fin.ledger) == GOLDEN["refund_tickets"]
    assert len(fin.quarantined) == GOLDEN["quarantined"]
    assert len(fin.excluded) == GOLDEN["unique_tickets"] - GOLDEN["refund_tickets"]


def test_bridge_matches_golden_and_residual_is_computed(fin):
    steps = dict(zip(fin.bridge["rule_id"], fin.bridge["amount_paise"] // 100))
    g = GOLDEN["bridge_inr"]
    assert steps["raw_sum"] == g["naive_raw_sum"]
    assert steps["legacy_fd_div_100"] == g["legacy_rescale"]
    assert steps["exact_ticket_id_dedup"] == g["duplicates"]
    assert steps["ledger_sum"] == g["canonical"]
    assert steps["validation_failure"] == 0
    assert fin.residual_paise == 0 and steps["residual"] == 0


def test_quarterly_and_monthly_totals(fin):
    quarterly = reports.quarterly(fin.canonical, fin.kept, fin.ledger)
    assert dict(zip(quarterly["quarter"], quarterly["canonical_inr"].astype(int))) == GOLDEN["quarterly_inr"]
    monthly = reports.monthly(fin.kept, fin.ledger)
    assert int(monthly["refund_paise"].sum()) == GOLDEN["bridge_inr"]["canonical"] * 100


def test_reason_codes_open_pending_and_legacy_units(fin):
    summary = reports.reason_code_summary(fin.ledger).set_index("refund_reason_code")
    for code, expected in GOLDEN["reason_code_inr"].items():
        assert summary.loc[code, "refund_tickets"] == expected["tickets"]
        assert summary.loc[code, "refund_paise"] == expected["inr"] * 100
    open_pending = fin.ledger[fin.ledger["status"].isin(["open", "pending"])]
    assert (len(open_pending), int(open_pending["amount_paise"].sum()) // 100) == BRIEF["open_pending"]
    legacy = fin.raw[(fin.raw["source_system"] == "legacy_fd") & (fin.raw["refund_amount_inr"] != "")]
    assert (legacy["refund_amount_inr"].astype("int64") % 100 == 0).all()


def test_order_integrity(fin, orders):
    above, over, summary = order_integrity(fin.ledger, orders)
    assert len(above) == GOLDEN["tickets_refund_above_order_value"] == 0
    assert (summary["orders_over_refunded"], summary["over_refund_excess_paise"] // 100) == BRIEF["over_refunded"]
    assert summary["refund_tickets_with_order_id"] + summary["refund_tickets_without_order_id"] == len(fin.ledger)
    assert summary["order_id_not_in_orders"] == 0
