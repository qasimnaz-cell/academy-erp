import os
import gspread
import pandas as pd
import streamlit as st
from datetime import datetime
from modules.config import SERVICE_ACCOUNT_FILE, SPREADSHEET_ID, SHEETS

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def _get_client():
    from google.oauth2.service_account import Credentials
    try:
        import json
        json_str = st.secrets.get("SERVICE_ACCOUNT_JSON", "")
        if json_str:
            info = json.loads(json_str)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        return None

def sheet_to_df(sheet_name: str) -> pd.DataFrame:
    try:
        client = _get_client()
        if not client or not SPREADSHEET_ID:
            return pd.DataFrame()
        ws = client.open_by_key(SPREADSHEET_ID).worksheet(SHEETS[sheet_name])
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def append_row(sheet_name: str, row: list):
    try:
        client = _get_client()
        if client and SPREADSHEET_ID:
            client.open_by_key(SPREADSHEET_ID).worksheet(SHEETS[sheet_name]).append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        st.error(f"Could not save: {e}")

def get_students() -> pd.DataFrame:
    df = sheet_to_df("students")
    if not df.empty:
        df["MonthlyFee"] = pd.to_numeric(df.get("MonthlyFee", 0), errors="coerce").fillna(0)
        df["PaidAmount"] = pd.to_numeric(df.get("PaidAmount", 0), errors="coerce").fillna(0)
        df["Balance"] = df["MonthlyFee"] - df["PaidAmount"]
    return df

def get_expenses() -> pd.DataFrame:
    df = sheet_to_df("expenses")
    if not df.empty:
        df["Amount"] = pd.to_numeric(df.get("Amount", 0), errors="coerce").fillna(0)
        df["Date"] = pd.to_datetime(df.get("Date", ""), errors="coerce")
    return df

def get_revenue() -> pd.DataFrame:
    df = sheet_to_df("revenue")
    if not df.empty:
        df["Amount"] = pd.to_numeric(df.get("Amount", 0), errors="coerce").fillna(0)
        df["Date"] = pd.to_datetime(df.get("Date", ""), errors="coerce")
    return df

def get_splits() -> pd.DataFrame:
    return sheet_to_df("splits")

def add_student(data: dict) -> str:
    sid = f"STU-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    append_row("students", [sid, data["name"], data["contact"], data.get("email",""), data["course"], data["monthly_fee"], 0, data["monthly_fee"], data.get("enrollment_date",""), "Active"])
    return sid

def record_payment(student_id: str, amount: float, note: str = ""):
    append_row("payments", [datetime.now().isoformat(), student_id, "", amount, "", "", note, "manual"])

def add_expense(data: dict):
    append_row("expenses", [datetime.now().isoformat(), data["date"], data["description"], data["category"], data["amount"], data.get("paid_by",""), data.get("receipt_url",""), data.get("department",""), data.get("is_recurring",False), data.get("notes","")])

def add_revenue(data: dict):
    append_row("revenue", [datetime.now().isoformat(), data["date"], data["source"], data["description"], data["amount"], data.get("notes","")])

def add_split(data: dict):
    append_row("splits", [datetime.now().isoformat(), data["description"], data["total_amount"], data["split_type"], data["participants"], data["shares"], data["paid_by"], "unsettled"])

def settle_split(split_id: str, settled_by: str):
    pass

def audit_log(user: str, action: str, detail: str = ""):
    append_row("logs", [datetime.now().isoformat(), user, action, detail])
