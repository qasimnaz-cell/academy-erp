import streamlit as st
from modules.auth import get_current_user
from modules.config import APP_TITLE, APP_VERSION, SPREADSHEET_ID, SHEETS, COURSES, EXPENSE_CATEGORIES

def _get_users():
    try:
        raw = st.secrets.get("APP_USERS", "")
        users = {}
        for u in raw.split(","):
            parts = u.strip().split(":")
            if len(parts) == 3:
                users[parts[0].strip()] = {"password": parts[1].strip(), "role": parts[2].strip()}
        return users
    except:
        return {}

def render():
    st.title("Settings")
    user = get_current_user()
    tab_users, tab_app, tab_sheets = st.tabs(["👥 User Management", "ℹ️ App Info", "🔗 Sheets"])

    with tab_users:
        if user.get("role") != "admin":
            st.warning("Admin access required.")
            return

        users = _get_users()
        st.subheader("Current Users")
        if users:
            for email, info in users.items():
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{email}** — `{info['role'].upper()}`")
                c2.markdown("🔒 password set")
        else:
            st.info("No users configured.")

        st.divider()
        st.subheader("Add New User")
        with st.form("add_user_form"):
            c1, c2, c3 = st.columns(3)
            new_email = c1.text_input("Email")
            new_pass  = c2.text_input("Password")
            new_role  = c3.selectbox("Role", ["admin","finance","staff","viewer"])
            existing  = st.text_area("Current APP_USERS (paste from Streamlit secrets)", height=60)
            if st.form_submit_button("Generate New APP_USERS", type="primary"):
                if not new_email or not new_pass:
                    st.error("Email and password required.")
                else:
                    sep = "," if existing.strip() else ""
                    updated = f"{existing.strip()}{sep}{new_email}:{new_pass}:{new_role}"
                    st.success("Copy this into Streamlit secrets as APP_USERS then reboot:")
                    st.code(updated)

        st.divider()
        st.subheader("Remove User")
        with st.form("del_user_form"):
            existing2 = st.text_area("Current APP_USERS", height=60, key="del_ex")
            del_email = st.text_input("Email to remove")
            if st.form_submit_button("Generate Updated APP_USERS", type="secondary"):
                if not del_email:
                    st.error("Enter email to remove.")
                else:
                    parts = [u for u in existing2.split(",") if not u.strip().startswith(del_email)]
                    st.success("Copy this into Streamlit secrets as APP_USERS then reboot:")
                    st.code(",".join(parts))

        st.divider()
        st.subheader("Change Password")
        with st.form("pwd_form"):
            existing3 = st.text_area("Current APP_USERS", height=60, key="pwd_ex")
            upd_email = st.text_input("Email to update")
            new_pwd   = st.text_input("New Password")
            if st.form_submit_button("Generate Updated APP_USERS", type="secondary"):
                if not upd_email or not new_pwd:
                    st.error("Both fields required.")
                else:
                    parts = []
                    for u in existing3.split(","):
                        p = u.strip().split(":")
                        if len(p) == 3 and p[0].strip() == upd_email:
                            parts.append(f"{p[0].strip()}:{new_pwd}:{p[2].strip()}")
                        else:
                            parts.append(u.strip())
                    st.success("Copy this into Streamlit secrets as APP_USERS then reboot:")
                    st.code(",".join(parts))

    with tab_app:
        c1,c2,c3 = st.columns(3)
        c1.metric("App", APP_TITLE)
        c2.metric("Version", APP_VERSION)
        c3.metric("Your Role", user.get("role","viewer").capitalize())
        st.divider()
        st.write(f"**Logged in as:** {user.get('name','')} ({user.get('email','')})")

    with tab_sheets:
        if SPREADSHEET_ID:
            st.success("Google Sheets Connected")
            st.code(f"ID: {SPREADSHEET_ID}")
            for k,v in SHEETS.items():
                st.write(f"• {v}")
        else:
            st.error("Not connected")
        st.divider()
        col1,col2 = st.columns(2)
        with col1:
            st.subheader("Courses")
            for c in COURSES: st.write(f"• {c}")
        with col2:
            st.subheader("Expense Categories")
            for c in EXPENSE_CATEGORIES: st.write(f"• {c}")
