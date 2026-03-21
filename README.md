
```markdown
# 🤖 Nutrabay AI Hiring Pipeline

An end-to-end AI-powered recruitment automation system built for Nutrabay.
Automates resume screening, candidate shortlisting, availability collection,
and interview scheduling — all connected to Google Sheets.

---

## 📌 Features

- **AI Resume Screening** — Gemini AI scores and ranks resumes against a JD
- **Smart Shortlisting** — Admin reviews and confirms shortlisted candidates
- **Automated Emails** — Sends availability request emails to candidates & interviewers
- **Availability Tracking** — Tracks Google Form responses in real time
- **AI Interview Scheduling** — Gemini matches overlapping slots, handles conflicts
- **Confirmation Emails** — Sends interview confirmation with Google Meet link
- **Reschedule Support** — Admin can reassign slots with full availability reference
- **Dashboard** — Hiring funnel, fit distribution, score charts via Plotly

---

## 🗂️ Project Structure

```

nutrabay_hiring/
│
├── app.py                        \# Main Streamlit application
│
├── modules/
│   ├── screening.py              \# Gemini AI resume screening logic
│   ├── scheduling.py             \# Gemini AI interview slot matching
│   ├── sheets_handler.py         \# Google Sheets read/write operations
│   └── email_handler.py          \# Gmail SMTP email sending
│
├── credentials.json              \# Google Service Account key (not committed)
├── .env                          \# Environment variables (not committed)
├── requirements.txt              \# Python dependencies
└── README.md

```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| AI Model | Google Gemini 3.1 Flash preview |
| Database | Google Sheets (via gspread) |
| Email | Gmail SMTP |
| Charts | Plotly |
| PDF Parsing | pdfplumber |
| Language | Python 3.10+ |

---

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/AdityaC784/NUTRABAY_HIRING_ASSI.git
cd NUTRABAY_HIRING_ASSI
```


### 2. Install Dependencies

```bash
pip install -r requirements.txt
```


### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_SHEET_NAME=Nutrabay_Hiring_Pipeline
GMAIL_ADDRESS=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_gmail_app_password
AVAILABILITY_FORM_LINK=https://forms.gle/your_form_link
```


### 4. Set Up Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project → Enable **Google Sheets API** and **Google Drive API**
3. Create a **Service Account** → Download `credentials.json`
4. Place `credentials.json` in the project root
5. Share your Google Sheet with the service account email

### 5. Set Up Gmail App Password

1. Go to your Google Account → Security
2. Enable **2-Step Verification**
3. Go to **App Passwords** → Generate one for "Mail"
4. Use this as `GMAIL_APP_PASSWORD` in `.env`

### 6. Set Up Google Form

Create a Google Form with these exact fields:


| Field Label | Type |
| :-- | :-- |
| Full Name | Short answer |
| Email Address | Short answer |
| Role | Multiple choice (Candidate / Interviewer) |
| Available Time Slots | Paragraph |

- Link the form responses to your Google Sheet tab named **"Form Responses 1"**
- Copy the form link and set it as `AVAILABILITY_FORM_LINK` in `.env`


### 7. Run the Application

```bash
streamlit run app.py
```


---

## 🔄 Workflow

```
Step 1 — Setup
  └── Add interviewers (Name, Email, Department, Max interviews/day)

Step 2 — Resume Screening
  └── Paste JD + Upload PDFs + Enter candidate emails
  └── Gemini AI scores and ranks all resumes

Step 3 — Shortlist
  └── Admin reviews ranked results
  └── Tick candidates → Confirm Shortlist
  └── Emails sent to candidates + interviewers with availability form link

Step 4 — Availability Tracking
  └── Monitor who filled the Google Form
  └── Send reminders to pending candidates/interviewers

Step 5 — Interview Scheduling
  └── Click "Match Interview Slots"
  └── Gemini AI finds overlapping slots, resolves conflicts
  └── Admin can manually assign or reschedule

Step 6 — Confirmation
  └── Add Google Meet link
  └── Click "Send Confirmation Email"
  └── Both candidate and interviewer receive confirmation emails
```


---

## 📊 Google Sheets Structure

The system auto-creates these tabs in your Google Sheet:


| Sheet Tab | Purpose |
| :-- | :-- |
| `Screening Results` | All screened candidates with scores |
| `Interviewers` | Interviewer master data |
| `Form Responses 1` | Google Form availability responses |
| `Scheduled Interviews` | Matched interview slots + confirmation status |


---

## 🤖 AI Capabilities

### Resume Screening (Gemini)

- Extracts: name, experience, current role, notice period, achievements
- Scores: overall, skills, experience, education (0–100)
- Classifies: Strong Fit / Moderate Fit / Not Fit
- Lists: strengths and gaps per candidate


### Interview Scheduling (Gemini)

- Finds overlapping 1-hour slots for each candidate + interviewer
- Resolves double-booking by shifting conflicting slots
- Respects max interviews per day per interviewer
- Handles edge cases: No Overlap, Interviewer Full

---

## 📧 Email Automation

| Trigger | Recipients |
| :-- | :-- |
| Shortlist confirmed | Candidates + Interviewers (availability request) |
| Pending response | Individual reminder (manual trigger) |
| Slot confirmed | Candidate + Interviewer (confirmation + meet link) |
| Slot rescheduled | Candidate + Interviewer (updated confirmation) |


---

## 📸 Dashboard

- **Hiring Funnel** — Applied → Screened → Shortlisted → Scheduled
- **Fit Distribution** — Pie chart of Strong / Moderate / Not Fit
- **Score Distribution** — Bar chart ranked by overall score
- **Conversion Rates** — Stage-wise drop-off percentages

---

## 🔐 Environment Variables Reference

| Variable | Description |
| :-- | :-- |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GOOGLE_CREDENTIALS_PATH` | Path to service account JSON |
| `GOOGLE_SHEET_NAME` | Name of your Google Sheet |
| `GMAIL_ADDRESS` | Sender Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not account password) |
| `AVAILABILITY_FORM_LINK` | Public Google Form URL |


---

## 📦 requirements.txt

```
streamlit
pandas
plotly
google-generativeai
gspread
google-auth
pdfplumber
python-dotenv
```


---

## ⚠️ Important Notes

- Never commit `credentials.json` or `.env` to GitHub
- Add both to `.gitignore`
- Gmail App Password is different from your Gmail login password
- Google Form tab must be named exactly `Form Responses 1`
- Service account must have Editor access to the Google Sheet

---

## 👤 Author

Built as part of the Nutrabay AI Automation Internship Assessment.

---



## `.gitignore` to add alongside:

```gitignore
.env
credentials.json
__pycache__/
*.pyc
.DS_Store
venv/
```


