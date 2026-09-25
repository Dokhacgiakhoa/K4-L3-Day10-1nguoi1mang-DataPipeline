from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import json
from pathlib import Path

import pandas as pd
import pytest

from core.config import load_settings
from ingestion.crossref import PaperRecord

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"


@pytest.fixture(scope="session")
def base_settings():
    """Settings thật của repo, dùng cho các test không ghi file."""
    return load_settings()


@pytest.fixture
def isolated_settings(base_settings, tmp_path):
    """Bản sao Settings trỏ toàn bộ output vào thư mục tạm, để test không
    đụng vào data/ thật của repo (đặc biệt là data/chroma và data/quality)."""
    paths = base_settings.paths
    tmp_paths = replace(
        paths,
        chroma_dir=tmp_path / "chroma",
        embeddings_json=tmp_path / "embeddings" / "papers_embeddings.json",
        corrupted_embeddings_json=tmp_path / "embeddings" / "papers_embeddings_corrupted.json",
        repaired_embeddings_json=tmp_path / "embeddings" / "papers_embeddings_repaired.json",
        quality_dir=tmp_path / "quality",
        gx_dir=tmp_path / "quality" / "gx",
        baseline_quality_report=tmp_path / "quality" / "baseline_quality_report.json",
        corrupted_quality_report=tmp_path / "quality" / "corrupted_quality_report.json",
        freshness_report=tmp_path / "quality" / "freshness_report.json",
    )
    return replace(base_settings, paths=tmp_paths)


@pytest.fixture
def clean_fixture_df() -> pd.DataFrame:
    """DataFrame sạch chuẩn (contract) dùng làm input cho corruption/quality/testset."""
    return pd.read_json(FIXTURES_DIR / "papers_clean.json")


@pytest.fixture
def corrupted_fixture_df() -> pd.DataFrame:
    """DataFrame đã bị lỗi chuẩn (contract) — GX phải FAIL trên bộ này."""
    return pd.read_json(FIXTURES_DIR / "papers_clean_corrupted.json")


@pytest.fixture
def run_date() -> datetime:
    return datetime(2026, 9, 25, tzinfo=UTC)


def make_record(**overrides) -> PaperRecord:
    """Helper tạo PaperRecord hợp lệ, override field nào cần cho từng test case."""
    defaults = dict(
        paper_id="10.1000/test-001",
        title="A Sample Paper Title",
        summary="This is a sufficiently long summary used purely for testing purposes here.",
        authors=["Jane Doe", "John Smith"],
        categories=["Computer Science"],
        primary_category="Computer Science",
        published="2026-01-15",
        updated="2026-01-16",
        abs_url="https://doi.org/10.1000/test-001",
        pdf_url="",
        comment="",
    )
    defaults.update(overrides)
    return PaperRecord(**defaults)


@pytest.fixture
def record_factory():
    return make_record


@pytest.fixture
def sample_crossref_payload() -> dict:
    """Payload Crossref tối giản nhưng đúng cấu trúc thật, dùng cho test parse."""
    return {
        "message": {
            "items": [
                {
                    "DOI": "10.1000/payload-001",
                    "title": ["  A   Paper   With <b>Messy</b> Title  "],
                    "abstract": "<jats:p>Some <b>abstract</b> text &amp; more &lt;content&gt;.</jats:p>",
                    "author": [
                        {"given": "Ada", "family": "Lovelace"},
                        {"given": "", "family": "", "name": "Group Author"},
                    ],
                    "subject": ["Artificial Intelligence", "Databases"],
                    "published": {"date-parts": [[2026, 3, 5]]},
                    "created": {"date-time": "2026-03-06T10:00:00Z"},
                    "URL": "https://doi.org/10.1000/payload-001",
                    "link": [
                        {"URL": "https://example.org/payload-001.pdf", "content-type": "application/pdf"},
                    ],
                },
                {
                    # Item thiếu abstract -> phải bị loại bởi parse_crossref_payload
                    "DOI": "10.1000/payload-002",
                    "title": ["Paper Without Abstract"],
                    "abstract": "",
                    "author": [],
                    "subject": [],
                    "published": {"date-parts": [[2026, 4, 1]]},
                },
            ]
        }
    }


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
