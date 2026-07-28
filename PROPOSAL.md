# ĐỀ CƯƠNG NGHIÊN CỨU (PROPOSAL)

## Đánh giá và Tối ưu hóa Truy xuất Ảnh Đa phương thức (Composed Image Retrieval) ở Quy mô Lớn bằng FAISS: Nghiên cứu Thực nghiệm trên CLIP4Cir, SEARLE và Pic2Word

---

## 1. Đặt vấn đề

**Composed Image Retrieval (CIR)** là bài toán truy xuất ảnh trong đó truy vấn gồm 2 thành phần: một ảnh tham chiếu (reference image) và một câu văn bản mô tả sự thay đổi mong muốn (relative caption). Ví dụ: đưa vào một ảnh chiếc váy đỏ kèm câu "nhưng màu xanh và tay ngắn hơn", hệ thống phải trả về ảnh chiếc váy xanh, tay ngắn tương ứng trong kho dữ liệu. Đây là bài toán quan trọng trong tìm kiếm thương mại điện tử, nơi người dùng thường muốn tinh chỉnh kết quả tìm kiếm dựa trên một sản phẩm họ đã thấy.

Ba năm gần đây (2023) chứng kiến bước tiến lớn của CIR nhờ tận dụng không gian biểu diễn của CLIP: **CLIP4Cir** (supervised, dùng Combiner network), **SEARLE** và **Pic2Word** (zero-shot, dùng Textual Inversion / pseudo-word token). Cả ba công trình đều tập trung tối ưu **tầng model** — làm sao sinh ra 1 vector truy vấn biểu diễn chính xác nhất ý định người dùng — và đánh giá bằng cách quét cạn (brute-force, `O(N)`) toàn bộ gallery để tính Recall@K/mAP@K.

Cách đánh giá này ẩn chứa một giả định không thực tế: **gallery đủ nhỏ để quét cạn trong thời gian chấp nhận được**. Trong triển khai thực tế (catalogue thương mại điện tử có thể lên tới hàng triệu ảnh), quét cạn là bất khả thi — ngành công nghiệp dùng **Approximate Nearest Neighbor (ANN) search** (ví dụ FAISS của Meta) để đánh đổi một phần độ chính xác lấy tốc độ tra cứu gần như hằng số. Tuy nhiên, **chưa có công trình CIR nào hệ thống hóa việc đo lường mức độ đánh đổi này** — không rõ liệu một mô hình CIR tối ưu (Recall cao trên brute-force) có giữ được lợi thế đó khi chuyển sang ANN index hay không, và loại index nào (IVF, HNSW, hay Product Quantization) phù hợp nhất với đặc tính của vector truy vấn CIR.

## 2. Khoảng trống nghiên cứu (Research Gap)

Từ `LITERATURE_REVIEW.md`: cả 3 công trình nền tảng (CLIP4Cir, SEARLE, Pic2Word) đều dùng phép nhân ma trận trực tiếp (`matmul`/dot product) giữa vector truy vấn và toàn bộ gallery trong code đánh giá gốc — tức **quét cạn `O(N)`**. Không công trình nào đề cập đến **tầng Index** (làm sao tra cứu nhanh trong kho hàng triệu vector). Đây chính là khoảng trống mà đề tài này nhắm tới: thay thế phép quét cạn `O(N)` bằng các cấu trúc chỉ mục xấp xỉ của FAISS (`IVFFlat`, `HNSWFlat`, `IVFPQ`), đo lường có hệ thống mức độ đánh đổi giữa **tốc độ (Latency/QPS)**, **bộ nhớ (Memory footprint)**, và **độ chính xác (Recall/mAP)** — trên cả 2 trường phái model (supervised và zero-shot) và cả 3 benchmark chuẩn của lĩnh vực (FashionIQ, CIRR, CIRCO).

## 3. Mục tiêu nghiên cứu

1. **Tái hiện thực nghiệm (reproduce)** đúng giao thức đánh giá gốc của 3 công trình CIR đại diện — làm nền để mọi so sánh sau đó có giá trị khoa học (không so sánh trên một baseline sai).
2. **Xây dựng một hệ thống benchmark thống nhất** (1 eval harness dùng chung cho cả 3 model) đo lường Recall@K, mAP@K, Recall Retention (so với brute-force), Latency, QPS, và Memory footprint khi thay FAISS `IndexFlatIP` bằng `IndexIVFFlat`, `IndexHNSWFlat`, `IndexIVFPQ`.
3. **Quét không gian tham số** của từng loại index (`nlist`, `nprobe`, `M`, `efSearch`, `m` subquantizer) để tìm "điểm ngọt" — cấu hình giữ Recall Retention > 98% nhưng đạt speedup đáng kể.
4. **Rút ra khuyến nghị thực tiễn**: loại index nào phù hợp nhất với mỗi kịch bản (model supervised vs zero-shot; gallery vài nghìn ảnh vs hàng trăm nghìn ảnh).

### Câu hỏi nghiên cứu (Research Questions)
- **RQ1:** Khi thay brute-force bằng ANN index, Recall@K của CIR giảm bao nhiêu ở mỗi mức speedup?
- **RQ2:** Đặc tính này có khác nhau giữa vector truy vấn sinh bởi model supervised (CLIP4Cir) và zero-shot (SEARLE, Pic2Word) hay không?
- **RQ3:** Loại index nào (IVFFlat/HNSWFlat/IVFPQ) cho tỉ lệ Recall-Retention/Speedup tốt nhất, và đánh đổi đó thay đổi thế nào khi tăng quy mô gallery (15K → 123K)?
- **RQ4:** IVFPQ tiết kiệm bộ nhớ bao nhiêu lần so với Flat/HNSW, và cái giá phải trả về Recall là bao nhiêu?

## 4. Đối tượng và Phạm vi nghiên cứu

**Không tự thiết kế model mới** — đề tài thuộc dạng nghiên cứu thực nghiệm/tái hiện (reproducibility study) kết hợp benchmark hệ thống, không phải đề xuất kiến trúc CIR mới. Trọng tâm đóng góp nằm ở **tầng Index**, không phải tầng Model.

| Model | Loại | Backbone | Checkpoint | Dim |
|---|---|---|---|---|
| CLIP4Cir (ACM TOMM 2023) | Supervised | CLIP RN50x4 + Combiner | Riêng cho từng dataset (`fiq_*`, `cirr_*`) | 640 |
| SEARLE (ICCV 2023) | Zero-shot | CLIP ViT-B/32 + Textual Inversion Φ | Chung 1 checkpoint (torch.hub) | 512 |
| Pic2Word (CVPR 2023) | Zero-shot | CLIP ViT-L/14 + IM2TEXT | Chung 1 checkpoint | 768 |

**Ma trận Model × Dataset** (giải thích ô trống ở mục 6.2):

| | FashionIQ | CIRR | CIRCO |
|---|---|---|---|
| CLIP4Cir | ✅ | ✅ | ❌ *(không có checkpoint chính chủ)* |
| SEARLE | ✅ | ✅ | ✅ |
| Pic2Word | ✅ | ✅ | ✅ |

**FAISS index khảo sát:** `IndexFlatIP` (baseline chính xác 100%), `IndexIVFFlat`, `IndexHNSWFlat`, `IndexIVFPQ`.

## 5. Tổng quan các công trình liên quan (Related Work)

*(Nội dung đầy đủ tại `LITERATURE_REVIEW.md`, tóm tắt lại đây để mạch lạc với đề cương.)*

- **CLIP4Cir** (Baldrati et al., ACM TOMM 2023): đóng băng/fine-tune nhẹ CLIP, dùng mạng **Combiner** (MLP với cơ chế dynamic scalar) để hợp nhất vector ảnh và vector văn bản thành 1 vector truy vấn. Đại diện tiêu biểu cho hướng **supervised**, đánh giá gốc trên FashionIQ và CIRR.
- **SEARLE** (Baldrati et al., ICCV 2023): dùng **Textual Inversion** — mạng Φ ánh xạ ảnh tham chiếu thành 1 pseudo-word token `S*`, chèn vào câu văn bản dạng `"a photo of [S*] that ..."`, đẩy qua CLIP Text Encoder đã đóng băng. Đề xuất bộ dữ liệu **CIRCO** (gallery 120K ảnh COCO) làm benchmark zero-shot quy mô lớn.
- **Pic2Word** (Saito et al., CVPR 2023, Google Research): cùng triết lý biến ảnh thành pseudo-token nhưng dùng mạng MLP đơn giản (**IM2TEXT**) huấn luyện trên tập ảnh-chú thích quy mô lớn. Đóng vai trò đối chiếu chéo với SEARLE trên cùng benchmark zero-shot.
- **FAISS** (Johnson et al., 2019 — *Billion-scale similarity search with GPUs*): thư viện ANN chuẩn công nghiệp, cung cấp `IndexIVFFlat` (phân cụm Voronoi/Inverted File), `IndexHNSWFlat` (đồ thị Hierarchical Navigable Small World), `IndexIVFPQ` (Product Quantization — nén vector thành mã byte ngắn).

## 6. Phương pháp nghiên cứu

### 6.1. Kiến trúc hệ thống

Hệ thống tách biệt hoàn toàn 2 giai đoạn để tối ưu chi phí tính toán (xem `PIPELINE_ARCHITECTURE.md`):

```
[Phase 1] Feature Extraction          [Phase 2] Query & Benchmark
  Adapter (CLIP4Cir/SEARLE/Pic2Word)    Adapter.extract_query_features()
     -> gallery_{cat}.npy                 -> query.pkl (features + ground truth)
     -> check_data_integrity.py           -> FaissEvaluator (4 loại index)
                                           -> Recall@K / mAP@K / Latency / QPS
                                           -> benchmark_*.csv
```

**Nguyên tắc thiết kế cốt lõi:** cả 3 model, dù kiến trúc train khác nhau hoàn toàn, đều quy về cùng 1 việc ở bước inference — sinh ra **1 vector `d`-chiều** cho mỗi query, so khớp cosine similarity với gallery vector `d`-chiều. Do đó chỉ cần **một `BaseAdapter` interface chung** (`extract_image_features`, `extract_query_features` → `np.float32` L2-normalized) và **một eval harness chung** (`FaissEvaluator` + các hàm tính metric), tiết kiệm đáng kể công sức so với viết pipeline đánh giá riêng cho từng model.

### 6.2. Dữ liệu và giao thức đánh giá (per-dataset)

Đây là phần **quyết định tính học thuật** của đề tài — mỗi benchmark có một giao thức đánh giá riêng, không được trộn lẫn (xem bằng chứng trích trực tiếp từ source code gốc trong `DATA_EVALUATION_PROTOCOL.md`):

| Dataset | Gallery | Cách chia Index | Metric |
|---|---|---|---|
| **FashionIQ** (Wu et al.) | 3 category `dress`/`shirt`/`toptee`, tách riêng theo `split.{cat}.val.json`: 3,817 / 6,346 / 5,373 ảnh | **3 FAISS index độc lập** — 1 category tuyệt đối không được lẫn sang category khác | Recall@{1,5,10,50}, lấy **trung bình cộng 3 category** |
| **CIRR** (Liu et al.) | Chỉ ảnh thuộc split `dev` (val): 2,297 ảnh | 1 index duy nhất | Recall@{1,5,10,50} toàn cục + **Subset Recall@{1,2,3}** (lọc theo 6 ảnh nhiễu trong `group_members`) |
| **CIRCO** (Baldrati et al., đề xuất trong SEARLE) | Toàn bộ pool COCO2017 unlabeled: 123,403 ảnh | 1 index duy nhất (đúng chủ đích benchmark — mô phỏng gallery thương mại lớn) | **mAP@{5,10,25,50}** (nhiều ground-truth hợp lệ/query, không phải bài toán 1-target) |

Lý do đây là điểm mấu chốt: một lần rà soát code đã phát hiện việc gallery FashionIQ/CIRR ban đầu bị trộn lẫn cả `train/val/test` thay vì lọc đúng split `val` (74,381 ảnh thay vì 15,536 theo category; 21,551 ảnh thay vì 2,297) khiến Recall đo được sai lệch nghiêm trọng so với công bố gốc. Toàn bộ chi tiết kỹ thuật, bằng chứng số liệu, và cách khắc phục nằm trong `AUDIT_AND_REVISED_PLAN.md` — **được xem như một phần nội dung học thuật của đề tài** (mục "Reproducibility Pitfalls" trong phần Discussion), không chỉ là việc sửa lỗi kỹ thuật.

Nguyên tắc tương tự áp dụng cho checkpoint: CLIP4Cir được fine-tune riêng cho từng dataset (checkpoint FashionIQ ≠ checkpoint CIRR) — dùng sai checkpoint khi trích xuất tương đương với đánh giá một mô hình lệch miền dữ liệu hoàn toàn.

### 6.3. Các loại FAISS Index và không gian tham số khảo sát

| Index | Nguyên lý | Tham số sweep |
|---|---|---|
| `IndexFlatIP` | Quét cạn, Inner Product = Cosine (vector đã L2-normalize) | — (baseline) |
| `IndexIVFFlat` | Phân cụm K-Means (Voronoi cells), chỉ quét `nprobe` cụm gần nhất | `nlist ∈ {100, 256}`, `nprobe ∈ {8, 32, 128}` |
| `IndexHNSWFlat` | Đồ thị Hierarchical Navigable Small World, duyệt đa tầng | `M ∈ {16, 32}`, `efSearch ∈ {32, 128}` |
| `IndexIVFPQ` | IVF kết hợp Product Quantization (nén vector thành mã byte) | `nlist = 256`, `m ∈ {8, 16}` subquantizer, `nprobe ∈ {32, 128}` |

### 6.4. Độ đo đánh giá (Metrics)

- **Recall@K** (FashionIQ, CIRR): tỉ lệ query có ảnh đích nằm trong top-K kết quả trả về.
- **Subset Recall@K** (CIRR): Recall@K tính riêng trong tập con 6 ảnh nhiễu của mỗi query (`group_members`).
- **mAP@K** (CIRCO): Mean Average Precision, do một query có thể có nhiều ảnh đích hợp lệ.
- **Recall Retention** (mới bổ sung so với 3 paper gốc — cốt lõi của đề tài): tỉ lệ Recall@K của ANN index so với **chính brute-force**, tách biệt "độ lệch do xấp xỉ ANN" khỏi "giới hạn vốn có của model".
- **Latency (ms/query)** và **QPS**: đo cách ly (isolated), có warm-up trước khi bấm giờ.
- **Memory footprint**: dung lượng cấu trúc index trên RAM, làm nổi bật ưu thế nén của IVFPQ.

### 6.5. Quy trình kiểm định bắt buộc (Sanity-check Gate)

Trước khi chạy bất kỳ thực nghiệm FAISS nào, Recall@K đo bằng brute-force (`FlatIP`) của cả 3 model trên cả 3 dataset **phải được đối chiếu với số liệu công bố trong paper gốc**, sai số chấp nhận ~1-2 điểm %. Đây là bước không được cắt bỏ dù áp lực tiến độ — nếu baseline sai, mọi kết quả FAISS phía sau đều vô nghĩa (bài học rút ra trực tiếp từ vòng lặp thực nghiệm đầu tiên của đề tài, xem `AUDIT_AND_REVISED_PLAN.md`).

## 7. Thiết kế thực nghiệm (Experimental Design)

1. **Trích xuất đặc trưng** (Phase 1): 3 model × (3 category FashionIQ + CIRR + CIRCO, trừ CLIP4Cir/CIRCO) = 14 lần chạy gallery.
2. **Trích xuất truy vấn** (Phase 2a): tương ứng 14 tổ hợp.
3. **Sanity-check**: đối chiếu Recall@K brute-force với paper gốc cho toàn bộ 14 tổ hợp.
4. **Benchmark FAISS đầy đủ**: mỗi tổ hợp × 4 loại index × lưới tham số (mục 6.3) → đo Recall/mAP, Recall Retention, Latency, QPS, Memory.
5. **Phân tích**: vẽ đường cong đánh đổi *Recall Retention vs Speedup* cho từng (model, dataset, index type); xác định điểm ngọt.

## 8. Đóng góp dự kiến của đề tài

1. Một **bộ dữ liệu thực nghiệm tái hiện đúng giao thức gốc** của 3 công trình CIR SOTA — có thể dùng làm baseline tham chiếu cho các nghiên cứu CIR tiếng Việt sau này.
2. Một **hệ thống benchmark FAISS thống nhất, tái sử dụng được** (1 Adapter interface + 1 eval harness) cho bất kỳ model CIR nào sinh vector `d`-chiều.
3. **Đường cong đánh đổi Recall-Retention/Speedup/Memory** đầu tiên (trong phạm vi khảo sát tài liệu của đề tài) cho bài toán CIR, so sánh có hệ thống giữa model supervised và zero-shot.
4. **Khuyến nghị thực tiễn** cho việc triển khai CIR ở quy mô công nghiệp: loại index nào nên dùng ở quy mô gallery nào.
5. Một mục **"Reproducibility Pitfalls"** ghi lại các lỗi tái hiện thực nghiệm điển hình (trộn split, sai checkpoint theo dataset) — đóng góp phương pháp luận cho cộng đồng tái hiện nghiên cứu CIR.

## 9. Kế hoạch thực hiện

Chi tiết theo ngày nằm trong `AUDIT_AND_REVISED_PLAN.md` (14 ngày, tính từ thời điểm rà soát lại toàn bộ pipeline). Tóm tắt các mốc chính:

| Giai đoạn | Nội dung | Deliverable |
|---|---|---|
| Ngày 1 | Vá lỗi gallery/checkpoint theo đúng giao thức | Code sửa xong, verify bằng số liệu thật |
| Ngày 2 | Trích xuất lại Gallery + Query (Phase 1 + 2a) | 14 tổ hợp embedding đúng chuẩn |
| Ngày 3-4 | **Sanity-check gate** (không được cắt) | Bảng đối chiếu Recall@K với paper gốc |
| Ngày 5 | Cài Recall Retention + lưới sweep tham số | `run_eval_benchmark.py` phiên bản đầy đủ |
| Ngày 6-8 | Chạy full benchmark + buffer | CSV kết quả đầy đủ trong `data/results/` |
| Ngày 9-10 | Phân tích, vẽ đường cong trade-off | Section Results |
| Ngày 11-12 | Discussion, Conclusion, tự review | Bản thảo hoàn chỉnh |
| Ngày 13-14 | Polish, format, proofread, nộp | PDF cuối cùng |

## 10. Rủi ro và phương án dự phòng

| Rủi ro | Mức độ | Phương án |
|---|---|---|
| Sanity-check lệch paper gốc | Cao (chặn toàn bộ tiến độ) | Checklist debug: L2-normalize, template pseudo-token, resize ảnh, đúng checkpoint |
| Hết thời gian trước khi hoàn tất sweep đầy đủ | Trung bình | Thứ tự cắt giảm: (1) mở rộng distractor-set, (2) rút gọn lưới sweep còn 2 điểm/tham số, (3) bỏ IVFPQ chỉ báo cáo IVFFlat+HNSWFlat. Không bao giờ cắt sanity-check hoặc thời gian viết. |
| OOM khi train IVFPQ trên gallery CIRCO (123K) | Trung bình | Giảm `nlist`, theo dõi log qua `check_data_integrity.py`/guardrails `gc.collect()` |
| CLIP4Cir/CIRCO bị hiểu nhầm là so sánh công bằng | Thấp nhưng ảnh hưởng tính học thuật | Loại khỏi bảng so sánh chính, chỉ nêu trong Discussion với chú thích rõ phạm vi ngoài miền huấn luyện |

## 11. Tài liệu tham khảo

1. Baldrati, A., et al. *CLIP4Cir: An Empirical Study of CLIP for Composed Image Retrieval*. ACM TOMM, 2023.
2. Baldrati, A., et al. *Zero-Shot Composed Image Retrieval with Textual Inversion (SEARLE)*. ICCV, 2023.
3. Saito, K., et al. *Pic2Word: Mapping Pictures to Words for Zero-shot Composed Image Retrieval*. CVPR, 2023.
4. Johnson, J., Douze, M., Jégou, H. *Billion-scale similarity search with GPUs*. IEEE Transactions on Big Data, 2019. (FAISS)
5. Wu, H., et al. *Fashion IQ: A New Dataset Towards Retrieving Images by Natural Language Feedback*. CVPR, 2021.
6. Liu, Z., et al. *Image Retrieval on Real-life Images with Pre-trained Vision-and-Language Models (CIRR)*. ICCV, 2021.
7. Radford, A., et al. *Learning Transferable Visual Models From Natural Language Supervision (CLIP)*. ICML, 2021.

---
*Tài liệu liên quan trong repo: `LITERATURE_REVIEW.md` (chi tiết Related Work), `DATA_EVALUATION_PROTOCOL.md` (bằng chứng giao thức từ source code gốc), `PIPELINE_ARCHITECTURE.md` (luồng hệ thống), `AUDIT_AND_REVISED_PLAN.md` (rà soát lỗi + kế hoạch 14 ngày).*
