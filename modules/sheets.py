import os, json
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
        json_str = st.secrets.get("SERVICE_ACCOUNT_JSON", "")
        if json_str:
            creds = Credentials.from_service_account_info(json.loads(json_str), scopes=SCOPES)
        else:
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return gspread.authorize(creds)
    except: return None

def _ss():
    c = _get_client()
    if not c or not SPREADSHEET_ID: return None
    try: return c.open_by_key(SPREADSHEET_ID)
    except: return None

def sheet_to_df(name):
    try:
        ss = _ss()
        if not ss: return pd.DataFrame()
        data = ss.worksheet(SHEETS[name]).get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except: return pd.DataFrame()

def append_row(name, row):
    try:
        ss = _ss()
        if ss: ss.worksheet(SHEETS[name]).append_row(row, value_input_option="USER_ENTERED")
    except Exception as e: st.error(f"Save failed: {e}")

def find_row(name, col, value):
    try:
        ss = _ss()
        if not ss: return None
        cell = ss.worksheet(SHEETS[name]).find(str(value), in_column=col)
        return cell.row if cell else None
    except: return None

def update_cell(name, row, col, value):
    try:
        ss = _ss()
        if ss: ss.worksheet(SHEETS[name]).update_cell(row, col, value)
    except Exception as e: st.error(f"Update failed: {e}")

def delete_row(name, row):
    try:
        ss = _ss()
        if ss: ss.worksheet(SHEETS[name]).delete_rows(row)
    except Exception as e: st.error(f"Delete failed: {e}")

def get_students():
    df = sheet_to_df("students")
    if not df.empty:
        for c in ["MonthlyFee","PaidAmount"]:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        if "MonthlyFee" in df.columns and "PaidAmount" in df.columns:
            df["Balance"] = df["MonthlyFee"] - df["PaidAmount"]
    return df

def add_student(data):
    sid = f"STU-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    append_row("students", [sid, data["name"], data["contact"], data.get("email",""),
        data["course"], data["monthly_fee"], 0, data["monthly_fee"],
        data.get("enrollment_date",""), "Active"])
    return sid

def update_student(sid, data):
    idx = find_row("students", 1, sid)
    if idx:
        ss = _ss()
        if ss:
            ws = ss.worksheet(SHEETS["students"])
            ws.update_cell(idx, 2, data.get("name",""))
            ws.update_cell(idx, 3, data.get("contact",""))
            ws.update_cell(idx, 4, data.get("email",""))
            ws.update_cell(idx, 5, data.get("course",""))
            ws.update_cell(idx, 6, data.get("monthly_fee",0))
            ws.update_cell(idx, 10, data.get("status","Active"))

def record_payment(sid, amount, note=""):
    df = get_students()
    if df.empty or "StudentID" not in df.columns: return
    row = df[df["StudentID"]==sid]
    if row.empty: return
    idx = row.index[0]
    paid = float(row.iloc[0].get("PaidAmount",0)) + amount
    fee  = float(row.iloc[0].get("MonthlyFee",0))
    bal  = fee - paid
    ss = _ss()
    if ss:
        ws = ss.worksheet(SHEETS["students"])
        ws.update_cell(idx+2, 7, paid)
        ws.update_cell(idx+2, 8, bal)
    append_row("payments", [datetime.now().isoformat(), sid,
        row.iloc[0].get("Name",""), amount, paid, bal, note, "manual"])

def get_payments(): return sheet_to_df("payments")

def get_expenses():
    df = sheet_to_df("expenses")
    if not df.empty and "Amount" in df.columns:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    return df

def add_expense(data):
    append_row("expenses", [datetime.now().isoformat(), data["date"],
        data["description"], data["category"], data["amount"],
        data.get("paid_by",""), data.get("receipt_url",""),
        data.get("department",""), data.get("is_recurring",False), data.get("notes","")])

def update_expense(ts, data):
    idx = find_row("expenses", 1, ts)
    if idx:
        ss = _ss()
        if ss:
            ws = ss.worksheet(SHEETS["expenses"])
            ws.update_cell(idx,2,data["date"]); ws.update_cell(idx,3,data["description"])
            ws.update_cell(idx,4,data["category"]); ws.update_cell(idx,5,data["amount"])
            ws.update_cell(idx,6,data.get("paid_by","")); ws.update_cell(idx,10,data.get("notes",""))

def delete_expense(ts):
    idx = find_row("expenses", 1, ts)
    if idx: delete_row("expenses", idx)

def get_revenue():
    df = sheet_to_df("revenue")
    if not df.empty and "Amount" in df.columns:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    return df

def add_revenue(data):
    append_row("revenue", [datetime.now().isoformat(), data["date"],
        data["source"], data["description"], data["amount"], data.get("notes","")])

def update_revenue(ts, data):
    idx = find_row("revenue", 1, ts)
    if idx:
        ss = _ss()
        if ss:
            ws = ss.worksheet(SHEETS["revenue"])
            ws.update_cell(idx,2,data["date"]); ws.update_cell(idx,3,data["source"])
            ws.update_cell(idx,4,data["description"]); ws.update_cell(idx,5,data["amount"])

def delete_revenue(ts):
    idx = find_row("revenue", 1, ts)
    if idx: delete_row("revenue", idx)

def get_groups(): return sheet_to_df("groups")

def add_group(data):
    gid = f"GRP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    append_row("groups", [gid, data["name"], data.get("description",""),
        data.get("members",""), datetime.now().isoformat(), "active"])
    return gid

def get_splits():
    df = sheet_to_df("splits")
    if not df.empty and "TotalAmount" in df.columns:
        df["TotalAmount"] = pd.to_numeric(df["TotalAmount"], errors="coerce").fillna(0)
    return df

def add_split(data):
    sid = f"SPL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    append_row("splits", [sid, datetime.now().isoformat(),
        data.get("group_id",""), data["description"], data["total_amount"],
        data["split_type"], data.get("category",""), data["participants"],
        data["shares"], data["paid_by"], data.get("notes",""),
        data.get("receipt_url",""), "unsettled"])
    return sid

def settle_split(split_id, settled_by, amount=0):
    idx = find_row("splits", 1, split_id)
    if idx: update_cell("splits", idx, 13, "settled")
    append_row("settlements", [datetime.now().isoformat(), split_id, settled_by, amount, "paid"])

def delete_split(split_id):
    idx = find_row("splits", 1, split_id)
    if idx: delete_row("splits", idx)

def get_settlements(): return sheet_to_df("settlements")
def audit_log(user, action, detail=""): append_row("logs", [datetime.now().isoformat(), user, action, detail])