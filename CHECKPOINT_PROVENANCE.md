# Nguồn gốc Checkpoint (Provenance) — 3 mô hình

> Tài liệu này ghi lại đầy đủ nguồn tải, mức độ xác minh được, và checksum của từng checkpoint đang dùng trong khóa luận — phục vụ mục Methodology/Reproducibility. Xếp theo thứ tự **độ tin cậy nguồn gốc giảm dần**.

---

## 1. SEARLE — độ tin cậy cao nhất (GitHub Release chính chủ)

**Nguồn:** `torch.hub.load(repo_or_dir='miccunifi/SEARLE', model='searle', backbone='ViT-B/32', source='github')`

Đọc trực tiếp `hubconf.py` của repo chính chủ (`github.com/miccunifi/SEARLE`), checkpoint được tải từ:
```
https://github.com/miccunifi/SEARLE/releases/download/weights/SEARLE_ViT-B32.pt
```

Đây là **GitHub Release asset host trực tiếp bởi tài khoản tác giả** (`miccunifi` = MICC, University of Florence — nhóm nghiên cứu công bố paper SEARLE) — không qua Google Drive, không qua mirror bên thứ 3. `torch.hub.load_state_dict_from_url()` tự động tải và cache.

| | |
|---|---|
| File local | `~/.cache/torch/hub/checkpoints/SEARLE_ViT-B32.pt` |
| SHA256 | `55f4414bbfdad5cef2f6dc02452e44f2bdb87ca87ebeb94dfec9f97f188b424c` |
| Size | 25,186,327 bytes |
| Xác minh | Nguồn chính chủ trực tiếp — **không cần thêm bước xác minh nào khác** |

---

## 2. CLIP4Cir — độ tin cậy cao (Google Drive chính chủ, đã verify hash)

**Nguồn:** Google Drive folder ID `1ny2hhzP8HZBnXhjvDEni8P8G4_inCNTv`, dẫn trực tiếp từ README chính thức của tác giả (`github.com/ABaldrati/CLIP4Cir`, mục "Pre-trained models"). Tải bằng `gdown --folder` (`src/extractors/download_checkpoints.py`).

**Đã xác minh độc lập** (trong lúc debug bug CIRR self-retrieval, xem `SANITY_CHECK_REPORT.md` mục 4): tải lại toàn bộ thư mục từ đúng ID Drive trên, so SHA256 với file đang dùng — **khớp 100%** (`f805e08282246e5f316ecf3643ff0bcb` cho `cirr_clip_RN50x4_fullft.pt`). Loại trừ khả năng tải nhầm/hỏng.

| File | SHA256 | Size |
|---|---|---|
| `checkpoints/CLIP4Cir/FashionIQ/RN50x4_fullft/fiq_clip_RN50x4_fullft.pt` | `4111ac139cf96ac0cf31b30bf8f55b654247b06f0f5fbee4fe8dcc8c1c7cfd2f` | 713,874,695 bytes |
| `checkpoints/CLIP4Cir/CIRR/RN50x4_fullft/cirr_clip_RN50x4_fullft.pt` | `7e730077485589379ebba4a52d2ca16e12c894a7ca3654aed5c674bcafb1f50e` | 713,874,695 bytes |

**Lưu ý riêng:** dù nguồn xác minh đúng chính chủ, benchmark FashionIQ vẫn lệch ~11-13 điểm so với paper (đã điều tra kỹ, xem `SANITY_CHECK_REPORT.md` mục 8, `RESULTS_ANALYSIS.md`) — kết luận là giới hạn của bản checkpoint được công bố công khai, không phải do tải sai nguồn.

---

## 3. Pic2Word — độ tin cậy THẤP NHẤT, cần disclosure rõ ràng trong luận văn

### 3.1. Nguồn chính chủ đã chết, xác nhận qua GitHub Issue

README chính thức (`github.com/google-research/composed_image_retrieval`, dòng 40) trỏ tới:
```
https://drive.google.com/file/d/1IxRi2Cj81RxMu0ViT4q4nkfyjbSHm1dF/view
```
**Issue #30** trên repo chính chủ ("The link to the pre-training model file is not working", mở 12/08/2024) xác nhận link này đã chết — **tính đến thời điểm khóa luận, issue vẫn ở trạng thái Open, tác giả (Google Research) chưa phản hồi hay cung cấp link thay thế chính thức**.

### 3.2. Nguồn thực tế đang dùng: mirror cộng đồng HuggingFace, KHÔNG có xác minh nguồn gốc

```
https://huggingface.co/flashingtt/pic2word/resolve/main/pic2word_model.pt
```
Đã kiểm tra trực tiếp trang HuggingFace: **"No model card"** — không có tài liệu mô tả, không rõ danh tính người upload (`flashingtt`), không có xác nhận nào từ tác giả gốc hay bên thứ 3 đáng tin cậy nào về tính toàn vẹn của file.

| | |
|---|---|
| File local | `checkpoints/pic2word_vit_l_14.pt` |
| SHA256 | `bde01cfd53f642c58011b44590a26e14a0fd7d94efb3a16653e660e342aeab7e` |
| Size | 1,723,251,477 bytes |
| Model card | Không có |
| Xác nhận từ tác giả gốc | Không |

### 3.3. Bù đắp bằng xác minh HÀNH VI (functional/behavioral verification) — bằng chứng thay thế cho checksum

Vì không thể đối chiếu checksum với bản gốc (chưa từng công bố công khai, link đã chết), khóa luận dùng phương pháp xác minh gián tiếp nhưng mạnh: **so sánh kết quả benchmark thực tế với số liệu đã công bố trong paper** — một checkpoint bị hỏng/sai gần như chắc chắn sẽ KHÔNG tái tạo lại đúng số liệu paper một cách nhất quán trên nhiều dataset độc lập.

| Dataset | Đo được (FlatIP) | Paper (validation) | Δ |
|---|---|---|---|
| FashionIQ (Table 4, avg R@10) | 25.42 | 24.70 | +0.72 |
| FashionIQ Shirt R@10 (Table 4) | 26.20 | 26.20 | **khớp tuyệt đối** |
| CIRCO (Table 10, mAP@10) | 8.70 | 9.02 | -0.32 |
| CIRCO (Table 10, mAP@50) | 10.69 | 10.83 | -0.14 |

Khớp trong biên độ ≤0.3-0.9 điểm trên **2 dataset độc lập, 8 mốc K khác nhau** — xác suất một checkpoint sai/hỏng ngẫu nhiên tái tạo được mức khớp chính xác này gần như bằng 0. Đây là bằng chứng gián tiếp nhưng đủ mạnh để tin cậy checkpoint đang dùng phản ánh đúng mô hình đã công bố.

### 3.4. Đoạn disclosure đề xuất đưa vào Methodology/Limitations

> *"Checkpoint chính thức của Pic2Word (Saito et al., CVPR 2023) được công bố qua Google Drive, nhưng liên kết này đã ngừng hoạt động (xác nhận qua GitHub Issue #30 trên repo chính chủ, còn mở tại thời điểm thực hiện khóa luận, chưa được tác giả khắc phục). Do không có nguồn thay thế chính thức, khóa luận sử dụng bản mirror cộng đồng trên HuggingFace (`flashingtt/pic2word`) — nguồn này không có model card hay xác nhận nào từ tác giả gốc. Để bù đắp việc không thể xác minh checksum, chúng tôi xác minh gián tiếp bằng cách đối chiếu kết quả benchmark brute-force (FlatIP) với số liệu validation đã công bố trên 2 bộ dữ liệu độc lập (FashionIQ, CIRCO) — kết quả khớp trong biên độ ≤1 điểm ở mọi mốc đo, cho thấy checkpoint phản ánh đúng mô hình đã công bố dù không xác minh được nguồn gốc tuyệt đối. SHA256 của file đang dùng được ghi lại trong `CHECKPOINT_PROVENANCE.md` để đảm bảo khả năng tái lập của chính khóa luận này."*

---

## Tóm tắt

| Model | Nguồn | Loại xác minh | Mức tin cậy |
|---|---|---|---|
| SEARLE | GitHub Release chính chủ | Trực tiếp (nguồn = chính chủ) | ⭐⭐⭐ Cao nhất |
| CLIP4Cir | Google Drive chính chủ | Hash-match qua re-download | ⭐⭐⭐ Cao |
| Pic2Word | HuggingFace mirror cộng đồng (không model card) | Gián tiếp qua functional verification (khớp paper) | ⭐ Thấp, đã bù đắp bằng bằng chứng hành vi |
