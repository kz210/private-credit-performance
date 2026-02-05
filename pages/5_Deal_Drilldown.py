import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from lib.metrics import principal_bridge_for_loan
from lib.state import get_data

DATA = get_data()
#DATA = st.session_state["DATA"]
positions = DATA["positions"]
cashflows = DATA["cashflows"]
risk = DATA["risk"]

st.header("Deal Drilldown")

loan_ids = sorted(positions["loan_id"].unique())
loan_id = st.selectbox("Select loan", loan_ids)

p = positions[positions["loan_id"] == loan_id].sort_values("asof_date")
cf = cashflows[cashflows["loan_id"] == loan_id].sort_values("pay_date")
r = risk[risk["loan_id"] == loan_id].sort_values("asof_date")

latest = p.iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Par", f"{latest['par']:,.0f}")
c2.metric("Status", str(latest.get("status","")))
c3.metric("LTV", f"{latest.get('ltv', float('nan')):.2f}" if "ltv" in latest else "n/a")
c4.metric("DSCR", f"{latest.get('dscr', float('nan')):.2f}" if "dscr" in latest else "n/a")

st.subheader("Par Over Time")
fig_par = px.line(p, x="asof_date", y="par", markers=True)
st.plotly_chart(fig_par, use_container_width=True)

st.subheader("PD (12m) Over Time")
if len(r) == 0 or "pd_12m" not in r.columns:
    st.info("No PD history for this loan.")
else:
    fig_pd = px.line(r, x="asof_date", y="pd_12m", markers=True)
    st.plotly_chart(fig_pd, use_container_width=True)

# --- Principal waterfall ---
st.subheader("Principal Waterfall (Draws vs Repayments)")

min_d = p["asof_date"].min().date()
max_d = p["asof_date"].max().date()
w_start, w_end = st.date_input("Waterfall date range", (min_d, max_d))
w_start, w_end = pd.to_datetime(w_start), pd.to_datetime(w_end)

try:
    br = principal_bridge_for_loan(positions, cashflows, loan_id, w_start, w_end)

    components = ["Start Principal", "Draws", "Amort Repay", "Prepay", "PIK Capitalised", "Residual", "End Principal"]
    values = [
        br["p_start"],
        br["draws"],
        -br["repay"],
        -br["prepay"],
        br["pik"],
        br["residual"],   # makes it reconcile exactly to end snapshot
        br["p_end"],
    ]
    measures = ["absolute","relative","relative","relative","relative","relative","absolute"]

    fig = go.Figure(go.Waterfall(
        x=components,
        y=values,
        measure=measures,
        connector={"line": {"width": 1}},
    ))
    fig.update_layout(title="Outstanding Principal Bridge", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(pd.DataFrame({"component": components, "amount": values}), use_container_width=True)

except Exception as e:
    st.warning(f"Cannot compute waterfall for selected range: {e}")

st.subheader("Cashflows (monthly)")
show_cols = [c for c in [
    "pay_date","interest_cash","interest_pik","principal_draw","principal_repayment","prepayment","fees"
] if c in cf.columns]
st.dataframe(cf[show_cols].tail(200), use_container_width=True)
