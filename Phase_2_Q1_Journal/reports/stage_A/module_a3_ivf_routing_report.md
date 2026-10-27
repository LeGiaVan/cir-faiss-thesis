# Báo cáo Thực nghiệm Module A.3: Sai số định tuyến IVFFlat

> Bản sửa P0; sinh từ JSON legacy bằng `render_p0_reports.py`. Không gán cấu hình reference mới cho số liệu lịch sử.

## 1. Câu hỏi nghiên cứu

Recall retention có bằng tỷ lệ exact neighbor nằm trong các cụm đã probe không?

## 2. Giả thuyết và dự đoán

Kiểm tra đồng nhất thức cấu trúc coverage/retention, không đặt giả thuyết về nhiễu lượng tử hóa cho IVFFlat.

## 3. Thiết kế thực nghiệm

Nguồn: `data/results/phase2_stageA/json/module_a3_ivf_routing.json`. Profile legacy nlist=351, CIRCO val; chưa áp cấu hình reference mới. Margin là chênh điểm giữa centroid thứ nprobe và nprobe+1.

## 4. Kết quả

searle: nprobe nhỏ nhất trong dải đã đo đạt ≥95% là 32 (96.27%). pic2word: nprobe nhỏ nhất trong dải đã đo đạt ≥95% là 32 (96.05%).

| Model | nlist | nprobe | Retention | Coverage | Margin |
|---|---|---|---|---|---|
| searle | 351 | 1 | 46.09% | 46.09% | 0.013610 |
| searle | 351 | 2 | 62.14% | 62.14% | 0.006868 |
| searle | 351 | 4 | 76.41% | 76.41% | 0.004569 |
| searle | 351 | 8 | 86.18% | 86.18% | 0.003017 |
| searle | 351 | 16 | 92.36% | 92.36% | 0.001295 |
| searle | 351 | 32 | 96.27% | 96.27% | 0.000701 |
| searle | 351 | 64 | 98.77% | 98.77% | 0.000344 |
| searle | 351 | 128 | 99.82% | 99.82% | 0.000214 |
| pic2word | 351 | 1 | 34.95% | 34.95% | 0.012016 |
| pic2word | 351 | 2 | 52.73% | 52.73% | 0.007231 |
| pic2word | 351 | 4 | 68.91% | 68.91% | 0.004815 |
| pic2word | 351 | 8 | 80.77% | 80.77% | 0.002851 |
| pic2word | 351 | 16 | 90.41% | 90.41% | 0.001677 |
| pic2word | 351 | 32 | 96.05% | 96.05% | 0.000766 |
| pic2word | 351 | 64 | 98.59% | 98.59% | 0.000410 |
| pic2word | 351 | 128 | 99.45% | 99.45% | 0.000224 |

## 5. Kết luận và trạng thái

**XÁC NHẬN (kiểm tra cài đặt):** IVFFlat tính inner product trực tiếp trên vector trong các cụm được probe; coverage của exact top-k và retention trùng nhau theo cấu trúc khi cùng metric, candidate set và xử lý ties nhất quán. Đây là kiểm tra cài đặt, không phải phát hiện nhân quả.

## 6. Hạn chế

Chưa có CI và metadata lịch sử đầy đủ. Kết quả không chứng minh quan hệ nhân quả giữa hubness và định tuyến. SEARLE/Pic2Word không có mạng Combiner riêng để fine-tune.

## 7. Các bước tiếp theo

Chuẩn hóa cấu hình; bổ sung thứ hạng cụm của exact neighbor và imbalance factor; chỉ so sánh nprobe trong cùng nlist/profile.

### Cập nhật P1 — profile chuẩn hóa

Reference nlist khác legacy; không dùng ngưỡng nprobe của profile này cho profile khác.

- pic2word, nlist=1024, nprobe=8: retention=71.45%, coverage=71.45%. [JSON](../../R2_Audit/p1_reference/results/a3_pic2word.json).
- pic2word, nlist=1024, nprobe=16: retention=82.73%, coverage=82.73%. [JSON](../../R2_Audit/p1_reference/results/a3_pic2word.json).
- pic2word, nlist=1024, nprobe=32: retention=90.59%, coverage=90.59%. [JSON](../../R2_Audit/p1_reference/results/a3_pic2word.json).
- pic2word, nlist=1024, nprobe=64: retention=95.18%, coverage=95.18%. [JSON](../../R2_Audit/p1_reference/results/a3_pic2word.json).
- searle, nlist=1024, nprobe=8: retention=80.41%, coverage=80.41%. [JSON](../../R2_Audit/p1_reference/results/a3_searle.json).
- searle, nlist=1024, nprobe=16: retention=87.82%, coverage=87.82%. [JSON](../../R2_Audit/p1_reference/results/a3_searle.json).
- searle, nlist=1024, nprobe=32: retention=93.68%, coverage=93.68%. [JSON](../../R2_Audit/p1_reference/results/a3_searle.json).
- searle, nlist=1024, nprobe=64: retention=97.09%, coverage=97.09%. [JSON](../../R2_Audit/p1_reference/results/a3_searle.json).
