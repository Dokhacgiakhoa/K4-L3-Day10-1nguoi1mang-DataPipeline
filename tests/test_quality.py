from __future__ import annotations

import pandas as pd
import pytest

from observability.quality import build_freshness_report, run_data_quality_checks


@pytest.mark.slow
def test_quality_checks_pass_on_clean_fixture(clean_fixture_df, isolated_settings):
    result = run_data_quality_checks(clean_fixture_df, isolated_settings, "pytest_clean")

    assert result["success"] is True
    assert result["gx_success"] is True
    assert result["total_records"] == len(clean_fixture_df)
    assert result["freshness"]["is_fresh"] is True


@pytest.mark.slow
def test_quality_checks_fail_on_corrupted_fixture(corrupted_fixture_df, isolated_settings):
    result = run_data_quality_checks(corrupted_fixture_df, isolated_settings, "pytest_corrupted")

    assert result["gx_success"] is False
    failed = {e["expectation"] for e in result["expectations"] if not e["success"]}
    assert "expect_column_values_to_be_unique" in failed or "expect_column_value_lengths_to_be_between" in failed


@pytest.mark.slow
def test_quality_checks_write_report_file(clean_fixture_df, isolated_settings):
    run_data_quality_checks(clean_fixture_df, isolated_settings, "pytest_write")
    report_path = isolated_settings.paths.quality_dir / "pytest_write_quality_report.json"
    assert report_path.exists()


def test_freshness_report_fresh_when_below_threshold(clean_fixture_df, isolated_settings):
    report = build_freshness_report(clean_fixture_df, isolated_settings)
    assert report["total_rows"] == len(clean_fixture_df)
    assert report["is_fresh"] is True
    assert report["stale_ratio"] <= 0.25


def test_freshness_report_stale_when_over_threshold(isolated_settings):
    df = pd.DataFrame(
        {
            "published": ["2020-01-01"] * 10,
            "age_days": [2000] * 10,
        }
    )
    report = build_freshness_report(df, isolated_settings)
    assert report["stale_rows"] == 10
    assert report["stale_ratio"] == 1.0
    assert report["is_fresh"] is False


def test_freshness_report_handles_empty_dataframe(isolated_settings):
    df = pd.DataFrame(columns=["published", "age_days"])
    report = build_freshness_report(df, isolated_settings)
    assert report["total_rows"] == 0
    assert report["is_fresh"] is True


def test_freshness_report_writes_file_when_path_given(clean_fixture_df, isolated_settings, tmp_path):
    out = tmp_path / "freshness.json"
    build_freshness_report(clean_fixture_df, isolated_settings, out)
    assert out.exists()
