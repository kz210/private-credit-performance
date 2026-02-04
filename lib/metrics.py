from __future__ import annotations
import pandas as pd
import numpy as np

def wa(df: pd.DataFrame, value_col: str, weight_col: str) -> float:
    w = df[weight_col].astype(float)
    v = df[value_col].astype(float)
    if w.sum() == 0:
        return float("nan")
    return float((v * w).sum() / w.sum())

def portfolio_snapshot(positions: pd.DataFrame, risk: pd.DataFrame, asof: pd.Timestamp) -> dict:
    p = positions[positions["asof_date"] == asof].copy()
    r = risk[risk["asof_date"d","asof_date"], how="left")

    out = {}
    out["num_loans"] = int(pr["loan_id"].nunique())
    out["par"] = float(pr["par"].sum())
    out["mv"] = float(pr.get("market_value", pr["par"]).sum())
    out["wa_pd_12m"] = wa(pr, "pd_12m", "ead") if "pd_12m" in pr.columns and "ead" in pr.columns else np.nan
    out["wa_lgd"] = wa(pr, "lgd", "ead") if "lgd" in pr.columns and "ead" in pr.columns else np.nan
    if {"pd_12m","lgd","ead"}.issubset(pr.columns):
        out["el"] = float((pr["pd_12m"] * pr["lgd"] * pr["ead"]).sum())
    else:
        out["el"] = np.nan

    out["watchlist_pct"] = float((pr["par"].where(pr["status"].eq("watchlist"), 0).sum()) / out["par"]) if out["par"] else 0.0
    out["dpd_30_plus_pct"] = float((pr["par"].where(pr["dpd"].fillna(0) >= 30, 0).sum()) / out["par"]) if out["par"] else 0.0
    return out

def performance_bridge(cashflows: pd.DataFrame, nav: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    cf = cashflows[(cashflows["pay_date"] >= start) & (cashflows["pay_date"] <= end)].copy()
    bridge = {
        "Cash Interest": cf.get("interest_cash", pd.Series(dtype=float)).sum(),
        "PIK Accrual": cf.get("interest_pik", pd.Series(dtype=float)).sum(),
        "Fees": cf.get("fees", pd.Series(dtype=float)).sum(),
        "Principal": cf.get("pr] == asof].copy()
    pr = p.merge(r, on=["loan_iincipal", pd.Series(dtype=float)).sum(),
    }
    # fund-level fees/expenses if present
    navw = nav[(nav["date"] >= start) & (nav["date"] <= end)].copy()
    bridge["Mgmt Fees"] = navw.get("fees", pd.Series(dtype=float)).sum()
    bridge["Expenses"] = navw.get("expenses", pd.Series(dtype=float)).sum()

    df = pd.DataFrame({"component": list(bridge.keys()), "amount": list(bridge.values())})
    return df
