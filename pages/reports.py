"""
pages/reports.py
Report generation — monthly, P&L, pending dues — PDF + Excel.
"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime, date

from modules.sheets import get_students, get_expenses, get_revenue
from modules.config import CURRENCY
from utils.finance import monthly_summary, expense_breakdown, revenue_breakdown, pending_collections
from utils.pdf_report import generate_monthly_report


def render():
    st.title("📋 Reports")

    report_type = st.selectbox("Select Report Type", [
        "Monthly Finance Report",
        "Pending Collections Report",
        "Expense Detail Report",
        "Revenue Detail Report",
    ])

    st.divider()

    # ── Monthly Finance Report ─────────────────────────────────────────
    if report_type == "Monthly Finance Report":
        col1, col2 = st.columns(2)
        year  = col1.selectbox("Year",  list(range(2023, 2027)), index=2)
        month = col2.selectbox("Month", list(range(1, 13)),
                               index=datetime.today().month - 1)
        month_str = f"{year}-{month:02d}"

        if st.button("Generate Report", type="primary"):
            with st.spinner("Generating…"):
                expenses = get_expenses()
                revenue  = get_revenue()
                summary  = monthly_summary(expenses, revenue, month_str)
                exp_grp  = expense_breakdown(expenses)
                rev_grp  = revenue_breakdown(revenue)

            # Preview
            st.subheader(f"Report: {month_str}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Revenue",  f"{CURRENCY}{summary['total_revenue']:,.0f}")
            c2.metric("Expenses", f"{CURRENCY}{summary['total_expenses']:,.0f}")
            c3.metric("Profit",   f"{CURRENCY}{summary['net_profit']:,.0f}")
            c4.metric("Margin",   f"{summary['profit_margin']:.1f}%")

            # PDF
            try:
                pdf_bytes = generate_monthly_report(summary, exp_grp, rev_grp, month_str)
                st.download_button(
                    "⬇️ Download PDF Report",
                    pdf_bytes,
                    f"report_{month_str}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.warning(f"PDF generation failed: {e}")

            # Excel
            try:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    pd.DataFrame([summary]).to_excel(writer, sheet_name="Summary", index=False)
                    if not exp_grp.empty:
                        exp_grp.to_excel(writer, sheet_name="Expenses", index=False)
                    if not rev_grp.empty:
                        rev_grp.to_excel(writer, sheet_name="Revenue", index=False)
                st.download_button(
                    "⬇️ Download Excel Report",
                    buf.getvalue(),
                    f"report_{month_str}.xlsx",
                )
            except Exception as e:
                st.warning(f"Excel generation failed: {e}")

    # ── Pending Collections ────────────────────────────────────────────
    elif report_type == "Pending Collections Report":
        if st.button("Generate Pending Report", type="primary"):
            students = get_students()
            pending  = pending_collections(students)

            st.metric("Total Pending", f"{CURRENCY}{pending['total']:,.0f}")
            st.metric("Students Overdue", pending["count"])

            if pending["students"]:
                df = pd.DataFrame(pending["students"])
                display = ["StudentID", "Name", "Course", "Balance"]
                display = [c for c in display if c in df.columns]
                st.dataframe(df[display], use_container_width=True, hide_index=True)

                csv = df.to_csv(index=False).encode()
                st.download_button("⬇️ Export CSV", csv, "pending_collections.csv", "text/csv")

    # ── Expense Detail ─────────────────────────────────────────────────
    elif report_type == "Expense Detail Report":
        if st.button("Generate Expense Report", type="primary"):
            expenses = get_expenses()
            if not expenses.empty:
                st.dataframe(expenses, use_container_width=True, hide_index=True)
                csv = expenses.to_csv(index=False).encode()
                st.download_button("⬇️ Export CSV", csv, "expenses.csv", "text/csv")
            else:
                st.info("No expense data available.")

    # ── Revenue Detail ─────────────────────────────────────────────────
    elif report_type == "Revenue Detail Report":
        if st.button("Generate Revenue Report", type="primary"):
            revenue = get_revenue()
            if not revenue.empty:
                st.dataframe(revenue, use_container_width=True, hide_index=True)
                csv = revenue.to_csv(index=False).encode()
                st.download_button("⬇️ Export CSV", csv, "revenue.csv", "text/csv")
            else:
                st.info("No revenue data available.")
