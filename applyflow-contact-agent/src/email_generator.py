from __future__ import annotations

import re
import unicodedata

from .domain_resolver import normalize_domain


def normalize_name(name: str | None) -> list[str]:
    if not name:
        return []
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_name = ascii_name.lower().replace("'", "").replace("’", "")
    ascii_name = re.sub(r"[-_/]", " ", ascii_name)
    ascii_name = re.sub(r"[^a-z\s.]", "", ascii_name)
    parts = [part.strip(".") for part in ascii_name.split() if part.strip(".")]
    return parts


def generate_direct_email_candidates(full_name: str | None, domain: str | None) -> list[dict]:
    domain = normalize_domain(domain)
    parts = normalize_name(full_name)
    if not parts or not domain:
        return []
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ""
    middle = parts[1:-1]
    candidates: list[tuple[str, str]] = []
    if first and last:
        candidates.extend(
            [
                (f"{first}.{last}@{domain}", "first.last"),
                (f"{first[0]}{last}@{domain}", "firstinitiallast"),
                (f"{first}{last}@{domain}", "firstlast"),
                (f"{first}@{domain}", "first"),
                (f"{last}.{first}@{domain}", "last.first"),
                (f"{last}{first}@{domain}", "lastfirst"),
                (f"{last}@{domain}", "last"),
                (f"{first}_{last}@{domain}", "first_last"),
                (f"{first[0]}.{last}@{domain}", "firstinitial.lastname"),
                (f"{last}{first[0]}@{domain}", "lastfirstinitial"),
            ]
        )
        if middle:
            candidates.append((f"{first}.{'.'.join(middle)}.{last}@{domain}", "first.middle.last"))
            candidates.append((f"{first}{''.join(middle)}{last}@{domain}", "firstmiddlelast"))
    else:
        candidates.append((f"{first}@{domain}", "first"))

    seen = set()
    output = []
    for email, pattern in candidates:
        if email not in seen:
            seen.add(email)
            output.append({"email": email, "type": "direct_candidate", "pattern": pattern})
    return output


def generate_generic_aliases(domain: str | None) -> list[dict]:
    domain = normalize_domain(domain)
    if not domain:
        return []
    aliases = [
        "careers",
        "recruiting",
        "talent",
        "jobs",
        "hr",
        "people",
        "recruitment",
        "universityrecruiting",
        "earlycareers",
        "campusrecruiting",
        "collegejobs",
        "students",
    ]
    return [
        {"email": f"{alias}@{domain}", "type": "generic_alias", "pattern": "generic_alias"}
        for alias in aliases
    ]
