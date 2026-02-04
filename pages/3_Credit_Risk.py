import streamlit as st
import pandas as pd
import plotly.express as px

DATA = st.session_state["DATA"]
positions = DATA["positions"]
risk = DATA["risk"]
asof = DATA["asof"]

st.header("Credit Risk & Asset Quality")

p = positions[positions["asof_date"] == asof].copy()
r = risk[risk["asof_date"] == asof].copy()
pr = p.merge(r, on=["loan_id","asof_date"], how="left")

if "pd_12m" in pr.columns:
    bins = [0, 0.01, 0.03, 0.05, 0.10, 1.0]
    labels = ["0–1%", "1–3%", "3–5%", "5–10%", "10%+"]

    pr["pd_bucket"] = pd.cut(pr["pd_12m"], bins=bins, labels=labels, include_lowest=True)

    fig = px.histogram(pr, x="pd_bucket", y="par", histfunc="sum", title="Par by PD Bucket")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Watchlist / DPD")
wl = pr[(pr["status"].isin(["watchlist","default"])) | (pr["dpd"].fillna(0) >= 30)]
st.dataframe(
    wl[["loan_id","par","sector","rating","dpd","ltv","dscr","pd_12m","lgd"]].sort_values("par", ascending=False),
    use_container_width=True
)
