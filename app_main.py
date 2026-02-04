import streamlit as st
from lib.io import load_all,load_table

st.set_page_config(page_title="Private Credit Portfolio Dashboard", layout="wide", page_icon= ":bar_chart:")

st.title("Private Credit Portfolio Dashboard")

uploaded_file = st.file_uploader("Upload your data file", type=["csv","xlsx","zip"])
if uploaded_file is None:
    st.info("Please upload a data file to proceed, or will consume default data in local")

df = load_table(uploaded_file)
#st.dataframe(df)
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

### run cmd: streamlit run app_main.py --server.fileWatcherType=poll ###
