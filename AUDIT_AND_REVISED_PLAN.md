# Rà soát toàn diện & Kế hoạch sửa lỗi 14 ngày

> Tài liệu này thay thế vai trò "kim chỉ nam" của `plan.txt` gốc cho giai đoạn còn lại. Viết dựa trên việc đọc trực tiếp toàn bộ code trong `src/`, chạy thử trên dữ liệu thật đã tải (`data/raw`, `data/annotations`, `data/embeddings`), không suy đoán.

---

## PHẦN 1 — Phản biện `plan.txt` gốc

### Cái plan làm đúng (giữ nguyên tinh thần)
- **Chọn 3 bài thay vì 4**: quyết định đúng, đúng tinh thần "1 người/18 ngày".
- **Một eval harness dùng chung** (`gallery_emb.npy` + `query_emb.npy` + `gt.json`): đúng chiến lược, đã tiết kiệm effort thật — `eval_harness.py` hiện tại đúng là dùng chung cho cả 3 model.
- **`DATA_EVALUATION_PROTOCOL.md`**: phần nghiên cứu protocol (FashionIQ theo category, CIRR theo subset mask, CIRCO theo mAP) là **chính xác** và bám sát source code gốc của 3 paper. Đây là tài liệu tốt nhất trong repo.

### Cái plan thiếu — và đây chính là nguồn gốc "kết quả không tốt"
1. **Plan không đặc tả "gallery" nghĩa là gì cho từng dataset.** `DATA_EVALUATION_PROTOCOL.md` nói đúng lý thuyết ("phải lọc theo category", "chỉ dùng subset") nhưng **không có bước hành động cụ thể nào bắt buộc code phải lọc theo split (train/val/test)**. Đây là lỗ hổng lớn nhất — nó khiến người viết code hiểu "gallery" = "tất cả ảnh có trong thư mục", trong khi đúng ra phải là "chỉ ảnh thuộc tập val, đúng category".
2. **Bước sanity-check (Ngày 3-5, "so khớp với số liệu công bố trong paper gốc") — bước mà chính plan gọi là "không được cắt dù trễ tiến độ" — trên thực tế đã không được thực hiện.** Bằng chứng: thư mục `data/results/` hiện **rỗng hoàn toàn**, không có bảng Recall@K nào từng được đối chiếu với paper gốc. Pipeline đã được viết tới tận "Ngày 9" (4 loại FAISS index, sweep theo kế hoạch) nhưng chưa từng chạy qua cổng kiểm định quan trọng nhất. Đây là lý do bug tồn tại âm thầm suốt từ ngày 2 tới giờ mà không ai phát hiện.
3. **Plan không có bước "khớp checkpoint với dataset đang chạy".** Hệ quả: checkpoint CIRR (`checkpoints/CLIP4Cir/CIRR/RN50x4_fullft/*.pt`) đã được tải sẵn về máy **nhưng chưa từng được code gọi tới** — `get_adapter()` trong cả `extract_features.py` và `extract_queries.py` luôn hard-code checkpoint FashionIQ bất kể `--dataset` là gì.
4. **Plan đề ra sweep tham số (nlist, nprobe, M, efSearch) làm trọng tâm nghiên cứu, nhưng code hiện tại (`run_eval_benchmark.py`) chỉ chạy đúng 1 cấu hình cố định cho mỗi loại index.** Nếu không sửa, thesis sẽ không có "đường cong đánh đổi Recall vs Speedup" — vốn là **đóng góp học thuật chính** của đề tài.
5. **Plan chưa lường trước vấn đề học thuật:** CLIP4Cir là mô hình **supervised**, chỉ được paper gốc train & công bố kết quả trên FashionIQ và CIRR — **không hề có checkpoint CLIP4Cir train trên CIRCO** (xác nhận: thư mục `checkpoints/CLIP4Cir/` chỉ có `FashionIQ/` và `CIRR/`, không có `CIRCO/`). Nếu đưa CLIP4Cir vào so sánh ngang hàng với SEARLE/Pic2Word (zero-shot) trên CIRCO mà không chú thích, đây là lỗi **so sánh không công bằng** (apples-to-oranges) — vi phạm tính học thuật mà bạn yêu cầu phải đảm bảo.

**Kết luận:** code không "gần xong nhưng ra kết quả xấu" một cách ngẫu nhiên — nó xấu vì **3 bug có thể chứng minh cụ thể** (Phần 2), và các bug này lẽ ra phải bị chặn lại bởi chính bước sanity-check mà plan gốc đã cảnh báo "không được cắt". Tin tốt: kiến trúc code (Adapter pattern, 1 eval harness chung) **vẫn đúng và không cần viết lại** — chỉ cần vá đúng chỗ.

---

## PHẦN 2 — Kiểm toán code: bằng chứng cụ thể cho từng bug

### 🔴 Bug #1 (nghiêm trọng nhất): Gallery không lọc theo split/category

Đã xác minh bằng cách load trực tiếp các file `.npy` đã trích xuất và đối chiếu với annotation gốc:

| Dataset | Gallery hiện tại (`.npy`) | Đúng theo protocol | Vấn đề |
|---|---|---|---|
| FashionIQ | **74,381** ảnh (1 index duy nhất, trộn `dress`+`shirt`+`toptee`, cả `train`+`val`+`test`) | 3 index riêng biệt: dress=**3,817**, shirt=**6,346**, toptee=**5,373** (chỉ tập `val`) — đã xác minh từ `data/annotations/fashionIQ/split.{cat}.val.json` có sẵn trên máy | Recall@K bị đo trên gallery lớn gấp ~5 lần và lẫn 3 category — chắc chắn thấp hơn nhiều so với paper |
| CIRR | **21,551** ảnh (gộp cả `train/`, `dev/`, `test1/` trong `img_raw_filtered/`) | Chỉ **2,297** ảnh — chính là thư mục `img_raw_filtered/dev/` đã có sẵn, đếm ra đúng **2,297** file | Recall@K bị đo trên gallery lớn gấp ~9.4 lần |
| CIRCO | 123,403 ảnh — **ĐÚNG**, vì CIRCO chủ đích dùng cả pool COCO unlabeled2017 làm gallery lớn | ✅ Không cần sửa | — |

Nguyên nhân: `src/data/generic_dataloader.py` (`GenericGalleryDataset`) chỉ làm `os.walk()` trên toàn bộ thư mục ảnh raw, **không hề có tham số lọc theo `split` hay `category`**.

**Điểm may mắn:** dữ liệu để fix đã có sẵn 100% trên máy — không cần tải gì thêm:
- FashionIQ: dùng `split.dress.val.json`, `split.shirt.val.json`, `split.toptee.val.json` (đã có trong `data/annotations/fashionIQ/`).
- CIRR: chỉ cần trỏ vào đúng thư mục con `data/raw/cirr/img_raw_filtered/dev/` thay vì cả `img_raw_filtered/`.

### 🔴 Bug #2: CLIP4Cir dùng sai checkpoint cho CIRR

`get_adapter()` (lặp lại giống hệt nhau ở `extract_features.py:27-38` và `extract_queries.py:30-41`) hard-code:
```python
base_ckpt_dir = "checkpoints/CLIP4Cir/FashionIQ/RN50x4_fullft"
```
bất kể `args.dataset` là `fashioniq`, `cirr` hay `circo`. Trong khi checkpoint đúng cho CIRR (`checkpoints/CLIP4Cir/CIRR/RN50x4_fullft/cirr_clip_RN50x4_fullft.pt` và `cirr_comb_RN50x4_fullft.pt`) **đã được tải về sẵn** nhưng chưa bao giờ được dùng. Hệ quả: mọi số liệu CLIP4Cir trên CIRR từ trước tới giờ đều dùng nhầm trọng số fine-tune cho ảnh thời trang, áp lên ảnh đời thường CIRR → lệch domain hoàn toàn, Recall gần như chắc chắn rất thấp.

CIRCO: **không có checkpoint CLIP4Cir chính chủ** (paper gốc chưa từng train/công bố trên CIRCO) → đây là vấn đề thiết kế học thuật, không phải bug code (xem Phần 3, mục "Quyết định học thuật").

### 🟠 Bug #3: Không có sweep tham số FAISS

`run_eval_benchmark.py:54-59` định nghĩa đúng **1 cấu hình cố định** mỗi loại index (`IVFFlat: nprobe=8`, `HNSWFlat: efSearch=64`, `IVFPQ: nprobe=8`). Không có vòng lặp qua nhiều `nlist/nprobe/M/efSearch` như plan gốc yêu cầu (mục 23-24 của `plan.txt`). Nếu giữ nguyên, thesis sẽ chỉ có 1 điểm dữ liệu/index thay vì đường cong đánh đổi — mất đi phần phân tích quan trọng nhất.

### 🟠 Bug #4: Thiếu metric "Recall Retention" so với Brute-force

Toàn bộ hàm tính metric trong `eval_harness.py` (`compute_fashioniq_cirr_recall`, `compute_cirr_subset_recall`, `compute_circo_map`) chỉ so với **ground truth**, không so kết quả của index xấp xỉ (IVF/HNSW/PQ) với chính kết quả của `FlatIP` (brute-force). Thiếu điều này thì không tách được "độ lệch do xấp xỉ ANN" ra khỏi "giới hạn vốn có của model" — trong khi `DATA_EVALUATION_PROTOCOL.md` gốc (mục cuối) đã xác định rõ đây là ý tưởng cốt lõi.

### 🟡 Bug #5 (nhỏ, không ảnh hưởng số liệu): Đặt tên sai ở SEARLE

`searle_adapter.py:25` đặt `model_name="searle_rn50x4"` nhưng thực chất load backbone **ViT-B/32** (`clip.load("ViT-B/32", ...)`, `torch.hub` với `backbone='ViT-B/32'`). Không sai về số liệu, nhưng nếu để nguyên tên này lọt vào bảng kết quả trong thesis sẽ là lỗi báo cáo sai backbone — cần đổi thành `searle_vitb32`.

---

## PHẦN 3 — Quyết định học thuật cần chốt trước khi code tiếp

1. **CLIP4Cir trên CIRCO**: vì không có checkpoint CIRCO chính chủ, đề xuất — **loại CLIP4Cir khỏi bảng so sánh chính trên CIRCO** (chỉ so SEARLE vs Pic2Word ở đó, đúng bản chất "zero-shot benchmark"). Có thể giữ 1 thí nghiệm phụ ở phần Discussion/Appendix: "áp checkpoint CIRR (gần miền dữ liệu tự nhiên nhất) lên CIRCO để minh họa generalization gap của mô hình supervised", nhưng phải chú thích rõ đây là ngoài phạm vi huấn luyện gốc, không so sánh công bằng.
2. **FashionIQ**: xây 3 FAISS index riêng biệt (dress/shirt/toptee), Recall@K cuối cùng = trung bình cộng 3 category — đúng như `DATA_EVALUATION_PROTOCOL.md` đã kết luận.
3. **CIRR**: gallery = 2,297 ảnh `dev` only. Giữ nguyên cách tính `Subset Recall` hiện tại (dùng `group_members`) — logic đó đã đúng, không cần sửa.

---

## PHẦN 4 — Kế hoạch chi tiết 14 ngày (fix-forward, không viết lại từ đầu)

Toàn bộ kiến trúc (Adapter pattern, 1 eval harness chung) được giữ nguyên. Đây là kế hoạch **vá đúng chỗ + chạy lại đúng cách + phân tích + viết**, không phải làm lại từ số 0.

### Ngày 1 — Vá 3 bug gốc (không chạy gì nặng, chỉ sửa code)
- Sửa `GenericGalleryDataset` (`generic_dataloader.py`) và `GenericQueryDataset` (`generic_query_dataloader.py`) để nhận tham số lọc split/category:
  - FashionIQ: thêm tham số `category` (dress/shirt/toptee), lọc theo `split.{cat}.val.json`.
  - CIRR: đổi `img_dir` trỏ thẳng vào `img_raw_filtered/dev/` khi `split="val"`.
- Sửa `get_adapter()` (cả 2 file `extract_features.py`, `extract_queries.py`) để chọn checkpoint CLIP4Cir theo đúng `--dataset` (`FashionIQ/` vs `CIRR/`); với `--dataset circo` → raise lỗi rõ ràng hoặc gắn cờ `--allow-out-of-domain` thay vì âm thầm dùng nhầm checkpoint.
- Đổi `model_name` của SEARLE thành `searle_vitb32`.
- **Deliverable:** code sửa xong, `git diff` review lại tất cả thay đổi.

### Ngày 2 — Trích xuất lại phần bị ảnh hưởng
- Xoá và trích xuất lại: `fashioniq_gallery.npy` (×3 model × 3 category = 9 file nhỏ) và `cirr_gallery.npy` (×3 model, chỉ 2,297 ảnh — nhanh) cho cả 3 model.
- CIRCO: **giữ nguyên**, không cần trích xuất lại (đã đúng).
- Trích xuất lại toàn bộ queries (đang chỉ có đúng 1 file `searle/fashioniq_queries.pkl`) cho 3 model × 3 dataset.
- Chạy `check_data_integrity.py` cho từng file mới.
- **Deliverable:** đầy đủ gallery + query embeddings đúng chuẩn cho 3×3 tổ hợp (trừ CLIP4Cir/CIRCO đã loại theo Phần 3).

### Ngày 3 — CỔNG SANITY-CHECK (không được cắt, đây là bài học từ plan cũ)
- Chạy brute-force (`FlatIP`) cho toàn bộ tổ hợp, in bảng Recall@K/mAP@K.
- Đối chiếu trực tiếp với số liệu công bố trong 3 paper gốc (CLIP4Cir paper Table cho FashionIQ/CIRR, SEARLE paper Table cho CIRR/CIRCO, Pic2Word paper Table cho CIRR/CIRCO). Sai số chấp nhận ~1-2 điểm %.
- Ghi kết quả đối chiếu vào `data/results/sanity_check.md` — đây là file **bắt buộc phải tồn tại và có nội dung** trước khi đi tiếp, khác với lần trước.
- **Deliverable:** bảng đối chiếu, mọi hàng lệch >2-3% phải được ghi chú nguyên nhân nghi ngờ.

### Ngày 4 — Buffer debug (dự phòng cho Ngày 3)
- Nếu Ngày 3 khớp paper: dùng ngày này rà lại `compute_circo_map` (đặc biệt giả định `gt_ids[0] == target_img_id`, đã kiểm chứng đúng 100% trên 220 dòng `val.json` hiện có nhưng nên assert tường minh trong code thay vì ngầm định) và viết Related Work.
- Nếu lệch: debug theo checklist quen thuộc (quên L2-normalize, sai template ghép pseudo-token, sai resize/preprocess, chưa đúng checkpoint).

### Ngày 5 — Cài Recall Retention + Sweep tham số (rút gọn cho vừa 14 ngày)
- Thêm hàm `compute_recall_retention(ann_indices, flat_indices, k_list)` vào `eval_harness.py` — so ANN với chính brute-force, không phải ground truth.
- Sửa `run_eval_benchmark.py`: thay 1 cấu hình cố định bằng lưới rút gọn (đủ để vẽ trade-off, không quá tốn thời gian với 14 ngày):
  - IVFFlat: `nlist ∈ {100, 256}`, `nprobe ∈ {8, 32, 128}`
  - HNSWFlat: `M ∈ {16, 32}`, `efSearch ∈ {32, 128}`
  - IVFPQ: `m ∈ {8, 16}`, `nlist=256`, `nprobe ∈ {32, 128}` + đo memory footprint (RAM của index, dùng `index.sa_code_size()` hoặc so file size)
- **Deliverable:** `run_eval_benchmark.py` chạy ra CSV với nhiều dòng/index type, có cột Recall Retention lẫn Recall thật.

### Ngày 6-7 — Chạy full benchmark
- Chạy toàn bộ tổ hợp model × dataset × index-config qua `run_pipeline.bat` (đã update).
- Theo dõi log lỗi OOM/crash, đặc biệt CIRCO (123K) với IVFPQ train.
- **Deliverable:** toàn bộ CSV kết quả nằm trong `data/results/`.

### Ngày 8 — Buffer bắt buộc
- Dự phòng nếu Ngày 6-7 trễ (rất hay xảy ra với data thật). Nếu đúng tiến độ: chạy thêm 1 thử nghiệm mở rộng nhẹ (vd. tăng CIRCO gallery bằng cách thêm distractor từ COCO val2017 chưa dùng, nếu còn thời gian).

### Ngày 9-10 — Phân tích + viết Results
- Vẽ biểu đồ Recall Retention vs Speedup cho từng index type, từng dataset.
- Bảng memory footprint riêng cho IVFPQ.
- Chọn "điểm ngọt" (retention giảm <1-2% nhưng speedup đáng kể) làm luận điểm chính.
- Viết Methodology + Experiments + Results trong `main.tex`.

### Ngày 11 — Discussion, Conclusion, Abstract + mục "Reproducibility Pitfalls"
- Viết lý giải: vì sao IVFPQ tiết kiệm RAM nhưng giảm recall nhiều hơn HNSW; vì sao HNSW thường cho tỉ lệ tốc độ/độ chính xác tốt nhất.
- **Đề xuất thêm 1 mục ngắn "Reproducibility Pitfalls" trong Discussion**: mô tả ngắn gọn 2-3 bug đã tìm và sửa (gallery lẫn split, checkpoint sai dataset). Đây không phải "để lộ lỗi" — nó là nội dung học thuật thật, cho thấy hiểu sâu protocol gốc, và là điểm cộng thường thấy trong các bài về reproducibility.

### Ngày 12 — Tự review như reviewer
- Đọc lại toàn bài, đối chiếu số liệu trong bảng với CSV gốc (double-check không có sai sót copy-paste).

### Ngày 13 — Polish, format, bibliography
### Ngày 14 — Proofread cuối, xuất PDF, nộp sớm (chừa margin)

---

## PHẦN 5 — Thứ tự cắt giảm nếu trễ tiến độ (14 ngày là khá chặt)

1. Cắt trước: mở rộng distractor-set (phần "nếu còn dư" ở Ngày 8).
2. Tiếp theo: rút gọn lưới sweep (vd. IVFFlat chỉ còn `nprobe ∈ {8, 128}`, bỏ mốc giữa) — vẫn đủ 2 điểm để vẽ xu hướng, chỉ là đường cong thô hơn.
3. Tiếp theo: cắt IVFPQ, chỉ báo cáo IVFFlat + HNSWFlat — vẫn là 2/3 loại index.
4. **Không bao giờ cắt**: Ngày 1-4 (vá bug + sanity-check) — đây chính xác là bước đã bị bỏ qua lần trước và gây ra toàn bộ vấn đề hiện tại. Cũng không cắt thời gian viết (Ngày 11-14).
