# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `1nguoi1mang`
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** [`K4-L3-Day10-1nguoi1mang-DataPipeline`](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline)

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | GitHub Issue | Báo cáo cá nhân |
|---:|---|---|---|---|---|---|
| 1 | Đỗ Khắc Gia Khoa (@Dokhacgiakhoa) | | dokhacgiakhoa666@gmail.com | Trưởng nhóm / Pipeline Integrator (`core/`, `phase1.py`, `corruption_flow.py`, `data/fixtures/`) | [Issue #1](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/1) | `report/<MSSV1>_HoTen.md` |
| 2 | Đỗ Thái Sơn (@tsun165) | | sondoforwork@gmail.com | Data Ingestion & Cleaning (`crossref.py`, `cleaning.py`) | [Issue #2](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/2) | `report/<MSSV2>_HoTen.md` |
| 3 | Hoàng Thái Đạt (@Liber72) | | hoangthaidat722004@gmail.com | Controlled Corruption & Reporting (`corruption.py`, `reporting.py`, smoke test `retrieval/`) | [Issue #3](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/3) | `report/<MSSV3>_HoTen.md` |
| 4 | Nguyễn Nguyên Phong (@Heargreaves1) | | nguyennguyenphong977@gmail.com | Observability & Evaluation (`quality.py` GX 1.x, Freshness SLA, `testset.py`) | [Issue #4](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/4) | `report/<MSSV4>_HoTen.md` |

*(Nếu nhóm có 3 hoặc 5-6 thành viên, xem bảng phân công chi tiết theo vai trò trong file `CHECKPOINTS.md`)*.

---

## # Cá nhân

### ## Đỗ Khắc Gia Khoa - MSSV1
- **Vai trò:** Trưởng nhóm & Điều phối Pipeline.
- **Trạng thái:** ✅ Hoàn thành, merged ([PR #5](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/pull/5)).
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập cấu hình hệ thống `core/config.py` và đường dẫn artifacts `core/utils.py`.
  - Kết nối luồng thực thi trong `src/pipelines/phase1.py` (Ingest → Clean → Index → Testset → Evaluate → Quality/Freshness → Report) và `src/pipelines/corruption_flow.py` (Corrupt → Evaluate → Idempotent Repair → 3-state Report).
  - Tạo `data/fixtures/` — dữ liệu mẫu đúng contract để cả nhóm test độc lập, không chờ nhau.
  - Chạy end-to-end thật, xác nhận: Baseline hit_rate=100% (GX PASS, fresh) → Corrupted hit_rate=60% (GX FAIL, stale) → Repaired hit_rate=100% (GX PASS, fresh, khớp baseline).
- **Điều học được / Đóng góp chính:**
  - Hiểu sâu sắc về thiết kế Idempotent Pipeline và quản lý trạng thái luồng dữ liệu đa tầng.

### ## Đỗ Thái Sơn - MSSV2
- **Vai trò:** Phụ trách Ingestion & Cleaning dữ liệu.
- **Trạng thái:** 🚧 Đang thực hiện (branch `feat/m2-ingestion`, [Issue #2](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/2)).
- **Công việc chi tiết đã hoàn thành:**
  - _(cập nhật sau khi PR merge)_
- **Điều học được / Đóng góp chính:**
  - _(cập nhật sau khi PR merge)_

### ## Hoàng Thái Đạt - MSSV3
- **Vai trò:** Phụ trách Controlled Corruption & Reporting.
- **Trạng thái:** 🚧 Đang thực hiện (branch `feat/m3-corruption-reporting`, [Issue #3](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/3)).
- **Công việc chi tiết đã hoàn thành:**
  - _(cập nhật sau khi PR merge)_
- **Điều học được / Đóng góp chính:**
  - _(cập nhật sau khi PR merge)_

### ## Nguyễn Nguyên Phong - MSSV4
- **Vai trò:** Phụ trách Data Observability (GX 1.x) & Test Set.
- **Trạng thái:** 🚧 Đang thực hiện (branch `feat/m4-quality-testset`, [Issue #4](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/4)).
- **Công việc chi tiết đã hoàn thành:**
  - _(cập nhật sau khi PR merge)_
- **Điều học được / Đóng góp chính:**
  - _(cập nhật sau khi PR merge)_
