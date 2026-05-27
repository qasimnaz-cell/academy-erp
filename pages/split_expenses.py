import json
import streamlit as st
import pandas as pd
from modules.sheets import get_splits, add_split, settle_split
from modules.auth import get_current_user
from modules.config import CURRENCY

def calc(total, people, method, shares=None):
    n = len(people)
    if not n: return {}
    if method=="Equal": return {p: round(total/n,2) for p in people}
    if method=="Percentage":
        if not shares or abs(sum(shares)-100)>0.1: raise ValueError("Must sum to 100")
        return {p: round(total*s/100,2) for p,s in zip(people,shares)}
    if method=="Custom":
        if not shares or abs(sum(shares)-total)>1: raise ValueError("Must sum to total")
        return {p: round(s,2) for p,s in zip(people,shares)}

def render():
    st.title("🤝 Split Expenses")
    tab_add, tab_history = st.tabs(["➕ Add Split", "📋 History"])
    with tab_add:
        with st.form("split_form", clear_on_submit=True):
            desc   = st.text_input("Description *")
            c1,c2  = st.columns(2)
            total  = c1.number_input(f"Total ({CURRENCY}) *", min_value=0.0, step=100.0)
            paid_by= c2.text_input("Paid By *")
            method = st.radio("Split", ["Equal","Percentage","Custom"], horizontal=True)
            raw    = st.text_area("Participants (one per line) *", height=80)
            people = [p.strip() for p in raw.split("\n") if p.strip()]
            shares = None
            if method != "Equal" and people:
                shares = []
                cols = st.columns(min(len(people),4))
                for i,p in enumerate(people):
                    d = 100/len(people) if method=="Percentage" else total/len(people)
                    shares.append(cols[i%4].number_input(p, min_value=0.0, value=round(d,1)))
            if st.form_submit_button("Add Split", type="primary", use_container_width=True):
                if not desc or not paid_by or not people: st.error("All fields required.")
                elif total<=0: st.error("Amount must be > 0.")
                else:
                    try:
                        result = calc(total, people, method, shares)
                        add_split({"description":desc,"total_amount":total,"split_type":method,
                                  "participants":json.dumps(list(result.keys())),
                                  "shares":json.dumps(list(result.values())),"paid_by":paid_by})
                        st.success("Split recorded!")
                        for person,amt in result.items(): st.write(f"• **{person}** owes {CURRENCY}{amt:,.0f}")
                    except ValueError as e: st.error(str(e))
    with tab_history:
        splits = get_splits()
        if splits.empty: st.info("No splits yet."); return
        c1,c2 = st.columns(2)
        c1.number_input("Amount", min_value=0.0, step=100.0, key="calc_a", label_visibility="visible")
        c2.number_input("People", min_value=2, value=3, key="calc_n", label_visibility="visible")
        if st.session_state.get("calc_a",0) > 0:
            st.info(f"Each pays: {CURRENCY}{st.session_state['calc_a']/st.session_state['calc_n']:,.0f}")
        st.divider()
        unsettled = splits[splits.get("Status",pd.Series(dtype=str))!="settled"] if "Status" in splits.columns else splits
        if unsettled.empty: st.success("All settled!")
        else:
            for _, row in unsettled.iterrows():
                with st.expander(f"{row.get('Description','')} — {CURRENCY}{row.get('TotalAmount',0):,.0f}"):
                    try:
                        for p,s in zip(json.loads(row.get("Participants","[]")),json.loads(row.get("Shares","[]"))):
                            st.write(f"• **{p}** owes {CURRENCY}{s:,.0f}")
                    except: st.write("Parse error.")
                    if st.button("Mark Settled", key=f"s_{row.get('Timestamp','')}"):
                        settle_split(str(row.get("Timestamp","")), get_current_user().get("name",""))
                        st.rerun()