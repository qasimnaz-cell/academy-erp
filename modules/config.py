import os
from dotenv import load_dotenv
load_dotenv()

def _get(key, default=""):
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

APP_TITLE    = "AcademyERP"
LOGO_ICON    = "🏦"
APP_VERSION  = "1.0.0"

GOOGLE_CLIENT_ID     = _get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = _get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI  = _get("GOOGLE_REDIRECT_URI", "http://localhost:8501")
SPREADSHEET_ID       = _get("SPREADSHEET_ID")
SERVICE_ACCOUNT_FILE = _get("SERVICE_ACCOUNT_FILE", "credentials/service_account.json")
APPS_SCRIPT_URL      = _get("APPS_SCRIPT_URL")
DRIVE_RECEIPTS_FOLDER= _get("DRIVE_RECEIPTS_FOLDER")

SHEETS = {
    "students": "Students", "payments": "Payments",
    "expenses": "Expenses", "revenue": "Revenue",
    "splits": "SplitExpenses", "settlements": "Settlements", "logs": "AuditLogs",
}

CURRENCY      = "₨"
CURRENCY_CODE = "PKR"
EXPENSE_CATEGORIES = ["Salaries","Rent","Utilities","Marketing","Equipment","Travel","Events","Software","Miscellaneous"]
REVENUE_STREAMS    = ["Student Fees","Workshops","Sponsorships","Course Sales","Merchandise","Other"]
COURSES = ["Python Full Stack","UI/UX Design","Data Science","Digital Marketing","Mobile Development","Cloud Engineering"]
ROLES = {
    "admin":   ["*"],
    "finance": ["dashboard","students","expenses","revenue","reports","pnl","analytics"],
    "staff":   ["dashboard","students","expenses"],
    "viewer":  ["dashboard","analytics"],
}
