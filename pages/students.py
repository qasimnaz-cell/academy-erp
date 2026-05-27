import streamlit as st
import pandas as pd
from datetime import date, datetime
import io
from modules.sheets import get_students, add_student, record_payment, update_student, get_payments
from modules.config import CURRENCY, COURSES
from utils.pdf_report import generate_receipt

def render():
    st.title("👥 Student Fee Management")
    tab_add, tab_list, tab_pay, tab_hist = st.tabs(["➕ Add Student","📋 All Students","💳 Collect Payment","📜 Payment History"])
    with tab_add:
        with st.form("add_student_form", clear_on_submit=True):
            c1,c2 = st.columns(2)
            name=c1.text_input("Full Name *"); contact=c2.text_input("Phone *")
            email=c1.text_input("Email"); course=c2.selectbox("Course *",COURSES)
            fee=c1.number_input(f"Monthly Fee ({CURRENCY}) *",min_value=0,step=500)
            enroll=c2.date_input("Enrollment Date",value=date.today())
            if st.form_submit_button("Enroll Student",type="primary",use_container_width=True):
                if not name or not contact: st.error("Name and phone required.")
                elif fee<=0: st.error("Fee must be > 0.")
                else:
                    sid=add_student({"name":name,"contact":contact,"email":email,"course":course,"monthly_fee":fee,"enrollment_date":str(enroll)})
                    st.success(f"Enrolled! ID: **{sid}**")
    with tab_list:
        students=get_students()
        if students.empty: st.info("No students yet.")
        else:
            hb="Balance" in students.columns
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Total",len(students))
            c2.metric("Overdue",len(students[students["Balance"]>0]) if hb else 0)
            c3.metric("Pending",f"{CURRENCY}{students[students['Balance']>0]['Balance'].sum():,.0f}" if hb else f"{CURRENCY}0")
            c4.metric("Paid",len(students[students["Balance"]==0]) if hb else 0)
            st.divider()
            search=st.text_input("Search by name or ID")
            df=students.copy()
            if search: df=df[df.apply(lambda r: search.lower() in str(r.get("Name","")).lower() or search.lower() in str(r.get("StudentID","")).lower(),axis=1)]
            def st_(r):
                b=r.get("Balance",0); p=r.get("PaidAmount",0)
                if b<0: return "Advance"
                if b==0: return "Paid"
                if p>0: return "Partial"
                return "Overdue"
            df["Status"]=df.apply(st_,axis=1)
            cols=[c for c in ["StudentID","Name","Course","MonthlyFee","PaidAmount","Balance","Status"] if c in df.columns]
            st.dataframe(df[cols],use_container_width=True,hide_index=True)
            st.divider()
            st.subheader("Edit Student")
            sel=st.selectbox("Select student",students["StudentID"].tolist() if "StudentID" in students.columns else [])
            if sel:
                row=students[students["StudentID"]==sel].iloc[0]
                with st.form("edit_form"):
                    ec1,ec2=st.columns(2)
                    en=ec1.text_input("Name",value=row.get("Name",""))
                    ec=ec2.text_input("Phone",value=row.get("Contact",""))
                    ee=ec1.text_input("Email",value=row.get("Email",""))
                    ecourse=ec2.selectbox("Course",COURSES,index=COURSES.index(row.get("Course",COURSES[0])) if row.get("Course") in COURSES else 0)
                    ef=ec1.number_input("Monthly Fee",value=float(row.get("MonthlyFee",0)),step=500.0)
                    es=ec2.selectbox("Status",["Active","Inactive","Graduated"],index=["Active","Inactive","Graduated"].index(row.get("Status","Active")) if row.get("Status") in ["Active","Inactive","Graduated"] else 0)
                    if st.form_submit_button("Save Changes",type="primary"):
                        update_student(sel,{"name":en,"contact":ec,"email":ee,"course":ecourse,"monthly_fee":ef,"status":es})
                        st.success("Updated!")
            c1,c2=st.columns(2)
            c1.download_button("Export CSV",df.to_csv(index=False).encode(),"students.csv","text/csv")
    with tab_pay:
        students=get_students()
        if students.empty: st.info("No students enrolled.")
        else:
            opts={f"{r['Name']} ({r['StudentID']}) Balance:{CURRENCY}{r.get('Balance',0):,.0f}":r["StudentID"] for _,r in students.iterrows()}
            sel=st.selectbox("Select Student",list(opts.keys()))
            sid=opts[sel]; row=students[students["StudentID"]==sid].iloc[0]
            c1,c2,c3=st.columns(3)
            c1.metric("Monthly Fee",f"{CURRENCY}{row.get('MonthlyFee',0):,.0f}")
            c2.metric("Paid",f"{CURRENCY}{row.get('PaidAmount',0):,.0f}")
            c3.metric("Balance",f"{CURRENCY}{row.get('Balance',0):,.0f}")
            st.divider()
            with st.form("payment_form",clear_on_submit=True):
                pc1,pc2=st.columns(2)
                amount=pc1.number_input(f"Amount ({CURRENCY}) *",min_value=0.0,step=500.0)
                note=pc2.text_input("Note",placeholder="e.g. May 2025 fee")
                gen_r=st.checkbox("Generate PDF receipt",value=True)
                if st.form_submit_button("Record Payment",type="primary",use_container_width=True):
                    if amount<=0: st.error("Amount must be > 0")
                    else:
                        with st.spinner("Recording..."):
                            record_payment(sid,amount,note)
                        st.success(f"Payment of {CURRENCY}{amount:,.0f} recorded!")
                        if gen_r:
                            try:
                                pdf=generate_receipt({"student_id":sid,"name":row["Name"],"course":row.get("Course",""),"amount":amount,"date":datetime.today().strftime("%Y-%m-%d"),"note":note})
                                st.download_button("Download Receipt",pdf,f"receipt_{sid}.pdf",mime="application/pdf")
                            except Exception as e: st.warning(f"Receipt failed: {e}")
    with tab_hist:
        payments=get_payments()
        if payments.empty: st.info("No payment records yet.")
        else:
            cols=[c for c in ["Timestamp","StudentID","Name","Amount","TotalPaid","Balance","Note"] if c in payments.columns]
            st.dataframe(payments[cols],use_container_width=True,hide_index=True)
            st.download_button("Export CSV",payments.to_csv(index=False).encode(),"payments.csv","text/csv")