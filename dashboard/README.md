# Interactive Observability Dashboard (Bonus B1)

Trang Streamlit đọc trực tiếp các artifact thật trong `data/` (không tính toán lại, không dữ liệu giả lập) và hiển thị:

- Trạng thái Great Expectations 1.x (pass/fail từng expectation) cho Baseline / Corrupted / Repaired.
- Freshness SLA — tỷ lệ bản ghi quá hạn, ngưỡng cảnh báo.
- Phân bố độ tuổi bài báo (`age_days`) dạng histogram.
- **Drift Monitor đơn giản**: so sánh phân bố `age_days` của trạng thái đang chọn với Baseline, cảnh báo khi tuổi trung bình lệch > 30 ngày.
- Bảng so sánh `retrieval_hit_rate` / `mean_token_f1` / `judge_accuracy` giữa 3 trạng thái.
- Nhật ký chi tiết 6 kịch bản Corruption (`data/results/corruption_log.json`).

## Chạy thử

Cần chạy `python script/run_phase1.py` và `python script/run_corruption_flow.py` trước để có đủ artifact (nếu chưa, dashboard sẽ báo trạng thái nào còn thiếu thay vì crash).

```bash
python -m pip install -e ".[dashboard]"   # hoặc: uv sync --extra dashboard
streamlit run dashboard/app.py
```

Mở trình duyệt tại `http://localhost:8501`.
