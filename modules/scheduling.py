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

    prompt = f"""You are an interview scheduling assistant.

CANDIDATES AVAILABILITY:
{cand_text}

INTERVIEWERS AVAILABILITY:
{iv_text}

TASK:
- For each candidate, find the best overlapping time slot with an available interviewer
- Respect each interviewer's max interviews per day limit
- Suggest exactly one best slot per candidate

Return ONLY a valid JSON array like this (no markdown, no extra text):
[
  {{
    "candidate": "Candidate Full Name",
    "candidate_email": "candidate@email.com",
    "interviewer": "Interviewer Full Name",
    "interviewer_email": "interviewer@email.com",
    "slot": "Tuesday 3PM - 4PM",
    "reasoning": "Only overlapping window between candidate and interviewer"
  }}
]

If no overlap found for a candidate, still include them with slot: "No overlap found" and reasoning explaining why."""

    model = genai.GenerativeModel("gemini-3-flash-preview")
    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Clean markdown if present
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw.strip())
