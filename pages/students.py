import streamlit as st
import pandas as pd
from datetime import datetime, date
import io

from modules.sheets import get_students, add_student, record_payment
from modules.config import CURRENCY, COURSES
from utils.pdf_report import generate_receipt


def render():
    st.title("👥 Student Fee Management")

    tab_add, tab_list, tab_pay = st.tabs(["➕ Add Student", "📋 All Students", "💳 Collect Payment"])

    with tab_add:
        st.subheader("Enroll New Student")
        with st.form("add_student_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name    = c1.text_input("Full Name *")
            contact = c2.text_input("Phone *")
            email   = c1.text_input("Email")
            course  = c2.selectbox("Course *", COURSES)
            fee     = c1.number_input(f"Monthly Fee ({CURRENCY}) *", min_value=0, step=500)
            enroll  = c2.date_input("Enrollment Date", value=date.today())
            submitted = st.form_submit_button("✅ Enroll Student", use_container_width=True, type="primary")
            if submitted:
                if not name or not contact:
                    st.error("Name and contact are required.")
                elif fee <= 0:
                    st.error("Monthly fee must be > 0.")
                else:
                    with st.spinner("Enrolling…"):
                        sid = add_student({
                            "name": name, "contact": contact, "email": email,
                            "course": course, "monthly_fee": fee,
                            "enrollment_date": str(enroll),
                        })
                    st.success(f"✅ Enrolled! Student ID: **{sid}**")

    with tab_list:
        students = get_students()
        if students.empty:
            st.info("No students yet. Use the ➕ Add Student tab above.")
        else:
            has_balance = "Balance" in students.columns
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", len(students))
            c2.metric("Overdue", len(students[students["Balance"] > 0]) if has_balance else 0)
            c3.metric("Pending", f"{CURRENCY}{students[students['Balance']>0]['Balance'].sum():,.0f}" if has_balance else f"{CURRENCY}0")
            c4.metric("Paid", len(students[students["Balance"] == 0]) if has_balance else 0)
            st.divider()
            search = st.text_input("🔍 Search", placeholder="Name or ID")
            df = students.copy()
            if search:
                df = df[df.apply(lambda r: search.lower() in str(r.get("Name","")).lower() or search.lower() in str(r.get("StudentID","")).lower(), axis=1)]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Export CSV", df.to_csv(index=False).encode(), "students.csv", "text/csv")

    with tab_pay:
        st.subheader("Collect Payment")
        students = get_students()
        if students.empty:
            st.info("No students enrolled yet.")
        else:
            options = {f"{r['Name']} ({r['StudentID']})": r["StudentID"] for _, r in students.iterrows()}
            selected = st.selectbox("Select Student", list(options.keys()))
            sid = options[selected]
            row = students[students["StudentID"] == sid].iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Monthly Fee", f"{CURRENCY}{row.get('MonthlyFee',0):,.0f}")
            c2.metric("Paid", f"{CURRENCY}{row.get('PaidAmount',0):,.0f}")
            c3.metric("Balance", f"{CURRENCY}{row.get('Balance',0):,.0f}")
            st.divider()
            with st.form("payment_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                amount = col1.number_input(f"Amount ({CURRENCY}) *", min_value=0.0, step=500.0)
                note   = col2.text_input("Note", placeholder="e.g. May 2025 fee")
                if st.form_submit_button("💳 Record Payment", type="primary", use_container_width=True):
                    if amount <= 0:
                        st.error("Amount must be > 0")
                    else:
                        record_payment(sid, amount, note)
                        st.success(f"✅ Payment of {CURRENCY}{amount:,.0f} recorded!")
