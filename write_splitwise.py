import os

content = r'''
import json
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.sheets import get_groups, add_group, get_splits, add_split, settle_split, delete_split, get_settlements
from modules.auth import get_current_user
from modules.config import CURRENCY, EXPENSE_CATEGORIES

def calculate_split(total, people, method, shares=None):
    n = len(people)
    if not n: return {}
    if method == "Equal":
        return {p: round(total/n, 2) for p in people}
    if method == "Percentage":
        if not shares or abs(sum(shares)-100) > 0.1:
            raise ValueError("Percentages must sum to 100")
        return {p: round(total*s/100, 2) for p,s in zip(people, shares)}
    if method == "Exact Amount":
        if not shares or abs(sum(shares)-total) > 1:
            raise ValueError(f"Amounts must sum to {total}")
        return {p: round(s, 2) for p,s in zip(people, shares)}
    return {}

def simplify_debts(balances):
    creditors = sorted([(p,b) for p,b in balances.items() if b > 0], key=lambda x:-x[1])
    debtors   = sorted([(p,-b) for p,b in balances.items() if b < 0], key=lambda x:-x[1])
    txns, i, j = [], 0, 0
    while i < len(creditors) and j < len(debtors):
        cr, credit = creditors[i]
        dr, debt   = debtors[j]
        amt = min(credit, debt)
        txns.append({"from": dr, "to": cr, "amount": round(amt, 2)})
        creditors[i] = (cr, credit - amt)
        debtors[j]   = (dr, debt - amt)
        if creditors[i][1] < 0.01: i += 1
        if debtors[j][1]   < 0.01: j += 1
    return txns

def compute_balances(splits_df):
    balances = {}
    if splits_df.empty: return balances
    df = splits_df[splits_df.get("Status", pd.Series(dtype=str)) != "settled"] if "Status" in splits_df.columns else splits_df
    for _, row in df.iterrows():
        try:
            participants = json.loads(row.get("Participants","[]"))
            shares       = json.loads(row.get("Shares","[]"))
            paid_by      = str(row.get("PaidBy",""))
            total        = float(row.get("TotalAmount", 0))
            for p, s in zip(participants, shares):
                balances[p] = balances.get(p, 0) - float(s)
            balances[paid_by] = balances.get(paid_by, 0) + total
        except: continue
    return {k: round(v, 2) for k, v in balances.items()}

def render():
    st.title("🤝 Split Expenses")
    st.caption("Splitwise-style group expense tracking and debt settlement")

    splits = get_splits()
    groups = get_groups()
    user   = get_current_user()

    tab_dash, tab_add, tab_groups, tab_settle, tab_history = st.tabs([
        "📊 Dashboard", "➕ Add Expense", "👥 Groups", "✅ Settle Up", "📜 History"
    ])

    # ── DASHBOARD ──────────────────────────────────────────────────────
    with tab_dash:
        if splits.empty:
            st.info("No split expenses yet. Use ➕ Add Expense to get started.")
        else:
            balances  = compute_balances(splits)
            txns      = simplify_debts(balances)
            total_amt = float(splits["TotalAmount"].sum()) if "TotalAmount" in splits.columns else 0
            unsettled = splits[splits.get("Status", pd.Series(dtype=str)) != "settled"] if "Status" in splits.columns else splits
            settled   = splits[splits.get("Status", pd.Series(dtype=str)) == "settled"] if "Status" in splits.columns else pd.DataFrame()

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Expenses",     f"{CURRENCY}{total_amt:,.0f}")
            c2.metric("Unsettled Splits",   len(unsettled))
            c3.metric("Settled Splits",     len(settled))
            c4.metric("Pending Transfers",  len(txns))

            st.divider()
            st.subheader("💳 Member Balances")
            if balances:
                cols = st.columns(min(len(balances), 4))
                for i, (person, amount) in enumerate(sorted(balances.items(), key=lambda x: x[1])):
                    col = cols[i % len(cols)]
                    if amount > 0:
                        col.metric(person, f"{CURRENCY}{amount:,.0f}", "gets back ↑", delta_color="normal")
                    elif amount < 0:
                        col.metric(person, f"{CURRENCY}{abs(amount):,.0f}", "owes ↓", delta_color="inverse")
                    else:
                        col.metric(person, "Settled ✓", delta_color="off")
            else:
                st.success("✅ All balanced!")

            if txns:
                st.divider()
                st.subheader("🔁 Simplified Settlement Plan")
                st.caption("Minimum transactions to clear all debts")
                for t in txns:
                    c1,c2,c3 = st.columns([2,1,2])
                    c1.markdown(f"**{t['from']}**")
                    c2.markdown(f"→ {CURRENCY}{t['amount']:,.0f} →")
                    c3.markdown(f"**{t['to']}**")

    # ── ADD EXPENSE ────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add Shared Expense")
        group_options = {"No Group": ""}
        if not groups.empty and "Name" in groups.columns:
            for _, g in groups.iterrows():
                group_options[g["Name"]] = g.get("GroupID","")

        with st.form("split_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            desc     = c1.text_input("Title *", placeholder="e.g. Team Lunch")
            category = c2.selectbox("Category", EXPENSE_CATEGORIES)
            total    = c1.number_input(f"Total Amount ({CURRENCY}) *", min_value=0.0, step=100.0)
            paid_by  = c2.text_input("Paid By *", placeholder="Who paid the bill")
            grp_lbl  = st.selectbox("Group (optional)", list(group_options.keys()))
            method   = st.radio("Split Method", ["Equal","Percentage","Exact Amount"], horizontal=True)
            raw      = st.text_area("Participants (one per line) *", placeholder="Ahmed\nSara\nUsman", height=100)
            people   = [p.strip() for p in raw.split("\n") if p.strip()]
            notes    = st.text_input("Notes", placeholder="Optional")

            shares = None
            if method != "Equal" and people and total > 0:
                st.write(f"**Enter {'% for each' if method=='Percentage' else 'amount for each'}:**")
                shares = []
                scols = st.columns(min(len(people), 4))
                for i, p in enumerate(people):
                    default = round(100/len(people), 1) if method=="Percentage" else round(total/len(people), 0)
                    step    = 0.1 if method == "Percentage" else 100.0
                    v = scols[i%4].number_input(p, min_value=0.0, value=float(default), step=step, key=f"sh_{i}")
                    shares.append(v)

            if st.form_submit_button("➕ Add Split Expense", type="primary", use_container_width=True):
                if not desc: st.error("Title required.")
                elif not paid_by: st.error("Paid By required.")
                elif len(people) < 2: st.error("Need at least 2 participants.")
                elif total <= 0: st.error("Amount must be > 0.")
                else:
                    try:
                        result = calculate_split(total, people, method, shares)
                        add_split({
                            "group_id":    group_options[grp_lbl],
                            "description": desc,
                            "total_amount": total,
                            "split_type":  method,
                            "category":    category,
                            "participants": json.dumps(list(result.keys())),
                            "shares":       json.dumps(list(result.values())),
                            "paid_by":     paid_by,
                            "notes":       notes,
                            "receipt_url": "",
                        })
                        st.success("✅ Expense added!")
                        st.write("**Breakdown:**")
                        for person, amt in result.items():
                            st.write(f"• **{person}** owes {CURRENCY}{amt:,.0f}")
                    except ValueError as e:
                        st.error(str(e))

    # ── GROUPS ─────────────────────────────────────────────────────────
    with tab_groups:
        st.subheader("Expense Groups")
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Create New Group**")
            with st.form("group_form", clear_on_submit=True):
                gname    = st.text_input("Group Name *", placeholder="e.g. Office Team")
                gdesc    = st.text_input("Description")
                gmembers = st.text_area("Members (one per line)", placeholder="Ahmed\nSara\nUsman", height=80)
                if st.form_submit_button("Create Group", type="primary", use_container_width=True):
                    if not gname: st.error("Name required.")
                    else:
                        members = [m.strip() for m in gmembers.split("\n") if m.strip()]
                        add_group({"name": gname, "description": gdesc, "members": json.dumps(members)})
                        st.success(f"Group '{gname}' created!")
        with col2:
            st.write("**Existing Groups**")
            groups = get_groups()
            if groups.empty: st.info("No groups yet.")
            else:
                for _, g in groups.iterrows():
                    with st.expander(f"**{g.get('Name','')}**"):
                        st.write(f"Description: {g.get('Description','—')}")
                        try:
                            members = json.loads(g.get("Members","[]"))
                            st.write(f"Members: {', '.join(members)}")
                        except: pass

    # ── SETTLE UP ──────────────────────────────────────────────────────
    with tab_settle:
        st.subheader("Settle Debts")
        splits = get_splits()
        if splits.empty:
            st.info("No splits to settle.")
        else:
            unsettled = splits[splits.get("Status", pd.Series(dtype=str)) != "settled"] if "Status" in splits.columns else splits
            if unsettled.empty:
                st.success("✅ Everything is settled!")
            else:
                balances = compute_balances(splits)
                txns     = simplify_debts(balances)

                if txns:
                    st.write("**Suggested Settlements:**")
                    tx_labels = [f"{t['from']} → {t['to']}: {CURRENCY}{t['amount']:,.0f}" for t in txns]
                    sel_tx    = st.selectbox("Select settlement to record", tx_labels)
                    tx_idx    = tx_labels.index(sel_tx)
                    selected  = txns[tx_idx]

                    with st.form("settle_form", clear_on_submit=True):
                        st.info(f"**{selected['from']}** pays **{CURRENCY}{selected['amount']:,.0f}** to **{selected['to']}**")
                        amt_paid   = st.number_input(f"Amount ({CURRENCY})", min_value=0.0, value=float(selected["amount"]), step=100.0)
                        settle_note= st.text_input("Note", placeholder="e.g. Paid via JazzCash")
                        if st.form_submit_button("✅ Record Settlement", type="primary", use_container_width=True):
                            count = 0
                            for _, row in unsettled.iterrows():
                                try:
                                    parts = json.loads(row.get("Participants","[]"))
                                    if selected["from"] in parts or selected["to"] in parts:
                                        settle_split(str(row.get("SplitID", row.get("Timestamp",""))), selected["from"], amt_paid)
                                        count += 1
                                except: continue
                            if count:
                                st.success(f"✅ {count} split(s) marked settled!")
                                st.rerun()

                st.divider()
                st.subheader("All Unsettled Expenses")
                for _, row in unsettled.iterrows():
                    split_id = str(row.get("SplitID", row.get("Timestamp","")))
                    with st.expander(f"**{row.get('Description','')}** — {CURRENCY}{row.get('TotalAmount',0):,.0f} | Paid by {row.get('PaidBy','')}"):
                        try:
                            parts  = json.loads(row.get("Participants","[]"))
                            shares = json.loads(row.get("Shares","[]"))
                            for p, s in zip(parts, shares):
                                st.write(f"• **{p}** owes {CURRENCY}{s:,.0f}")
                        except: st.write("Could not parse details.")
                        st.caption(f"Category: {row.get('Category','—')} | Type: {row.get('SplitType','—')}")
                        bc1, bc2 = st.columns(2)
                        if bc1.button("✅ Settle", key=f"s_{split_id}"):
                            settle_split(split_id, user.get("name",""), 0)
                            st.rerun()
                        if bc2.button("🗑️ Delete", key=f"d_{split_id}"):
                            delete_split(split_id)
                            st.rerun()

    # ── HISTORY ────────────────────────────────────────────────────────
    with tab_history:
        st.subheader("All Split Expenses")
        splits = get_splits()
        if splits.empty:
            st.info("No history yet.")
            return
        c1, c2 = st.columns(2)
        status_f = c1.selectbox("Status", ["All","unsettled","settled"])
        df = splits.copy()
        if status_f != "All" and "Status" in df.columns:
            df = df[df["Status"] == status_f]
        dcols = [c for c in ["Description","TotalAmount","SplitType","Category","PaidBy","Status"] if c in df.columns]
        st.dataframe(df[dcols], use_container_width=True, hide_index=True)
        st.download_button("Export CSV", df.to_csv(index=False).encode(), "splits.csv", "text/csv")
        st.divider()
        st.subheader("Settlement History")
        settlements = get_settlements()
        if not settlements.empty:
            st.dataframe(settlements, use_container_width=True, hide_index=True)
        else:
            st.info("No settlements recorded yet.")
'''

open("pages/split_expenses.py", "w").write(content.strip())
print("split_expenses.py written! Lines:", len(content.strip().split("\n")))
