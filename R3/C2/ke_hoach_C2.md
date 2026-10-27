# Kế hoạch C2: Centering so với tăng mật độ đồ thị gốc

**Trạng thái: đề xuất, chờ duyệt.** Tài liệu này chỉ mô tả phương án; chưa dựng đồ thị, viết mã thực nghiệm hay chạy C2. Nguồn: [feedback mentor R3](../mentor_feedback_R3.md), [kế hoạch R3](../R3_execution_plan.md), [đăng ký trước](../stage0_preregistration.md) và [kết quả C1](../C1/bao_cao_C1.md).

## 1. Câu hỏi và mục tiêu

C1 cho thấy centering cải thiện retention của Pic2Word trong các ngân sách `ndis` đã khảo sát; SEARLE chưa có bằng chứng cải thiện. C2 kiểm tra liệu tăng `M` cho HNSW trên gallery gốc có đạt kết quả tương tự centering khi **số cạnh thực tế gần nhau và chi phí tìm kiếm `ndis/query` tương đương** hay không. Đây là phép đối chiếu thực nghiệm để đánh giá lời giải thích về mật độ, không tự chứng minh cơ chế nhân quả.

## 2. Giả thuyết và quy tắc đã đăng ký

- So sánh centered IP `M=32` với original IP có `M` thuộc `{32, 40, 48, 64}`; không giả định trước giá trị `M` nào khớp.
- Nếu một mức original có số cạnh gần centered và retention tương tự tại cùng `ndis`, kết quả phù hợp với khả năng tăng mật độ có thể tạo hiệu quả tương tự. CI chứa 0 không tự chứng minh hai phương án tương đương; cần báo độ lớn và độ rộng CI.
- Nếu tại cùng ngân sách, centered cao hơn original đã khớp số cạnh và CI ghép cặp của chênh lệch hoàn toàn dương, dữ liệu ủng hộ lợi thế bổ sung trong cấu hình khảo sát. Không gọi đây là chứng minh cơ chế hình học.
- Theo đăng ký trước, chỉ gọi là **khớp mật độ theo tiêu chí C2** khi median số cạnh của mức original lệch không quá 2% so với median của centered `M=32`. Chọn mức có sai lệch tuyệt đối nhỏ nhất, xử lý hòa bằng `M` nhỏ hơn. Nếu không đạt ngưỡng, báo mức gần nhất và chênh lệch thực tế; kết luận là so sánh **xấp xỉ**, không gọi cùng mật độ.

## 3. Dữ liệu và cấu hình

- CIRCO, 123.403 gallery và 1.020 query cho mỗi backbone: SEARLE 512 chiều và Pic2Word 768 chiều. Dùng cùng embeddings, cache query, thứ tự hàng, chuẩn hóa và ground truth exact IP như C1; kiểm tra hash theo [manifest C1](../C1/run_manifest.json) trước khi chạy.
- HNSWFlat inner product, `efConstruction=200`, seed `[42, 43, 44, 45, 46]`, `k=10`. Original dùng gallery gốc với bốn mức `M`; centered dùng `M=32`, gallery trừ mean, không chuẩn hóa lại, query giữ nguyên.
- Quét `efSearch=[32,48,64,96,128,160,192,256,384]` cho từng đồ thị; ghi retention từng query, `ndis/query` và latency. Latency theo reference: một lần khởi động, bảy lần đo, batch một; báo median và các lần đo, kèm phần cứng và số luồng.
- Kiểm tra exact top-10 original/centered giống nhau; nếu không khớp thì dừng và điều tra tie/sai số trước khi diễn giải.

## 4. Đo và ghép số cạnh

1. Đếm **cạnh có hướng hợp lệ ở tầng 0** trực tiếp từ danh sách láng giềng FAISS, không tính ô trống `-1`. Ghi rõ định nghĩa, tổng cạnh, số nút và trung bình cạnh ra mỗi nút. Kiểm tra tổng bậc vào bằng tổng bậc ra; không dùng số slot cấp phát thay cho số cạnh.
2. Lưu số cạnh cho từng model, seed, `M` và biến thể; báo median, từng seed và tỷ lệ sai lệch so với centered `M=32`. Chọn `M` riêng cho từng backbone theo quy tắc ở Mục 2, trước khi xem chênh lệch retention của C2.
3. Checkpoint C1 lưu kết quả tìm kiếm nhưng không lưu đồ thị hoặc số cạnh, nên **không thể suy ra chính xác số cạnh của những đồ thị C1**. Dựng lại centered `M=32` và original `M=32` để đo số cạnh gắn với chính kết quả tìm kiếm C2. Báo C1 làm tham chiếu riêng; không coi lượt dựng mới là cùng đồ thị C1, vì dựng đa luồng có thể biến thiên.
4. Khớp theo median không bảo đảm từng cặp seed có cùng số cạnh; báo sai lệch theo seed và tránh kết luận mạnh nếu sai lệch lớn hoặc biến thiên giữa seed đáng kể.

## 5. So sánh retention tại cùng chi phí

- Với mỗi backbone, so centered `M=32` với original ở mức `M` được chọn. Có thể trình bày thêm các mức `M` còn lại để thấy đánh đổi, nhưng không thay đổi lựa chọn chính sau khi xem retention.
- Tìm miền giao `ndis` của toàn bộ đường cần so sánh theo seed; trong miền đó lấy 5 ngân sách cách đều theo log. Nội suy tuyến tính retention từng query và seed theo `ndis`, không ngoại suy. Báo độ nhạy của ước lượng khi nội suy theo log `ndis` và trường hợp không có miền chung.
- Ước lượng `retention centered − retention original` tại từng ngân sách. Bootstrap 2.000 lần, lấy mẫu lại ghép cặp theo seed và query; báo CI percentile 95%, từng seed và mức sai lệch cạnh. Xem seed cùng số là cặp thí nghiệm, không giả định chúng tạo đồ thị tương ứng từng cạnh; giữ `ndis` đo được cố định trong bootstrap.
- Nếu không có miền `ndis` chung, báo số cạnh và các điểm đo trực tiếp, nêu rõ không thể kết luận so sánh cùng chi phí theo thiết kế này.

## 6. Đầu ra dự kiến

Trong thư mục `C2`, tạo mã chạy/phân tích và manifest kèm hash input, script, cấu hình, phiên bản thư viện, CPU, số luồng, trạng thái working tree; lưu checkpoint riêng theo model/seed/biến thể/`M`, dữ liệu per-query và JSON tổng hợp.

1. Bảng số cạnh thực tế cho từng seed và median theo `M`, kèm tỷ lệ lệch và dấu mức được chọn.
2. Bảng grid search: `M`, seed, `efSearch`, retention, `ndis/query`, latency; bảng riêng so sánh tại 5 mức `ndis` chung, chênh lệch và CI.
3. Hình cho từng backbone: retention theo `ndis` của centered `M=32` và original ở mức `M` được chọn; thể hiện seed, ngân sách chung và chênh lệch kèm CI. Hình phụ thể hiện các mức `M` còn lại và số cạnh thực tế.
4. Báo cáo theo cấu trúc câu hỏi, giả thuyết, thiết kế, kết quả, kết luận, hạn chế và bước tiếp theo. Mọi số trong báo cáo/hình lấy từ dữ liệu kết quả; phân biệt rõ trường hợp khớp trong 2% với trường hợp chỉ gần nhất.

## 7. Giới hạn và điều kiện dừng

Workspace hiện dirty; ghi lại hash và provenance, không dọn hoặc sửa dữ liệu cũ. ID nguồn của 800 test query chưa xác minh độc lập từng hàng; ghép cặp theo thứ tự feature đã cố định, không khẳng định ánh xạ ID. Năm seed và nội suy giới hạn độ chắc chắn; các CI tại nhiều ngân sách không phải CI đồng thời. Nếu hash input thay đổi, exact ranking không khớp, đếm cạnh không nhất quán hoặc checkpoint thiếu provenance, dừng phân tích và báo rõ trước khi diễn giải.
