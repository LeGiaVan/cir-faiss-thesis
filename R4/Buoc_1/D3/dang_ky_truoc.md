# D3 — Đăng ký phân tích trước khi tính kết quả

**Phạm vi:** phân tích R4 bổ sung được đề xuất sau khi đã xem R3; không phải dự đoán độc lập được đăng ký trước R3. Nguồn: [kế hoạch D3](./ke_hoach_D3.md), [Bước 1](../ke_hoach_buoc_1.md) và [feedback R4](../../mentor_feedback_r4.txt).

## Câu hỏi và đại lượng chính

Với từng backbone, dự đoán trung bình `a_z` của exact top-10 CIR thấp hơn trung bình `a_z` toàn gallery. Sau chuẩn hóa độ trung tâm **riêng trong từng model**, dự đoán mức lệch Pic2Word âm hơn SEARLE.

Với query `q` và model `m`, đặt `T_m(q) = mean(a_z[j] for j in exact_top10_m(q))`; ước lượng chính là `mean_q T_m(q) − mean_gallery(a_z_m)`. So sánh giữa backbone là `Δ = [mean_q T_P(q) − mean_gallery(a_z_P)] − [mean_q T_S(q) − mean_gallery(a_z_S)]`. Đây là chênh lệch hai vị trí tương đối sau chuẩn hóa, không giả định hai không gian embedding có cùng đơn vị hình học.

## Dữ liệu và kiểm tra

- Dùng gallery CIRCO 123.403 ảnh, 1.020 query/model (220 val + 800 test), same gallery/order/query caches như C4/R3. Kiểm tra SHA-256 input/manifest, chữ ký C4 và hash `a_z` với manifest D1; kiểm tra mọi ID neighbor hợp lệ, không trùng trong từng top-10.
- Tính lại exact IP top-10 từ gallery L2-normalize và query cache L2-normalize theo cùng FAISS/reference. So từng ID với top-10 C4; nếu có sai khác, dừng điều tra tie/sai số trước khi phân tích, không im lặng thay truth. Dùng cùng quy tắc không tự loại reference image như pipeline C4; phép kiểm tra này chỉ có nghĩa theo chính thiết kế đó.
- Khóa thứ tự query theo annotation và query manifest R2; xác minh validation feature prefix/target theo annotation, so hash input và báo cáo so sánh 800 query của Bước 0. Chỉ dùng bootstrap ghép cặp hai backbone khi cả hai cùng query manifest và kiểm tra Bước 0 đạt. Cache cũ không có source ID từng hàng; `test:251` và `test:631` có cùng ảnh tham chiếu/caption và feature khó phân biệt. Ghi đây là bằng chứng nhất quán theo vị trí, không phải chứng minh lịch sử tuyệt đối.

## Độ bất định và quy tắc quyết định

Bootstrap 2.000 lần, RNG seed 42, lấy mẫu theo query ghép cặp giữa hai backbone; giữ 10 neighbor của mỗi query và cố định gallery. CI percentile 95% cho ước lượng từng model và `Δ`. Không xem 10 neighbor, hai bản duplicate hay các ảnh lặp giữa query là các mẫu hoàn toàn độc lập. Bootstrap query không loại bỏ toàn bộ phụ thuộc do ảnh xuất hiện ở nhiều query; không điều chỉnh cho nhiều phép so sánh.

- Với từng model, gọi hướng ngoại vi **phù hợp với dự đoán trên tập đã khảo sát** nếu ước lượng <0 và CI 95% hoàn toàn âm; CI chứa 0 là chưa kết luận; CI hoàn toàn dương không ủng hộ hướng dự đoán.
- Với `Δ`, quy tắc tương tự: CI hoàn toàn âm phù hợp với dự đoán Pic2Word ngoại vi tương đối hơn; CI chứa 0 không chứng minh hai model tương đương. Không suy khác biệt giữa model chỉ từ hai CI riêng.
- Bắt buộc báo cả kết quả chính 1.020 query và độ nhạy loại `test:251`, `test:631` còn 1.018 query; không bỏ một query hoặc đổi kết quả chính sau khi thấy số liệu. Giải thích hai ID có cùng reference/caption trong annotation CIRCO và được trích xuất mới kèm ID.
- Báo số ảnh duy nhất, số occurrence, phân vị 10/50/90 của occurrence và của trung bình query; báo trung bình `a_z` tính theo tập ảnh duy nhất như độ nhạy mô tả, không thay thế estimand theo query. Nếu cần suy luận theo cụm ảnh đầy đủ, thiết kế bổ sung và ghi hạn chế thay vì coi bootstrap query đã xử lý xong.

## Đầu ra và provenance

Trước khi phân tích, khóa script và đăng ký này trong source snapshot commit sạch. Lưu hash gallery/query, D1 vector, query manifest, Bước 0 comparison, C4 truth/manifest và source config; dữ liệu/dependency ngoài commit phải ghi riêng. Xuất JSON, manifest, bảng từng query, bảng ảnh/tần suất lặp, hình phân phối và báo cáo có thể kiểm tra lại. Nếu hash, exact IDs hoặc pairing không khớp, dừng. Không suy diễn D3 là nguyên nhân duy nhất của gain hay xem D3 như đối chứng query ảnh D4.
