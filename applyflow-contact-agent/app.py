from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from src.contact_discovery import (
    generate_hiring_manager_search_queries,
    generate_recruiter_search_queries,
    rank_contact_title,
)
from src.database import (
    delete_application,
    export_to_csv,
    get_applications,
    get_settings,
    init_db,
    save_application,
    save_settings,
    update_application,
)
from src.domain_resolver import extract_domain_from_url, is_ats_domain, normalize_domain
from src.email_confidence import score_email_candidate
from src.email_generator import generate_direct_email_candidates, generate_generic_aliases
from src.email_validator import validate_email_candidate
from src.job_parser import detect_role_category, extract_keywords, extract_required_tools
from src.outreach_writer import (
    extract_resume_proof_bullets,
    generate_follow_up_html,
    generate_follow_up_markdown,
    generate_follow_up_plain,
    generate_linkedin_dm,
    generate_reel_style_email_html,
    generate_reel_style_email_markdown,
    generate_reel_style_email_plain,
    generate_short_email_html,
    generate_short_email_markdown,
    generate_short_email_plain,
    select_truthful_hook,
)
from src.prompt_builder import build_chatgpt_refinement_prompt
from src.resume_parser import extract_text_from_pdf
from src.utils import UPLOADS_DIR, add_business_days_simple, ensure_directories, safe_json_dumps, today_iso


STATUS_OPTIONS = [
    "Applied",
    "Need Contact",
    "Contact Found",
    "Email Candidate Found",
    "Email Drafted",
    "Email Sent",
    "Follow-up Needed",
    "Follow-up Sent",
    "Skip",
    "Rejected",
    "Replied",
]
PRIORITY_OPTIONS = ["High", "Medium", "Low"]


def bootstrap() -> None:
    ensure_directories()
    init_db()
    st.set_page_config(
        page_title="ApplyFlow Contact Agent",
        page_icon="AF",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
        h1, h2, h3 {letter-spacing: 0;}
        .small-note {color: #5b6470; font-size: 0.92rem;}
        .metric-card {
            border: 1px solid #d9e0e8;
            border-radius: 8px;
            padding: 0.8rem 1rem;
            background: #fbfcfd;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def text_area_join(items: list[str]) -> str:
    return "\n".join(items)


def validate_and_score_candidates(
    raw_candidates: list[dict],
    contact_name: str,
    contact_title: str,
    contact_context: str,
    contact_linkedin: str,
    department: str,
    job_title: str,
    domain_source: str,
) -> list[dict]:
    scored = []
    for candidate in raw_candidates:
        validation = validate_email_candidate(candidate["email"])
        enriched = {
            **candidate,
            **validation,
            "contact_name": contact_name,
            "contact_linkedin": contact_linkedin,
        }
        scored.append(
            score_email_candidate(
                enriched,
                contact_title=contact_title,
                contact_context=contact_context,
                department=department,
                domain_source=domain_source,
                job_title=job_title,
            )
        )
    return sorted(scored, key=lambda row: row["confidence_score"], reverse=True)


def score_resume_match(job_description: str, resume_text: str, job_title: str) -> dict:
    keywords = extract_keywords(job_description)
    tools = extract_required_tools(job_description)
    role_category = detect_role_category(job_title, job_description)
    resume_lower = resume_text.lower()
    matched = sorted({kw for kw in [*keywords, *tools] if kw.lower() in resume_lower})
    missing = sorted({kw for kw in [*keywords, *tools] if kw.lower() not in resume_lower})

    skill_score = round(50 * (len(matched) / max(len(set([*keywords, *tools])), 1)))
    responsibility_terms = ["dashboard", "analysis", "stakeholder", "pipeline", "reporting", "model", "requirements"]
    responsibility_hits = [term for term in responsibility_terms if term in resume_lower and term in job_description.lower()]
    responsibility_score = min(25, len(responsibility_hits) * 5)
    role_score = 15 if role_category.lower().split()[0] in resume_lower or any(kw.lower() in resume_lower for kw in keywords[:3]) else 5
    education_score = 10 if any(term in resume_lower for term in ["degree", "university", "certification", "certified", "master", "bachelor"]) else 0
    total = min(100, skill_score + responsibility_score + role_score + education_score)

    if total >= 85:
        interpretation = "Strong fit"
    elif total >= 70:
        interpretation = "Good fit"
    elif total >= 55:
        interpretation = "Moderate fit"
    else:
        interpretation = "Weak fit"

    return {
        "keywords": keywords,
        "tools": tools,
        "matched_skills": matched,
        "missing_keywords": missing,
        "role_category": role_category,
        "match_score": total,
        "interpretation": interpretation,
        "proof_bullets": extract_resume_proof_bullets(resume_text, matched or keywords),
    }


def candidate_dataframe(candidates: list[dict]) -> pd.DataFrame:
    if not candidates:
        return pd.DataFrame()
    columns = [
        "email",
        "type",
        "pattern",
        "syntax_valid",
        "domain_valid",
        "mx_valid",
        "confidence_score",
        "confidence_label",
        "recommended_action",
        "notes",
        "confidence_notes",
    ]
    return pd.DataFrame(candidates)[columns]


def render_header() -> None:
    st.title("ApplyFlow Contact Agent")
    st.caption("Find the right recruiter email and generate warm, role-specific outreach after applying.")
    st.info(
        "V1 uses free local checks only. MX records show that a domain can receive email; they do not prove an exact inbox exists.",
    )


def render_find_contact(settings: dict) -> None:
    st.subheader("Find Contact")
    st.write("Best first target: recruiter or talent acquisition person connected to the company or department.")
    st.write("Best backup target: hiring manager or team lead if a recruiter email is not available. Generic recruiting inboxes are fallback options only.")

    left, right = st.columns([1, 1])
    with left:
        company = st.text_input("Company name", key="fc_company")
        job_title = st.text_input("Job title", key="fc_job_title")
        job_url = st.text_input("Job URL or company careers URL", key="fc_job_url")
        company_domain = st.text_input("Company domain", key="fc_domain")
        job_location = st.text_input("Job location", key="fc_job_location")
        department = st.text_input("Department/team", value="Data", key="fc_department")
    with right:
        contact_name = st.text_input("Contact name", key="fc_contact_name")
        contact_title = st.text_input("Contact title", key="fc_contact_title")
        contact_linkedin = st.text_input("Contact LinkedIn URL", key="fc_contact_linkedin")
        contact_context = st.text_area(
            "Contact context",
            placeholder="Technical recruiter at this company, posted about this role, hiring manager for analytics team...",
            height=130,
            key="fc_contact_context",
        )

    button_cols = st.columns(4)
    with button_cols[0]:
        if st.button("Resolve Domain", use_container_width=True):
            if company_domain:
                resolved = normalize_domain(company_domain)
                st.session_state["resolved_domain"] = resolved
                st.success(f"Using provided domain: {resolved}")
            elif job_url:
                extracted = extract_domain_from_url(job_url)
                if is_ats_domain(extracted):
                    st.session_state["resolved_domain"] = ""
                    st.warning("This appears to be an ATS/job-platform domain, not the company's email domain. Please enter the company website domain manually.")
                elif extracted:
                    st.session_state["resolved_domain"] = extracted
                    st.success(f"Resolved likely domain from URL: {extracted}")
                else:
                    st.warning("Could not confidently determine the company domain. Please enter the company website domain manually.")
            else:
                st.error("Enter a company domain or job/company URL first.")

    resolved_domain = st.session_state.get("resolved_domain") or normalize_domain(company_domain)
    if resolved_domain:
        st.caption(f"Current domain: {resolved_domain}")

    with button_cols[1]:
        if st.button("Generate Contact Search Queries", use_container_width=True):
            if not company or not job_title:
                st.error("Company name and job title are required.")
            else:
                st.session_state["recruiter_queries"] = generate_recruiter_search_queries(company, resolved_domain, job_title, department)
                st.session_state["manager_queries"] = generate_hiring_manager_search_queries(company, resolved_domain, job_title, department)

    with button_cols[2]:
        if st.button("Generate Email Candidates", use_container_width=True):
            if not resolved_domain:
                st.error("Missing company domain. Enter or resolve the company website domain first.")
            else:
                direct = generate_direct_email_candidates(contact_name, resolved_domain)
                aliases = generate_generic_aliases(resolved_domain)
                if not direct and not aliases:
                    st.error("No email candidates generated.")
                else:
                    scored_direct = validate_and_score_candidates(
                        direct,
                        contact_name,
                        contact_title,
                        contact_context,
                        contact_linkedin,
                        department,
                        job_title,
                        "provided",
                    )
                    scored_aliases = validate_and_score_candidates(
                        aliases,
                        "",
                        contact_title,
                        contact_context,
                        contact_linkedin,
                        department,
                        job_title,
                        "provided",
                    )
                    st.session_state["email_candidates"] = scored_direct + scored_aliases
                    if scored_direct:
                        st.session_state["selected_candidate_email"] = scored_direct[0]["email"]
                        st.session_state["selected_candidate_label"] = scored_direct[0]["confidence_label"]

    with button_cols[3]:
        if st.button("Save Contact Search", use_container_width=True):
            if not company or not job_title:
                st.error("Company name and job title are required before saving.")
            else:
                candidates = st.session_state.get("email_candidates", [])
                best = candidates[0] if candidates else {}
                app_id = save_application(
                    {
                        "company_name": company,
                        "company_domain": resolved_domain,
                        "job_title": job_title,
                        "job_url": job_url,
                        "job_location": job_location,
                        "department": department,
                        "contact_name": contact_name,
                        "contact_title": contact_title,
                        "contact_linkedin": contact_linkedin,
                        "contact_context": contact_context,
                        "selected_email": best.get("email"),
                        "email_candidates": safe_json_dumps(candidates),
                        "generic_aliases": safe_json_dumps([c for c in candidates if c.get("type") == "generic_alias"]),
                        "confidence_score": best.get("confidence_score"),
                        "confidence_label": best.get("confidence_label"),
                        "confidence_notes": best.get("confidence_notes"),
                        "status": "Email Candidate Found" if best else "Contact Found",
                        "priority": settings.get("default_priority", "Medium"),
                    }
                )
                st.success(f"Saved contact search as application #{app_id}.")

    if st.session_state.get("recruiter_queries"):
        query_left, query_right = st.columns(2)
        with query_left:
            st.text_area("Recruiter and talent search queries", text_area_join(st.session_state["recruiter_queries"]), height=260)
        with query_right:
            st.text_area("Hiring-manager search queries", text_area_join(st.session_state["manager_queries"]), height=260)

    if contact_title:
        ranking = rank_contact_title(contact_title, job_title, department)
        st.caption(f"Contact role guidance: rank {ranking['rank']} - {ranking['matched_role']}")

    candidates = st.session_state.get("email_candidates", [])
    if candidates:
        st.markdown("**Email candidates**")
        st.caption("Fallback aliases are not person-specific and not verified.")
        st.dataframe(candidate_dataframe(candidates), use_container_width=True, hide_index=True)
        candidate_emails = [candidate["email"] for candidate in candidates]
        selected = st.selectbox("Select email candidate for outreach", candidate_emails, key="candidate_select")
        selected_row = next((candidate for candidate in candidates if candidate["email"] == selected), candidates[0])
        st.session_state["selected_candidate_email"] = selected
        st.session_state["selected_candidate_label"] = selected_row.get("confidence_label", "")
        st.session_state["selected_candidate_score"] = selected_row.get("confidence_score", 0)
        st.session_state["selected_candidate_notes"] = selected_row.get("confidence_notes", "")
        st.text_area("Copy-ready candidate emails", "\n".join(candidate_emails), height=160)


def render_generate_email(settings: dict) -> None:
    st.subheader("Generate Email")
    st.caption("The email uses only the submitted resume text, job description, and notes you provide.")

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company name", value=st.session_state.get("fc_company", ""), key="ge_company")
        job_title = st.text_input("Job title", value=st.session_state.get("fc_job_title", ""), key="ge_job_title")
        contact_name = st.text_input("Selected contact name", value=st.session_state.get("fc_contact_name", ""), key="ge_contact_name")
        contact_email = st.text_input("Selected contact email", value=st.session_state.get("selected_candidate_email", ""), key="ge_contact_email")
        contact_title = st.text_input("Selected contact title", value=st.session_state.get("fc_contact_title", ""), key="ge_contact_title")
        contact_context = st.text_area("Selected contact context", value=st.session_state.get("fc_contact_context", ""), height=110, key="ge_contact_context")
    with col2:
        company_note = st.text_area("Company research note", height=90, key="ge_company_note")
        role_hook = st.text_input("Role/company hook", key="ge_role_hook")
        application_date = st.date_input("Application date", key="ge_application_date")
        confidence_label = st.text_input("Selected email confidence", value=st.session_state.get("selected_candidate_label", ""), key="ge_confidence")
        company_domain = st.text_input("Company domain", value=st.session_state.get("resolved_domain", ""), key="ge_domain")

    link_cols = st.columns(3)
    with link_cols[0]:
        linkedin_url = st.text_input("LinkedIn URL", value=settings.get("linkedin_url", ""), key="ge_linkedin")
    with link_cols[1]:
        github_url = st.text_input("GitHub URL", value=settings.get("github_url", ""), key="ge_github")
    with link_cols[2]:
        portfolio_url = st.text_input("Portfolio URL", value=settings.get("portfolio_url", ""), key="ge_portfolio")

    job_description = st.text_area("Job description", height=220, key="ge_job_description")
    resume_upload = st.file_uploader("Upload resume PDF used for this job", type=["pdf"], key="ge_resume_upload")
    pasted_resume = st.text_area("Or paste resume text manually", height=220, key="ge_resume_text")

    if st.button("Generate Outreach", type="primary", use_container_width=True):
        if not company or not job_title:
            st.error("Company name and job title are required.")
            return
        if not job_description:
            st.error("Missing job description.")
            return
        resume_text = pasted_resume.strip()
        resume_filename = ""
        if resume_upload is not None:
            resume_filename = resume_upload.name
            try:
                resume_upload.seek(0)
                resume_text = extract_text_from_pdf(resume_upload)
                upload_path = UPLOADS_DIR / resume_upload.name
                upload_path.write_bytes(resume_upload.getvalue())
            except ValueError as exc:
                st.error(str(exc))
                return
        if not resume_text:
            st.error("Upload a resume PDF or paste the exact resume text used for this application.")
            return

        active_settings = {
            **settings,
            "linkedin_url": linkedin_url,
            "github_url": github_url,
            "portfolio_url": portfolio_url,
        }
        match = score_resume_match(job_description, resume_text, job_title)
        selected_hook = role_hook or select_truthful_hook(company, job_title, contact_context, company_note, job_description)
        context = {
            "company": company,
            "job_title": job_title,
            "contact_name": contact_name,
            "contact_title": contact_title,
            "contact_email": contact_email,
            "contact_context": contact_context,
            "company_note": company_note,
            "job_description": job_description,
            "selected_hook": selected_hook,
            "matched_skills": match["matched_skills"],
            "proof_bullets": match["proof_bullets"],
            "role_category": match["role_category"],
            "settings": active_settings,
        }
        subject_lines = [
            f"{job_title} application - {(match['matched_skills'] or [match['role_category']])[0]}",
            f"Following up on my {job_title} application",
            f"{job_title} candidate with {(match['matched_skills'] or [match['role_category']])[0]} experience",
        ]
        outputs = {
            "subject_lines": subject_lines,
            "main_plain": generate_reel_style_email_plain(**context),
            "main_markdown": generate_reel_style_email_markdown(**context),
            "main_html": generate_reel_style_email_html(**context),
            "short_plain": generate_short_email_plain(**context),
            "short_markdown": generate_short_email_markdown(**context),
            "short_html": generate_short_email_html(**context),
            "follow_plain": generate_follow_up_plain(**context),
            "follow_markdown": generate_follow_up_markdown(**context),
            "follow_html": generate_follow_up_html(**context),
            "linkedin_dm": generate_linkedin_dm(**context),
        }
        prompt = build_chatgpt_refinement_prompt(
            company=company,
            job_title=job_title,
            job_description=job_description,
            contact_name=contact_name,
            contact_title=contact_title,
            contact_email=contact_email,
            contact_context=contact_context,
            selected_hook=selected_hook,
            resume_text=resume_text,
            settings=active_settings,
            confidence_label=confidence_label,
        )
        st.session_state["outreach_outputs"] = outputs
        st.session_state["outreach_record"] = {
            "company_name": company,
            "company_domain": company_domain,
            "job_title": job_title,
            "job_description": job_description,
            "contact_name": contact_name,
            "contact_title": contact_title,
            "contact_context": contact_context,
            "selected_email": contact_email,
            "confidence_label": confidence_label,
            "confidence_score": st.session_state.get("selected_candidate_score"),
            "confidence_notes": st.session_state.get("selected_candidate_notes"),
            "resume_filename": resume_filename,
            "resume_text": resume_text,
            "match_score": match["match_score"],
            "matched_skills": safe_json_dumps(match["matched_skills"]),
            "missing_keywords": safe_json_dumps(match["missing_keywords"]),
            "selected_hook": selected_hook,
            "subject_lines": safe_json_dumps(subject_lines),
            "main_email_plain": outputs["main_plain"],
            "main_email_markdown": outputs["main_markdown"],
            "main_email_html": outputs["main_html"],
            "short_email_plain": outputs["short_plain"],
            "short_email_markdown": outputs["short_markdown"],
            "short_email_html": outputs["short_html"],
            "follow_up_email_plain": outputs["follow_plain"],
            "follow_up_email_markdown": outputs["follow_markdown"],
            "follow_up_email_html": outputs["follow_html"],
            "linkedin_dm": outputs["linkedin_dm"],
            "chatgpt_prompt": prompt,
            "status": "Email Drafted",
            "priority": settings.get("default_priority", "Medium"),
            "follow_up_date": add_business_days_simple(today_iso(), int(settings.get("default_follow_up_days") or 4)),
        }
        st.session_state["outreach_match"] = match
        st.session_state["chatgpt_prompt"] = prompt
        st.success("Generated outreach. Review before sending manually.")

    outputs = st.session_state.get("outreach_outputs")
    if outputs:
        match = st.session_state.get("outreach_match", {})
        st.markdown("**Resume and job match**")
        metric_cols = st.columns(4)
        metric_cols[0].metric("Match score", f"{match.get('match_score', 0)}/100")
        metric_cols[1].metric("Interpretation", match.get("interpretation", ""))
        metric_cols[2].metric("Role category", match.get("role_category", ""))
        metric_cols[3].metric("Matched skills", len(match.get("matched_skills", [])))
        st.caption("This score is a heuristic, not a guarantee.")
        st.write("Matched skills:", ", ".join(match.get("matched_skills", [])) or "None found")
        st.write("Missing keywords:", ", ".join(match.get("missing_keywords", [])) or "None found")

        st.text_area("Three subject line options", "\n".join(outputs["subject_lines"]), height=100)
        st.text_area("Main reel-style cold email - plain text", outputs["main_plain"], height=330)
        st.text_area("Main reel-style cold email - Markdown", outputs["main_markdown"], height=330)
        st.text_area("Main reel-style cold email - HTML / rich email", outputs["main_html"], height=330)
        st.text_area("Short recruiter-safe version - plain text", outputs["short_plain"], height=220)
        st.text_area("Short recruiter-safe version - Markdown", outputs["short_markdown"], height=220)
        st.text_area("Short recruiter-safe version - HTML / rich email", outputs["short_html"], height=220)
        st.text_area("Follow-up email - plain text", outputs["follow_plain"], height=190)
        st.text_area("Follow-up email - Markdown", outputs["follow_markdown"], height=190)
        st.text_area("Follow-up email - HTML / rich email", outputs["follow_html"], height=190)
        st.text_area("LinkedIn backup DM", outputs["linkedin_dm"], height=120)
        st.text_area("Hook used", st.session_state["outreach_record"].get("selected_hook", ""), height=80)
        if st.session_state["outreach_record"].get("confidence_label") in {"Medium confidence", "Low confidence", "Do not use"}:
            st.warning("The selected email confidence is not high. Consider checking the contact manually before sending.")
        st.info("For Gmail, the HTML version may need to be pasted through a rich-text capable editor or copied from a rendered preview to preserve clickable labels.")
        st.text_area("Copy-ready ChatGPT refinement prompt", st.session_state.get("chatgpt_prompt", ""), height=360)
        if st.button("Save Generated Outreach", use_container_width=True):
            app_id = save_application(st.session_state["outreach_record"])
            st.success(f"Saved generated outreach as application #{app_id}.")


def render_tracker() -> None:
    st.subheader("Tracker")
    df = get_applications()
    if df.empty:
        st.info("No saved applications yet.")
        return

    filters = st.columns(6)
    with filters[0]:
        company_filter = st.text_input("Company filter")
    with filters[1]:
        title_filter = st.text_input("Job title filter")
    with filters[2]:
        confidence_filter = st.selectbox("Confidence", ["All", *sorted([x for x in df["confidence_label"].dropna().unique()])])
    with filters[3]:
        status_filter = st.selectbox("Status", ["All", *STATUS_OPTIONS])
    with filters[4]:
        priority_filter = st.selectbox("Priority", ["All", *PRIORITY_OPTIONS])
    with filters[5]:
        follow_due = st.checkbox("Follow-up due")

    filtered = df.copy()
    if company_filter:
        filtered = filtered[filtered["company_name"].str.contains(company_filter, case=False, na=False)]
    if title_filter:
        filtered = filtered[filtered["job_title"].str.contains(title_filter, case=False, na=False)]
    if confidence_filter != "All":
        filtered = filtered[filtered["confidence_label"] == confidence_filter]
    if status_filter != "All":
        filtered = filtered[filtered["status"] == status_filter]
    if priority_filter != "All":
        filtered = filtered[filtered["priority"] == priority_filter]
    if follow_due:
        filtered = filtered[(filtered["follow_up_date"].fillna("") <= today_iso()) & (filtered["follow_up_date"].fillna("") != "")]

    display_cols = [
        "id",
        "created_at",
        "company_name",
        "job_title",
        "job_url",
        "company_domain",
        "contact_name",
        "contact_title",
        "selected_email",
        "confidence_label",
        "confidence_score",
        "status",
        "follow_up_date",
        "priority",
        "notes",
    ]
    st.dataframe(filtered[display_cols], use_container_width=True, hide_index=True)

    edit_cols = st.columns([1, 1, 1, 1])
    selected_id = edit_cols[0].number_input("Application ID", min_value=1, step=1)
    new_status = edit_cols[1].selectbox("Update status", STATUS_OPTIONS)
    new_priority = edit_cols[2].selectbox("Update priority", PRIORITY_OPTIONS)
    if edit_cols[3].button("Apply Update", use_container_width=True):
        update_application(int(selected_id), {"status": new_status, "priority": new_priority})
        st.success("Tracker row updated. Refresh filters if needed.")

    danger_cols = st.columns([1, 3])
    if danger_cols[0].button("Delete ID", use_container_width=True):
        delete_application(int(selected_id))
        st.warning(f"Deleted application #{int(selected_id)}.")

    export_path = export_to_csv()
    csv_bytes = Path(export_path).read_bytes()
    st.download_button(
        "Export all records to CSV",
        data=csv_bytes,
        file_name="exported_contacts.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_settings(settings: dict) -> None:
    st.subheader("Settings")
    with st.form("settings_form"):
        full_name = st.text_input("Full name", value=settings.get("full_name", "Ayush Meshram"))
        email = st.text_input("Email", value=settings.get("email") or "")
        phone = st.text_input("Phone, optional", value=settings.get("phone") or "")
        linkedin_url = st.text_input("LinkedIn URL", value=settings.get("linkedin_url", "https://www.linkedin.com/in/ayush-meshram025/"))
        github_url = st.text_input("GitHub URL", value=settings.get("github_url", "https://github.com/Ayush141910"))
        portfolio_url = st.text_input("Portfolio URL", value=settings.get("portfolio_url", "https://portfolio-two-orcin-btti7o0q2p.vercel.app/"))
        default_signature = st.text_area("Default signature/style note", value=settings.get("default_signature") or "Reel-style warm outreach")
        default_follow_up_days = st.number_input("Default follow-up days", min_value=1, max_value=30, value=int(settings.get("default_follow_up_days") or 4))
        default_priority = st.selectbox(
            "Default priority",
            PRIORITY_OPTIONS,
            index=PRIORITY_OPTIONS.index(settings.get("default_priority", "Medium")) if settings.get("default_priority", "Medium") in PRIORITY_OPTIONS else 1,
        )
        submitted = st.form_submit_button("Save Settings", use_container_width=True)
        if submitted:
            save_settings(
                {
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "linkedin_url": linkedin_url,
                    "github_url": github_url,
                    "portfolio_url": portfolio_url,
                    "default_signature": default_signature,
                    "default_follow_up_days": int(default_follow_up_days),
                    "default_priority": default_priority,
                }
            )
            st.success("Settings saved. Generated emails will use the latest values.")


def render_help() -> None:
    st.subheader("Help / Rules")
    st.markdown(
        """
**What this app does**

This app helps find likely recruiter or hiring contact emails and generate warm, role-specific outreach after you apply to a job.

**What this app does not do**

It does not guarantee exact recruiter emails. It does not verify exact inbox ownership. It does not scrape LinkedIn. It does not send emails automatically. It does not replace paid contact databases. It does not invent personal connections.

**Email confidence warning**

High confidence does not mean guaranteed deliverability. Medium confidence should be manually checked when possible. Low confidence emails should generally not be used. MX records show that a domain can receive email, not that a specific inbox exists.

**Link formatting warning**

Markdown and HTML versions show LinkedIn, GitHub, and Portfolio as clean clickable labels. Plain text emails cannot hide raw URLs, so the plain text version may show the full links.

**Ethical usage**

Use this app only for targeted professional job outreach. Do not spam. Do not send misleading emails. Do not fake referrals, conversations, or relationships. Respect opt-outs. Do not repeatedly contact people who do not respond.
"""
    )


def main() -> None:
    bootstrap()
    settings = get_settings()
    render_header()
    tabs = st.tabs(["Find Contact", "Generate Email", "Tracker", "Settings", "Help / Rules"])
    with tabs[0]:
        render_find_contact(settings)
    with tabs[1]:
        render_generate_email(settings)
    with tabs[2]:
        render_tracker()
    with tabs[3]:
        render_settings(settings)
    with tabs[4]:
        render_help()


if __name__ == "__main__":
    main()
