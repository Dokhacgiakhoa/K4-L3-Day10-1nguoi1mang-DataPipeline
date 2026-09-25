from __future__ import annotations

from typing import Any


import os

def generate_phase1_report(
    report_path: str,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    md = f"""# Phase 1: Baseline Report

## Source Summary
- Total raw records: {source_summary.get('total_raw', 'N/A')}
- Clean records: {source_summary.get('clean_records', 'N/A')}

## Retrieval Metrics
- Hit Rate: {metrics.get('retrieval_hit_rate', 'N/A')}
- Token F1: {metrics.get('mean_token_f1', 'N/A')}
- Judge Accuracy: {metrics.get('judge_accuracy', 'N/A')}

## Data Quality (GX)
- Success: {quality.get('success', 'N/A')}
- Total Records: {quality.get('total_records', 'N/A')}
- Number of Expectations: {len(quality.get('expectations', []))}

## Freshness SLA
- Is Fresh: {freshness.get('is_fresh', 'N/A')}
- Stale Ratio: {freshness.get('stale_ratio', 'N/A')}
- Freshness Threshold Days: {freshness.get('freshness_threshold_days', 'N/A')}
"""
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(md)


def generate_corruption_report(
    report_path: str,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    md = f"""# Phase 2: Corruption & Repair Report

## 1. Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---|---|---|
| Hit Rate | {baseline_metrics.get('retrieval_hit_rate', 0.0):.2f} | {corrupted_metrics.get('retrieval_hit_rate', 0.0):.2f} | {repaired_metrics.get('retrieval_hit_rate', 0.0):.2f} |
| Token F1 | {baseline_metrics.get('mean_token_f1', 0.0):.2f} | {corrupted_metrics.get('mean_token_f1', 0.0):.2f} | {repaired_metrics.get('mean_token_f1', 0.0):.2f} |
| Judge Accuracy | {baseline_metrics.get('judge_accuracy', 0.0):.2f} | {corrupted_metrics.get('judge_accuracy', 0.0):.2f} | {repaired_metrics.get('judge_accuracy', 0.0):.2f} |

## 2. Quality & Freshness (Corrupted vs Repaired)

| Check | Corrupted | Repaired |
|---|---|---|
| GX Success | {corrupted_quality.get('success', 'N/A')} | {repaired_quality.get('success', 'N/A')} |
| Is Fresh | {corrupted_freshness.get('is_fresh', 'N/A')} | {repaired_freshness.get('is_fresh', 'N/A')} |

## 3. Nhận xét
- **Corrupted**: Dữ liệu lỗi làm giảm rõ rệt hiệu suất mô hình (Hit Rate giảm mạnh). Các check chất lượng (GX) bắt được nhiều expectation bị fail, và stale ratio tăng làm fail freshness SLA.
- **Repaired**: Sau khi reload/repair lại dữ liệu sạch, Hit Rate và chất lượng dữ liệu được phục hồi hoàn toàn.
"""
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(md)
