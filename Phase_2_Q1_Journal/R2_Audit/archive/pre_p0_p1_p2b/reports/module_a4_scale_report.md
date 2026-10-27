# Báo cáo Thực nghiệm Module A.4: Khảo sát Quy mô Gallery Mở rộng (10K - 500K)

> **Mục tiêu:** Giải quyết triệt để phản biện 'Quy mô gallery nhỏ không ai cần dùng ANN' bằng cách thiết lập trục thực nghiệm mở rộng gallery từ 10.000 đến 500.000 ảnh (sử dụng distractor vectors).

---

## 1. Bảng Đo lường Hiệu năng theo Quy mô Gallery

| Quy mô Gallery (N) | FlatIP Latency | HNSW Latency | HNSW Speedup | HNSW Retention | IVFFlat Latency | IVFFlat Speedup | IVFFlat Retention |
|---|---|---|---|---|---|---|---|
| **10,000** | 0.553 ms | 0.050 ms | **11.1x** | 97.3% | 0.115 ms | **4.8x** | 98.2% |
| **50,000** | 2.751 ms | 0.122 ms | **22.6x** | 95.5% | 0.362 ms | **7.6x** | 97.3% |
| **123,403** | 7.665 ms | 0.183 ms | **41.9x** | 93.6% | 0.722 ms | **10.6x** | 96.0% |
| **250,000** | 15.773 ms | 0.191 ms | **82.6x** | 92.9% | 0.919 ms | **17.2x** | 95.3% |
| **500,000** | 37.466 ms | 0.273 ms | **137.4x** | 93.1% | 1.155 ms | **32.4x** | 93.9% |

---

## 2. Phân tích Bản chất Khoa học

1. **Động lực tăng tốc của ANN ở quy mô lớn:**
   - Ở quy mô nhỏ (N = 10K), FlatIP chỉ tốn ~0.55 ms. Tăng tốc của HNSW hay IVF chỉ ở mức 4–11x.
   - Khi quy mô tăng lên 123K và 500.000 ảnh (500K), độ trễ của FlatIP tăng tuyến tính O(N) lên tới 37.47 ms, trong khi HNSW chỉ tăng theo logarithmic O(log N) ở mức 0.27 ms. Tăng tốc đạt **137.4x** (với retention ổn định 93.1%).
2. **Bảo toàn tính khoa học của Evaluation Protocol:**
   - Vì toàn bộ ground truth target vẫn nằm trong gallery gốc, các chỉ số Recall@10 và Retention@10 vẫn phản ánh chính xác khả năng tìm kiếm của mô hình trong không gian bị 'pha loãng' bởi 376.597 vector nhiễu (distractor vectors).

## 3. Biểu đồ Minh hoạ

1. `data/results/phase2_stageA/plots/scale_crossover_1m.png`: Biểu đồ log-log thể hiện đường cong crossover và tốc độ bứt phá của HNSW/IVF ở quy mô 500K.

