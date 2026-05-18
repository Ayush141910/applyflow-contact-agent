from __future__ import annotations


CONTACT_RANKINGS = [
    "technical recruiter",
    "data recruiter",
    "analytics recruiter",
    "university recruiter",
    "early careers recruiter",
    "talent acquisition partner",
    "recruiter",
    "hiring manager",
    "data analytics manager",
    "bi manager",
    "data engineering manager",
    "director of analytics",
    "director of data",
    "head of data",
    "careers",
    "recruiting",
]


def _quote(value: str | None) -> str:
    return f'"{value.strip()}"' if value and value.strip() else '""'


def generate_recruiter_search_queries(
    company: str, domain: str | None, job_title: str, department: str | None
) -> list[str]:
    company_q = _quote(company)
    job_q = _quote(job_title)
    dept_q = _quote(department or "Data")
    queries = [
        f"site:linkedin.com/in {company_q} \"technical recruiter\"",
        f"site:linkedin.com/in {company_q} \"talent acquisition\"",
        f"site:linkedin.com/in {company_q} \"recruiter\" {dept_q}",
        f"site:linkedin.com/in {company_q} \"data recruiter\"",
        f"site:linkedin.com/in {company_q} \"analytics recruiter\"",
        f"site:linkedin.com/in {company_q} \"university recruiter\"",
        f"site:linkedin.com/in {company_q} \"early careers\"",
        f"{company_q} \"technical recruiter\" {job_q}",
        f"{company_q} \"talent acquisition partner\"",
        f"{company_q} \"recruiting\" {dept_q}",
    ]
    if domain:
        queries.extend(
            [
                f"site:{domain} \"recruiter\"",
                f"site:{domain} \"talent acquisition\"",
                f"site:{domain} \"careers@\"",
                f"site:{domain} \"recruiting@\"",
                f"site:{domain} \"talent@\"",
            ]
        )
    return queries


def generate_hiring_manager_search_queries(
    company: str, domain: str | None, job_title: str, department: str | None
) -> list[str]:
    company_q = _quote(company)
    job_q = _quote(job_title)
    dept_q = _quote(department or "Data")
    return [
        f"site:linkedin.com/in {company_q} \"data analytics manager\"",
        f"site:linkedin.com/in {company_q} \"business intelligence manager\"",
        f"site:linkedin.com/in {company_q} \"data engineering manager\"",
        f"site:linkedin.com/in {company_q} \"director analytics\"",
        f"site:linkedin.com/in {company_q} \"head of data\"",
        f"site:linkedin.com/in {company_q} {dept_q} \"manager\"",
        f"site:linkedin.com/in {company_q} {job_q}",
    ]


def rank_contact_title(contact_title: str | None, job_title: str | None, department: str | None) -> dict:
    title = (contact_title or "").lower()
    for index, role in enumerate(CONTACT_RANKINGS, start=1):
        if role in title:
            return {"rank": index, "matched_role": role.title()}
    if department and department.lower() in title:
        return {"rank": 8, "matched_role": "Department-Aligned Contact"}
    if job_title and any(token in title for token in job_title.lower().split()):
        return {"rank": 8, "matched_role": "Role-Aligned Contact"}
    return {"rank": 99, "matched_role": "Unknown"}
