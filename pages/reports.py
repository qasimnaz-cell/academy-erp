import streamlit as st
import pandas as pd
import io
from datetime import datetime
from modules.sheets import get_students, get_expenses, get_revenue
from modules.config import CURRENCY

def render():
    st.title("📋 Reports")
    report = st.selectbox("Select Report", ["Monthly Finance Report","Pending Collections","Expense Detail","Revenue Detail","Student List"])
    st.divider()
    if report == "Monthly Finance Report":
        c1,c2 = st.columns(2)
        year  = c1.selectbox("Year", [2024,2025,2026], index=1)
        month = c2.selectbox("Month", list(range(1,13)), index=datetime.today().month-1)
        month_str = f"{year}-{month:02d}"
        if st.button("Generate", type="primary"):
            expenses = get_expenses(); revenue = get_revenue()
            def fm(df):
                if df.empty or "Date" not in df.columns: return df
                df = df.copy(); df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                return df[df["Date"].dt.strftime("%Y-%m")==month_str]
            em = fm(expenses); rm = fm(revenue)
            tr = float(pd.to_numeric(rm["Amount"], errors="coerce").fillna(0).sum()) if not rm.empty and "Amount" in rm.columns else 0
            te = float(pd.to_numeric(em["Amount"], errors="coerce").fillna(0).sum()) if not em.empty and "Amount" in em.columns else 0
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Revenue", f"{CURRENCY}{tr:,.0f}"); c2.metric("Expenses", f"{CURRENCY}{te:,.0f}")
            c3.metric("Profit", f"{CURRENCY}{tr-te:,.0f}"); c4.metric("Margin", f"{(tr-te)/tr*100:.1f}%" if tr else "0%")
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                pd.DataFrame([{"Month":month_str,"Revenue":tr,"Expenses":te,"Profit":tr-te}]).to_excel(w,sheet_name="Summary",index=False)
                if not em.empty: em.to_excel(w,sheet_name="Expenses",index=False)
                if not rm.empty: rm.to_excel(w,sheet_name="Revenue",index=False)
            st.download_button("Download Excel", buf.getvalue(), f"report_{month_str}.xlsx")
    elif report == "Pending Collections":
        students = get_students()
        if students.empty or "Balance" not in students.columns: st.info("No data."); return
        ov = students[pd.to_numeric(students["Balance"], errors="coerce").fillna(0) > 0]
        st.metric("Pending", f"{CURRENCY}{pd.to_numeric(ov['Balance'], errors='coerce').fillna(0).sum():,.0f}")
        st.metric("Students", len(ov))
        if not ov.empty:
            cols = [c for c in ["StudentID","Name","Course","Balance"] if c in ov.columns]
            st.dataframe(ov[cols], use_container_width=True, hide_index=True)
            st.download_button("Export CSV", ov.to_csv(index=False).encode(), "pending.csv", "text/csv")
    elif report == "Expense Detail":
        df = get_expenses()
        if df.empty: st.info("No expenses."); return
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Export CSV", df.to_csv(index=False).encode(), "expenses.csv", "text/csv")
    elif report == "Revenue Detail":
        df = get_revenue()
        if df.empty: st.info("No revenue."); return
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Export CSV", df.to_csv(index=False).encode(), "revenue.csv", "text/csv")
    elif report == "Student List":
        df = get_students()
        if df.empty: st.info("No students."); return
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Export CSV", df.to_csv(index=False).encode(), "students.csv", "text/csv")