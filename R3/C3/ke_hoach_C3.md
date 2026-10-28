# C3 — Kế hoạch đối chứng L2

Câu hỏi: khi trừ cùng mean gallery khỏi cả gallery và query, khoảng cách L2, exact top-10 và retention HNSW L2 có thay đổi do sai số số học và quá trình dựng đồ thị hay không? Đây là kiểm tra đối chứng, không giả định HNSW phải giống tuyệt đối.

Dùng dữ liệu và hash đã khóa của C1, CIRCO 1.020 query và 123.403 gallery, SEARLE và Pic2Word. Chuẩn hóa vector như C1; tính `mu` trên gallery đã chuẩn hóa. Hai nhánh là `(gallery, query)` và `(gallery-mu, query-mu)`, cùng `METRIC_L2`, `M=32`, `efConstruction=200`, `efSearch=128`, 5 seed. Tính exact L2 top-10 riêng từng nhánh, so ID, sai số khoảng cách của top-10 và 10.000 cặp query–gallery được chọn ngẫu nhiên có seed 42. Ngưỡng kiểm tra khoảng cách tuyệt đối `1e-5` cho squared L2 được xác định trước khi chạy; nếu vượt ngưỡng hoặc exact top-10 không giống, dừng trước khi diễn giải, ghi lỗi để điều tra near-tie và precision.

Đo retention@10, ndis/query và số cạnh tầng 0 của từng seed, lưu per-query và provenance; bootstrap chéo seed/query 2.000 lần cho chênh lệch retention có ghép cặp. CI chứa 0 không chứng minh tính tương đương; sai khác có thể do số học và dựng HNSW đa luồng. Báo rõ độ lệch và không suy luận nhân quả chỉ từ đối chứng. Giữ kết quả C1 riêng; dựng cả hai nhánh trong cùng điều kiện C3 để so sánh nhất quán.

C3 được xếp chạy sau C2 để không gây nhiễu latency C2. Kết quả gồm manifest, checkpoint, JSON, bảng theo seed và báo cáo; không kết luận trước khi kiểm tra exact và xem số liệu thực tế.
