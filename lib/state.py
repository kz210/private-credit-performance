import streamlit as st
from lib.io import load_all

@st.cache_resource
def _load_data_cached():
    # Loaded once per server process (fast + stable)
    return load_all()

def get_data():
    # Ensure DATA always exists
    if "DATA" not in st.session_state:
        positions, cashflows, nav, risk, facility = _load_data_cached()
        asof_dates = sorted(positions["asof_date"].dropna().unique())
        asof = asof_dates[-1] if asof_dates else None
        st.session_state["DATA"] = {
            "positions": positions,
            "cashflows": cashflows,
            "nav": nav,
            "risk": risk,
            "facility": facility,
            "asof": asof,
        }
    return st.session_state["DATA"]
