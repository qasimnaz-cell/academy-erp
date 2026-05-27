import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta
from modules.sheets import get_expenses, get_revenue
from modules.config import CURRENCY

def render():
    st.title("📑 P&L Statement")
    expenses = get_expenses()
    revenue  = get_revenue()
    if expenses.empty and revenue.empty:
        st.info("No data yet.")
        return
    rows = []
    for i in range(5,-1,-1):
        d = datetime.today().replace(day=1) - timedelta(days=i*28)
        m = d.strftime("%Y-%m")
        rv = 0
        if not revenue.empty and "Date" in revenue.columns and "Amount" in revenue.columns:
            r2 = revenue.copy(); r2["Date"] = pd.to_datetime(r2["Date"], errors="coerce")
            rv = float(pd.to_numeric(r2[r2["Date"].dt.strftime("%Y-%m")==m]["Amount"], errors="coerce").fillna(0).sum())
        ev = 0
        if not expenses.empty and "Date" in expenses.columns and "Amount" in expenses.columns:
            e2 = expenses.copy(); e2["Date"] = pd.to_datetime(e2["Date"], errors="coerce")
            ev = float(pd.to_numeric(e2[e2["Date"].dt.strftime("%Y-%m")==m]["Amount"], errors="coerce").fillna(0).sum())
        rows.append({"Month": d.strftime("%b %Y"), "Revenue": rv, "Expenses": ev, "Net Profit": rv-ev, "Margin": f"{(rv-ev)/rv*100:.1f}%" if rv else "0%"})
    df = pd.DataFrame(rows)
    fig = go.Figure()
    fig.add_bar(name="Revenue", x=df["Month"], y=df["Revenue"], marker_color="#2563EB")
    fig.add_bar(name="Expenses", x=df["Month"], y=df["Expenses"], marker_color="#EF4444")
    fig.add_scatter(name="Net Profit", x=df["Month"], y=df["Net Profit"], mode="lines+markers", line=dict(color="#10B981", width=2.5))
    fig.update_layout(barmode="group", height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=10,b=0), yaxis=dict(gridcolor="rgba(128,128,128,.1)"), legend=dict(orientation="h",y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    st.divider()
    display = df.copy()
    for col in ["Revenue","Expenses","Net Profit"]:
        display[col] = display[col].apply(lambda v: f"{CURRENCY}{v:,.0f}")
    st.dataframe(display, use_container_width=True, hide_index=True)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w: df.to_excel(w, index=False, sheet_name="PnL")
    st.download_button("Export Excel", buf.getvalue(), "pnl.xlsx")