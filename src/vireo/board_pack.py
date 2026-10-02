import pandas as pd


def _money(value):
    return f"{value:,.0f}"


def _table(frame, money=(), pct=()):
    shown = frame.copy()
    for col in money:
        shown[col] = shown[col].map(_money)
    for col in pct:
        shown[col] = shown[col].map(lambda v: f"{v:.1%}")
    for col in shown.columns:
        if pd.api.types.is_integer_dtype(shown[col]):
            shown[col] = shown[col].map(lambda v: f"{v:,}")
    return shown.to_markdown(index=False)


def render(n):
    d, b, rf = n["data"], n["canonical"], n["reported_figures"]
    ai = n["ai"]
    lines = [
        "# Vireo Audio refund summary",
        "",
        f"Period: {n['period']['first_quarter']} to {n['period']['last_quarter']} ({n['period']['quarters']} quarters, by ticket creation date, IST as exported). All money in rupees.",
        "",
        "## Business Goal",
        "",
        "Reduce the refund rate from 20.1% back to 19.0%, the H1 2025 level. At the recent ticket volume, this represents approximately ₹73,000 less refund value per quarter. This is an opportunity estimate, not a guaranteed saving.",
        "",
        "## Headline",
        "",
        f"- Canonical refund total: ₹{_money(b['inr'])} (₹{b['lakh']:.1f} lakh) on {d['refund_tickets']:,} refund tickets.",
        f"- The raw export read as rupees sums to ₹{_money(n['raw_export']['naive_sum_inr'])} (₹{n['raw_export']['crore']:.1f} crore). The gap is explained line by line below, with a computed residual of ₹{_money(n['reconciliation']['residual_inr'])}.",
        f"- Average per quarter: canonical ₹{b['avg_per_quarter_lakh']:.1f} lakh; raw export ₹{n['raw_export']['avg_per_quarter_crore']:.1f} crore.",
        "",
        "## Reconciliation bridge",
        "",
        _table(pd.DataFrame(n["reconciliation"]["lines"]), money=["amount_inr"]),
        "",
        "## The two reported figures",
        "",
        f"- Finance said the export sums to well over a crore a quarter. The raw export averages ₹{rf['finance']['raw_avg_per_quarter_crore']:.1f} crore a quarter and is above one crore in {rf['finance']['quarters_above_one_crore']} of {n['period']['quarters']} quarters ({', '.join(rf['finance']['quarters_above_one_crore_list'])}). That is consistent with Finance reading `refund_amount_inr` as rupees. It does not hold from {rf['finance']['first_quarter_below_one_crore']}, when no legacy rows exist.",
        f"- The helpdesk said refunds run around ₹11 lakh a quarter. The canonical average is ₹{b['avg_per_quarter_lakh']:.1f} lakh, {rf['helpdesk']['difference_pct']:+.1f}% from 11. That is consistent with the helpdesk figure. The exact method behind either report is not known, so this is consistency, not reproduction.",
        "",
        "## By quarter",
        "",
        _table(pd.DataFrame(n["quarterly"]), money=["avg_refund_inr", "canonical_inr", "raw_export_inr"], pct=["refund_rate"]),
        "",
        "## By month",
        "",
        _table(pd.DataFrame(n["monthly"]), money=["refund_inr"], pct=["refund_rate"]),
        "",
        "## By reason code as recorded by agents",
        "",
        _table(pd.DataFrame(n["reason_code"]), money=["refund_inr"], pct=["share"]),
        "",
        "## By team (first-assigned team on the ticket)",
        "",
        _table(pd.DataFrame(n["teams"]), money=["refund_inr", "avg_refund_inr"], pct=["refund_rate", "share_of_refund_inr"]),
        "",
        "## Order integrity (report only, not in the ledger)",
        "",
        f"- Refund tickets with an order id: {n['order_integrity']['refund_tickets_with_order_id']:,}. Without one: {n['order_integrity']['refund_tickets_without_order_id']:,} (not checked).",
        f"- Tickets refunding more than the order value: {n['order_integrity']['tickets_above_order_value']}.",
        f"- Orders refunded more than their value across several tickets: {n['order_integrity']['orders_over_refunded']}, excess ₹{_money(n['order_integrity']['over_refund_excess_inr'])}.",
        "",
        "## Reading the ticket text",
        "",
        "**⚠️ LIMITATION:** The vast majority of classifications currently rely on the `rules_fallback` baseline. Final AI accuracy has not yet been established across the full dataset.",
        "",
        f"- Source of labels: {', '.join(f'{k} {v:,}' for k, v in sorted(ai['source_counts'].items()))}.",
        f"- Replacement estimate from keyword rules*: {n['replacement']['rules_yes']:,} refund tickets. The helpdesk flag marks {n['replacement']['flag_yes']:,}.",
        "",
        "*Estimate from keyword rules, not validated against human labels.",
        "",
    ]
    return "\n".join(lines)
