from __future__ import annotations

from typing import Any

from core.config import Settings, load_settings
from core.utils import read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.corruption import corrupt_clean_dataframe
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from pipelines.phase1 import run_baseline_pipeline
from retrieval.index import LocalEmbeddingIndex


def _step(label: str) -> None:
    print(f"\n[corruption_flow] === {label} ===")


def _index_and_evaluate(
    settings: Settings,
    df,
    embeddings_path,
    metrics_path,
    answers_path,
    quality_name: str,
) -> dict[str, Any]:
    index = LocalEmbeddingIndex.build(df, settings, embeddings_output_path=embeddings_path)
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=metrics_path,
        answers_output_path=answers_path,
    )
    quality = run_data_quality_checks(df, settings, quality_name)
    freshness = build_freshness_report(df, settings, report_path=None)
    return {"index": index, "metrics": bundle.summary, "quality": quality, "freshness": freshness}


def main() -> None:
    settings = load_settings()

    # 1. Load baseline metrics và clean dataset. Nếu Phase 1 chưa chạy (self-healing),
    #    tự động chạy lại baseline pipeline trước khi tiếp tục Phase 2.
    _step("Load Baseline: tải dataset & metrics sạch từ Phase 1")
    if settings.paths.clean_json.exists() and settings.paths.baseline_metrics.exists():
        import pandas as pd

        baseline_df = pd.read_json(settings.paths.clean_json)
        baseline_metrics = read_json(settings.paths.baseline_metrics)
    else:
        print("[corruption_flow] Không tìm thấy artifacts baseline -> tự chạy Phase 1 trước (self-healing).")
        baseline_bundle = run_baseline_pipeline(settings)
        baseline_df = baseline_bundle["df"]
        baseline_metrics = baseline_bundle["metrics_summary"]
    print(f"[corruption_flow] Baseline: {len(baseline_df)} dòng | hit_rate={baseline_metrics.get('retrieval_hit_rate', 0):.2%}")

    # 2. Tạo corrupted dataframe (6 kịch bản lỗi)
    _step("Corrupt: tiêm 6 kịch bản lỗi vào dữ liệu")
    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    print(f"[corruption_flow] Corrupted: {len(corrupted_df)} dòng (từ {len(baseline_df)} dòng gốc).")

    # 3. Save corrupted artifacts
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))

    # 4. Rebuild index (papers-corrupted) và evaluate
    _step("Index + Evaluate: dữ liệu bị lỗi (papers-corrupted)")
    corrupted = _index_and_evaluate(
        settings,
        corrupted_df,
        embeddings_path=settings.paths.corrupted_embeddings_json,
        metrics_path=settings.paths.corrupted_metrics,
        answers_path=settings.paths.corrupted_answers,
        quality_name="corrupted",
    )
    print(
        f"[corruption_flow] Corrupted hit_rate={corrupted['metrics']['retrieval_hit_rate']:.2%} | "
        f"GX success={corrupted['quality']['gx_success']} | is_fresh={corrupted['freshness']['is_fresh']}"
    )

    # 5. (quality checks/freshness trên corrupted data đã chạy ở bước 4)

    # 6. Repair: tái tạo lại từ raw snapshot nguyên thủy (idempotent self-healing) —
    #    raw_records_json không hề bị corruption chạm vào, nên clean lại từ đầu sẽ luôn
    #    cho ra kết quả giống hệt baseline_df, bất kể chạy corruption_flow bao nhiêu lần.
    _step("Repair: tái tạo dữ liệu sạch từ raw snapshot (Idempotent Self-Healing)")
    from datetime import UTC, datetime

    from ingestion.cleaning import build_clean_dataframe
    from ingestion.crossref import load_raw_records

    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, datetime.now(UTC))
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    print(f"[corruption_flow] Repaired: {len(repaired_df)} dòng (khớp baseline: {len(repaired_df) == len(baseline_df)}).")

    # 7. Evaluate repaired dataset
    _step("Index + Evaluate: dữ liệu đã phục hồi (papers-repaired)")
    repaired = _index_and_evaluate(
        settings,
        repaired_df,
        embeddings_path=settings.paths.repaired_embeddings_json,
        metrics_path=settings.paths.repaired_metrics,
        answers_path=settings.paths.repaired_answers,
        quality_name="repaired",
    )
    print(
        f"[corruption_flow] Repaired hit_rate={repaired['metrics']['retrieval_hit_rate']:.2%} | "
        f"GX success={repaired['quality']['gx_success']} | is_fresh={repaired['freshness']['is_fresh']}"
    )

    # 8. Comparison report (3-state: Baseline vs Corrupted vs Repaired)
    _step("Report: sinh báo cáo đối chiếu 3 trạng thái")
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted["metrics"],
        repaired_metrics=repaired["metrics"],
        corrupted_quality=corrupted["quality"],
        repaired_quality=repaired["quality"],
        corrupted_freshness=corrupted["quality"]["freshness"],
        repaired_freshness=repaired["quality"]["freshness"],
    )
    print(f"[corruption_flow] Báo cáo đã ghi tại: {settings.paths.comparison_report}")
    print("\n[corruption_flow] Hoàn tất Phase 2 (Corruption -> Repair Flow).")


if __name__ == "__main__":
    main()
