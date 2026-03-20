import pdfplumber
import google.generativeai as genai
import json
import io
import os
import time
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def parse_pdf_bytes(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

def build_prompt(resume_text: str, jd_text: str) -> str:
    return f"""You are an expert HR recruiter. Analyze this resume against the job description.

JOB DESCRIPTION:
{jd_text}

RESUME:
{resume_text}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "candidate_name": "full name extracted from resume",
  "overall_score": <0-100>,
  "years_of_experience": "e.g.3",
  "current_role": "last job title",
  "current_company": "last company name",
  "notice_period": "Immediate / 30 days / 60 days / 90 days / Unknown",
  "employment_gap": "None",
  "quantified_achievements": true,
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "gaps": ["gap 1", "gap 2", "gap 3"],
  "recommendation": "Strong Fit / Moderate Fit / Not Fit"
}}"""

def parse_gemini_json(raw: str) -> dict:
    text = raw.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

def screen_single_resume(resume_text: str, jd_text: str) -> Dict:
    model = genai.GenerativeModel("gemini-3-flash-preview")
    prompt = build_prompt(resume_text, jd_text)
    response = model.generate_content(prompt)
    return parse_gemini_json(response.text)

def screen_all_resumes(files: List[Dict], jd_text: str, progress_callback=None) -> List[Dict]:
    """
    files: list of {"file_name": str, "bytes": bytes, "email": str}
    Returns ranked list of screening results.
    """
    results = []
    total = len(files)
    for idx, f in enumerate(files):
        try:
            resume_text = parse_pdf_bytes(f["bytes"])
            result = screen_single_resume(resume_text, jd_text)
            result["email"] = f.get("email", "")
            result["file_name"] = f.get("file_name", "")
            results.append(result)
        except Exception as e:
            results.append({
                "candidate_name": f.get("file_name", f"Candidate {idx+1}"),
                "email": f.get("email", ""),
                "file_name": f.get("file_name", ""),
                "overall_score": 0,
                "years_of_experience": "Unknown",
                "current_role": "Unknown",
                "current_company": "Unknown",
                "notice_period": "Unknown",
                "employment_gap": "Unknown",
                "quantified_achievements": False,
                "strengths": ["Could not parse"],
                "gaps": [str(e)],
                "recommendation": "Error"
            })
        if progress_callback:
            progress_callback(idx + 1, total)
        time.sleep(1)  # respect rate limits

    results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
    return results
