import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
DATA = st.session_state["DATA"]
positions = DATA["positions"]
cashflows = DATA["cashflows"]
risk = DATA["risk"]

st.header("Deal Drilldown")

loan_ids = sorted(positions["loan_id"].unique())
loan_id = st.selectbox("Select loan", loan_ids)

p = positions[positions["loan_id"] == loan_id].sort_values("asof_date")
cf = cashflows[cashflows["loan_id"] == loan_id].sort_values("pay_date")
r = risk[risk["loan_id"] == loan_id].sort_values("asof_date")

c1, c2, c3, c4 = st.columns(4)
latest = p.iloc[-1]
c1.metric("Par", f"{latest['par']:,.0f}")
c2.metric("Status", str(latest.get("status","")))
c3.metric("LTV", f"{latest.get('ltv', float('nan')):.2f}" if "ltv" in latest else "n/a")
c4.metric("DSCR", f"{latest.get('dscr', float('nan')):.2f}" if "dscr" in latest else "n/a")

if "asof_date" in p.columns and "par" in p.columns:
    #st.plotly_chart(px.line(p, x="asof_date", y="par", title="Par Over Time"), use_container_width=True)
    st.subheader("Par Over Time")
    if len(p) >= 2:
        fig = px.line(p, x="asof_date", y="par", markers=True)
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=p["asof_date"], y=p["par"], mode="markers"))
        fig.update_layout(title="Par Over Time (single snapshot)")
    st.plotly_chart(fig, use_container_width=True)
if "asof_date" in r.columns and "pd_12m" in r.columns:
    #st.plotly_chart(px.line(r, x="asof_date", y="pd_12m", title="PD (12m) Over Time"), use_container_width=True)
    st.subheader("PD (12m) Over Time")
    if len(r) == 0:
        st.info("No risk history for this loan.")
    elif len(r) >= 2:
        fig = px.line(r, x="asof_date", y="pd_12m", markers=True)
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=r["asof_date"], y=r["pd_12m"], mode="markers"))
        fig.update_layout(title="PD (12m) Over Time (single snapshot)")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Cashflows")
st.dataframe(cf.tail(200), use_container_width=True)
