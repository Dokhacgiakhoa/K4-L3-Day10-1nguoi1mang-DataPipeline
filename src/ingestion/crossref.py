from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import requests

from core.config import Settings
from core.utils import normalize_whitespace, write_json

CROSSREF_API_URL = "https://api.crossref.org/works"

_TAG_RE = re.compile(r"<[^>]+>")
_RETRY_STATUS = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(value: str) -> str:
    """Bo tag XML/JATS va gom whitespace ve mot space."""
    return normalize_whitespace(_TAG_RE.sub(" ", value or ""))


def _format_date_parts(date_parts: list[int]) -> str:
    """[2026, 5, 20] -> '2026-05-20'. Crossref co the thieu thang/ngay."""
    year, month, day = (list(date_parts) + [1, 1])[:3]
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    records: list[PaperRecord] = []
    for item in payload.get("message", {}).get("items", []):
        paper_id = (item.get("DOI") or "").strip()
        titles = item.get("title") or []
        title = _clean_text(titles[0]) if titles else ""
        summary = _clean_text(item.get("abstract", ""))
        if not paper_id or not title or not summary:
            continue

        authors = [
            name
            for name in (
                _clean_text(f"{a.get('given', '')} {a.get('family', '')}")
                for a in item.get("author") or []
            )
            if name
        ]
        categories = [c for c in (_clean_text(s) for s in item.get("subject") or []) if c]
        date_parts = (item.get("published") or {}).get("date-parts") or [[]]
        published = _format_date_parts(date_parts[0]) if date_parts[0] else ""
        created = (item.get("created") or {}).get("date-time", "")
        abs_url = (item.get("URL") or "").strip()

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=published,
                updated=created[:10] or published,
                abs_url=abs_url,
                pdf_url="",
                comment=f"Crossref record {paper_id}",
            )
        )
    return records


def _get_with_retry(params: dict, attempts: int = 3, backoff: float = 2.0) -> dict:
    """GET Crossref, retry khi gap status tam thoi (429/5xx)."""
    for attempt in range(attempts):
        response = requests.get(
            CROSSREF_API_URL,
            params=params,
            timeout=30,
            headers={"User-Agent": "day10-data-observability-lab/0.1"},
        )
        if response.status_code in _RETRY_STATUS and attempt < attempts - 1:
            time.sleep(backoff * (attempt + 1))
            continue
        response.raise_for_status()
        return response.json()
    raise requests.RequestException("Crossref khong tra ve ket qua hop le.")


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi Crossref API va luu raw response + records.

    Loi mang hoac payload hong -> fallback doc snapshot offline.
    """
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    try:
        payload = _get_with_retry(params)
    except (requests.RequestException, ValueError):
        return load_raw_records(settings.paths.raw_records_json)

    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_api_response, payload)
    write_json(settings.paths.raw_records_json, [asdict(r) for r in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh `PaperRecord`."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    names = {f.name for f in fields(PaperRecord)}
    return [PaperRecord(**{k: v for k, v in item.items() if k in names}) for item in payload]
