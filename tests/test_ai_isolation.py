import json
import re

import pytest

from src.vireo import config as C
from src.vireo.pipeline import run

MONEY_FILES = ["ledger.csv", "bridge.csv"]
USAGE = {"prompt_tokens": 1, "output_tokens": 1, "thinking_tokens": 0, "total_tokens": 2}


def chaotic_provider(prompt):
    labels = C.LABELS + [C.UNCERTAIN]
    pick = labels[sum(map(ord, prompt)) % len(labels)]
    return json.dumps({"reason": pick, "replacement_sent": "yes", "evidence": "x", "certainty": "low"}), USAGE


def broken_provider(prompt):
    raise RuntimeError("provider down")


def test_ledger_bytes_do_not_depend_on_the_ai_layer(tmp_path, no_sleep):
    runs = {
        "rules": dict(mode="rules"),
        "stub": dict(mode="live", provider=chaotic_provider),
        "failure": dict(mode="live", provider=broken_provider),
        "cache_empty": dict(mode="cache"),
    }
    out = {}
    for name, kwargs in runs.items():
        out[name] = tmp_path / name
        run(output_dir=out[name], cache_path=tmp_path / f"{name}.jsonl", **kwargs)

    for filename in MONEY_FILES:
        reference = (out["rules"] / filename).read_bytes()
        for name in runs:
            assert (out[name] / filename).read_bytes() == reference, (filename, name)

    numbers = {name: json.loads((out[name] / "numbers.json").read_text()) for name in runs}
    for name in runs:
        assert {k: v for k, v in numbers[name].items() if k not in ("ai", "replacement")} == {k: v for k, v in numbers["rules"].items() if k not in ("ai", "replacement")}

    assert numbers["stub"]["ai"]["source_counts"] == {"llm": 2340}
    assert numbers["failure"]["ai"]["source_counts"] == {"rules_fallback": 2340}
    assert numbers["rules"]["ai"]["source_counts"] == {"rules": 2340}


def test_default_run_is_offline_and_prints_one_summary_line(tmp_path, no_network, capsys):
    run(output_dir=tmp_path, cache_path=tmp_path / "empty.jsonl", mode="cache")
    lines = [l for l in capsys.readouterr().out.splitlines() if l.startswith("AI:")]
    assert len(lines) == 1 and "cache_misses=2340" in lines[0] and "WARNING" in lines[0]


def test_outputs_have_no_scientific_notation_and_share_of_month_sums_to_one(tmp_path):
    run(output_dir=tmp_path, cache_path=tmp_path / "x.jsonl", mode="rules")
    for name in ("board_pack.md", "numbers.json", "bridge.csv", "reason.csv", "agent.csv"):
        assert not re.search(r"\d[eE][+-]?\d", (tmp_path / name).read_text()), name
    import pandas as pd

    reason = pd.read_csv(tmp_path / "reason.csv")
    assert (reason.groupby("month")["share_of_month"].sum().sub(1).abs() < 0.002).all()
    assert reason["refund_paise"].sum() == pd.read_csv(tmp_path / "ledger.csv")["amount_paise"].sum()
