import streamlit as st
from modules.config import APP_TITLE, LOGO_ICON
from modules.theme import apply_theme
from modules.auth import require_auth
from modules.navigation import render_sidebar

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=LOGO_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
require_auth()
page = render_sidebar()

if page == "dashboard":
    from pages.dashboard import render
elif page == "students":
    from pages.students import render
elif page == "expenses":
    from pages.expenses import render
elif page == "split":
    from pages.split_expenses import render
elif page == "revenue":
    from pages.revenue import render
elif page == "reports":
    from pages.reports import render
elif page == "pnl":
    from pages.pnl import render
elif page == "analytics":
    from pages.analytics import render
elif page == "settings":
    from pages.settings import render
else:
    from pages.dashboard import render

render()
