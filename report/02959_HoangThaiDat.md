# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Hoàng Thái Đạt             |
| MSSV               | 2A202602959            |
| Khóa/Lớp         | K4-L3-DAY10              |
| Tên nhóm         | 1nguoi1mang     |
| Vai trò chính    | Phụ trách Controlled Corruption & Reporting (Member 3)                 |
| Repository         | https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline |
| Ngày hoàn thành | 2026-09-25               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Tiêm lỗi dữ liệu | `src/ingestion/corruption.py` | `data/fixtures/papers_clean.json` | DataFrame bị lỗi (`corrupt_clean_dataframe`) | Hoàn thành |
| Xuất báo cáo markdown | `src/observability/reporting.py` | JSON metrics, quality report | `phase1_report.md`, `corruption_report.md` | Hoàn thành |
| Retrieval | `src/retrieval/` | Dữ liệu papers | Câu trả lời từ LLM | Hoàn thành (review & smoke test) |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng hàm corrupt_clean_dataframe | `src/ingestion/corruption.py` | Trả về dataframe lỗi (21 records) | `python -c "import pandas..."` |
| Xây dựng hàm generate_corruption_report | `src/observability/reporting.py` | Báo cáo `.md` so sánh metrics 3 Phase | Chạy hàm `generate_corruption_report` thành công |
| Smoke test QA | `src/retrieval/qa.py` | Câu trả lời chứa authors đúng | Chạy test QA |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Tạo ra các kịch bản lỗi (corruption) để mô phỏng thực tế nhằm kiểm chứng chất lượng của observability tool (GX) và sự ảnh hưởng tới pipeline truy xuất RAG. Sau đó tự động hóa việc sinh báo cáo.

### Cách triển khai
- Dùng Pandas/Numpy xử lý DataFrame: random 10% row để xoá summary, truncate title, thay đổi published date.
- Viết f-string sinh định dạng markdown để tổng hợp các metrics từ phase 1 (baseline) và phase 2 (corruption).

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Pandas DataFrame từ `papers_clean.json` và dict JSON chứa các metrics đo được. |
| Output                         | Pandas DataFrame corrupted và các file markdown (.md). |

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần tiêm lỗi một cách nhất quán (deterministic) qua nhiều lần chạy để dễ trace bug.
- **Các phương án đã cân nhắc:** Random hoàn toàn không cố định seed, hay dùng `np.random.seed(42)` để có cùng một phân phối mỗi lần chạy.
- **Phương án đã chọn:** Dùng `np.random.seed(42)`.
- **Lý do:** Giúp cho testing và evaluation có thể lặp lại (reproducibility) và đối sánh chính xác kết quả qua các phase.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `SyntaxError: unterminated string literal` khi chạy lệnh smoke test bằng bash.
- **Lệnh hoặc bước tái hiện:** Chạy chuỗi Python inline với dấu nháy kép bọc ngoài `python -c "..."` và bên trong vẫn chứa dấu nháy kép cho string.
- **Nguyên nhân gốc:** Parsing string trên terminal command bị hỏng cú pháp.
- **Cách xử lý:** Tạo một script `test_smoke.py` độc lập để chạy thay vì inline bash.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
Từ JSON nguyên gốc (Crossref API) -> DataFrame (cleaning, nối chuỗi) -> `text_for_embedding` -> ChromaDB tạo index cho RAG.
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
Kiểm tra xem văn bản được retrieve có trùng với `ground_truth_doc_ids` hay không để tính Hit Rate / Token F1 / Accuracy.
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
Quality check (GX) bắt lỗi về cấu trúc, độ dài, null, trong khi freshness theo dõi thời gian `age_days` hoặc `published` có vượt quá ngưỡng SLA không.
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
Để đảm bảo tính công bằng (fair comparison) khi đánh giá sự ảnh hưởng của corrupted data.
5. Repair được xem là thành công dựa trên artifact và metric nào?
Khi metrics (Hit Rate, Token F1) của Repaired quay trở lại bằng (hoặc xấp xỉ) Baseline, và Quality checks Pass trở lại.

## 8. Phân tích kết quả
(Đã kiểm chứng khi chạy các hàm report mẫu, sẽ có kết quả thực tế khi chạy E2E)

## 9. Điều học được và hướng cải thiện

1. Tiêm lỗi mô phỏng là một kỹ thuật hữu ích giúp kiểm tra xem Quality Gate có thực sự hoạt động.
2. Dữ liệu lỗi (mất summary) ảnh hưởng rất lớn đến độ chính xác của RAG.
3. Sinh báo cáo tự động giúp cho Pipeline dễ theo dõi và tích hợp CI/CD.

## 10. Cam kết của thành viên
- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Hoàng Thái Đạt
**Ngày xác nhận:** 2026-09-25
