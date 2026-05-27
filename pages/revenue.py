import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import date
from modules.sheets import get_revenue, add_revenue
from modules.config import CURRENCY, REVENUE_STREAMS

def render():
    st.title("💰 Revenue Tracking")
    tab_add, tab_list = st.tabs(["➕ Add Revenue", "📋 All Revenue"])
    with tab_add:
        with st.form("add_revenue_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            source   = c1.selectbox("Source *", REVENUE_STREAMS)
            amount   = c2.number_input(f"Amount ({CURRENCY}) *", min_value=0.0, step=100.0)
            rev_date = c1.date_input("Date *", value=date.today())
            desc     = c2.text_input("Description")
            if st.form_submit_button("Add Revenue", type="primary", use_container_width=True):
                if amount <= 0: st.error("Amount must be > 0.")
                else:
                    add_revenue({"date": str(rev_date), "source": source, "description": desc, "amount": amount, "notes": ""})
                    st.success(f"Revenue of {CURRENCY}{amount:,.0f} added!")
    with tab_list:
        revenue = get_revenue()
        if revenue.empty:
            st.info("No revenue yet.")
            return
        total = float(pd.to_numeric(revenue["Amount"], errors="coerce").fillna(0).sum()) if "Amount" in revenue.columns else 0
        c1,c2 = st.columns(2)
        c1.metric("Total Revenue", f"{CURRENCY}{total:,.0f}")
        c2.metric("Transactions", len(revenue))
        if "Source" in revenue.columns:
            grp = revenue.groupby("Source")["Amount"].sum().reset_index()
            fig = px.pie(grp, names="Source", values="Amount", hole=0.6, color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig, use_container_width=True)
        cols = [c for c in ["Date","Source","Description","Amount"] if c in revenue.columns]
        st.dataframe(revenue[cols], use_container_width=True, hide_index=True)
        st.download_button("Export CSV", revenue.to_csv(index=False).encode(), "revenue.csv", "text/csv")