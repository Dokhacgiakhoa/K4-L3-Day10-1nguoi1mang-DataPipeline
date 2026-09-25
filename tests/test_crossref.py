from __future__ import annotations

from dataclasses import asdict

import pytest

from ingestion.crossref import PaperRecord, load_raw_records, parse_crossref_payload


def test_parse_crossref_payload_extracts_expected_fields(sample_crossref_payload):
    records = parse_crossref_payload(sample_crossref_payload)

    # Item 2 khong co abstract -> phai bi loai, chi con lai 1 record hop le.
    assert len(records) == 1
    rec = records[0]
    assert rec.paper_id == "10.1000/payload-001"
    assert rec.title == "A Paper With Messy Title"
    # _clean_text() chi bo tag XML/JATS va gom whitespace, khong unescape HTML
    # entity (&amp;/&lt;/&gt; giu nguyen dang) -- day la hanh vi thuc te dang
    # chay tren main, khong phai gia dinh.
    assert rec.summary == "Some abstract text &amp; more &lt;content&gt;."
    # Tac gia co given/family duoc ghep dung; tac gia dang "group" (chi co
    # field 'name', given/family rong) hien bi loai vi code khong fallback
    # ve 'name' -- ghi nhan hanh vi thuc te, khong phai gia dinh ly tuong.
    assert rec.authors == ["Ada Lovelace"]
    assert rec.categories == ["Artificial Intelligence", "Databases"]
    assert rec.published == "2026-03-05"
    # Crossref khong tra ve link PDF that; parse_crossref_payload() phan anh
    # dung dieu do bang cach luon de pdf_url rong (xem quyet dinh ky thuat
    # trong report/2A202603021_DoThaiSon.md muc 5).
    assert rec.pdf_url == ""


def test_parse_crossref_payload_drops_item_without_abstract(sample_crossref_payload):
    records = parse_crossref_payload(sample_crossref_payload)
    ids = [r.paper_id for r in records]
    assert "10.1000/payload-002" not in ids


def test_parse_crossref_payload_empty_items_returns_empty_list():
    assert parse_crossref_payload({"message": {"items": []}}) == []


def test_parse_crossref_payload_missing_message_key_does_not_crash():
    assert parse_crossref_payload({}) == []


def test_load_raw_records_round_trips_through_json(tmp_path, record_factory):
    records = [record_factory(paper_id="10.1/rt-1"), record_factory(paper_id="10.1/rt-2")]
    raw_path = tmp_path / "records.json"
    raw_path.write_text(
        __import__("json").dumps([asdict(r) for r in records]),
        encoding="utf-8",
    )

    loaded = load_raw_records(raw_path)

    assert loaded == records
    assert all(isinstance(r, PaperRecord) for r in loaded)


def test_load_raw_records_matches_team_raw_snapshot():
    """Snapshot da commit tren main phai luon doc duoc dung dinh dang PaperRecord."""
    from core.config import load_settings

    settings = load_settings()
    records = load_raw_records(settings.paths.raw_records_json)
    assert len(records) >= 5
    assert all(r.paper_id for r in records)
