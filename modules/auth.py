"""
modules/auth.py
Google OAuth 2.0 login for Streamlit.
Uses streamlit-oauth or manual flow depending on deployment.
"""
import streamlit as st
import requests
import urllib.parse
import os
from modules.config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI, ROLES,
)

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_INFO_URL  = "https://www.googleapis.com/oauth2/v2/userinfo"

# Allowlist: set in .env as comma-separated emails, or leave empty to allow any Google user
ALLOWED_EMAILS = set(
    e.strip() for e in os.getenv("ALLOWED_EMAILS", "").split(",") if e.strip()
)
USER_ROLES = {
    e.split(":")[0].strip(): e.split(":")[1].strip()
    for e in os.getenv("USER_ROLES", "").split(",")
    if ":" in e
}


def _build_auth_url() -> str:
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def _exchange_code(code: str) -> dict:
    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "grant_type":    "authorization_code",
    })
    return resp.json()


def _get_user_info(access_token: str) -> dict:
    resp = requests.get(
        GOOGLE_INFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return resp.json()


def require_auth():
    """
    Enforces authentication. Call at the top of app.py.
    In development (DEV_MODE=true in .env), auto-logs in as admin.
    """
    # Dev bypass
    if os.getenv("DEV_MODE", "false").lower() == "true":
        if "user" not in st.session_state:
            st.session_state["user"] = {
                "email": "dev@academy.local",
                "name":  "Dev Admin",
                "picture": "",
                "role": "admin",
            }
        return

    # Check if already logged in
    if "user" in st.session_state:
        return

    # Handle OAuth callback
    params = st.query_params
    if "code" in params:
        with st.spinner("Authenticating…"):
            tokens    = _exchange_code(params["code"])
            user_info = _get_user_info(tokens.get("access_token", ""))
            email     = user_info.get("email", "")

            if ALLOWED_EMAILS and email not in ALLOWED_EMAILS:
                st.error("⛔ Access denied. Your email is not authorized.")
                st.stop()

            role = USER_ROLES.get(email, "viewer")
            st.session_state["user"] = {
                "email":   email,
                "name":    user_info.get("name", email),
                "picture": user_info.get("picture", ""),
                "role":    role,
            }
            st.query_params.clear()
            st.rerun()

    # Show login page
    _render_login()
    st.stop()


def _render_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🏦 AcademyERP")
        st.markdown("Finance & Office Management Platform")
        st.markdown("---")
        st.markdown("Sign in with your Google account to continue.")
        auth_url = _build_auth_url()
        st.markdown(
            f'<a href="{auth_url}" target="_self">'
            f'<button style="background:#4285F4;color:white;border:none;padding:10px 20px;'
            f'border-radius:6px;cursor:pointer;font-size:14px;width:100%">'
            f'🔑 Sign in with Google</button></a>',
            unsafe_allow_html=True,
        )


def get_current_user() -> dict:
    return st.session_state.get("user", {})


def has_permission(page: str) -> bool:
    user = get_current_user()
    role = user.get("role", "viewer")
    allowed = ROLES.get(role, [])
    return "*" in allowed or page in allowed


def logout():
    st.session_state.pop("user", None)
    st.rerun()
