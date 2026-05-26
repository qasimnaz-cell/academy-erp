"""
pages/split_expenses.py
Splitwise-style shared expense splitting and settlement tracking.
"""
import json
import streamlit as st
import pandas as pd

from modules.sheets import get_splits, add_split, settle_split
from modules.auth import get_current_user
from modules.config import CURRENCY
from utils.finance import calculate_split, net_balances


def render():
    st.title("🤝 Split Expenses")
    st.caption("Splitwise-style shared expense management for departments and team members")

    tab_balance, tab_add, tab_history = st.tabs(["⚖️ Balances", "➕ Add Split", "📜 History"])

    # ── Tab 1: Balances ────────────────────────────────────────────────
    with tab_balance:
        splits = get_splits()
        st.subheader("Net Balances")

        if splits.empty:
            st.info("No shared expenses yet.")
        else:
            balances = net_balances(splits)
            if not balances:
                st.success("✅ All expenses are settled!")
            else:
                cols = st.columns(min(len(balances), 4))
                for i, (person, amount) in enumerate(sorted(balances.items(), key=lambda x: x[1])):
                    col = cols[i % len(cols)]
                    label = f"{CURRENCY}{abs(amount):,.0f}"
                    if amount > 0:
                        col.metric(person, label, "gets back", delta_color="normal")
                    else:
                        col.metric(person, label, "owes", delta_color="inverse")

        st.divider()
        st.subheader("Unsettled Splits")
        if not splits.empty:
            unsettled = splits[splits.get("Status", pd.Series(dtype=str)) != "settled"]
            if unsettled.empty:
                st.success("✅ All clear!")
            else:
                for _, row in unsettled.iterrows():
                    with st.expander(f"**{row.get('Description','')}** — {CURRENCY}{row.get('TotalAmount',0):,.0f} paid by {row.get('PaidBy','')}"):
                        try:
                            participants = json.loads(row.get("Participants", "[]"))
                            shares       = json.loads(row.get("Shares", "[]"))
                            for p, s in zip(participants, shares):
                                st.write(f"• **{p}** owes {CURRENCY}{s:,.0f}")
                        except Exception:
                            st.write("Could not parse split details.")

                        if st.button(f"✅ Mark as Settled", key=f"settle_{row.get('Timestamp','')}"):
                            user = get_current_user()
                            settle_split(str(row.get("Timestamp", "")), user.get("name", "unknown"))
                            st.rerun()

    # ── Tab 2: Add Split ────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add Shared Expense")

        with st.form("split_form"):
            desc         = st.text_input("Description *", placeholder="e.g. Team Lunch, Software License")
            total_amount = st.number_input(f"Total Amount ({CURRENCY}) *", min_value=0.0, step=100.0)
            paid_by      = st.text_input("Paid By *", placeholder="Name of person who paid")
            split_type   = st.radio("Split Method", ["equal", "percentage", "custom"], horizontal=True)

            participants_raw = st.text_area(
                "Participants (one per line) *",
                placeholder="Ahmed\nSara\nUsman",
                height=100,
            )
            participants = [p.strip() for p in participants_raw.split("\n") if p.strip()]

            shares_input = None
            if split_type in ("percentage", "custom") and participants:
                st.write(f"Enter {'percentages (must sum to 100)' if split_type=='percentage' else 'amounts (must sum to total)'}:")
                shares_input = []
                cols = st.columns(min(len(participants), 4))
                for i, person in enumerate(participants):
                    val = cols[i % len(cols)].number_input(
                        person,
                        min_value=0.0,
                        value=100.0 / len(participants) if split_type == "percentage" else total_amount / len(participants),
                        step=0.1 if split_type == "percentage" else 100.0,
                    )
                    shares_input.append(val)

            submitted = st.form_submit_button("Add Split", type="primary", use_container_width=True)
            if submitted:
                if not desc or not paid_by or not participants:
                    st.error("Description, paid by, and participants are required.")
                elif total_amount <= 0:
                    st.error("Amount must be > 0.")
                else:
                    try:
                        result = calculate_split(total_amount, participants, split_type, shares_input)
                        add_split({
                            "description":  desc,
                            "total_amount": total_amount,
                            "split_type":   split_type,
                            "participants": json.dumps(list(result.keys())),
                            "shares":       json.dumps(list(result.values())),
                            "paid_by":      paid_by,
                        })
                        st.success("✅ Split recorded!")
                        st.write("**Split breakdown:**")
                        for person, amount in result.items():
                            st.write(f"• **{person}**: {CURRENCY}{amount:,.0f}")
                    except ValueError as e:
                        st.error(str(e))

    # ── Tab 3: History ──────────────────────────────────────────────────
    with tab_history:
        splits = get_splits()
        if splits.empty:
            st.info("No split history yet.")
        else:
            display_cols = ["Timestamp", "Description", "TotalAmount", "SplitType", "PaidBy", "Status"]
            display_cols = [c for c in display_cols if c in splits.columns]
            st.dataframe(splits[display_cols], use_container_width=True, hide_index=True)
