import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def build_schedule_from_responses(
    availability_df: pd.DataFrame,
    shortlisted_df: pd.DataFrame,
    interviewers_df: pd.DataFrame
) -> list:

    candidates = availability_df[availability_df["Role"] == "Candidate"]
    interviewers = availability_df[availability_df["Role"] == "Interviewer"]

    if candidates.empty or interviewers.empty:
        return []

    # Build readable availability text for Gemini
    cand_text = "\n".join(
        f"- {row['Name']} (email: {row['Email']}): {row['Available Slots']}"
        for _, row in candidates.iterrows()
    )
    iv_text = "\n".join(
        f"- {row['Name']} (email: {row['Email']}, max {interviewers_df[interviewers_df['Email'].str.lower() == row['Email'].lower()]['Max Interviews Per Day'].values[0] if not interviewers_df[interviewers_df['Email'].str.lower() == row['Email'].lower()].empty else 3} interviews/day): {row['Available Slots']}"
        for _, row in interviewers.iterrows()
    )

    prompt = f"""You are an expert interview scheduling assistant.

CANDIDATES AVAILABILITY:
{cand_text}

INTERVIEWERS AVAILABILITY:
{iv_text}

SCHEDULING RULES (follow strictly):
1. Find best overlapping 1-hour slot for each candidate with an interviewer
2. NO two candidates can be assigned the same interviewer at the same time
   - If conflict: assign first candidate that slot, shift second candidate to next available window
   - Example: Both want Tue 1PM-2PM → Candidate A gets Tue 1PM-2PM, Candidate B gets Tue 2PM-3PM
3. Respect max interviews per day per interviewer
   - If interviewer is fully booked: assign candidate to next available interviewer
   - If NO interviewer available: set slot as "Admin Action Required"
4. If no overlap at all for a candidate: set slot as "No Overlap Found"

Return ONLY a valid JSON array (no markdown, no extra text):
[
  {{
    "candidate": "Full Name",
    "candidate_email": "email",
    "interviewer": "Full Name",
    "interviewer_email": "email",
    "slot": "Tuesday 1PM - 2PM",
    "status": "Confirmed / Conflict Resolved / No Overlap / Interviewer Full",
    "reasoning": "explain the decision clearly"
  }}
]"""


    model = genai.GenerativeModel("gemini-3-flash-preview")
    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Clean markdown if present
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())
