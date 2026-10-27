# Kế hoạch thực hiện C1: retention ở cùng chi phí tìm kiếm

Tài liệu này được viết trước khi chạy C1. Thiết kế và dự đoán kế thừa [đăng ký trước Chặng 0](../stage0_preregistration.md); nguồn yêu cầu là [feedback R3](../mentor_feedback_R3.md) và [kế hoạch R3](../R3_execution_plan.md).

## Câu hỏi và dự đoán

Trên từng backbone SEARLE và Pic2Word, centering gallery có cải thiện retention@10 tại cùng số phép tính khoảng cách trung bình trên mỗi query (`ndis/query`) hay không? Dự đoán đã đăng ký: chênh lệch của Pic2Word có thể nhỏ đi khi khớp chi phí; hiệu ứng của SEARLE có thể nhỏ hơn Pic2Word. Không giả định hiệu ứng dương.

## Các bước thực hiện

1. Kiểm tra môi trường, dữ liệu, query cache, cấu hình, hash và giới hạn provenance của snapshot Chặng 0; ghi nhận mọi thay đổi và điều kiện chạy. Không ghi đè kết quả cũ.
2. Dựng HNSW với `M=32`, `efConstruction=200`, năm seed 42–46 cho mỗi model: gallery gốc IP; gallery trừ mean IP không chuẩn hóa lại; gallery trừ mean L2, đồng thời trừ mean khỏi query. Kiểm tra exact top-10 và tính bất biến thứ hạng IP trước khi phân tích. L2 là đường đối chứng sơ bộ; kiểm định đầy đủ thuộc C3.
3. Quét `efSearch=[32,48,64,96,128,160,192,256,384]`, lưu ID hàng xóm và retention từng query, `ndis/query`, độ trễ, seed, cấu hình, môi trường và provenance. Đo latency theo cấu hình reference; `ndis` là kết quả chính.
4. Với từng model, so centered IP và original IP tại năm ngân sách cách đều theo log trong miền `ndis` chung, nội suy tuyến tính giữa điểm đo kề nhau, không ngoại suy. Bootstrap ghép cặp theo seed và query 2.000 lần; báo CI, từng seed và độ nhạy nội suy.
5. Lưu dữ liệu theo seed, JSON tổng hợp, bảng retention/ndis/latency và chênh lệch cùng ngân sách, hình retention–ndis và báo cáo có thể truy vết. Đối chiếu trực tiếp với đầu ra; ghi rõ các giới hạn, kết quả âm tính và kiểm tra chưa thực hiện.

## Quy tắc kết luận

Chỉ nói có bằng chứng cải thiện tại ngân sách khảo sát nếu chênh lệch centered trừ original dương và CI ghép cặp hỗ trợ mức tăng. Nếu CI chứa 0, kết luận chưa có bằng chứng cải thiện tại ngân sách đó. Không diễn giải đường L2 là kiểm định hoàn chỉnh C3 khi chưa so với L2 gốc và kiểm tra bất biến. Không suy diễn nhân quả hay mở rộng ngoài cấu hình khảo sát.
