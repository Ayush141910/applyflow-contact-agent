from __future__ import annotations

import re

from .utils import clean_text


KEYWORDS = {
    "Data Analyst": [
        "sql",
        "excel",
        "tableau",
        "power bi",
        "dashboards",
        "reporting",
        "metrics",
        "kpi",
        "analysis",
        "visualization",
        "analytics",
    ],
    "Data Engineer": [
        "etl",
        "pipelines",
        "spark",
        "kafka",
        "airflow",
        "databricks",
        "data warehouse",
        "data lake",
        "orchestration",
        "batch",
        "streaming",
    ],
    "Data Scientist": [
        "machine learning",
        "model",
        "python",
        "statistics",
        "experiment",
        "prediction",
        "classification",
        "regression",
        "feature engineering",
    ],
    "Business Analyst": [
        "requirements",
        "stakeholders",
        "process",
        "documentation",
        "operations",
        "business process",
        "user stories",
    ],
    "Product Analyst": [
        "product metrics",
        "experimentation",
        "a/b testing",
        "funnel",
        "retention",
        "user behavior",
        "product analytics",
    ],
    "Software Engineer": [
        "software",
        "api",
        "backend",
        "frontend",
        "react",
        "node",
        "java",
        "distributed systems",
    ],
}


def extract_keywords(text: str | None) -> list[str]:
    lowered = clean_text(text).lower()
    found = set()
    for keywords in KEYWORDS.values():
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", lowered):
                found.add(keyword.upper() if keyword in {"sql", "etl", "kpi", "bi"} else keyword.title())
    return sorted(found)


def detect_role_category(job_title: str | None, job_description: str | None) -> str:
    haystack = f"{job_title or ''} {job_description or ''}".lower()
    scores = {
        category: sum(1 for keyword in keywords if keyword in haystack)
        for category, keywords in KEYWORDS.items()
    }
    if "analytics engineer" in haystack:
        return "Analytics Engineer"
    if "machine learning" in haystack or "ml engineer" in haystack:
        return "Machine Learning"
    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    return best_category if best_score else "Other"


def extract_required_tools(job_description: str | None) -> list[str]:
    tool_terms = [
        "SQL",
        "Python",
        "Excel",
        "Tableau",
        "Power BI",
        "Looker",
        "Snowflake",
        "dbt",
        "Airflow",
        "Spark",
        "Kafka",
        "Databricks",
        "AWS",
        "Azure",
        "GCP",
        "R",
        "SAS",
        "Java",
        "React",
        "Node",
    ]
    text = clean_text(job_description).lower()
    return [tool for tool in tool_terms if tool.lower() in text]
