from pathlib import Path

import pandas as pd


def load_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def load_tickets(path):
    df = load_csv(path)
    df["source_file"] = Path(path).name
    df["source_row"] = range(2, len(df) + 2)
    return df
