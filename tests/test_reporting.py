from __future__ import annotations

import pytest

from observability.reporting import generate_corruption_report, generate_phase1_report


@pytest.fixture
def sample_metrics():
    return {
        "samples": 10,
        "retrieval_hit_rate": 1.0,
        "mean_token_f1": 1.0,
        "judge_accuracy": 1.0,
        "mean_judge_score": 5,
    }


@pytest.fixture
def sample_quality():
    return {"success": True, "gx_success": True, "total_records": 24, "expectations": [{"success": True}] * 4}


@pytest.fixture
def sample_freshness():
    return {"is_fresh": True, "stale_ratio": 0.04, "freshness_threshold_days": 180}


def test_generate_phase1_report_writes_real_hit_rate(tmp_path, sample_metrics, sample_quality, sample_freshness):
    out = tmp_path / "phase1_report.md"
    source_summary = {"source_api": "Crossref", "total_records": 24, "clean_records": 24}

    generate_phase1_report(str(out), source_summary, sample_metrics, sample_quality, sample_freshness)

    text = out.read_text(encoding="utf-8")
    assert "Hit Rate: 1.0" in text
    assert "Token F1: 1.0" in text


@pytest.mark.xfail(
    reason=(
        "src/observability/reporting.py:18 doc key 'total_raw' nhung "
        "pipelines/phase1.py truyen source_summary voi key 'total_records' "
        "-> dong 'Total raw records' luon in N/A. Ghi nhan trong "
        "report/group_report.md muc 12 (Gioi han hien tai), chua duoc sua."
    ),
    strict=True,
)
def test_generate_phase1_report_total_raw_key_should_match_pipeline_contract(tmp_path, sample_metrics, sample_quality, sample_freshness):
    out = tmp_path / "phase1_report.md"
    # Day la dung contract that ma phase1.py::run_baseline_pipeline() truyen vao.
    source_summary = {"source_api": "Crossref", "total_records": 24, "clean_records": 24}

    generate_phase1_report(str(out), source_summary, sample_metrics, sample_quality, sample_freshness)

    text = out.read_text(encoding="utf-8")
    assert "Total raw records: 24" in text


def test_generate_corruption_report_shows_real_metric_values(tmp_path, sample_metrics, sample_quality, sample_freshness):
    out = tmp_path / "corruption_report.md"
    corrupted_metrics = {**sample_metrics, "retrieval_hit_rate": 0.6, "mean_token_f1": 0.82}

    generate_corruption_report(
        str(out),
        sample_metrics,
        corrupted_metrics,
        sample_metrics,
        {**sample_quality, "success": False},
        sample_quality,
        sample_freshness,
        sample_freshness,
    )

    text = out.read_text(encoding="utf-8")
    assert "1.00" in text
    assert "0.60" in text
    assert "0.82" in text


def test_generate_corruption_report_creates_parent_directory(tmp_path, sample_metrics, sample_quality, sample_freshness):
    out = tmp_path / "nested" / "dir" / "corruption_report.md"
    generate_corruption_report(
        str(out),
        sample_metrics,
        sample_metrics,
        sample_metrics,
        sample_quality,
        sample_quality,
        sample_freshness,
        sample_freshness,
    )
    assert out.exists()
