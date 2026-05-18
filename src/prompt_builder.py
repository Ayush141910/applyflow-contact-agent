from __future__ import annotations


def build_chatgpt_refinement_prompt(
    company: str,
    job_title: str,
    job_description: str,
    contact_name: str,
    contact_title: str,
    contact_email: str,
    contact_context: str,
    selected_hook: str,
    resume_text: str,
    settings: dict,
    confidence_label: str,
) -> str:
    linkedin = settings.get("linkedin_url", "")
    github = settings.get("github_url", "")
    portfolio = settings.get("portfolio_url", "")
    return f"""You are helping me write a warm cold email after I applied to a job.

Use only the information below. Do not invent experience, personal connections, referrals, posts, conversations, or company research.

Goal:
Write the email in this framework:
Context -> Connection/Hook -> What stood out -> Fit -> 3 proof bullets -> Resume/links -> Respectful ask.

Company:
{company}

Job title:
{job_title}

Job description:
{job_description}

Contact:
Name: {contact_name}
Title: {contact_title}
Email: {contact_email}
Context: {contact_context}

Selected hook:
{selected_hook}

Resume text from the exact resume I submitted:
{resume_text}

My links:
LinkedIn: {linkedin}
GitHub: {github}
Portfolio: {portfolio}

Important link formatting:
In the Markdown email version, do not show raw URLs. Use:
[LinkedIn]({linkedin}) | [GitHub]({github}) | [Portfolio]({portfolio})

In the HTML email version, do not show raw URLs. Use:
<a href="{linkedin}">LinkedIn</a> |
<a href="{github}">GitHub</a> |
<a href="{portfolio}">Portfolio</a>

Write:
1. 3 subject lines
2. Main reel-style cold email, 150-220 words
3. Main reel-style cold email in Markdown format with clickable labeled links
4. Main reel-style cold email in HTML format with clickable labeled links
5. Short recruiter-safe version, 90-140 words
6. Follow-up email, 60-100 words
7. LinkedIn DM under 500 characters
8. One sentence explaining why the email works
9. Any caution if the contact/email confidence is weak

Current contact/email confidence:
{confidence_label}

Rules:
- Do not invent anything.
- Do not fake a personal connection.
- Use only truthful hooks.
- Use 3 bullet points based on the submitted resume.
- Make it sound natural, confident, and professional.
- Avoid desperate language.
- Avoid generic phrases like "I am passionate and hardworking."
- Do not show raw URLs in Markdown or HTML versions.
- Show links as LinkedIn, GitHub, and Portfolio.
"""
