# KẾ HOẠCH CẬP NHẬT MODULE A.2: NHIỄU ĐIỂM SỐ IVFPQ
*(Theo Quy chuẩn Phản biện Mentor R2 — lập ngày 2026-10-15)*

**Phạm vi:** `module_a2/`; tham khảo cách tổ chức Step 0–5 của `../module_a1_revision/PLAN.md`.  
**Trạng thái tổng thể:** Đã rà soát mã và JSON cũ; chưa triển khai hoặc chạy pipeline A.2 R2. Các tên script/output dưới đây là thiết kế dự kiến.  
**Nguồn:** `../../mentor_feedback.md` (mục 3.3), `../P0_AUDIT_CHECKLIST.md` (P0.10–P0.11), skill `mentor-audit-protocol`.

**Cập nhật nguồn nhận xét:** `../../R2_Fixing_Plan.md` hiện chứa phản biện A.2 đầy đủ tại Mục 4.1 và yêu cầu P2a tại Mục 7. Dùng tài liệu này làm nguồn chính. P0 đã sửa báo cáo legacy; phép chạy lại P1 nằm trong `../p1_reference/`, chưa thay thế pipeline nhiễu có dấu P2a. P2a chưa nằm trong đợt ưu tiên P0/P1/P2b hiện tại.

Các đường dẫn tương đối trong kế hoạch tính từ `module_a2/`, trừ khi nêu rõ vị trí khác.

---

## 0. TRẠNG THÁI HIỆN TẠI ĐÃ XÁC MINH

### Artifact đã có

| Nhóm | Artifact | Trạng thái |
|---|---|---|
| Mã thực nghiệm cũ | `../../../src/phase2/stage_a/measure_pq_perturbation.py` | Đã đọc; có đo random/top-10/top-100 và reconstruct IVFPQ |
| JSON cũ | `../../../data/results/phase2_stageA/json/module_a2_pq_perturbation.json` | Đã đọc; thiếu metadata header |
| JSON lưu trữ | `../../../data/results/phase2_stageA/Report_3_October/json/module_a2_pq_perturbation.json` | Các thống kê trong bảng dưới khớp JSON cũ |
| Báo cáo cũ | `../../reports/stage_A/module_a2_pq_perturbation_report.md` | Còn kết luận phóng đại và công thức epsilon không nhất quán |
| Cấu hình chung | `../../../configs/reference.yaml` | Có IVFPQ reference, khác cấu hình script cũ |
| Pipeline A.2 R2 | `scripts/`, `data/`, `results/`, `plots/` | Chưa có trong `module_a2/` lúc rà soát |

### Số liệu nền đối chiếu trực tiếp từ JSON cũ

| Model | m | Dự báo RMS cũ | RMS random | RMS top-10 | Mean gap 10/11 | Retention@10 (%) |
|---|---:|---:|---:|---:|---:|---:|
| SEARLE | 8 | 0.020321 | 0.017543 | 0.050729 | 0.000976551 | 13.8636 |
| SEARLE | 16 | 0.018932 | 0.016038 | 0.044928 | 0.000976551 | 20.3636 |
| Pic2Word | 8 | 0.017855 | 0.022305 | 0.071288 | 0.001003315 | 11.3182 |
| Pic2Word | 16 | 0.017074 | 0.020707 | 0.065726 | 0.001003315 | 16.3636 |

Nguồn trường: `theoretical_prediction.pred_rms`, `stats_random.rms`, `stats_top10.rms`, `score_gap.mean`, `retention_at_10` theo từng model/m. Đây là kết quả cũ, không phải kết quả R2. `retention_at_10` trong JSON cũ có đơn vị phần trăm.

### Sai lệch cần xử lý

1. **P0.10:** Random và top-10 có phân phối khác nhau; không gọi RMS là “khớp hoàn hảo” lý thuyết hoặc ép tỉ số về 15–19 lần.
2. **P0.11:** Phải chỉ rõ delta là RMS/MAE/phân vị, thuộc random hay top-10; epsilon được tính từ đúng delta đó.
3. Script cũ dùng `mean(||e||)/sqrt(d)` làm dự báo RMS tổng hợp, dù đã lưu `rms(||e||)`. Cần phân biệt trung bình RMS có điều kiện với RMS của toàn bộ mẫu.
4. Script in `p95` dưới nhãn “95% CI”. Phân vị 95 của sai số không phải khoảng tin cậy 95% của một ước lượng.
5. Script cũ mặc định `nlist=351`, `nprobe=32`, `m=[8,16]`; cấu hình chung dùng `nlist=1024`, `default_nprobe=16`, `m_subquantizers=64`. Không gộp kết quả hai cấu hình thành một chuỗi so sánh.
6. JSON cũ chỉ lưu tối đa 2.000 giá trị đầu cho một số mảng, không có query ID đi kèm; không đủ để tái lập bootstrap theo query.
7. Các mô tả kết quả trong hàm sinh báo cáo cũ được viết cứng; cần thay bằng renderer đọc JSON.

---

## 1. MỤC TIÊU CỐT LÕI

1. Đo trực tiếp nhiễu có dấu `z(q,x) = q·(x_hat - x)` và độ lớn `delta(q,x) = |z(q,x)|`.
2. Tách ba quần thể random, exact top-10 và exact top-100; so sánh từng quần thể với giả định hình chiếu đẳng hướng.
3. Đo sai lệch, độ phân tán và khoảng tin cậy theo query; không coi mọi cặp cùng query là độc lập.
4. Phân biệt nhiễu PQ với mất ứng viên do IVF routing trước khi diễn giải retention.
5. Xác định nguồn delta, kiểm tra phép tính epsilon và giới hạn của kết luận bảo toàn thứ hạng.
6. Sinh lại báo cáo bảy phần từ JSON và tạo bằng chứng đóng P0.10–P0.11.

**Yêu cầu có sẵn từ mentor/protocol:** đo nhiễu trực tiếp, tách random/top-k, sửa diễn giải lý thuyết, truy xuất nguồn delta, chuẩn hóa metadata và báo cáo.

**Thiết kế bổ sung của kế hoạch:** lưu nhiễu có dấu, bootstrap theo query, kiểm tra đảo hạng 10/11 và đối chứng trên gallery tái tạo để hỗ trợ diễn giải cơ chế. Không triển khai training/Score-Gap Loss trong module này.

---

## 2. PIPELINE THEO TRẠNG THÁI

### Step 0 — Kiểm kê dữ liệu và khóa cấu hình

- **Script dự kiến:** `scripts/step0_audit_inputs.py`
- **Output:** `results/step0_input_audit.json`
- **Trạng thái:** TODO.

**Thiết kế:**

1. Kiểm tra gallery, query cache, dimensions, hữu hạn, norm và mapping ID cho cả SEARLE/Pic2Word.
2. Dùng query cache 1.020 queries từ `../module_a1_revision/data/circo_1020_queries_<model>.pkl` cho phân tích hình học chính, sau khi kiểm tra schema và ID. Không cần nhãn relevance; không tự fallback về cache cũ khi thiếu dữ liệu.
3. Ghi số query thực đọc, split và nguồn cache. Nếu chạy lại tập val cũ, tạo run riêng; không so trực tiếp kết quả 220 và 1.020 queries như cùng thí nghiệm.
4. Đọc `../../../configs/reference.yaml`. Khi triển khai, bổ sung section A.2 trong cấu hình chung cho các profile và tham số lấy mẫu/bootstrap; không thay mặc định của module khác.
5. Hai profile dự kiến: `reference` dùng cấu hình IVFPQ chung (`m=64`, `nlist=1024`, `nprobe=16`, `nbits=8`); `legacy_reproduction` dùng `m=[8,16]`, `nlist=351`, `nprobe=32`, `nbits=8` để đối chiếu mã cũ. Ghi rõ cấu hình legacy suy từ script, chưa được JSON cũ chứng thực bằng metadata.
6. Khóa seed, seed huấn luyện coarse/PQ, số threads, batch size và tập train; ghi versions FAISS/NumPy. Nếu lấy mẫu train, lưu ID/hash và cỡ mẫu, không để thư viện subsample mà thiếu ghi nhận.

**Checklist:**

- [ ] Xác minh input và sự tương ứng query ID giữa hai model
- [ ] Ghi cấu hình hiệu lực của từng run/profile
- [ ] Chốt quy tắc loại reference image và xử lý ties, áp dụng giống nhau cho exact và approximate search
- [ ] Kiểm tra tài nguyên trước khi dựng index và reconstruct theo batch

### Step 1 — Dựng IVFPQ và bảng nhiễu mức cặp

- **Script dự kiến:** `scripts/step1_build_perturbation_dataset.py`
- **Output:** `data/score_perturbation.parquet`, `data/query_metrics.parquet`, `results/step1_pq_measurements.json`
- **Trạng thái:** TODO.

**Quy trình:**

1. Normalize query/gallery đầu vào; dựng FlatIP để lấy exact top-100 và gap hạng 10/11.
2. Train/add IVFPQ theo từng profile; reconstruct vector theo ID gốc. Không normalize lại `x_hat`, vì việc đó thay đổi điểm số cần đo.
3. Đo random 100.000 cặp/run bằng RNG cố định; lưu ID cặp để dùng lại giữa các cấu hình PQ. Lưu riêng exact top-10 và top-100, ghi rõ top-10 là tập con của top-100.
4. Lưu cả score exact, score tái tạo và nhiễu có dấu; không chỉ lưu trị tuyệt đối hoặc cắt 2.000 dòng đầu.
5. Kiểm tra `q·x_hat` với điểm IVFPQ trả về trên các ID truy hồi được, trong dung sai số học đã khai báo. Nếu không khớp, dừng diễn giải nhiễu và kiểm tra metric/reconstruction trước.

**Schema cặp:**

| Cột | Mô tả |
|---|---|
| `run_id`, `profile`, `model`, `m` | Định danh cấu hình, tách các lần chạy |
| `query_id`, `neighbor_id`, `pair_id` | ID ổn định, giữ cả lần lấy mẫu lặp của random |
| `population`, `rank_exact` | random/top10/top100; rank có thể null ở random |
| `score_exact`, `score_reconstructed` | `q·x`, `q·x_hat` |
| `signed_error`, `absolute_error` | `z`, `|z|` |
| `reconstruction_norm` | `||x - x_hat||` |

`query_metrics.parquet` lưu gap 10/11, ID exact hạng 10/11, retention và số ứng viên hợp lệ theo query/run.

**Checklist:**

- [ ] Số dòng top-10 bằng `num_queries * 10` và top-100 bằng `num_queries * 100` cho từng run khi đủ ứng viên
- [ ] Không có ID `-1` bị dùng làm chỉ số; số ứng viên thiếu được ghi rõ
- [ ] Kiểm tra đồng nhất thức sai số và tính hữu hạn
- [ ] Không trộn các population chồng lấn khi tính thống kê gộp

### Step 2 — Phân phối nhiễu và clustered bootstrap CI

- **Script dự kiến:** `scripts/step2_descriptive_bootstrap.py`
- **Output:** `results/step2_noise_statistics.json`, `plots/fig1_noise_distributions.png`, `plots/fig2_noise_vs_prediction.png`
- **Trạng thái:** TODO.

**Thống kê bắt buộc cho từng model/profile/m/population:** signed mean (bias), signed standard deviation, MAE, RMS, median/p90/p95/p99/max của `|z|`, số query và số cặp.

**Phương pháp:**

- Bootstrap 1.000 lần theo cụm `query_id`, báo cáo percentile CI 95% cho bias, MAE, RMS và chênh lệch top-10 so với random. Giữ cùng query được lấy lại khi so sánh các cấu hình; nói rõ CI có điều kiện trên index đã train, chưa bao gồm biến thiên train PQ.
- Kiểm tra `RMS(z)^2 = Var(z) + Mean(z)^2` với phương sai tổng thể; không gọi RMS là độ lệch chuẩn khi bias khác 0.
- Dưới giả định hướng sai số đẳng hướng và query đơn vị, dự báo RMS tổng hợp bằng `sqrt(mean(||e||^2)/d)` trên đúng các cặp thuộc population đang xét. Tách dự báo gallery-uniform khỏi dự báo có trọng số theo tần suất xuất hiện của candidate.
- Giữ `mean(||e||)/sqrt(d)` dưới nhãn công thức cũ để audit. Với xấp xỉ Gaussian có điều kiện, MAE dự báo là `sqrt(2/pi) * mean(||e||)/sqrt(d)`; không mặc định bằng `sqrt(2/pi)` nhân RMS gộp khi norm thay đổi.
- Biểu đồ trình bày riêng random/top-10/top-100. Half-normal chỉ là đường tham chiếu dưới giả định, không mặc định là phân phối thật; khi norm thay đổi, nêu rõ đường cong đơn scale chỉ là xấp xỉ.

**Checklist:**

- [ ] `p95` và `ci95` có trường/nhãn khác nhau
- [ ] Báo cáo độ lệch tương đối thực đo so với dự báo cho cả hai model
- [ ] CI của tỷ lệ nằm trong `[0,1]`; CI của signed bias được phép âm
- [ ] Không suy góc giữa `q` và `e` chỉ từ góc giữa `q` và `x`

### Step 3 — Gap, đảo hạng và đối chứng routing

- **Script dự kiến:** `scripts/step3_ranking_diagnostics.py`
- **Output:** `results/step3_ranking_diagnostics.json`, `plots/fig3_ranking_diagnostics.png`
- **Trạng thái:** TODO; đây là thiết kế bổ sung để kiểm tra cơ chế.

**Đo theo query:**

1. `gap = s10 - s11`; `perturbed_gap = gap + z10 - z11`. Ghi tỷ lệ đảo hạng (`perturbed_gap < 0`) và tỷ lệ tie riêng. Chỉ cặp 10/11 không đại diện cho toàn bộ các khả năng mất top-10.
2. Tính các tỉ số noise/gap theo query, thống kê gap bằng 0 riêng, không thay bằng epsilon số học tùy ý. Phân biệt “tỉ số hai trung bình” với “trung bình các tỉ số”.
3. Dùng FlatIP trên toàn bộ gallery tái tạo `x_hat` làm đối chứng ranking chỉ có lượng tử hóa; so với IVFPQ thực tế dùng cùng vector tái tạo nhưng giới hạn candidate do routing. Tính overlap với top-10 exact gốc bằng cùng quy tắc lọc.
4. Báo cáo retention từng nhánh và paired bootstrap CI của chênh lệch. Không giả định chênh lệch luôn dương hay là phân rã cộng chính xác hai loại lỗi.

**Checklist:**

- [ ] Có nhiễu hạng 11 và quy tắc ties nhất quán
- [ ] Retention R2 lưu dạng fraction `[0,1]`, renderer mới chuyển sang `%`
- [ ] Không suy “retention chắc chắn sụp đổ” chỉ vì RMS/mean-gap lớn hơn 1
- [ ] Đối chứng dùng cùng index/codebook, không train lại giữa hai nhánh

### Step 4 — Audit delta và bảng margin epsilon

- **Script dự kiến:** `scripts/step4_margin_audit.py`
- **Output:** `results/step4_margin_audit.json`
- **Trạng thái:** TODO.

**Bảng bắt buộc:** `run_id`, `model`, `m`, `population`, `delta_statistic`, `delta_value`, `epsilon_value`, `source_json`, `source_key`, `interpretation`.

1. Tính `epsilon = 2 * delta` riêng cho từng nguồn thống kê; không ghép delta random với epsilon suy từ top-10.
2. Nếu `delta` là cận tuyệt đối cho sai số của cả hai ứng viên, `gap > 2*delta` là điều kiện đủ bảo toàn thứ tự cặp. Để bảo toàn tập top-10, cận phải áp dụng cho tất cả ứng viên liên quan, không chỉ mẫu top-10 đã đo.
3. Nếu delta là RMS/MAE/p95, epsilon chỉ là margin ứng viên cần kiểm chứng; p95 của một cạnh không tạo bảo đảm đồng thời 95% cho mọi cặp hoặc mọi top-10.
4. Không chọn margin tối ưu trên test queries. Nếu bước này được dùng cho huấn luyện sau này, cần tách calibration/validation/test trước khi chọn epsilon.

**Checklist:**

- [ ] Mọi epsilon kiểm tra tự động bằng `2*delta`
- [ ] Nguồn population/statistic/model/config đầy đủ
- [ ] Nhãn phân biệt cận bảo đảm và heuristic thực nghiệm
- [ ] Không khẳng định hiệu quả Score-Gap Loss khi chưa huấn luyện/đánh giá

### Step 5 — Render báo cáo và đóng audit

- **Script dự kiến:** `scripts/step5_render_report.py`
- **Output chính:** `../../reports/stage_A/module_a2_pq_perturbation_report.md`
- **Bằng chứng dự kiến:** `../p0_audit_checklist/p0_10_pq_distribution_evidence.md`, `../p0_audit_checklist/p0_11_delta_margin_evidence.md`
- **Trạng thái:** TODO.

**Điều kiện:** Step 0–4 đã có JSON hợp lệ và artifact tương ứng. Bảng legacy và R2 có nhãn dữ liệu/cấu hình riêng. Không dùng báo cáo cũ làm nguồn số liệu.

**Cấu trúc báo cáo bảy phần:**

1. Câu hỏi nghiên cứu.
2. Giả thuyết và dự đoán định lượng, khóa trước lần chạy R2; không gọi dự đoán rút từ kết quả cũ là độc lập với dữ liệu.
3. Thiết kế thực nghiệm, quần thể đo và giả định.
4. Kết quả, bảng JSON và biểu đồ.
5. Kết luận với nhãn `XÁC NHẬN`, `ỦNG HỘ MỘT PHẦN`, `CHƯA KẾT LUẬN` hoặc `BÁC BỎ` theo từng giả thuyết.
6. Hạn chế: tập query, phụ thuộc candidate, cấu hình PQ, train seed, giả định đẳng hướng, CI có điều kiện.
7. Các bước tiếp theo.

**Checklist:**

- [ ] Mọi con số, tỉ số, epsilon và diễn giải định lượng truy xuất được về JSON
- [ ] Không còn lời văn “khớp hoàn hảo”, “không thể chối cãi”, ép về 15–19 lần
- [ ] Copy plot sang `../../reports/stage_A/plots/` với tên `a2_*`; report dùng `./plots/a2_*.png`
- [ ] Kiểm tra đường dẫn ảnh từ vị trí report và đối chiếu bảng tự động
- [ ] Tạo evidence rồi mới đánh dấu P0.10–P0.11 DONE trong `../P0_AUDIT_CHECKLIST.md`

---

## 3. CẤU TRÚC ARTIFACT VÀ METADATA P1

```text
module_a2/
├── PLAN.md
├── scripts/
│   ├── step0_audit_inputs.py
│   ├── step1_build_perturbation_dataset.py
│   ├── step2_descriptive_bootstrap.py
│   ├── step3_ranking_diagnostics.py
│   ├── step4_margin_audit.py
│   └── step5_render_report.py
├── data/
│   ├── score_perturbation.parquet
│   └── query_metrics.parquet
├── results/
│   ├── step0_input_audit.json
│   ├── step1_pq_measurements.json
│   ├── step2_noise_statistics.json
│   ├── step3_ranking_diagnostics.json
│   └── step4_margin_audit.json
└── plots/
```

Mỗi JSON có `metadata` và `results`. Metadata gồm module, step, timestamp UTC, git commit và trạng thái dirty, random seed, hardware/threads, versions, config path/hash và input hashes. Với output đa model/config, dùng `metadata.runs[run_id]` chứa `dataset`, `query_split`, `gallery_size`, `num_queries`, `dim`, `index_config`, train sampling và normalization; `results` tham chiếu đúng run ID.

Lưu tham số bootstrap, số cặp random, chính sách ties/filtering, đơn vị retention và các dung sai kiểm tra. Ghi trạng thái lỗi/thiếu dữ liệu rõ ràng; không thay bằng số 0. Nếu báo cáo latency, áp dụng 1 warm-up và 7 lần đo theo cấu hình chung; thời gian build/train không được gọi là search latency.

---

## 4. THỨ TỰ TRIỂN KHAI VÀ LỆNH CHẠY DỰ KIẾN

**Các script chưa tồn tại; lệnh dưới chỉ dùng sau khi triển khai và hoàn tất cấu hình Step 0.**

```powershell
cd D:\KLTN\DATA_EVALUATION_PROTOCOL\cir_faiss_thesis\Phase_2_Q1_Journal\R2_Audit\module_a2
python scripts\step0_audit_inputs.py
python scripts\step1_build_perturbation_dataset.py
python scripts\step2_descriptive_bootstrap.py
python scripts\step3_ranking_diagnostics.py
python scripts\step4_margin_audit.py
python scripts\step5_render_report.py
```

Sau mỗi bước, kiểm tra schema, số dòng, metadata và các điều kiện nghiệm thu trước khi chạy bước kế tiếp. Chạy thử trên dữ liệu nhỏ để kiểm tra reconstruction/score/ID trước khi chạy đầy đủ. Không chạy lại script cũ để ghi đè báo cáo R2 vì hàm renderer cũ còn kết luận viết cứng.

---

## 5. P0 CẦN ĐÓNG VÀ TIÊU CHÍ HOÀN THÀNH

| Mã | Nội dung | Bằng chứng cần có | Trạng thái |
|---|---|---|---|
| P0.10 | Phân biệt random/top-10 và giới hạn dự báo đẳng hướng | Step 2 JSON, plot phân phối, evidence và báo cáo mới | TODO |
| P0.11 | Nguồn delta rõ ràng; epsilon nhất quán | Step 4 JSON, kiểm tra `epsilon=2*delta`, evidence và báo cáo mới | TODO |
| P0.13 — phần A.2 | Loại kết luận phóng đại khỏi A.2 | Báo cáo mới đọc từ JSON | TODO; không đóng P0.13 toàn dự án chỉ từ A.2 |

**Điều kiện hoàn thành:** pipeline chạy được từ input đã kiểm kê; bảng nhiễu và CI tái lập được; profile/dataset không bị trộn; mọi số liệu báo cáo truy xuất được; evidence và checklist khớp trạng thái thực. Chưa đánh dấu bất kỳ bước thực nghiệm R2 nào DONE trong lần lập kế hoạch này.
