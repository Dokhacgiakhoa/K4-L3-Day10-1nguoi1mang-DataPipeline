# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K4 — K4-L3-DAY10 |
| Tên nhóm | 1nguoi1mang |
| Repository | https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Đỗ Khắc Gia Khoa | 02733 | Pipeline Lead & Integration Architect | `src/core/config.py`, `src/core/utils.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, `data/fixtures/` |
| 2 | Đỗ Thái Sơn | 03021 | Data Ingestion & Cleaning | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py` |
| 3 | Hoàng Thái Đạt | 02959 | Controlled Corruption & Reporting | `src/ingestion/corruption.py`, `src/observability/reporting.py` |
| 4 | Nguyễn Nguyên Phong | [MSSV4] | Data Observability & Evaluation | `src/observability/quality.py`, `src/evaluation/testset.py` |

PR tương ứng: [#5](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/pull/5) (Khoa), [#6](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/pull/6) (Sơn), [#7](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/pull/7) (Đạt), [#8](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/pull/8) (Phong) — cả 4 PR đã merge vào `main`.

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành toàn bộ luồng end-to-end bắt buộc: ingest 24 bản ghi từ Crossref (snapshot offline), làm sạch thành DataFrame 24 dòng có `text_for_embedding`, đánh chỉ mục ChromaDB collection `papers-baseline`, sinh bộ test set 10 câu hỏi qua 4 nhóm nghiệp vụ, chạy baseline đạt `retrieval_hit_rate = 100%`, thiết lập Quality Gate Great Expectations 1.x cùng Freshness SLA (baseline `success=True`, `is_fresh=True`).

Nhóm tiêm đủ 6 kịch bản lỗi (drop 4 bản ghi mới nhất, xóa trắng 2 summary, chèn rác vào 2 summary, cắt ngắn 2 title, lùi ngày 4 bản ghi, nhân đôi 1 bản ghi), khiến `retrieval_hit_rate` rớt từ 100% xuống **60%** và Quality Gate fail (`gx_success=False`) do vi phạm ràng buộc `paper_id` duy nhất và độ dài `summary`. Corruption ảnh hưởng rõ nhất đến `retrieval_hit_rate` (giảm 40 điểm phần trăm) vì kịch bản drop-records khiến tài liệu biến mất hẳn khỏi vector index — nặng hơn các kịch bản chỉ làm suy giảm nội dung.

Repair (build lại từ `data/raw/crossref_records.json`, không bị corruption chạm vào) phục hồi **tuyệt đối 100%** mọi metric về đúng baseline: 24/24 dòng khớp, `gx_success=True`, `is_fresh=True`. Toàn bộ pipeline chạy idempotent — lặp lại nhiều lần cho cùng một kết quả.

Blocker đáng kể nhất trong quá trình làm nhóm không nằm ở kỹ thuật thuần túy mà ở phối hợp: một nhánh được tách ra trước khi các PR khác merge gây xung đột file ngoài phạm vi sở hữu, và một lỗi sai tên field (`hit_rate` thay vì `retrieval_hit_rate`) khiến báo cáo markdown âm thầm hiển thị sai số liệu — cả hai đã được phát hiện qua review và sửa trước khi merge.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API (hoặc snapshot data/raw/crossref_response.json)
    -> raw response/raw records (data/raw/)
    -> cleaning và data modeling (text_for_embedding, age_days)
    -> embedding (all-MiniLM-L6-v2) + ChromaDB index (papers-baseline)
    -> evaluation baseline (retrieval_hit_rate, token_f1, judge score)
    -> quality (GX 1.x) và freshness reports
    -> corruption (6 kịch bản lỗi) -> papers-corrupted
    -> re-index và re-evaluate trên dữ liệu lỗi
    -> repair từ data/raw/crossref_records.json -> papers-repaired
    -> comparison report (corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref API / snapshot offline | Fetch có retry (429/5xx), parse JATS/date-parts, fallback offline | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Sơn |
| Cleaning | `list[PaperRecord]` | Chuẩn hóa text, tính `age_days`, dedupe theo `paper_id`, dựng `text_for_embedding` | `data/clean/papers_clean.csv/json` | Sơn |
| Embedding/index | DataFrame sạch | `sentence-transformers/all-MiniLM-L6-v2`, ChromaDB 3 collection cô lập | `data/chroma/`, `data/embeddings/*.json` | (module có sẵn từ starter, Đạt review + smoke test) |
| Evaluation | DataFrame sạch, test set | Sinh 10 câu hỏi (4 loại), tính `retrieval_hit_rate`/`token_f1`/`judge_accuracy` | `data/eval/test_set.json`, `data/results/*_metrics.json` | Phong (testset), (metrics module có sẵn) |
| Observability | DataFrame ở từng trạng thái | GX 1.x ephemeral context (4 expectations) + Freshness SLA (ngưỡng 180 ngày, cảnh báo khi stale > 25%) | `data/quality/*_quality_report.json` | Phong |
| Corruption/repair | DataFrame sạch, raw snapshot | Tiêm 6 kịch bản lỗi; repair = build lại từ raw, không patch thủ công | `data/results/corruption_log.json`, `data/clean/papers_clean_corrupted/repaired.*` | Đạt (corruption), Khoa (repair trong `corruption_flow.py`) |
| Reporting | Metrics + quality JSON của 3 trạng thái | Tổng hợp markdown | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Đạt |
| Orchestration | Toàn bộ module trên | Gọi đúng thứ tự, self-healing nếu thiếu baseline, dùng chung 1 test set cho cả 3 trạng thái | `script/run_phase1.py`, `script/run_corruption_flow.py` | Khoa |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | `gemini` |
| `LLM_MODEL` | `gemini-3.6-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 (snapshot offline `data/raw/crossref_response.json`) |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày (cảnh báo khi > 25% bản ghi vượt ngưỡng) |
| Random seed | `42` (dùng trong `corrupt_clean_dataframe()` để corruption tái lập được) |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

```bash
python -m pip install -e .
```

### Lệnh chạy

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| --- | --- | --- | --- |
| Baseline pipeline | Thành công | 2026-09-25, sau khi PR #5–#8 merge vào `main` | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md`, exit code 0 |
| Corruption flow | Thành công | 2026-09-25, cùng lần chạy trên | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md`, exit code 0 |

Demo agent (3 câu hỏi mẫu bên trong `phase1.py`) bị bỏ qua do hết quota free-tier của Gemini API (`429 RESOURCE_EXHAUSTED`) — được bọc `try/except` nên không ảnh hưởng đến kết quả evaluation chính (evaluation dùng `answer_question()` trực tiếp, không qua agent, và LLM judge có fallback heuristic khi không gọi được LLM).

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | Crossref REST API (`api.crossref.org/works`), fallback snapshot `data/raw/crossref_response.json` |
| Query/filter | `agentic retrieval augmented generation large language model`; `from-pub-date:<180 ngày trước>,has-abstract:true` |
| Thời điểm lấy dữ liệu | Snapshot offline có sẵn trong repo, dùng xuyên suốt để đảm bảo tái lập được |
| Số record nhận được | 24 |
| Cơ chế retry/backoff | Retry tối đa 3 lần, backoff tăng dần, cho các status tạm thời `{429, 500, 502, 503, 504}`; hết retry hoặc lỗi mạng/JSON thì fallback đọc snapshot offline |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | str (DOI) | Có | Định danh duy nhất | Record thiếu bị loại ngay ở `parse_crossref_payload()` |
| `title`, `summary` | str | Có | Nội dung chính đưa vào embedding | Record thiếu `title`/`summary` bị loại |
| `published` | str `YYYY-MM-DD` | Có | Dùng tính `age_days` và freshness | Không parse được → loại dòng khỏi clean dataframe |
| `authors_joined`, `categories_joined` | str | Không | Metadata hiển thị và câu hỏi test set | Rỗng nếu record gốc không có |
| `age_days` | int | Có (tính toán) | `(run_date - published).days`, đầu vào cho Freshness SLA | Tính lại mỗi lần chạy dựa trên `run_date` hiện tại |
| `text_for_embedding` | str | Có | Chuỗi 5 khối (Title/Authors/Published/Categories/Summary) nạp vào ChromaDB | Rebuild lại mỗi khi bất kỳ trường nào trong 5 khối thay đổi (kể cả sau corruption) |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
| --- | --- | ---: | --- |
| Loại record thiếu `paper_id`/`title`/`summary`/`published` không đọc được | Completeness | 0/24 (snapshot hiện tại sạch) | Chạy `build_clean_dataframe()`, so `len(df)` với số record raw |
| Khử trùng lặp theo `paper_id`, giữ bản ghi đầu | Uniqueness | 0/24 (không có trùng trong snapshot gốc) | `ExpectColumnValuesToBeUnique("paper_id")` pass ở baseline |
| Sort theo `published` giảm dần, tie-break theo `paper_id` tăng dần | Consistency/Reproducibility | Toàn bộ 24 dòng | Chạy lại nhiều lần cho cùng thứ tự output |

`text_for_embedding` được ghép theo đúng 5 khối cố định (`Title / Authors / Published / Categories / Summary`), `paper_id` chính là DOI gốc từ Crossref (không tạo hash riêng), `age_days = (run_date.date() - published_date).days`.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 10 |
| Các `question_type` | `summary` (3), `authors` (3), `date` (2), `categories` (2) |
| Ground-truth document ID | `paper_id` (DOI) của bản ghi được chọn khi sinh câu hỏi |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | ChromaDB local, 3 collection cô lập: `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k` | 4 |
| LLM provider/model | `gemini` / `gemini-3.6-flash` (có fallback heuristic token-F1 khi LLM không gọi được) |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json`, sinh một lần ở Phase 1, tái sử dụng nguyên vẹn cho cả `evaluate_pipeline()` ở Phase 2 |

`corruption_flow.py` cố tình **không** sinh test set mới cho trạng thái corrupted/repaired — dùng lại chính xác cùng file `test_set.json` (cùng câu hỏi, cùng `ground_truth_doc_ids`) để biến độc lập duy nhất giữa 3 lần đánh giá là tình trạng dữ liệu, không phải độ khó câu hỏi. Nếu mỗi trạng thái dùng test set khác nhau, một `retrieval_hit_rate` thấp hơn không thể phân biệt được là do dữ liệu hỏng hay do câu hỏi khó hơn.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| Raw response/records | `data/raw/` | Có | 24 record |
| Cleaned dataset | `data/clean/` | Có | 24 dòng × 13 cột |
| Embedding manifest/index | `data/embeddings/`, `data/chroma/` | Có | Collection `papers-baseline`, 24 vector |
| Evaluation set | `data/eval/test_set.json` | Có | 10 câu, 4 loại |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Xem bảng dưới |
| Quality/freshness | `data/quality/baseline_quality_report.json`, `freshness_report.json` | Có | `success=True` |
| Baseline report | `data/reports/phase1_report.md` | Có | Sinh tự động bởi `generate_phase1_report()` |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | 1.00 | 100% câu hỏi tìm đúng tài liệu gốc trong top-4 |
| `mean_token_f1` | 1.00 | Câu trả lời trùng khớp hoàn toàn với ground truth |
| `judge_accuracy` | 1.00 | LLM judge (kèm fallback heuristic) đánh giá đúng 100% |
| `mean_judge_score` | 5 / 5 | Điểm tối đa |
| Ragas | N/A | `RUN_RAGAS` không bật (mặc định tắt vì tốn thời gian, không bắt buộc trong rubric) |

## 8. Data quality và freshness

### Quality checks

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| `ExpectTableRowCountToBeBetween` | Completeness | 5 – 5000 dòng | Pass (24 dòng) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`paper_id`, `title`, `text_for_embedding`) | Completeness | Không null | Pass | như trên |
| `ExpectColumnValuesToBeUnique("paper_id")` | Uniqueness | Không trùng | Pass | như trên |
| `ExpectColumnValueLengthsToBeBetween("summary", min_value=30)` | Validity | ≥ 30 ký tự | Pass | như trên |

### Freshness

| Thuộc tính | Giá trị |
| --- | --- |
| Freshness được đo tại | `data/clean/papers_clean.json` (và tương ứng ở corrupted/repaired) |
| Timestamp mới nhất | `2026-07-22` |
| Timestamp cũ nhất | `2026-03-28` |
| Ngưỡng freshness | 180 ngày; cảnh báo khi > 25% bản ghi vượt ngưỡng |
| Trạng thái baseline | Fresh — 1/24 dòng (4.2%) có `age_days > 180` |
| Lý do | Tỷ lệ 4.2% thấp hơn nhiều so với ngưỡng cảnh báo 25% |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| --- | --- | ---: | --- | --- | --- |
| Drop latest records | Bỏ 20% bản ghi mới nhất theo `published` | 4 | Giảm `total_records`, dữ liệu tươi biến mất | Tài liệu biến mất khỏi index — nguyên nhân chính khiến `retrieval_hit_rate` rớt còn 60% | Repair build lại từ raw, 4 bản ghi này quay lại |
| Blank summary | Xóa trắng `summary` ở một số dòng | 2 | Vi phạm `ExpectColumnValueLengthsToBeBetween(summary, min_value=30)` | Góp phần làm `gx_success=False` | Repair khôi phục `summary` gốc từ raw |
| Inject noise vào summary | Chèn ký tự rác `@@##$%$ ... !@!#` | 2 | Làm nhiễu embedding, giảm độ tương đồng cosine | Giảm `mean_token_f1`/`judge_accuracy` một phần | Repair khôi phục `summary` sạch |
| Truncate title | Cắt còn ≤ 7 ký tự | 2 | Hỏng cơ chế exact-title-match trong `answer_question()` | Một số câu hỏi không match được tiêu đề chính xác | Repair khôi phục `title` gốc |
| Stale date | Lùi `published` 365 ngày, cộng `age_days` tương ứng | 4 | Tăng `stale_ratio` | `stale_ratio` tăng từ 4.2% lên 23.8% — **chưa vượt ngưỡng 25%** nên `is_fresh` vẫn `True` | Repair khôi phục `published` gốc, `stale_ratio` về 4.2% |
| Duplicate rows | Nhân đôi một số dòng đã chọn | 1 | Vi phạm `ExpectColumnValuesToBeUnique("paper_id")` | Là nguyên nhân trực tiếp khiến `gx_success=False` | Repair build lại từ raw, không có `paper_id` trùng |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: log ghi đủ cả 6 kịch bản, mỗi kịch bản có số dòng bị ảnh hưởng và danh sách `paper_id` cụ thể bị tác động — đủ chi tiết để trace ngược từng dòng bị corrupt.

Repair đảm bảo phục hồi từ nguồn đáng tin cậy chứ không che kết quả lỗi: `repair` trong `corruption_flow.py` không sửa từng ô bị hỏng trên DataFrame đã corrupt, mà **build lại toàn bộ từ đầu** — đọc lại `data/raw/crossref_records.json` (file này chưa từng bị `corrupt_clean_dataframe()` đụng vào) rồi chạy lại `build_clean_dataframe()`. Vì vậy kết quả repaired luôn khớp baseline tuyệt đối (24/24 dòng, không có patch thủ công nào có thể để sót lỗi), và pipeline **idempotent** — chạy corruption → repair bao nhiêu lần cũng cho cùng kết quả.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.00 | 0.60 | 1.00 | -0.40 | 100% | Ảnh hưởng nặng nhất — do drop_latest_records xóa hẳn tài liệu khỏi index |
| `mean_token_f1` | 1.00 | 0.822 | 1.00 | -0.178 | 100% | Giảm nhẹ hơn hit_rate — một số câu trả lời vẫn đúng một phần dù dữ liệu nhiễu |
| `judge_accuracy` | 1.00 | 0.90 | 1.00 | -0.10 | 100% | LLM judge khoan dung hơn với câu trả lời gần đúng |
| `mean_judge_score` | 5 | 4 | 5 | -1 | 100% | Nhất quán với judge_accuracy |
| Quality checks (`gx_success`) | True | **False** | True | Fail 2/4 expectation | 100% | Fail đúng `unique(paper_id)` và `summary length` — 2 kịch bản duplicate + blank/truncate summary |
| Freshness (`is_fresh`) | True (4.2% stale) | True (23.8% stale) | True (4.2% stale) | +19.6 điểm % stale | 100% | Tăng mạnh nhưng chưa vượt ngưỡng 25% trong lần chạy này — nếu tiêm thêm stale date cho nhiều dòng hơn sẽ trip cờ `is_fresh=False` |

Hai kết luận nhân quả có bằng chứng artifact:

1. **[Duplicate rows + blank/truncate summary]** → **[`gx_success` chuyển từ `True` sang `False`, đúng 2 expectation fail: uniqueness và summary length]** → **[`retrieval_hit_rate` giảm từ 100% xuống 60%, vì `text_for_embedding` của các dòng bị corrupt mất nội dung hoặc trùng lặp gây nhiễu ranking]**.
2. **[Repair — build lại từ `data/raw/crossref_records.json` thay vì patch từng ô]** → **[`gx_success` và `is_fresh` quay lại `True`]** → **[Toàn bộ 4 metric agent phục hồi đúng 100% giá trị baseline, sai lệch 0.00 ở mọi chỉ số]**.

Kết quả khác kỳ vọng ban đầu của nhóm: dự đoán trước khi chạy (trong báo cáo cá nhân của Sơn) cho rằng kịch bản **blank summary** sẽ gây thiệt hại nặng nhất vì `summary` là khối dài nhất trong `text_for_embedding`. Số liệu thực tế cho thấy **drop_latest_records** mới là nguyên nhân chính — vì đây là kịch bản duy nhất khiến tài liệu **biến mất hoàn toàn** khỏi vector index (thay vì chỉ suy giảm nội dung), nên agent hoàn toàn không có gì để truy xuất cho những câu hỏi liên quan đến 4 bản ghi đó.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Sau khi Đạt push branch `feat/m3-corruption-reporting`, PR mở lên báo `mergeable: CONFLICTING` và đụng vào cả `crossref.py`, `cleaning.py`, `quality.py`, `data/raw/*.json` — những file không thuộc phạm vi Issue #3.
- **Nguyên nhân:** Branch được tách ra từ `main` **trước khi** PR #5 (Khoa), #6 (Sơn) và #8 (Phong) merge, nên branch vẫn còn giữ bản stub cũ của các file đó, xung đột với bản đã hoàn thiện trên `main`.
- **Cách xử lý:** Đạt rebase branch lên `main` mới nhất, resolve theo hướng giữ nguyên bản trên `main` cho các file ngoài phạm vi, chỉ giữ lại thay đổi ở `corruption.py`/`reporting.py`. Đồng thời trong lúc review, phát hiện thêm một bug độc lập: `reporting.py` đọc sai tên field (`hit_rate`/`token_f1` thay vì `retrieval_hit_rate`/`mean_token_f1` thật sự có trong metrics dict), khiến báo cáo luôn hiển thị `N/A`/`0.00` bất kể pipeline chạy tốt hay xấu — Đạt sửa lại đúng tên field trước khi merge.
- **Cách xác minh:** Sau khi Đạt push lại, `gh pr view 7 --json mergeable` trả về `MERGEABLE`/`CLEAN`. Chạy thử `generate_corruption_report()` với `data/fixtures/baseline_metrics.json` (retrieval_hit_rate=1.0) cho ra đúng "Hit Rate: 1.00" thay vì "N/A" như trước khi sửa.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| Trong lần chạy này, kịch bản stale-date chỉ tác động 4/21 dòng (23.8% stale), chưa đủ vượt ngưỡng 25% để trip `is_fresh=False` | Freshness SLA chưa được minh chứng ở trạng thái "cảnh báo" thực sự trong lần chạy này, dù cơ chế đã đúng (số liệu tăng đúng hướng) | Tăng số dòng bị stale-date trong `corrupt_clean_dataframe()` (ví dụ 30% thay vì 20%) để chủ động trip ngưỡng, chứng minh đầy đủ cả hai nhánh `is_fresh=True/False` |
| `reporting.py` (PR #7) còn một field sai tên (`source_summary.get('total_raw', ...)`, thực tế key là `total_records`) chưa được sửa | Dòng "Total raw records" trong `phase1_report.md` luôn hiển thị N/A | Đạt sửa 1 dòng, verify lại bằng cách chạy `generate_phase1_report()` với `data/fixtures` và kiểm tra dòng đó không còn N/A |
| Chưa có test tự động (pytest) cho các module — mọi xác minh hiện dựa trên script chạy tay và fixture | Không ai chạy lại được đúng bộ kiểm thử sau khi merge; dễ regressions không bị phát hiện | Viết bộ test pytest cho `build_clean_dataframe()`, `corrupt_clean_dataframe()`, `run_data_quality_checks()` dựa trên các edge case đã thử tay, đo cải thiện bằng cách tiêm lỗi giả và xác nhận test fail đúng chỗ |
| Báo cáo cá nhân của Phong (Member 4, PR #8) chưa được nộp tại thời điểm viết báo cáo nhóm này | Thiếu 1/4 báo cáo cá nhân theo yêu cầu `report/README.md` | Phong bổ sung `report/<MSSV4>_NguyenNguyenPhong.md` theo mẫu `individual_report.md` trước hạn nộp |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp (`main` sau khi PR #5–#8 merge).
- [x] Baseline, corrupted và repaired dùng cùng evaluation set (`data/eval/test_set.json`).
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng — **còn thiếu báo cáo cá nhân của Phong**.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
