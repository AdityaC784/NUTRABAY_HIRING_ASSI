# 🤖 Nutrabay AI Hiring Pipeline

AI-powered end-to-end hiring system — Resume Screening → Shortlisting → Interview Scheduling.
Covers Assessment Problems 1, 2, and 3 in a single Streamlit app.

---

## 📁 Project Structure

```
nutrabay_hiring/
├── app.py                    ← Main Streamlit app (run this)
├── modules/
│   ├── screening.py          ← AI resume scoring (Gemini)
│   ├── scheduling.py         ← Slot matching algorithm
│   ├── email_handler.py      ← Gmail email automation
│   └── sheets_handler.py     ← Google Sheets read/write
├── requirements.txt
├── .env.example              ← Copy to .env and fill values
└── README.md
```

---

## ⚙️ Setup Instructions

### Step 1 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Get API Keys

**A. Gemini API Key**
1. Go to https://aistudio.google.com
2. Click "Get API Key" → Create new key
3. Copy it to `.env` as `GEMINI_API_KEY`

**B. Gmail App Password**
1. Go to your Google Account → Security
2. Enable 2-Step Verification
3. Search "App passwords" → Create one for "Mail"
4. Copy the 16-character password to `.env`

**C. Google Sheets Service Account**
1. Go to https://console.cloud.google.com
2. Create a new project → Enable Sheets API + Drive API
3. Go to IAM → Service Accounts → Create Service Account
4. Download JSON key → save as `credentials.json` in project root
5. Copy the service account email (looks like: xxx@project.iam.gserviceaccount.com)
6. Share your Google Sheet with that email (Editor access)

**D. Google Form for Availability**
1. Create a Google Form with fields: Name, Email, Role (Candidate/Interviewer), Available Slots
2. Link it to a Google Sheet (Responses tab)
3. Copy the form URL to `.env` as `AVAILABILITY_FORM_LINK`

### Step 3 — Configure .env
```bash
cp .env.example .env
# Edit .env with your actual values
```

### Step 4 — Run the App
```bash
streamlit run app.py
```

---

## 🚀 How to Use

| Tab | What to Do |
|-----|-----------|
| ⚙️ Setup | Add interviewers (one time) |
| 📄 Screening | Upload JD + Resumes → Click Run |
| ✅ Shortlist | Tick candidates → Confirm (sends emails) |
| 📬 Availability | Monitor who filled the form |
| 📅 Schedule | Match slots → Send confirmations |
| 📊 Dashboard | View hiring funnel & stats |

---

## 📊 Output in Google Sheets

The app auto-creates and populates these tabs:
- `Screening Results` — ranked candidates with scores
- `Interviewers` — interviewer master list
- `Availability Responses` — form responses
- `Scheduled Interviews` — confirmed slots

---

## 🔮 Future Scope (Production)
- Connect directly to Nutrabay careers page form via webhook
- RAG-based semantic resume retrieval (ChromaDB) for 1000+ resumes
- Google Calendar auto-invite on slot confirmation
- Rebuild using Google MCP Server for full agentic automation
"# NUTRABAY_HIRING_ASS" 
