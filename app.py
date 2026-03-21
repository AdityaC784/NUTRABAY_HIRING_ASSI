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
    save_scheduled_slots,update_slot_confirmed 
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
    st.info("Add interviewers below. Saved permanently to Google Sheets.")

    existing = read_interviewers()
    if not existing.empty:
        st.subheader("Current Interviewers")
        st.dataframe(existing, use_container_width=True)

    st.subheader("Add / Update Interviewers")

    # ✅ st.form() — page only reloads when Save button clicked
    with st.form("interviewer_form"):
        num = st.number_input("Number of interviewers", min_value=1, max_value=10, value=3)
        interviewers = []
        for i in range(int(num)):
            st.markdown(f"**Interviewer {i+1}**")
            c1, c2, c3, c4 = st.columns(4)
            interviewers.append({
                "name": c1.text_input("Name", key=f"iv_name_{i}"),
                "email": c2.text_input("Email", key=f"iv_email_{i}"),
                "department": c3.text_input("Dept", key=f"iv_dept_{i}"),
                "max_per_day": c4.number_input("Max/Day", 1, 10, 3, key=f"iv_max_{i}")
            })

        submitted = st.form_submit_button("💾 Save Interviewers")
        if submitted:
            valid = [iv for iv in interviewers if iv["name"] and iv["email"]]
            if valid:
                save_interviewers(valid)
                st.success(f"✅ {len(valid)} interviewers saved!")
                st.rerun()
            else:
                st.warning("Please fill at least name and email.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESUME SCREENING
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("📄 AI Resume Screening")

    with st.form("screening_form"):
        st.subheader("Job Description")
        jd_text = st.text_area("Paste JD here", height=250,
                                placeholder="We are looking for a Data Analyst...")
        st.subheader("Upload Resumes (PDF)")
        uploaded_files = st.file_uploader("Upload multiple resumes", type=["pdf"],
                                           accept_multiple_files=True)
        submitted = st.form_submit_button("🚀 Run AI Screening", type="primary")

    # Email inputs outside form (dynamic, based on uploaded files)
    emails = {}
    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} resume(s) uploaded")
        with st.expander("📧 Enter candidate emails (optional)"):
            for uf in uploaded_files:
                emails[uf.name] = st.text_input(f"Email for {uf.name}",
                                                  key=f"email_{uf.name}",
                                                  placeholder="candidate@gmail.com")

    if submitted:
        if not jd_text.strip():
            st.error("Please paste a Job Description.")
        elif not uploaded_files:
            st.error("Please upload at least one resume.")
        else:
            files = [{"file_name": uf.name, "bytes": uf.read(),
                      "email": emails.get(uf.name, "")} for uf in uploaded_files]
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
            st.success(f"✅ {len(results)} resumes screened!")
            st.markdown(f"[📊 View Google Sheet]({sheet_url})")

    if st.session_state["screening_results"]:
        results = st.session_state["screening_results"]
        st.subheader(f"📊 Results — {len(results)} Candidates Ranked")
        display_data = []
        for i, r in enumerate(results, 1):
            rec_color = {"Strong Fit": "🟢", "Moderate Fit": "🟡",
                         "Not Fit": "🔴"}.get(r.get("recommendation", ""), "⚪")
            display_data.append({
                "Rank": i,
                "Candidate": r.get("candidate_name", ""),
                "Score": r.get("overall_score", 0),
                "Exp Years": r.get("years_of_experience", ""),
                "Current Role": r.get("current_role", ""),
                "Achievements": "✅" if r.get("quantified_achievements") else "❌",
                "Recommendation": f"{rec_color} {r.get('recommendation', '')}",
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True)

        with st.expander("🔍 Detailed Analysis"):
            for r in results:
                st.markdown(f"### {r.get('candidate_name')} — {r.get('overall_score')}/100")
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
            st.warning("No screening data found.")
        else:
            st.info("Tick candidates to shortlist, then click Confirm.")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Screened", len(df))
            col2.metric("Strong Fit", len(df[df["Recommendation"].str.contains("Strong", na=False)]))
            col3.metric("Moderate Fit", len(df[df["Recommendation"].str.contains("Moderate", na=False)]))

            # ✅ Checkboxes inside form
            with st.form("shortlist_form"):
                shortlist_flags = {}
                for _, row in df.iterrows():
                    rec = str(row.get("Recommendation", ""))
                    shortlist_flags[row["Candidate Name"]] = st.checkbox(
                        f"{row['Candidate Name']} — Score: {row['Overall Score']} | {rec}",
                        value="Strong" in rec,
                        key=f"shortlist_{row['Candidate Name']}"
                    )
                submitted = st.form_submit_button("✅ Confirm Shortlist & Send Emails",
                                                   type="primary")

            if submitted:
                selected = [n for n, checked in shortlist_flags.items() if checked]
                if not selected:
                    st.error("Please select at least one candidate.")
                else:
                    update_shortlist(selected)
                    shortlisted_df = df[df["Candidate Name"].isin(selected)]
                    interviewers_df = read_interviewers()
                    sent_c, sent_i, failed = 0, 0, []

                    with st.spinner("Sending emails..."):
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
                    st.success(f"✅ {len(selected)} shortlisted | 📧 {sent_c} candidate + {sent_i} interviewer emails sent")
                    if failed:
                        st.warning("Failed: " + ", ".join(failed))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AVAILABILITY STATUS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("📬 Availability Status")

    if not st.session_state["shortlist_confirmed"]:
        st.warning("⚠️ Please confirm shortlist first (Tab 2).")
    else:
        col1, col2 = st.columns([1, 5])
        if col1.button("🔄 Refresh"):
            st.rerun()

        responses_df = read_availability_responses()
        shortlisted_df = read_shortlisted()
        interviewers_df = read_interviewers()

        shortlisted_names = shortlisted_df["Candidate Name"].tolist() if not shortlisted_df.empty else []
        iv_names = interviewers_df["Name"].tolist() if not interviewers_df.empty else []
        responded_names = (
    responses_df["Name"].str.strip().str.lower().tolist()
    if not responses_df.empty and "Name" in responses_df.columns
    else []
)   

        st.subheader("Candidate Response Status")
        for name in shortlisted_names:
            status = "✅ Responded" if name.strip().lower() in responded_names else "⏳ Pending"
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"👤 {name}")
            c2.write(status)
            if "Pending" in status:
                email_row = shortlisted_df[shortlisted_df["Candidate Name"] == name]
                email = email_row.iloc[0]["Email"] if not email_row.empty else ""
                if c3.button("📨 Remind", key=f"rem_c_{name}") and email:
                    send_reminder(name, email, FORM_LINK)
                    st.success(f"Reminder sent to {name}")

        st.divider()
        st.subheader("Interviewer Response Status")
        for name in iv_names:
            status = "✅ Responded" if name.strip().lower() in responded_names else "⏳ Pending"
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"🧑‍💼 {name}")
            c2.write(status)
            if "Pending" in status:
                iv_row = interviewers_df[interviewers_df["Name"] == name]
                email = iv_row.iloc[0]["Email"] if not iv_row.empty else ""
                if c3.button("📨 Remind", key=f"rem_i_{name}") and email:
                    send_reminder(name, email, FORM_LINK)
                    st.success(f"Reminder sent to {name}")

        total_expected = len(shortlisted_names) + len(iv_names)
        total_responded = len([n for n in responded_names
                                if n in [x.lower() for x in shortlisted_names + iv_names]])
        st.progress(min(total_responded / max(total_expected, 1), 1.0))
        st.caption(f"{total_responded}/{total_expected} responses received")

        if not responses_df.empty:
            st.subheader("All Responses")
            st.dataframe(responses_df, use_container_width=True)

        # ── Admin Controls ─────────────────────────────────────────────
        with st.expander("⚠️ Admin Controls"):
            if st.button("🗑️ Clear All Responses (New Round)"):
                from modules.sheets_handler import get_or_create_sheet
                ws = get_or_create_sheet(
                    os.getenv("GOOGLE_SHEET_NAME"), "Form Responses 1")
                all_values = ws.get_all_values()
                if len(all_values) > 1:
                    ws.delete_rows(2, len(all_values))
                    st.success("✅ Responses cleared!")
                    st.rerun()


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
            if responses_df.empty:
                st.error("No availability responses yet. Check Tab 3.")
            else:
                slots = build_schedule_from_responses(
                    responses_df, read_shortlisted(), read_interviewers())
                st.session_state["suggested_slots"] = slots
                save_scheduled_slots(slots)
                st.success(f"✅ {len(slots)} slot(s) matched!")

        for i, slot in enumerate(st.session_state.get("suggested_slots", [])):
            status = slot.get("status", "Confirmed")
            icons = {
                "Confirmed": "✅", "Conflict Resolved": "⚡",
                "Rescheduled": "🔄", "Manually Assigned": "📌",
                "No Overlap": "❌", "Interviewer Full": "🚫"
            }
            colors = {
                "Confirmed": st.success, "Conflict Resolved": st.warning,
                "Rescheduled": st.info, "Manually Assigned": st.info,
                "No Overlap": st.error, "Interviewer Full": st.error
            }

            with st.container():
                colors.get(status, st.info)(
                    f"{icons.get(status,'')} **{slot['candidate']}** → "
                    f"🗓️ {slot['slot']} with **{slot['interviewer']}** | *{status}*"
                )
                st.caption(f"💡 {slot.get('reasoning', '')}")

                # ── Availability Reference (always visible) ────────────
                responses_df = read_availability_responses()
                cand_avail = responses_df[
                    responses_df["Name"].str.strip().str.lower() == slot["candidate"].strip().lower()
                ]
                if not cand_avail.empty:
                    st.info(f"📅 **{slot['candidate']} Availability:** {cand_avail.iloc[0].get('Available Slots', '')}")

                with st.expander("👥 All Interviewer Availability"):
                    for _, r in responses_df[responses_df["Role"] == "Interviewer"].iterrows():
                        st.markdown(f"- **{r['Name']}:** {r.get('Available Slots', '')}")

                # ── Manual Assign (No Overlap only) ───────────────────
                if status == "No Overlap":
                    c1, c2 = st.columns(2)
                    m_slot = c1.text_input("Assign slot", key=f"manual_slot_{i}", placeholder="Wed 11AM-12PM")
                    m_iv = c2.selectbox("Interviewer", read_interviewers()["Name"].tolist(), key=f"manual_iv_{i}")
                    if st.button(f"📌 Assign", key=f"manual_btn_{i}") and m_slot:
                        st.session_state["suggested_slots"][i].update({"slot": m_slot, "interviewer": m_iv, "status": "Manually Assigned"})
                        st.rerun()

                # ── Confirmation Email ─────────────────────────────────
                if status not in ["No Overlap", "Interviewer Full"]:
                    meet = st.text_input("Meet link (optional)", key=f"meet_{i}", placeholder="https://meet.google.com/...")
                    if st.button(f"📨 Send Confirmation", key=f"confirm_{i}"):
                        try:
                            send_confirmation(slot["candidate"], slot.get("candidate_email",""),
                                              slot["interviewer"], slot.get("interviewer_email",""),
                                              slot["slot"], meet or None)
                            update_slot_confirmed(slot["candidate"], slot["slot"])
                            st.success("✅ Confirmation sent!")
                        except Exception as e:
                            st.error(f"Email failed: {e}")

                # ── Reschedule ─────────────────────────────────────────
                if st.button(f"🔄 Reschedule", key=f"reschedule_{i}"):
                    st.session_state[f"rescheduling_{i}"] = True

                if st.session_state.get(f"rescheduling_{i}", False):
                    rc1, rc2, rc3 = st.columns(3)
                    new_slot = rc1.text_input("New slot", key=f"new_slot_{i}", placeholder="Thu 11AM-12PM")
                    new_iv   = rc2.selectbox("New interviewer", read_interviewers()["Name"].tolist(), key=f"new_iv_{i}")
                    new_meet = rc3.text_input("Meet link", key=f"new_meet_{i}", placeholder="https://meet.google.com/...")
                    bc1, bc2 = st.columns(2)
                    if bc1.button("✅ Confirm", key=f"confirm_reschedule_{i}"):
                        if not new_slot:
                            st.error("Enter a new time slot.")
                        else:
                            st.session_state["suggested_slots"][i].update({
                                "slot": new_slot, "interviewer": new_iv,
                                "status": "Rescheduled",
                                "reasoning": f"Rescheduled by admin → {new_slot} with {new_iv}"
                            })
                            st.session_state[f"rescheduling_{i}"] = False
                            try:
                                iv_df = read_interviewers()
                                iv_email = iv_df[iv_df["Name"] == new_iv].iloc[0]["Email"]
                                send_confirmation(slot["candidate"], slot.get("candidate_email",""),
                                                  new_iv, iv_email, new_slot, new_meet or None)
                                st.success("✅ Rescheduled & confirmation sent!")
                            except Exception as e:
                                st.error(f"Email failed: {e}")
                            st.rerun()
                    if bc2.button("❌ Cancel", key=f"cancel_reschedule_{i}"):
                        st.session_state[f"rescheduling_{i}"] = False
                        st.rerun()

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
