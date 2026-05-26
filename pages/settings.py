"""
pages/settings.py
App settings — API config, role management, sheet info.
"""
import streamlit as st
from modules.auth import get_current_user
from modules.config import APP_TITLE, APP_VERSION, SPREADSHEET_ID, SHEETS


def render():
    st.title("⚙️ Settings")

    user = get_current_user()
    if user.get("role") != "admin":
        st.warning("Admin access required to change settings.")
        return

    tab_gen, tab_sheets, tab_roles = st.tabs(["General", "Sheets Config", "Roles"])

    with tab_gen:
        st.subheader("Application Info")
        st.json({"app": APP_TITLE, "version": APP_VERSION,
                 "user": user.get("email", ""), "role": user.get("role", "")})

    with tab_sheets:
        st.subheader("Google Sheets Configuration")
        st.code(f"Spreadsheet ID: {SPREADSHEET_ID}")
        for key, name in SHEETS.items():
            st.write(f"• `{key}` → sheet: **{name}**")

    with tab_roles:
        st.subheader("Role Permissions")
        from modules.config import ROLES
        for role, pages in ROLES.items():
            st.write(f"**{role.capitalize()}**: {', '.join(pages)}")
