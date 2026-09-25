"""Test tich hop offline cho tang orchestration (src/pipelines/).

Dung LLM_PROVIDER="mock" (khong goi API that, khong can key) de chay trong CI/
may local ma khong phu thuoc mang hay quota. Vi mock LLM khong ho tro
`with_structured_output`, LLM judge trong evaluation/metrics.py se tu dong
fallback ve heuristic token-F1 (co san, da duoc thiet ke san cho truong hop
nay) -- van cho ket qua xac dinh (deterministic) de assert.
"""

from __future__ import annotations

from dataclasses import replace
import shutil

import pandas as pd
import pytest

from core.config import load_settings
from ingestion.corruption import corrupt_clean_dataframe
from pipelines.phase1 import run_baseline_pipeline

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def integration_settings(tmp_path_factory):
    """Settings tro toan bo output vao thu muc tam, dung snapshot raw that da
    commit tren main (khong goi mang), va LLM_PROVIDER=mock (khong can API key)."""
    base = load_settings()
    root = tmp_path_factory.mktemp("integration")
    (root / "raw").mkdir(parents=True, exist_ok=True)

    shutil.copy(base.paths.raw_records_json, root / "raw" / "crossref_records.json")
    if base.paths.raw_api_response.exists():
        shutil.copy(base.paths.raw_api_response, root / "raw" / "crossref_response.json")

    paths = replace(
        base.paths,
        raw_api_response=root / "raw" / "crossref_response.json",
        raw_records_json=root / "raw" / "crossref_records.json",
        clean_csv=root / "clean" / "papers_clean.csv",
        clean_json=root / "clean" / "papers_clean.json",
        chroma_dir=root / "chroma",
        embeddings_json=root / "embeddings" / "papers_embeddings.json",
        corrupted_clean_csv=root / "clean" / "papers_clean_corrupted.csv",
        corrupted_clean_json=root / "clean" / "papers_clean_corrupted.json",
        corrupted_embeddings_json=root / "embeddings" / "papers_embeddings_corrupted.json",
        repaired_clean_csv=root / "clean" / "papers_clean_repaired.csv",
        repaired_clean_json=root / "clean" / "papers_clean_repaired.json",
        repaired_embeddings_json=root / "embeddings" / "papers_embeddings_repaired.json",
        eval_testset=root / "eval" / "test_set.json",
        baseline_metrics=root / "results" / "baseline_metrics.json",
        baseline_answers=root / "results" / "baseline_answers.json",
        demo_answers=root / "results" / "agent_demo_answers.json",
        quality_dir=root / "quality",
        gx_dir=root / "quality" / "gx",
        baseline_quality_report=root / "quality" / "baseline_quality_report.json",
        corrupted_quality_report=root / "quality" / "corrupted_quality_report.json",
        freshness_report=root / "quality" / "freshness_report.json",
        baseline_report=root / "reports" / "phase1_report.md",
        corruption_log=root / "results" / "corruption_log.json",
        corrupted_metrics=root / "results" / "corrupted_metrics.json",
        corrupted_answers=root / "results" / "corrupted_answers.json",
        repaired_metrics=root / "results" / "repaired_metrics.json",
        repaired_answers=root / "results" / "repaired_answers.json",
        comparison_report=root / "reports" / "corruption_report.md",
    )
    return replace(base, llm_provider="mock", paths=paths)


@pytest.fixture(scope="module")
def baseline_result(integration_settings):
    return run_baseline_pipeline(integration_settings)


def test_baseline_pipeline_ingests_and_cleans_data(baseline_result):
    assert len(baseline_result["df"]) > 0
    assert baseline_result["source_summary"]["clean_records"] == len(baseline_result["df"])


def test_baseline_pipeline_builds_index_with_all_documents(baseline_result):
    assert baseline_result["index"].collection.count() == len(baseline_result["df"])


def test_baseline_pipeline_perfect_retrieval_on_clean_data(baseline_result):
    """Tren du lieu sach, moi cau hoi phai tim dung tai lieu goc (hit rate 100%)."""
    assert baseline_result["metrics_summary"]["retrieval_hit_rate"] == 1.0


def test_baseline_pipeline_quality_gate_passes_on_clean_data(baseline_result):
    assert baseline_result["quality"]["gx_success"] is True
    assert baseline_result["freshness"]["is_fresh"] is True


def test_baseline_pipeline_writes_report_file(integration_settings, baseline_result):
    assert integration_settings.paths.baseline_report.exists()
    text = integration_settings.paths.baseline_report.read_text(encoding="utf-8")
    assert "Hit Rate" in text


def test_baseline_pipeline_is_idempotent_when_rerun(integration_settings, baseline_result):
    """Chay lai lan 2 tren cung settings phai cho dung so dong va cung tap paper_id."""
    second = run_baseline_pipeline(integration_settings)
    assert len(second["df"]) == len(baseline_result["df"])
    assert set(second["df"]["paper_id"]) == set(baseline_result["df"]["paper_id"])


def test_corruption_flow_main_runs_end_to_end_offline(monkeypatch, integration_settings, baseline_result):
    """Goi thang pipelines.corruption_flow.main() (khong chi cac manh ghep cua
    no) bang cach monkeypatch load_settings() -> integration_settings, tai su
    dung baseline da chay o fixture tren (nhanh hon, tranh chay lai tu dau)."""
    import pipelines.corruption_flow as corruption_flow

    monkeypatch.setattr(corruption_flow, "load_settings", lambda: integration_settings)

    corruption_flow.main()

    assert integration_settings.paths.comparison_report.exists()
    assert integration_settings.paths.corrupted_metrics.exists()
    assert integration_settings.paths.repaired_metrics.exists()

    import json

    repaired = json.loads(integration_settings.paths.repaired_metrics.read_text(encoding="utf-8"))
    assert repaired["retrieval_hit_rate"] == 1.0  # Idempotent repair phai phuc hoi ve dung baseline


def test_corruption_then_repair_restores_baseline_row_count(integration_settings, baseline_result):
    """End-to-end thu nho cua corruption_flow: tiem loi roi build lai tu raw
    phai cho dung so dong nhu baseline (co che Idempotent Repair)."""
    from ingestion.cleaning import build_clean_dataframe
    from ingestion.crossref import load_raw_records
    from core.utils import now_utc

    baseline_df = baseline_result["df"]
    corrupted_df = corrupt_clean_dataframe(baseline_df, integration_settings.paths.corruption_log)
    assert len(corrupted_df) != len(baseline_df) or corrupted_df["paper_id"].duplicated().any()

    repaired_records = load_raw_records(integration_settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(repaired_records, now_utc())

    assert len(repaired_df) == len(baseline_df)
    assert set(repaired_df["paper_id"]) == set(baseline_df["paper_id"])
