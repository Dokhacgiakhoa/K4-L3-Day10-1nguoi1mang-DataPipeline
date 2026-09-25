from __future__ import annotations

import json

import pandas as pd

from ingestion.corruption import corrupt_clean_dataframe

EXPECTED_SCENARIOS = {
    "scenario_1_drop_newest",
    "scenario_2_blank_summary",
    "scenario_3_noise_summary",
    "scenario_4_truncate_title",
    "scenario_5_shift_date",
    "scenario_6_duplicate_rows",
}


def test_corrupt_clean_dataframe_does_not_mutate_input(clean_fixture_df, tmp_path):
    original = clean_fixture_df.copy(deep=True)
    corrupt_clean_dataframe(clean_fixture_df, tmp_path / "log.json")
    pd.testing.assert_frame_equal(clean_fixture_df, original)


def test_corrupt_clean_dataframe_writes_all_six_scenarios(clean_fixture_df, tmp_path):
    log_path = tmp_path / "corruption_log.json"
    corrupt_clean_dataframe(clean_fixture_df, log_path)

    assert log_path.exists()
    log = json.loads(log_path.read_text(encoding="utf-8"))
    assert EXPECTED_SCENARIOS.issubset(set(log.keys()))
    for scenario in EXPECTED_SCENARIOS:
        assert log[scenario]["affected_rows"] >= 0


def test_corrupt_clean_dataframe_drops_some_latest_records(clean_fixture_df, tmp_path):
    corrupted = corrupt_clean_dataframe(clean_fixture_df, tmp_path / "log.json")
    log = json.loads((tmp_path / "log.json").read_text(encoding="utf-8"))
    dropped_ids = set(log["scenario_1_drop_newest"]["ids"])

    assert len(dropped_ids) > 0
    # Cac id bi drop khong con nam trong tap cuoi cung (tru khi bi duplicate lai).
    surviving_ids = set(corrupted["paper_id"])
    assert not dropped_ids.issubset(surviving_ids) or len(dropped_ids & surviving_ids) < len(dropped_ids)


def test_corrupt_clean_dataframe_can_produce_duplicate_paper_ids(clean_fixture_df, tmp_path):
    """Kich ban 6 (duplicate rows) phai lam paper_id khong con duy nhat -- day
    chinh la dieu Quality Gate (expect_column_values_to_be_unique) can bat."""
    corrupted = corrupt_clean_dataframe(clean_fixture_df, tmp_path / "log.json")
    assert corrupted["paper_id"].duplicated().any()


def test_corrupt_clean_dataframe_rebuilds_text_for_embedding(clean_fixture_df, tmp_path):
    corrupted = corrupt_clean_dataframe(clean_fixture_df, tmp_path / "log.json")
    for _, row in corrupted.iterrows():
        assert row["title"] in row["text_for_embedding"] or len(row["title"]) <= 7
        assert row["summary"] in row["text_for_embedding"]


def test_corrupt_clean_dataframe_introduces_short_summaries(clean_fixture_df, tmp_path):
    """Kich ban blank/noise summary phai tao ra it nhat 1 dong summary < 30
    ky tu -- day la dieu expect_column_value_lengths_to_be_between se bat."""
    corrupted = corrupt_clean_dataframe(clean_fixture_df, tmp_path / "log.json")
    assert (corrupted["summary"].str.len() < 30).any()


def test_corrupt_clean_dataframe_shifts_published_date_back(clean_fixture_df, tmp_path):
    corrupted = corrupt_clean_dataframe(clean_fixture_df, tmp_path / "log.json")
    log = json.loads((tmp_path / "log.json").read_text(encoding="utf-8"))
    shifted_ids = set(log["scenario_5_shift_date"]["ids"])

    baseline_by_id = clean_fixture_df.set_index("paper_id")["published"]
    corrupted_by_id = corrupted.set_index("paper_id")["published"]

    for paper_id in shifted_ids:
        if paper_id not in corrupted_by_id.index:
            continue
        old_date = pd.Timestamp(baseline_by_id.loc[paper_id])
        new_date = pd.Timestamp(corrupted_by_id.loc[paper_id])
        assert (old_date - new_date).days >= 300
