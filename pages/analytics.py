"""
pages/analytics.py
Advanced analytics — trends, forecasting, AI insights.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from modules.sheets import get_students, get_expenses, get_revenue
from modules.config import CURRENCY
from utils.finance import monthly_cashflow, forecast_next_month, expense_breakdown


def render():
    st.title("📈 Analytics")

    expenses = get_expenses()
    revenue  = get_revenue()
    students = get_students()

    cashflow = monthly_cashflow(expenses, revenue, months=6)

    # ── Forecast Row ───────────────────────────────────────────────────
    st.subheader("Next Month Forecast")
    f_rev = forecast_next_month(cashflow, "Revenue")
    f_exp = forecast_next_month(cashflow, "Expenses")
    f_prf = f_rev - f_exp

    c1, c2, c3 = st.columns(3)
    c1.metric("📈 Forecast Revenue",  f"{CURRENCY}{f_rev:,.0f}")
    c2.metric("📉 Forecast Expenses", f"{CURRENCY}{f_exp:,.0f}")
    c3.metric("💡 Forecast Profit",   f"{CURRENCY}{f_prf:,.0f}")

    st.divider()

    # ── Cash Flow Trend ────────────────────────────────────────────────
    if not cashflow.empty:
        st.subheader("Cash Flow Trend")
        fig = go.Figure()
        fig.add_scatter(name="Revenue",  x=cashflow["Month"], y=cashflow["Revenue"],
                        fill="tozeroy", line=dict(color="#2563EB"))
        fig.add_scatter(name="Expenses", x=cashflow["Month"], y=cashflow["Expenses"],
                        fill="tozeroy", fillcolor="rgba(239,68,68,.15)",
                        line=dict(color="#EF4444"))
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)",
                          yaxis=dict(gridcolor="rgba(128,128,128,.12)"))
        st.plotly_chart(fig, use_container_width=True)

    # ── Course Enrollment ──────────────────────────────────────────────
    if not students.empty and "Course" in students.columns:
        st.subheader("Enrollment by Course")
        enrollment = students.groupby("Course").size().reset_index(name="Students")
        fig2 = px.bar(enrollment, x="Course", y="Students",
                      color="Students", color_continuous_scale="Blues")
        fig2.update_layout(height=280, showlegend=False,
                           paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Spending Insights ──────────────────────────────────────────────
    st.subheader("💡 AI Spending Insights")
    exp_grp = expense_breakdown(expenses)
    if not exp_grp.empty:
        top_cat = exp_grp.iloc[0]
        top_pct = top_cat["Percentage"]
        st.info(
            f"**{top_cat['Category']}** is your biggest expense at **{top_pct}%** of total spending. "
            f"{'Consider reviewing this category for optimization.' if top_pct > 50 else 'Spending looks balanced across categories.'}"
        )
        if not cashflow.empty:
            recent_profit = cashflow["NetProfit"].iloc[-1]
            prev_profit   = cashflow["NetProfit"].iloc[-2] if len(cashflow) > 1 else recent_profit
            change_pct    = ((recent_profit - prev_profit) / abs(prev_profit) * 100) if prev_profit else 0
            icon = "📈" if change_pct >= 0 else "📉"
            st.info(
                f"{icon} Net profit **{'increased' if change_pct >= 0 else 'decreased'} by {abs(change_pct):.1f}%** "
                f"compared to the previous month."
            )
    else:
        st.info("Add expense data to unlock AI spending insights.")
