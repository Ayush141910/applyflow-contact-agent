from __future__ import annotations


COMMON_PATTERNS = {"first.last", "firstinitiallast"}
RECRUITER_TERMS = [
    "recruiter",
    "talent acquisition",
    "university recruiter",
    "technical recruiter",
]
DEPARTMENT_TERMS = ["data", "analytics", "bi", "business intelligence", "engineering"]


def label_confidence(score: int) -> str:
    if score >= 80:
        return "High confidence"
    if score >= 55:
        return "Medium confidence"
    if score >= 30:
        return "Low confidence"
    return "Do not use"


def recommended_action(label: str) -> str:
    actions = {
        "High confidence": "Good candidate to email manually.",
        "Medium confidence": "Use carefully; consider verifying manually.",
        "Low confidence": "Do not use unless you verify elsewhere.",
        "Do not use": "Skip this email.",
    }
    return actions.get(label, "Review manually before using.")


def score_email_candidate(
    candidate: dict,
    contact_title: str | None,
    contact_context: str | None,
    department: str | None,
    domain_source: str | None = "provided",
    job_title: str | None = "",
) -> dict:
    score = 0
    reasons: list[str] = []
    title = (contact_title or "").lower()
    dept = (department or "").lower()
    job = (job_title or "").lower()
    pattern = candidate.get("pattern", "")

    if candidate.get("syntax_valid"):
        score += 20
        reasons.append("+20 syntax valid")
    else:
        score -= 30
        reasons.append("-30 syntax invalid")
    if candidate.get("domain_valid"):
        score += 20
        reasons.append("+20 domain exists")
    if candidate.get("mx_valid"):
        score += 20
        reasons.append("+20 MX records found")
    else:
        score -= 30
        reasons.append("-30 no MX records")
    if any(term in title for term in RECRUITER_TERMS):
        score += 15
        reasons.append("+15 recruiter or talent title")
    if any(term in f"{title} {job} {dept}" for term in DEPARTMENT_TERMS):
        score += 10
        reasons.append("+10 department alignment")
    if contact_context:
        score += 10
        reasons.append("+10 contact context provided")
    if pattern in COMMON_PATTERNS:
        score += 10
        reasons.append("+10 common email pattern")
    if candidate.get("contact_linkedin"):
        score += 5
        reasons.append("+5 LinkedIn URL provided")
    if candidate.get("type") == "generic_alias":
        score -= 20
        reasons.append("-20 generic alias fallback")
    if candidate.get("type") == "direct_candidate" and not candidate.get("contact_name"):
        score -= 25
        reasons.append("-25 no contact name")
    if not candidate.get("email") or "@" not in candidate.get("email", ""):
        score -= 40
        reasons.append("-40 no domain/email")
    if domain_source == "guessed":
        score -= 20
        reasons.append("-20 guessed domain")

    score = max(0, min(100, score))
    label = label_confidence(score)
    candidate["confidence_score"] = score
    candidate["confidence_label"] = label
    candidate["recommended_action"] = recommended_action(label)
    candidate["confidence_notes"] = "; ".join(reasons)
    return candidate
