"""
pages/pnl.py
Profit & Loss Statement — multi-month comparison table.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from modules.sheets import get_expenses, get_revenue
from modules.config import CURRENCY
from utils.finance import monthly_cashflow, monthly_summary, expense_breakdown, revenue_breakdown


def render():
    st.title("📑 P&L Statement")

    col1, col2 = st.columns(2)
    months = col1.slider("Months to show", 3, 12, 6)

    expenses = get_expenses()
    revenue  = get_revenue()

    cashflow = monthly_cashflow(expenses, revenue, months=months)

    if cashflow.empty:
        st.info("No data yet. Add expenses and revenue to see your P&L.")
        return

    # ── Chart ──────────────────────────────────────────────────────────
    fig = go.Figure()
    fig.add_bar(name="Revenue",   x=cashflow["Month"], y=cashflow["Revenue"],   marker_color="#2563EB")
    fig.add_bar(name="Expenses",  x=cashflow["Month"], y=cashflow["Expenses"],  marker_color="#EF4444")
    fig.add_scatter(name="Net Profit", x=cashflow["Month"], y=cashflow["NetProfit"],
                    mode="lines+markers", line=dict(color="#10B981", width=2.5),
                    marker=dict(size=6))
    fig.update_layout(
        barmode="group", height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="rgba(128,128,128,.12)"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Table ──────────────────────────────────────────────────────────
    st.subheader("Summary Table")
    display = cashflow.copy()
    for col in ["Revenue", "Expenses", "NetProfit"]:
        if col in display.columns:
            display[col] = display[col].apply(lambda v: f"{CURRENCY}{v:,.0f}")

    st.dataframe(display, use_container_width=True, hide_index=True)

    # ── Export ─────────────────────────────────────────────────────────
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        cashflow.to_excel(writer, sheet_name="PnL", index=False)
    st.download_button("⬇️ Export Excel", buf.getvalue(), "pnl_statement.xlsx")
