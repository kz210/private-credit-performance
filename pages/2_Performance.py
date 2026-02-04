import streamlit as st
import plotly.graph_objects as go
from lib.metrics import performance_bridge

DATA = st.session_state["DATA"]
cashflows = DATA["cashflows"]
nav = DATA["nav"]

st.header("Performance Attribution")

min_d, max_d = nav["date"].min(), nav["date"].max()
start, end = st.date_input("Date range", (min_d.date(), max_d.date()))
start, end = st.to_datetime(start), st.to_datetime(end)

bridge = performance_bridge(cashflows, nav, start, end)

# Plotly waterfall
measure = ["relative"] * len(bridge)
fig = go.Figure(go.Waterfall(
    name="NAV Bridge",
    x=bridge["component"],
    y=bridge["amount"],
    measure=measure
))
fig.update_layout(title="Return Components (Cash/PIK/Fees/Expenses)", waterfallgap=0.3)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(bridge.sort_values("amount", ascending=False), use_container_width=True)
