import streamlit as st
import requests
import urllib.parse
import os
from modules.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, ROLES

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_INFO_URL  = "https://www.googleapis.com/oauth2/v2/userinfo"

def _get_secret(key, default=""):
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except:
        return os.getenv(key, default)

def _allowed_emails():
    raw = _get_secret("ALLOWED_EMAILS", "")
    return set(e.strip() for e in raw.split(",") if e.strip())

def _user_roles():
    raw = _get_secret("USER_ROLES", "")
    return {e.split(":")[0].strip(): e.split(":")[1].strip() for e in raw.split(",") if ":" in e}

def _build_auth_url():
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

def _exchange_code(code):
    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "grant_type":    "authorization_code",
    })
    return resp.json()

def _get_user_info(access_token):
    resp = requests.get(GOOGLE_INFO_URL, headers={"Authorization": f"Bearer {access_token}"})
    return resp.json()

def require_auth():
    dev_mode = _get_secret("DEV_MODE", "false").lower()
    if dev_mode == "true":
        if "user" not in st.session_state:
            st.session_state["user"] = {"email": "dev@academy.local", "name": "Dev Admin", "picture": "", "role": "admin"}
        return
    if "user" in st.session_state:
        return
    params = st.query_params
    if "code" in params:
        with st.spinner("Authenticating..."):
            try:
                tokens    = _exchange_code(params["code"])
                user_info = _get_user_info(tokens.get("access_token", ""))
                email     = user_info.get("email", "")
                allowed   = _allowed_emails()
                if allowed and email not in allowed:
                    st.error(f"Access denied. {email} is not authorized.")
                    st.stop()
                roles = _user_roles()
                st.session_state["user"] = {
                    "email": email, "name": user_info.get("name", email),
                    "picture": user_info.get("picture", ""), "role": roles.get(email, "viewer"),
                }
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Authentication failed: {e}")
                st.stop()
    _render_login()
    st.stop()

def _render_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<div style="text-align:center"><div style="font-size:48px">🏦</div><div style="font-size:24px;font-weight:700;color:#f1f5f9;">AcademyERP</div><div style="font-size:13px;color:#64748b;margin-top:4px;">Finance & Office Management Platform</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        auth_url = _build_auth_url()
        st.markdown(f'<a href="{auth_url}" target="_self" style="text-decoration:none;"><div style="background:#4285F4;color:white;padding:12px 24px;border-radius:8px;font-size:15px;font-weight:500;text-align:center;cursor:pointer;">🔑 Sign in with Google</div></a>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:12px;font-size:12px;color:#475569;">Only authorized accounts can access this platform</div>', unsafe_allow_html=True)

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