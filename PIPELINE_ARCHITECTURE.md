# Phân Tích Cấu Trúc Toàn Diện Hệ Thống Đánh Giá CIR - FAISS

Tài liệu này giải thích chi tiết logic dòng chảy dữ liệu (Data Flow) và cách các script tương tác với nhau để tạo ra một hệ thống Benchmarking đo lường hiệu năng chuyên nghiệp.

Hệ thống được chia làm hai giai đoạn (Phases) hoàn toàn độc lập với nhau nhằm tối ưu tài nguyên và thời gian thực thi: **Phase 1 (Nghiền dữ liệu)** và **Phase 2 (Truy vấn & Đánh giá)**.

---

## 🛠️ PHASE 1: Trích xuất Kho Ảnh (Gallery Feature Extraction)
Mục tiêu của Phase 1 là quét qua hàng trăm nghìn tấm ảnh trong database, biến chúng thành các "vector toán học" (embedding) và lưu xuống ổ cứng. Quá trình này rất nặng, nhưng nhờ tách bạch, ta chỉ cần **chạy đúng 1 lần duy nhất**.

**Luồng chạy (Workflow):**
1. **`generic_dataloader.py`**:
   - Quét cấu trúc thư mục của FashionIQ hoặc CIRCO.
   - Nhặt toàn bộ các file `.jpg/.png` và nạp vào bộ nhớ (không cần biết đến label hay json caption).
2. **`extract_features.py`**:
   - Dựng lên 1 trong 3 mô hình AI thông qua `clip4cir_adapter.py`, `searle_adapter.py`, hoặc `pic2word_adapter.py`. (Tất cả đều kế thừa từ `BaseAdapter`).
   - Hút dữ liệu từ Dataloader với `batch_size=128`.
   - Vắt kiệt sức mạnh GPU để đổi ảnh thành ma trận numpy kích thước `(N, 512)` hoặc `(N, 640)` hoặc `(N, 768)`.
   - **Bảo mật bộ nhớ:** PyTorch được ép giải phóng rác (`gc.collect()`, `empty_cache()`) để ngăn VRAM phình to (OOM).
   - Lưu trữ thành file `.npy` vào thư mục `data/embeddings/`.
3. **`check_data_integrity.py`**:
   - Đóng vai trò là "Cảnh sát Kiểm duyệt". Nó soi lại file `.npy` vừa tạo. 
   - Kiểm tra 3 điều kiện tiên quyết: Không có lỗi toán học (NaN/Inf), Số chiều phải khớp hoàn toàn với Model (ví dụ SEARLE là 512), và **Độ dài Vector (Norm) phải bằng đúng 1.0**. Nếu sai 1 li, toàn bộ tiến trình sẽ báo động đỏ và dừng lập tức.

---

## 🎯 PHASE 2: Trích xuất Truy vấn & FAISS Benchmarking
Mục tiêu của Phase này là mô phỏng quá trình người dùng thực tế nhập câu lệnh: "Tôi muốn tìm chiếc áo giống ảnh này nhưng màu xanh". Hệ thống sẽ tạo vector truy vấn, bắn vào kho dữ liệu FAISS và tính điểm.

**Luồng chạy (Workflow):**

### 2.1. Trích xuất Query (`extract_queries.py`)
1. **`generic_query_dataloader.py`**:
   - Phân tích các file `JSON` rất dị của từng bộ dữ liệu:
     - *FashionIQ*: Ghép nối 2 caption bằng chữ "and", target là 1 ảnh.
     - *CIRCO*: Nhặt mảng `gt_img_ids` (nhiều đáp án đúng - phục vụ mAP).
     - *CIRR*: Nhặt target và mảng `group_members` (các đáp án gây nhiễu).
2. Tương tự như Phase 1, các Query (gồm cả Ảnh mồi + Text) được đẩy qua hàm `extract_query_features` của Adapters.
3. Vì dữ liệu này có chứa cả Ground Truth, hệ thống không lưu dưới dạng `.npy` mà đóng gói lại thành từ điển Pickle (`.pkl`) lưu tại `data/queries/`.

### 2.2. Chạy Thử nghiệm (Benchmarking - `run_eval_benchmark.py`)
Đây là Trái tim Cốt lõi của Khóa luận.
1. **Nạp Đạn:** Load file Gallery (`.npy`) và file Query (`.pkl`) từ ổ cứng lên RAM hệ thống.
2. **Kích hoạt FAISS Harness (`eval_harness.py`):** Dữ liệu được nhồi vào 4 cỗ máy FAISS (Index):
   - **FlatIP:** Quét tuyến tính (Brute-force). Độ trễ cao, chính xác 100%. (Tính bằng tích vô hướng Inner Product, tương đương Cosine).
   - **IVFFlat:** Dùng thuật toán K-Means chia không gian thành các cụm (Voronoi Cells), chỉ tìm ở những cụm tiềm năng. Tốc độ cao, ăn RAM bình thường.
   - **HNSWFlat:** Giăng đồ thị 3D nhiều tầng. Điểm ưu việt là tìm siêu nhanh nhưng bù lại tốn cực nhiều bộ nhớ để lưu đồ thị.
   - **IVFPQ (Product Quantization):** Ép chiều dữ liệu (ví dụ 512 chiều) thành các mã số ngắn (byte codes). **Vũ khí tối thượng của FAISS** để giảm dung lượng RAM xuống hàng chục lần (phục vụ Big Data).
3. **Đo Lường Cách Ly (Isolated Measurement):**
   - Đo Latency độc lập bằng hàm `time.perf_counter()`, cách ly hoàn toàn khỏi quá trình Load Data.
   - Gọi hàm toán học (`compute_fashioniq_cirr_recall` và `compute_circo_map`) để xem Top 10 / Top 50 trả về có trúng đích không.
4. **Báo cáo:** Dữ liệu xuất thẳng thành bảng đẹp trên Console và lưu vĩnh viễn vào `data/results/benchmark_*.csv`.

---

## ⚙️ BỘ ĐIỀU PHỐI: `run_pipeline.bat`
Tất cả những chi tiết trên được tự động hóa hoàn toàn bằng file Batch này. Bạn được cấp Menu tương tác để tùy ý chọn chạy Phase 1 xong cúp cầu dao đi ngủ, hoặc chạy Phase 2 để lấy báo cáo vào sáng hôm sau. Việc này triệt tiêu hoàn toàn rủi ro Crash ở 99% quá trình rồi phải bắt đầu lại từ đầu.
