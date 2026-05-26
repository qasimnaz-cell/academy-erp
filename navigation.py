"""
modules/navigation.py
Renders the sidebar and returns the selected page key.
"""
import streamlit as st
from modules.auth import get_current_user, logout, has_permission
from modules.config import APP_TITLE


def render_sidebar() -> str:
    user = get_current_user()

    with st.sidebar:
        # ── Brand ──────────────────────────────────────────────────────
        st.markdown(f"## 🏦 {APP_TITLE}")
        st.caption("Finance & Office Platform")
        st.divider()

        # ── User chip ──────────────────────────────────────────────────
        if user:
            pic = user.get("picture", "")
            name = user.get("name", "User")
            role = user.get("role", "viewer").capitalize()
            if pic:
                st.markdown(
                    f'<img src="{pic}" width="32" style="border-radius:50%;margin-right:8px">'
                    f'<strong>{name}</strong><br><small>{role}</small>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"**{name}** · {role}")
            st.divider()

        # ── Nav ────────────────────────────────────────────────────────
        if "page" not in st.session_state:
            st.session_state["page"] = "dashboard"

        def nav_btn(label: str, key: str, icon: str):
            if has_permission(key):
                if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
                    st.session_state["page"] = key

        st.markdown("**Overview**")
        nav_btn("Dashboard",  "dashboard", "📊")
        nav_btn("Analytics",  "analytics", "📈")

        st.markdown("**Finance**")
        nav_btn("Student Fees",    "students",  "👥")
        nav_btn("Expenses",        "expenses",  "🧾")
        nav_btn("Revenue",         "revenue",   "💰")
        nav_btn("Split Expenses",  "split",     "🤝")

        st.markdown("**Reports**")
        nav_btn("Reports",       "reports", "📋")
        nav_btn("P&L Statement", "pnl",     "📑")

        st.markdown("**System**")
        nav_btn("Settings", "settings", "⚙️")

        st.divider()
        if st.button("🚪 Sign out", use_container_width=True):
            logout()

    return st.session_state.get("page", "dashboard")
