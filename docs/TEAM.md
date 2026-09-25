# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `1nguoi1mang`
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** [`K4-L3-Day10-1nguoi1mang-DataPipeline`](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline)

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | GitHub Issue | Báo cáo cá nhân |
|---:|---|---|---|---|---|---|
| 1 | Đỗ Khắc Gia Khoa (@Dokhacgiakhoa) | 02733 | dokhacgiakhoa666@gmail.com | Trưởng nhóm / Pipeline Integrator (`core/`, `phase1.py`, `corruption_flow.py`, `data/fixtures/`) | [Issue #1](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/1) | [`report/02733_DoKhacGiaKhoa.md`](../report/02733_DoKhacGiaKhoa.md) |
| 2 | Đỗ Thái Sơn (@tsun165) | 03021 | sondoforwork@gmail.com | Data Ingestion & Cleaning (`crossref.py`, `cleaning.py`) | [Issue #2](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/2) | [`report/03021_DoThaiSon.md`](../report/03021_DoThaiSon.md) |
| 3 | Hoàng Thái Đạt (@Liber72) | 02959 | hoangthaidat722004@gmail.com | Controlled Corruption & Reporting (`corruption.py`, `reporting.py`, smoke test `retrieval/`) | [Issue #3](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/3) | [`report/02959_HoangThaiDat.md`](../report/02959_HoangThaiDat.md) |
| 4 | Nguyễn Nguyên Phong (@Heargreaves1) | 02691 | nguyennguyenphong977@gmail.com | Observability & Evaluation (`quality.py` GX 1.x, Freshness SLA, `testset.py`) | [Issue #4](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/4) | [`report/02691_NguyenNguyenPhong.md`](../report/02691_NguyenNguyenPhong.md) |

*(Nếu nhóm có 3 hoặc 5-6 thành viên, xem bảng phân công chi tiết theo vai trò trong file `CHECKPOINTS.md`)*.

---

## # Cá nhân

### ## Đỗ Khắc Gia Khoa - 02733
- **Vai trò:** Trưởng nhóm & Điều phối Pipeline.
- **Trạng thái:** ✅ Hoàn thành, merged ([PR #5](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/pull/5)).
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập cấu hình hệ thống `core/config.py` và đường dẫn artifacts `core/utils.py`.
  - Kết nối luồng thực thi trong `src/pipelines/phase1.py` (Ingest → Clean → Index → Testset → Evaluate → Quality/Freshness → Report) và `src/pipelines/corruption_flow.py` (Corrupt → Evaluate → Idempotent Repair → 3-state Report).
  - Tạo `data/fixtures/` — dữ liệu mẫu đúng contract để cả nhóm test độc lập, không chờ nhau.
  - Chạy end-to-end thật, xác nhận: Baseline hit_rate=100% (GX PASS, fresh) → Corrupted hit_rate=60% (GX FAIL, stale) → Repaired hit_rate=100% (GX PASS, fresh, khớp baseline).
- **Điều học được / Đóng góp chính:**
  - Hiểu sâu sắc về thiết kế Idempotent Pipeline và quản lý trạng thái luồng dữ liệu đa tầng.

### ## Đỗ Thái Sơn - 03021
- **Vai trò:** Phụ trách Ingestion & Cleaning dữ liệu.
- **Trạng thái:** ✅ Hoàn thành, merged ([PR #6](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/pull/6)). Báo cáo cá nhân: [report/03021_DoThaiSon.md](../report/03021_DoThaiSon.md).
- **Công việc chi tiết đã hoàn thành:**
  - Triển khai `parse_crossref_payload()` và `fetch_source_records()` — gọi Crossref API có retry cho status tạm thời (429/5xx), tự fallback đọc snapshot offline khi mất mạng.
  - Triển khai `build_clean_dataframe()` — chuẩn hóa text, tính `age_days`, khử trùng lặp theo `paper_id`, dựng `text_for_embedding` 5 khối, sort xác định (tie-break theo `paper_id`) để kết quả tái lập được giữa các lần chạy.
  - Xác minh toàn bộ 312 ô dữ liệu khớp tuyệt đối với `data/fixtures/papers_clean.json` (contract chuẩn của nhóm).
- **Điều học được / Đóng góp chính:**
  - Tầng ingestion phải xác định (deterministic) thì mọi so sánh baseline/corrupted/repaired phía sau mới có ý nghĩa; phát hiện và xử lý rủi ro sort không ổn định của pandas khi nhiều bản ghi trùng ngày xuất bản.

### ## Hoàng Thái Đạt - 02959
- **Vai trò:** Phụ trách Controlled Corruption & Reporting.
- **Trạng thái:** ✅ Hoàn thành, merged ([PR #7](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/pull/7)). Báo cáo cá nhân: [report/02959_HoangThaiDat.md](../report/02959_HoangThaiDat.md).
- **Công việc chi tiết đã hoàn thành:**
  - Triển khai `corrupt_clean_dataframe()` — tiêm đủ 6 kịch bản lỗi (drop bản ghi mới, xóa/nhiễu summary, cắt title, lùi ngày, nhân đôi dòng) với seed cố định để tái lập được, ghi log chi tiết từng kịch bản.
  - Triển khai `generate_phase1_report()` và `generate_corruption_report()` — sinh báo cáo Markdown đối chiếu 3 trạng thái từ metrics/quality report thật.
  - Rebase lại branch sau khi phát hiện conflict với PR #5/#6/#8 và sửa bug đọc sai tên field (`hit_rate`/`token_f1` → `retrieval_hit_rate`/`mean_token_f1`) khiến báo cáo từng hiển thị sai số liệu.
- **Điều học được / Đóng góp chính:**
  - Tiêm lỗi có seed cố định giúp kiểm chứng Quality Gate một cách tái lập được; dữ liệu bẩn (đặc biệt mất `summary`) ảnh hưởng rất lớn đến độ chính xác của RAG.

### ## Nguyễn Nguyên Phong - 02691
- **Vai trò:** Phụ trách Data Observability (GX 1.x) & Test Set.
- **Trạng thái:** ✅ Hoàn thành, merged ([PR #8](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/pull/8)). Báo cáo cá nhân: [report/02691_NguyenNguyenPhong.md](../report/02691_NguyenNguyenPhong.md).
- **Công việc chi tiết đã hoàn thành:**
  - Triển khai `run_data_quality_checks()` — Great Expectations 1.x (Ephemeral Context) với đủ 4 expectations bắt buộc.
  - Triển khai `build_freshness_report()` — Freshness SLA, cảnh báo `is_fresh=False` khi > 25% bản ghi có `age_days > 180`.
  - Xây dựng `build_test_set()` — 10 câu hỏi benchmark qua 4 dạng nghiệp vụ (summary/authors/date/categories).
- **Điều học được / Đóng góp chính:**
  - Cách thiết lập chốt kiểm dịch dữ liệu tự động chặn đứng Silent Failure trước khi dữ liệu lỗi vào serving layer.
