"""
pages/revenue.py
Revenue tracking — all income streams.
"""
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import date

from modules.sheets import get_revenue, add_revenue
from modules.config import CURRENCY, REVENUE_STREAMS
from utils.finance import revenue_breakdown


def render():
    st.title("💰 Revenue Tracking")

    tab_list, tab_add = st.tabs(["📋 All Revenue", "➕ Add Revenue"])

    with tab_list:
        revenue = get_revenue()

        if not revenue.empty:
            total = revenue["Amount"].sum()
            breakdown = revenue_breakdown(revenue)

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Revenue", f"{CURRENCY}{total:,.0f}")
            c2.metric("Transactions",   len(revenue))
            c3.metric("Top Stream",     breakdown.iloc[0]["Source"] if not breakdown.empty else "—")

            st.divider()

            if not breakdown.empty:
                col_t, col_c = st.columns([1, 1])
                with col_t:
                    st.subheader("By Stream")
                    st.dataframe(
                        breakdown.rename(columns={"Amount": f"Amount ({CURRENCY})", "Percentage": "%"}),
                        use_container_width=True, hide_index=True,
                    )
                with col_c:
                    fig = px.bar(breakdown, x="Source", y="Amount",
                                 color="Source", color_discrete_sequence=px.colors.qualitative.Set2)
                    fig.update_layout(showlegend=False, height=250,
                                      paper_bgcolor="rgba(0,0,0,0)",
                                      plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True)

            st.divider()
            display = ["Date", "Source", "Description", "Amount"]
            display = [c for c in display if c in revenue.columns]
            st.dataframe(revenue[display].sort_values("Date", ascending=False),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No revenue recorded yet.")

    with tab_add:
        st.subheader("Record New Revenue")
        with st.form("add_revenue_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            source  = c1.selectbox("Source *", REVENUE_STREAMS)
            amount  = c2.number_input(f"Amount ({CURRENCY}) *", min_value=0.0, step=100.0)
            rev_date = c1.date_input("Date *", value=date.today())
            desc    = c2.text_input("Description")
            notes   = st.text_area("Notes", height=70)

            if st.form_submit_button("Add Revenue", type="primary", use_container_width=True):
                if amount <= 0:
                    st.error("Amount must be > 0.")
                else:
                    add_revenue({
                        "date": str(rev_date), "source": source,
                        "description": desc, "amount": amount, "notes": notes,
                    })
                    st.success(f"✅ Revenue of {CURRENCY}{amount:,.0f} added!")
