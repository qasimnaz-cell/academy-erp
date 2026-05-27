import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import date
from modules.sheets import get_revenue, add_revenue, update_revenue, delete_revenue
from modules.config import CURRENCY, REVENUE_STREAMS

def render():
    st.title("💰 Revenue Tracking")
    tab_add,tab_list,tab_edit=st.tabs(["➕ Add Revenue","📋 All Revenue","✏️ Edit/Delete"])
    with tab_add:
        with st.form("add_revenue_form",clear_on_submit=True):
            c1,c2=st.columns(2)
            source=c1.selectbox("Source *",REVENUE_STREAMS)
            amount=c2.number_input(f"Amount ({CURRENCY}) *",min_value=0.0,step=100.0)
            rev_date=c1.date_input("Date *",value=date.today())
            desc=c2.text_input("Description"); notes=st.text_input("Notes")
            if st.form_submit_button("Add Revenue",type="primary",use_container_width=True):
                if amount<=0: st.error("Amount must be > 0.")
                else:
                    add_revenue({"date":str(rev_date),"source":source,"description":desc,"amount":amount,"notes":notes})
                    st.success(f"{CURRENCY}{amount:,.0f} added!")
    with tab_list:
        revenue=get_revenue()
        if revenue.empty: st.info("No revenue yet."); return
        total=float(revenue["Amount"].sum()) if "Amount" in revenue.columns else 0
        c1,c2=st.columns(2)
        c1.metric("Total Revenue",f"{CURRENCY}{total:,.0f}"); c2.metric("Transactions",len(revenue))
        if "Source" in revenue.columns:
            grp=revenue.groupby("Source")["Amount"].sum().reset_index()
            fig=px.pie(grp,names="Source",values="Amount",hole=0.6,color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=250,paper_bgcolor="rgba(0,0,0,0)",margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig,use_container_width=True)
        cols=[c for c in ["Date","Source","Description","Amount","Notes"] if c in revenue.columns]
        st.dataframe(revenue[cols],use_container_width=True,hide_index=True)
        st.download_button("Export CSV",revenue.to_csv(index=False).encode(),"revenue.csv","text/csv")
    with tab_edit:
        revenue=get_revenue()
        if revenue.empty: st.info("No revenue to edit."); return
        opts={f"{r.get('Date','')} - {r.get('Source','')} ({CURRENCY}{r.get('Amount',0):,.0f})":r.get("Timestamp","") for _,r in revenue.iterrows()}
        sel=st.selectbox("Select entry",list(opts.keys()))
        ts=opts[sel]
        row=revenue[revenue["Timestamp"]==ts].iloc[0] if ts and "Timestamp" in revenue.columns else revenue.iloc[0]
        ce,cd=st.columns([3,1])
        with ce:
            with st.form("edit_revenue_form"):
                ec1,ec2=st.columns(2)
                esrc=ec1.selectbox("Source",REVENUE_STREAMS,index=REVENUE_STREAMS.index(row.get("Source",REVENUE_STREAMS[0])) if row.get("Source") in REVENUE_STREAMS else 0)
                ea=ec2.number_input("Amount",value=float(row.get("Amount",0)),step=100.0)
                edate=ec1.text_input("Date",value=str(row.get("Date","")))
                ed=ec2.text_input("Description",value=row.get("Description",""))
                if st.form_submit_button("Save Changes",type="primary"):
                    update_revenue(ts,{"date":edate,"source":esrc,"description":ed,"amount":ea})
                    st.success("Updated!")
        with cd:
            st.write(""); st.write("")
            if st.button("Delete",type="secondary",use_container_width=True):
                delete_revenue(ts); st.success("Deleted!"); st.rerun()