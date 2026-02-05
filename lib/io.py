from __future__ import annotations

import pandas as pd
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

DATE_COLS = ["asof_date", "date", "pay_date"]

@lru_cache(maxsize=32)
def load_table(name: str) -> pd.DataFrame:
    if not isinstance(name, str) or not name:
        raise ValueError("load_table expects a non-empty table name string")
    xlsx_fp = DATA_DIR / f"{name}.xlsx"
    csv_fp  = DATA_DIR / f"{name}.csv"

    if xlsx_fp.exists():
        df = pd.read_excel(xlsx_fp,engine="openpyxl")
    elif csv_fp.exists():
        df = pd.read_csv(csv_fp)
    else:
        raise FileNotFoundError(f"Missing {name}.xlsx or {name}.csv in {DATA_DIR}")

    # Normalize date columns to midnight (prevents weird microseconds on plots)
    for c in DATE_COLS:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.normalize()

    return df

def load_all():
    positions = load_table("positions")
    cashflows = load_table("cashflows")
    nav = load_table("nav")
    risk = load_table("risk_metrics")
    facility = load_table("facility")
    return positions, cashflows, nav, risk, facility
