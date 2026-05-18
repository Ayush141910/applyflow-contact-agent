from __future__ import annotations

import re
from typing import Any

from .utils import clean_text, escape_html


def _first_name(name: str | None) -> str:
    if not name:
        return "there"
    return name.strip().split()[0]


def _sentence_with_keyword(text: str, keyword: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    for sentence in sentences:
        if keyword.lower() in sentence.lower():
            return clean_text(sentence)[:220]
    return ""


def _top_items(items: list[str], limit: int = 3) -> list[str]:
    return [item for item in items if item][:limit]


def select_truthful_hook(
    company: str,
    job_title: str,
    contact_context: str | None,
    company_note: str | None,
    job_description: str | None,
) -> str:
    if contact_context:
        return f"noticing your connection to this search: {clean_text(contact_context)}"
    if company_note:
        return clean_text(company_note)
    jd = clean_text(job_description)
    for keyword in ["SQL", "analytics", "dashboard", "data", "reporting", "pipeline", "stakeholder"]:
        if keyword.lower() in jd.lower():
            return f"noticing the role's focus on {keyword}"
    return f"applying for the {job_title} role at {company}"


def extract_resume_proof_bullets(resume_text: str, job_keywords: list[str]) -> list[str]:
    resume = clean_text(resume_text)
    bullets = []
    for keyword in job_keywords:
        sentence = _sentence_with_keyword(resume, keyword)
        if sentence and sentence not in bullets:
            bullets.append(sentence)
        if len(bullets) == 3:
            break
    if len(bullets) < 3:
        raw_bullets = re.findall(r"(?:^|\n)\s*[-*]\s+(.+)", resume_text or "")
        for bullet in raw_bullets:
            cleaned = clean_text(bullet)[:220]
            if cleaned and cleaned not in bullets:
                bullets.append(cleaned)
            if len(bullets) == 3:
                break
    while len(bullets) < 3:
        bullets.append("Resume evidence available in the submitted resume; review this bullet before sending.")
    return bullets[:3]


def build_plain_signature(settings: dict[str, Any]) -> str:
    lines = ["Best,", settings.get("full_name") or "Ayush Meshram"]
    if settings.get("linkedin_url"):
        lines.append(f"LinkedIn: {settings['linkedin_url']}")
    if settings.get("github_url"):
        lines.append(f"GitHub: {settings['github_url']}")
    if settings.get("portfolio_url"):
        lines.append(f"Portfolio: {settings['portfolio_url']}")
    return "\n".join(lines)


def build_markdown_signature(settings: dict[str, Any]) -> str:
    name = settings.get("full_name") or "Ayush Meshram"
    links = []
    if settings.get("linkedin_url"):
        links.append(f"[LinkedIn]({settings['linkedin_url']})")
    if settings.get("github_url"):
        links.append(f"[GitHub]({settings['github_url']})")
    if settings.get("portfolio_url"):
        links.append(f"[Portfolio]({settings['portfolio_url']})")
    return f"Best,  \n{name}  \n{' | '.join(links)}"


def build_html_signature(settings: dict[str, Any]) -> str:
    name = escape_html(settings.get("full_name") or "Ayush Meshram")
    links = []
    if settings.get("linkedin_url"):
        links.append(f'<a href="{escape_html(settings["linkedin_url"])}">LinkedIn</a>')
    if settings.get("github_url"):
        links.append(f'<a href="{escape_html(settings["github_url"])}">GitHub</a>')
    if settings.get("portfolio_url"):
        links.append(f'<a href="{escape_html(settings["portfolio_url"])}">Portfolio</a>')
    return f"<p>\nBest,<br>\n{name}<br>\n{' | '.join(links)}\n</p>"


def _subject_lines(job_title: str, matched_skills: list[str], role_category: str) -> list[str]:
    focus = matched_skills[0] if matched_skills else role_category
    return [
        f"{job_title} application - {focus}",
        f"Following up on my {job_title} application",
        f"{job_title} candidate with {focus} experience",
    ]


def build_email_context(**kwargs) -> dict:
    matched_skills = _top_items(kwargs.get("matched_skills") or [], 3)
    bullets = kwargs.get("proof_bullets") or []
    hook = kwargs.get("selected_hook") or select_truthful_hook(
        kwargs["company"],
        kwargs["job_title"],
        kwargs.get("contact_context"),
        kwargs.get("company_note"),
        kwargs.get("job_description"),
    )
    role_focus = ", ".join(matched_skills[:2]) if matched_skills else kwargs.get("role_category", "the role")
    return {
        **kwargs,
        "first_name": _first_name(kwargs.get("contact_name")),
        "matched_skills": matched_skills,
        "proof_bullets": bullets,
        "selected_hook": hook,
        "role_focus": role_focus,
        "subject_lines": _subject_lines(kwargs["job_title"], matched_skills, kwargs.get("role_category", "the role")),
    }


def generate_reel_style_email_plain(**kwargs) -> str:
    c = build_email_context(**kwargs)
    signature = build_plain_signature(c["settings"])
    bullets = "\n".join(f"- {bullet}" for bullet in c["proof_bullets"][:3])
    return f"""Subject: {c['subject_lines'][0]}

Hi {c['first_name']},

I recently applied for the {c['job_title']} role at {c['company']}, and I wanted to reach out directly after {c['selected_hook']}.

What stood out to me was the role's focus on {c['role_focus']}, especially because it connects closely with the resume I submitted for this application.

A few parts of my experience that felt especially relevant:

{bullets}

I've attached the resume I submitted for this role and included my LinkedIn, GitHub, and portfolio below. I'd really appreciate the chance to be considered if my background looks relevant for the team.

{signature}"""


def generate_reel_style_email_markdown(**kwargs) -> str:
    c = build_email_context(**kwargs)
    signature = build_markdown_signature(c["settings"])
    bullets = "\n".join(f"- {bullet}" for bullet in c["proof_bullets"][:3])
    return f"""Subject: {c['subject_lines'][0]}

Hi {c['first_name']},

I recently applied for the **{c['job_title']}** role at **{c['company']}**, and I wanted to reach out directly after {c['selected_hook']}.

What stood out to me was the role's focus on **{c['role_focus']}**, especially because it connects closely with the resume I submitted for this application.

A few parts of my experience that felt especially relevant:

{bullets}

I've attached the resume I submitted for this role and included my LinkedIn, GitHub, and portfolio below. I'd really appreciate the chance to be considered if my background looks relevant for the team.

{signature}"""


def generate_reel_style_email_html(**kwargs) -> str:
    c = build_email_context(**kwargs)
    signature = build_html_signature(c["settings"])
    bullet_items = "".join(f"<li>{escape_html(bullet)}</li>" for bullet in c["proof_bullets"][:3])
    return f"""<p><strong>Subject:</strong> {escape_html(c['subject_lines'][0])}</p>
<p>Hi {escape_html(c['first_name'])},</p>
<p>I recently applied for the <strong>{escape_html(c['job_title'])}</strong> role at <strong>{escape_html(c['company'])}</strong>, and I wanted to reach out directly after {escape_html(c['selected_hook'])}.</p>
<p>What stood out to me was the role's focus on <strong>{escape_html(c['role_focus'])}</strong>, especially because it connects closely with the resume I submitted for this application.</p>
<p>A few parts of my experience that felt especially relevant:</p>
<ul>{bullet_items}</ul>
<p>I've attached the resume I submitted for this role and included my LinkedIn, GitHub, and portfolio below. I'd really appreciate the chance to be considered if my background looks relevant for the team.</p>
{signature}"""


def generate_short_email_plain(**kwargs) -> str:
    c = build_email_context(**kwargs)
    return f"""Subject: {c['subject_lines'][1]}

Hi {c['first_name']},

I recently applied for the {c['job_title']} role at {c['company']} and wanted to reach out directly. The role's focus on {c['role_focus']} lines up with the resume I submitted, especially my experience around {', '.join(c['matched_skills']) or 'the listed requirements'}.

I'd appreciate the chance to be considered if my background looks relevant for the team.

{build_plain_signature(c['settings'])}"""


def generate_short_email_markdown(**kwargs) -> str:
    c = build_email_context(**kwargs)
    return f"""Subject: {c['subject_lines'][1]}

Hi {c['first_name']},

I recently applied for the **{c['job_title']}** role at **{c['company']}** and wanted to reach out directly. The role's focus on **{c['role_focus']}** lines up with the resume I submitted, especially my experience around {', '.join(c['matched_skills']) or 'the listed requirements'}.

I'd appreciate the chance to be considered if my background looks relevant for the team.

{build_markdown_signature(c['settings'])}"""


def generate_short_email_html(**kwargs) -> str:
    c = build_email_context(**kwargs)
    return f"""<p><strong>Subject:</strong> {escape_html(c['subject_lines'][1])}</p>
<p>Hi {escape_html(c['first_name'])},</p>
<p>I recently applied for the <strong>{escape_html(c['job_title'])}</strong> role at <strong>{escape_html(c['company'])}</strong> and wanted to reach out directly. The role's focus on <strong>{escape_html(c['role_focus'])}</strong> lines up with the resume I submitted, especially my experience around {escape_html(', '.join(c['matched_skills']) or 'the listed requirements')}.</p>
<p>I'd appreciate the chance to be considered if my background looks relevant for the team.</p>
{build_html_signature(c['settings'])}"""


def generate_follow_up_plain(**kwargs) -> str:
    c = build_email_context(**kwargs)
    top_skills = ", ".join(c["matched_skills"][:2]) or "the role's requirements"
    return f"""Hi {c['first_name']},

Just wanted to follow up on my note regarding the {c['job_title']} role at {c['company']}. I'm still very interested, especially because of the role's focus on {c['role_focus']}.

I'd appreciate the chance to be considered if my background in {top_skills} looks relevant.

{build_plain_signature(c['settings'])}"""


def generate_follow_up_markdown(**kwargs) -> str:
    c = build_email_context(**kwargs)
    top_skills = ", ".join(c["matched_skills"][:2]) or "the role's requirements"
    return f"""Hi {c['first_name']},

Just wanted to follow up on my note regarding the **{c['job_title']}** role at **{c['company']}**. I'm still very interested, especially because of the role's focus on **{c['role_focus']}**.

I'd appreciate the chance to be considered if my background in {top_skills} looks relevant.

{build_markdown_signature(c['settings'])}"""


def generate_follow_up_html(**kwargs) -> str:
    c = build_email_context(**kwargs)
    top_skills = ", ".join(c["matched_skills"][:2]) or "the role's requirements"
    return f"""<p>Hi {escape_html(c['first_name'])},</p>
<p>Just wanted to follow up on my note regarding the <strong>{escape_html(c['job_title'])}</strong> role at <strong>{escape_html(c['company'])}</strong>. I'm still very interested, especially because of the role's focus on <strong>{escape_html(c['role_focus'])}</strong>.</p>
<p>I'd appreciate the chance to be considered if my background in {escape_html(top_skills)} looks relevant.</p>
{build_html_signature(c['settings'])}"""


def generate_linkedin_dm(**kwargs) -> str:
    c = build_email_context(**kwargs)
    top_skills = ", ".join(c["matched_skills"][:2]) or "the role's requirements"
    message = (
        f"Hi {c['first_name']}, I recently applied for the {c['job_title']} role at {c['company']} "
        f"and wanted to reach out directly. The role's focus on {c['role_focus']} aligns closely "
        f"with my background in {top_skills}. I'd appreciate the chance to be considered if my profile looks relevant. Thank you!"
    )
    if len(message) <= 500:
        return message
    shorter = (
        f"Hi {c['first_name']}, I recently applied for the {c['job_title']} role at {c['company']} "
        f"and wanted to reach out directly. The role's focus on {c['role_focus']} aligns with my background. "
        "I'd appreciate the chance to be considered. Thank you!"
    )
    return shorter[:500]
