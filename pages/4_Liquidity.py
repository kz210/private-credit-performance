import streamlit as st
import plotly.express as px

DATA = st.session_state["DATA"]
facility = DATA["facility"]

st.header("Liquidity, Funding & Headroom")

fig = px.line(facility.sort_values("date"), x="date", y=["drawn","commitment"], title="Facility Drawn vs Commitment")
st.plotly_chart(fig, use_container_width=True)

if {"oc_cushion","ic_cushion"}.issubset(facility.columns):
    fig2 = px.line(facility.sort_values("date"), x="date", y=["oc_cushion","ic_cushion"], title="OC / IC Cushion")
    st.plotly_chart(fig2, use_container_width=True)

st.dataframe(facility.sort_values("date", ascending=False).head(50), use_container_width=True)
