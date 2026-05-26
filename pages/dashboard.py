"""
pages/dashboard.py
Finance Dashboard — KPIs, charts, recent transactions.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

from modules.sheets import get_students, get_expenses, get_revenue
from utils.finance import (
    monthly_summary, pending_collections,
    expense_breakdown, monthly_cashflow, forecast_next_month,
)
from modules.config import CURRENCY


def render():
    st.title("📊 Finance Dashboard")
    st.caption(f"Academic Year 2024–25 · {datetime.today().strftime('%B %Y')}")

    # ── Load data ──────────────────────────────────────────────────────
    with st.spinner("Loading data…"):
        students = get_students()
        expenses = get_expenses()
        revenue  = get_revenue()

    month   = datetime.today().strftime("%Y-%m")
    summary = monthly_summary(expenses, revenue, month)
    pending = pending_collections(students)

    # ── KPI Row ────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Revenue",
                  f"{CURRENCY}{summary['total_revenue']:,.0f}",
                  delta="+12.4%")
    with c2:
        st.metric("Total Expenses",
                  f"{CURRENCY}{summary['total_expenses']:,.0f}",
                  delta="+3.1%", delta_color="inverse")
    with c3:
        st.metric("Net Profit",
                  f"{CURRENCY}{summary['net_profit']:,.0f}",
                  delta=f"{summary['profit_margin']:.1f}% margin")
    with c4:
        st.metric("Pending Collections",
                  f"{CURRENCY}{pending['total']:,.0f}",
                  delta=f"{pending['count']} students",
                  delta_color="off")

    st.divider()

    # ── Charts ─────────────────────────────────────────────────────────
    col_left, col_right = st.columns([1.6, 1])

    with col_left:
        st.subheader("Revenue vs Expenses")
        cashflow = monthly_cashflow(expenses, revenue, months=6)
        if not cashflow.empty:
            fig = go.Figure()
            fig.add_bar(name="Revenue",  x=cashflow["Month"], y=cashflow["Revenue"],
                        marker_color="#2563EB")
            fig.add_bar(name="Expenses", x=cashflow["Month"], y=cashflow["Expenses"],
                        marker_color="#EF4444")
            fig.update_layout(
                barmode="group", height=300,
                margin=dict(l=0, r=0, t=20, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="rgba(128,128,128,.15)"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet — add expenses and revenue entries.")

    with col_right:
        st.subheader("Expense Breakdown")
        exp_grp = expense_breakdown(expenses)
        if not exp_grp.empty:
            fig2 = px.pie(
                exp_grp, names="Category", values="Amount",
                hole=0.65,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig2.update_layout(
                height=300, margin=dict(l=0, r=0, t=20, b=0),
                showlegend=True,
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(font_size=11),
            )
            fig2.update_traces(textinfo="percent", hovertemplate="%{label}: %{value:,.0f}")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No expense data yet.")

    st.divider()

    # ── Forecast banner ────────────────────────────────────────────────
    cashflow = monthly_cashflow(expenses, revenue, months=6)
    if not cashflow.empty:
        next_rev = forecast_next_month(cashflow, "Revenue")
        next_exp = forecast_next_month(cashflow, "Expenses")
        fa, fb, fc = st.columns(3)
        fa.metric("📈 Forecast Revenue (next mo.)", f"{CURRENCY}{next_rev:,.0f}")
        fb.metric("📉 Forecast Expenses",           f"{CURRENCY}{next_exp:,.0f}")
        fc.metric("💡 Forecast Profit",             f"{CURRENCY}{next_rev - next_exp:,.0f}")
        st.divider()

    # ── Recent Transactions ────────────────────────────────────────────
    st.subheader("Recent Transactions")
    _render_recent_transactions(expenses, revenue)


def _render_recent_transactions(expenses: pd.DataFrame, revenue: pd.DataFrame):
    rows = []
    if not expenses.empty:
        for _, r in expenses.tail(10).iterrows():
            rows.append({
                "Date":        str(r.get("Date", ""))[:10],
                "Description": r.get("Description", ""),
                "Type":        "Expense",
                "Category":    r.get("Category", ""),
                "Amount":      f"-{CURRENCY}{r.get('Amount', 0):,.0f}",
            })
    if not revenue.empty:
        for _, r in revenue.tail(10).iterrows():
            rows.append({
                "Date":        str(r.get("Date", ""))[:10],
                "Description": r.get("Description", ""),
                "Type":        "Revenue",
                "Category":    r.get("Source", ""),
                "Amount":      f"+{CURRENCY}{r.get('Amount', 0):,.0f}",
            })

    if rows:
        df = pd.DataFrame(rows).sort_values("Date", ascending=False).head(15)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet. Add expenses or revenue entries to get started.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Expense", use_container_width=True):
            st.session_state["page"] = "expenses"
            st.rerun()
    with col2:
        if st.button("💰 Add Revenue", use_container_width=True):
            st.session_state["page"] = "revenue"
            st.rerun()
