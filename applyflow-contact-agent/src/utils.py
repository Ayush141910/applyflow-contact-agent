from __future__ import annotations

import html
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = PROJECT_ROOT / "uploads" / "resumes"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def safe_json_dumps(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=True)
    except TypeError:
        return json.dumps(str(value), ensure_ascii=True)


def safe_json_loads(value: str | None, default: Any = None) -> Any:
    if default is None:
        default = []
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def today_iso() -> str:
    return date.today().isoformat()


def add_business_days_simple(start_iso: str | None, days: int) -> str:
    current = date.fromisoformat(start_iso or today_iso())
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current.isoformat()


def escape_html(value: str | None) -> str:
    return html.escape(value or "", quote=True)


def split_lines(text: str | None) -> list[str]:
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]
