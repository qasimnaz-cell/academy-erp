"""
modules/config.py
Central configuration — reads from .env via python-dotenv.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── App Identity ──────────────────────────────────────────────────────────
APP_TITLE   = "AcademyERP"
LOGO_ICON   = "🏦"
APP_VERSION = "1.0.0"

# ── Google OAuth ──────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")

# ── Google Sheets ─────────────────────────────────────────────────────────
SPREADSHEET_ID       = os.getenv("SPREADSHEET_ID", "")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "credentials/service_account.json")

SHEETS = {
    "students":    "Students",
    "payments":    "Payments",
    "expenses":    "Expenses",
    "revenue":     "Revenue",
    "splits":      "SplitExpenses",
    "settlements": "Settlements",
    "logs":        "AuditLogs",
}

# ── Google Apps Script ────────────────────────────────────────────────────
APPS_SCRIPT_URL = os.getenv("APPS_SCRIPT_URL", "")

# ── Google Drive ──────────────────────────────────────────────────────────
DRIVE_RECEIPTS_FOLDER = os.getenv("DRIVE_RECEIPTS_FOLDER", "")

# ── Finance ────────────────────────────────────────────────────────────────
CURRENCY     = "₨"
CURRENCY_CODE = "PKR"

EXPENSE_CATEGORIES = [
    "Salaries", "Rent", "Utilities", "Marketing",
    "Equipment", "Travel", "Events", "Software", "Miscellaneous",
]

REVENUE_STREAMS = [
    "Student Fees", "Workshops", "Sponsorships",
    "Course Sales", "Merchandise", "Other",
]

COURSES = [
    "Python Full Stack",
    "UI/UX Design",
    "Data Science",
    "Digital Marketing",
    "Mobile Development",
    "Cloud Engineering",
]

# ── Roles ──────────────────────────────────────────────────────────────────
ROLES = {
    "admin":   ["*"],
    "finance": ["dashboard", "students", "expenses", "revenue", "reports", "pnl", "analytics"],
    "staff":   ["dashboard", "students", "expenses"],
    "viewer":  ["dashboard", "analytics"],
}
