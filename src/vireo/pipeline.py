import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.vireo import board_pack, reasons, reports
from src.vireo.canonicalize import canonicalize
from src.vireo.config import CACHE_PATH, OUTPUT_DIR, RAW_DIR
from src.vireo.dedup import amount_conflicts, deduplicate
from src.vireo.integrity import order_integrity
from src.vireo.ledger import LEDGER_COLUMNS, build_ledger
from src.vireo.load import load_csv, load_tickets
from src.vireo.reconcile import reconcile
from src.vireo.validate import validate


@dataclass
class Financials:
    raw: pd.DataFrame
    quarantined: pd.DataFrame
    canonical: pd.DataFrame
    kept: pd.DataFrame
    removed: pd.DataFrame
    audit: pd.DataFrame
    ledger: pd.DataFrame
    excluded: pd.DataFrame
    bridge: pd.DataFrame
    residual_paise: int
    amount_conflicts: list


def run_financial(tickets):
    # 1. Validate: Find rows missing critical data (IDs, dates). 'valid' holds clean rows, 'quarantined' holds bad rows.
    valid, quarantined = validate(tickets)
    
    # 2. Canonicalize: Convert legacy paise to INR. 'canonical' holds normalized money, 'canonical_audit' tracks changes.
    canonical, canonical_audit = canonicalize(valid)
    
    # 3. Deduplicate: Remove duplicate tickets from system migration. 'kept' are unique tickets, 'removed' are duplicates.
    kept, removed, dedup_audit = deduplicate(canonical)
    audit = pd.concat([canonical_audit, dedup_audit], ignore_index=True)
    
    # 4. Build Ledger: 'ledger' is the absolute Financial Source of Truth (one clean row per valid refund).
    ledger, excluded = build_ledger(kept, removed, quarantined, len(tickets))
    
    # 5. Reconcile: 'bridge' maps the mathematical path from the messy raw total to the true canonical ledger total.
    bridge, residual = reconcile(tickets, quarantined, audit, ledger)
    
    return Financials(
        raw=tickets, quarantined=quarantined, canonical=canonical, kept=kept, removed=removed,
        audit=audit, ledger=ledger, excluded=excluded,
        bridge=bridge, residual_paise=residual, amount_conflicts=amount_conflicts(canonical),
    )


def _write(frame, path):
    frame.to_csv(path, index=False, lineterminator="\n")


def build_numbers(fin, orders_summary, classes, stats, quarterly_df, monthly_df, reason_codes, teams, mode):
    ledger_total = int(fin.ledger["amount_paise"].sum())
    n_quarters = len(quarterly_df)
    raw_naive = int(fin.bridge.iloc[0]["amount_paise"])
    bridge_lines = fin.bridge.copy()
    avg_canonical = ledger_total / n_quarters / 100
    avg_raw = quarterly_df["raw_export_paise"].sum() / n_quarters / 100
    above = quarterly_df[quarterly_df["raw_export_inr"] > 10_000_000]["quarter"].tolist()
    below = quarterly_df[quarterly_df["raw_export_inr"] <= 10_000_000]["quarter"].tolist()
    open_pending = fin.ledger[fin.ledger["status"].isin(["open", "pending"])]
    return {
        "period": {"first_quarter": quarterly_df["quarter"].iloc[0], "last_quarter": quarterly_df["quarter"].iloc[-1], "quarters": n_quarters},
        "data": {
            "raw_rows": len(fin.raw),
            "unique_tickets": len(fin.kept),
            "duplicates_removed": len(fin.removed),
            "duplicates_with_amount": int((fin.removed["amount_paise"] > 0).sum()),
            "duplicate_amount_conflicts": len(fin.amount_conflicts),
            "refund_tickets": len(fin.ledger),
            "excluded_non_refund": len(fin.excluded),
            "quarantined": len(fin.quarantined),
        },
        "canonical": {
            "paise": ledger_total,
            "inr": ledger_total / 100,
            "lakh": ledger_total / 100 / 1e5,
            "avg_per_quarter_inr": round(avg_canonical, 2),
            "avg_per_quarter_lakh": round(avg_canonical / 1e5, 2),
        },
        "raw_export": {
            "naive_sum_inr": raw_naive / 100,
            "crore": raw_naive / 100 / 1e7,
            "avg_per_quarter_inr": round(avg_raw, 2),
            "avg_per_quarter_crore": round(avg_raw / 1e7, 2),
        },
        "reconciliation": {
            "residual_inr": fin.residual_paise / 100,
            "lines": bridge_lines[["step", "rule_id", "rows_with_amount", "amount_inr"]].to_dict("records"),
        },
        "reported_figures": {
            "finance": {
                "stated": "well over a crore a quarter",
                "raw_avg_per_quarter_crore": round(avg_raw / 1e7, 2),
                "quarters_above_one_crore": len(above),
                "quarters_above_one_crore_list": above,
                "first_quarter_below_one_crore": below[0] if below else "none",
            },
            "helpdesk": {
                "stated": "around Rs 11 lakh a quarter",
                "canonical_avg_per_quarter_lakh": round(avg_canonical / 1e5, 2),
                "difference_pct": round((avg_canonical / 1e5 / 11 - 1) * 100, 1),
            },
        },
        "quarterly": quarterly_df[["quarter", "tickets_total", "refund_tickets", "refund_rate", "avg_refund_inr", "canonical_inr", "raw_export_inr"]].to_dict("records"),
        "monthly": monthly_df[["month", "tickets_total", "refund_tickets", "refund_rate", "refund_inr"]].to_dict("records"),
        "reason_code": reason_codes[["refund_reason_code", "refund_tickets", "refund_inr", "share"]].to_dict("records"),
        "teams": teams[["assigned_team", "tier", "tickets_total", "refund_tickets", "refund_rate", "refund_inr", "avg_refund_inr", "share_of_refund_inr"]].to_dict("records"),
        "open_pending": {"tickets": len(open_pending), "inr": int(open_pending["amount_paise"].sum()) / 100},
        "order_integrity": {**{k: v for k, v in orders_summary.items() if k != "over_refund_excess_paise"}, "over_refund_excess_inr": orders_summary["over_refund_excess_paise"] / 100},
        "replacement": {
            "flag_yes": int((classes["replacement_flag"] == "Y").sum()),
            "rules_yes": int((classes["rules_replacement"] == "yes").sum()),
            "final_yes": int((classes["replacement_sent"] == "yes").sum()),
        },
        "ai": {
            "mode": mode,
            "source_counts": stats["source_counts"],
            "model_id": stats["model_id"],
            "prompt_version": stats["prompt_version"],
            "tokens": {k: stats[k] for k in ("prompt_tokens", "output_tokens", "thinking_tokens", "total_tokens", "usage_calls")},
        },
    }


def run(raw_dir=RAW_DIR, output_dir=OUTPUT_DIR, mode="cache", provider=None, cache_path=CACHE_PATH):
    # HOW TO RUN: Use `make run-live` in the terminal to process all tickets with AI.
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # A. LOAD DATA: Read the raw CSV files
    tickets = load_tickets(Path(raw_dir) / "tickets.csv")
    agents = load_csv(Path(raw_dir) / "agents.csv")
    orders = load_csv(Path(raw_dir) / "orders.csv")

    # B. DETERMINISTIC FINANCIAL PIPELINE: Build the pristine ledger first (Code owns the money)
    fin = run_financial(tickets)
    if fin.amount_conflicts:
        raise ValueError(f"duplicate tickets disagree on amount: {fin.amount_conflicts[:5]}")
    _, _, orders_summary = order_integrity(fin.ledger, orders)
    monthly_df = reports.monthly(fin.kept, fin.ledger)
    quarterly_df = reports.quarterly(fin.canonical, fin.kept, fin.ledger)

    _write(fin.ledger[LEDGER_COLUMNS], output_dir / "ledger.csv")
    _write(fin.bridge, output_dir / "bridge.csv")
    if fin.residual_paise != 0:
        raise AssertionError(f"reconciliation residual is {fin.residual_paise} paise; see {output_dir / 'bridge.csv'}")

    # C. AI ENRICHMENT LAYER: Only the clean ledger text is passed to the AI.
    # The AI classifies the tickets. Results are instantly cached to `cache/llm_cache.jsonl` so we don't pay twice.
    text_columns = reasons.TEXT_COLUMNS
    classes, stats = reasons.classify_tickets(fin.ledger[text_columns], mode=mode, provider=provider, cache_path=cache_path)
    
    # D. GENERATE REPORTS: Combine the AI classifications with the financial ledger
    reason_df = reports.reason_table(fin.ledger, classes)
    agent_df = reports.agent_table(fin.ledger, agents)
    teams = reports.team_table(fin.kept, fin.ledger, agents)
    reason_codes = reports.reason_code_summary(fin.ledger)
    dips = reports.double_dip_table(fin.ledger, classes)
    
    total = int(fin.ledger["amount_paise"].sum())
    for name, frame in (("monthly", monthly_df), ("reason", reason_df), ("agent", agent_df), ("team", teams)):
        if int(frame["refund_paise"].sum()) != total:
            raise AssertionError(f"{name} report does not sum to the ledger")
            
    # E. SAVE OUTPUTS: Write the final CSV reports to the outputs/ directory
    _write(reason_df, output_dir / "reason.csv")
    _write(agent_df, output_dir / "agent.csv")
    _write(classes, output_dir / "classifications.csv")
    _write(dips, output_dir / "double_dip_exceptions.csv")
    
    # Generate human review queue for uncertain or unverified AI output
    review_queue = classes[(classes["certainty"] == "low") | (classes["label"] == "UNCERTAIN") | (~classes["evidence_verified"])]
    _write(review_queue, output_dir / "review_queue.csv")

    # F. BOARD PACK: Generate the final presentation metrics
    numbers = build_numbers(fin, orders_summary, classes, stats, quarterly_df, monthly_df, reason_codes, teams, mode)
    (output_dir / "numbers.json").write_text(json.dumps(numbers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "board_pack.md").write_text(board_pack.render(numbers), encoding="utf-8")
    
    print(reasons.summary_line(stats))
    print(f"ledger: {len(fin.ledger):,} refund tickets, INR {total / 100:,.0f}; residual INR {fin.residual_paise / 100:,.0f}; outputs in {output_dir}")
    return {"financials": fin, "classes": classes, "stats": stats, "numbers": numbers}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m src.vireo.pipeline")
    parser.add_argument("--mode", choices=["cache", "live", "rules"], default="cache")
    args = parser.parse_args(argv)
    run(mode=args.mode)


if __name__ == "__main__":
    main()
