import streamlit as st
from modules.auth import get_current_user, logout, has_permission

def render_sidebar() -> str:
    user = get_current_user()
    with st.sidebar:
        st.markdown("""<div style="padding:.5rem 0 1.5rem;"><div style="font-size:20px;font-weight:700;color:#f1f5f9;">🏦 AcademyERP</div><div style="font-size:11px;color:#475569;margin-top:3px;">Finance & Office Platform</div></div>""", unsafe_allow_html=True)
        if user:
            name = user.get("name","User"); role = user.get("role","viewer").capitalize()
            st.markdown(f"""<div style="background:#1e293b;border-radius:8px;padding:8px 12px;margin-bottom:1.25rem;border:1px solid #334155;"><div style="font-size:13px;font-weight:600;color:#f1f5f9;">{name}</div><div style="font-size:11px;color:#2563eb;">{role}</div></div>""", unsafe_allow_html=True)
        if "page" not in st.session_state:
            st.session_state["page"] = "dashboard"
        def nav(label, key, icon):
            if has_permission(key):
                if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
                    st.session_state["page"] = key
                    st.rerun()
        st.markdown("<div style='font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.1em;padding:4px 0 2px;'>Overview</div>", unsafe_allow_html=True)
        nav("Dashboard","dashboard","📊"); nav("Analytics","analytics","📈")
        st.markdown("<div style='font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.1em;padding:12px 0 2px;'>Finance</div>", unsafe_allow_html=True)
        nav("Student Fees","students","👥"); nav("Expenses","expenses","🧾")
        nav("Revenue","revenue","💰"); nav("Split Expenses","split","🤝")
        st.markdown("<div style='font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.1em;padding:12px 0 2px;'>Reports</div>", unsafe_allow_html=True)
        nav("Reports","reports","📋"); nav("P&L Statement","pnl","📑")
        st.markdown("<div style='font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:.1em;padding:12px 0 2px;'>System</div>", unsafe_allow_html=True)
        nav("Settings","settings","⚙️")
        st.markdown("---")
        if st.button("🚪 Sign out", use_container_width=True, key="signout"): logout()
    return st.session_state.get("page","dashboard")