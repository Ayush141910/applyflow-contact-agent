from __future__ import annotations

import fitz

from .utils import clean_text


def extract_text_from_pdf(file) -> str:
    try:
        data = file.read()
        doc = fitz.open(stream=data, filetype="pdf")
        pages = [page.get_text("text") for page in doc]
        doc.close()
        return clean_resume_text("\n".join(pages))
    except Exception as exc:
        raise ValueError("Could not extract resume text. Please paste the resume text manually.") from exc


def clean_resume_text(text: str | None) -> str:
    return clean_text(text)
