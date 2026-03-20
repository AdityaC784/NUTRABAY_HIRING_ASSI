import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL = os.getenv("GMAIL_ADDRESS")
APP_PWD = os.getenv("GMAIL_APP_PASSWORD")
COMPANY = "Nutrabay"

def _send(to: str, subject: str, html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL, APP_PWD)
        server.sendmail(GMAIL, to, msg.as_string())

def send_availability_request_candidate(name: str, email: str, form_link: str):
    subject = f"🎉 You've been shortlisted at {COMPANY}!"
    html = f"""
    <h2>Congratulations, {name}!</h2>
    <p>We are pleased to inform you that you have been <b>shortlisted</b> for the role at <b>{COMPANY}</b>.</p>
    <p>As the next step, please fill in your availability for the interview using the link below:</p>
    <p><a href="{form_link}" style="background:#4CAF50;color:white;padding:10px 20px;
    text-decoration:none;border-radius:5px;">📅 Fill Availability Form</a></p>
    <p>Please respond within <b>24 hours</b>.</p>
    <p>Best regards,<br><b>{COMPANY} HR Team</b></p>
    """
    _send(email, subject, html)

def send_availability_request_interviewer(name: str, email: str, form_link: str, num_candidates: int):
    subject = f"[{COMPANY}] New Interview Round — Please Share Availability"
    html = f"""
    <h2>Hi {name},</h2>
    <p>A new interview round has been initiated. We have shortlisted <b>{num_candidates} candidate(s)</b> for interviews.</p>
    <p>Please share your availability using the form below:</p>
    <p><a href="{form_link}" style="background:#2196F3;color:white;padding:10px 20px;
    text-decoration:none;border-radius:5px;">📅 Fill Availability Form</a></p>
    <p>Please respond within <b>24 hours</b>.</p>
    <p>Best regards,<br><b>{COMPANY} HR Team</b></p>
    """
    _send(email, subject, html)

def send_reminder(name: str, email: str, form_link: str):
    subject = f"[Reminder] Please fill your availability — {COMPANY}"
    html = f"""
    <h2>Hi {name},</h2>
    <p>This is a gentle reminder to fill in your <b>availability form</b> for the upcoming interview round at {COMPANY}.</p>
    <p><a href="{form_link}" style="background:#FF9800;color:white;padding:10px 20px;
    text-decoration:none;border-radius:5px;">📅 Fill Availability Form</a></p>
    <p>Kindly respond at the earliest.</p>
    <p>Best regards,<br><b>{COMPANY} HR Team</b></p>
    """
    _send(email, subject, html)

def send_confirmation(
    candidate_name: str, candidate_email: str,
    interviewer_name: str, interviewer_email: str,
    slot: str, meet_link: str = None
):
    meet_section = f'<p>📹 <b>Meeting Link:</b> <a href="{meet_link}">{meet_link}</a></p>' if meet_link else ""

    # To candidate
    html_c = f"""
    <h2>Interview Scheduled — {COMPANY}</h2>
    <p>Hi <b>{candidate_name}</b>,</p>
    <p>Your interview at <b>{COMPANY}</b> has been confirmed!</p>
    <p>📅 <b>Date & Time:</b> {slot}<br>
    👤 <b>Interviewer:</b> {interviewer_name}</p>
    {meet_section}
    <p>Please be available 5 minutes early. Good luck!</p>
    <p>Best regards,<br><b>{COMPANY} HR Team</b></p>
    """
    _send(candidate_email, f"✅ Interview Confirmed — {slot} | {COMPANY}", html_c)

    # To interviewer
    html_i = f"""
    <h2>Interview Scheduled — {COMPANY}</h2>
    <p>Hi <b>{interviewer_name}</b>,</p>
    <p>An interview has been scheduled with <b>{candidate_name}</b>.</p>
    <p>📅 <b>Date & Time:</b> {slot}<br>
    👤 <b>Candidate:</b> {candidate_name}</p>
    {meet_section}
    <p>Best regards,<br><b>{COMPANY} HR Team</b></p>
    """
    _send(interviewer_email, f"📋 Interview Scheduled: {candidate_name} — {slot}", html_i)
