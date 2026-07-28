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

### D. Đóng góp chính (Contributions)
- **Recall Retention@K**: metric tự thiết kế, đo trực tiếp độ trùng khớp top-K giữa index xấp xỉ (ANN) và `IndexFlatIP` (vét cạn), tách bạch sai số do bản thân index gây ra khỏi sai số vốn có của model — độc lập với ground truth.
- **Adaptive `nlist`**: `nlist ≈ √N`–`4√N` theo quy mô gallery từng dataset, có căn cứ định lượng bám theo khuyến nghị chính thức của FAISS (`4√N`–`16√N`) và ràng buộc tối thiểu `N ≥ 30·nlist` điểm huấn luyện/centroid.
- **Đo lặp lại đảm bảo tính khách quan**: đã kiểm chứng thực nghiệm `FlatIP`/`IVFFlat`/`IVFPQ` deterministic tuyệt đối khi build lại (seed k-means cố định), chỉ `HNSWFlat` có ngẫu nhiên thật (random level assignment) → Latency/QPS đo lặp 7 lần cho mọi index; riêng HNSWFlat build lại độc lập 5 lần để báo cáo Recall/Retention dạng mean ± std.
- **Chuỗi chẩn đoán tái lập (reproducibility)**: phát hiện và sửa 2 bug nghiêm trọng (chuẩn hóa L2 sai trong CLIP4Cir gây tự truy hồi 98.4%; batch-indexing crash trong Pic2Word) — xem chi tiết ở `SANITY_CHECK_REPORT.md`.

Toàn văn báo cáo khoa học (IEEE format) nằm ở [`thesis_report/main.tex`](thesis_report/main.tex); kết quả tương tác (biểu đồ trade-off Recall Retention vs Speedup trên cả 120 cấu hình) xem tại `data/results/faiss_tradeoff.html` (mở trực tiếp bằng trình duyệt).

---

## 📂 2. Cấu trúc Thư mục

```text
cir_faiss_thesis/
├── data/
│   ├── raw/                 # [KHÔNG commit] Ảnh gốc + JSON annotations (fashionIQ, circo, cirr) - tự tải, xem Bước 1
│   ├── embeddings/          # [KHÔNG commit] Vector (.npy) Gallery sau khi trích xuất - tự sinh ra khi chạy pipeline
│   ├── queries/              # [KHÔNG commit] Vector (.pkl) Queries kèm Ground Truth - tự sinh ra khi chạy pipeline
│   └── results/             # [CÓ commit] Báo cáo Benchmark CSV/JSON + artifact HTML - đây là kết quả chính của khóa luận
├── src/                      # [CÓ commit] Toàn bộ code của khóa luận
├── thesis_report/            # [CÓ commit] Báo cáo khoa học LaTeX (IEEE format)
├── third_party/              # Git submodule - source code gốc CLIP4Cir/SEARLE/Pic2Word, xem Bước 1.1
├── checkpoints/              # [KHÔNG commit] Weights (.pt) - tự tải, xem Bước 1
├── run_pipeline.bat           # Kịch bản TỰ ĐỘNG HÓA chạy toàn bộ Pipeline 1-click
└── setup_env.bat              # Khởi tạo môi trường ảo Python
```

Các thư mục đánh dấu **[KHÔNG commit]** bị loại khỏi git (xem `.gitignore`) vì quá nặng (checkpoints ~11GB, embeddings ~1GB) và/hoặc chứa dữ liệu/code thuộc bản quyền của bên thứ ba (dataset gốc, code gốc của tác giả 3 model, ảnh chụp bảng số liệu từ paper) — không phù hợp để redistribute lại. Làm theo Bước 1 bên dưới để tự chuẩn bị.

---

## 🛠️ 3. Hướng dẫn Chạy (How to run)

### Bước 1: Chuẩn bị Dữ liệu & Môi trường

**1.1. Lấy code gốc của 3 model (đã cấu hình sẵn dạng git submodule trong `.gitmodules`):**
```bash
git submodule update --init --recursive
```
(Nếu vừa clone repo này lần đầu, dùng `git clone --recurse-submodules <url>` để lấy luôn submodule trong 1 lệnh.)

> ⚠️ **Patch bắt buộc sau khi lấy submodule Pic2Word** (`third_party/composed_image_retrieval`): file `model/clip.py` của tác giả gốc dùng tên token `<start_of_text>`/`<end_of_text>` không khớp với vocab tokenizer CLIP hiện hành (`<|startoftext|>`/`<|endoftext|>`), gây lỗi tokenize. Cần sửa lại 2 dòng đó trong `model/clip.py` (hàm `tokenize`) trước khi chạy Pic2Word — xem đúng nội dung cần sửa trong `src/extractors/pic2word_adapter.py` (comment liên quan) hoặc hỏi lại nếu cần patch file cụ thể.

**1.2. Tải checkpoint đã fine-tune vào `checkpoints/`** (chi tiết nguồn/SHA256 xem `CHECKPOINT_PROVENANCE.md`):
- **SEARLE** (nguồn tin cậy cao nhất — GitHub Release chính chủ):
  `https://github.com/miccunifi/SEARLE/releases/download/weights/SEARLE_ViT-B32.pt`
- **CLIP4Cir** (Google Drive chính chủ, đã verify SHA256): xem link Google Drive folder ID `1ny2hhzP8HZBnXhjvDEni8P8G4_inCNTv` trong README chính thức của `ABaldrati/CLIP4Cir`, hoặc chạy `python src/extractors/download_checkpoints.py`.
- **Pic2Word** (⚠️ link Google Drive gốc đã chết — GitHub Issue #30 trên repo gốc còn mở, chưa được tác giả xử lý; dùng mirror cộng đồng, đã xác minh gián tiếp qua behavioral verification — xem `CHECKPOINT_PROVENANCE.md` mục 3):
  `https://huggingface.co/flashingtt/pic2word/resolve/main/pic2word_model.pt`

**1.3. Cài môi trường:** Python 3.9+, chạy `setup_env.bat` để tạo `venv` + cài `requirements.txt`.

**1.4. Tải Image + Captions của 3 dataset vào `data/raw/`** theo cấu trúc:
   - `data/raw/fashionIQ/images`, `data/raw/fashionIQ/captions`
   - `data/raw/circo/unlabeled2017`, `data/raw/circo/annotations`
   - `data/raw/cirr/captions`, `data/raw/cirr/image_splits`

   (FashionIQ ảnh độ phân giải gốc: xem `src/scripts/download_fashioniq_highres.py`; CIRCO/CIRR annotations: xem `download_circo_annotations.py`, `download_fashioniq_annotations.py` ở thư mục gốc.)

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

---

## 🔍 5. Tóm tắt Kết quả chính (Key Findings)

Chi tiết đầy đủ + lập luận trong `thesis_report/main.tex`. Ba phát hiện chính (sau khi đo lặp lại và điều tra cơ chế, không chỉ dừng ở số liệu thô):

1. **HNSWFlat luôn nhanh hơn brute-force ở mọi quy mô đã đo** (2.3K–123K ảnh), biên độ thắng giãn từ ~1–5× lên 22.8× khi gallery lớn dần — giải thích bằng tốc độ tăng trưởng chi phí khác nhau (FlatIP tuyến tính theo N, HNSW gần như logarit theo N).
2. **IVFPQ đánh đổi cực đoan**: nén vector 512–768 chiều xuống chỉ 8–16 sub-quantizer khiến sai số tái tạo lớn hơn ~440–470 lần so với mức chênh lệch cần thiết để xếp đúng hạng top-10 (chứng minh bằng bất đẳng thức Cauchy-Schwarz) — retention chỉ 10.9–58.7% tùy dataset.
3. **Thứ tự HNSWFlat vs IVFFlat phụ thuộc model**: ngoại lệ Pic2Word/CIRCO có dấu hiệu liên quan đến việc tham số M (graph degree) chưa scale theo số chiều embedding (768-d, cao nhất trong 3 model) — bằng chứng nhất quán trên CIRCO và CIRR, nhưng không lặp lại trên FashionIQ.

Xem biểu đồ tương tác đầy đủ 120 cấu hình tại `data/results/faiss_tradeoff.html`.

---

## 📄 6. Giấy phép & Trích dẫn

Code trong repository này (thư mục `src/`, `thesis_report/`) được phát hành theo giấy phép MIT — xem `LICENSE`.

Các submodule trong `third_party/` (xem Bước 1.1) giữ nguyên giấy phép gốc của tác giả tương ứng (CLIP4Cir, SEARLE, Pic2Word) — không thuộc phạm vi giấy phép MIT ở trên.

Nếu sử dụng lại code/kết quả trong khóa luận này, vui lòng trích dẫn báo cáo ở `thesis_report/main.tex` cùng 3 công trình gốc: CLIP4Cir (Baldrati et al., 2023), SEARLE (Baldrati et al., 2023), Pic2Word (Saito et al., 2023) — xem đầy đủ trong `thesis_report/references.bib`.
