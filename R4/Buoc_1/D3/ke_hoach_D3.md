# D3 — Độ trung tâm của exact neighbor truy vấn CIR

**Trạng thái:** kế hoạch chờ duyệt. Áp dụng [kế hoạch chung Bước 1](../ke_hoach_buoc_1.md) và [feedback R4](../../mentor_feedback_r4.txt).

## Câu hỏi và dự đoán

Trong từng backbone, 10 exact neighbor của query CIR có độ trung tâm chuẩn hóa `a_z` thấp hơn trung bình gallery không? Sau chuẩn hóa riêng từng model, mức lệch có âm hơn ở Pic2Word so với SEARLE không? Đây là **hai câu hỏi**: kiểm tra từng model so với gallery và so sánh khác biệt mức lệch giữa hai model.

## Thiết kế

1. Dùng vector `a_z` của gallery và exact top-10 CIR trên gallery gốc, kiểm tra hash, thứ tự gallery, query ID và cùng dữ liệu/config. Nạp top-10 C4 nếu provenance được xác minh; đối chiếu hoặc tính lại exact IP và kiểm tra ID trong `[0,N)`, 10 ID hợp lệ mỗi query và không lẫn model. Gallery baseline `mean(a_z)` được tính trực tiếp theo định nghĩa, gần 0 về số học.
2. Với mỗi query, tính trung bình `a_z` trên 10 neighbor; lấy trung bình trên query và so với baseline gallery của cùng model. Báo phân vị 10/50/90 của phân phối occurrence và phân phối trung bình theo query, số query, số occurrence và số ảnh khác nhau; phân biệt rõ hai phân phối. Tính thêm phiên bản mỗi ảnh chỉ tính một lần như độ nhạy, không thay thế estimand chính.
3. Bootstrap **query** 2.000 lần, RNG 42, giữ cả 10 neighbor của query và cố định gallery/ground truth đã quan sát; báo CI 95% cho lệch trung bình từng model. Các ảnh có thể lặp ở nhiều query, nên CI không xử lý hết phụ thuộc theo ảnh; báo số ảnh riêng, độ tập trung và độ nhạy theo ảnh nếu khả thi.
4. So chênh lệch `Δ = mean_query(a_z Pic2Word) − mean_query(a_z SEARLE)` và CI: trước hết xác minh hai bộ query tương ứng theo manifest; nếu ghép đúng cùng query thì bootstrap theo **query ghép cặp** giữa model, giữ 10 neighbor của từng model. Nếu không xác minh được pairing, không giả định ghép cặp; báo giới hạn và phương án độ nhạy riêng. `Δ<0` nghĩa là mức trung tâm chuẩn hóa của Pic2Word thấp hơn, không có nghĩa khác biệt backbone là nguyên nhân duy nhất của gain.
5. Bước 0 xác nhận 800/800 vector mới khớp cache cũ trong tolerance nhưng hai query `test:251` và `test:631` có feature khó phân biệt và cache cũ không có ID nguồn. Báo kết quả chính giữ đủ query và **độ nhạy loại cả hai query**, không tự gán lại ID. Kiểm tra validation prefix/target và ghi rõ hạn chế ID lịch sử. Tập query ảnh và so CIR–ảnh là D4/Bước 6, không đưa vào kết luận D3 hiện tại.
6. Phân tích theo model riêng và báo so sánh trực tiếp `Δ` cùng CI; không suy ra khác biệt giữa model từ việc một CI chứa 0 còn CI kia không chứa 0. Chuẩn hóa riêng giúp mô tả vị trí tương đối trong từng gallery, không chứng minh hai backbone có cùng thang hình học hay cùng cấu trúc phân phối.

## Đầu ra và cổng

Lưu `manifest.json`, bảng từng query và từng model, CI, số ảnh riêng/tần suất lặp, kết quả độ nhạy loại hai query, histogram/violin gallery so với exact neighbor và báo cáo. Dừng khi hash, mapping, exact neighbors hoặc pairing không được kiểm chứng; nếu chưa có commit sạch cho script chạy, chỉ gắn nhãn thăm dò. Không coi chênh lệch D3 hay so sánh hai backbone là bằng chứng nhân quả của lợi ích centering.
