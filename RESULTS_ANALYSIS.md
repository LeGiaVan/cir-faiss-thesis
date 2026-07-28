# Phân tích Kết quả: FAISS Trade-off (Recall Retention vs Speedup)

> Tài liệu này ghi lại kết quả sweep tham số FAISS đầy đủ (Ngày 5-7 theo `AUDIT_AND_REVISED_PLAN.md`), cách tính Recall Retention, và phân tích để viết trực tiếp vào phần **Experiments/Results/Discussion** của khóa luận. Biểu đồ tương tác đầy đủ: xem `data/results/faiss_tradeoff.html` (đã publish artifact).

---

## 1. Phương pháp đo

### 1.1. Recall Retention (metric mới, bổ sung Ngày 5)

Đo trực tiếp **overlap giữa tập top-K trả về bởi index xấp xỉ và tập top-K trả về bởi FlatIP** (brute-force), không qua ground truth — tách biệt hoàn toàn "độ trung thành thuật toán" khỏi "chất lượng vốn có của model":

```
Recall Retention@K = trung bình[ |top-K(ANN) ∩ top-K(FlatIP)| / K ]  trên toàn bộ query
```

Cài đặt tại `compute_recall_retention()` trong `src/evaluation/eval_harness.py`. FlatIP luôn được chạy đầu tiên trong mỗi sweep để làm baseline so sánh.

### 1.2. Lưới sweep tham số (thích ứng theo quy mô gallery N)

Phát hiện quan trọng trong lúc code: `nlist` **không thể dùng số cố định** cho mọi dataset — dùng `nlist=256` cố định (như bản gốc) khiến FAISS cảnh báo "quá ít điểm/cụm" trên gallery nhỏ (CIRR 2,297 ảnh, FashionIQ 3,817-6,346 ảnh), làm hỏng recall của IVFFlat/IVFPQ một cách giả tạo. Sửa bằng công thức thích ứng: `nlist_small ≈ √N`, `nlist_large ≈ 4√N`.

| Index | Tham số sweep |
|---|---|
| IVFFlat | `nlist ∈ {√N, 4√N}` × `nprobe ∈ {8, 32, 128}` (giới hạn ≤ nlist) |
| HNSWFlat | `M ∈ {16, 32}` × `efSearch ∈ {32, 128}` |
| IVFPQ | `nlist = √N` (cố định, ưu tiên train ổn định) × `m ∈ {8, 16}` × `nprobe ∈ {32, 128}` |

### 1.3. Memory footprint

Đo bằng `faiss.serialize_index()` — kích thước byte thực tế của toàn bộ cấu trúc index (bao gồm đồ thị HNSW, inverted list IVF, mã nén PQ), chính xác hơn ước lượng thủ công `dimension × 4 × N`.

### 1.4. Phạm vi chạy

14 tổ hợp (dataset-tag) hợp lệ × ~15 cấu hình/tổ hợp = **120 điểm dữ liệu**, không lỗi. CLIP4Cir không chạy trên CIRCO (quyết định học thuật, xem `AUDIT_AND_REVISED_PLAN.md` mục 3).

---

## 2. Bảng điểm ngọt (sweet spot)

Cấu hình đạt **Speedup cao nhất** trong số các cấu hình có **Recall Retention@10 ≥ 95%**:

| Model | Dataset | Index | Tham số | Speedup | Retention@10 | Tỉ lệ bộ nhớ | Trạng thái |
|---|---|---|---|---|---|---|---|
| SEARLE | CIRCO | HNSWFlat | M32_ef128 | **22.6x** | 97.7% | 113.3% | ✅ Đạt |
| SEARLE | CIRCO | IVFFlat | nlist1405_nprobe128 | 6.4x | 98.3% | 101.5% | ✅ Đạt |
| SEARLE | CIRCO | IVFPQ | m16_nprobe32 | 105.5x | 20.3% | **1.7%** | ❌ Không đạt |
| Pic2Word | CIRCO | HNSWFlat | M32_ef128 | 4.8x | 91.6% | 108.9% | ❌ Không đạt (gần) |
| Pic2Word | CIRCO | IVFFlat | nlist1405_nprobe128 | 1.3x | 97.2% | 101.4% | ✅ Đạt |
| Pic2Word | CIRCO | IVFPQ | m16_nprobe32 | 33.9x | 16.5% | **1.3%** | ❌ Không đạt |
| CLIP4Cir | CIRR | HNSWFlat | M16_ef32 | 4.7x | 96.1% | 105.6% | ✅ Đạt |
| CLIP4Cir | CIRR | IVFFlat | nlist48_nprobe8 | 1.7x | 95.4% | 102.4% | ✅ Đạt |
| CLIP4Cir | CIRR | IVFPQ | m16_nprobe32 | 1.8x | 57.1% | 14.2% | ❌ Không đạt |
| SEARLE | CIRR | HNSWFlat | M16_ef32 | 4.2x | 95.8% | 107.0% | ✅ Đạt |
| Pic2Word | CIRR | HNSWFlat | M32_ef32 | 2.9x | 98.2% | 108.8% | ✅ Đạt |
| CLIP4Cir | FashionIQ | HNSWFlat | M32_ef128 | 1.2x | 99.1% | 110.6% | ✅ Đạt (không đáng dùng) |
| SEARLE | FashionIQ | IVFFlat | nlist293_nprobe128 (~) | 0.9x | 99.1% | 106.0% | ✅ Đạt nhưng **chậm hơn** brute-force |

*(Bảng đầy đủ 24 dòng: `data/results/sweet_spots.csv` hoặc artifact.)*

---

## 3. Ba phát hiện chính

### 3.1. HNSWFlat là lựa chọn an toàn nhất, nhưng hiệu quả phụ thuộc hoàn toàn vào quy mô gallery

Trên **CIRCO (123K ảnh)**: HNSW đạt speedup **22.6x** (SEARLE) trong khi vẫn giữ **97.7%** Recall Retention — đúng câu chuyện "nhanh hơn nhiều, giảm ít". Trên **CIRR/FashionIQ (2.3K-6.3K ảnh)**: speedup tốt nhất chỉ 1-5x, và với FashionIQ (gallery nhỏ nhất) một số cấu hình HNSW/IVFFlat thậm chí **chậm hơn brute-force** (speedup <1x) — ở quy mô này, chi phí quản lý cấu trúc chỉ mục (đồ thị/cụm) vượt quá lợi ích tiết kiệm so sánh, vì brute-force vốn đã cực nhanh trên vài nghìn vector.

**→ Kết luận:** ANN indexing chỉ thật sự có giá trị khi gallery đủ lớn (ngưỡng quan sát được: đâu đó giữa 6K và 123K ảnh trong thực nghiệm này). Đây là phát hiện có giá trị thực tiễn — không phải "luôn luôn nên dùng FAISS", mà "nên dùng FAISS khi vượt một ngưỡng quy mô nhất định".

### 3.2. IVFPQ không đạt "giảm ít" trong sweep hiện tại — đây là đánh đổi cực đoan, không phải lựa chọn cân bằng

IVFPQ luôn cho tốc độ cao nhất (tới **134.97x**, xem `consolidated_sweep.csv`) và bộ nhớ nhẹ nhất (chỉ **1.3-14.4%** kích thước gốc — đúng ưu thế nén PQ) — nhưng Recall Retention@10 cao nhất đo được trong cả sweep chỉ **57-58%** (CIRR), và tệ hơn nhiều ở FashionIQ/CIRCO (**16-32%**). Không cấu hình `m ∈ {8,16}` nào tiệm cận ngưỡng 95%.

**→ Kết luận:** IVFPQ ở lưới tham số đã thử là lựa chọn "đổi rất nhiều để lấy rất nhiều" (cực nhanh + cực nhẹ, nhưng mất hơn 40% độ chính xác) — phù hợp cho use-case chấp nhận đánh đổi lớn (bộ nhớ là ràng buộc cứng), **không phải** ứng viên cho luận điểm "giảm ít". Cần trình bày 2 luận điểm tách biệt trong Discussion: (a) IVFFlat/HNSW = trade-off cân bằng tốt; (b) IVFPQ = trade-off cực đoan, nêu như một lựa chọn khác cho kịch bản khác (bộ nhớ là nút thắt), không gộp chung kết luận.

### 3.3. IVFFlat và HNSWFlat có đặc tính khác nhau đáng chú ý: HNSW nhanh hơn ở cùng mức retention, nhưng IVFFlat ổn định/dễ đoán hơn

Ở hầu hết tổ hợp, HNSW đạt speedup cao hơn IVFFlat tại cùng ngưỡng retention (vd CIRCO/SEARLE: HNSW 22.6x vs IVFFlat 6.4x, cùng ~97-98% retention) — khớp với đặc tính lý thuyết đã biết của HNSW. Ngoại lệ đáng chú ý: **Pic2Word/CIRCO**, HNSW nhanh hơn (4.8x) nhưng KHÔNG đạt 95% (chỉ 91.6%) trong khi IVFFlat đạt 97.2% dù chậm hơn nhiều (1.3x) — cho thấy đặc tính này phụ thuộc vào phân bố embedding cụ thể của từng model, không phải quy luật tuyệt đối.

---

## 4. Đề xuất viết vào khóa luận

- **Methodology**: trích mục 1 (định nghĩa Recall Retention, công thức nlist thích ứng, lý do).
- **Results**: bảng điểm ngọt (mục 2) + biểu đồ trade-off (artifact, chụp màn hình lưới 3×3 cho từng dataset).
- **Discussion**: 3 phát hiện (mục 3) — đặc biệt nhấn 3.1 (ngưỡng quy mô) làm luận điểm chính, 3.2 làm luận điểm phụ (giới hạn của PQ), 3.3 làm quan sát bổ sung (không phải quy luật tuyệt đối, cần thận trọng khi tổng quát hóa).
- **Limitations**: lưới sweep còn thô (2-3 giá trị/tham số) do giới hạn thời gian 14 ngày — nếu mở rộng, đáng thử thêm điểm giữa cho IVFPQ (m=32, nlist lớn hơn) để xem có tiệm cận được ngưỡng 95% ở cấu hình khác hay không, và mở rộng CIRCO bằng distractor set (Ngày 8 buffer) để có thêm 1 điểm quy mô giữa 6K và 123K, làm rõ hơn "ngưỡng quy mô" ở mục 3.1.
