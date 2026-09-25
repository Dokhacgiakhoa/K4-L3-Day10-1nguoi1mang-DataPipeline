# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Đỗ Thái Sơn |
| MSSV | 2A202603021 |
| Khóa/Lớp | K4 — K4-L3-DAY10 |
| Tên nhóm | 1nguoi1mang |
| Vai trò chính | Member 2 — Data Ingestion & Cleaning |
| Repository | https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

Issue phụ trách: [Issue #2](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/2) · Branch: `feat/m2-ingestion`

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Thu thập nguồn Crossref | `src/ingestion/crossref.py` — `fetch_source_records()`, `parse_crossref_payload()`, `load_raw_records()` | Crossref REST API; fallback `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | `list[PaperRecord]` (11 trường) + 2 file raw snapshot | Hoàn thành |
| Làm sạch & chuẩn hóa schema | `src/ingestion/cleaning.py` — `build_clean_dataframe()` | `list[PaperRecord]`, `run_date` | DataFrame 13 cột đúng schema `data/fixtures/papers_clean.json` | Hoàn thành |

Tôi chỉ nhận ownership 2 file trên. Quan hệ phụ thuộc:

- **Tôi nhận từ:** nguồn ngoài (Crossref API) và snapshot offline có sẵn trên `main`. Không phụ thuộc output của thành viên nào, nên làm song song được ngay từ đầu.
- **Ai phụ thuộc vào tôi:** Member 1 gọi cả 4 hàm trong `src/pipelines/phase1.py`; Member 3 nhận DataFrame sạch làm input cho `corrupt_clean_dataframe()`; Member 4 chạy Great Expectations và freshness SLA trên chính các cột tôi sinh ra.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Phát hiện sai lệch dữ liệu giữa `data/raw/crossref_records.json` và `data/fixtures/papers_clean.json` ở trường `pdf_url` | Member 1 (sở hữu `data/`) | Xác định snapshot `crossref_records.json` là bản cũ; fixture mới đúng. Chi tiết ở mục 5. |
| Đối chiếu chéo cột `age_days` với fixture freshness | Member 4 (`quality.py`) | `age_days > 180` cho đúng 1 dòng, trùng `stale_rows: 1` trong `data/fixtures/freshness_report.json` — xác nhận contract giữa 2 phần việc khớp nhau trước khi ai chạy pipeline thật. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Parse payload Crossref thành `PaperRecord` | `crossref.py::parse_crossref_payload` | 24 record, đã strip tag JATS khỏi abstract | So khớp từng trường với `data/raw/crossref_records.json`: khớp 10/11 trường × 24 record |
| Gọi API có retry và fallback offline | `crossref.py::fetch_source_records` | Ghi `data/raw/crossref_response.json` + `crossref_records.json` | 5 kịch bản mock `requests.get`, xem mục 4 |
| Đọc snapshot offline | `crossref.py::load_raw_records` | 24 `PaperRecord` | Lệnh tự kiểm thử số 1 trong Issue #2 |
| Chuẩn hóa thành DataFrame sẵn sàng embed | `cleaning.py::build_clean_dataframe` | DataFrame 24 dòng × 13 cột | So khớp toàn bộ 312 ô với `data/fixtures/papers_clean.json` |

Một output cụ thể phần việc của tôi tạo ra:

Cột `text_for_embedding` chính là chuỗi được nạp vào vector store. Trong `src/retrieval/index.py`, hàm `LocalEmbeddingIndex._build_documents()` gán `"content": row["text_for_embedding"]` — tức toàn bộ chất lượng retrieval của nhóm phụ thuộc trực tiếp vào định dạng 5 khối mà hàm của tôi dựng:

```
Title: {title}
Authors: {authors_joined}
Published: {published}
Categories: {categories_joined}
Summary: {summary}
```

Chạy luồng đầy đủ `crossref_response.json → parse_crossref_payload → build_clean_dataframe` cho kết quả trùng khít 312/312 ô với fixture chuẩn của nhóm, không lệch ô nào.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline cần một tầng ingestion **tái lập được** (reproducible) và **không phụ thuộc mạng**. Hai rủi ro cụ thể:

1. Crossref trả về dữ liệu bẩn: abstract bọc tag JATS XML, `date-parts` thiếu tháng/ngày, tên tác giả tách rời `given`/`family`, whitespace lộn xộn. Nếu nạp thẳng vào embedding thì rác đi vào vector.
2. Nếu bài lab phụ thuộc mạng, kết quả mỗi lần chạy sẽ khác nhau và không so sánh được giữa baseline / corrupted / repaired — phá vỡ mục tiêu chính của cả bài.

### Cách triển khai

**`parse_crossref_payload()`** — duyệt `payload["message"]["items"]`, ánh xạ `DOI → paper_id`, strip mọi tag XML bằng regex rồi gom whitespace, ghép `given + family` thành tên tác giả, lấy `subject[0]` làm `primary_category`, đổi `published.date-parts` `[2026, 5, 20]` thành `2026-05-20` và lấy `created.date-time` làm `updated`. Record thiếu `paper_id`, `title` hoặc `summary` bị loại ngay tại bước này.

Hàm `_format_date_parts()` pad phần thiếu về mặc định (`[2026] → 2026-01-01`). Snapshot offline hiện có đủ 3 thành phần ở cả 24 item nên nhánh này không kích hoạt, nhưng `fetch_source_records()` gọi API thật mà Crossref thường xuyên trả `date-parts` chỉ có năm — không pad thì `_to_date()` sẽ loại oan record hợp lệ.

**`fetch_source_records()`** — dựng params từ `settings.source_query`, `settings.source_filter`, `settings.max_results`, gọi `https://api.crossref.org/works` với timeout 30s. Retry tối đa 3 lần với backoff tăng dần cho các status tạm thời `{429, 500, 502, 503, 504}`. Thành công thì ghi cả raw response lẫn records đã parse. Lỗi mạng, hết retry, hoặc body không phải JSON hợp lệ đều rơi về đọc snapshot offline thay vì ném exception làm gãy pipeline.

Tôi mở rộng tập retry sang cả `500/502/504` chứ không chỉ `429/503` như gợi ý ban đầu, vì đây đều là lỗi tạm thời phía server, retry được, và chi phí sai sót của việc retry thừa thấp hơn nhiều so với việc rơi về snapshot cũ khi API thực ra vẫn sống.

**`build_clean_dataframe()`** — với mỗi record: chuẩn hóa text, parse ngày, loại dòng thiếu `paper_id`/`title`/`summary` hoặc ngày không đọc được; tính `age_days = (run_date.date() - published).days`; ghép `authors_joined`, `categories_joined`; đếm `summary_chars`; dựng `text_for_embedding`. Sau đó `drop_duplicates(subset="paper_id", keep="first")` và sort `published` giảm dần, tie-break bằng `paper_id` tăng dần.

Tie-break là chủ ý: pandas mặc định dùng quicksort **không ổn định**, nên nếu chỉ sort theo `published` thì hai bài cùng ngày có thể đảo chỗ giữa các lần chạy. Bộ dữ liệu có đúng 2 cặp trùng ngày (`2026-06-12` và `2026-06-08`), đủ để gây nhiễu khi so sánh artifact giữa 3 trạng thái. Thêm khóa phụ làm thứ tự output xác định hoàn toàn.

Tôi giữ `published`/`updated` ở dạng chuỗi `YYYY-MM-DD` thay vì `datetime64`, vì khi xuất JSON pandas sẽ đổi `datetime64` thành epoch milliseconds, không còn khớp fixture. Dạng `YYYY-MM-DD` cũng sort theo từ điển trùng với sort theo thời gian nên không mất gì.

Trong lúc làm tôi có viết 2 helper chuẩn hóa text riêng, sau đó phát hiện `src/core/utils.py` đã có sẵn `normalize_whitespace()` và `compact_join()` làm đúng việc đó, nên đã xóa bản của mình và import lại từ `core.utils` — cùng lý do với việc dùng `write_json()` thay vì tự ghi file.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Crossref REST API (`query`, `filter`, `rows`), hoặc snapshot `data/raw/crossref_response.json` / `crossref_records.json` |
| Output | `list[PaperRecord]` (11 trường) và `pd.DataFrame` 13 cột: `paper_id, title, summary, authors_joined, categories_joined, primary_category, published, updated, abs_url, pdf_url, age_days, summary_chars, text_for_embedding` |
| Module phụ thuộc | `core.config.Settings` (query, paths), `core.utils` (`normalize_whitespace`, `compact_join`, `write_json`) |
| Module sử dụng output | `pipelines/phase1.py`, `retrieval/index.py` (`text_for_embedding`), `ingestion/corruption.py`, `observability/quality.py` (GX + freshness) |
| Điều kiện lỗi cần xử lý | Mất mạng / DNS lỗi; HTTP 429 rate limit; 5xx tạm thời; body không phải JSON; record thiếu trường bắt buộc; `date-parts` thiếu tháng/ngày; `paper_id` trùng; whitespace và tag XML trong text |

### Cách xác minh

```bash
# Lệnh tự kiểm thử số 1 trong Issue #2
python -c "from core.config import load_settings; from ingestion.crossref import load_raw_records; s=load_settings(); r=load_raw_records(s.paths.raw_records_json); print('records:', len(r))"

# Lệnh tự kiểm thử số 2 trong Issue #2
python -c "from datetime import datetime, timezone; import pandas as pd; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); fx=pd.read_json('data/fixtures/papers_clean.json'); print('rows:', len(df), '| thieu cot:', set(fx.columns)-set(df.columns) or 'khong')"
```

- **Kết quả mong đợi:** `records: 24`; `rows: 24 | thieu cot: khong`.
- **Kết quả thực tế:** đúng như trên.

Ngoài 2 lệnh bắt buộc, tôi tự kiểm thêm 4 nhóm:

| Kiểm tra | Cách làm | Kết quả |
| --- | --- | --- |
| Parse đúng | So từng trường 24 record với `data/raw/crossref_records.json` | Khớp 10/11 trường; `pdf_url` lệch có chủ đích (mục 5) |
| Clean đúng | So từng ô DataFrame với `data/fixtures/papers_clean.json` | 312/312 ô khớp, kể cả thứ tự sort |
| Luồng E2E | `crossref_response.json → parse → clean` rồi so fixture | Khớp tuyệt đối 100%, **kể cả `pdf_url`** |
| Nhánh lỗi & edge case | 10 record bịa: trùng `paper_id`, thiếu id, title rỗng, summary rỗng, ngày hỏng, whitespace thừa, `updated` rỗng, input rỗng | 10 vào → 5 ra đúng kỳ vọng; dedupe giữ bản đầu tiên; input rỗng trả DataFrame 0 dòng vẫn đủ 13 cột |
| `fetch_source_records` | Mock `requests.get`: lỗi mạng, 2×503 rồi 200, 429 liên tục, body không phải JSON, ghi file | 5/5 kịch bản đúng; snapshot đang được git track không bị ghi đè trong lúc test |

- **Artifact/log:** `data/raw/crossref_response.json`, `data/raw/crossref_records.json`. Các artifact sinh ra (`data/clean/`, `data/chroma/`) không commit theo quy ước nhóm. Báo cáo không chứa secret; `fetch_source_records()` không dùng API key nào.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Trường `pdf_url` mâu thuẫn giữa hai nguồn được coi là chuẩn. `data/raw/crossref_records.json` có `pdf_url` = URL DOI ở cả 24 record, còn `data/fixtures/papers_clean.json` — fixture contract do nhóm trưởng ban hành — để rỗng ở cả 24 dòng. Crossref trên thực tế **không trả về link PDF**, item chỉ có trường `URL` trỏ tới trang DOI.

- **Các phương án đã cân nhắc:**
  1. Pass-through nguyên vẹn: `parse` lấy `pdf_url = item["URL"]` cho khớp snapshot. Nhất quán với `crossref_records.json` nhưng lệch fixture, mà fixture mới là contract chính thức.
  2. Ép `pdf_url = ""` ngay trong `build_clean_dataframe()`. Khớp fixture tuyệt đối với mọi input, nhưng là logic xóa dữ liệu vô cớ, rất khó biện minh khi review.
  3. `parse` đặt `pdf_url = ""` vì Crossref không có link PDF; `cleaning` chỉ pass-through giá trị nhận được.

- **Phương án đã chọn:** phương án 3.

- **Lý do:** Mỗi hàm giữ đúng một trách nhiệm. `parse_crossref_payload()` phản ánh trung thực những gì API thật sự cung cấp — và API không cung cấp PDF link. `build_clean_dataframe()` là tầng chuẩn hóa, không phải tầng bịa hay xóa dữ liệu; nếu nó âm thầm ép một cột về rỗng thì bất kỳ ai đọc code sau này cũng không hiểu vì sao. Phương án 2 tuy cho điểm khớp fixture cao nhất nhưng đánh đổi bằng một dòng logic không giải thích được.

- **Bằng chứng quyết định phù hợp:** Chạy luồng đầy đủ từ payload gốc `crossref_response.json` qua `parse_crossref_payload()` rồi `build_clean_dataframe()`, kết quả khớp `papers_clean.json` **312/312 ô, bao gồm cả `pdf_url`**. Điều này chứng minh fixture của nhóm được sinh ra chính từ luồng parse API, và `crossref_records.json` mới là snapshot cũ còn sót giá trị `pdf_url` lỗi thời. Khác biệt duy nhất chỉ xuất hiện khi khởi động từ snapshot cũ đó — đúng bản chất vấn đề, không phải lỗi hàm của tôi. Tôi đã báo lại để nhóm trưởng cân nhắc regenerate snapshot.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** Lệnh tự kiểm thử số 2 trong Issue #2 không chạy được:

  ```
  FileNotFoundError: data/fixtures/papers_clean.json
  ```

- **Lệnh tái hiện:** chạy lệnh tự kiểm thử số 2 tại commit `77a0fda` trên `main`.

- **Nguyên nhân gốc:** Không phải lỗi code. Issue #1 quy định Member 1 phải push `data/fixtures/` lên `main` **trước tiên**, vì đó là điều kiện tiên quyết để 3 thành viên còn lại bắt đầu. Tại thời điểm tôi bắt đầu, thư mục đó chưa tồn tại — local `main` của tôi đang ở `77a0fda` trong khi `origin/main` đã có `e5697b0` chứa fixtures.

- **Cách xử lý:** `git fetch` rồi `git pull --ff-only origin main` để lấy commit `e5697b0 chore(team): add contract fixtures for parallel work`, sau đó mới tạo branch `feat/m2-ingestion` từ `main` đã cập nhật.

- **Cách xác minh sau khi sửa:** `ls data/fixtures/` liệt kê đủ 11 file; lệnh tự kiểm thử số 2 chạy ra `rows: 24 | thieu cot: khong`.

- **Điều học được:** Trong mô hình chia việc song song, thứ chặn tôi lại không phải code của ai mà là **artifact contract chưa có mặt**. Bài học cụ thể: kiểm tra `git fetch` và đối chiếu `origin/main` **trước khi** kết luận một lệnh trong issue bị sai — tôi suýt đi báo là lệnh tự kiểm thử viết nhầm đường dẫn, trong khi thực ra chỉ là local đang cũ.

## 7. Hiểu biết về luồng end-to-end

**1. Dữ liệu đi từ Crossref đến vector index như thế nào?**

`fetch_source_records()` gọi Crossref REST API (fallback snapshot nếu lỗi mạng) → `parse_crossref_payload()` đổi payload thô thành `list[PaperRecord]` → `build_clean_dataframe()` chuẩn hóa thành DataFrame 13 cột, trong đó `text_for_embedding` gộp 5 khối Title/Authors/Published/Categories/Summary. `LocalEmbeddingIndex._build_documents()` lấy đúng cột đó làm `content`, kèm `paper_id` làm định danh và các cột còn lại làm metadata. Chuỗi này được encode bằng `sentence-transformers/all-MiniLM-L6-v2` và ghi vào ChromaDB tại `data/chroma` dưới collection `papers-baseline`. Điểm mấu chốt: chất lượng vector phụ thuộc hoàn toàn vào chuỗi text tầng cleaning dựng ra — rác không bị lọc ở đây sẽ nằm vĩnh viễn trong vector space.

**2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**

`build_test_set()` sinh 10 câu hỏi từ chính DataFrame sạch, mỗi câu kèm `ground_truth` (câu trả lời đúng) và `ground_truth_doc_ids` — chính là `paper_id` của bài lẽ ra phải được truy xuất. `evaluate_pipeline()` chạy từng câu qua `answer_question()`, rồi tách đôi phép đo: `retrieval_hit` kiểm tra `any(doc_id in item["ground_truth_doc_ids"] for doc_id in result.retrieved_doc_ids)` — tức **tầng tìm kiếm** có lấy đúng tài liệu không; còn `token_f1` và LLM judge (`judge_accuracy`, `mean_judge_score`) đo **tầng sinh câu trả lời**. Tách như vậy mới biết khi điểm tụt thì lỗi nằm ở retrieval hay ở generation. Vì `ground_truth_doc_ids` dựa trên `paper_id`, việc `build_clean_dataframe()` đảm bảo `paper_id` duy nhất là điều kiện cần để phép đo này có nghĩa.

**3. Quality checks khác freshness monitoring ở điểm nào?**

Quality checks (Great Expectations) hỏi *"dữ liệu có đúng hình dạng không?"* — số dòng trong khoảng hợp lệ, `paper_id`/`title`/`text_for_embedding` không null, `paper_id` duy nhất, `summary` đủ dài. Đây là kiểm tra **tĩnh, tại một thời điểm**. Freshness monitoring hỏi *"dữ liệu có còn mới không?"* — dựa trên `age_days` so với `freshness_threshold_days = 180`, là kiểm tra **theo trục thời gian**. Một tập dữ liệu có thể pass toàn bộ expectation mà vẫn cũ mèm: đúng schema, không null, không trùng, nhưng toàn bài từ 2 năm trước. Ngược lại dữ liệu rất mới vẫn có thể hỏng schema. Hai tín hiệu bắt hai lớp lỗi khác nhau nên phải chạy cả hai.

**4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**

Vì đây là thí nghiệm có đối chứng, và biến độc lập cần cô lập là **tình trạng dữ liệu**. Nếu mỗi trạng thái dùng một test set khác thì khi `retrieval_hit_rate` tụt sẽ không phân biệt được là do dữ liệu bị hỏng hay do bộ câu hỏi mới khó hơn — hai nguyên nhân bị trộn lẫn, kết luận mất giá trị. Giữ nguyên test set, đặc biệt là `ground_truth_doc_ids` gắn cứng vào các `paper_id` cố định, thì mọi chênh lệch chỉ còn quy về một nguyên nhân duy nhất.

**5. Repair được xem là thành công dựa trên artifact và metric nào?**

Cần đồng thời cả hai lớp tín hiệu, đối chiếu ba trạng thái:

- **Lớp dữ liệu:** `repaired_quality_report.json` có `success: true` trở lại (các expectation từng fail khi corrupted nay pass), và `freshness_report.json` quay về `is_fresh: true`.
- **Lớp agent:** `repaired_metrics.json` có `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score` phục hồi về sát `baseline_metrics.json`.

Bảng đối chiếu cả ba trạng thái được xuất ra `data/reports/corruption_report.md`. Chỉ quality gate xanh trở lại là chưa đủ — nếu chất lượng dữ liệu pass mà metric agent vẫn thấp thì repair mới chỉ vá được phần hình thức, chưa khôi phục được nội dung thật sự.

## 8. Phân tích kết quả

> **Cập nhật 2026-09-25 (sau khi PR #5, #7, #8 merge và nhóm chạy E2E thật):** phần dự đoán để trống bên dưới lúc nộp lần đầu nay đã có số liệu thật từ `python script/run_phase1.py` và `python script/run_corruption_flow.py` chạy trên `main`. Giữ nguyên phần dự đoán gốc ở "Kết luận từ số liệu" và đối chiếu ngay sau đó — đúng theo cam kết ở mục 10 là không sửa số liệu để làm đẹp báo cáo.

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.00 | 0.60 | 1.00 | Đúng dạng Silent Failure: dữ liệu lỗi không làm agent báo lỗi, chỉ âm thầm trả lời sai/thiếu |
| `mean_token_f1` | 1.00 | 0.822 | 1.00 | Giảm ít hơn hit_rate — nhiều câu vẫn trúng một phần dù tài liệu bị nhiễu |
| `judge_accuracy` | 1.00 | 0.90 | 1.00 | LLM judge khoan dung hơn token F1 |
| `mean_judge_score` | 5 | 4 | 5 | Nhất quán với judge_accuracy |
| Quality checks (`gx_success`) | True | False | True | Fail đúng `unique(paper_id)` và `summary length` — 2 kịch bản duplicate + blank/truncate summary |
| Freshness status (`is_fresh`) | True (4.2% stale) | True (23.8% stale) | True (4.2% stale) | Tăng mạnh nhưng chưa vượt ngưỡng 25% trong lần chạy này |

### Những gì đã kiểm chứng được ở tầng dữ liệu

Chưa chạy được agent không có nghĩa là chưa đo được gì. Các số dưới đây lấy trực tiếp từ DataFrame do `build_clean_dataframe()` sinh ra, chạy ngày 2026-09-25:

| Chỉ số tầng dữ liệu | Giá trị | Ý nghĩa |
| --- | ---: | --- |
| Số dòng sau clean | 24 | Khớp `total_records` trong `data/fixtures/baseline_quality_report.json` |
| `paper_id` duy nhất | Có | Thỏa `ExpectColumnValuesToBeUnique("paper_id")` của Member 4 |
| `summary_chars` nhỏ nhất | 193 | Vượt xa ngưỡng `min_value=30` của expectation về độ dài `summary` |
| `age_days` nhỏ nhất / lớn nhất | 65 / 181 | Khoảng tuổi dữ liệu |
| Số dòng `age_days > 180` | 1 | **Trùng khớp `stale_rows: 1`** trong `data/fixtures/freshness_report.json` |

Dòng cuối là kết quả tôi thấy đáng giá nhất: cột `age_days` do hàm của tôi tính tái lập **độc lập** đúng con số `stale_rows` mà Member 4 ghi trong fixture freshness, dù hai phần việc làm song song trên hai branch khác nhau và chưa hề tích hợp. Điều này cho thấy contract giữa tầng cleaning và tầng observability đã đúng trước cả khi pipeline chạy lần đầu.

### Kết luận từ số liệu

Hai chuỗi nhân quả dưới đây là **giả thuyết dựa trên contract dữ liệu**, chưa phải kết quả đo. Tôi ghi ra để đối chiếu với thực tế khi có số:

1. [Corruption kịch bản xóa trắng `summary` và cắt `title` < 8 ký tự] → [`ExpectColumnValueLengthsToBeBetween("summary", min_value=30)` fail, `summary_chars` sụt mạnh] → [`text_for_embedding` mất phần lớn nội dung ngữ nghĩa → vector kém phân biệt → `retrieval_hit_rate` giảm].
2. [Repair bằng cách ingest lại từ raw snapshot] → [quality checks pass trở lại, freshness về trong ngưỡng SLA] → [metric agent phục hồi về sát baseline].

Dự đoán của tôi: trong 6 kịch bản corruption, **xóa trắng `summary`** sẽ gây thiệt hại nặng nhất. Lý do nằm ở chính cấu trúc `text_for_embedding` mà tôi dựng: `summary` là khối dài nhất trong 5 khối, chiếm phần lớn nội dung ngữ nghĩa được embed. Mất nó thì document chỉ còn tiêu đề và metadata, vector gần như không còn thông tin để phân biệt. Ngược lại, kịch bản lùi `published` 365 ngày sẽ đánh mạnh vào freshness SLA nhưng gần như **không** ảnh hưởng retrieval, vì `published` chỉ là một dòng ngắn trong chuỗi embed. Nếu số liệu thực tế bác bỏ dự đoán này, tôi sẽ ghi lại nguyên nhân khi cập nhật mục 8.

> **Đối chiếu với số liệu thật:** dự đoán trên **bị bác bỏ một phần**. `retrieval_hit_rate` giảm mạnh nhất (100% → 60%) chủ yếu do kịch bản **drop_latest_records** (4/24 bản ghi bị loại hẳn khỏi index), chứ không phải do blank/noise summary như tôi dự đoán. Lý do tôi bỏ sót: mất tài liệu khỏi index (drop) khiến agent **hoàn toàn không có gì để truy xuất** cho câu hỏi liên quan — một dạng lỗi nặng hơn hẳn so với "tài liệu vẫn ở trong index nhưng nội dung bị nhiễu" (blank/noise summary), vì với dạng sau agent đôi khi vẫn suy luận đúng một phần nhờ tiêu đề/metadata còn nguyên. Phần dự đoán về `published` (ảnh hưởng freshness nhưng không ảnh hưởng retrieval) thì **đúng**: `is_fresh` vẫn `True` do stale ratio 23.8% chưa vượt ngưỡng 25%, đúng như tôi dự đoán dựa trên cấu trúc `text_for_embedding`.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** Tầng ingestion phải xác định (deterministic) thì mọi so sánh phía sau mới có nghĩa. Bài học cụ thể nhất là vụ sort: pandas mặc định dùng quicksort không ổn định, hai bài trùng ngày có thể đảo chỗ giữa các lần chạy, và chênh lệch vô hại đó sẽ lan xuống tận artifact so sánh 3 trạng thái. Một khóa sort phụ là đủ để chặn cả lớp lỗi khó truy vết này. Fallback offline cũng phục vụ cùng mục đích: tái lập được, không phụ thuộc mạng.

2. **Về data quality/observability:** Quality và freshness bắt hai lớp lỗi hoàn toàn khác nhau, không thay thế nhau được. Dữ liệu pass sạch mọi expectation vẫn có thể đã cũ tới mức vô dụng. Tôi cũng nhận ra tầng cleaning chính là nơi **sinh ra tín hiệu quan sát**, không chỉ là nơi làm sạch: `age_days` và `summary_chars` tôi tính ra chính là đầu vào cho quality gate và freshness SLA của Member 4.

3. **Về ảnh hưởng của data đến RAG agent:** Quyết định định dạng `text_for_embedding` của tầng cleaning quyết định trực tiếp chất lượng retrieval, vì `index.py` embed đúng chuỗi đó chứ không phải cột nào khác. Đây là chỗ mà "lỗi dữ liệu" biến thành "lỗi mô hình" một cách âm thầm — agent không báo lỗi, không crash, chỉ đơn giản trả lời kém đi. Đúng dạng silent failure mà cả bài lab này muốn phơi bày.

### Nếu có thêm thời gian

Tôi sẽ viết một bộ test tự động cho `build_clean_dataframe()` bằng pytest (repo đã khai báo `pytest` trong `[project.optional-dependencies].dev` nhưng chưa có thư mục test nào). Hiện tôi kiểm thử bằng script chạy tay, kết quả đúng nhưng không ai chạy lại được sau khi tôi merge. Cụ thể: parametrize 10 edge case đã dùng (trùng `paper_id`, thiếu trường, ngày hỏng, whitespace thừa, input rỗng) thành các case pytest, cộng một test so khớp toàn bộ 312 ô với fixture. Cách đo cải thiện: thêm một dòng corruption vào input mẫu và xác nhận test fail đúng chỗ — chứng minh bộ test thật sự bắt được lỗi chứ không chỉ chạy xanh.

Việc này có giá trị vượt ra ngoài phần của tôi: Member 3 sẽ tiêm 6 kịch bản lỗi lên chính DataFrame này, và một bộ test hồi quy ở tầng cleaning sẽ giúp phân biệt ngay "corruption do Member 3 cố ý tiêm" với "bug do tầng cleaning".

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu. Phần chưa có số liệu được đánh dấu rõ ở mục 8 thay vì suy đoán.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng. Mục 8 để trống vì pipeline E2E còn phụ thuộc module của Issue #1, #3, #4.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đỗ Thái Sơn
**Ngày xác nhận:** 2026-09-25
