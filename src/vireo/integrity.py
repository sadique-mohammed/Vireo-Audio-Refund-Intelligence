import pandas as pd


def order_integrity(ledger, orders):
    orders = orders.assign(order_value_paise=orders["order_value_inr"].astype("int64") * 100)
    with_order = ledger[ledger["order_id"] != ""]
    joined = with_order.merge(orders[["order_id", "order_value_paise"]], on="order_id", how="left", validate="m:1")
    unmatched = int(joined["order_value_paise"].isna().sum())
    joined = joined.dropna(subset=["order_value_paise"])
    joined["order_value_paise"] = joined["order_value_paise"].astype("int64")

    above = joined[joined["amount_paise"] > joined["order_value_paise"]]
    above = above[["canonical_id", "order_id", "order_value_paise", "amount_paise"]].rename(columns={"canonical_id": "ticket_id", "amount_paise": "refund_paise"})

    per_order = joined.groupby("order_id").agg(
        order_value_paise=("order_value_paise", "first"),
        refund_tickets=("canonical_id", "size"),
        refunded_paise=("amount_paise", "sum"),
    )
    over = per_order[per_order["refunded_paise"] > per_order["order_value_paise"]].copy()
    over["excess_paise"] = over["refunded_paise"] - over["order_value_paise"]
    over = over.reset_index().sort_values(["excess_paise", "order_id"], ascending=[False, True], kind="stable")

    summary = {
        "refund_tickets_with_order_id": len(with_order),
        "refund_tickets_without_order_id": len(ledger) - len(with_order),
        "order_id_not_in_orders": unmatched,
        "tickets_above_order_value": len(above),
        "orders_over_refunded": len(over),
        "over_refund_excess_paise": int(over["excess_paise"].sum()),
    }
    return above, over, summary
