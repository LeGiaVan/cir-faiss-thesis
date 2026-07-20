# Báo cáo: Phương pháp luận Dữ liệu & Đánh giá (Dựa trên Source Code gốc)

Để đảm bảo tính "chuẩn học thuật" (Reproducibility), khi chúng ta viết `Generic Dataloader` và `Eval Harness`, ta KHÔNG ĐƯỢC gộp chung tất cả các dataset lại thành một mớ. Mỗi bài báo có một triết lý thiết lập thực nghiệm rất chặt chẽ.

Dưới đây là bằng chứng kỹ thuật chính xác 100% được trích xuất từ source code gốc của 3 công trình (CLIP4Cir, SEARLE, Pic2Word) để làm kim chỉ nam cho đồ án:

---

## 1. FashionIQ: Đánh giá tách biệt theo Category
Cả 3 công trình đều tuân thủ cách chia FashionIQ thành 3 tập riêng biệt.

- **Bằng chứng từ Code:**
  Khi kiểm tra file `third_party/SEARLE/src/datasets.py` và code của `CLIP4Cir`, hàm khởi tạo của `FashionIQDataset` luôn nhận vào tham số `dress_types`. 
  Trong file `validate.py`, vòng lặp đánh giá được viết cứng (hardcode) như sau:
  ```python
  for dress_type in ['dress', 'shirt', 'toptee']:
      dataset = FashionIQDataset('val', [dress_type], 'relative')
      # ... tiến hành trích xuất đặc trưng và tính recall ...
  ```
- **Kết luận cho Dataloader:** Dataloader của đồ án bắt buộc phải có khả năng filter (lọc) theo category. Vector đặc trưng của `dress` tuyệt đối không được lẫn vào không gian tìm kiếm của `shirt`. FAISS Index cũng sẽ phải xây dựng 3 cây Index độc lập cho 3 danh mục này. Metric cuối cùng là trung bình cộng Recall của 3 danh mục.

---

## 2. CIRR: Cách tính $Recall_{Subset}$
CIRR là bộ dữ liệu rất khó vì mỗi query đi kèm với một nhóm ảnh "rất giống nhau" (subset).

- **Bằng chứng từ Code:**
  Kiểm tra file `third_party/SEARLE/src/validate.py` (hàm `cirr_compute_val_metrics`), họ không chỉ tính Recall thông thường mà còn lọc Mask:
  Mỗi batch load lên, họ lấy ra thông tin `group_members` (là danh sách 6 bức ảnh nhiễu lấy từ `gt.json`). Sau khi FAISS (hoặc torch.matmul) trả về danh sách `sorted_index_names` (rank trên toàn bộ ~36,000 ảnh gallery), họ tạo một mặt nạ lọc để giữ lại vị trí của bức ảnh mục tiêu *chỉ trong phạm vi 6 bức ảnh subset đó*:
  ```python
  # Tạo mặt nạ lọc chỉ giữ lại 6 ảnh trong group_members
  group_mask = (sorted_index_names[..., None] == group_members[:, None, :]).sum(-1).astype(bool)
  group_labels = labels[group_mask].reshape(labels.shape[0], -1)
  
  # Tính Recall Subset
  group_recall_at1 = (torch.sum(group_labels[:, :1]) / len(group_labels)).item() * 100
  ```
- **Kết luận cho Dataloader:** Generic Dataloader khi đọc tập query của CIRR phải load kèm mảng `group_members` (chứa 6 ID) để Eval Harness lát nữa dùng làm Mask lọc kết quả FAISS.

---

## 3. CIRCO: Tư duy Nhiều Ground-truths (mAP)
Bộ CIRCO sử dụng toàn bộ 120,000 bức ảnh COCO 2017 làm một biển gallery khổng lồ.

- **Bằng chứng từ Code:**
  Khi kiểm tra `third_party/SEARLE/src/circo_eval/circo_eval.py`, hàm đánh giá không dùng `Recall` mà tính **Average Precision (mAP)**. 
  Lý do là trong `gt.json` của CIRCO, một câu query có thể chứa mảng `target_img_ids` gồm **rất nhiều ID ảnh hợp lệ**. Nó không phải bài toán tìm 1 ảnh đúng duy nhất nữa.
- **Kết luận cho Dataloader:** Với CIRCO, Dataloader sẽ nhồi toàn bộ 120K ảnh vào 1 cụm duy nhất (không chia category). Tập Ground-truth sẽ là một mảng List, và Eval Harness phải implement hàm tính `mAP@5`, `mAP@10`, `mAP@25`, `mAP@50` chuẩn của CIRCO.

---

## 💡 Tổng kết Định hướng Hành động

Tất cả những bằng chứng này củng cố mạnh mẽ cho Kế hoạch của đồ án:
**Chỉ viết MỘT Eval Harness duy nhất, lấy đầu vào là `gallery_emb.npy`, `query_emb.npy` và `gt.json`.**

Mỗi module trích xuất (CLIP4Cir, SEARLE, Pic2Word) chỉ làm nhiệm vụ ném ra các file `.npy` tương ứng. Việc phân tách category, lọc subset mask, hay tính mAP sẽ do một Module Eval độc lập (tích hợp FAISS) đảm nhiệm. Điều này tiết kiệm thời gian tái hiện code cực lớn.
