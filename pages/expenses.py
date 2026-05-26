"""
pages/expenses.py
Expense Management — add, view, filter, and upload receipts to Google Drive.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

from modules.sheets import get_expenses, add_expense
from modules.config import CURRENCY, EXPENSE_CATEGORIES
from utils.drive_upload import upload_receipt


def render():
    st.title("🧾 Expense Management")

    tab_list, tab_add, tab_chart = st.tabs(["📋 All Expenses", "➕ Add Expense", "📊 Analytics"])

    # ── Tab 1: List ────────────────────────────────────────────────────
    with tab_list:
        expenses = get_expenses()

        if expenses.empty:
            st.info("No expenses yet. Add your first expense using the 'Add Expense' tab.")
            return

        # Filters
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        search   = c1.text_input("🔍 Search", placeholder="Description…")
        cat_f    = c2.selectbox("Category", ["All"] + EXPENSE_CATEGORIES)
        month_f  = c3.text_input("Month", placeholder="YYYY-MM", value=date.today().strftime("%Y-%m"))
        min_a, max_a = c4.slider("Amount range", 0, 500000, (0, 500000), step=1000)

        df = expenses.copy()
        if search:
            df = df[df["Description"].str.contains(search, case=False, na=False)]
        if cat_f != "All":
            df = df[df["Category"] == cat_f]
        if month_f:
            df = df[pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m") == month_f]
        df = df[(df["Amount"] >= min_a) & (df["Amount"] <= max_a)]

        # KPI row
        total = df["Amount"].sum()
        k1, k2, k3 = st.columns(3)
        k1.metric(f"Total Expenses ({month_f})", f"{CURRENCY}{total:,.0f}")
        k2.metric("Transactions",                 len(df))
        k3.metric("Avg. Transaction",             f"{CURRENCY}{df['Amount'].mean():,.0f}" if len(df) else "—")

        st.divider()

        display = ["Date", "Description", "Category", "Amount", "PaidBy", "Receipt"]
        display = [c for c in display if c in df.columns]
        st.dataframe(df[display], use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode()
        st.download_button("⬇️ Export CSV", csv, "expenses.csv", "text/csv")

    # ── Tab 2: Add ─────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add New Expense")
        with st.form("add_expense_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            desc       = c1.text_input("Description *")
            category   = c2.selectbox("Category *", EXPENSE_CATEGORIES)
            amount     = c1.number_input(f"Amount ({CURRENCY}) *", min_value=0.0, step=100.0)
            exp_date   = c2.date_input("Date *", value=date.today())
            paid_by    = c1.text_input("Paid By", placeholder="Name or department")
            dept       = c2.text_input("Department", placeholder="Optional")
            is_recur   = c1.checkbox("Recurring monthly expense")
            notes      = st.text_area("Notes", height=80)
            receipt    = st.file_uploader("Receipt (PDF/image)", type=["pdf", "png", "jpg", "jpeg"])

            submitted = st.form_submit_button("Add Expense", type="primary", use_container_width=True)
            if submitted:
                if not desc:
                    st.error("Description is required.")
                elif amount <= 0:
                    st.error("Amount must be > 0.")
                else:
                    receipt_url = ""
                    if receipt:
                        with st.spinner("Uploading receipt to Drive…"):
                            try:
                                receipt_url = upload_receipt(receipt, f"{exp_date}_{desc[:30]}")
                            except Exception as e:
                                st.warning(f"Receipt upload failed: {e}")

                    add_expense({
                        "date":         str(exp_date),
                        "description":  desc,
                        "category":     category,
                        "amount":       amount,
                        "paid_by":      paid_by,
                        "department":   dept,
                        "is_recurring": is_recur,
                        "notes":        notes,
                        "receipt_url":  receipt_url,
                    })
                    st.success(f"✅ Expense of {CURRENCY}{amount:,.0f} added!")

    # ── Tab 3: Analytics ───────────────────────────────────────────────
    with tab_chart:
        expenses = get_expenses()
        if expenses.empty:
            st.info("No data to show.")
            return

        st.subheader("Spending by Category")
        grp = expenses.groupby("Category")["Amount"].sum().reset_index()
        fig = px.bar(grp, x="Category", y="Amount", color="Category",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(showlegend=False, height=350,
                          paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Monthly Expense Trend")
        if "Date" in expenses.columns:
            expenses["Month"] = pd.to_datetime(expenses["Date"], errors="coerce").dt.to_period("M").astype(str)
            monthly = expenses.groupby("Month")["Amount"].sum().reset_index()
            fig2 = px.line(monthly, x="Month", y="Amount", markers=True,
                           color_discrete_sequence=["#EF4444"])
            fig2.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
