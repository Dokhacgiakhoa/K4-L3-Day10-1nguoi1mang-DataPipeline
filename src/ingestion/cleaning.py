from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord

COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors_joined",
    "categories_joined",
    "primary_category",
    "published",
    "updated",
    "abs_url",
    "pdf_url",
    "age_days",
    "summary_chars",
    "text_for_embedding",
]


def _norm(value: str) -> str:
    return normalize_whitespace(value or "")


def _join(values: list[str]) -> str:
    return compact_join(_norm(item) for item in values or [])


def _to_date(value: str):
    """Parse ngay ve `datetime.date`, tra None neu khong doc duoc."""
    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed.date()


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed."""
    rows = []
    for record in records:
        title = _norm(record.title)
        summary = _norm(record.summary)
        published = _to_date(record.published)
        if not record.paper_id or not title or not summary or published is None:
            continue

        published_str = published.isoformat()
        updated = _to_date(record.updated)
        authors_joined = _join(record.authors)
        categories_joined = _join(record.categories)

        rows.append(
            {
                "paper_id": record.paper_id.strip(),
                "title": title,
                "summary": summary,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "primary_category": _norm(record.primary_category),
                "published": published_str,
                "updated": updated.isoformat() if updated else published_str,
                "abs_url": _norm(record.abs_url),
                "pdf_url": _norm(record.pdf_url),
                "age_days": (run_date.date() - published).days,
                "summary_chars": len(summary),
                "text_for_embedding": (
                    f"Title: {title}\n"
                    f"Authors: {authors_joined}\n"
                    f"Published: {published_str}\n"
                    f"Categories: {categories_joined}\n"
                    f"Summary: {summary}"
                ),
            }
        )

    frame = pd.DataFrame(rows, columns=COLUMNS)
    frame = frame.drop_duplicates(subset="paper_id", keep="first")
    frame = frame.sort_values(["published", "paper_id"], ascending=[False, True])
    return frame.reset_index(drop=True)
