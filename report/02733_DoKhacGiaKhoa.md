# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Đỗ Khắc Gia Khoa |
| MSSV | 02733 |
| Khóa/Lớp | K4 — K4-L3-DAY10 |
| Tên nhóm | 1nguoi1mang |
| Vai trò chính | Member 1 — Pipeline Lead & Integration Architect |
| Repository | https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline |
| Ngày hoàn thành | 2026-09-25 |

Issue phụ trách: [Issue #1](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/issues/1) · Branch: `feat/m1-pipelines` · PR: [#5](https://github.com/Dokhacgiakhoa/K4-L3-Day10-1nguoi1mang-DataPipeline/pull/5)

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Điều phối Baseline Pipeline | `src/pipelines/phase1.py` — `run_baseline_pipeline()`, `main()` | `Settings`; hàm của Member 2/3/4 (`fetch_source_records`, `build_clean_dataframe`, `LocalEmbeddingIndex`, `evaluate_pipeline`, `run_data_quality_checks`, `build_test_set`, `generate_phase1_report`) | `data/clean/*`, ChromaDB `papers-baseline`, `baseline_metrics.json`, `phase1_report.md` | Hoàn thành |
| Điều phối Corruption/Repair Flow | `src/pipelines/corruption_flow.py` — `main()`, `_index_and_evaluate()` | Baseline df/metrics; `corrupt_clean_dataframe`, `generate_corruption_report` | `papers_clean_corrupted/repaired.*`, ChromaDB `papers-corrupted`/`papers-repaired`, `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` | Hoàn thành |
| Quản lý cấu hình & đường dẫn | `src/core/config.py`, `src/core/utils.py` | Biến môi trường, cấu trúc thư mục `data/` | `Settings`, `Paths` dùng chung cho toàn bộ 4 thành viên | Hoàn thành (đã tồn tại sẵn từ starter repo, tôi rà soát và không cần sửa) |
| Contract dữ liệu mẫu cho làm song song | `data/fixtures/` | Schema mà 4 module cuối cùng phải sinh ra | 11 file JSON mẫu (clean, corrupted, metrics, quality report, freshness, test set) | Hoàn thành |
| Điều phối & merge PR | GitHub Issues #1–#4, PR #5–#8 | Code từ 3 thành viên còn lại | 4 PR review + merge vào `main`, đồng bộ lại lịch sử commit đúng tác giả | Hoàn thành |

Tôi là người duy nhất chạm vào tầng orchestration (`pipelines/`) và `core/` — không thành viên nào khác cần sửa 2 file này, nên không có xung đột file trong suốt quá trình làm song song.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Review PR #6 (Member 2), phát hiện bug tiềm ẩn "silent drop" khi Crossref thiếu `abstract`/`published.date-parts` | Sơn (`ingestion/crossref.py`) | Comment inline kèm bằng chứng cụ thể; không chặn merge vì chưa lộ ra với data mẫu, nhưng ghi rõ rủi ro khi chạy API thật |
| Review PR #7 (Member 3), phát hiện branch tách trước khi PR #5/#6/#8 merge gây conflict, và bug sai tên field khiến `reporting.py` luôn in `N/A`/`0.00` | Đạt (`corruption.py`, `reporting.py`) | Hướng dẫn rebase cụ thể; Đạt sửa và tôi verify lại bằng cách chạy `generate_corruption_report()` với data thật, số liệu đúng mới merge |
| Review PR #8 (Member 4) | Phong (`quality.py`, `testset.py`) | Chạy thử với `data/fixtures/papers_clean.json` (sạch) và `papers_clean_corrupted.json` (lỗi), xác nhận GX PASS/FAIL đúng chiều trước khi merge |
| Phát hiện và sửa lỗi gán sai tác giả commit trên GitHub | Đạt, Phong | 2 lần `gh pr merge --squash` gán nhầm tác giả thành tôi; dùng `git filter-branch --env-filter` sửa lại đúng 2 commit rồi force-push, xác minh lại bằng `git log --format="%an <%ae>"` |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Chạy trọn Phase 1 end-to-end | `script/run_phase1.py` | `baseline_metrics.json`, `phase1_report.md` | Chạy thật, exit code 0 |
| Chạy trọn Phase 2 end-to-end (self-healing) | `script/run_corruption_flow.py` | `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` | Chạy thật, exit code 0 |
| Tạo `data/fixtures/` làm điều kiện khởi động song song | `data/fixtures/*.json` | 3 thành viên còn lại bắt đầu ngay không cần chờ pipeline chạy được | Cả 3 người tự test độc lập bằng lệnh trong Issue, không ai báo blocker về thiếu dữ liệu đầu vào |
| Điều phối 4 PR, đảm bảo Contributors đúng | PR #5–#8 | Toàn bộ code merge vào `main`, `git log` xác nhận đúng 4 tác giả | `git log --format="%h AUTHOR=%an <%ae>"` |

Một output cụ thể phần việc của tôi tạo ra:

`src/pipelines/corruption_flow.py::main()` là nơi duy nhất trong repo gọi đủ cả 4 module của 4 thành viên trong cùng một luồng: `corrupt_clean_dataframe()` (Đạt) → `LocalEmbeddingIndex.build()` + `evaluate_pipeline()` (sẵn có, Member 3 theo phân công gốc) → `run_data_quality_checks()` (Phong) → `load_raw_records()` + `build_clean_dataframe()` (Sơn) để repair → `generate_corruption_report()` (Đạt). Đây chính là điểm tích hợp thật sự của cả nhóm; nếu bất kỳ contract nào giữa 4 người sai lệch, hàm này là nơi đầu tiên báo lỗi.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Bốn thành viên viết 4 module độc lập, mỗi người tự test bằng snippet riêng lẻ trong Issue của mình — điều đó chứng minh từng hàm *chạy được*, nhưng không chứng minh *ghép lại với nhau chạy đúng*. Cần một tầng orchestration:

1. Gọi đúng thứ tự phụ thuộc dữ liệu (ingest → clean → index → eval → quality → report).
2. Đảm bảo Phase 2 dùng lại đúng test set của Phase 1 (yêu cầu bắt buộc để so sánh 3 trạng thái có ý nghĩa).
3. Tự phục hồi được (idempotent) — chạy lại bao nhiêu lần từ raw snapshot cũng phải ra cùng kết quả.
4. Không sập toàn bộ pipeline khi một phần phụ (demo agent) gặp lỗi ngoài tầm kiểm soát (hết quota LLM).

### Cách triển khai

**`run_baseline_pipeline()`** — theo đúng 9 bước pseudocode gốc: ingest (ưu tiên đọc `raw_records_json` đã có sẵn, chỉ gọi `fetch_source_records()` khi thiếu hoặc `REFRESH_SOURCE=1`) → `build_clean_dataframe()` → ghi CSV/JSON → build index `papers-baseline` → tạo/tải test set → `evaluate_pipeline()` → `run_data_quality_checks()` + `build_freshness_report()` → `generate_phase1_report()` → demo agent trên 3 câu mẫu, bọc trong `try/except` để lỗi quota/mạng của LLM không làm gãy toàn bộ pipeline (chỉ log rồi bỏ qua). Hàm trả về một `dict` chứa toàn bộ artifact trung gian (`df`, `index`, `metrics_summary`...) để `corruption_flow.py` tái sử dụng trực tiếp thay vì đọc lại từ đĩa.

**`main()` của `corruption_flow.py`** — có cơ chế tự phục hồi bậc pipeline: nếu chưa có `clean_json`/`baseline_metrics` (tức Phase 1 chưa từng chạy), tự gọi `run_baseline_pipeline()` trước thay vì raise lỗi. Sau đó: `corrupt_clean_dataframe()` → build index + evaluate trên `papers-corrupted` → **idempotent repair** bằng cách gọi lại `load_raw_records()` + `build_clean_dataframe()` từ `data/raw/crossref_records.json` (file này không hề bị `corrupt_clean_dataframe()` đụng vào) → build index + evaluate trên `papers-repaired` → `generate_corruption_report()` với dữ liệu quality/freshness lấy trực tiếp từ kết quả `run_data_quality_checks()` của từng trạng thái (đảm bảo không lệch giữa số hiển thị và số thật).

Điểm quan trọng nhất về tính "idempotent": tôi **không** viết logic sửa lỗi thủ công (patch từng dòng bị corrupt). Repair = build lại từ đầu từ raw snapshot gốc. Vì vậy chạy `corruption_flow.py` bao nhiêu lần liên tiếp, kết quả repaired luôn giống hệt baseline — không tích lũy sai lệch qua các lần chạy.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `Settings` (từ `core.config.load_settings()`); toàn bộ hàm public của 4 thành viên còn lại theo đúng signature đã thống nhất trong Issue |
| Output | `data/clean/*.csv/json`, ChromaDB 3 collection, `data/eval/test_set.json`, `data/results/*_metrics.json`, `data/quality/*_quality_report.json`, `data/reports/*.md` |
| Module phụ thuộc | `ingestion.crossref`, `ingestion.cleaning`, `ingestion.corruption`, `retrieval.index`, `retrieval.agent`, `evaluation.metrics`, `evaluation.testset`, `observability.quality`, `observability.reporting` |
| Module sử dụng output | Không ai gọi `pipelines/*` — đây là tầng cao nhất, chỉ `script/run_phase1.py` và `script/run_corruption_flow.py` gọi vào |
| Điều kiện lỗi cần xử lý | LLM hết quota/timeout khi demo agent (bắt bằng `try/except`, không chặn pipeline); baseline artifact chưa tồn tại khi chạy thẳng `corruption_flow.py` (tự chạy `run_baseline_pipeline()` trước) |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** cả hai lệnh thoát với exit code 0, sinh đủ artifact liệt kê trong `report/README.md` mục 7.
- **Kết quả thực tế:** đúng như trên, chạy 2 lần trên 2 bộ code khác nhau (lần 1: code tôi tự viết trước khi 3 người kia merge, dùng để kiểm thử tầng orchestration độc lập; lần 2 — lần dùng để lấy số liệu trong báo cáo này — chạy lại từ đầu sau khi PR #5–#8 của cả 4 người đã merge vào `main`, không còn stub nào trong repo).
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`. Không chứa secret; log demo agent có in thông báo lỗi quota Gemini nhưng không chứa API key.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** 3 thành viên còn lại cần test module của mình mà không thể chờ nhau — Member 3 cần DataFrame sạch của Member 2 để test corruption, Member 4 cần cả 2 để test quality gate, nhưng nếu chờ đúng thứ tự thực thi thì mất tính song song hoàn toàn của việc chia task.
- **Các phương án đã cân nhắc:**
  1. Yêu cầu làm tuần tự đúng thứ tự phụ thuộc (Member 2 xong trước, rồi Member 3, rồi Member 4).
  2. Mỗi người tự tạo dữ liệu giả (mock) riêng để test, không thống nhất schema.
  3. Trưởng nhóm publish trước một bộ dữ liệu mẫu (`data/fixtures/`) đúng contract schema thật, mọi người dùng chung.
- **Phương án đã chọn:** phương án 3.
- **Lý do:** Phương án 1 phá vỡ mục tiêu làm song song, lãng phí 180 phút thời lượng bài lab. Phương án 2 tạo rủi ro contract lệch nhau giữa các module — ví dụ Member 4 tưởng cột tên `hit_rate` trong khi thực tế là `retrieval_hit_rate` (lỗi này thực sự đã xảy ra ở PR #7, xem mục 6). Phương án 3 vừa giữ được tính song song, vừa đảm bảo tất cả cùng test trên một schema thật — vì fixture được tôi sinh ra bằng cách chạy chính pipeline thật của mình trước khi push.
- **Bằng chứng quyết định phù hợp:** Sơn ghi rõ trong báo cáo cá nhân rằng cột `age_days` do `build_clean_dataframe()` của anh tính ra **trùng khớp độc lập** với `stale_rows: 1` trong fixture freshness của Phong — hai người chưa hề tích hợp code với nhau tại thời điểm đó. Đây là bằng chứng trực tiếp rằng contract qua fixture hoạt động đúng trước khi chạy pipeline thật lần đầu.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Sau khi squash-merge PR #7 và PR #8, `git log --format="%an <%ae>"` cho thấy 2 commit đó có tác giả là `Đỗ Khắc Gia Khoa <dokhacgiakhoa666@gmail.com>` thay vì Đạt/Phong, trong khi PR #6 (Sơn) squash-merge cùng cách lại giữ đúng tác giả gốc.
- **Lệnh hoặc bước tái hiện:** `gh pr merge <7|8> --squash --delete-branch` rồi kiểm tra `git log`.
- **Nguyên nhân gốc:** Hành vi gán tác giả của squash-merge qua GitHub API không nhất quán giữa các PR trong trường hợp này (không phải do số lượng commit — cả 3 PR đều 1–2 commit). Không xác định được nguyên nhân chính xác từ phía GitHub, chỉ xác nhận được hiện tượng qua so sánh trực tiếp.
- **Cách xử lý:** Dùng `git filter-branch --env-filter` giới hạn đúng 2 commit hash bị sai (đây là 2 commit mới nhất trên `main` tại thời điểm phát hiện, chưa ai branch từ đó), gán lại `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL` đúng theo commit từ PR gốc (lấy qua `gh api repos/.../pulls/<n>/commits`), sau đó `git push origin main --force-with-lease`.
- **Cách xác minh sau khi sửa:** `git log --format="%h AUTHOR=%an <%ae>" -4` cho ra đúng `Liber72` và `Nguyen Nguyen Phong`. Trước khi force-push, tôi đã hỏi ý kiến xác nhận vì đây là thao tác viết lại lịch sử trên nhánh chung.
- **Điều học được:** Trong bài lab này, điểm chuyên cần nhóm phụ thuộc trực tiếp vào GitHub Insights → Contributors — một thao tác merge tưởng như vô hại (`--squash`) có thể âm thầm xóa mất công sức của thành viên trên biểu đồ đóng góp mà không có cảnh báo nào. Cần kiểm tra `git log` ngay sau mỗi lần merge thay vì tin tưởng mặc định vào hành vi của công cụ.

## 7. Hiểu biết về luồng end-to-end

**1. Dữ liệu đi từ Crossref đến vector index như thế nào?**

`fetch_source_records()` (Sơn) gọi Crossref API hoặc fallback snapshot offline → `parse_crossref_payload()` chuẩn hóa thành `list[PaperRecord]` → `build_clean_dataframe()` (Sơn) chuyển thành DataFrame với cột `text_for_embedding` ghép 5 khối Title/Authors/Published/Categories/Summary → `LocalEmbeddingIndex.build()` encode bằng `all-MiniLM-L6-v2`, ghi vào ChromaDB. Tôi là người gọi đúng thứ tự này trong `phase1.py`, nhưng không sửa logic bên trong bất kỳ bước nào.

**2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**

`build_test_set()` (Phong) sinh 10 câu hỏi gắn `ground_truth_doc_ids` là `paper_id` thật. `evaluate_pipeline()` chạy từng câu qua `answer_question()`, tách `retrieval_hit` (đúng tài liệu có được tìm thấy không) khỏi `token_f1`/`judge_accuracy` (câu trả lời có đúng nội dung không) — hai tín hiệu độc lập giúp định vị lỗi nằm ở tầng retrieval hay tầng generation.

**3. Quality checks khác freshness monitoring ở điểm nào?**

Quality checks (GX 1.x, do Phong triển khai) kiểm tra *hình dạng* dữ liệu tại một thời điểm: đủ dòng, không null, không trùng `paper_id`, `summary` đủ dài. Freshness kiểm tra *tuổi* dữ liệu theo `age_days` so với ngưỡng 180 ngày. Trong lần chạy thật tôi vừa thực hiện, dữ liệu corrupted có `gx_success=False` (do trùng `paper_id` ở kịch bản duplicate và `summary` quá ngắn ở kịch bản blank/truncate) nhưng `is_fresh` vẫn `True` (stale_ratio 23.8% chưa vượt ngưỡng 25%) — minh chứng rõ ràng hai tín hiệu này độc lập với nhau, không thể suy ra cái này từ cái kia.

**4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**

Vì biến độc lập cần cô lập là tình trạng dữ liệu, không phải độ khó câu hỏi. `corruption_flow.py` tôi viết cố tình dùng lại đúng `settings.paths.eval_testset` cho cả 3 lần `evaluate_pipeline()`, không sinh test set mới — nếu không, một `retrieval_hit_rate` giảm có thể do câu hỏi mới khó hơn chứ không phải do dữ liệu bị hỏng, phá vỡ toàn bộ giá trị của phép so sánh.

**5. Repair được xem là thành công dựa trên artifact và metric nào?**

Dựa trên `data/reports/corruption_report.md` — nơi tôi tổng hợp cả 2 lớp tín hiệu: lớp dữ liệu (`repaired_quality_report.json` có `gx_success=True`, `freshness.is_fresh=True`) và lớp agent (`repaired_metrics.json` có `retrieval_hit_rate`, `mean_token_f1`... quay lại bằng `baseline_metrics.json`). Trong lần chạy thật: cả hai lớp đều phục hồi 100% — 24/24 dòng khớp baseline, mọi metric quay về đúng giá trị baseline.

## 8. Phân tích kết quả

Số liệu dưới đây lấy từ lần chạy thật cuối cùng (2026-09-25) sau khi PR #5–#8 của cả 4 thành viên đã merge vào `main`, dùng đúng code trên `main`, không phải code thử nghiệm cá nhân.

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.00 | 0.60 | 1.00 | Giảm 40 điểm phần trăm khi 6 kịch bản lỗi được tiêm, phục hồi tuyệt đối sau repair |
| `mean_token_f1` | 1.00 | 0.822 | 1.00 | Giảm ít hơn hit_rate — một số câu trả lời vẫn trúng một phần dù tài liệu bị hỏng |
| `judge_accuracy` | 1.00 | 0.90 | 1.00 | LLM judge khoan dung hơn token F1 với câu trả lời "gần đúng" |
| `mean_judge_score` | 5 | 4 | 5 | Nhất quán với judge_accuracy |
| Quality checks (`gx_success`) | True | **False** | True | Fail đúng 2 expectation: `paper_id` trùng (do duplicate rows) và `summary` quá ngắn |
| Freshness (`is_fresh`) | True (stale 4.2%) | True (stale 23.8%) | True (stale 4.2%) | Corrupted áp sát ngưỡng 25% nhưng chưa vượt — kịch bản lùi ngày 365 ngày chỉ áp dụng cho 4/21 dòng nên chưa đủ kéo tỷ lệ qua ngưỡng |

### Kết luận từ số liệu

1. **[Corruption: duplicate rows + blank/truncate summary]** → **[GX fail 2 expectation: `expect_column_values_to_be_unique(paper_id)` và `expect_column_value_lengths_to_be_between(summary)`]** → **[`text_for_embedding` của các dòng bị corrupt mất phần lớn nội dung ngữ nghĩa → `retrieval_hit_rate` rớt từ 100% xuống 60%]**.
2. **[Repair: build lại từ `data/raw/crossref_records.json`]** → **[GX pass trở lại 100%, freshness quay về stale 4.2%]** → **[Toàn bộ 4 metric agent phục hồi đúng 100% giá trị baseline, không sai lệch dù chỉ 1 điểm phần trăm]**.

Corruption có ảnh hưởng rõ nhất đến `retrieval_hit_rate` (giảm 40 điểm phần trăm) chứ không phải `judge_accuracy` (chỉ giảm 10 điểm). Điều này khớp với thiết kế `text_for_embedding`: khi `drop_latest_records` loại bỏ hẳn 4 dòng khỏi index, agent hoàn toàn **không có tài liệu để tìm** — đây là lỗi ở tầng retrieval, nặng hơn hẳn so với lỗi ở tầng nội dung (blank/noise summary), vì với những dòng còn tồn tại trong index nhưng nội dung bị nhiễu, agent đôi khi vẫn suy luận đúng một phần nhờ LLM judge khoan dung. Kết quả này khác với dự đoán của Sơn trong báo cáo cá nhân (dự đoán `blank_summary` sẽ gây thiệt hại nặng nhất) — số liệu thực tế cho thấy **mất hẳn tài liệu khỏi index** (`drop_latest_records`) mới là nguyên nhân chính kéo `retrieval_hit_rate` xuống, vì đây là dạng lỗi duy nhất trong 6 kịch bản khiến tài liệu **hoàn toàn biến mất** khỏi không gian vector, thay vì chỉ suy giảm chất lượng nội dung.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** Tầng orchestration không chỉ là "gọi hàm theo đúng thứ tự" — nó là nơi duy nhất phát hiện được lỗi tích hợp giữa các module mà test đơn lẻ của từng người không bao giờ bắt được (ví dụ bug sai tên field `hit_rate`/`retrieval_hit_rate` ở PR #7 chỉ lộ ra khi tôi chạy `generate_corruption_report()` với dữ liệu thật của toàn hệ thống).
2. **Về data quality/observability:** Freshness và GX quality là hai chốt độc lập thật sự, không phải lý thuyết suông — lần chạy này chứng minh cụ thể: corrupted data fail GX nhưng freshness vẫn pass, vì hai kịch bản lỗi khác nhau (duplicate/truncate vs. stale date) tác động vào hai chốt khác nhau với số lượng dòng khác nhau (chỉ 4/21 dòng bị lùi ngày, chưa đủ vượt ngưỡng 25%).
3. **Về ảnh hưởng của data đến RAG agent:** Không phải mọi corruption gây thiệt hại như nhau. Corruption làm **biến mất tài liệu khỏi index** (drop records) nguy hiểm hơn hẳn corruption làm **suy giảm nội dung tài liệu còn tồn tại** (blank/noise summary) — vì cái đầu là mất khả năng tìm kiếm, cái sau vẫn còn cơ hội được LLM suy luận bù đắp một phần.

### Nếu có thêm thời gian

Tôi sẽ thêm một bước kiểm tra "cross-check tự động" ngay trong `corruption_flow.py`: sau khi repair, tự động so sánh `len(repaired_df) == len(baseline_df)` và `set(repaired_df["paper_id"]) == set(baseline_df["paper_id"])`, raise cảnh báo rõ ràng nếu không khớp thay vì chỉ in ra console như hiện tại. Cách đo cải thiện: cố tình sửa raw snapshot để tạo lệch 1 dòng, xác nhận pipeline dừng lại với thông báo lỗi rõ ràng thay vì âm thầm sinh ra báo cáo "repair thành công" sai sự thật — đúng tinh thần chống Silent Failure của cả bài lab.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đỗ Khắc Gia Khoa
**Ngày xác nhận:** 2026-09-25
