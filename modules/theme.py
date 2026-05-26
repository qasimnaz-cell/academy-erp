"""
modules/theme.py
Injects custom CSS into Streamlit for production-grade UI.
"""
import streamlit as st


def apply_theme():
    st.markdown("""
    <style>
    /* Sidebar refinements */
    section[data-testid="stSidebar"] {
        background: var(--background-color);
        border-right: 1px solid rgba(128,128,128,.12);
    }
    /* Button upgrades */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all .15s;
    }
    /* Metric cards */
    [data-testid="metric-container"] {
        background: rgba(37,99,235,.05);
        border: 1px solid rgba(37,99,235,.15);
        border-radius: 10px;
        padding: 1rem;
    }
    /* Dataframe */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        font-weight: 500;
    }
    /* Hide Streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)
