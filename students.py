"""
pages/students.py
Student Fee Management — add, search, collect payments, generate receipts.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date

from modules.sheets import get_students, add_student, record_payment
from modules.auth import get_current_user
from modules.config import CURRENCY, COURSES
from utils.pdf_report import generate_receipt


def render():
    st.title("👥 Student Fee Management")

    tab_list, tab_add, tab_pay = st.tabs(["📋 All Students", "➕ Add Student", "💳 Collect Payment"])

    # ── Tab 1: Student List ────────────────────────────────────────────
    with tab_list:
        students = get_students()
        if students.empty:
            st.info("No students yet. Use the 'Add Student' tab to get started.")
            return

        # Filters
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search = st.text_input("🔍 Search", placeholder="Name, ID, or contact…")
        with col2:
            course_filter = st.selectbox("Course", ["All"] + COURSES)
        with col3:
            status_filter = st.selectbox("Status", ["All", "Overdue", "Paid", "Partial", "Advance"])

        # Apply filters
        df = students.copy()
        if search:
            mask = (
                df["Name"].str.contains(search, case=False, na=False) |
                df["StudentID"].str.contains(search, case=False, na=False) |
                df.get("Contact", pd.Series(dtype=str)).str.contains(search, case=False, na=False)
            )
            df = df[mask]
        if course_filter != "All":
            df = df[df["Course"] == course_filter]
        if status_filter == "Overdue":
            df = df[df["Balance"] > 0]
        elif status_filter == "Paid":
            df = df[df["Balance"] == 0]
        elif status_filter == "Partial":
            df = df[(df["PaidAmount"] > 0) & (df["Balance"] > 0)]
        elif status_filter == "Advance":
            df = df[df["Balance"] < 0]

        # Summary chips
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Students", len(students))
        c2.metric("Overdue",        len(students[students["Balance"] > 0]))
        c3.metric("Total Pending",  f"{CURRENCY}{students[students['Balance']>0]['Balance'].sum():,.0f}")
        c4.metric("Fully Paid",     len(students[students["Balance"] == 0]))

        st.divider()

        # Table
        display_cols = ["StudentID", "Name", "Course", "MonthlyFee", "PaidAmount", "Balance"]
        display_cols = [c for c in display_cols if c in df.columns]

        def _status(row):
            if row["Balance"] < 0:  return "🔵 Advance"
            if row["Balance"] == 0: return "✅ Paid"
            if row["PaidAmount"] > 0: return "🟡 Partial"
            return "🔴 Overdue"

        df["Status"] = df.apply(_status, axis=1)

        st.dataframe(
            df[display_cols + ["Status"]].rename(columns={
                "MonthlyFee":  f"Fee ({CURRENCY})",
                "PaidAmount":  f"Paid ({CURRENCY})",
                "Balance":     f"Balance ({CURRENCY})",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Export
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv = df.to_csv(index=False).encode()
            st.download_button("⬇️ Export CSV", csv, "students.csv", "text/csv")
        with col_exp2:
            try:
                from openpyxl import Workbook
                import io
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as w:
                    df.to_excel(w, index=False, sheet_name="Students")
                st.download_button("⬇️ Export Excel", buf.getvalue(), "students.xlsx")
            except Exception:
                pass

    # ── Tab 2: Add Student ─────────────────────────────────────────────
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

            submitted = st.form_submit_button("Enroll Student", use_container_width=True, type="primary")
            if submitted:
                if not name or not contact:
                    st.error("Name and contact are required.")
                elif fee <= 0:
                    st.error("Monthly fee must be greater than 0.")
                else:
                    with st.spinner("Enrolling…"):
                        sid = add_student({
                            "name": name, "contact": contact, "email": email,
                            "course": course, "monthly_fee": fee,
                            "enrollment_date": str(enroll),
                        })
                    st.success(f"✅ Student enrolled! ID: **{sid}**")

    # ── Tab 3: Collect Payment ─────────────────────────────────────────
    with tab_pay:
        st.subheader("Record Payment")
        students = get_students()

        if not students.empty:
            student_options = {
                f"{r['Name']} ({r['StudentID']}) — Balance: {CURRENCY}{r['Balance']:,.0f}": r["StudentID"]
                for _, r in students.iterrows()
            }
            selected_label = st.selectbox("Select Student", list(student_options.keys()))
            selected_id    = student_options[selected_label]
            student_row    = students[students["StudentID"] == selected_id].iloc[0]

            st.info(
                f"**{student_row['Name']}** · {student_row['Course']} · "
                f"Monthly: {CURRENCY}{student_row['MonthlyFee']:,.0f} · "
                f"Paid: {CURRENCY}{student_row['PaidAmount']:,.0f} · "
                f"Balance: {CURRENCY}{student_row['Balance']:,.0f}"
            )

            with st.form("payment_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                amount = c1.number_input(
                    f"Amount ({CURRENCY}) *",
                    min_value=0.0,
                    max_value=float(student_row["MonthlyFee"]) * 2,
                    step=500.0,
                )
                note = c2.text_input("Note", placeholder="e.g. May 2025 fee")
                gen_receipt = st.checkbox("Generate PDF receipt", value=True)

                submitted = st.form_submit_button("Record Payment", type="primary", use_container_width=True)
                if submitted:
                    if amount <= 0:
                        st.error("Amount must be > 0")
                    else:
                        with st.spinner("Recording…"):
                            record_payment(selected_id, amount, note)
                        st.success(f"✅ Payment of {CURRENCY}{amount:,.0f} recorded!")

                        if gen_receipt:
                            try:
                                pdf_bytes = generate_receipt({
                                    "student_id": selected_id,
                                    "name":       student_row["Name"],
                                    "course":     student_row["Course"],
                                    "amount":     amount,
                                    "date":       datetime.today().strftime("%Y-%m-%d"),
                                    "note":       note,
                                })
                                st.download_button(
                                    "⬇️ Download Receipt",
                                    pdf_bytes,
                                    f"receipt_{selected_id}_{datetime.today().strftime('%Y%m%d')}.pdf",
                                    mime="application/pdf",
                                )
                            except Exception as e:
                                st.warning(f"Receipt generation failed: {e}")
        else:
            st.info("No students enrolled yet.")
