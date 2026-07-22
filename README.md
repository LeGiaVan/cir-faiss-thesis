---

## 🚀 1. Tổng quan Kiến trúc

Hệ thống được thiết kế theo chuẩn MLOps/Data Engineering, tách biệt hoàn toàn giữa quá trình Trích xuất (Feature Extraction) và quá trình Đánh giá (Search Evaluation).

### A. Các Mô hình Đánh giá (Model Adapters)
Chúng tôi sử dụng chung một Base Interface (`BaseAdapter`) để đồng bộ hóa đầu ra của 3 kiến trúc CIR khác biệt:
1. **CLIP4Cir**: Sử dụng mạng kết hợp (Combiner Network) trên nền CLIP RN50x4 (640-dim).
2. **SEARLE**: Sử dụng kỹ thuật Textual Inversion với mạng $\Phi$, chèn pseudo-token `$` vào truy vấn văn bản (512-dim).
3. **Pic2Word**: Sử dụng mô hình ViT-L/14 kết hợp MLP `IM2TEXT`, chèn token `*` vào truy vấn (768-dim).

*Lưu ý: Tất cả các vector đầu ra đều được chuẩn hóa L2 (`L2 Normalization`) để đảm bảo phép đo Inner Product của FAISS tương đương tuyệt đối với Cosine Similarity.*

### B. FAISS Benchmarking Harness
Hệ thống thử nghiệm 4 thuật toán Index để tìm ra điểm cân bằng giữa Tốc độ / Bộ nhớ / Độ chính xác:
- `IndexFlatIP`: Vét cạn (Brute-force) - Baseline chính xác 100%.
- `IndexIVFFlat`: Phân mảnh không gian Voronoi (Inverted File).
- `IndexHNSWFlat`: Duyệt đồ thị tốc độ siêu tốc độ (Hierarchical Navigable Small World).
- `IndexIVFPQ`: Lượng tử hóa vector thành mã Byte (Product Quantization) - Giảm hàng chục lần dung lượng RAM.

### C. Cơ chế An toàn (Guardrails)
Do giới hạn phần cứng và khối lượng dữ liệu khổng lồ (hơn 200,000 ảnh), pipeline được trang bị:
- `gc.collect()` và `torch.cuda.empty_cache()` để chống rò rỉ VRAM (OOM Leak).
- Script cảnh vệ `check_data_integrity.py` ngăn chặn lỗi NaN/Inf và sai lệch chuẩn hóa L2 trước khi chạy FAISS.

---

## 📂 2. Cấu trúc Thư mục

```text
cir_faiss_thesis/
├── data/
│   ├── raw/                 # Chứa ảnh gốc và JSON annotations (fashionIQ, circo, cirr)
│   ├── embeddings/          # Chứa vector file (.npy) của Gallery sau khi trích xuất
│   ├── queries/             # Chứa vector file (.pkl) của Queries kèm Ground Truth
│   └── results/             # Chứa báo cáo Benchmark dạng CSV
├── src/
│   ├── data/
│   │   ├── generic_dataloader.py       # Dataloader lấy ảnh Gallery
│   │   └── generic_query_dataloader.py # Dataloader lấy Truy vấn (Ảnh mồi + Text)
│   ├── extractors/
│   │   ├── base_adapter.py             # Interface gốc
│   │   ├── clip4cir_adapter.py         # Adapter CLIP4Cir
│   │   ├── searle_adapter.py           # Adapter SEARLE
│   │   └── pic2word_adapter.py         # Adapter Pic2Word
│   ├── evaluation/
│   │   └── eval_harness.py             # Hệ thống đo lường Metric & FAISS
│   └── scripts/
│       ├── extract_features.py         # Chạy trích xuất Gallery
│       ├── extract_queries.py          # Chạy trích xuất Queries
│       ├── run_eval_benchmark.py       # Chạy đo lường FAISS
│       └── check_data_integrity.py     # Kiểm duyệt dữ liệu Vector
├── third_party/             # Source code gốc của CLIP4Cir, SEARLE, Pic2Word
├── checkpoints/             # Nơi lưu Weights/Models (.pt) tải từ internet
├── run_pipeline.bat         # Kịch bản TỰ ĐỘNG HÓA chạy toàn bộ Pipeline 1-click
└── setup_env.bat            # Khởi tạo môi trường ảo Python
```

---

## 🛠️ 3. Hướng dẫn Chạy (How to run)

### Bước 1: Chuẩn bị Dữ liệu & Môi trường
1. Cài đặt Python 3.9+ và chạy `setup_env.bat` để tạo môi trường ảo `.venv`.
2. Tải các bộ Weights vào thư mục `checkpoints/`.
3. Tải toàn bộ Image và Captions của 3 Datasets đặt vào `data/raw/` theo cấu trúc:
   - `data/raw/fashionIQ/images`, `data/raw/fashionIQ/captions`
   - `data/raw/circo/unlabeled2017`, `data/raw/circo/annotations`
   - `data/raw/cirr/captions`, `data/raw/cirr/image_splits`

### Bước 2: Chạy Tự động Toàn bộ Benchmark
Chỉ cần mở Terminal / Command Prompt và chạy:
```cmd
.\run_pipeline.bat
```

Script này sẽ tự động:
1. Duyệt qua 3 Mô hình $\times$ 3 Bộ dữ liệu.
2. Trích xuất Gallery và kiểm định tính toàn vẹn (Data Integrity).
3. Trích xuất Queries và Ground Truths.
4. Đẩy vào `eval_harness.py` test qua FlatIP, IVFFlat, HNSW, IVFPQ.
5. Xuất ra file Excel CSV báo cáo tại thư mục `data/results/`.

---

## 📈 4. Các Chỉ số Đánh giá (Metrics)

Trong thư mục `data/results/`, bạn sẽ thu được các phân tích sâu sắc:
- **Tốc độ:** `Latency (ms/query)` và `QPS` (Queries Per Second) được đo lường cô lập nghiêm ngặt bằng đồng hồ của CPU.
- **Recall@K (FashionIQ, CIRR):** Đo lường tỷ lệ ảnh mục tiêu nằm trong top K kết quả trả về.
- **Subset Recall@K (CIRR):** Đo lường khả năng phân biệt hình ảnh vi tế bằng cách tìm trong 6 bức hình bị nhiễu.
- **mAP@K (CIRCO):** Tính toán độ chính xác trung bình (Mean Average Precision) đối với bộ dữ liệu CIRCO vì có nhiều Ground Truth hợp lệ cho cùng một truy vấn.
