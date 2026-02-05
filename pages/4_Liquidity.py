import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from lib.metrics import borrowing_base_snapshot, facility_yield_snapshot
from lib.state import get_data

DATA = get_data()
positions = DATA["positions"]
cashflows = DATA["cashflows"]
facility = DATA["facility"]
asof = DATA["asof"]

st.header("Liquidity, Funding & Borrowing Base")

# -----------------------------
# Borrowing base snapshot
# -----------------------------
bb = borrowing_base_snapshot(positions, asof)

f = facility.sort_values("date").copy()
f_asof = f[f["date"] <= asof].iloc[-1] if (f["date"] <= asof).any() else f.iloc[-1]

drawn = float(f_asof["drawn"])
commitment = float(f_asof["commitment"])
undrawn = max(0.0, commitment - drawn)

# Prefer facility’s stored BB net/headroom if present (audit-friendly)
if {"borrowing_base_net", "headroom", "margin_call"}.issubset(f_asof.index):
    borrowing_base_net = float(f_asof["borrowing_base_net"])
    headroom = float(f_asof["headroom"])
    margin_call = float(f_asof["margin_call"])
else:
    # Fallback if facility file doesn't contain net BB fields
    borrowing_base_net = float(bb["borrowing_base"])
    headroom = borrowing_base_net - drawn if borrowing_base_net == borrowing_base_net else np.nan
    margin_call = max(0.0, drawn - borrowing_base_net) if borrowing_base_net == borrowing_base_net else np.nan

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Drawn", f"{drawn:,.0f}")
c2.metric("Commitment", f"{commitment:,.0f}")
c3.metric("Undrawn", f"{undrawn:,.0f}")
c4.metric("Borrowing Base (Net)", f"{borrowing_base_net:,.0f}" if borrowing_base_net == borrowing_base_net else "n/a")
c5.metric("Headroom", f"{headroom:,.0f}" if headroom == headroom else "n/a")

if margin_call == margin_call and margin_call > 0:
    st.error(f"⚠️ Margin call required: {margin_call:,.0f}")

st.caption("Borrowing base is driven by eligible collateral × advance rate minus reserves. Headroom = BB(net) − Drawn.")

# -----------------------------
# Time series charts
# -----------------------------
st.subheader("Funding & Borrowing Base Over Time")

# If facility has these, plot them directly. Otherwise compute BB series from positions.
if {"borrowing_base_net", "headroom"}.issubset(f.columns):
    ts = f[["date", "drawn", "borrowing_base_net", "headroom"]].copy()
    ts = ts.rename(columns={"borrowing_base_net": "borrowing_base"})
else:
    asof_list = sorted(positions["asof_date"].dropna().unique())
    bb_ts = []
    for d in asof_list:
        b = borrowing_base_snapshot(positions, d)
        bb_ts.append([d, b["borrowing_base"], b["eligible_collateral"]])
    bb_ts = pd.DataFrame(bb_ts, columns=["date", "borrowing_base", "eligible_collateral"])
    ts = f.merge(bb_ts[["date", "borrowing_base"]], on="date", how="left")
    ts["headroom"] = ts["borrowing_base"] - ts["drawn"]

fig1 = px.line(ts, x="date", y=["drawn", "borrowing_base"], title="Drawn vs Borrowing Base")
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.line(ts, x="date", y="headroom", title="Headroom Over Time")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Facility yield & net carry
# -----------------------------
st.subheader("Facility Yield & Net Carry")

with st.sidebar.expander("Facility pricing inputs", expanded=False):
    fac_margin_bps = st.number_input("Facility margin (bps)", min_value=0.0, max_value=2000.0, value=250.0, step=25.0)
    undrawn_fee_bps = st.number_input("Undrawn fee (bps)", min_value=0.0, max_value=500.0, value=50.0, step=5.0)

y = facility_yield_snapshot(
    facility=facility,
    cashflows=cashflows,
    asof=asof,
    facility_margin_bps=fac_margin_bps,
    undrawn_fee_bps=undrawn_fee_bps
)

d1, d2, d3, d4 = st.columns(4)
d1.metric(
    "Lender yield (on drawn)",
    f"{100*y['lender_yield_on_drawn']:.2f}%" if y["lender_yield_on_drawn"] == y["lender_yield_on_drawn"] else "n/a"
)
d2.metric(
    "Lender yield (on commitment)",
    f"{100*y['lender_yield_on_commitment']:.2f}%" if y["lender_yield_on_commitment"] == y["lender_yield_on_commitment"] else "n/a"
)
d3.metric(
    "Net carry yield (on drawn)",
    f"{100*y['net_carry_yield_on_drawn']:.2f}%" if y["net_carry_yield_on_drawn"] == y["net_carry_yield_on_drawn"] else "n/a"
)
d4.metric(
    "Funding/base proxy (cost_of_funds)",
    f"{100*y['base_or_funding_rate']:.2f}%" if y["base_or_funding_rate"] == y["base_or_funding_rate"] else "n/a"
)

with st.expander("Details (annualized, simplified)"):
    st.write(
        {
            "asset_income_annual": y["asset_income_annual"],
            "funding_cost_annual": y["funding_cost_annual"],
            "net_carry_annual": y["net_carry_annual"],
            "lender_income_annual": y["lender_income_annual"],
            "drawn": y["drawn"],
            "undrawn": y["undrawn"],
        }
    )

st.caption(
    "Net carry uses trailing-month collateral interest (cash + PIK) annualized ×12 minus funding cost on drawn. "
    "Lender yield assumes facility rate = cost_of_funds + margin, plus undrawn fee on unused commitment."
)

# -----------------------------
# Collateral composition (optional but useful)
# -----------------------------
st.subheader("Collateral & Eligibility (As-of)")

p_asof = positions[positions["asof_date"] == asof].copy()
cols = [c for c in [
    "loan_id","par","status","dpd",
    "collateral_mv","haircut_pct","advance_rate_pct","eligible_flag",
    "eligible_collateral","borrowing_base_contrib"
] if c in p_asof.columns]

st.dataframe(
    p_asof[cols].sort_values("par", ascending=False),
    use_container_width=True
)
