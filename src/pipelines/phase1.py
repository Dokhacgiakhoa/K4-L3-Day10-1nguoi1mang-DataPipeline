from __future__ import annotations

from typing import Any

from core.config import Settings, load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex


def _step(label: str) -> None:
    print(f"\n[phase1] === {label} ===")


def run_baseline_pipeline(settings: Settings) -> dict[str, Any]:
    """Điều phối toàn bộ chu trình Baseline (Phase 1): Ingest -> Clean -> Index -> Eval -> Report.

    Trả về dict chứa các artifact chính (df, index, metrics, quality, freshness) để
    `corruption_flow.py` có thể tái sử dụng mà không phải chạy lại từ đầu.
    """
    # 1. Load hoặc fetch raw records (fetch_source_records tự fallback về snapshot offline
    #    và luôn ghi lại data/raw/crossref_records.json phục vụ idempotent repair ở Phase 2).
    _step("Ingest: thu thập bản ghi thô từ Crossref (hoặc snapshot offline)")
    if settings.paths.raw_records_json.exists() and not settings.refresh_source:
        records = load_raw_records(settings.paths.raw_records_json)
    else:
        records = fetch_source_records(settings)
    print(f"[phase1] Thu thập được {len(records)} bản ghi thô.")

    # 2. Clean data
    _step("Clean: chuẩn hóa dữ liệu và tính age_days / text_for_embedding")
    run_date = now_utc()
    df = build_clean_dataframe(records, run_date)
    print(f"[phase1] Dữ liệu sạch: {len(df)} dòng.")

    # 3. Save clean CSV/JSON
    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))

    # 4. Build Chroma index (collection: papers-baseline)
    _step("Index: khởi tạo ChromaDB collection 'papers-baseline'")
    index = LocalEmbeddingIndex.build(df, settings, embeddings_output_path=settings.paths.embeddings_json)
    print(f"[phase1] Index sẵn sàng: {index.collection.count()} vectors.")

    # 5. Tạo hoặc load evaluation set
    _step("Testset: tạo hoặc tải bộ câu hỏi benchmark")
    if settings.paths.eval_testset.exists() and not settings.refresh_test_set:
        test_set = read_json(settings.paths.eval_testset)
    else:
        test_set = build_test_set(df, settings.paths.eval_testset)
    print(f"[phase1] Bộ testset: {len(test_set)} câu hỏi.")

    # 6. Evaluate
    _step("Evaluate: chạy QA agent trên testset và chấm điểm")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print(
        f"[phase1] Hit rate: {bundle.summary['retrieval_hit_rate']:.2%} | "
        f"Token F1: {bundle.summary['mean_token_f1']:.2%} | "
        f"Judge accuracy: {bundle.summary['judge_accuracy']:.2%}"
    )

    # 7. Quality checks + freshness report
    _step("Quality Gate: Great Expectations 1.x + Freshness SLA")
    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    print(f"[phase1] GX success: {quality['gx_success']} | is_fresh: {freshness['is_fresh']}")

    # 8. Markdown report
    _step("Report: sinh báo cáo Markdown Phase 1")
    source_summary = {
        "source_api": settings.source_api,
        "total_records": len(records),
        "clean_records": len(df),
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )
    print(f"[phase1] Báo cáo đã ghi tại: {settings.paths.baseline_report}")

    # 9. Demo agent trên vài câu hỏi mẫu (best-effort, không chặn pipeline nếu thiếu LLM key)
    _step("Demo: QA agent trả lời vài câu hỏi mẫu")
    demo_answers: list[dict[str, str]] = []
    try:
        agent = build_agent(settings, index)
        for item in test_set[:3]:
            answer = run_agent_question(agent, item["question"])
            demo_answers.append({"question": item["question"], "answer": answer})
            print(f"[phase1] Q: {item['question']}\n         A: {answer[:160]}")
        write_json(settings.paths.demo_answers, demo_answers)
    except Exception as exc:  # pragma: no cover - phụ thuộc LLM credentials tùy máy
        print(f"[phase1] Bỏ qua demo agent (thiếu LLM credentials hoặc lỗi mạng): {exc}")

    return {
        "settings": settings,
        "records": records,
        "df": df,
        "index": index,
        "test_set": test_set,
        "metrics_summary": bundle.summary,
        "quality": quality,
        "freshness": freshness,
        "source_summary": source_summary,
    }


def main() -> None:
    settings = load_settings()
    run_baseline_pipeline(settings)
    print("\n[phase1] Hoàn tất Phase 1 (Baseline Pipeline).")


if __name__ == "__main__":
    main()
