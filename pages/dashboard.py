import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from modules.sheets import get_students, get_expenses, get_revenue
from modules.config import CURRENCY

def safe_sum(df, col):
    if df.empty or col not in df.columns: return 0.0
    return float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum())

def render():
    st.title("📊 Finance Dashboard")
    st.caption(f"Academic Year 2024-25 · {datetime.today().strftime('%B %Y')}")
    expenses = get_expenses()
    revenue  = get_revenue()
    students = get_students()
    total_rev = safe_sum(revenue, "Amount")
    total_exp = safe_sum(expenses, "Amount")
    net = total_rev - total_exp
    pending = 0
    pending_count = 0
    if not students.empty and "Balance" in students.columns:
        ov = students[pd.to_numeric(students["Balance"], errors="coerce").fillna(0) > 0]
        pending = float(pd.to_numeric(ov["Balance"], errors="coerce").fillna(0).sum())
        pending_count = len(ov)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Revenue", f"{CURRENCY}{total_rev:,.0f}")
    c2.metric("Total Expenses", f"{CURRENCY}{total_exp:,.0f}")
    c3.metric("Net Profit", f"{CURRENCY}{net:,.0f}")
    c4.metric("Pending Fees", f"{CURRENCY}{pending:,.0f}", f"{pending_count} students", delta_color="off")
    st.divider()
    if not expenses.empty or not revenue.empty:
        months, rv_list, ev_list = [], [], []
        for i in range(5,-1,-1):
            d = (datetime.today().replace(day=1) - timedelta(days=i*28))
            m = d.strftime("%Y-%m")
            months.append(d.strftime("%b"))
            rv = 0
            if not revenue.empty and "Date" in revenue.columns and "Amount" in revenue.columns:
                r2 = revenue.copy(); r2["Date"] = pd.to_datetime(r2["Date"], errors="coerce")
                rv = float(pd.to_numeric(r2[r2["Date"].dt.strftime("%Y-%m")==m]["Amount"], errors="coerce").fillna(0).sum())
            ev = 0
            if not expenses.empty and "Date" in expenses.columns and "Amount" in expenses.columns:
                e2 = expenses.copy(); e2["Date"] = pd.to_datetime(e2["Date"], errors="coerce")
                ev = float(pd.to_numeric(e2[e2["Date"].dt.strftime("%Y-%m")==m]["Amount"], errors="coerce").fillna(0).sum())
            rv_list.append(rv); ev_list.append(ev)
        col1, col2 = st.columns([3,2])
        with col1:
            st.subheader("Revenue vs Expenses")
            fig = go.Figure()
            fig.add_bar(name="Revenue", x=months, y=rv_list, marker_color="#2563EB")
            fig.add_bar(name="Expenses", x=months, y=ev_list, marker_color="#EF4444")
            fig.update_layout(barmode="group", height=280, margin=dict(l=0,r=0,t=10,b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h",y=1.1), yaxis=dict(gridcolor="rgba(128,128,128,.1)"))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Expense Breakdown")
            if not expenses.empty and "Category" in expenses.columns:
                grp = expenses.groupby("Category")["Amount"].sum().reset_index()
                fig2 = px.pie(grp, names="Category", values="Amount", hole=0.6,
                    color_discrete_sequence=px.colors.qualitative.Set2)
                fig2.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0),
                    paper_bgcolor="rgba(0,0,0,0)", showlegend=True, legend=dict(font_size=11))
                fig2.update_traces(textinfo="percent")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Add expenses to see breakdown.")
    else:
        st.info("No data yet. Start by adding expenses and revenue.")
    st.divider()
    st.subheader("Recent Transactions")
    rows = []
    if not expenses.empty:
        for _, r in expenses.tail(5).iterrows():
            rows.append({"Date": str(r.get("Date",""))[:10], "Description": r.get("Description",""), "Type": "Expense", "Amount": f"-{CURRENCY}{r.get('Amount',0):,.0f}"})
    if not revenue.empty:
        for _, r in revenue.tail(5).iterrows():
            rows.append({"Date": str(r.get("Date",""))[:10], "Description": r.get("Description",""), "Type": "Revenue", "Amount": f"+{CURRENCY}{r.get('Amount',0):,.0f}"})
    if rows:
        df = pd.DataFrame(rows).sort_values("Date", ascending=False).head(10)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet.")