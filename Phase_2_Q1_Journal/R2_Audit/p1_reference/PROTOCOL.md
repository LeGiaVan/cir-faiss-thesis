# Giao thức P1 và phạm vi chạy lại

Nguồn cấu hình duy nhất: [reference.yaml](../../../configs/reference.yaml). Mã dùng chung: [protocol.py](../../../src/phase2/protocol.py). Đường dẫn trong hai link này được tính từ thư mục `p1_reference` (gốc repo ở ba cấp trên).

## 1. Cấu hình và phân tách dữ liệu

- HNSW reference/stress lấy từ YAML; profile hiện chạy A.1 là reference.
- A.1 phân tích neighbor-level/retention trên val+test; phép đo có ground truth trong A.2/A.3 và anchor latency dùng val. Không dùng test không có nhãn để tự tính mAP.
- A.2/A.3 reference dùng nlist/nprobe trong YAML, khác cấu hình legacy. Dữ liệu cũ được giữ nguyên; các kết quả mới ghi vào `p1_reference/results/` hoặc A.1 R2.
- Mỗi JSON mới ghi cấu hình đã resolve, hash config, hash đầu vào, source-tree hash, git commit và trạng thái dirty, package versions, hardware và số FAISS threads thực tế. Hash code là cần thiết vì nhiều file mới chưa thuộc commit.
- Không coi commit đơn lẻ là đủ tái lập workspace dirty. Giữ các script/config cùng artifact; hash chỉ kiểm tra phiên bản, không thay thế việc lưu mã.

## 2. Định nghĩa RC/LID

RC = trung bình khoảng cách cosine của các cặp gallery non-self ngẫu nhiên / trung bình khoảng cách cosine tới nearest non-self của mẫu gallery. Đây là tỷ số của hai trung bình, không phải trung bình của các tỷ số. Lấy mẫu, k và số cặp nằm trong YAML; self bị loại theo ID.

LID dùng Euclidean chord trên vector đơn vị: `T = sqrt(2 * max(1 - dot, 0))`. Với k láng giềng non-self, ước lượng mỗi điểm bằng `(k - 1) / sum_{j<k} ln(T_k/T_j)`; báo mean/median trên các neighborhood hợp lệ. Loại neighborhood có khoảng cách không dương hoặc mẫu số không dương/không hữu hạn, và báo số bị loại. Không cắt LID theo số chiều embedding.

Code legacy dùng `1 - cosine` cho LID, là bình phương khoảng cách chord chia hai. Điều này làm khác thang ước lượng; số liệu mới cũng có thể khác do sample size, seed và xử lý zero-distance. Không gán định nghĩa mới cho số legacy, không khẳng định đã giải thích toàn bộ sai khác với bài ICRCV nếu thiếu giao thức gốc của bài.

## 3. Giao thức độ trễ

Một lượt warm-up, bảy lượt đo; mỗi lượt chạy hết tập query, batch query=1. Lưu ms/query từng lượt, median, standard deviation và phạm vi phép đo (gồm overhead vòng lặp gọi search). Đây là latency từng query, khác throughput batch của các phép tìm exact phục vụ phân tích. Cố định số luồng theo YAML; không chạy đồng thời hai benchmark nặng khi đo.

A.4 P1 chỉ chạy lại anchor trên gallery gốc cho hai mô hình. Chuỗi gallery mở rộng 250K/500K vẫn là legacy chưa nghiệm thu vì provenance distractor chưa đủ; không tái công bố dưới nhãn reference. P3a sẽ xử lý distractor, mAP và matched retention. Chênh lệch latency legacy/ICRCV không thể quy hết cho thuật toán khi metadata phần cứng/batch/threads lịch sử thiếu.

## 4. A.1 và centering

Neighbor table và hồi quy dùng seed reference đầu tiên. Centering dùng năm seed, mỗi seed dựng before/after riêng, giữ query và không chuẩn hóa lại gallery centered. Mọi query đều được kiểm tra exact top-k và đẳng thức dịch điểm. In-degree/out-degree tầng 0 được đo cho mỗi đồ thị; tổng bậc vào phải bằng tổng bậc ra.

CI delta retention lấy mẫu lại cặp seed và query theo hai trục, giữ cặp before/after. Năm lần dựng chưa đủ khẳng định ổn định ở mọi cấu hình; nguồn phụ thuộc do cùng ảnh ở nhiều query chưa được loại bỏ. GEE dùng robust sandwich SE theo query và phải hội tụ trước khi lưu.

ID val được xác minh bằng prefix feature và thứ tự GT. ID test được tái dựng từ mã extraction và thứ tự annotation vì bundle cũ không lưu ID từng hàng; ghi hạn chế này trong manifest, không trình bày như bằng chứng độc lập đã xác minh toàn bộ embedding test.

## 5. Lệnh tái tạo từ gốc repo

```powershell
python Phase_2_Q1_Journal/R2_Audit/scripts/render_p0_reports.py
python Phase_2_Q1_Journal/R2_Audit/scripts/check_protocol.py
python Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/run_reference_audit.py
python Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/step2_descriptive_bootstrap.py
python Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/step3_nested_logistic.py
python Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/step5_render_report.py
python Phase_2_Q1_Journal/R2_Audit/scripts/run_p1_reference.py --modules a2 a3 a4 a5
```

`render_p0_reports.py` tái tạo các báo cáo legacy đã sửa. Sau khi chạy lại renderer này, dùng `run_p1_reference.py --render-only` để gắn lại phần kết quả P1 hiện có. Mã Stage A cũ đã chuyển entrypoint sang pipeline chuẩn; các renderer văn phong cũ đã ngừng dùng. Không chạy lại script migration một cách thường xuyên; code trước sửa được lưu trong archive.
