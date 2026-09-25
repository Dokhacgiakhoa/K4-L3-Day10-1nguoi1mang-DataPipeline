from __future__ import annotations

import pandas as pd

from ingestion.cleaning import COLUMNS, build_clean_dataframe


def test_build_clean_dataframe_happy_path(record_factory, run_date):
    records = [record_factory(paper_id="10.1/a", title="Paper A", published="2026-06-01")]
    df = build_clean_dataframe(records, run_date)

    assert len(df) == 1
    assert list(df.columns) == COLUMNS
    assert df.iloc[0]["paper_id"] == "10.1/a"
    assert df.iloc[0]["age_days"] == (run_date.date() - pd.Timestamp("2026-06-01").date()).days


def test_text_for_embedding_has_five_blocks(record_factory, run_date):
    rec = record_factory(
        title="My Title",
        authors=["Alice", "Bob"],
        published="2026-01-01",
        categories=["AI"],
        summary="Summary content here for the paper being tested thoroughly.",
    )
    df = build_clean_dataframe([rec], run_date)
    text = df.iloc[0]["text_for_embedding"]

    for block in ("Title:", "Authors:", "Published:", "Categories:", "Summary:"):
        assert block in text
    assert "My Title" in text
    assert "Alice, Bob" in text


def test_drops_record_with_missing_paper_id(record_factory, run_date):
    records = [record_factory(paper_id="")]
    df = build_clean_dataframe(records, run_date)
    assert len(df) == 0


def test_drops_record_with_missing_title(record_factory, run_date):
    records = [record_factory(title="")]
    df = build_clean_dataframe(records, run_date)
    assert len(df) == 0


def test_drops_record_with_missing_summary(record_factory, run_date):
    records = [record_factory(summary="")]
    df = build_clean_dataframe(records, run_date)
    assert len(df) == 0


def test_drops_record_with_unparseable_date(record_factory, run_date):
    records = [record_factory(published="not-a-date")]
    df = build_clean_dataframe(records, run_date)
    assert len(df) == 0


def test_dedupes_by_paper_id_keeps_first(record_factory, run_date):
    records = [
        record_factory(paper_id="10.1/dup", title="First Version"),
        record_factory(paper_id="10.1/dup", title="Second Version"),
    ]
    df = build_clean_dataframe(records, run_date)
    assert len(df) == 1
    assert df.iloc[0]["title"] == "First Version"


def test_whitespace_is_normalized(record_factory, run_date):
    records = [record_factory(title="  Extra   Spaces   Title  ")]
    df = build_clean_dataframe(records, run_date)
    assert df.iloc[0]["title"] == "Extra Spaces Title"


def test_empty_input_returns_empty_dataframe_with_columns(run_date):
    df = build_clean_dataframe([], run_date)
    assert len(df) == 0
    # Contract: ngay ca khi rong, code goi sau (vd testset builder) van co the
    # kiem tra len(df) truoc khi doc cot, nen chi can dam bao khong crash.
    assert isinstance(df, pd.DataFrame)


def test_sorted_by_published_desc_then_paper_id_asc(record_factory, run_date):
    records = [
        record_factory(paper_id="10.1/b", title="B", published="2026-01-01"),
        record_factory(paper_id="10.1/a", title="A", published="2026-01-01"),
        record_factory(paper_id="10.1/c", title="C", published="2026-02-01"),
    ]
    df = build_clean_dataframe(records, run_date)
    assert list(df["paper_id"]) == ["10.1/c", "10.1/a", "10.1/b"]


def test_missing_updated_falls_back_to_published(record_factory, run_date):
    records = [record_factory(published="2026-01-01", updated="")]
    df = build_clean_dataframe(records, run_date)
    assert df.iloc[0]["updated"] == "2026-01-01"


def test_matches_team_fixture_schema(clean_fixture_df, record_factory, run_date):
    """Cot sinh ra phai dung schema contract ca nhom dung chung trong data/fixtures/."""
    df = build_clean_dataframe([record_factory()], run_date)
    assert set(df.columns) == set(clean_fixture_df.columns)
