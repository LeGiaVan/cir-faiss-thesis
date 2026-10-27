# KẾ HOẠCH CẬP NHẬT MODULE A.1: HUBNESS VÀ HNSWFLAT
*(Theo Quy chuẩn Phản biện Mentor R2 — cập nhật theo trạng thái hiện tại ngày 2026-10-14)*

**Nguồn:** `../../R2_Fixing_Plan.md`, `../P0_AUDIT_CHECKLIST.md`, `mentor-audit-protocol`  
**Phạm vi:** `module_a1_revision/`  
**Mốc lịch sử:** phần kiểm kê/số liệu dưới đây mô tả lần chạy ngày 14/10/2026. Đợt P0/P1/P2b mới dùng `scripts/run_reference_audit.py` với cấu hình chung, đo in-degree, năm cặp seed và paired CI. Trạng thái nghiệm thu mới xem `../README.md` và `../P0_P1_P2b_COMPLETION_REPORT.md` khi được sinh; không coi các số lịch sử dưới đây là kết quả reference mới.

---

## 0. TRẠNG THÁI HIỆN TẠI ĐÃ XÁC MINH

### Artifact đã có

| Nhóm | Artifact | Trạng thái |
|---|---|---|
| Query cache | `data/circo_1020_queries_searle.pkl` | Đã có |
| Query cache | `data/circo_1020_queries_pic2word.pkl` | Đã có |
| Neighbor dataset | `data/neighbor_level_data.parquet` | Đã có |
| Step 1 result | `results/step1_hnsw_indegree.json` | Đã có |
| Step 2 result | `results/step2_bootstrap_ci.json` | Đã có |
| Step 3 result | `results/step3_nested_logit.json` | Đã có |
| Step 4 result | `results/step4_centering.json` | Đã có |
| Plots | `plots/fig1_*.png`, `fig2_*.png`, `fig3_*.png` | Đã có |
| Final report | `../../reports/stage_A/module_a1_hubness_report.md` | Đã sinh từ pipeline R2 |

### Số liệu Step 1 đã xác minh từ file hiện có

| Mô hình | Queries | Gallery | Dim | Dòng neighbor-level | Retention@10 | Miss rate | Anti-hub gallery ratio | k-occurrence skewness | In-degree=0 ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SEARLE | 1,020 | 123,403 | 512 | 10,200 | 0.9698 | 0.0302 | 0.9325 | 6.7992 | 0.000008 |
| Pic2Word | 1,020 | 123,403 | 768 | 10,200 | 0.9059 | 0.0941 | 0.9346 | 8.3298 | 0.000162 |

**Tổng số dòng thực tế:** 20,400 = 1,020 queries x 10 neighbors x 2 models.  
Kế hoạch cũ ghi 220 queries / 4,400 dòng là không còn đúng với trạng thái hiện tại.

### Lưu ý P1 metadata

`results/step1_hnsw_indegree.json` đã có `metadata` gồm `module`, `step`, `timestamp`, `git_commit`, `random_seed`, `hardware`, `dataset`, và `index_config`. Tuy nhiên `gallery_size`, `num_queries`, và `dim` đang nằm trong `results.<model>` thay vì nằm trực tiếp trong `metadata`. Trước khi chốt báo cáo, cần quyết định một trong hai hướng:

1. Chấp nhận schema hiện tại và để `step5_render_report.py` đọc số liệu theo từng model từ `results`.
2. Chuẩn hóa lại Step 1 JSON để đưa các trường P1 bắt buộc vào metadata theo schema thống nhất.

---

## 1. MỤC TIÊU CỐT LÕI

1. Chuyển đơn vị phân tích từ query-level sang neighbor-level.
2. Đo trực tiếp in-degree trên cấu trúc đồ thị HNSW layer 0 của FAISS, tránh nhầm `N10=0` của FlatIP với việc "không có cạnh HNSW".
3. Ước lượng miss-rate theo nhóm k-occurrence bằng clustered bootstrap theo `query_id`.
4. Chạy nested logistic regression để tách vai trò của hubness/graph features và query features.
5. Kiểm tra can thiệp centering như một phân tích cơ chế, nhưng phải diễn giải thận trọng vì script hiện có dùng re-normalization cho nhánh after.
6. Sinh lại báo cáo A.1 từ JSON, không gõ tay số liệu, và dùng nhãn kết luận chuẩn mực.

---

## 2. PIPELINE THEO TRẠNG THÁI

### Step 0 — Build query cache 1,020 queries

- **Script:** `scripts/step0_build_circo_1020_queries.py`
- **Output đã có:**
  - `data/circo_1020_queries_searle.pkl`
  - `data/circo_1020_queries_pic2word.pkl`
- **Trạng thái:** DONE — 2026-10-14

**Checklist:**
- [x] Query cache SEARLE tồn tại
- [x] Query cache Pic2Word tồn tại
- [x] Step 1 đã sử dụng query cache 1,020 queries thay vì fallback 220 val queries

---

### Step 1 — Build neighbor-level dataset và HNSW in-degree

- **Script:** `scripts/step1_build_neighbor_dataset.py`
- **Output đã có:**
  - `data/neighbor_level_data.parquet`
  - `results/step1_hnsw_indegree.json`
- **Trạng thái:** DONE — 2026-10-14

**Schema output đã xác minh:**

| Cột | Mô tả |
|---|---|
| `model` | `searle` hoặc `pic2word` |
| `query_id` | ID truy vấn |
| `neighbor_id` | ID neighbor trong top-10 FlatIP |
| `rank` | Thứ hạng neighbor, 1..10 |
| `missed` | 1 nếu HNSW bỏ sót neighbor FlatIP, 0 nếu tìm thấy |
| `k_occurrence` | N10(x) theo top-10 FlatIP trên tập query |
| `in_degree_hnsw` | In-degree layer 0 của node x trong HNSW |
| `s1` | Cosine similarity top-1 của query |
| `c_contrast` | Tương phản cục bộ `s1(q) - s100(q)` |

**Checklist:**
- [x] Script đã chạy và sinh output
- [x] `neighbor_level_data.parquet` có đúng 20,400 dòng
- [x] Mỗi model có 10,200 dòng
- [x] `results/step1_hnsw_indegree.json` có metadata cơ bản theo P1
- [ ] Chuẩn hóa lại metadata Step 1 nếu muốn `gallery_size`, `num_queries`, `dim` nằm trong `metadata`

---

### Step 2 — Descriptive analysis và clustered bootstrap CI

- **Script:** `scripts/step2_descriptive_bootstrap.py`
- **Output cần sinh:**
  - `results/step2_bootstrap_ci.json`
  - `plots/fig1_miss_rate_by_k_group.png`
- **Trạng thái:** DONE — 2026-10-14.

**Nhóm N10(x):**

| Nhóm | Điều kiện |
|---|---|
| Anti-hub | `N10 = 0` |
| Low | `1 <= N10 <= 4` |
| Mid | `5 <= N10 <= 9` |
| High | `10 <= N10 <= 29` |
| Hub | `N10 >= 30` |

**Yêu cầu bắt buộc:**
- Bootstrap 95% CI với 1,000 lần lấy mẫu theo cụm `query_id`.
- Không dùng `±1 std` cho thanh sai số.
- CI trên biểu đồ không vượt quá `[0%, 100%]`.
- JSON phải có `miss_rate`, `ci_lower`, `ci_upper`, `n_observations` cho từng nhóm x model.

**Checklist:**
- [x] Chạy script thành công
- [x] Sinh `step2_bootstrap_ci.json`
- [x] Sinh `fig1_miss_rate_by_k_group.png`
- [x] Đối chiếu JSON trước khi diễn giải P0.3

---

### Step 3 — Nested logistic regression

- **Script:** `scripts/step3_nested_logistic.py`
- **Output cần sinh:**
  - `results/step3_nested_logit.json`
  - `plots/fig2_logit_coef_path.png`
- **Trạng thái:** DONE — 2026-10-14.

**Ba mô hình:**

| Mô hình | Công thức |
|---|---|
| M0 | `missed ~ is_pic2word` |
| M1 | `missed ~ is_pic2word + rank + log_n10 + log_indeg` |
| M2 | `missed ~ is_pic2word + rank + log_n10 + log_indeg + s1 + c_contrast` |

**Quy tắc diễn giải:**
- Nếu `β_model` giảm mạnh từ M0 sang M1, hubness/graph features có thể giải thích một phần khoảng cách model.
- Nếu `β_model` chỉ giảm sau khi thêm M2, đặc tính query có vai trò lớn hơn hubness.
- Nếu `β_model` ổn định, không được kết luận hubness là cơ chế chính.

**Checklist:**
- [x] Chạy script thành công
- [x] Báo cáo `coef`, `std_err`, `p_value`, `95% CI` cho từng biến
- [x] Dùng QIC như metric chẩn đoán khi pseudo-R² không phù hợp với GEE
- [x] Kiểm tra `beta_model_path` trước khi viết kết luận

---

### Step 4 — Centering intervention

- **Script:** `scripts/step4_centering_intervention.py`
- **Output cần sinh:**
  - `results/step4_centering.json`
  - `plots/fig3_centering_before_after.png`
- **Trạng thái:** DONE — 2026-10-14.

**Thiết kế hiện tại trong script:**

1. Normalize gallery/query ban đầu.
2. Tính `mu = mean(gallery)`.
3. Tạo nhánh kiểm tra rank invariance bằng `gallery_raw - mu` không re-normalize.
4. Tạo nhánh after chính bằng `gallery_raw - mu` và không re-normalize để giữ đúng giả định rank-preserving.
5. Dựng lại HNSWFlat với `M=32`, `efSearch=128`, `efConstruction=200`.

**Lưu ý diễn giải bắt buộc:**
- Rank invariance tuyệt đối chỉ đúng cho phép trừ `mu` không re-normalize.
- Nhánh after đã được sửa sang biến thể không re-normalize; `rank_invariance_verified=True` cho cả SEARLE và Pic2Word.
- Nếu dùng kết quả Step 4 trong báo cáo, phải ghi rõ biến thể centering nào được đo.

**Checklist:**
- [x] Chạy script thành công
- [x] Xác nhận `rank_invariance_verified` cho từng model
- [x] JSON ghi đủ before/after cho SEARLE và Pic2Word
- [x] Kết luận nhân quả chỉ dựa trên `causal_label` và delta số liệu thực tế

---

### Step 5 — Render báo cáo Module A.1

- **Script:** `scripts/step5_render_report.py`
- **Output cần sinh:**
  - `../../reports/stage_A/module_a1_hubness_report.md`
- **Trạng thái:** DONE — 2026-10-14.

**Điều kiện trước khi chạy:**
- [x] `results/step1_hnsw_indegree.json` tồn tại
- [x] `results/step2_bootstrap_ci.json` tồn tại
- [x] `results/step3_nested_logit.json` tồn tại
- [x] `results/step4_centering.json` tồn tại
- [x] Các plot `fig1`, `fig2`, `fig3` tồn tại

**Yêu cầu báo cáo:**
- Dùng cấu trúc 7 phần theo `mentor-audit-protocol`.
- Không dùng từ ngữ phóng đại như "đột phá", "hoàn hảo", "đanh thép", "khớp dự đoán".
- Mọi số liệu lấy trực tiếp từ JSON.
- Đường dẫn plot là tương đối: `./plots/<ten_file>.png`.
- Nhãn kết luận chỉ dùng một trong bốn nhãn: `XÁC NHẬN`, `ỦNG HỘ MỘT PHẦN`, `CHƯA KẾT LUẬN`, `BÁC BỎ`.

**Checklist:**
- [x] Chạy script thành công sau khi có đủ JSON
- [x] Kiểm tra báo cáo không còn kết luận phóng đại từ bản R1
- [x] Kiểm tra đường dẫn plot tồn tại tương ứng với vị trí report
- [x] Đối chiếu P0.1-P0.4 và cập nhật `../P0_AUDIT_CHECKLIST.md`

---

## 3. LỆNH CHẠY TIẾP THEO

Chạy từ thư mục:

```powershell
cd D:\KLTN\DATA_EVALUATION_PROTOCOL\cir_faiss_thesis\Phase_2_Q1_Journal\R2_Audit\module_a1_revision
```

Thứ tự chạy tiếp theo:

```powershell
python scripts\step2_descriptive_bootstrap.py
python scripts\step3_nested_logistic.py
python scripts\step4_centering_intervention.py
python scripts\step5_render_report.py
```

Sau mỗi bước, kiểm tra output tương ứng trong `results/` và `plots/` trước khi chạy bước kế tiếp.

---

## 4. P0 CẦN ĐÓNG CHO MODULE A.1

| Mã | Nội dung | Trạng thái hiện tại trong module_a1_revision |
|---|---|---|
| P0.1 | Skewness Pic2Word không được diễn giải sai là "cao hơn rõ rệt" nếu số liệu cũ cho thấy 1.00x | DONE — evidence `../p0_audit_checklist/p0_01_skewness_evidence.md` |
| P0.2 | Không được viết Pic2Word có đuôi dày hơn nếu JSON gốc cho thấy SEARLE có kurtosis/max hub cao hơn | DONE — evidence `../p0_audit_checklist/p0_02_tail_evidence.md` |
| P0.3 | Không được kết luận p < 0.05 nếu bootstrap/stat test không ủng hộ | DONE — evidence `../p0_audit_checklist/p0_03_significance_evidence.md` |
| P0.4 | Phân biệt `N10=0` của FlatIP với in-degree HNSW | DONE — evidence `../p0_audit_checklist/p0_04_hnsw_indegree_evidence.md` |

**Quy tắc:** Chỉ đánh dấu P0 DONE sau khi có file bằng chứng trong `../p0_audit_checklist/` và báo cáo A.1 đã được sửa/sinh lại từ JSON.

---

## 5. RỦI RO ĐÃ XỬ LÝ VÀ LƯU Ý CÒN LẠI

1. `step5_render_report.py` đã được sửa để đọc `num_queries`, `gallery_size`, và số dòng từ `results.<model>` thay vì metadata chung.
2. `step3_nested_logistic.py` không dùng McFadden pseudo-R² cho GEE; script ghi QIC như metric chẩn đoán khi thư viện hỗ trợ.
3. `step4_centering_intervention.py` đã dùng biến thể `subtract_gallery_mean_without_renormalization`; rank invariance PASS cho cả hai model.
4. Plot đã được copy sang `reports/stage_A/plots/` để đường dẫn tương đối trong report hoạt động.
5. `../P0_AUDIT_CHECKLIST.md` đã cập nhật P0.1-P0.4 sau khi có JSON, báo cáo, và file bằng chứng.
6. Lưu ý: nhóm `N10=0` không có quan sát trong bảng neighbor-level vì exact top-10 neighbor luôn có `N10 >= 1`; kết luận P0.3 vì vậy dựa trên JSON cũ và được ghi là không có bằng chứng thống kê ở mức alpha 0.05.
