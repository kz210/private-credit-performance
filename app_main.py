import streamlit as st
from lib.io import load_all

st.set_page_config(page_title="Private Credit Portfolio Dashboard", layout="wide")

st.title("Private Credit Portfolio Dashboard")

positions, cashflows, nav, risk, facility = load_all()

# global filters (available on all pages)
asof_dates = sorted(positions["asof_date"].dropna().unique())
asof = st.sidebar.selectbox("As-of date", asof_dates, index=len(asof_dates)-1)

st.sidebar.markdown("---")
st.sidebar.caption("Filters applied across pages")

# store in session for pages
st.session_state["DATA"] = {
    "positions": positions,
    "cashflows": cashflows,
    "nav": nav,
    "risk": risk,
    "facility": facility,
    "asof": asof
}

st.info("Use the left sidebar to navigate pages.")
