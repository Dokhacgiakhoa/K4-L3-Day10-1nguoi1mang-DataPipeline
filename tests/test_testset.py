from __future__ import annotations

import pytest

from evaluation.testset import build_test_set


def test_build_test_set_returns_ten_questions(clean_fixture_df):
    test_set = build_test_set(clean_fixture_df, output_path=None)
    assert len(test_set) == 10


def test_build_test_set_covers_four_question_types(clean_fixture_df):
    test_set = build_test_set(clean_fixture_df, output_path=None)
    types = {item["question_type"] for item in test_set}
    assert types == {"summary", "authors", "date", "categories"}


def test_build_test_set_each_item_has_required_fields(clean_fixture_df):
    test_set = build_test_set(clean_fixture_df, output_path=None)
    for item in test_set:
        for field in ("id", "question_type", "question", "ground_truth", "ground_truth_doc_ids"):
            assert field in item
        assert isinstance(item["ground_truth_doc_ids"], list)
        assert len(item["ground_truth_doc_ids"]) >= 1


def test_build_test_set_ground_truth_doc_ids_reference_real_papers(clean_fixture_df):
    test_set = build_test_set(clean_fixture_df, output_path=None)
    known_ids = set(clean_fixture_df["paper_id"])
    for item in test_set:
        assert set(item["ground_truth_doc_ids"]).issubset(known_ids)


def test_build_test_set_writes_json_when_path_given(clean_fixture_df, tmp_path):
    out = tmp_path / "test_set.json"
    build_test_set(clean_fixture_df, out)
    assert out.exists()


def test_build_test_set_raises_when_too_few_records(clean_fixture_df):
    small_df = clean_fixture_df.head(3)
    with pytest.raises(ValueError):
        build_test_set(small_df, output_path=None)
