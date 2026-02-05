from __future__ import annotations
import pandas as pd
import numpy as np
def facility_yield_snapshot(
    facility: pd.DataFrame,
    cashflows: pd.DataFrame,
    asof: pd.Timestamp,
    facility_margin_bps: float = 250.0,   # input (bank margin over base)
    undrawn_fee_bps: float = 50.0,        # input
    day_count: int = 360,
) -> dict:
    """
    Returns both:
      (1) Lender facility yield (needs margin + undrawn fee inputs)
      (2) Borrower net carry (uses asset interest from cashflows minus funding cost)

    Assumptions:
      - cashflows has monthly interest_cash + interest_pik (asset income proxy)
      - facility has drawn, commitment, cost_of_funds (funding/base proxy)
      - uses last available facility row with date <= asof
      - annualizes using trailing 30-day cashflow at asof (simple, consistent with our monthly synthetic data)
    """
    f = facility.sort_values("date")
    f_asof = f[f["date"] <= asof].iloc[-1] if (f["date"] <= asof).any() else f.iloc[-1]

    drawn = float(f_asof["drawn"])
    commitment = float(f_asof["commitment"])
    undrawn = max(0.0, commitment - drawn)

    # funding/base rate proxy (annual)
    base = float(f_asof.get("cost_of_funds", np.nan))  # we treat as base/funding proxy

    # trailing month asset income (cash + PIK) at asof date
    cf_m = cashflows[cashflows["pay_date"] == asof].copy()
    asset_income_month = float(cf_m.get("interest_cash", 0).sum() + cf_m.get("interest_pik", 0).sum())
    asset_income_annual = asset_income_month * 12.0  # simple annualization for monthly data

    # (A) Lender facility yield (annual)
    margin = facility_margin_bps / 10_000.0
    undrawn_fee = undrawn_fee_bps / 10_000.0
    facility_rate_drawn = (base if base == base else 0.0) + margin

    lender_income_annual = drawn * facility_rate_drawn + undrawn * undrawn_fee
    lender_yield_on_drawn = lender_income_annual / drawn if drawn > 0 else np.nan
    lender_yield_on_commitment = lender_income_annual / commitment if commitment > 0 else np.nan

    # (B) Borrower net carry (annual)
    funding_cost_annual = drawn * (base if base == base else 0.0)
    net_carry_annual = asset_income_annual - funding_cost_annual
    net_carry_yield_on_drawn = net_carry_annual / drawn if drawn > 0 else np.nan

    return {
        "drawn": drawn,
        "commitment": commitment,
        "undrawn": undrawn,
        "base_or_funding_rate": base,
        "asset_income_annual": asset_income_annual,

        "lender_income_annual": lender_income_annual,
        "lender_yield_on_drawn": lender_yield_on_drawn,
        "lender_yield_on_commitment": lender_yield_on_commitment,

        "funding_cost_annual": funding_cost_annual,
        "net_carry_annual": net_carry_annual,
        "net_carry_yield_on_drawn": net_carry_yield_on_drawn,
    }
def borrowing_base_snapshot(positions: pd.DataFrame, asof: pd.Timestamp) -> dict:
    p = positions[positions["asof_date"] == asof].copy()
    if p.empty:
        return {"borrowing_base": float("nan"), "eligible_collateral": float("nan")}

    # Respect eligibility if present
    if "eligible_flag" in p.columns:
        p = p[p["eligible_flag"] == 1]

    # Prefer stored (audited) fields
    if {"eligible_collateral","borrowing_base_contrib"}.issubset(p.columns):
        return {
            "eligible_collateral": float(p["eligible_collateral"].sum()),
            "borrowing_base": float(p["borrowing_base_contrib"].sum()),  # gross BB
        }

    # Fallback compute
    req = {"collateral_mv","haircut_pct","advance_rate_pct"}
    if not req.issubset(p.columns):
        return {"borrowing_base": float("nan"), "eligible_collateral": float("nan")}

    p["eligible_collateral"] = p["collateral_mv"] * (1 - p["haircut_pct"])
    p["bb_contrib"] = p["eligible_collateral"] * p["advance_rate_pct"]

    return {
        "eligible_collateral": float(p["eligible_collateral"].sum()),
        "borrowing_base": float(p["bb_contrib"].sum()),
    }

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
