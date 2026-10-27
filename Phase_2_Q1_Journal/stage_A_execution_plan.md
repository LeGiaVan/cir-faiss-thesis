# Kế hoạch Thực nghiệm Chi tiết: Giai đoạn A — Đo lường Nền tảng
## (Stage A: Empirical Foundation & Falsification Phase)

> **Mục tiêu cốt lõi:** Thực hiện toàn bộ các phép đo đạc hình học và lượng tử hoá trên embedding đã cache để:
> 1. Kiểm định trực tiếp giả thuyết Hubness / Anti-hub lý giải ca dị thường Pic2Word trên HNSWFlat.
> 2. Đo chính xác phân phối nhiễu điểm số delta thực nghiệm của IVFPQ (thay thế cận Cauchy–Schwarz 439x).
> 3. Đo biên định tuyến và tỉ lệ rơi sai cụm của IVFFlat.
> 4. Chuẩn bị trục mở rộng quy mô (Distractor Gallery: 10K, 100K, 1M).
> 5. So sánh sức mạnh dự báo của các chỉ số hình học để hình thành Bảng 1 & 2 của bài báo Journal.
>
> **Đặc điểm:** Chi phí tính toán cực thấp (1-2 ngày, tận dụng cache embedding sẵn có, không cần GPU đào tạo mô hình).

---

## 1. Bản đồ Dữ liệu & Tài nguyên Sẵn có

Tất cả các thực nghiệm của Giai đoạn A sử dụng trực tiếp các embedding đã được trích xuất từ Khóa luận:

| Đối tượng | File đường dẫn | Kích thước / Chiều |
|---|---|---|
| **SEARLE CIRCO Gallery** | `data/embeddings/searle/circo_gallery.npy` | 123.704 vector × 512-d (float32) |
| **SEARLE CIRCO Queries** | `data/queries/searle/circo_queries.pkl` | 220 query test-split (512-d) |
| **Pic2Word CIRCO Gallery** | `data/embeddings/pic2word/circo_gallery.npy` | 123.704 vector × 768-d (float32) |
| **Pic2Word CIRCO Queries** | `data/queries/pic2word/circo_queries.pkl` | 220 query test-split (768-d) |
| **CIRCO Ground Truth** | `data/annotations/circo/` | Danh sách target IDs chuẩn |
| **CIRR & FashionIQ Cache** | `data/embeddings/{searle,clip4cir,pic2word}/...` | Đã có sẵn đầy đủ |

**Thư mục lưu trữ kết quả của Giai đoạn A:**
* Dữ liệu kết quả: `data/results/phase2_stageA/`
* Biểu đồ trực quan: `data/results/phase2_stageA/plots/`
* Báo cáo tổng hợp: `data/results/phase2_stageA/stageA_report.json`

---

## 2. Chi tiết 5 Module Thực nghiệm

---

### MODULE A.1: Kiểm định Giả thuyết Hubness & Anti-Hub (HNSWFlat)
*Mục đích: Giải thích hiện tượng Pic2Word chỉ đạt 91.5% retention trên HNSWFlat trong khi SEARLE đạt 97.0%.*

#### 1. Cơ sở lý thuyết & Giả thuyết kiểm định:
* **Định nghĩa k-occurrence N_k(x):** Với mỗi điểm x trong gallery, N_k(x) là số lần x xuất hiện trong danh sách k láng giềng gần nhất (k-NN) của tất cả các điểm khác trong gallery.
* **Giả thuyết H1 (Hubness Hypothesis):**
  * Không gian 768-d của Pic2Word có độ lệch hubness (skewness) cao hơn rõ rệt so với 512-d của SEARLE.
  * Tỉ lệ ảnh mục tiêu (ground truth) rơi vào nhóm **Anti-hub** (N_k(x) = 0) ở Pic2Word cao hơn SEARLE.
  * HNSWFlat thất bại chủ yếu trên các query có ảnh mục tiêu thuộc nhóm Anti-hub (vì đồ thị HNSW thiếu cạnh đi vào các anti-hub).
* **Giả thuyết đối H0 (Null Hypothesis):**
  * Skewness của Pic2Word và SEARLE tương đương nhau; tỉ lệ retention@10 của HNSWFlat không có sự khác biệt có ý nghĩa thống kê giữa nhóm mục tiêu Anti-hub và nhóm mục tiêu Normal/Hub.

#### 2. Quy trình thực nghiệm:
1. **Bước 1: Tính k-occurrence toàn cục trên CIRCO Gallery (N = 123.704):**
   * Sử dụng FAISS `IndexFlatIP` (vét cạn chính xác 100%) để tìm top-k láng giềng (chọn k = 10) cho mọi vector x trong gallery.
   * Đếm tần suất xuất hiện `N_10(x)` cho từng ảnh x.
2. **Bước 2: Tính các chỉ số thống kê phân phối k-occurrence:**
   * **Skewness S_{N_10}:** Đo độ lệch bậc 3 của phân phối:
     `Skewness = E[(N_10 - mean)^3] / (std^3)`
   * **Tỉ lệ Anti-hub:** Tỉ lệ phần trăm các điểm có `N_10(x) == 0` (những điểm không bao giờ là láng giềng của ai).
   * **Tỉ lệ Hub lớn:** Tỉ lệ phần trăm các điểm có `N_10(x) >= 30` (3*k) và tỉ lệ top 1% điểm giữ bao nhiêu % tổng số kết nối (Robin Hood index).
3. **Bước 3: Phân loại Gallery:**
   * Nhóm **Anti-hub**: N_10(x) == 0
   * Nhóm **Normal**: 1 <= N_10(x) < 30
   * Nhóm **Hub**: N_10(x) >= 30
4. **Bước 4: Kiểm định trực tiếp trên Query CIRCO:**
   * Với 220 query CIRCO, phân loại query dựa trên ảnh mục tiêu ground truth thuộc nhóm nào (Anti-hub, Normal, hay Hub).
   * Đo Recall Retention@10 của HNSWFlat (với M=32, efSearch=64) riêng trên từng nhóm query:
     `Retention_Group = (Recall_HNSW trong nhóm) / (Recall_Flat trong nhóm)`
   * Chạy kiểm định thống kê Mann-Whitney U test giữa nhóm Anti-hub và nhóm Normal.

#### 3. Tiêu chí xác nhận / Bác bỏ:
* **Xác nhận (H1 được chấp nhận):**
  * Skewness của Pic2Word > SEARLE ít nhất 1.5 lần.
  * Retention@10 của HNSWFlat trên nhóm query Anti-hub thấp hơn nhóm Normal >= 10% (với p-value < 0.01).
* **Bác bỏ (H0 được chấp nhận):**
  * Skewness hai bên xấp xỉ nhau, hoặc retention nhóm Anti-hub không khác biệt có ý nghĩa thống kê. Khi đó ta có kết quả âm tính mạnh (falsification) để chuyển hướng sang cơ chế khác (ví dụ: góc bó cụm, manifold curvature).

---

### MODULE A.2: Đo Thực nghiệm Phân phối Nhiễu Điểm số delta (IVFPQ)
*Mục đích: Sửa lỗi cận Cauchy-Schwarz 439x, cung cấp giá trị delta chuẩn xác cho bài báo và làm cơ sở chọn margin epsilon cho Stage C.*

#### 1. Cơ sở lý thuyết:
* Khi nén vector x bằng PQ thành x^, nhiễu điểm số với query q là:
  `Delta_s = |q · x - q · x^|`
* Lý thuyết hình học dự báo: do tính trực giao trong không gian d chiều, giá trị RMS của Delta_s xấp xỉ bằng:
  `RMS(Delta_s) ≈ ||x - x^||_2 / sqrt(d)`
* Cần đo trực tiếp trên dữ liệu thật để kiểm chứng:
  * Phân phối thực nghiệm của Delta_s có đúng là Half-Normal không?
  * RMS thực tế có khớp với `0.428 / sqrt(512) ≈ 0.0189` không?
  * Khoảng tin cậy 95% và 99% của Delta_s là bao nhiêu?

#### 2. Quy trình thực nghiệm:
1. **Bước 1: Huấn luyện chỉ mục IVFPQ chuẩn:**
   * Index: `IVF351,PQ16` và `IVF351,PQ8` trên SEARLE CIRCO (512-d) và Pic2Word CIRCO (768-d).
2. **Bước 2: Trích xuất vector tái tạo x^:**
   * Dùng `index.reconstruct(i)` để tạo mảng `X_hat` tương ứng với toàn bộ gallery `X`.
   * Tính sai số tái tạo Euclidean trung bình: `Mean_Norm_E = mean(||X - X_hat||_2)`.
3. **Bước 3: Đo Delta_s trên 3 tập mẫu khác nhau:**
   * **Tập 1 (Top-10 candidates):** Đo Delta_s trên 10 ứng viên hàng đầu của mỗi query (vùng nhạy cảm nhất quyết định Retention@10).
   * **Tập 2 (Top-100 candidates):** Đo Delta_s trên top 100.
   * **Tập 3 (Random pairs):** Đo Delta_s trên 100.000 cặp query-gallery ngẫu nhiên (kiểm định tính đẳng hướng toàn cục).
4. **Bước 4: Báo cáo tham số phân phối:**
   * Mean, Standard Deviation, RMS, Median, 95th Percentile, 99th Percentile.
   * So sánh tỉ số thực tế: `Ratio = RMS(Delta_s) / Mean_Rank_10_11_Gap`.
   * Vẽ biểu đồ phân phối Histogram + KDE đối chiếu với đường cong phân phối Half-Normal lý thuyết.

#### 3. Tiêu chí thành công:
* RMS thực tế đo được rơi vào khoảng 0.017 – 0.021 (với SEARLE) và 0.014 – 0.018 (với Pic2Word).
* Tỉ số thực tế được chốt chính thức ở mức **15–19 lần** (thay thế hoàn toàn con số 439x).
* Trích xuất giá trị `delta = RMS(Delta_s)`.

---

### MODULE A.3: Đo Sai số Định tuyến IVF & Biên Cụm (IVFFlat)
*Mục đích: Định lượng cơ chế sai số của họ chỉ mục phân hoạch (IVFFlat) để định nghĩa "Biên định tuyến" cho khung Mục 4.2.*

#### 1. Cơ sở lý thuyết:
* `IVFFlat` không nén vector (lưu float32 100%) nên Delta_s = 0.
* Thất bại duy nhất của `IVFFlat` đến từ **sai số định tuyến (routing error)**: coarse quantizer gán query q vào danh sách nprobe cụm lân cận, nhưng ảnh mục tiêu x* lại nằm ở cụm khác không được quét tới.
* Cần đo:
  * Tỉ lệ rơi sai cụm (Cluster Misrouting Rate): % các query có ground truth bị bỏ sót hoàn toàn do nprobe chưa đủ lớn.
  * Biên định tuyến (Routing Margin): Khoảng cách từ query q đến tâm cụm chứa x* so với khoảng cách từ q đến tâm cụm thứ (nprobe + 1).

#### 2. Quy trình thực nghiệm:
1. **Bước 1: Xây dựng chỉ mục IVFFlat:**
   * Index: `IVF351,Flat` (chuẩn như bài ICRCV).
   * Lấy toạ độ các tâm cụm `Centroids` (351 vector × 512-d).
   * Xác định cụm gốc của từng ảnh gallery: `cluster_id(x)`.
2. **Bước 2: Quét qua 220 query CIRCO:**
   * Với mỗi query q, xếp hạng 351 tâm cụm theo khoảng cách cosine giảm dần: `Ranked_Clusters(q)`.
   * Với mỗi ground truth target x* của q, kiểm tra xem `cluster_id(x*)` nằm ở thứ hạng bao nhiêu trong danh sách tâm cụm của q.
3. **Bước 3: Đo lường theo nprobe:**
   * Khảo sát nprobe in {1, 4, 8, 16, 32, 64}:
     * **Misrouting Rate (%):** Tỉ lệ query có x* không nằm trong top-nprobe cụm.
     * Đối chiếu trực tiếp: `Misrouting Rate` có khớp chính xác với `(100% - Recall_Retention của IVFFlat)` ở cùng nprobe không?
   * Tính **Biên định tuyến trung bình (Mean Routing Gap):**
     `Margin = Distance(q, Centroid_{nprobe}) - Distance(q, Centroid_{target})`

#### 3. Tiêu chí thành công:
* Chứng minh đường cong Misrouting Rate trùng khít với đường cong Recall Retention của IVFFlat (chứng minh sai số định tuyến là nguyên nhân duy nhất và trọn vẹn của IVFFlat).
* Đưa ra con số cụ thể về nprobe tối thiểu để Misrouting Rate < 5%.

---

### MODULE A.4: Mở rộng Quy mô Gallery với Distractor (10K -> 100K -> 1M)
*Mục đích: Xử lý triệt để điểm yếu "gallery nhỏ không ai cần dùng ANN" bị phản biện bắt lỗi.*

#### 1. Cơ sở lý thuyết & Thiết kế:
* CIRR (2.297 ảnh) và FashionIQ (3.817–6.346 ảnh) quá nhỏ khiến thời gian tìm kiếm vét cạn chỉ tốn 0.5–2 ms, tốc độ ANN không thể hiện rõ.
* Giải pháp: Giữ nguyên tập query và ground truth của CIRCO / CIRR, nhưng bổ sung thêm các ảnh nhiễu (distractor) từ nguồn công khai (COCO Unlabeled 2017 hoặc OpenImages / LAION subset) để đưa quy mô gallery lên:
  * N_0: Gallery gốc (CIRCO ~123K; CIRR ~2.3K)
  * N_1: 10.000 ảnh (10K)
  * N_2: 100.000 ảnh (100K)
  * N_3: 1.000.000 ảnh (1M - quy mô chuẩn của benchmark ANN quốc tế như BigANN)
* **Tính hợp lệ khoa học:** Vì toàn bộ ground truth target vẫn nằm trong gallery, metric Recall@K và Recall Retention@K vẫn bảo toàn tính chính xác 100%, nhưng độ khó của bài toán tăng lên và hiệu ứng phân rã của ANN sẽ thể hiện rõ rệt.

#### 2. Kế hoạch triển khai:
1. **Bước 1: Chuẩn bị Distractor URLs / Paths:**
   * Tải danh sách 1M URL ảnh từ tập COCO Unlabeled + OpenImages V6 (hoặc sử dụng embeddings đã được tiền xử lý sẵn nếu có).
2. **Bước 2: Trích xuất embedding distractor 1 lần duy nhất:**
   * Sử dụng CLIP ViT-B/32 (cho SEARLE) và ViT-L/14 (cho Pic2Word).
   * Lưu dưới dạng file npy memmap (`data/embeddings/distractors_1m.npy`).
3. **Bước 3: Ghép Gallery theo các mốc quy mô:**
   * N = 10K, 100K, 500K, 1M.
4. **Bước 4: Chạy kiểm định tốc độ (Latency) & Retention:**
   * Đo thời gian tìm kiếm FlatIP vs HNSWFlat vs IVFFlat vs IVFPQ qua từng mốc N.
   * Vẽ biểu đồ Crossover (điểm cắt mà HNSW / IVF vượt trội hoàn toàn so với Flat).

---

### MODULE A.5: Tổng hợp Đánh giá Sức mạnh Dự báo Hình học (Table 1 của bài báo)
*Mục đích: Chứng minh dứt khoát rằng thước đo Hubness vượt trội hơn các thước đo kinh điển (Relative Contrast, LID).*

#### 1. Thiết kế so sánh:
Trên tất cả các dataset (CIRCO, CIRR, FashionIQ Dress, Shirt, Toptee) và cả 3 model (SEARLE, Pic2Word, CLIP4Cir), trích xuất 3 bộ chỉ số hình học:
1. **Relative Contrast (RC):** Tỉ lệ khoảng cách trung bình của cặp ngẫu nhiên chia cho khoảng cách láng giềng gần nhất (Beyer et al., 1999).
2. **Local Intrinsic Dimensionality (LID):** Ước lượng chiều nội tại cục bộ bằng công thức Levina-Bickel MLE (k=20).
3. **Hubness Skewness (S_{N_10}):** Độ lệch bậc 3 của phân phối k-occurrence (Radovanovic et al., 2010).

#### 2. Phân tích tương quan:
* Tính hệ số tương quan hạng **Spearman Rho** và hệ số tương quan tuyến tính **Pearson r** giữa:
  * (RC, LID, Hubness Skewness) với **Recall Retention@10 của HNSWFlat** trên 15 cặp (dataset, model).
* **Kết quả kỳ vọng:**
  * RC và LID có tương quan yếu hoặc nghịch hướng (|rho| < 0.3).
  * Hubness Skewness có tương quan nghịch cực mạnh (rho < -0.85, p < 0.001) với Retention của HNSWFlat.
  * Bảng này sẽ đi thẳng vào **Table 2 của bài báo Journal**, trực tiếp giải quyết nghi vấn của cộng đồng về cơ chế thất bại của graph ANN trên multimodal embeddings.

---

## 3. Kiến trúc Mã nguồn Đề xuất cho Giai đoạn A

Để giữ repo sạch sẽ, có tính tái lập cao và tuân thủ chuẩn nghiên cứu, toàn bộ mã của Giai đoạn A sẽ nằm trong thư mục mới:

```text
cir_faiss_thesis/
├── src/
│   ├── phase2_foundation/
│   │   ├── __init__.py
│   │   ├── measure_hubness.py         # Module A.1: Tính k-occurrence, skewness, phân loại gallery
│   │   ├── measure_pq_perturbation.py # Module A.2: Đo delta thực nghiệm, vẽ phân phối sai số PQ
│   │   ├── measure_ivf_routing.py     # Module A.3: Đo misrouting rate và routing margin của IVF
│   │   ├── build_distractor_scale.py  # Module A.4: Quản lý distractor và benchmark quy mô 10K-1M
│   │   ├── evaluate_geometry_power.py # Module A.5: Tính RC, LID, Skewness và chạy tương quan Spearman
│   │   └── run_stage_a_all.py         # Pipeline tự động chạy toàn bộ Giai đoạn A chỉ bằng 1 lệnh
├── data/
│   └── results/
│       └── phase2_stageA/             # Chứa toàn bộ file json kết quả và biểu đồ png
```

---

## 4. Kế hoạch Tiến độ & Thứ tự Ưu tiên (Execution Checklist)

| Thứ tự | Nhiệm vụ | Thời gian dự kiến | Output kiểm tra |
|---|---|---|---|
| **Ưu tiên 1** | **Chạy Module A.2 (Đo delta PQ)** | 1 - 2 giờ | File `pq_delta_distribution.json` + Biểu đồ phân phối + Chốt tỉ số 15-19x |
| **Ưu tiên 2** | **Chạy Module A.1 (Đo Hubness CIRCO)** | 2 - 3 giờ | File `hubness_skewness.json` + Bảng so sánh SEARLE vs Pic2Word + P-value |
| **Ưu tiên 3** | **Chạy Module A.3 (Đo Routing IVF)** | 1 - 2 giờ | File `ivf_routing_margins.json` + Đường cong Misrouting vs nprobe |
| **Ưu tiên 4** | **Chạy Module A.5 (Tổng hợp Bảng 1)** | 3 - 4 giờ | Script chạy tương quan Spearman trên các cache đã có |
| **Ưu tiên 5** | **Chạy Module A.4 (Distractor 1M)** | 1 ngày | Chuẩn bị dữ liệu quy mô cho các thực nghiệm scale-aware |

---

## 5. Kết quả Đầu ra Dự kiến của Giai đoạn A cho Bài báo

Khi hoàn thành Giai đoạn A, ta có ngay trong tay 4 tài sản khoa học quan trọng nhất:
1. **Một bảng dữ liệu thực nghiệm sạch thay thế Bảng VII ICRCV:** Xoá bỏ hoàn toàn lỗi Cauchy-Schwarz 439x, thay bằng phân phối delta có dẫn xuất lý thuyết sqrt(d) và kiểm chứng thực nghiệm.
2. **Một khám phá mới (Discovery) về Hubness trong CIR:** Bài báo đầu tiên chứng minh và giải thích cơ chế anti-hub gây sụt giảm recall trên graph ANN trong bài toán CIR.
3. **Giá trị delta thực tế:** Đặt nền móng toán học cho việc chọn margin epsilon = 2*delta trong Score-Gap Loss ở Stage C.
4. **Bảng so sánh sức mạnh dự báo (Table 2):** Chứng minh tính vượt trội của thước đo đề xuất so với các chỉ số hình học truyền thống (RC, LID).
