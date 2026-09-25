"""Interactive Observability Dashboard (Bonus B1).

Doc truc tiep cac artifact da co san trong data/ (khong tinh toan lai gi ca --
100% du lieu hien thi la du lieu that do pipeline sinh ra) va ve:
  - Trang thai Data Quality Gate (GX 1.x) cho tung trang thai (baseline/
    corrupted/repaired), tung expectation pass/fail.
  - Freshness SLA: stale ratio, nguong canh bao.
  - Phan bo do tuoi bai bao (age_days) -- histogram.
  - Bang so sanh metric RAG 3 trang thai (retrieval_hit_rate, mean_token_f1,
    judge_accuracy, mean_judge_score).
  - "Drift" don gian: so sanh phan bo age_days / summary_chars giua Baseline
    va trang thai dang chon, de thay ro du lieu da lech bao nhieu.
  - Nhat ky 6 kich ban corruption (data/results/corruption_log.json).

Chay:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.config import load_settings  # noqa: E402

st.set_page_config(page_title="Data Observability Dashboard", page_icon="📡", layout="wide")

STATES = {
    "Baseline (dữ liệu sạch)": "baseline",
    "Corrupted (dữ liệu bị lỗi)": "corrupted",
    "Repaired (sau phục hồi)": "repaired",
}


@st.cache_data(show_spinner=False)
def _read_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def _read_clean_df(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_json(path)


def _settings():
    return load_settings(project_dir=ROOT)


def _quality_path(settings, key: str) -> Path:
    if key == "baseline":
        return settings.paths.baseline_quality_report
    if key == "corrupted":
        return settings.paths.corrupted_quality_report
    return settings.paths.quality_dir / "repaired_quality_report.json"


def _metrics_path(settings, key: str) -> Path:
    return {
        "baseline": settings.paths.baseline_metrics,
        "corrupted": settings.paths.corrupted_metrics,
        "repaired": settings.paths.repaired_metrics,
    }[key]


def _clean_path(settings, key: str) -> Path:
    return {
        "baseline": settings.paths.clean_json,
        "corrupted": settings.paths.corrupted_clean_json,
        "repaired": settings.paths.repaired_clean_json,
    }[key]


def render_status_badge(label: str, ok: bool | None) -> None:
    if ok is None:
        st.metric(label, "—", help="Chưa có artifact — chạy pipeline trước.")
    elif ok:
        st.metric(label, "✅ PASS")
    else:
        st.metric(label, "❌ FAIL")


def main() -> None:
    settings = _settings()

    st.title("📡 Data Observability Dashboard")
    st.caption(
        "Đọc trực tiếp artifact thật trong `data/` — không tính toán lại, không dữ liệu giả lập. "
        "Chạy `python script/run_phase1.py` và `python script/run_corruption_flow.py` trước để có đủ số liệu."
    )

    state_label = st.sidebar.radio("Trạng thái dữ liệu", list(STATES.keys()), index=0)
    state_key = STATES[state_label]
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Nhóm 1nguoi1mang** · [Repo](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline)"
    )

    quality = _read_json(_quality_path(settings, state_key))
    metrics = _read_json(_metrics_path(settings, state_key))
    df = _read_clean_df(_clean_path(settings, state_key))
    baseline_df = _read_clean_df(settings.paths.clean_json)

    if quality is None and metrics is None and df is None:
        st.warning(
            f"Chưa có artifact nào cho trạng thái **{state_label}**. "
            "Chạy `python script/run_phase1.py` (cho Baseline) hoặc "
            "`python script/run_corruption_flow.py` (cho Corrupted/Repaired) trước."
        )
        return

    # --- Hàng 1: trạng thái tổng quan ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_status_badge("Great Expectations 1.x", quality["gx_success"] if quality else None)
    with c2:
        is_fresh = quality["freshness"]["is_fresh"] if quality else None
        render_status_badge("Freshness SLA", is_fresh)
    with c3:
        st.metric("Số bản ghi", quality["total_records"] if quality else (len(df) if df is not None else "—"))
    with c4:
        hit_rate = metrics.get("retrieval_hit_rate") if metrics else None
        st.metric("Retrieval Hit Rate", f"{hit_rate:.0%}" if hit_rate is not None else "—")

    st.markdown("---")

    # --- Hàng 2: Quality expectations + Freshness ---
    col_q, col_f = st.columns(2)

    with col_q:
        st.subheader("🛂 Great Expectations — chi tiết từng chốt kiểm dịch")
        if quality:
            exp_df = pd.DataFrame(quality["expectations"])
            exp_df["success"] = exp_df["success"].map({True: "✅ Pass", False: "❌ Fail"})
            exp_df = exp_df[["expectation", "success"]].rename(
                columns={"expectation": "Expectation", "success": "Kết quả"}
            )
            st.dataframe(exp_df, width="stretch", hide_index=True)
        else:
            st.info("Chưa có báo cáo Quality Gate cho trạng thái này.")

    with col_f:
        st.subheader("🕐 Freshness SLA")
        if quality:
            fresh = quality["freshness"]
            st.write(
                f"**Stale ratio:** {fresh['stale_ratio']:.1%}  "
                f"(ngưỡng cảnh báo: {fresh['freshness_threshold_days']} ngày / >25% bản ghi)"
            )
            st.progress(min(fresh["stale_ratio"], 1.0))
            st.caption(
                f"{fresh['stale_rows']}/{fresh['total_rows']} bản ghi vượt ngưỡng · "
                f"Mới nhất: {fresh['latest_published']} · Cũ nhất: {fresh['oldest_published']}"
            )
        else:
            st.info("Chưa có báo cáo Freshness cho trạng thái này.")

    st.markdown("---")

    # --- Hàng 3: phân bố age_days (histogram) + drift so với baseline ---
    st.subheader("📊 Phân bố độ tuổi bài báo (`age_days`)")
    if df is not None and "age_days" in df.columns:
        col_hist, col_drift = st.columns(2)
        with col_hist:
            st.caption(f"Trạng thái đang xem: {state_label}")
            st.bar_chart(df["age_days"].value_counts().sort_index())
        with col_drift:
            st.caption("So với Baseline (Drift Monitor đơn giản)")
            if baseline_df is not None and state_key != "baseline":
                compare = pd.DataFrame(
                    {
                        "Baseline": baseline_df["age_days"].describe(),
                        state_label: df["age_days"].describe(),
                    }
                )
                st.dataframe(compare, width="stretch")
                drift = abs(df["age_days"].mean() - baseline_df["age_days"].mean())
                if drift > 30:
                    st.error(f"⚠️ Drift đáng kể: tuổi trung bình lệch {drift:.0f} ngày so với Baseline.")
                else:
                    st.success(f"Tuổi trung bình lệch {drift:.0f} ngày so với Baseline — trong ngưỡng bình thường.")
            else:
                st.info("Chọn trạng thái Corrupted hoặc Repaired để so sánh drift với Baseline.")
    else:
        st.info("Chưa có dữ liệu sạch (`age_days`) cho trạng thái này.")

    st.markdown("---")

    # --- Hàng 4: so sánh metric 3 trạng thái ---
    st.subheader("📈 So sánh chỉ số RAG — Baseline vs Corrupted vs Repaired")
    rows = []
    for label, key in STATES.items():
        m = _read_json(_metrics_path(settings, key))
        if m:
            rows.append(
                {
                    "Trạng thái": label.split(" (")[0],
                    "Hit Rate": m.get("retrieval_hit_rate"),
                    "Token F1": m.get("mean_token_f1"),
                    "Judge Accuracy": m.get("judge_accuracy"),
                }
            )
    if rows:
        chart_df = pd.DataFrame(rows).set_index("Trạng thái")
        st.bar_chart(chart_df)
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("Chưa có đủ metrics của cả 3 trạng thái. Chạy `run_phase1.py` rồi `run_corruption_flow.py`.")

    st.markdown("---")

    # --- Hàng 5: corruption log ---
    st.subheader("🧪 Nhật ký 6 kịch bản Corruption")
    log = _read_json(settings.paths.corruption_log)
    if log:
        log_rows = [
            {"Kịch bản": name, "Số dòng bị ảnh hưởng": info.get("affected_rows", "—")}
            for name, info in log.items()
        ]
        st.dataframe(pd.DataFrame(log_rows), width="stretch", hide_index=True)
    else:
        st.info("Chưa chạy `run_corruption_flow.py` nên chưa có `corruption_log.json`.")


if __name__ == "__main__":
    main()
