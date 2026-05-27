import streamlit as st
import hashlib
from modules.config import ROLES

def _get_secret(key, default=""):
    try:
        return st.secrets.get(key, default)
    except:
        return default

def require_auth():
    dev_mode = _get_secret("DEV_MODE", "false").lower()
    if dev_mode == "true":
        if "user" not in st.session_state:
            st.session_state["user"] = {
                "email": "admin@academy.local",
                "name":  "Admin",
                "picture": "",
                "role": "admin",
            }
        return

    if "user" in st.session_state:
        return

    _render_login()
    st.stop()

def _render_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('''
        <div style="text-align:center;margin-bottom:2rem;">
            <div style="font-size:48px">🏦</div>
            <div style="font-size:26px;font-weight:700;color:#f1f5f9;margin:8px 0;">AcademyERP</div>
            <div style="font-size:13px;color:#64748b;">Finance & Office Management Platform</div>
        </div>
        ''', unsafe_allow_html=True)

        # Get users from secrets
        users_raw = _get_secret("APP_USERS", "")
        # Format: email:password:role,email2:password2:role2
        users = {}
        for u in users_raw.split(","):
            parts = u.strip().split(":")
            if len(parts) == 3:
                users[parts[0].strip()] = {"password": parts[1].strip(), "role": parts[2].strip(), "name": parts[0].split("@")[0].title()}

        if not users:
            st.error("No users configured. Add APP_USERS to Streamlit secrets.")
            return

        with st.form("login_form"):
            email    = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", type="primary", use_container_width=True):
                if email in users:
                    stored = users[email]["password"]
                    if password == stored:
                        st.session_state["user"] = {
                            "email":   email,
                            "name":    users[email]["name"],
                            "picture": "",
                            "role":    users[email]["role"],
                        }
                        st.rerun()
                    else:
                        st.error("Incorrect password.")
                else:
                    st.error("Email not found.")

        st.markdown('<div style="text-align:center;margin-top:12px;font-size:12px;color:#475569;">Contact admin to get access</div>', unsafe_allow_html=True)

def get_current_user():
    return st.session_state.get("user", {})

def has_permission(page):
    user = get_current_user()
    role = user.get("role", "viewer")
    allowed = ROLES.get(role, [])
    return "*" in allowed or page in allowed

def logout():
    st.session_state.pop("user", None)
    st.rerun()