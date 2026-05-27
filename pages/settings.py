import streamlit as st
from modules.auth import get_current_user
from modules.config import APP_TITLE, APP_VERSION, SPREADSHEET_ID, SHEETS, COURSES, EXPENSE_CATEGORIES

def render():
    st.title("⚙️ Settings")
    user = get_current_user()
    c1,c2,c3 = st.columns(3)
    c1.metric("App", APP_TITLE); c2.metric("Version", APP_VERSION)
    c3.metric("Your Role", user.get("role","viewer").capitalize())
    st.divider()
    st.subheader("Google Sheets")
    if SPREADSHEET_ID:
        st.success("Connected")
        st.code(f"ID: {SPREADSHEET_ID}")
    else:
        st.error("Not connected — add SPREADSHEET_ID to Streamlit secrets")
    st.divider()
    col1,col2 = st.columns(2)
    with col1:
        st.subheader("Courses"); [st.write(f"• {c}") for c in COURSES]
    with col2:
        st.subheader("Expense Categories"); [st.write(f"• {c}") for c in EXPENSE_CATEGORIES]