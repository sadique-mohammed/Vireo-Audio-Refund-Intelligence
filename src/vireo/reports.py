import pandas as pd


def _by_month_share(frame):
    return (frame["refund_paise"] / frame.groupby("month")["refund_paise"].transform("sum")).round(4)


def monthly(kept, ledger):
    out = kept.groupby("month").size().rename("tickets_total").to_frame()
    out = out.join(ledger.groupby("month").agg(refund_tickets=("canonical_id", "size"), refund_paise=("amount_paise", "sum")))
    out = out.fillna(0).astype("int64")
    out["refund_rate"] = (out["refund_tickets"] / out["tickets_total"]).round(4)
    out["refund_inr"] = out["refund_paise"] / 100
    return out.reset_index()


def quarterly(canonical, kept, ledger):
    out = kept.groupby("quarter").size().rename("tickets_total").to_frame()
    out = out.join(ledger.groupby("quarter").agg(refund_tickets=("canonical_id", "size"), refund_paise=("amount_paise", "sum")))
    out = out.join(canonical.groupby("quarter")["naive_paise"].sum().rename("raw_export_paise"))
    out = out.fillna(0).astype("int64")
    out["refund_rate"] = (out["refund_tickets"] / out["tickets_total"]).round(4)
    out["avg_refund_inr"] = (out["refund_paise"] / out["refund_tickets"] / 100).round(2)
    out["canonical_inr"] = out["refund_paise"] / 100
    out["raw_export_inr"] = out["raw_export_paise"] / 100
    return out.reset_index()


def reason_table(ledger, classes):
    labels = classes[["ticket_id", "label"]].rename(columns={"ticket_id": "canonical_id", "label": "text_reason"})
    df = ledger.merge(labels, on="canonical_id", how="left", validate="1:1")
    df["text_reason"] = df["text_reason"].fillna("UNCLASSIFIED")
    out = (
        df.groupby(["month", "refund_reason_code", "text_reason"])
        .agg(refund_tickets=("canonical_id", "size"), refund_paise=("amount_paise", "sum"))
        .reset_index()
        .rename(columns={"refund_reason_code": "reason_code"})
    )
    out["share_of_month"] = _by_month_share(out)
    out["refund_inr"] = out["refund_paise"] / 100
    return out


def agent_table(ledger, agents):
    if agents["agent_id"].duplicated().any():
        raise ValueError("roster has several rows per agent_id; a date-aware roster join is not implemented")
    roster = agents.rename(columns={"team": "roster_team"})[["agent_id", "roster_team", "tier", "site", "shift"]]
    df = ledger.merge(roster, on="agent_id", how="left", validate="m:1")
    keys = ["month", "agent_id", "assigned_team", "roster_team", "tier", "site", "shift"]
    df[keys[3:]] = df[keys[3:]].fillna("unknown")
    out = df.groupby(keys).agg(refund_tickets=("canonical_id", "size"), refund_paise=("amount_paise", "sum")).reset_index()
    out["refund_inr"] = out["refund_paise"] / 100
    return out


def team_table(kept, ledger, agents):
    tier = agents.groupby("team")["tier"].agg(lambda s: s.mode().iloc[0]).rename("tier")
    out = kept.groupby("assigned_team").size().rename("tickets_total").to_frame()
    out = out.join(ledger.groupby("assigned_team").agg(refund_tickets=("canonical_id", "size"), refund_paise=("amount_paise", "sum")))
    out = out.fillna(0).astype("int64").join(tier)
    out["refund_rate"] = (out["refund_tickets"] / out["tickets_total"]).round(4)
    out["avg_refund_inr"] = (out["refund_paise"] / out["refund_tickets"].where(out["refund_tickets"] > 0) / 100).round(2)
    out["share_of_refund_inr"] = (out["refund_paise"] / out["refund_paise"].sum()).round(4)
    out["refund_inr"] = out["refund_paise"] / 100
    return out.reset_index().sort_values("refund_paise", ascending=False, kind="stable")


def reason_code_summary(ledger):
    out = ledger.groupby("refund_reason_code").agg(refund_tickets=("canonical_id", "size"), refund_paise=("amount_paise", "sum"))
    out["share"] = (out["refund_paise"] / out["refund_paise"].sum()).round(4)
    out["refund_inr"] = out["refund_paise"] / 100
    return out.reset_index().sort_values("refund_paise", ascending=False, kind="stable")


def double_dip_table(ledger, classes):
    cols = ["canonical_id", "month", "assigned_team", "agent_id", "product_sku", "amount_paise"]
    df = classes.merge(ledger[cols], left_on="ticket_id", right_on="canonical_id", validate="1:1")
    flag = df["replacement_flag"] == "Y"
    text = df["replacement_sent"]
    df = df[flag | (text == "yes")].copy()
    flag, text = df["replacement_flag"] == "Y", df["replacement_sent"]
    df["status"] = "text_only"
    df.loc[flag & (text == "yes"), "status"] = "flag_and_text"
    df.loc[flag & (text == "no"), "status"] = "flag_only_text_denies"
    df.loc[flag & (text == "unclear"), "status"] = "flag_only_text_unclear"
    df["refund_inr"] = df["amount_paise"] / 100
    keep = ["ticket_id", "month", "assigned_team", "agent_id", "product_sku", "refund_inr", "replacement_flag", "replacement_sent", "source", "status", "evidence"]
    return df[keep].sort_values("ticket_id", kind="stable")
