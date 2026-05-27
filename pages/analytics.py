import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from modules.sheets import get_students, get_expenses, get_revenue
from modules.config import CURRENCY

def render():
    st.title("📈 Analytics")
    expenses = get_expenses()
    revenue  = get_revenue()
    students = get_students()
    if expenses.empty and revenue.empty:
        st.info("No data yet. Add expenses and revenue to see analytics.")
        return
    months, rv_list, ev_list = [], [], []
    for i in range(5,-1,-1):
        d = datetime.today().replace(day=1) - timedelta(days=i*28)
        m = d.strftime("%Y-%m")
        months.append(d.strftime("%b %Y"))
        rv = 0
        if not revenue.empty and "Date" in revenue.columns and "Amount" in revenue.columns:
            r2 = revenue.copy(); r2["Date"] = pd.to_datetime(r2["Date"], errors="coerce")
            rv = float(pd.to_numeric(r2[r2["Date"].dt.strftime("%Y-%m")==m]["Amount"], errors="coerce").fillna(0).sum())
        ev = 0
        if not expenses.empty and "Date" in expenses.columns and "Amount" in expenses.columns:
            e2 = expenses.copy(); e2["Date"] = pd.to_datetime(e2["Date"], errors="coerce")
            ev = float(pd.to_numeric(e2[e2["Date"].dt.strftime("%Y-%m")==m]["Amount"], errors="coerce").fillna(0).sum())
        rv_list.append(rv); ev_list.append(ev)
    fig = go.Figure()
    fig.add_scatter(name="Revenue", x=months, y=rv_list, fill="tozeroy", line=dict(color="#2563EB"), fillcolor="rgba(37,99,235,0.1)")
    fig.add_scatter(name="Expenses", x=months, y=ev_list, fill="tozeroy", line=dict(color="#EF4444"), fillcolor="rgba(239,68,68,0.1)")
    fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=10,b=0), yaxis=dict(gridcolor="rgba(128,128,128,.1)"), legend=dict(orientation="h",y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if not students.empty and "Course" in students.columns:
            st.subheader("Students by Course")
            enr = students.groupby("Course").size().reset_index(name="Count")
            fig2 = px.bar(enr, x="Course", y="Count", color="Course", color_discrete_sequence=px.colors.qualitative.Set2)
            fig2.update_layout(showlegend=False, height=250, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig2, use_container_width=True)
    with col2:
        if not expenses.empty and "Category" in expenses.columns:
            st.subheader("Spending by Category")
            grp = expenses.groupby("Category")["Amount"].sum().reset_index()
            fig3 = px.pie(grp, names="Category", values="Amount", hole=0.6, color_discrete_sequence=px.colors.qualitative.Set2)
            fig3.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig3, use_container_width=True)