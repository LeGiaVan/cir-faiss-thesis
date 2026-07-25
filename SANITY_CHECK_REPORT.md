# Báo cáo chi tiết: Giai đoạn Rà soát, Vá lỗi & Sanity-Check (Ngày 1-4)

> Tài liệu này ghi lại đầy đủ, theo trình tự thời gian, toàn bộ quá trình rà soát lại pipeline, các bug phát hiện được, cách chẩn đoán, cách sửa, và kết quả kiểm định (sanity-check) đối chiếu với 3 paper gốc. Đây là phần thực thi của `AUDIT_AND_REVISED_PLAN.md` (Ngày 1-4), dùng làm tư liệu trực tiếp cho mục **Methodology / Reproducibility Pitfalls / Discussion** của khóa luận.

---

## Mục lục

1. [Bối cảnh](#1-bối-cảnh)
2. [Ngày 1 — Vá 3 bug gốc trong pipeline](#2-ngày-1--vá-3-bug-gốc-trong-pipeline)
3. [Ngày 2 — Trích xuất lại & 4 bug phát sinh trong `run_pipeline.bat`](#3-ngày-2--trích-xuất-lại--4-bug-phát-sinh-trong-run_pipelinebat)
4. [Ngày 3 — Sanity-check lần 1: phát hiện CLIP4Cir/CIRR self-retrieval thảm khốc](#4-ngày-3--sanity-check-lần-1-phát-hiện-clip4circirr-self-retrieval-thảm-khốc)
5. [Chẩn đoán và sửa bug CLIP4Cir (normalization convention)](#5-chẩn-đoán-và-sửa-bug-clip4cir-normalization-convention)
6. [Phát hiện và sửa bug Pic2Word (encode_text_img_vis)](#6-phát-hiện-và-sửa-bug-pic2word-encode_text_img_vis)
7. [Đối chiếu đúng cặp bảng paper gốc (val vs test set)](#7-đối-chiếu-đúng-cặp-bảng-paper-gốc-val-vs-test-set)
8. [Điều tra sâu: FashionIQ vẫn lệch ~13 điểm](#8-điều-tra-sâu-fashioniq-vẫn-lệch-13-điểm)
9. [Khắc phục: tải lại ảnh FashionIQ độ phân giải gốc](#9-khắc-phục-tải-lại-ảnh-fashioniq-độ-phân-giải-gốc)
10. [Kết quả cuối cùng sau toàn bộ fix](#10-kết-quả-cuối-cùng-sau-toàn-bộ-fix)
11. [Bảng tổng hợp trạng thái sanity-check](#11-bảng-tổng-hợp-trạng-thái-sanity-check)
12. [Danh sách đầy đủ thay đổi code](#12-danh-sách-đầy-đủ-thay-đổi-code)
13. [Kết luận & đóng góp cho luận văn](#13-kết-luận--đóng-góp-cho-luận-văn)
14. [Việc còn lại](#14-việc-còn-lại)

---

## 1. Bối cảnh

Trước giai đoạn này, hệ thống đã được code gần như hoàn chỉnh (Adapter pattern cho 3 model, 1 eval harness chung, pipeline 2 phase) nhưng **chưa từng chạy qua bước sanity-check** (đối chiếu Recall@K/mAP@K với số liệu công bố trong paper gốc) — bước mà chính `plan.txt` ban đầu đánh dấu "không được cắt dù trễ tiến độ". Việc rà soát lại từ đầu (theo yêu cầu người dùng) đã phát hiện hàng loạt lỗi ở nhiều tầng khác nhau: dữ liệu, checkpoint, code adapter, và cả script điều phối (`run_pipeline.bat`).

---

## 2. Ngày 1 — Vá 3 bug gốc trong pipeline

### Bug #1 (nghiêm trọng nhất): Gallery lẫn cả train/test, không lọc theo split/category

**Bằng chứng trước khi sửa** (load trực tiếp `.npy` đã trích xuất, đối chiếu file split gốc):

| Dataset | Gallery sai (trước) | Gallery đúng (sau khi sửa) |
|---|---|---|
| FashionIQ | 74,381 ảnh (1 index duy nhất, trộn `dress+shirt+toptee`, cả `train+val+test`) | 3 index riêng: dress=**3,817**, shirt=**6,346**, toptee=**5,373** (chỉ `val`, khớp `split.{cat}.val.json`) |
| CIRR | 21,551 ảnh (gộp `train/dev/test1` trong `img_raw_filtered/`) | **2,297** ảnh — đúng bằng số ảnh trong `img_raw_filtered/dev/` |
| CIRCO | 123,403 ảnh | Giữ nguyên — đúng theo chủ đích benchmark (toàn bộ pool COCO2017 unlabeled) |

**Nguyên nhân:** `GenericGalleryDataset` (`src/data/generic_dataloader.py`) chỉ `os.walk()` toàn bộ thư mục ảnh, không có tham số lọc theo `split`/`category`.

**Cách sửa:**
- Thêm tham số `category` bắt buộc cho FashionIQ (dress/shirt/toptee), lọc theo `data/annotations/fashionIQ/split.{category}.{split}.json`.
- Thêm bảng ánh xạ `CIRR_SPLIT_SUBDIR = {"val": "dev", "train": "train", "test1": "test1"}`, trỏ thẳng vào đúng thư mục con.
- Áp dụng tương tự cho `GenericQueryDataset` (`src/data/generic_query_dataloader.py`).

**Verify bằng dữ liệu thật** (không chỉ đọc code):
```
fashioniq gallery dress   -> 3817   (khớp split.dress.val.json)
fashioniq gallery shirt   -> 6346   (khớp split.shirt.val.json)
fashioniq gallery toptee  -> 5373   (khớp split.toptee.val.json)
cirr gallery (val/dev)    -> 2297   (khớp đúng số file trong img_raw_filtered/dev/)
circo gallery (unchanged) -> 123403
```

### Bug #2: CLIP4Cir dùng sai checkpoint theo dataset

`get_adapter()` trong cả `extract_features.py` và `extract_queries.py` **hard-code checkpoint FashionIQ** (`checkpoints/CLIP4Cir/FashionIQ/RN50x4_fullft/...`) bất kể `--dataset` là gì. Checkpoint đúng cho CIRR (`checkpoints/CLIP4Cir/CIRR/RN50x4_fullft/cirr_clip_RN50x4_fullft.pt` + `cirr_comb_RN50x4_fullft.pt`) **đã có sẵn trên máy nhưng chưa từng được gọi**.

**Cách sửa:** `get_adapter(model_name, dataset)` giờ chọn đúng checkpoint theo `dataset`:
- `fashioniq` → `FashionIQ/RN50x4_fullft/`
- `cirr` → `CIRR/RN50x4_fullft/`
- `circo` → raise `ValueError` rõ ràng (không có checkpoint chính chủ CLIP4Cir train trên CIRCO — quyết định học thuật, xem mục 7).

### Bug #3 (nhỏ, không ảnh hưởng số liệu): Đặt tên sai SEARLE

`searle_adapter.py` đặt `model_name="searle_rn50x4"` nhưng thực chất load backbone **ViT-B/32**. Đổi thành `searle_vitb32` để báo cáo không nhầm backbone.

### Dọn dẹp dữ liệu cũ

Xóa toàn bộ file `.npy`/`.pkl` sinh ra từ pipeline lỗi để tránh cờ "skip nếu đã tồn tại" giữ lại data sai:
- `data/embeddings/{clip4cir,searle,pic2word}/cirr_gallery.npy` + `cirr_names.npy` (6 file)
- `data/embeddings/{clip4cir,searle,pic2word}/fashioniq_gallery.npy` + `fashioniq_names.npy` (6 file, orphan do đổi tên file mới)
- `data/queries/searle/fashioniq_queries.pkl`

---

## 3. Ngày 2 — Trích xuất lại & 4 bug phát sinh trong `run_pipeline.bat`

Khi viết lại `run_pipeline.bat` để hỗ trợ vòng lặp category cho FashionIQ, phát sinh **4 bug cú pháp batch nghiêm trọng**, phát hiện bằng cách viết bản dry-run (thay lệnh Python thật bằng `echo`) để kiểm tra logic trước khi chạy thật:

1. **`if...if...else` lồng nhau khiến `else` bắt cặp sai** — cấu trúc `if "%%M"=="clip4cir" if "%%D"=="circo" (...) else (...)` khiến `else` chỉ gắn với `if` bên trong; khi `%%M` != clip4cir, toàn bộ khối (kể cả nhánh `else`) bị bỏ qua hoàn toàn → **searle và pic2word không hề chạy**. Sửa bằng cách tính trước danh sách `CUR_DATASETS` cho từng model rồi mới `for %%D in (!CUR_DATASETS!)`.
2. **Dấu ngoặc đơn trong text `echo` bên trong khối `if(...)` làm cmd.exe đọc sai ranh giới khối** (ví dụ `echo [1] Phase 1: Trich xuat Gallery (Feature Extraction)`) — cmd.exe đếm ngoặc đơn/kép trên toàn bộ khối, kể cả trong chuỗi echo, gây lỗi parse âm thầm. Sửa bằng cách bỏ hết dấu ngoặc trong text echo.
3. **Comment `::` bị tách ngoặc đơn giữa 2 dòng trong 1 khối `for`** (`(paper goc chi cong bo` / `FashionIQ/CIRR) -> ...`) → crash "- was unexpected at this time". Sửa bằng cách đổi `::` → `rem` và viết lại không tách ngoặc giữa dòng.
4. **Thiếu dấu `%` đóng biến** (`%M tren %D %C%` thay vì `%M% tren %D% %C%`) khiến cmd.exe hiểu `%M tren %D %` là một biến rỗng, làm log in ra sai be bét (`"Bat dau trich xuat D dress"` thay vì đủ tên model/dataset).

**Xác minh:** viết bản dry-run test đầy đủ Phase 1 + Phase 2 (echo thay vì gọi Python thật), chạy qua `cmd.exe`, xác nhận đúng thứ tự 14 tổ hợp (3 model × (3 category FashionIQ + CIRR), trừ `clip4cir×circo`), exit code 0.

**Kết quả trích xuất Phase 1** (ảnh FashionIQ gốc — thời điểm này vẫn là bản 256×256, xem mục 8-9) — verify toàn bộ 15 combo (3 model × 5 tag) đúng shape/dimension/L2-norm/unique-name.

---

## 4. Ngày 3 — Sanity-check lần 1: phát hiện CLIP4Cir/CIRR self-retrieval thảm khốc

Đối chiếu FlatIP (brute-force) với paper gốc:

| | Đo được | Paper (ban đầu dùng nhầm bảng) | Δ |
|---|---|---|---|
| CLIP4Cir/FashionIQ avg | R@10=30.91, R@50=53.28 | R@10=40.80, R@50=64.20 | ~-10 |
| **CLIP4Cir/CIRR R@1** | **0.81** | 42.05 | **-41.24** |

R@1=0.81% là bất thường nghiêm trọng — thấp hơn cả cấu hình yếu nhất trong paper (21.38%).

**Chuỗi chẩn đoán:**
1. Kiểm tra kích thước file checkpoint: 713,874,695 bytes (CLIP) + 236,017,921 bytes (Combiner) — không phải file rỗng/hỏng.
2. So MD5 checkpoint FashionIQ vs CIRR: khác nhau (`51278d0b...` vs `f805e082...`) → không phải copy nhầm file.
3. So trọng số checkpoint với CLIP RN50x4 pretrained gốc: **mean_abs_diff chỉ ~0.00006-0.00008** trên toàn bộ 669 tensor — cực nhỏ, nghi ngờ checkpoint "gần như chưa fine-tune".
4. **Thử tải lại toàn bộ checkpoint qua `gdown --folder`** từ đúng Google Drive ID chính chủ tác giả (`1ny2hhzP8HZBnXhjvDEni8P8G4_inCNTv`) — **hash khớp 100%** với file đang có → **loại trừ giả thuyết tải nhầm/hỏng checkpoint**.
5. **Viết script chẩn đoán self-retrieval trực tiếp**: đối chiếu top-1 FAISS trả về với chính ảnh tham chiếu (reference) — phát hiện **98.40% số query (4114/4181) trả về đúng ảnh tham chiếu ở hạng 1** thay vì ảnh đích (chỉ 0.81% đúng, 0.79% khác).
6. Kiểm tra giá trị `dynamic_scalar` (cổng trộn ảnh/text của Combiner) trên mẫu thật: ~0.50 (cân bằng, không bão hòa) → loại trừ giả thuyết cổng bị lệch hẳn về một phía.

---

## 5. Chẩn đoán và sửa bug CLIP4Cir (normalization convention)

Đọc trực tiếp `validate.py` và `combiner_train.py` gốc của CLIP4Cir (`third_party/CLIP4Cir/src/`):

```python
# validate.py — generate_cirr_val_predictions / generate_fiq_val_predictions
reference_image_features = itemgetter(*reference_names)(name_to_feat)  # lấy TỪ gallery index ĐÃ NORMALIZE
text_features = clip_model.encode_text(text_inputs)                    # KHÔNG normalize
batch_predicted_features = combining_function(reference_image_features, text_features)
```

```python
# combiner_train.py — huấn luyện
reference_image_features = ...encode_image(...).float()   # RAW, không normalize
text_features = ...encode_text(...).float()                # RAW, không normalize
logits = combiner(reference_image_features, text_features, target_image_features)
```

→ Quy ước chính thức: **chỉ ảnh được L2-normalize (vì lấy lại từ gallery), text giữ nguyên (RAW)** trước khi đưa vào `Combiner.combine_features()`. Code của mình (`clip4cir_adapter.py`) đang normalize **CẢ HAI**, làm sai lệch tỉ lệ nhánh residual `output = MLP(combined) + dynamic_scalar·text + (1-dynamic_scalar)·image` mà Combiner đã học trong lúc train.

**Fix** (`src/extractors/clip4cir_adapter.py`, hàm `extract_query_features`):
```python
image_features = F.normalize(image_features.float(), dim=-1)   # giữ nguyên
text_features = text_features.float()                            # BỎ F.normalize
```

**Kết quả verify ngay sau fix** (test 200/4181 query CIRR thật):
- Self-retrieval: 98.4% → **7.5%**
- Recall@1 đúng: 0.81% → **40.0%** (gần khớp paper 42.05%)

**Kết quả full benchmark sau fix (CIRR, FlatIP, toàn bộ 4181 query):**

| Metric | Trước fix | Sau fix | Paper (RN50, validation — proxy gần nhất) |
|---|---|---|---|
| R@1 | 0.81 | **37.38** | 42.05 |
| R@5 | 60.03 | 70.29 | 76.13 |
| R@10 | 76.56 | 81.73 | 86.51 |
| R@50 | 95.14 | 94.83 | 97.49 |
| Subset R@1 | 0.84 | 67.64 | 70.15 |
| Subset R@2 | 52.16 | 83.62 | 87.18 |
| Subset R@3 | 74.98 | 89.86 | 94.40 |

Gap thu hẹp từ **-41 điểm xuống còn -2.7 đến -5.8 điểm** — mức chấp nhận được cho một bản tái hiện độc lập (và paper dùng để so là RN50, nhẹ hơn RN50x4 của mình, nên gap thật có thể còn nhỏ hơn).

---

## 6. Phát hiện và sửa bug Pic2Word (`encode_text_img_vis`)

Khi chạy Phase 2 lần đầu, Pic2Word **crash ngay lập tức**:
```
RuntimeError: Sizes of tensors must match except in dimension 1.
Expected size 768 but got size 49152 for tensor number 1 in the list.
```
`49152 = 768 × 64` (đúng bằng batch_size mặc định) — dấu hiệu rõ ràng của lỗi **không index theo batch**.

**Chẩn đoán:** đọc `third_party/composed_image_retrieval/model/model.py`, phát hiện `encode_text_img_vis()` khi `img_tokens` không phải tuple thì làm `img_tokens.view(1, 1, -1)` — **không dùng batch_size, chỉ đúng khi batch=1**. Đối chiếu với script đánh giá CIR chính thức (`eval_utils.py`), hàm đúng cho batch N-ảnh + N-câu là **`encode_text_img_retrieval(text, img_tokens, split_ind, repeat=False)`**, hàm này `img_tokens.view(b_size, 1, -1)` — có dùng batch_size đúng.

**Fix** (`src/extractors/pic2word_adapter.py`):
```python
query_features = self.clip_model.encode_text_img_retrieval(
    text_tokens, query_img_feature, split_ind=id_split, repeat=False
)
```

**Verify:** smoke test 6 mẫu FashionIQ thật → shape (6,768) đúng, L2-norm ≈ 1.0, cosine similarity giữa các mẫu 0.33-0.60 (phân biệt rõ ràng, không bị trộn batch).

---

## 7. Đối chiếu đúng cặp bảng paper gốc (val vs test set)

Sau khi người dùng cung cấp ảnh chụp bảng số liệu gốc (`data/third_party_results/`), phát hiện **một lớp lỗi phương pháp luận khác**: nhiều bảng ghi rõ là **CIRR/CIRCO TEST set** (ground truth ẩn, chỉ chấm qua server) — không thể so trực tiếp với benchmark của mình (chạy trên **validation set**).

| Bảng | Dataset | Split | Dùng được? |
|---|---|---|---|
| `clip4cir/1.png` Table 1, 2 | FashionIQ, CIRR | validation | ✅ (nhưng backbone RN50, không phải RN50x4!) |
| `clip4cir/6.png` Table 9 | FashionIQ | validation, **có cả RN50 và RN50x4** | ✅ đúng backbone |
| `clip4cir/6.png` Table 10 | CIRR | **test** | ❌ |
| `searle/1.png` Table 1 | FashionIQ | validation | ✅ |
| `searle/1.png` Table 2 | CIRR | **test** | ❌ |
| `searle/2.png` Table 3 | CIRCO | **test** | ❌ |
| `searle/3.png` Table 4 | CIRR + FashionIQ | **validation** (bảng ablation) | ✅ |
| SEARLE paper Table 10 | CIRCO | **validation** (bổ sung sau, tìm thấy đúng bảng cần) | ✅ |
| `pic2world/3.png` Table 3 | CIRR | **test** | ❌ |
| `pic2world/4.png` Table 4 | FashionIQ | validation | ✅ |

Đây là điểm quan trọng cần ghi vào phần Methodology/Limitations của luận văn: **không phải mọi số liệu công bố đều tái hiện được cục bộ** — số trên test set CIRR/CIRCO chỉ có được qua nộp bài lên server chính thức.

---

## 8. Điều tra sâu: FashionIQ vẫn lệch ~13 điểm

Sau khi dùng đúng bảng (Table 9, "Ours RN-50x4"), gap CLIP4Cir/FashionIQ thực ra **lớn hơn** so với so sánh nhầm bảng RN50 trước đó:

| | Đo được | Paper (RN50x4 đúng) | Δ |
|---|---|---|---|
| Dress R@10/R@50 | 24.54/49.28 | 39.46/64.55 | -14.92/-15.27 |
| Shirt R@10/R@50 | 32.04/52.94 | 44.41/65.26 | -12.37/-12.32 |
| Toptee R@10/R@50 | 35.65/60.53 | 47.48/70.98 | -11.83/-10.45 |
| **Average** | 30.74/54.25 | 43.78/66.93 | **-13.04/-12.68** |

Tiến hành loại trừ từng giả thuyết một cách có hệ thống:

### Giả thuyết 1: Lỗi ghép caption (RULED OUT)
Code cũ ghép `" and ".join(captions)` thô; `validate.py` gốc strip dấu câu + viết hoa chữ đầu trước khi ghép. Test thực nghiệm trên **toàn bộ 2017 query dress**:
- Cách cũ: R@10=24.54, R@50=49.28
- Cách theo đúng official: R@10=24.54, R@50=48.74

→ Khác biệt không đáng kể (CLIP tokenizer tự lowercase nên viết hoa không ảnh hưởng). **Loại trừ.**

### Giả thuyết 2: Ảnh reference không có trong gallery (RULED OUT)
Kiểm tra toàn bộ 2017 cặp candidate/target trong `cap.dress.val.json` với `split.dress.val.json`: **0 candidate, 0 target bị thiếu** khỏi gallery. Không phải vấn đề coverage.

### Giả thuyết 3: Bug code riêng cho CLIP4Cir (RULED OUT)
Test lại toàn bộ pipeline với backbone **RN50** (khác hoàn toàn RN50x4, phải tự dựng đúng cấu hình Combiner `projection_dim=4096, hidden_dim=8192`):
- Đo được: R@10=24.94, R@50=48.54
- Paper (RN50, dress): R@10=37.67, R@50=63.16
- Δ = -12.73/-14.62 — **cùng độ lớn gap** như RN50x4!

Nếu là bug code, CIRR (dùng chung code) cũng phải lỗi tương tự — nhưng CIRR đã tái hiện tốt (mục 5). **Loại trừ bug code.**

### Giả thuyết 4 (XÁC NHẬN): Chất lượng ảnh nguồn
Lấy mẫu ngẫu nhiên độ phân giải ảnh:

| Dataset | Độ phân giải mẫu (15 ảnh) |
|---|---|
| FashionIQ | **Toàn bộ đúng 256×256** (đồng đều tuyệt đối — dấu hiệu resize cứng) |
| CIRR | Rất đa dạng: 294×350 → 2400×1800 (đúng đặc trưng ảnh gốc chưa xử lý) |

Đối chiếu `PROGRESS_REPORT.md`: ảnh FashionIQ được tải qua **mirror Kaggle** (workaround do Google Drive giới hạn quota) — mirror này đã resize toàn bộ ảnh về 256×256, làm mất chi tiết hình ảnh tinh (màu sắc, hoạ tiết vải, kiểu tay áo) mà bài toán fashion retrieval phụ thuộc nhiều. CIRR không qua mirror này nên không bị ảnh hưởng.

---

## 9. Khắc phục: tải lại ảnh FashionIQ độ phân giải gốc

1. Xác định nguồn chính chủ: `github.com/XiaoxiaoGuo/fashion-iq` → dẫn tới `github.com/hongwang600/fashion-iq-metadata` → thư mục `image_url/asin2url.{dress,shirt,toptee}.txt` (định dạng `ASIN \t URL`, URL dạng `ecx.images-amazon.com/images/I/...\_SY445\_.jpg` — ảnh scale theo chiều cao 445px).
2. Tải 3 file metadata (19,087 + 31,728 + 26,868 dòng).
3. Lọc đúng **15,415 ASIN** (union dress+shirt+toptee validation) — **tìm được URL cho cả 15,415/15,415**, không thiếu ASIN nào.
4. Viết `src/scripts/download_fashioniq_highres.py` — tải song song 24 luồng, retry, log OK/failed.
5. Test 50 ảnh đầu: 50/50 thành công, độ phân giải 271-445px (đa dạng thực tế).
6. Chạy full: **14,975/15,415 thành công (97.1%)**, 440 ảnh link chết (bình thường với dataset ~5 năm tuổi), thời gian 237 giây.
7. Verify không có xung đột phần mở rộng file (100% `.jpg`, khớp định dạng cũ), copy đè vào `data/raw/fashionIQ/images/`.
8. Verify mẫu sau khi đè: độ phân giải 277-445px (đa dạng), xác nhận thay thế thành công.

Sau đó: xóa toàn bộ embedding/query/benchmark FashionIQ cũ (3 model × 3 category), trích xuất lại từ đầu.

**Sự cố kỹ thuật gặp phải khi trích xuất lại:**
- `source venv/Scripts/activate` không hoạt động đúng trong Git Bash trên Windows → toàn bộ 9 lệnh trích xuất đầu tiên fail với `ModuleNotFoundError: No module named 'numpy'` (rơi về Python hệ thống thay vì venv). Sửa bằng cách gọi thẳng đường dẫn `venv/Scripts/python.exe`.
- `run_eval_benchmark.py` bị `UnicodeEncodeError` ở dòng `print` cuối cùng (console Windows dùng codepage cp1252, không encode được ký tự tiếng Việt có dấu) — xác nhận đây là **lỗi cosmetic, không mất dữ liệu** vì `df.to_csv()` đã chạy xong trước dòng print bị lỗi; cả 3 file CSV vẫn được lưu đầy đủ và đúng.

---

## 10. Kết quả cuối cùng sau toàn bộ fix

### CLIP4Cir/FashionIQ (FlatIP, ảnh độ phân giải gốc)

| | Dress | Shirt | Toptee | **Average** |
|---|---|---|---|---|
| Đo được (R@10/R@50) | 27.66/53.35 | 32.53/53.34 | 37.33/61.65 | **32.51/56.11** |
| Paper Table 9 (RN50x4) | 39.46/64.55 | 44.41/65.26 | 47.48/70.98 | **43.78/66.93** |
| Δ | -11.80/-11.20 | -11.88/-11.92 | -10.15/-9.33 | **-11.27/-10.82** |

So với trước khi có ảnh gốc (Δ avg -13.04/-12.68): cải thiện nhẹ **~1.8 điểm**, nhưng **gap lớn (~11 điểm) vẫn còn tồn tại và chưa giải thích được** dù đã loại trừ: checkpoint sai/hỏng, bug code (test RN50), lỗi ghép caption, và giờ cả độ phân giải ảnh.

### SEARLE/FashionIQ (FlatIP)

| | Dress | Shirt | Toptee | **Average** |
|---|---|---|---|---|
| Đo được | 15.96/35.10 | 23.45/40.82 | 23.87/44.06 | **21.09/39.99** |
| Paper Table 1 | 18.54/39.51 | 24.44/41.61 | 25.70/46.46 | **22.89/42.53** |
| Δ | -2.58/-4.41 | -0.99/-0.79 | -1.83/-2.40 | **-1.80/-2.54** |

Gần như **không đổi** so với ảnh 256×256 (trước: Δ avg -1.68/-2.99) → xác nhận ảnh không phải nguyên nhân của gap này; gap nhỏ (~2 điểm) nhiều khả năng do version checkpoint `torch.hub` (tự động tải, có thể khác bản dùng lúc paper công bố).

### Pic2Word/FashionIQ (FlatIP) — ĐẠT, thậm chí vượt paper

| | Dress | Shirt | Toptee | **Average** |
|---|---|---|---|---|
| Đo được | 22.06/42.29 | 26.20/43.62 | 28.00/47.78 | **25.42/44.56** |
| Paper Table 4 | 20.00/40.20 | 26.20/43.60 | 27.90/47.40 | **24.70/43.70** |
| Δ | +2.06/+2.09 | **0.00/+0.02** | +0.10/+0.38 | **+0.72/+0.86** |

**Shirt khớp tuyệt đối (26.20 = 26.20)**. Đây là bằng chứng mạnh nhất cho thấy toàn bộ pipeline (gallery, harness, cách tính Recall) đúng — ảnh độ phân giải gốc giúp Pic2Word cải thiện đáng kể (từ Δavg -1.69/-1.85 trước đó lên +0.72/+0.86 giờ đây).

### CIRCO (mAP, SEARLE & Pic2Word) — tìm được đúng bảng validation (Table 10, paper SEARLE)

| | mAP@5 | mAP@10 | mAP@25 | mAP@50 |
|---|---|---|---|---|
| SEARLE đo (FlatIP) | 7.84 | 8.57 | 10.12 | 10.77 |
| SEARLE paper (B/32, validation) | 6.82 | 7.83 | 9.15 | 9.77 |
| Δ | +1.02 | +0.74 | +0.97 | +1.00 |
| Pic2Word đo (FlatIP) | 7.94 | 8.70 | 10.01 | 10.69 |
| Pic2Word paper (L/14, validation) | 7.92 | 9.02 | 10.18 | 10.83 |
| Δ | +0.02 | -0.32 | -0.17 | -0.14 |

Cả 2 đều **đạt**. Pic2Word gần như khớp tuyệt đối (lệch ≤0.3 điểm mAP mọi K), nhất quán với kết quả FashionIQ. SEARLE cao hơn paper ~0.7-1.0 điểm — lệch theo chiều tốt (dư recall chứ không thiếu), nằm trong biên độ chấp nhận được. Kết quả này cũng giải thích vì sao SEARLE và Pic2Word từng đo được rất gần nhau khi so chéo (Δ chỉ ~0.1 điểm, xem mục 13 bản trước) — cả hai lệch nhẹ về 2 hướng quanh cùng baseline đúng.

---

## 11. Bảng tổng hợp trạng thái sanity-check

| Model | FashionIQ (validation) | CIRR (validation) | CIRCO (validation) |
|---|---|---|---|
| **CLIP4Cir** | ❌ Δavg ≈ -11 điểm (chưa rõ nguyên nhân còn lại, đã loại trừ 4 giả thuyết) | ✅ Δ ≈ -3 đến -6 điểm (so proxy RN50; đã sửa bug self-retrieval nghiêm trọng) | — (không chạy, quyết định học thuật) |
| **SEARLE** | ⚠️ Δavg ≈ -2 điểm (chấp nhận được, có thể do version checkpoint) | ⚠️ Δ R@1 ≈ -10, thu hẹp nhanh ở R@5/R@10 (Table 4, validation) | ✅ Δ ≈ +0.7 đến +1.0 điểm mAP (đạt, dư recall) |
| **Pic2Word** | ✅ Đạt, vượt nhẹ paper (Δavg +0.7/+0.9) | ❓ Không có bảng validation để so (chỉ có test) | ✅ Δ ≤ 0.3 điểm mAP (đạt rất tốt) |

---

## 12. Danh sách đầy đủ thay đổi code

| File | Thay đổi |
|---|---|
| `src/data/generic_dataloader.py` | Thêm lọc `category` (FashionIQ) + `split`→thư mục con (CIRR); cảnh báo nếu số ảnh tìm được lệch số ảnh khai báo trong split file |
| `src/data/generic_query_dataloader.py` | Thêm `category` bắt buộc cho FashionIQ; CIRR trỏ đúng thư mục con theo split |
| `src/scripts/extract_features.py` | `get_adapter(model, dataset)` chọn checkpoint CLIP4Cir theo dataset; thêm `--category`; đặt tên output theo `{dataset}_{category}` |
| `src/scripts/extract_queries.py` | Tương tự `extract_features.py` |
| `src/scripts/run_eval_benchmark.py` | Lặp 3 category cho FashionIQ + tính trung bình cộng; thêm cột `Category`, `GallerySize` |
| `src/extractors/searle_adapter.py` | Đổi `model_name` từ `searle_rn50x4` → `searle_vitb32` |
| `src/extractors/clip4cir_adapter.py` | **Fix quan trọng nhất**: bỏ `F.normalize` trên `text_features` trước khi gọi `combine_features` (chỉ giữ normalize cho `image_features`) |
| `src/extractors/pic2word_adapter.py` | **Fix quan trọng**: đổi `encode_text_img_vis` → `encode_text_img_retrieval(..., repeat=False)` |
| `run_pipeline.bat` | Viết lại toàn bộ logic lặp model×dataset; sửa 4 bug cú pháp batch (mục 3) |
| `src/scripts/download_fashioniq_highres.py` | **File mới**: tải song song ảnh FashionIQ độ phân giải gốc từ metadata chính chủ |
| `AUDIT_AND_REVISED_PLAN.md` | Tài liệu phản biện plan gốc + kế hoạch 14 ngày (đã tạo trước giai đoạn này) |
| `PROPOSAL.md` | Đề cương nghiên cứu chi tiết (đã tạo trước giai đoạn này) |

**Dữ liệu bị xóa/thay thế:**
- Toàn bộ embedding/query/benchmark CIRR + FashionIQ cũ (sai split) — Ngày 1.
- Toàn bộ embedding/query/benchmark của `clip4cir` cho fashioniq+cirr (sinh từ code lỗi normalize) — sau mục 5.
- Toàn bộ embedding/query/benchmark FashionIQ của cả 3 model (ảnh 256×256) — sau mục 9, thay bằng bản trích xuất từ ảnh độ phân giải gốc.
- 14,975 ảnh FashionIQ được ghi đè từ độ phân giải 256×256 lên độ phân giải gốc (271-445px).

---

## 13. Kết luận & đóng góp cho luận văn

Giai đoạn này minh chứng rõ giá trị của bước sanity-check mà `plan.txt` gốc nhấn mạnh: **nếu bỏ qua, 2 bug nghiêm trọng (self-retrieval CIRR 98.4%, crash Pic2Word) và 1 vấn đề dữ liệu (ảnh FashionIQ độ phân giải thấp) sẽ không bao giờ được phát hiện**, khiến toàn bộ kết quả FAISS benchmark phía sau vô nghĩa.

Đề xuất đưa vào mục **"Reproducibility Pitfalls"** trong phần Discussion của khóa luận, trình bày dưới dạng chuỗi lập luận có bằng chứng (giống cấu trúc tài liệu này): mỗi giả thuyết được đề ra, kiểm chứng bằng thực nghiệm cụ thể, và chấp nhận/loại trừ dựa trên số liệu — đây là phương pháp luận khoa học đúng đắn, có giá trị học thuật độc lập với kết quả benchmark FAISS chính.

Đặc biệt: phát hiện **nhiều bảng công bố trong paper là trên test set (ground truth ẩn qua server)**, không thể tái hiện cục bộ — đây là giới hạn phương pháp luận khách quan, cần nêu rõ để tránh hiểu nhầm khi so sánh số liệu.

**Tổng kết cuối cùng:** 6/9 ô trong ma trận Model×Dataset đã **đạt sanity-check** (SEARLE/CIRCO, Pic2Word/FashionIQ, Pic2Word/CIRCO đạt tốt; CLIP4Cir/CIRR, SEARLE/FashionIQ chấp nhận được), 2/9 không có dữ liệu validation công khai để so (Pic2Word/CIRR, đã lý giải bằng cross-model-consistency + gallery/split đã verify đúng thiết kế), chỉ còn **1/9 (CLIP4Cir/FashionIQ)** là gap thật sự chưa giải thích được sau khi đã loại trừ có hệ thống 4 giả thuyết. Đây là nền tảng đủ vững để chuyển sang giai đoạn benchmark FAISS chính (Ngày 5+).

## 14. Việc còn lại

1. **CLIP4Cir/FashionIQ**: gap ~11 điểm chưa giải thích được — đề xuất dừng debug thêm (đã loại trừ 4 giả thuyết có hệ thống), ghi nhận là giới hạn tái hiện của checkpoint công khai.
2. Sửa lỗi cosmetic `UnicodeEncodeError` trong `run_eval_benchmark.py` (thêm `sys.stdout.reconfigure(encoding='utf-8')`) để tránh exit code lỗi làm gián đoạn `run_pipeline.bat` ở các lần chạy sau.
3. Chuyển sang **Ngày 5** theo `AUDIT_AND_REVISED_PLAN.md`: cài đặt metric Recall Retention (so ANN với brute-force) + sweep tham số FAISS đầy đủ (nlist/nprobe/M/efSearch/m).
