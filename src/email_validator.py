from __future__ import annotations

import re

import dns.exception
import dns.resolver


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_valid_email_syntax(email: str | None) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def _domain_from_email(email: str | None) -> str:
    if not email or "@" not in email:
        return ""
    return email.rsplit("@", 1)[1].strip().lower()


def domain_exists(domain: str | None) -> bool:
    if not domain:
        return False
    try:
        dns.resolver.resolve(domain, "A")
        return True
    except dns.exception.DNSException:
        try:
            dns.resolver.resolve(domain, "AAAA")
            return True
        except dns.exception.DNSException:
            return has_mx_records(domain)


def has_mx_records(domain: str | None) -> bool:
    if not domain:
        return False
    try:
        answers = dns.resolver.resolve(domain, "MX")
        return len(list(answers)) > 0
    except dns.exception.DNSException:
        return False


def validate_email_candidate(email: str | None) -> dict:
    domain = _domain_from_email(email)
    syntax_valid = is_valid_email_syntax(email)
    domain_valid = domain_exists(domain) if syntax_valid else False
    mx_valid = has_mx_records(domain) if syntax_valid else False
    notes = []
    if syntax_valid:
        notes.append("syntax valid")
    else:
        notes.append("syntax invalid")
    if domain_valid:
        notes.append("domain exists")
    else:
        notes.append("domain not confirmed")
    if mx_valid:
        notes.append("MX records found; domain can receive mail")
    else:
        notes.append("no MX records found")
    return {
        "email": email or "",
        "syntax_valid": syntax_valid,
        "domain_valid": domain_valid,
        "mx_valid": mx_valid,
        "notes": "; ".join(notes),
    }
