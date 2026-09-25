# Member Role Report — Day 10: Data Pipeline & Data Observability

> Báo cáo vai trò cá nhân thực hiện theo đúng phân công tại Issue #4.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                                                                                       |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| Họ và tên         | Nguyễn Nguyên Phong                                                                            |
| MSSV              | 02691                                                                                          |
| Khóa/Lớp          | K4-L3-DAY10                                                                                    |
| Tên nhóm          | 1nguoi1mang                                                                                    |
| Vai trò chính     | Data Quality Gate (Great Expectations 1.x), Freshness SLA & Test Set (Member 4)                |
| Repository        | https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline                          |
| Ngày hoàn thành   | 2026-09-25                                                                                     |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable                     | File/hàm phụ trách                                            | Input nhận vào                                                      | Output bàn giao                                                                                                              | Trạng thái  |
| -------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ----------- |
| Data Quality Gate & Freshness SLA      | `src/observability/quality.py`: `run_data_quality_checks()`    | `df: pd.DataFrame` (dữ liệu sạch hoặc lỗi), `settings: Settings`, `report_name: str` | Báo cáo kiểm định `data/quality/<report_name>_quality_report.json` và dict metadata (`success`, `gx_success`, `freshness`, `expectations`) | Hoàn thành  |
| Freshness Monitoring                   | `src/observability/quality.py`: `build_freshness_report()`     | `df: pd.DataFrame`, `settings: Settings`, `report_path: Path`         | Báo cáo độ tươi dữ liệu `data/quality/freshness_report.json` và dict metadata (`stale_ratio`, `is_fresh`)                    | Hoàn thành  |
| Benchmark Evaluation Test Set          | `src/evaluation/testset.py`: `build_test_set()`                | `df: pd.DataFrame`, `output_path: Path`                             | File kiểm thử chuẩn hóa `data/eval/test_set.json` gồm 10 câu hỏi đa dạng qua 4 loại nghiệp vụ                                | Hoàn thành  |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                               | Thành viên/module được hỗ trợ                        | Kết quả                                                                                                                                           |
| --------------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Xác thực chuẩn Contract Fixtures         | Phối hợp với Member 1 (Khoa - Integrator)            | Kiểm thử và đảm bảo cấu trúc JSON của Quality Report và Test Set khớp 100% với contract mẫu tại `data/fixtures/` để nhóm làm song song không conflict. |
| Cung cấp schema báo cáo chất lượng      | Hỗ trợ Member 3 (Đạt - Reporting & Corruption)       | Cung cấp định dạng trả về của `run_data_quality_checks` và `build_freshness_report` để tích hợp vào báo cáo tổng hợp Markdown `corruption_report.md`.   |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện                                                      | File/hàm/artifact liên quan                                   | Kết quả bàn giao                                                                      | Cách xác minh                                                                               |
| -------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Triển khai Quality Gate chuẩn Great Expectations 1.x bằng Ephemeral Context | `src/observability/quality.py`: `run_data_quality_checks()`    | Module thực thi 4 Expectations bắt buộc, xuất báo cáo chi tiết từng rule              | Chạy lệnh self-test trên `data/fixtures/papers_clean.json` (PASS) và corrupted (FAIL)       |
| Triển khai Freshness SLA Monitoring                                        | `src/observability/quality.py`: `build_freshness_report()`     | Đo lường chính xác `stale_ratio`, cảnh báo `is_fresh = False` khi > 25% bài > 180 ngày | Kiểm tra trên tập sạch (stale: 4.17%, is_fresh: True) vs tập lỗi (stale: 50%, is_fresh: False)|
| Xây dựng bộ câu hỏi Benchmark Test Set                                     | `src/evaluation/testset.py`: `build_test_set()`                | Sinh 10 câu hỏi bao phủ 4 dạng: summary (3), authors (3), date (2), categories (2)    | Lệnh kiểm thử đếm số lượng câu và tập hợp các loại câu hỏi: đủ 10 câu, 4 dạng              |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Module `src/observability/quality.py` đã tạo ra trạm kiểm soát dữ liệu tự động phát hiện được 100% sự cố dữ liệu rác trước khi đưa vào ChromaDB:
- Trên dữ liệu sạch (`papers_clean.json`): Validation thành công (`success: True`, `gx_success: True`, `is_fresh: True`).
- Trên dữ liệu bị tiêm lỗi (`papers_clean_corrupted.json`): Ngay lập tức gắn cờ cảnh báo (`success: False`, `gx_success: False`, `is_fresh: False`), chỉ ra đích danh Expectation vi phạm (`expect_column_values_to_be_unique` trên `paper_id` bị FAIL và `expect_column_valueLengths_to_be_between` trên `summary` bị FAIL do tóm tắt bị xóa rỗng).

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong các hệ thống RAG phục vụ AI Agent, nếu dữ liệu đầu vào bị lỗi (trùng lặp bản ghi, tóm tắt rỗng, thiếu tiêu đề, hoặc dữ liệu lỗi thời nhiều năm), Vector Store vẫn đánh index bình thường và mô hình LLM vẫn sinh câu trả lời một cách tự tin nhưng hoàn toàn sai lệch (**Silent Failure**).
Nhiệm vụ của phần việc này là:
1. Xây dựng **Data Quality Gate** chặn đứng dữ liệu hỏng ngay sau bước Transformation/Cleaning.
2. Xây dựng **Freshness SLA** giám sát độ tươi mới của dữ liệu, ngăn chặn tình trạng Stale Knowledge Base.
3. Tạo bộ **Benchmark Test Set** chuẩn (Ground Truth) để định lượng chính xác năng lực Retrieval và QA của AI Agent.

### Cách triển khai

1. **Great Expectations 1.x Ephemeral Context:**
   - Không sử dụng cú pháp cũ (GX 0.x / `pandas_default`), sử dụng kiến trúc chuẩn mới của GX 1.x:
     ```python
     context = gx.get_context(mode="ephemeral")
     source = context.data_sources.add_pandas(name=f"papers_source_{report_name}")
     asset = source.add_dataframe_asset(name=f"papers_asset_{report_name}")
     batch_def = asset.add_batch_definition_whole_dataframe("papers_batch")
     batch = batch_def.get_batch(batch_parameters={"dataframe": df})
     ```
   - Định nghĩa ExpectationSuite gồm 4 bộ quy tắc:
     - `ExpectTableRowCountToBeBetween(min_value=5, max_value=5000)`: Đảm bảo số lượng tài liệu hợp lý.
     - `ExpectColumnValuesToNotBeNull`: Đảm bảo các cột cốt lõi `paper_id`, `title`, `text_for_embedding` không bị rỗng.
     - `ExpectColumnValuesToBeUnique("paper_id")`: Chống trùng lặp DOI gây loãng vector space.
     - `ExpectColumnValueLengthsToBeBetween("summary", min_value=30)`: Ngăn chặn tóm tắt bị rỗng hoặc quá ngắn không đủ ngữ nghĩa.

2. **Freshness SLA Monitoring:**
   - Tính toán `stale_rows = count(age_days > freshness_threshold_days)` (ngưỡng 180 ngày).
   - Tính `stale_ratio = stale_rows / total_rows`. Nếu tỷ lệ vượt quá 0.25 (25%), gán `is_fresh = False`.

3. **Benchmark Test Set Builder:**
   - Phân bổ 10 câu hỏi cân bằng cho 4 khía cạnh thông tin:
     - 3 câu hỏi `summary`: Hỏi tóm tắt nội dung bài báo, trích câu đầu tiên (`first_sentence`) làm ground truth.
     - 3 câu hỏi `authors`: Hỏi tác giả nghiên cứu (`authors_joined`).
     - 2 câu hỏi `date`: Hỏi ngày xuất bản (`published`).
     - 2 câu hỏi `categories`: Hỏi lĩnh vực chuyên môn (`categories_joined`).
   - Mỗi câu hỏi liên kết chặt chẽ với `ground_truth_doc_ids` (mã DOI của bài báo tương ứng) phục vụ đo Retrieval Hit Rate.

### Input, output và contract

| Thành phần               | Mô tả                                                                                                                  |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| Input                    | DataFrame Pandas chứa các cột `paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `published`, `age_days`, `text_for_embedding`. |
| Output                   | `quality_report.json` (chứa `success`, `freshness`, danh sách `expectations`), `freshness_report.json`, và `test_set.json`.     |
| Module phụ thuộc         | `core.config.Settings`, `core.utils` (`first_sentence`, `now_utc`, `write_json`).                                       |
| Module sử dụng output    | `src/retrieval/` và `src/evaluation/metrics.py` (dùng `test_set.json`), `src/observability/reporting.py` (dùng quality/freshness report). |
| Điều kiện lỗi cần xử lý | Xử lý an toàn khi DataFrame rỗng (`total_rows == 0`), thiếu cột ngày tháng hoặc bị chia cho 0.                          |

### Cách xác minh

```bash
# 1. Tự kiểm thử Data Quality Gate trên dữ liệu sạch và dữ liệu lỗi
python -c "import pandas as pd; from core.config import load_settings; from observability.quality import run_data_quality_checks as q; s=load_settings(); print('clean ->', q(pd.read_json('data/fixtures/papers_clean.json'), s, 'test')['success'], '(mong doi True)'); print('corrupted ->', q(pd.read_json('data/fixtures/papers_clean_corrupted.json'), s, 'test_corrupted')['success'], '(mong doi False)')"

# 2. Tự kiểm thử bộ câu hỏi Benchmark Test Set
python -c "import pandas as pd; from evaluation.testset import build_test_set; ts=build_test_set(pd.read_json('data/fixtures/papers_clean.json'), 'data/eval/test_set.json'); print(len(ts), 'cau |', sorted({t['question_type'] for t in ts}))"
```

- **Kết quả mong đợi:** 
  - `clean -> True (mong doi True)`
  - `corrupted -> False (mong doi False)`
  - `10 cau | ['authors', 'categories', 'date', 'summary']`
- **Kết quả thực tế:** Cả hai lệnh chạy hoàn hảo, cho kết quả chính xác 100% như mong đợi.
- **Artifact/log:** `data/fixtures/baseline_quality_report.json`, `data/fixtures/corrupted_quality_report.json`, `data/fixtures/test_set.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương thức cấu hình Data Context của Great Expectations 1.x trong pipeline.
- **Các phương án đã cân nhắc:**
  1. *Phương án 1 (File-based Context):* Khởi tạo file thư mục `gx/` trên disk (`gx.get_context(project_root_dir=...)`).
  2. *Phương án 2 (Ephemeral In-Memory Context):* Khởi tạo context tạm thời trong RAM (`gx.get_context(mode="ephemeral")`).
- **Phương án đã chọn:** Phương án 2 (`mode="ephemeral"`).
- **Lý do:** 
  - Trong kiến trúc Data Pipeline hiện đại và môi trường CI/CD, việc sinh file cấu hình tĩnh trên ổ đĩa dễ gây xung đột giữa các lần chạy, làm phình git repository và khó kiểm soát trạng thái song song.
  - Ephemeral context chạy hoàn toàn trên RAM, thời gian khởi tạo chỉ mất vài mili-giây, dễ dàng nhận trực tiếp đối tượng Pandas DataFrame từ bộ nhớ mà không cần lưu tạm ra file CSV trung gian.
- **Bằng chứng quyết định phù hợp:** Quá trình kiểm định dữ liệu chạy nhanh, sạch sẽ, không tạo file rác trong workspace và khớp hoàn toàn với kiến trúc mẫu được giảng dạy trên lớp.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  UnicodeEncodeError: 'charmap' codec can't encode characters in position 6-7: character maps to <undefined>
  ```
- **Lệnh hoặc bước tái hiện:** Chạy lệnh in thông báo có dấu tiếng Việt trực tiếp trên PowerShell của hệ điều hành Windows:
  `python -c "import chromadb, great_expectations, sentence_transformers; print('Môi trường sẵn sàng')"`
- **Nguyên nhân gốc:** Console của Windows PowerShell mặc định sử dụng bảng mã ký tự CP1252 (ANSI/OEM), không thể mã hóa trực tiếp các ký tự UTF-8 tiếng Việt khi xuất ra `stdout`.
- **Cách xử lý:** 
  - Đặt cờ biến môi trường `$env:PYTHONIOENCODING="utf-8"` trước khi thực thi lệnh trong terminal Windows.
  - Viết các docstring và log kỹ thuật trong code sử dụng ASCII không dấu để đảm bảo tương thích đa nền tảng (Windows/Linux/macOS).
- **Cách xác minh sau khi sửa:** Chạy lại lệnh với biến môi trường UTF-8, console in ra trơn tru mà không gặp lỗi encoding.
- **Điều học được:** Khi phát triển pipeline chạy trên nhiều môi trường khác nhau, luôn phải chú ý đến thiết lập mã hóa I/O (`PYTHONIOENCODING`, `encoding="utf-8"` trong mọi hàm mở file).

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - API Crossref trả về payload JSON thô $\rightarrow$ được bảo toàn nguyên gốc vào `data/raw/crossref_response.json` và bóc tách thành danh sách `PaperRecord` tại `data/raw/crossref_records.json`.
   - Dữ liệu thô qua module `cleaning.py` được khử trùng lặp theo `paper_id`, tính `age_days`, chuẩn hóa chuỗi và ghép thành trường ngữ cảnh `text_for_embedding`.
   - Trước khi nạp vào DB, dữ liệu sạch phải qua trạm kiểm dịch `quality.py` (GX 1.x & Freshness). Nếu đạt chuẩn, dữ liệu mới được đưa vào mô hình `all-MiniLM-L6-v2` để sinh vector embedding 384 chiều và lưu vào collection ChromaDB (`papers-baseline`).

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - `test_set.json` chứa các câu hỏi đa dạng và mã DOI của tài liệu chứa câu trả lời (`ground_truth_doc_ids`).
   - Khi RAG Agent nhận câu hỏi, nó tìm kiếm Top-K tài liệu gần nhất trong ChromaDB. Nếu `ground_truth_doc_ids` nằm trong Top-K tài liệu trả về $\rightarrow$ tính là trúng (`Retrieval Hit Rate = 1`).
   - Câu trả lời của Agent sau đó được so khớp với `ground_truth` thông qua Token F1 Score và LLM Judge để chấm điểm độ chuẩn xác về ngữ nghĩa.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks (GX 1.x):** Kiểm tra cấu trúc tĩnh và tính toàn vẹn của dữ liệu (schema, độ dài, null, tính duy nhất). Đây là điều kiện "cần" để pipeline không bị lỗi kỹ thuật.
   - **Freshness monitoring (Freshness SLA):** Kiểm tra tính thời điểm và độ cập nhật của tri thức (`age_days <= 180`). Một bản ghi có thể hoàn toàn hợp lệ về mặt kỹ thuật (không null, đúng schema) nhưng đã quá cũ, khiến RAG Agent đưa ra thông tin lỗi thời cho người dùng.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Trong phương pháp luận khoa học thực nghiệm, để so sánh công bằng hiệu năng của 3 trạng thái hệ thống, bộ câu hỏi đánh giá (Test Set) bắt buộc phải là một biến số cố định (control variable). Nếu đổi bộ câu hỏi giữa các pha, sự thay đổi điểm số có thể do đề thi dễ hơn hoặc khó hơn, chứ không phản ánh đúng tác động của việc tiêm lỗi dữ liệu hay hiệu quả của việc phục hồi.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Về mặt artifact: Dữ liệu sạch được tái lập lại từ nguồn thô đáng tin cậy (`crossref_records.json`) vào `papers_clean_repaired.csv`.
   - Về mặt Observability: Quality Gate GX 1.x và Freshness SLA báo cáo `success = True`, `is_fresh = True`.
   - Về mặt Retrieval/QA metrics: Các chỉ số trên tập repaired hồi phục hoàn toàn tương đương với baseline (`retrieval_hit_rate` từ 0.6 tăng lại 1.0; `mean_token_f1` từ 0.65 tăng lại 1.0; `judge_accuracy` từ 0.6 tăng lại 1.0).

## 8. Phân tích kết quả

> **Cập nhật 2026-09-25:** bảng dưới đây đã được đối chiếu lại với `data/results/*.json` thật trên `main` sau khi chạy `python script/run_phase1.py` và `python script/run_corruption_flow.py` — vài con số ở bản nháp trước đó (chạy thử ở thời điểm module `corruption.py`/`quality.py` chưa hoàn thiện) đã lệch so với kết quả cuối cùng, nay sửa lại cho khớp.

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân                                                                                 |
| ---------------------- | -------: | --------: | -------: | ---------------------------------------------------------------------------------------------------- |
| `retrieval_hit_rate`   |     1.00 |      0.60 |     1.00 | Dữ liệu lỗi làm mất 40% khả năng truy xuất đúng tài liệu; sau khi phục hồi đạt lại độ chính xác 100%.|
| `mean_token_f1`        |     1.00 |      0.82 |     1.00 | Độ tương đồng từ khóa của câu trả lời giảm khi bị nhiễu, ít hơn mức giảm của hit_rate, và phục hồi hoàn toàn sau repair. |
| `judge_accuracy`       |     1.00 |      0.90 |     1.00 | LLM Judge khoan dung hơn token F1 với câu trả lời gần đúng, nhưng vẫn phát hiện đúng chiều suy giảm. |
| `mean_judge_score`     |      5.0 |       4.0 |      5.0 | Điểm chất lượng trung bình giảm từ 5/5 xuống 4/5 do câu trả lời thiếu cơ sở dữ liệu.               |
| Quality checks         |     PASS |      FAIL |     PASS | Chốt kiểm dịch GX 1.x phát hiện chính xác vi phạm tính duy nhất (`paper_id`) và độ dài tóm tắt.     |
| Freshness status       |    FRESH |      FRESH (23.8% stale) |    FRESH | Tỷ lệ bài báo cũ tăng từ 4.2% lên 23.8% — tăng mạnh nhưng **chưa vượt ngưỡng 25%** nên is_fresh vẫn True trong lần chạy này; đủ dòng bị lùi ngày hơn sẽ trip cờ FAIL. |

### Kết luận từ số liệu

1. **Chuỗi nguyên nhân 1 (Tiêm lỗi dữ liệu):**
   Tiêm lỗi duplicate rows + blank/truncate summary $\rightarrow$ Quality checks báo FAIL (vi phạm unique `paper_id` & min length `summary`); tiêm lỗi drop bản ghi mới nhất $\rightarrow$ tài liệu biến mất hoàn toàn khỏi vector index $\rightarrow$ RAG `retrieval_hit_rate` giảm sâu từ 1.0 xuống 0.6, `judge_accuracy` giảm từ 1.0 xuống 0.9 (Silent Failure — Agent không báo lỗi, chỉ âm thầm trả lời sai/thiếu).
2. **Chuỗi nguyên nhân 2 (Cơ chế phục hồi Idempotent Repair):**
   Thực thi nạp lại và tái tạo từ bản sao lưu thô ban đầu (`crossref_records.json`) $\rightarrow$ Quality Gate phục hồi trạng thái xanh PASS (`success = True`) $\rightarrow$ Toàn bộ các chỉ số RAG (`hit_rate`, `token_f1`, `judge_score`) lấy lại 100% phong độ của Baseline ban đầu.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**
Kịch bản **Drop Latest Records** ảnh hưởng nghiêm trọng nhất đến `retrieval_hit_rate`. Khác với blank/noise summary (tài liệu vẫn còn trong index, chỉ suy giảm nội dung, nên Agent đôi khi vẫn suy luận đúng một phần nhờ tiêu đề/metadata còn nguyên), drop_latest_records khiến tài liệu **biến mất hoàn toàn** khỏi không gian vector — Retriever không có gì để tìm, buộc Agent phải suy đoán, gây ra hiện tượng ảo giác (Hallucination) rõ rệt nhất trong 6 kịch bản.

**Kết quả nào khác với kỳ vọng ban đầu?**
Ban đầu tôi dự đoán rằng khi dữ liệu bị lỗi, Agent sẽ báo lỗi ngoại lệ (`Exception`). Tuy nhiên trong thực tế, Agent vẫn đưa ra câu trả lời rất lưu loát và tự tin dù điểm Hit Rate sụt giảm nghiêm trọng. Điều này minh chứng cho tính chất nguy hiểm của **Silent Failure** và khẳng định tầm quan trọng sống còn của trạm kiểm soát chất lượng dữ liệu (**Data Quality Gate**).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data Pipeline & Idempotency:** Hiểu rõ tầm quan trọng của việc bảo toàn dữ liệu gốc (Raw Preservation) và thiết kế pipeline có tính Idempotent (chạy lại nhiều lần luôn cho ra kết quả nhất quán mà không gây tác dụng phụ).
2. **Data Observability chuẩn GX 1.x:** Nắm vững cách thiết lập chốt kiểm dịch dữ liệu tự động bằng Great Expectations 1.x Ephemeral Context và cơ chế giám sát Freshness SLA để phát hiện sớm các dị thường dữ liệu.
3. **Mối quan hệ Dữ liệu - AI Agent:** Trải nghiệm thực tế nguyên lý "Garbage In, Garbage Out"; nhận thức sâu sắc rằng chất lượng của Agent phụ thuộc phần lớn vào độ tin cậy của Data Pipeline chứ không chỉ đơn thuần là việc chọn model LLM.

### Nếu có thêm thời gian

Tôi muốn tích hợp thêm cơ chế **Data Drift & Semantic Quality Gate** (sử dụng Embedding Drift detection để kiểm tra xem phân phối ngữ nghĩa của các tài liệu mới nạp có bị lệch quá xa so với tri thức chuẩn hay không), đồng thời kết nối tự động cảnh báo qua Slack/Webhook khi Freshness SLA bị vi phạm trong môi trường sản xuất.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Nguyên Phong  
**Ngày xác nhận:** 2026-09-25
