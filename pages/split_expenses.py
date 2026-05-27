import json
import streamlit as st
import pandas as pd
from datetime import datetime, date
from modules.sheets import get_groups, add_group, get_splits, add_split, settle_split, delete_split, get_settlements
from modules.auth import get_current_user
from modules.config import CURRENCY, EXPENSE_CATEGORIES

# ── Core calculation engine ────────────────────────────────────────────────

def get_group_balances(splits_df, group_id=None):
    """Returns {person: net_balance} — positive = gets back, negative = owes."""
    balances = {}
    if splits_df.empty: return balances
    df = splits_df.copy()
    if group_id:
        df = df[df.get("GroupID", pd.Series(dtype=str)) == group_id] if "GroupID" in df.columns else df
    for _, row in df.iterrows():
        if row.get("Status","") == "settled": continue
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

def simplify_debts(balances):
    """Greedy debt simplification — minimizes number of transactions."""
    creditors = sorted([(p,b) for p,b in balances.items() if b > 0.01],  key=lambda x: -x[1])
    debtors   = sorted([(p,-b) for p,b in balances.items() if b < -0.01], key=lambda x: -x[1])
    txns, i, j = [], 0, 0
    while i < len(creditors) and j < len(debtors):
        cr, credit = list(creditors[i])
        dr, debt   = list(debtors[j])
        amt = min(credit, debt)
        txns.append({"from": dr, "to": cr, "amount": round(amt, 2)})
        creditors[i] = (cr, round(credit - amt, 2))
        debtors[j]   = (dr, round(debt - amt, 2))
        if creditors[i][1] < 0.01: i += 1
        if debtors[j][1]   < 0.01: j += 1
    return txns

def calculate_split(total, people, method, shares=None):
    n = len(people)
    if not n: return {}
    if method == "Equal":
        each = round(total / n, 2)
        # fix rounding
        result = {p: each for p in people}
        diff = round(total - sum(result.values()), 2)
        if diff: result[people[0]] = round(result[people[0]] + diff, 2)
        return result
    if method == "Percentage":
        if not shares or abs(sum(shares)-100) > 0.1:
            raise ValueError("Percentages must sum to 100")
        return {p: round(total*s/100, 2) for p,s in zip(people, shares)}
    if method == "Exact Amount":
        if not shares or abs(sum(shares)-total) > 0.5:
            raise ValueError(f"Amounts must sum to {CURRENCY}{total:,.0f}")
        return {p: round(s, 2) for p,s in zip(people, shares)}
    return {}

# ── Main render ────────────────────────────────────────────────────────────

def render():
    st.title("🤝 Split Expenses")

    splits  = get_splits()
    groups  = get_groups()
    user    = get_current_user()
    me      = user.get("name", "Dev Admin")

    # Sidebar-style group selector
    group_map = {}
    if not groups.empty and "Name" in groups.columns:
        for _, g in groups.iterrows():
            group_map[g["Name"]] = g.get("GroupID","")

    view_options = ["🏠 All Expenses"] + [f"👥 {n}" for n in group_map.keys()]
    selected_view = st.sidebar.selectbox("View", view_options) if group_map else "🏠 All Expenses"

    selected_group_id = ""
    selected_group_name = ""
    if selected_view != "🏠 All Expenses":
        selected_group_name = selected_view.replace("👥 ","")
        selected_group_id   = group_map.get(selected_group_name,"")

    # Filter splits
    filtered_splits = splits.copy()
    if selected_group_id and "GroupID" in filtered_splits.columns:
        filtered_splits = filtered_splits[filtered_splits["GroupID"] == selected_group_id]

    # ── Top balance bar ────────────────────────────────────────────────
    balances = get_group_balances(filtered_splits, selected_group_id if selected_group_id else None)
    my_balance = balances.get(me, 0)

    if my_balance > 0:
        st.success(f"**Overall: you are owed {CURRENCY}{my_balance:,.0f}**")
    elif my_balance < 0:
        st.error(f"**Overall: you owe {CURRENCY}{abs(my_balance):,.0f}**")
    else:
        st.info("**Overall: you are all settled up ✅**")

    # Balance columns
    if balances:
        owes_you = {p: b for p,b in balances.items() if b < 0 and p != me}
        you_owe  = {p: b for p,b in balances.items() if b > 0 and p != me}

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**YOU OWE**")
            if not owes_you:
                st.caption("You don't owe anything")
            else:
                for person, amt in owes_you.items():
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:10px;background:#1e293b;border-radius:8px;margin:4px 0;border-left:3px solid #ef4444;">
                        <div style="width:36px;height:36px;border-radius:50%;background:#334155;display:flex;align-items:center;justify-content:center;font-weight:600;color:#f1f5f9;">{person[0].upper()}</div>
                        <div><div style="color:#f1f5f9;font-weight:500;">{person}</div><div style="color:#ef4444;font-size:13px;">you owe {CURRENCY}{abs(amt):,.0f}</div></div>
                    </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown("**YOU ARE OWED**")
            if not you_owe:
                st.caption("You are not owed anything")
            else:
                for person, amt in you_owe.items():
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:10px;background:#1e293b;border-radius:8px;margin:4px 0;border-left:3px solid #22c55e;">
                        <div style="width:36px;height:36px;border-radius:50%;background:#334155;display:flex;align-items:center;justify-content:center;font-weight:600;color:#f1f5f9;">{person[0].upper()}</div>
                        <div><div style="color:#f1f5f9;font-weight:500;">{person}</div><div style="color:#22c55e;font-size:13px;">owes you {CURRENCY}{amt:,.0f}</div></div>
                    </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Main tabs ──────────────────────────────────────────────────────
    tab_activity, tab_add, tab_settle, tab_groups, tab_balances = st.tabs([
        "📋 Activity", "➕ Add Expense", "✅ Settle Up", "👥 Groups", "📊 Balances"
    ])

    # ── ACTIVITY FEED ──────────────────────────────────────────────────
    with tab_activity:
        if filtered_splits.empty:
            st.info("No expenses yet. Use ➕ Add Expense to add your first shared expense.")
        else:
            # Sort by timestamp desc
            df = filtered_splits.copy()
            if "Timestamp" in df.columns:
                df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
                df = df.sort_values("Timestamp", ascending=False)

            # Group by month
            current_month = None
            for _, row in df.iterrows():
                ts = row.get("Timestamp", "")
                month_label = pd.to_datetime(ts).strftime("%B %Y") if pd.notna(ts) and ts != "" else "Unknown"
                if month_label != current_month:
                    st.markdown(f"**{month_label}**")
                    current_month = month_label

                paid_by = str(row.get("PaidBy",""))
                total   = float(row.get("TotalAmount", 0))
                desc    = row.get("Description","")
                status  = row.get("Status","unsettled")
                split_id= str(row.get("SplitID", row.get("Timestamp","")))

                # Calculate my share
                my_share = 0
                try:
                    parts  = json.loads(row.get("Participants","[]"))
                    shares = json.loads(row.get("Shares","[]"))
                    for p, s in zip(parts, shares):
                        if p == me: my_share = float(s)
                except: pass

                if paid_by == me:
                    lent = round(total - my_share, 2)
                    share_text = f"you lent {CURRENCY}{lent:,.0f}"
                    color = "#22c55e"
                else:
                    share_text = f"you borrowed {CURRENCY}{my_share:,.0f}"
                    color = "#ef4444"

                if status == "settled":
                    share_text = "settled ✓"
                    color = "#64748b"

                cat = row.get("Category","")
                cat_icon = {"Food":"🍽️","Rent":"🏠","Utilities":"⚡","Travel":"✈️","Software":"💻","Marketing":"📢","Salaries":"💼","Equipment":"🔧"}.get(cat,"📄")

                col_icon, col_info, col_amount, col_action = st.columns([0.5, 3, 1.5, 0.8])
                col_icon.markdown(f"<div style='font-size:24px;text-align:center;padding:8px 0'>{cat_icon}</div>", unsafe_allow_html=True)
                col_info.markdown(f"""
                <div style='padding:6px 0'>
                    <div style='color:#f1f5f9;font-weight:500;font-size:14px'>{desc}</div>
                    <div style='color:#64748b;font-size:12px'>{paid_by} paid {CURRENCY}{total:,.0f}</div>
                </div>""", unsafe_allow_html=True)
                col_amount.markdown(f"""
                <div style='text-align:right;padding:6px 0'>
                    <div style='color:#94a3b8;font-size:11px'>{paid_by} {"paid" if paid_by==me else "lent you"}</div>
                    <div style='color:{color};font-weight:600;font-size:14px'>{share_text}</div>
                </div>""", unsafe_allow_html=True)
                with col_action:
                    if status != "settled":
                        if st.button("✓", key=f"quick_settle_{split_id}", help="Mark settled"):
                            settle_split(split_id, me, total)
                            st.rerun()

                st.markdown("<hr style='margin:4px 0;border-color:#1e293b'>", unsafe_allow_html=True)

    # ── ADD EXPENSE ────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add an Expense")

        group_options = {"No Group": ""}
        if group_map:
            for n, gid in group_map.items():
                group_options[f"👥 {n}"] = gid

        with st.form("add_split_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            desc     = c1.text_input("Description *", placeholder="e.g. Roti, Office Rent, Petrol")
            category = c2.selectbox("Category", EXPENSE_CATEGORIES)
            total    = c1.number_input(f"Amount ({CURRENCY}) *", min_value=0.0, step=100.0)
            paid_by  = c2.text_input("Paid by *", placeholder="Who paid", value=me)
            grp_lbl  = st.selectbox("Group", list(group_options.keys()))
            exp_date = st.date_input("Date", value=date.today())

            method = st.radio("Split method", ["Equal","Percentage","Exact Amount"], horizontal=True)

            raw    = st.text_area("With you and:", placeholder="Enter one name per line\nAhmed\nSara\nUsman", height=90)
            people = [p.strip() for p in raw.split("\n") if p.strip()]
            # Add self if not in list
            all_people = list(dict.fromkeys([paid_by] + people)) if paid_by else people

            shares = None
            if method != "Equal" and all_people and total > 0:
                st.write(f"**{'Percentage' if method=='Percentage' else 'Amount'} for each person:**")
                shares = []
                scols  = st.columns(min(len(all_people), 4))
                for i, p in enumerate(all_people):
                    default = round(100/len(all_people), 1) if method == "Percentage" else round(total/len(all_people), 0)
                    v = scols[i%4].number_input(p, min_value=0.0, value=float(default),
                                                step=0.1 if method=="Percentage" else 100.0, key=f"sp_{i}")
                    shares.append(v)

            notes = st.text_input("Notes", placeholder="Optional")

            if st.form_submit_button("Save", type="primary", use_container_width=True):
                if not desc: st.error("Description required.")
                elif total <= 0: st.error("Amount must be > 0.")
                elif not paid_by: st.error("Paid by is required.")
                elif len(all_people) < 2: st.error("Add at least one other person.")
                else:
                    try:
                        result = calculate_split(total, all_people, method, shares)
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
                        st.success(f"✅ Expense added!")
                        st.write("**Split breakdown:**")
                        for person, amt in result.items():
                            icon = "✓ paid" if person == paid_by else "owes"
                            st.write(f"• **{person}** {icon} {CURRENCY}{amt:,.0f}")
                    except ValueError as e:
                        st.error(str(e))

    # ── SETTLE UP ──────────────────────────────────────────────────────
    with tab_settle:
        st.subheader("Settle Up")
        balances = get_group_balances(filtered_splits)
        txns     = simplify_debts(balances)

        if not txns:
            st.success("✅ All settled up! No pending payments.")
        else:
            st.write("**Suggested payments to settle all debts:**")
            for t in txns:
                col1, col2, col3, col4 = st.columns([2,0.5,2,1.5])
                col1.markdown(f"""
                <div style='background:#1e293b;border-radius:8px;padding:10px 14px;border-left:3px solid #ef4444'>
                    <div style='color:#94a3b8;font-size:11px'>PAYS</div>
                    <div style='color:#f1f5f9;font-weight:600'>{t["from"]}</div>
                </div>""", unsafe_allow_html=True)
                col2.markdown(f"<div style='text-align:center;padding-top:14px;color:#64748b'>→</div>", unsafe_allow_html=True)
                col3.markdown(f"""
                <div style='background:#1e293b;border-radius:8px;padding:10px 14px;border-left:3px solid #22c55e'>
                    <div style='color:#94a3b8;font-size:11px'>RECEIVES</div>
                    <div style='color:#f1f5f9;font-weight:600'>{t["to"]}</div>
                </div>""", unsafe_allow_html=True)
                col4.markdown(f"<div style='padding-top:8px;text-align:right;color:#2563eb;font-weight:600;font-size:16px'>{CURRENCY}{t['amount']:,.0f}</div>", unsafe_allow_html=True)
                st.write("")

            st.divider()
            st.write("**Record a settlement:**")
            tx_labels = [f"{t['from']} → {t['to']}: {CURRENCY}{t['amount']:,.0f}" for t in txns]
            sel_tx    = st.selectbox("Select", tx_labels)
            tx_idx    = tx_labels.index(sel_tx)
            selected  = txns[tx_idx]

            with st.form("settle_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                amt_paid   = c1.number_input(f"Amount ({CURRENCY})", min_value=0.0, value=float(selected["amount"]), step=100.0)
                settle_note= c2.text_input("Note", placeholder="e.g. Paid via JazzCash")
                if st.form_submit_button("✅ Record Settlement", type="primary", use_container_width=True):
                    settled = 0
                    for _, row in filtered_splits.iterrows():
                        if row.get("Status","") == "settled": continue
                        try:
                            parts = json.loads(row.get("Participants","[]"))
                            if selected["from"] in parts and selected["to"] in parts:
                                settle_split(str(row.get("SplitID", row.get("Timestamp",""))), selected["from"], amt_paid)
                                settled += 1
                        except: continue
                    if settled:
                        st.success(f"✅ {settled} expense(s) settled!")
                        st.rerun()
                    else:
                        st.warning("No matching unsettled splits found.")

    # ── GROUPS ─────────────────────────────────────────────────────────
    with tab_groups:
        col1, col2 = st.columns([1,1])
        with col1:
            st.subheader("Create Group")
            with st.form("group_form", clear_on_submit=True):
                gname    = st.text_input("Group Name *", placeholder="e.g. Office Team, Trip to Lahore")
                gdesc    = st.text_input("Description", placeholder="Optional")
                gmembers = st.text_area("Members (one per line)", placeholder=f"{me}\nAtif Khan\nSara", height=90)
                if st.form_submit_button("Create Group", type="primary", use_container_width=True):
                    if not gname: st.error("Name required.")
                    else:
                        members = [m.strip() for m in gmembers.split("\n") if m.strip()]
                        add_group({"name": gname, "description": gdesc, "members": json.dumps(members)})
                        st.success(f"✅ Group '{gname}' created!")
        with col2:
            st.subheader("Your Groups")
            groups = get_groups()
            if groups.empty:
                st.info("No groups yet.")
            else:
                for _, g in groups.iterrows():
                    with st.expander(f"👥 **{g.get('Name','')}**"):
                        st.caption(g.get("Description",""))
                        try:
                            members = json.loads(g.get("Members","[]"))
                            for m in members:
                                gb = get_group_balances(splits, g.get("GroupID","")).get(m,0)
                                color = "#22c55e" if gb > 0 else "#ef4444" if gb < 0 else "#64748b"
                                label = f"gets back {CURRENCY}{gb:,.0f}" if gb > 0 else f"owes {CURRENCY}{abs(gb):,.0f}" if gb < 0 else "settled"
                                st.markdown(f"<span style='color:{color}'>● {m} — {label}</span>", unsafe_allow_html=True)
                        except: pass

    # ── BALANCES ───────────────────────────────────────────────────────
    with tab_balances:
        st.subheader("Detailed Balances")
        all_balances = get_group_balances(filtered_splits)

        if not all_balances:
            st.info("No balance data yet.")
        else:
            for person, amount in sorted(all_balances.items(), key=lambda x: x[1]):
                if amount > 0:
                    bar_color = "#22c55e"
                    label     = f"gets back {CURRENCY}{amount:,.0f}"
                elif amount < 0:
                    bar_color = "#ef4444"
                    label     = f"owes {CURRENCY}{abs(amount):,.0f}"
                else:
                    bar_color = "#64748b"
                    label     = "settled ✓"

                st.markdown(f"""
                <div style="display:flex;align-items:center;justify-content:space-between;background:#1e293b;border-radius:8px;padding:12px 16px;margin:6px 0;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="width:40px;height:40px;border-radius:50%;background:#334155;display:flex;align-items:center;justify-content:center;font-weight:700;color:#f1f5f9;font-size:16px;">{person[0].upper()}</div>
                        <div style="font-size:15px;font-weight:500;color:#f1f5f9;">{person}</div>
                    </div>
                    <div style="font-size:15px;font-weight:600;color:{bar_color};">{label}</div>
                </div>""", unsafe_allow_html=True)

        st.divider()
        st.subheader("Settlement History")
        settlements = get_settlements()
        if not settlements.empty:
            st.dataframe(settlements, use_container_width=True, hide_index=True)
        else:
            st.info("No settlements recorded yet.")

        st.divider()
        if not filtered_splits.empty:
            cols = [c for c in ["Description","TotalAmount","SplitType","Category","PaidBy","Status"] if c in filtered_splits.columns]
            st.dataframe(filtered_splits[cols], use_container_width=True, hide_index=True)
            st.download_button("Export CSV", filtered_splits.to_csv(index=False).encode(), "splits.csv", "text/csv")