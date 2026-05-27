import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from modules.sheets import get_expenses, add_expense, update_expense, delete_expense
from modules.config import CURRENCY, EXPENSE_CATEGORIES

def render():
    st.title("🧾 Expense Management")
    tab_add,tab_list,tab_edit=st.tabs(["➕ Add Expense","📋 All Expenses","✏️ Edit/Delete"])
    with tab_add:
        with st.form("add_expense_form",clear_on_submit=True):
            c1,c2=st.columns(2)
            desc=c1.text_input("Description *"); category=c2.selectbox("Category *",EXPENSE_CATEGORIES)
            amount=c1.number_input(f"Amount ({CURRENCY}) *",min_value=0.0,step=100.0)
            exp_date=c2.date_input("Date *",value=date.today())
            paid_by=c1.text_input("Paid By"); notes=c2.text_input("Notes")
            if st.form_submit_button("Add Expense",type="primary",use_container_width=True):
                if not desc: st.error("Description required.")
                elif amount<=0: st.error("Amount must be > 0.")
                else:
                    add_expense({"date":str(exp_date),"description":desc,"category":category,"amount":amount,"paid_by":paid_by,"notes":notes,"receipt_url":"","department":"","is_recurring":False})
                    st.success(f"Expense of {CURRENCY}{amount:,.0f} added!")
    with tab_list:
        expenses=get_expenses()
        if expenses.empty: st.info("No expenses yet."); return
        total=float(expenses["Amount"].sum()) if "Amount" in expenses.columns else 0
        c1,c2,c3=st.columns(3)
        c1.metric("Total",f"{CURRENCY}{total:,.0f}"); c2.metric("Transactions",len(expenses))
        c3.metric("Average",f"{CURRENCY}{total/len(expenses):,.0f}" if len(expenses) else "0")
        if "Category" in expenses.columns:
            grp=expenses.groupby("Category")["Amount"].sum().reset_index()
            fig=px.bar(grp,x="Category",y="Amount",color="Category",color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(showlegend=False,height=220,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig,use_container_width=True)
        cols=[c for c in ["Date","Description","Category","Amount","PaidBy","Notes"] if c in expenses.columns]
        st.dataframe(expenses[cols],use_container_width=True,hide_index=True)
        st.download_button("Export CSV",expenses.to_csv(index=False).encode(),"expenses.csv","text/csv")
    with tab_edit:
        expenses=get_expenses()
        if expenses.empty: st.info("No expenses to edit."); return
        opts={f"{r.get('Date','')} - {r.get('Description','')} ({CURRENCY}{r.get('Amount',0):,.0f})":r.get("Timestamp","") for _,r in expenses.iterrows()}
        sel=st.selectbox("Select expense",list(opts.keys()))
        ts=opts[sel]
        row=expenses[expenses["Timestamp"]==ts].iloc[0] if ts and "Timestamp" in expenses.columns else expenses.iloc[0]
        ce,cd=st.columns([3,1])
        with ce:
            with st.form("edit_expense_form"):
                ec1,ec2=st.columns(2)
                ed=ec1.text_input("Description",value=row.get("Description",""))
                ecat=ec2.selectbox("Category",EXPENSE_CATEGORIES,index=EXPENSE_CATEGORIES.index(row.get("Category",EXPENSE_CATEGORIES[0])) if row.get("Category") in EXPENSE_CATEGORIES else 0)
                ea=ec1.number_input("Amount",value=float(row.get("Amount",0)),step=100.0)
                edate=ec2.text_input("Date",value=str(row.get("Date","")))
                ep=ec1.text_input("Paid By",value=row.get("PaidBy",""))
                en=ec2.text_input("Notes",value=row.get("Notes",""))
                if st.form_submit_button("Save Changes",type="primary"):
                    update_expense(ts,{"date":edate,"description":ed,"category":ecat,"amount":ea,"paid_by":ep,"notes":en})
                    st.success("Updated!")
        with cd:
            st.write(""); st.write("")
            if st.button("Delete",type="secondary",use_container_width=True):
                delete_expense(ts); st.success("Deleted!"); st.rerun()