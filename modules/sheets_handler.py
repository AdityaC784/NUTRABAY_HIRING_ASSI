import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_client():
    creds = Credentials.from_service_account_file(
        os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
        scopes=SCOPES
    )
    return gspread.authorize(creds)

def get_or_create_sheet(sheet_name: str, tab_name: str):
    client = get_client()
    try:
        spreadsheet = client.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(sheet_name)
        spreadsheet.share(None, perm_type="anyone", role="writer")
    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=30)
    return worksheet

# ── Screening Results ──────────────────────────────────────────────────────────
SCREENING_HEADERS = [
    "Rank", "Candidate Name", "Email", "Overall Score",
    "Years of Experience", "Current Role", "Current Company",
    "Notice Period", "Employment Gap",
    "Quantified Achievements", "Strengths", "Gaps", "Recommendation", "Shortlisted"
]

def save_screening_results(results: list):
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Nutrabay_Hiring_Pipeline")
    ws = get_or_create_sheet(sheet_name, "Screening Results")
    ws.clear()
    ws.append_row(SCREENING_HEADERS)
    for i, r in enumerate(results, 1):
        row = [
            i,
            r.get("candidate_name", ""),
            r.get("email", ""),
            r.get("overall_score", 0),
            r.get("years_of_experience", ""),
            r.get("current_role", ""),
            r.get("current_company", ""),
            r.get("notice_period", ""),
            r.get("employment_gap", "None"),
            str(r.get("quantified_achievements", False)),
            " | ".join(r.get("strengths", [])),
            " | ".join(r.get("gaps", [])),
            r.get("recommendation", ""),
            "No"
        ]
        ws.append_row(row)
    return ws.spreadsheet.url

def read_screening_results() -> pd.DataFrame:
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Nutrabay_Hiring_Pipeline")
    ws = get_or_create_sheet(sheet_name, "Screening Results")
    data = ws.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame(columns=SCREENING_HEADERS)

def update_shortlist(shortlisted_names: list):
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Nutrabay_Hiring_Pipeline")
    ws = get_or_create_sheet(sheet_name, "Screening Results")
    records = ws.get_all_records()
    for i, record in enumerate(records, 2):
        status = "Yes" if record.get("Candidate Name") in shortlisted_names else "No"
        ws.update_cell(i, SCREENING_HEADERS.index("Shortlisted") + 1, status)

def read_shortlisted() -> pd.DataFrame:
    df = read_screening_results()
    if df.empty:
        return df
    return df[df["Shortlisted"] == "Yes"]

# ── Interviewer Master ─────────────────────────────────────────────────────────
INTERVIEWER_HEADERS = ["Name", "Email", "Department", "Max Interviews Per Day", "Preferred Slots"]

def save_interviewers(interviewers: list):
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Nutrabay_Hiring_Pipeline")
    ws = get_or_create_sheet(sheet_name, "Interviewers")
    ws.clear()
    ws.append_row(INTERVIEWER_HEADERS)
    for iv in interviewers:
        ws.append_row([
            iv.get("name", ""),
            iv.get("email", ""),
            iv.get("department", ""),
            iv.get("max_per_day", 3),
            iv.get("preferred_slots", "")
        ])

def read_interviewers() -> pd.DataFrame:
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Nutrabay_Hiring_Pipeline")
    ws = get_or_create_sheet(sheet_name, "Interviewers")
    data = ws.get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame(columns=INTERVIEWER_HEADERS)

# ── Availability Responses ─────────────────────────────────────────────────────
def read_availability_responses() -> pd.DataFrame:
    """Read responses from Google Form-linked sheet"""
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Nutrabay_Hiring_Pipeline")
    ws = get_or_create_sheet(sheet_name, "Form Responses 1")  # ✅ actual Google Form tab
    data = ws.get_all_records()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)

    # Rename columns to match what our code expects
    df = df.rename(columns={
        "Full Name": "Name",
        "Email Address": "Email",
        "Available Time Slots": "Available Slots",
        "Role": "Role"
    })
    df = df[df["Name"].astype(str).str.strip() != ""]
    df = df[df["Email"].astype(str).str.strip() != ""]
    return df.reset_index(drop=True)

def save_availability_response(name: str, email: str, role: str, slots: str):
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Nutrabay_Hiring_Pipeline")
    ws = get_or_create_sheet(sheet_name, "Availability Responses")
    if ws.row_count == 0 or not ws.get_all_values():
        ws.append_row(["Timestamp", "Name", "Email", "Role", "Available Slots"])
    from datetime import datetime
    ws.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        name, email, role, slots
    ])

# ── Schedule Results ───────────────────────────────────────────────────────────
def save_scheduled_slots(slots: list):
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Nutrabay_Hiring_Pipeline")
    ws = get_or_create_sheet(sheet_name, "Scheduled Interviews")
    ws.clear()
    ws.append_row(["Candidate", "Candidate Email", "Interviewer", "Interviewer Email", "Slot", "Reasoning", "Confirmed"])
    for s in slots:
        ws.append_row([
            s.get("candidate", ""),
            s.get("candidate_email", ""),
            s.get("interviewer", ""),
            s.get("interviewer_email", ""),
            s.get("slot", ""),
            s.get("reasoning", ""),
            s.get("confirmed", "No")
        ])

def confirm_slot(slot_index: int):
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Nutrabay_Hiring_Pipeline")
    ws = get_or_create_sheet(sheet_name, "Scheduled Interviews")
    ws.update_cell(slot_index + 2, 7, "Yes")
