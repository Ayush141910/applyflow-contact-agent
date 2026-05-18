from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from .utils import DATA_DIR, OUTPUTS_DIR, ensure_directories, today_iso


DB_PATH = DATA_DIR / "applyflow.db"


APPLICATION_COLUMNS = [
    "created_at",
    "updated_at",
    "company_name",
    "company_domain",
    "job_title",
    "job_url",
    "job_location",
    "department",
    "job_description",
    "contact_name",
    "contact_title",
    "contact_linkedin",
    "contact_context",
    "selected_email",
    "email_candidates",
    "generic_aliases",
    "confidence_score",
    "confidence_label",
    "confidence_notes",
    "resume_filename",
    "resume_text",
    "match_score",
    "matched_skills",
    "missing_keywords",
    "selected_hook",
    "subject_lines",
    "main_email_plain",
    "main_email_markdown",
    "main_email_html",
    "short_email_plain",
    "short_email_markdown",
    "short_email_html",
    "follow_up_email_plain",
    "follow_up_email_markdown",
    "follow_up_email_html",
    "linkedin_dm",
    "chatgpt_prompt",
    "status",
    "priority",
    "follow_up_date",
    "notes",
]


def _connect() -> sqlite3.Connection:
    ensure_directories()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    ensure_directories()
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                updated_at TEXT,

                company_name TEXT NOT NULL,
                company_domain TEXT,
                job_title TEXT NOT NULL,
                job_url TEXT,
                job_location TEXT,
                department TEXT,
                job_description TEXT,

                contact_name TEXT,
                contact_title TEXT,
                contact_linkedin TEXT,
                contact_context TEXT,

                selected_email TEXT,
                email_candidates TEXT,
                generic_aliases TEXT,
                confidence_score INTEGER,
                confidence_label TEXT,
                confidence_notes TEXT,

                resume_filename TEXT,
                resume_text TEXT,
                match_score INTEGER,
                matched_skills TEXT,
                missing_keywords TEXT,
                selected_hook TEXT,

                subject_lines TEXT,

                main_email_plain TEXT,
                main_email_markdown TEXT,
                main_email_html TEXT,

                short_email_plain TEXT,
                short_email_markdown TEXT,
                short_email_html TEXT,

                follow_up_email_plain TEXT,
                follow_up_email_markdown TEXT,
                follow_up_email_html TEXT,

                linkedin_dm TEXT,
                chatgpt_prompt TEXT,

                status TEXT DEFAULT 'Applied',
                priority TEXT DEFAULT 'Medium',
                follow_up_date TEXT,
                notes TEXT
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT DEFAULT 'Ayush Meshram',
                email TEXT,
                phone TEXT,
                linkedin_url TEXT DEFAULT 'https://www.linkedin.com/in/ayush-meshram025/',
                github_url TEXT DEFAULT 'https://github.com/Ayush141910',
                portfolio_url TEXT DEFAULT 'https://portfolio-two-orcin-btti7o0q2p.vercel.app/',
                default_signature TEXT,
                default_follow_up_days INTEGER DEFAULT 4,
                default_priority TEXT DEFAULT 'Medium'
            );
            """
        )
        existing = conn.execute("SELECT COUNT(*) AS count FROM settings").fetchone()["count"]
        if existing == 0:
            conn.execute(
                """
                INSERT INTO settings (
                    full_name, linkedin_url, github_url, portfolio_url,
                    default_signature, default_follow_up_days, default_priority
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "Ayush Meshram",
                    "https://www.linkedin.com/in/ayush-meshram025/",
                    "https://github.com/Ayush141910",
                    "https://portfolio-two-orcin-btti7o0q2p.vercel.app/",
                    "Reel-style warm outreach",
                    4,
                    "Medium",
                ),
            )
        conn.commit()


def save_application(record: dict[str, Any]) -> int:
    now = today_iso()
    data = {column: record.get(column) for column in APPLICATION_COLUMNS}
    data["created_at"] = data.get("created_at") or now
    data["updated_at"] = now
    data["status"] = data.get("status") or "Applied"
    data["priority"] = data.get("priority") or "Medium"
    columns = list(data.keys())
    placeholders = ", ".join(["?"] * len(columns))
    with _connect() as conn:
        cursor = conn.execute(
            f"INSERT INTO applications ({', '.join(columns)}) VALUES ({placeholders})",
            [data[column] for column in columns],
        )
        conn.commit()
        return int(cursor.lastrowid)


def update_application(id: int, record: dict[str, Any]) -> None:
    data = {key: value for key, value in record.items() if key in APPLICATION_COLUMNS}
    data["updated_at"] = today_iso()
    assignments = ", ".join(f"{key} = ?" for key in data)
    with _connect() as conn:
        conn.execute(
            f"UPDATE applications SET {assignments} WHERE id = ?",
            [*data.values(), id],
        )
        conn.commit()


def get_applications() -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql_query("SELECT * FROM applications ORDER BY created_at DESC, id DESC", conn)


def delete_application(id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM applications WHERE id = ?", (id,))
        conn.commit()


def export_to_csv(path: str | Path | None = None) -> Path:
    output_path = Path(path) if path else OUTPUTS_DIR / "exported_contacts.csv"
    df = get_applications()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def get_settings() -> dict[str, Any]:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM settings ORDER BY id LIMIT 1").fetchone()
    return dict(row) if row else {}


def save_settings(settings: dict[str, Any]) -> None:
    existing = get_settings()
    allowed = [
        "full_name",
        "email",
        "phone",
        "linkedin_url",
        "github_url",
        "portfolio_url",
        "default_signature",
        "default_follow_up_days",
        "default_priority",
    ]
    data = {key: settings.get(key) for key in allowed}
    assignments = ", ".join(f"{key} = ?" for key in allowed)
    with _connect() as conn:
        conn.execute(
            f"UPDATE settings SET {assignments} WHERE id = ?",
            [data[key] for key in allowed] + [existing.get("id", 1)],
        )
        conn.commit()
