import streamlit as st
def apply_theme():
    st.markdown("""<style>
    #MainMenu,footer,header{visibility:hidden}
    .block-container{padding:1.5rem 2rem 2rem;max-width:1200px}
    section[data-testid="stSidebar"]{background:#0f172a!important;border-right:1px solid #1e293b}
    section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] span,section[data-testid="stSidebar"] div{color:#94a3b8!important}
    section[data-testid="stSidebar"] strong{color:#f1f5f9!important}
    section[data-testid="stSidebar"] .stButton>button{background:transparent!important;border:none!important;color:#94a3b8!important;text-align:left!important;padding:7px 12px!important;border-radius:7px!important;font-size:13px!important;width:100%!important}
    section[data-testid="stSidebar"] .stButton>button:hover{background:#1e293b!important;color:#f1f5f9!important}
    .stButton>button{border-radius:8px!important;font-weight:500!important;font-size:13px!important;padding:8px 16px!important;border:1px solid #334155!important;background:#1e293b!important;color:#f1f5f9!important;transition:all .15s!important}
    .stButton>button:hover{background:#2563eb!important;border-color:#2563eb!important;color:white!important}
    .stButton>button[kind="primary"]{background:#2563eb!important;border-color:#2563eb!important;color:white!important}
    [data-testid="metric-container"]{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:1rem 1.25rem}
    [data-testid="metric-container"] label{color:#94a3b8!important;font-size:11px!important;text-transform:uppercase;letter-spacing:.05em}
    [data-testid="stMetricValue"]{color:#f1f5f9!important;font-size:22px!important;font-weight:600!important}
    .stTextInput input,.stNumberInput input,.stTextArea textarea{background:#1e293b!important;border:1px solid #334155!important;border-radius:8px!important;color:#f1f5f9!important}
    .stTabs [data-baseweb="tab-list"]{background:#1e293b;border-radius:10px;padding:4px;gap:4px;border:none}
    .stTabs [data-baseweb="tab"]{border-radius:7px!important;color:#94a3b8!important;font-weight:500!important;font-size:13px!important;border:none!important}
    .stTabs [aria-selected="true"]{background:#2563eb!important;color:white!important}
    [data-testid="stDataFrame"]{border-radius:10px;border:1px solid #334155;overflow:hidden}
    hr{border-color:#1e293b!important;margin:1.5rem 0!important}
    h1{color:#f1f5f9!important;font-size:1.5rem!important;font-weight:600!important}
    h2{color:#e2e8f0!important;font-size:1.1rem!important;font-weight:600!important}
    p,li{color:#94a3b8!important}
    .stAlert{border-radius:10px!important}
    [data-testid="stForm"]{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:1.5rem!important}
    .stDownloadButton>button{background:#1e293b!important;border:1px solid #334155!important;color:#f1f5f9!important;border-radius:8px!important}
    .stDownloadButton>button:hover{background:#2563eb!important;border-color:#2563eb!important;color:white!important}
    </style>""", unsafe_allow_html=True)