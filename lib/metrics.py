from __future__ import annotations

import pandas as pd
import numpy as np

def wa(df: pd.DataFrame, value_col: str, weight_col: str) -> float:
    w = df[weight_col].astype(float)
    v = df[value_col].astype(float)
    s = w.sum()
    if s == 0:
        return float("nan")
    return float((v * w).sum() / s)

def portfolio_snapshot(positions: pd.DataFrame, risk: pd.DataFrame, asof: pd.Timestamp) -> dict:
    p = positions[positions["asof_date"] == asof].copy()
    r = risk[risk["asof_date"] == asof].copy()
    pr = p.merge(r, on=["loan_id", "asof_date"], how="left")

    par = float(pr["par"].sum()) if "par" in pr.columns else 0.0
    mv = float(pr.get("market_value", pr["par"]).sum()) if len(pr) else 0.0

    out = {
        "num_loans": int(pr["loan_id"].nunique()) if len(pr) else 0,
        "par": par,
        "mv": mv,
        "watchlist_pct": float(pr["par"].where(pr["status"].eq("watchlist"), 0).sum() / par) if par else 0.0,
        "dpd_30_plus_pct": float(pr["par"].where(pr["dpd"].fillna(0) >= 30, 0).sum() / par) if par else 0.0,
        "wa_pd_12m": wa(pr, "pd_12m", "ead") if {"pd_12m","ead"}.issubset(pr.columns) else np.nan,
        "wa_lgd": wa(pr, "lgd", "ead") if {"lgd","ead"}.issubset(pr.columns) else np.nan,
    }

    if {"pd_12m","lgd","ead"}.issubset(pr.columns):
        out["el"] = float((pr["pd_12m"] * pr["lgd"] * pr["ead"]).sum())
    else:
        out["el"] = np.nan

    # Optional: utilisation if commitment/undrawn exists
    if "commitment" in pr.columns:
        comm = float(pr["commitment"].sum())
        out["utilisation"] = float(par / comm) if comm else np.nan
    else:
        out["utilisation"] = np.nan

    return out

def performance_bridge(cashflows: pd.DataFrame, nav: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    cf = cashflows[(cashflows["pay_date"] >= start) & (cashflows["pay_date"] <= end)].copy()
    navw = nav[(nav["date"] >= start) & (nav["date"] <= end)].copy()

    bridge = {
        "Cash Interest": float(cf.get("interest_cash", 0).sum()),
        "PIK Accrual": float(cf.get("interest_pik", 0).sum()),
        "Fees (Loan)": float(cf.get("fees", 0).sum()),
        "Mgmt Fees": float(navw.get("fees", 0).sum()),
        "Expenses": float(navw.get("expenses", 0).sum()),
    }
    return pd.DataFrame({"component": list(bridge.keys()), "amount": list(bridge.values())})

def principal_bridge_for_loan(
    positions: pd.DataFrame,
    cashflows: pd.DataFrame,
    loan_id: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict:
    """
    Computes start/end principal and principal flows in (start, end] window.
    Uses:
      cashflows: principal_draw, principal_repayment, prepayment, interest_pik
      positions: par snapshots
    """
    p_loan = positions[positions["loan_id"] == loan_id].sort_values("asof_date")
    if p_loan.empty:
        raise ValueError(f"No positions for {loan_id}")

    # Align start/end to available snapshots
    p_start_series = p_loan[p_loan["asof_date"] <= start]["par"]
    p_end_series = p_loan[p_loan["asof_date"] <= end]["par"]
    if p_start_series.empty or p_end_series.empty:
        raise ValueError("Selected range is outside available position dates")

    p_start = float(p_start_series.iloc[-1])
    p_end = float(p_end_series.iloc[-1])

    cf = cashflows[
        (cashflows["loan_id"] == loan_id) &
        (cashflows["pay_date"] > start) &
        (cashflows["pay_date"] <= end)
    ].copy()

    draws = float(cf.get("principal_draw", 0).sum())
    repay = float(cf.get("principal_repayment", 0).sum())
    prepay = float(cf.get("prepayment", 0).sum())
    pik = float(cf.get("interest_pik", 0).sum())  # treated as capitalised PIK in our synthetic data

    # "explained" end (may differ slightly if timing mismatches)
    explained_end = p_start + draws - repay - prepay + pik
    residual = p_end - explained_end

    return dict(
        p_start=p_start, p_end=p_end,
        draws=draws, repay=repay, prepay=prepay, pik=pik,
        explained_end=explained_end, residual=residual
    )
