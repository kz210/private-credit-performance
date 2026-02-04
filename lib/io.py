from __future__ import annotations
import pandas as pd
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@lru_cache(maxsize=32)
def load_table(name: str) -> pd.DataFrame:
    fp = DATA_DIR / f"{name}.xlsx"
    df = pd.read_excel(fp, engine="openpyxl")
    # normalize dates
    for c in ["asof_date", "date", "pay_date"]:
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
