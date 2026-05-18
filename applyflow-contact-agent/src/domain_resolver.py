from __future__ import annotations

import re
from urllib.parse import urlparse

import tldextract


_EXTRACTOR = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)

ATS_DOMAINS = {
    "greenhouse.io",
    "lever.co",
    "myworkdayjobs.com",
    "workdayjobs.com",
    "ashbyhq.com",
    "icims.com",
    "smartrecruiters.com",
    "jobvite.com",
    "taleo.net",
    "oraclecloud.com",
    "successfactors.com",
    "bamboohr.com",
    "workable.com",
    "jobs.lever.co",
    "boards.greenhouse.io",
}


def normalize_domain(domain: str | None) -> str:
    if not domain:
        return ""
    domain = domain.strip().lower()
    if "://" not in domain:
        domain = f"https://{domain}"
    parsed = urlparse(domain)
    host = parsed.netloc or parsed.path
    host = host.split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return re.sub(r"[^a-z0-9.-]", "", host).strip(".")


def extract_domain_from_url(url: str | None) -> str:
    if not url:
        return ""
    host = normalize_domain(url)
    if not host:
        return ""
    extracted = _EXTRACTOR(host)
    if not extracted.domain or not extracted.suffix:
        return host
    return f"{extracted.domain}.{extracted.suffix}"


def is_ats_domain(domain: str | None) -> bool:
    host = normalize_domain(domain)
    if not host:
        return False
    return any(host == ats or host.endswith(f".{ats}") for ats in ATS_DOMAINS)


def suggest_domain_from_company(company_name: str | None) -> str:
    """Placeholder by design. V1 avoids aggressive company-domain guessing."""
    return ""
