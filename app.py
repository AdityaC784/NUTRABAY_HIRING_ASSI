import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()

from modules.screening import screen_all_resumes
from modules.sheets_handler import (
    save_screening_results, read_screening_results,
    update_shortlist, read_shortlisted,
    save_interviewers, read_interviewers,
    save_availability_response, read_availability_responses,
    save_scheduled_slots
)
from modules.email_handler import (
    send_availability_request_candidate,
    send_availability_request_interviewer,
    send_reminder, send_confirmation
)
from modules.scheduling import build_schedule_from_responses

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nutrabay AI Hiring Pipeline",
    page_icon="🤖",
    layout="wide"
)

# ── Session State Init ─────────────────────────────────────────────────────────
for key in ["screening_done", "shortlist_confirmed", "emails_sent", "slots_matched"]:
    if key not in st.session_state:
        st.session_state[key] = False
if "screening_results" not in st.session_state:
    st.session_state["screening_results"] = []
if "suggested_slots" not in st.session_state:
    st.session_state["suggested_slots"] = []

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🤖 Nutrabay AI Hiring Pipeline")
st.caption("Automated Resume Screening → Shortlisting → Interview Scheduling")

FORM_LINK = os.getenv("AVAILABILITY_FORM_LINK", "#")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚙️ Setup",
    "📄 Resume Screening",
    "✅ Shortlist",
    "📬 Availability",
    "📅 Schedule",
    "📊 Dashboard"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 — SETUP
# ══════════════════════════════════════════════════════════════════════════════
with tab0:
    st.header("⚙️ One-Time Setup")
    st.info("Add interviewers below. This is saved permanently to Google Sheets.")

    existing = read_interviewers()
    if not existing.empty:
        st.subheader("Current Interviewers")
        st.dataframe(existing, use_container_width=True)

    st.subheader("Add / Update Interviewers")
    num = st.number_input("Number of interviewers", min_value=1, max_value=10, value=3)
    interviewers = []
    for i in range(int(num)):
        st.markdown(f"**Interviewer {i+1}**")
        c1, c2, c3, c4, c5 = st.columns(5)
        interviewers.append({
            "name": c1.text_input("Name", key=f"iv_name_{i}"),
            "email": c2.text_input("Email", key=f"iv_email_{i}"),
            "department": c3.text_input("Dept", key=f"iv_dept_{i}"),
            "max_per_day": c4.number_input("Max/Day", 1, 10, 3, key=f"iv_max_{i}"),
            "preferred_slots": c5.text_input("Preferred Slots", key=f"iv_slots_{i}",
                                              placeholder="Mon 10AM-1PM, Tue 2PM-5PM")
        })
    if st.button("💾 Save Interviewers"):
        valid = [iv for iv in interviewers if iv["name"] and iv["email"]]
        if valid:
            save_interviewers(valid)
            st.success(f"✅ {len(valid)} interviewers saved to Google Sheets!")
        else:
            st.warning("Please fill at least name and email.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESUME SCREENING
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("📄 AI Resume Screening")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Job Description")
        jd_text = st.text_area("Paste JD here", height=300,
                                placeholder="We are looking for a Data Analyst with 2+ years of experience...")
    with col2:
        st.subheader("Upload Resumes (PDF)")
        uploaded_files = st.file_uploader(
            "Upload multiple resumes", type=["pdf"],
            accept_multiple_files=True
        )
        st.caption("Tip: Name files as CandidateName.pdf for best results")

    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} resume(s) uploaded")
        emails = {}
        with st.expander("📧 Enter candidate emails (optional)"):
            for uf in uploaded_files:
                emails[uf.name] = st.text_input(
                    f"Email for {uf.name}", key=f"email_{uf.name}",
                    placeholder="candidate@gmail.com"
                )

    if st.button("🚀 Run AI Screening", type="primary"):
        if not jd_text.strip():
            st.error("Please paste a Job Description.")
        elif not uploaded_files:
            st.error("Please upload at least one resume.")
        else:
            files = [
                {
                    "file_name": uf.name,
                    "bytes": uf.read(),
                    "email": emails.get(uf.name, "")
                }
                for uf in uploaded_files
            ]
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(done, total):
                progress_bar.progress(done / total)
                status_text.text(f"Screening resume {done}/{total}...")

            with st.spinner("AI is screening resumes..."):
                results = screen_all_resumes(files, jd_text, update_progress)

            st.session_state["screening_results"] = results
            sheet_url = save_screening_results(results)
            st.session_state["screening_done"] = True
            status_text.text("✅ Screening complete!")
            st.success(f"✅ {len(results)} resumes screened and saved to Google Sheets!")
            st.markdown(f"[📊 View Google Sheet]({sheet_url})")

    if st.session_state["screening_results"]:
        results = st.session_state["screening_results"]
        st.subheader(f"📊 Results — {len(results)} Candidates Ranked")

        display_data = []
        for i, r in enumerate(results, 1):
            rec_color = {"Strong Fit": "🟢", "Moderate Fit": "🟡", "Not Fit": "🔴"}.get(
                r.get("recommendation", ""), "⚪")
            display_data.append({
                "Rank": i,
                "Candidate": r.get("candidate_name", ""),
                "Score": r.get("overall_score", 0),
                "Exp Years": r.get("years_of_experience", ""),
                "Current Role": r.get("current_role", ""),
                "Notice Period": r.get("notice_period", ""),
                "Achievements": "✅" if r.get("quantified_achievements") else "❌",
                "Recommendation": f"{rec_color} {r.get('recommendation', '')}",
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True)

        with st.expander("🔍 View Detailed Analysis per Candidate"):
            for r in results:
                with st.container():
                    st.markdown(f"### {r.get('candidate_name', 'Unknown')} — Score: {r.get('overall_score', 0)}/100")
                    c1, c2 = st.columns(2)
                    c1.markdown("**✅ Strengths:**\n" + "\n".join(f"- {s}" for s in r.get("strengths", [])))
                    c2.markdown("**❌ Gaps:**\n" + "\n".join(f"- {g}" for g in r.get("gaps", [])))
                    st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SHORTLIST
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("✅ Admin Review & Shortlist")

    if not st.session_state["screening_done"]:
        st.warning("⚠️ Please complete Resume Screening first (Tab 1).")
    else:
        df = read_screening_results()
        if df.empty:
            st.warning("No screening data found. Run screening first.")
        else:
            st.info("Tick the candidates you want to shortlist, then click Confirm.")
            strong = df[df["Recommendation"].str.contains("Strong", na=False)]
            moderate = df[df["Recommendation"].str.contains("Moderate", na=False)]

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Screened", len(df))
            col2.metric("Strong Fit", len(strong))
            col3.metric("Moderate Fit", len(moderate))

            shortlist_flags = {}
            for _, row in df.iterrows():
                rec = str(row.get("Recommendation", ""))
                default = "Strong" in rec
                shortlist_flags[row["Candidate Name"]] = st.checkbox(
                    f"{row['Candidate Name']} — Score: {row['Overall Score']} | {rec}",
                    value=default,
                    key=f"shortlist_{row['Candidate Name']}"
                )

            selected = [name for name, checked in shortlist_flags.items() if checked]
            st.markdown(f"**Selected: {len(selected)} candidates**")

            if st.button("✅ Confirm Shortlist & Send Emails", type="primary"):
                if not selected:
                    st.error("Please select at least one candidate.")
                else:
                    update_shortlist(selected)
                    shortlisted_df = df[df["Candidate Name"].isin(selected)]
                    interviewers_df = read_interviewers()

                    with st.spinner("Sending availability emails..."):
                        sent_c, sent_i, failed = 0, 0, []
                        for _, row in shortlisted_df.iterrows():
                            email = row.get("Email", "")
                            if email:
                                try:
                                    send_availability_request_candidate(
                                        row["Candidate Name"], email, FORM_LINK)
                                    sent_c += 1
                                except Exception as e:
                                    failed.append(f"{row['Candidate Name']}: {e}")

                        for _, iv in interviewers_df.iterrows():
                            if iv.get("Email"):
                                try:
                                    send_availability_request_interviewer(
                                        iv["Name"], iv["Email"], FORM_LINK, len(selected))
                                    sent_i += 1
                                except Exception as e:
                                    failed.append(f"{iv['Name']}: {e}")

                    st.session_state["shortlist_confirmed"] = True
                    st.success(f"✅ Shortlisted {len(selected)} candidates")
                    st.success(f"📧 Emails sent: {sent_c} candidates + {sent_i} interviewers")
                    if failed:
                        st.warning("Some emails failed: " + ", ".join(failed))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AVAILABILITY STATUS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("📬 Availability Status")

    if not st.session_state["shortlist_confirmed"]:
        st.warning("⚠️ Please confirm shortlist first (Tab 2).")
    else:
        if st.button("🔄 Refresh Responses"):
            st.rerun()

        responses_df = read_availability_responses()
        shortlisted_df = read_shortlisted()
        interviewers_df = read_interviewers()

        shortlisted_names = shortlisted_df["Candidate Name"].tolist() if not shortlisted_df.empty else []
        iv_names = interviewers_df["Name"].tolist() if not interviewers_df.empty else []
        responded_names = responses_df["Name"].tolist() if not responses_df.empty else []

        st.subheader("Candidate Response Status")
        for name in shortlisted_names:
            status = "✅ Responded" if name in responded_names else "⏳ Pending"
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"👤 {name}")
            c2.write(status)
            if name not in responded_names:
                email_row = shortlisted_df[shortlisted_df["Candidate Name"] == name]
                email = email_row.iloc[0]["Email"] if not email_row.empty else ""
                if c3.button("📨 Send Reminder", key=f"rem_c_{name}") and email:
                    send_reminder(name, email, FORM_LINK)
                    st.success(f"Reminder sent to {name}")

        st.divider()
        st.subheader("Interviewer Response Status")
        for name in iv_names:
            status = "✅ Responded" if name in responded_names else "⏳ Pending"
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"🧑‍💼 {name}")
            c2.write(status)
            if name not in responded_names:
                iv_row = interviewers_df[interviewers_df["Name"] == name]
                email = iv_row.iloc[0]["Email"] if not iv_row.empty else ""
                if c3.button("📨 Send Reminder", key=f"rem_i_{name}") and email:
                    send_reminder(name, email, FORM_LINK)
                    st.success(f"Reminder sent to {name}")

        total_expected = len(shortlisted_names) + len(iv_names)
        total_responded = len([n for n in responded_names if n in shortlisted_names + iv_names])
        progress_val = min(total_responded / max(total_expected, 1), 1.0)
        st.progress(progress_val)
        st.caption(f"{total_responded}/{total_expected} responses received")

        if not responses_df.empty:
            st.subheader("All Responses")
            st.dataframe(responses_df, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — INTERVIEW SCHEDULING
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("📅 Interview Scheduling")

    if not st.session_state["shortlist_confirmed"]:
        st.warning("⚠️ Please confirm shortlist first (Tab 2).")
    else:
        if st.button("📅 Match Slots", type="primary"):
            responses_df = read_availability_responses()
            shortlisted_df = read_shortlisted()
            interviewers_df = read_interviewers()

            if responses_df.empty:
                st.error("No availability responses yet. Check Tab 3.")
            else:
                suggestions = build_schedule_from_responses(
                    responses_df, shortlisted_df, interviewers_df)
                st.session_state["suggested_slots"] = suggestions
                st.session_state["slots_matched"] = True
                save_scheduled_slots(suggestions)
                st.success(f"✅ {len(suggestions)} interview slot(s) matched!")

        if st.session_state["suggested_slots"]:
            slots = st.session_state["suggested_slots"]
            st.subheader("Suggested Interview Slots")

            for i, slot in enumerate(slots):
                with st.container():
                    st.markdown(f"**{slot['candidate']}** → 🗓️ {slot['slot']} with {slot['interviewer']}")
                    st.caption(f"💡 Reasoning: {slot['reasoning']}")
                    meet_link = st.text_input("Google Meet link (optional)",
                                              key=f"meet_{i}",
                                              placeholder="https://meet.google.com/xxx-xxxx-xxx")
                    if st.button(f"📨 Send Confirmation to {slot['candidate']}", key=f"confirm_{i}"):
                        try:
                            send_confirmation(
                                slot["candidate"], slot.get("candidate_email", ""),
                                slot["interviewer"], slot.get("interviewer_email", ""),
                                slot["slot"], meet_link or None
                            )
                            st.success(f"✅ Confirmation emails sent for {slot['candidate']}!")
                        except Exception as e:
                            st.error(f"Email failed: {e}")
                    st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.header("📊 Hiring Funnel Dashboard")
    df = read_screening_results()

    if df.empty:
        st.info("Run screening first to see dashboard data.")
    else:
        total = len(df)
        shortlisted = len(df[df["Shortlisted"] == "Yes"]) if "Shortlisted" in df.columns else 0
        strong_fit = len(df[df["Recommendation"].str.contains("Strong", na=False)])
        moderate_fit = len(df[df["Recommendation"].str.contains("Moderate", na=False)])
        not_fit = len(df[df["Recommendation"].str.contains("Not Fit", na=False)])
        scheduled = len(st.session_state["suggested_slots"])

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📥 Total Applied", total)
        c2.metric("🟢 Strong Fit", strong_fit)
        c3.metric("🟡 Moderate Fit", moderate_fit)
        c4.metric("✅ Shortlisted", shortlisted)
        c5.metric("📅 Scheduled", scheduled)

        col1, col2 = st.columns(2)

        with col1:
            fig_funnel = go.Figure(go.Funnel(
                y=["Total Applied", "Screened", "Shortlisted", "Scheduled"],
                x=[total, total, shortlisted, scheduled],
                textinfo="value+percent initial",
                marker_color=["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"]
            ))
            fig_funnel.update_layout(title="Hiring Funnel", height=400)
            st.plotly_chart(fig_funnel, use_container_width=True)

        with col2:
            fig_pie = px.pie(
                names=["Strong Fit", "Moderate Fit", "Not Fit"],
                values=[strong_fit, moderate_fit, not_fit],
                color_discrete_sequence=["#4CAF50", "#FF9800", "#F44336"],
                title="Candidate Fit Distribution"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        if "Overall Score" in df.columns:
            fig_scores = px.bar(
                df.sort_values("Overall Score", ascending=False),
                x="Candidate Name", y="Overall Score",
                color="Recommendation",
                color_discrete_map={"Strong Fit": "#4CAF50", "Moderate Fit": "#FF9800", "Not Fit": "#F44336"},
                title="Candidate Score Distribution"
            )
            fig_scores.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_scores, use_container_width=True)

        with st.expander("📋 Stage-wise Conversion Rates"):
            stages = ["Applied", "Screened", "Shortlisted", "Scheduled"]
            values = [total, total, shortlisted, scheduled]
            for i in range(1, len(stages)):
                rate = (values[i] / values[i-1] * 100) if values[i-1] > 0 else 0
                st.metric(f"{stages[i-1]} → {stages[i]}", f"{rate:.1f}%")
