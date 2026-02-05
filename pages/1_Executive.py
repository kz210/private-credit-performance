import streamlit as st
import plotly.express as px
from lib.metrics import portfolio_snapshot

DATA = st.session_state["DATA"]
positions = DATA["positions"]
risk = DATA["risk"]
asof = DATA["asof"]

st.header("Executive Summary")

snap = portfolio_snapshot(positions, risk, asof)
util = snap["utilisation"]
st.metric("Utilisation", f"{100*util:.1f}%" if util==util else "n/a")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Loans", snap["num_loans"])
c2.metric("Par", f"{snap['par']:,.0f}")
c3.metric("Model/MV", f"{snap['mv']:,.0f}")
c4.metric("Watchlist %", f"{100*snap['watchlist_pct']:.2f}%")
c5.metric("DPD 30+ %", f"{100*snap['dpd_30_plus_pct']:.2f}%")

c6, c7, c8 = st.columns(3)
c6.metric("WA PD (12m)", f"{100*snap['wa_pd_12m']:.2f}%" if snap["wa_pd_12m"]==snap["wa_pd_12m"] else "n/a")
c7.metric("WA LGD", f"{100*snap['wa_lgd']:.2f}%" if snap["wa_lgd"]==snap["wa_lgd"] else "n/a")
c8.metric("Expected Loss", f"{snap['el']:,.0f}" if snap["el"]==snap["el"] else "n/a")

# concentration example
p = positions[positions["asof_date"] == asof].copy()
fig = px.bar(
    p.groupby("sector", as_index=False)["par"].sum().sort_values("par", ascending=False).head(12),
    x="sector", y="par", title="Top Sectors by Par"
)
st.plotly_chart(fig, use_container_width=True)
