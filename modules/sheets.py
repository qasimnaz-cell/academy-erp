"""
modules/sheets.py
Google Sheets as database — full CRUD layer via gspread.
Uses service account credentials for server-to-server auth.
"""
import gspread
import pandas as pd
import streamlit as st
from datetime import datetime
from google.oauth2.service_account import Credentials
from modules.config import SERVICE_ACCOUNT_FILE, SPREADSHEET_ID, SHEETS

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource(ttl=300)
def _get_client():
    """Return an authenticated gspread client (cached 5 min)."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource(ttl=300)
def _get_spreadsheet():
    return _get_client().open_by_key(SPREADSHEET_ID)


def _worksheet(name: str):
    return _get_spreadsheet().worksheet(SHEETS[name])


# ─── Generic helpers ────────────────────────────────────────────────────────

def sheet_to_df(sheet_name: str) -> pd.DataFrame:
    """Read entire sheet → DataFrame. Caches for 60 s."""
    ws = _worksheet(sheet_name)
    data = ws.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame()


def append_row(sheet_name: str, row: list):
    """Append a single row to a sheet."""
    _worksheet(sheet_name).append_row(row, value_input_option="USER_ENTERED")
    _clear_cache()


def update_row(sheet_name: str, row_index: int, values: list):
    """Update an existing row (1-indexed, includes header)."""
    ws = _worksheet(sheet_name)
    ws.update(f"A{row_index}", [values])
    _clear_cache()


def delete_row(sheet_name: str, row_index: int):
    """Delete a row by index."""
    _worksheet(sheet_name).delete_rows(row_index)
    _clear_cache()


def find_row_index(sheet_name: str, col: int, value: str) -> int | None:
    """Find 1-indexed row where column col == value. Returns None if not found."""
    ws = _worksheet(sheet_name)
    cell = ws.find(value, in_column=col)
    return cell.row if cell else None


def _clear_cache():
    st.cache_resource.clear()


# ─── Students ───────────────────────────────────────────────────────────────

def get_students() -> pd.DataFrame:
    df = sheet_to_df("students")
    if df.empty:
        return df
    df["MonthlyFee"]  = pd.to_numeric(df.get("MonthlyFee", 0),  errors="coerce").fillna(0)
    df["PaidAmount"]  = pd.to_numeric(df.get("PaidAmount", 0),  errors="coerce").fillna(0)
    df["Balance"]     = df["MonthlyFee"] - df["PaidAmount"]
    return df


def add_student(data: dict) -> str:
    """Add student, return generated StudentID."""
    sid = f"STU-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    row = [
        sid,
        data["name"],
        data["contact"],
        data["email"],
        data["course"],
        data["monthly_fee"],
        0,          # PaidAmount
        data["monthly_fee"],  # Balance
        data.get("enrollment_date", datetime.today().strftime("%Y-%m-%d")),
        "Active",
    ]
    append_row("students", row)
    return sid


def record_payment(student_id: str, amount: float, note: str = ""):
    """Record a payment and update student balance."""
    df = get_students()
    row = df[df["StudentID"] == student_id]
    if row.empty:
        raise ValueError(f"Student {student_id} not found")

    idx   = row.index[0]
    paid  = float(row.iloc[0]["PaidAmount"]) + amount
    fee   = float(row.iloc[0]["MonthlyFee"])
    bal   = fee - paid

    # Update student row
    sheet_row_index = idx + 2   # +1 for header, +1 for 1-index
    ws = _worksheet("students")
    ws.update_cell(sheet_row_index, 7, paid)   # PaidAmount col
    ws.update_cell(sheet_row_index, 8, bal)    # Balance col

    # Append payment log
    append_row("payments", [
        datetime.now().isoformat(),
        student_id,
        row.iloc[0]["Name"],
        amount,
        paid,
        bal,
        note,
        "manual",
    ])
    _clear_cache()


# ─── Expenses ───────────────────────────────────────────────────────────────

def get_expenses() -> pd.DataFrame:
    df = sheet_to_df("expenses")
    if not df.empty:
        df["Amount"] = pd.to_numeric(df.get("Amount", 0), errors="coerce").fillna(0)
        df["Date"]   = pd.to_datetime(df.get("Date", ""), errors="coerce")
    return df


def add_expense(data: dict):
    row = [
        datetime.now().isoformat(),
        data["date"],
        data["description"],
        data["category"],
        data["amount"],
        data.get("paid_by", ""),
        data.get("receipt_url", ""),
        data.get("department", ""),
        data.get("is_recurring", False),
        data.get("notes", ""),
    ]
    append_row("expenses", row)


# ─── Revenue ────────────────────────────────────────────────────────────────

def get_revenue() -> pd.DataFrame:
    df = sheet_to_df("revenue")
    if not df.empty:
        df["Amount"] = pd.to_numeric(df.get("Amount", 0), errors="coerce").fillna(0)
        df["Date"]   = pd.to_datetime(df.get("Date", ""), errors="coerce")
    return df


def add_revenue(data: dict):
    row = [
        datetime.now().isoformat(),
        data["date"],
        data["source"],
        data["description"],
        data["amount"],
        data.get("notes", ""),
    ]
    append_row("revenue", row)


# ─── Split Expenses ──────────────────────────────────────────────────────────

def get_splits() -> pd.DataFrame:
    return sheet_to_df("splits")


def add_split(data: dict):
    row = [
        datetime.now().isoformat(),
        data["description"],
        data["total_amount"],
        data["split_type"],       # equal | percentage | custom
        data["participants"],     # JSON string
        data["shares"],           # JSON string
        data["paid_by"],
        "unsettled",
    ]
    append_row("splits", row)


def settle_split(split_id: str, settled_by: str):
    idx = find_row_index("splits", 1, split_id)
    if idx:
        ws = _worksheet("splits")
        ws.update_cell(idx, 8, "settled")
        append_row("settlements", [
            datetime.now().isoformat(), split_id, settled_by,
        ])
    _clear_cache()


# ─── Audit Log ───────────────────────────────────────────────────────────────

def audit_log(user: str, action: str, detail: str = ""):
    append_row("logs", [
        datetime.now().isoformat(), user, action, detail,
    ])
