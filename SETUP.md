# AcademyERP — Complete Setup Guide (macOS)

## Prerequisites

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.12+
brew install python@3.12

# Verify
python3 --version   # should show 3.12.x
```

---

## 1. Project Setup

```bash
# Clone / create project
mkdir academy-erp && cd academy-erp

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Google Cloud Setup

### 2a. Create a Google Cloud Project
1. Go to https://console.cloud.google.com
2. Create new project: **AcademyERP**
3. Enable these APIs (APIs & Services → Library):
   - Google Sheets API
   - Google Drive API
   - Google OAuth 2.0

### 2b. Service Account (for Sheets + Drive)
```bash
# In Google Cloud Console:
# IAM & Admin → Service Accounts → Create Service Account
# Name: academy-erp-sa
# Role: Editor
# Download JSON key → save as credentials/service_account.json

mkdir -p credentials
# Move downloaded JSON here
mv ~/Downloads/your-key.json credentials/service_account.json
```

### 2c. OAuth 2.0 Credentials (for user login)
```bash
# APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
# Application type: Web application
# Authorized redirect URIs: http://localhost:8501
# Download → note Client ID and Client Secret
```

---

## 3. Google Sheets Database Setup

```bash
# Create a new Google Sheet at https://sheets.google.com
# Note the Spreadsheet ID from the URL

# Share the sheet with your service account email:
# (find it in credentials/service_account.json → "client_email")
# Sheet → Share → paste the email → Editor role
```

Then bootstrap the sheet headers by running the Apps Script (see step 5).

---

## 4. Environment Variables

```bash
cp .env.example .env
nano .env   # Fill in all values
```

Required values:
- `SPREADSHEET_ID` — from Google Sheets URL
- `SERVICE_ACCOUNT_FILE=credentials/service_account.json`
- `GOOGLE_CLIENT_ID` — from OAuth credentials
- `GOOGLE_CLIENT_SECRET` — from OAuth credentials
- `DRIVE_RECEIPTS_FOLDER` — Google Drive folder ID for receipts

---

## 5. Google Apps Script Deployment

1. Open your Google Sheet
2. Extensions → Apps Script
3. Delete default code, paste contents of `scripts/Code.gs`
4. Set script property:
   - Project Settings → Script Properties → Add Property
   - Key: `SPREADSHEET_ID`, Value: your sheet ID
5. Run `bootstrapSheets()` once (creates all sheet tabs with headers)
6. Deploy → New deployment → Web app
   - Execute as: **Me**
   - Who has access: **Anyone**
7. Copy deployment URL → paste into `.env` as `APPS_SCRIPT_URL`

---

## 6. Run Locally

```bash
source venv/bin/activate
streamlit run app.py

# App opens at http://localhost:8501
# Set DEV_MODE=true in .env to skip Google login during development
```

---

## 7. Deploy to Streamlit Community Cloud (Free)

```bash
# Push to GitHub first
git init
git add .
git commit -m "Initial AcademyERP setup"
git remote add origin https://github.com/yourusername/academy-erp.git
git push -u origin main
```

Then:
1. Go to https://share.streamlit.io
2. Connect GitHub → select repo → `app.py`
3. Add secrets (Settings → Secrets):
   ```toml
   SPREADSHEET_ID = "your-id"
   GOOGLE_CLIENT_ID = "your-client-id"
   GOOGLE_CLIENT_SECRET = "your-secret"
   GOOGLE_REDIRECT_URI = "https://your-app.streamlit.app"
   ALLOWED_EMAILS = "admin@youracademy.com"
   USER_ROLES = "admin@youracademy.com:admin"
   DEV_MODE = "false"
   ```
4. Add service account JSON as a secret:
   ```toml
   SERVICE_ACCOUNT_JSON = '''{ ...paste full JSON content... }'''
   ```
5. Deploy!

---

## 8. Useful Commands

```bash
# Activate environment
source venv/bin/activate

# Run app
streamlit run app.py

# Run with custom port
streamlit run app.py --server.port 8502

# Clear Streamlit cache
streamlit cache clear

# Update dependencies
pip install -r requirements.txt --upgrade

# Check what's installed
pip list | grep -E "streamlit|pandas|plotly|gspread"

# Run tests
python -m pytest tests/ -v

# Deactivate environment
deactivate
```

---

## 9. Folder Structure

```
academy-erp/
├── app.py                    # Streamlit entry point
├── requirements.txt
├── .env.example
├── .env                      # ← gitignored
├── .gitignore
├── .streamlit/
│   └── config.toml           # Theme + server config
├── credentials/
│   └── service_account.json  # ← gitignored
├── modules/
│   ├── __init__.py
│   ├── auth.py               # Google OAuth
│   ├── config.py             # All constants + env vars
│   ├── navigation.py         # Sidebar nav
│   ├── sheets.py             # Google Sheets CRUD layer
│   └── theme.py              # CSS injection
├── pages/
│   ├── dashboard.py          # Finance overview
│   ├── students.py           # Fee management
│   ├── expenses.py           # Expense tracker
│   ├── split_expenses.py     # Splitwise-style splitting
│   ├── revenue.py            # Revenue tracking
│   ├── reports.py            # Report generation
│   ├── pnl.py                # P&L statement
│   ├── analytics.py          # Advanced analytics
│   └── settings.py           # App settings
├── utils/
│   ├── finance.py            # Pure financial calculations
│   ├── pdf_report.py         # ReportLab PDF generation
│   └── drive_upload.py       # Google Drive file upload
├── scripts/
│   └── Code.gs               # Google Apps Script backend
├── reports/                  # Generated reports (gitignored)
├── assets/                   # Static files
└── tests/
    └── test_finance.py
```

---

## 10. Google Sheets Schema

| Sheet | Columns |
|-------|---------|
| Students | StudentID, Name, Contact, Email, Course, MonthlyFee, PaidAmount, Balance, EnrollmentDate, Status |
| Payments | Timestamp, StudentID, Name, Amount, TotalPaid, Balance, Note, Source |
| Expenses | Timestamp, Date, Description, Category, Amount, PaidBy, Receipt, Department, IsRecurring, Notes |
| Revenue | Timestamp, Date, Source, Description, Amount, Notes |
| SplitExpenses | SplitID, Timestamp, Description, TotalAmount, SplitType, Participants, Shares, PaidBy, Status |
| Settlements | Timestamp, SplitID, SettledBy |
| AuditLogs | Timestamp, User, Action, Detail |

---

## Troubleshooting

```bash
# Google Sheets auth error
# → Check service account email is shared on the sheet with Editor access

# OAuth redirect error
# → Ensure GOOGLE_REDIRECT_URI in .env matches exactly what's in Google Cloud Console

# Module not found
pip install -r requirements.txt

# Streamlit won't start
streamlit --version
# If old: pip install streamlit --upgrade

# Check .env is loaded
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('SPREADSHEET_ID'))"
```
