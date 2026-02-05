import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from lib.metrics import performance_bridge
from lib.state import get_data

DATA = get_data()
#DATA = st.session_state["DATA"]
cashflows = DATA["cashflows"]
nav = DATA["nav"]

st.header("Performance Attribution")

min_d, max_d = nav["date"].min(), nav["date"].max()
start, end = st.date_input("Date range", (min_d.date(), max_d.date()))

start, end = pd.to_datetime(start), pd.to_datetime(end)

bridge = performance_bridge(cashflows, nav, start, end)

fig = go.Figure(go.Waterfall(
    name="NAV Bridge",
    x=bridge["component"],
    y=bridge["amount"],
    measure=["relative"] * len(bridge),
))
fig.update_layout(title="Return Components (Cash/PIK/Fees/Expenses)", waterfallgap=0.3)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(bridge.sort_values("amount", ascending=False), use_container_width=True)
