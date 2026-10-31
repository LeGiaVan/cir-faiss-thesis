---
name: cir-gee-interaction
description: Hướng dẫn đặt giả thuyết và diễn giải GEE nhị thức cho tương tác giữa centering và s1 trong thực nghiệm CIR–FAISS C5 hoặc phân tích xu hướng tương tự; dùng khi thiết kế, chạy, rà soát hoặc viết báo cáo về hiệu ứng centering theo s1.
---

# GEE cho hiệu ứng centering theo s1

Áp dụng khi phân tích câu hỏi liệu hiệu ứng centering đối với xác suất bỏ sót exact neighbor thay đổi theo `s1` của query. Đọc feedback và preregistration của vòng thực nghiệm liên quan trước khi chọn mục tiêu, phương pháp và cách diễn giải.

## Thiết kế và mô hình

- Với mỗi backbone, chuẩn hóa `s1` theo Z-score trong backbone đó, tính mean và độ lệch chuẩn trên các query duy nhất của tập phân tích; dùng cùng các giá trị chuẩn hóa cho original/centered, mọi seed và neighbor. Ghi tập dùng để chuẩn hóa, giá trị mean/std và quy ước độ lệch chuẩn; kiểm tra std khác 0. Không gộp hai backbone trên thang `s1` thô nếu chưa chứng minh khả năng so sánh.
- Đơn vị Bernoulli là `missed` của một exact neighbor: 1 nếu HNSW bỏ sót, 0 nếu tìm thấy; `centered` là 0 với original, 1 với centered. Mô hình mentor đề xuất là GEE nhị thức, liên kết logit: `logit(p_miss) = β0 + β1*s1z + β2*centered + β3*(centered*s1z)`; gom cụm theo query ID, giữ cả 10 neighbor, seed và hai biến thể trong cùng cụm. Ghi cấu trúc tương quan làm việc, cách tính covariance, kiểm tra hội tụ và số cụm. Bootstrap/cụm theo query không tự xử lý mọi phụ thuộc do ảnh lặp giữa query hoặc các đồ thị dùng chung seed; nêu giới hạn và thực hiện độ nhạy theo thiết kế được duyệt nếu khả thi.
- `β2` là hiệu ứng centering trên log-odds tại `s1z=0`; `β3` là mức thay đổi hiệu ứng log-odds của centering khi `s1z` tăng một độ lệch chuẩn. Tại `s1z=z`, odds ratio centered/original là `exp(β2 + β3*z)`. Đây là tương tác giữa hiệu ứng centering và `s1`, không phải tương quan thống kê giữa biến chỉ báo centering và `s1`.

## Đặt và đánh giá giả thuyết

- Với nghiên cứu mới về xu hướng, không mặc định yêu cầu giá trị trung bình của cả năm quintile giảm đơn điệu từng bậc. Chọn trước estimand, hướng hoặc kiểm định hai phía, mức ý nghĩa, CI, thang đo và quy tắc quyết định. Các nhóm quintile vẫn có thể dùng để mô tả, với số query và CI; khác biệt giữa hai nhóm cần CI/kiểm định trực tiếp.
- Nếu tiên đoán centering giảm odds bỏ sót mạnh hơn ở `s1` thấp và hiệu ứng yếu dần khi `s1` tăng, với mã `missed=1`, `centered=1` thì hướng tương tác dự đoán là `β3 > 0` trên thang log-odds. Kiểm tra lại định nghĩa mã hóa và giả thuyết trước khi đặt hướng; không áp đặt dấu này cho các câu hỏi hoặc thang đo khác.
- Nếu câu hỏi là hiệu ứng tương đối có gần đồng đều giữa các giá trị `s1` hay không, báo `β3`, CI 95%, p-value và `exp(β3)` kèm CI. `p > 0,05` hoặc CI chứa 0 chỉ nghĩa là chưa đủ bằng chứng về tương tác theo kiểm định đó; không chứng minh `β3=0` hoặc đồng đều. Muốn kết luận tương đương thực tế, xác định trước miền tương đương có ý nghĩa và dùng kiểm định/CI phù hợp; nếu CI rộng, báo chưa kết luận.
- Odds ratio không đồng nhất với risk ratio hay phần trăm giảm miss. Báo riêng miss gốc/sau, chênh lệch tuyệt đối và giảm tương đối `(miss_before − miss_after)/miss_before` theo nhóm khi cần, nêu rõ đơn vị phân tích và xử lý mẫu số bằng 0. Hiệu ứng odds đồng nhất không đảm bảo hiệu ứng tuyệt đối hay risk ratio đồng nhất.

## Tính toàn vẹn kết quả R3 và so sánh chi phí

- Giữ nguyên quy tắc C5 R3 đã đăng ký: trung bình gain của năm nhóm không tăng và CI chênh lệch nhóm thấp nhất trừ cao nhất dương. Không thay quy tắc đó sau khi đã xem kết quả; GEE R4 và quy tắc mới được ghi rõ là phân tích bổ sung dựa trên kết quả đã quan sát, trừ khi có dữ liệu xác nhận độc lập và đăng ký trước riêng.
- So tại cùng `efSearch` không đảm bảo cùng `ndis`. Đối chiếu với C1 tại cùng ngân sách; nội suy retention từng query/seed chỉ trong miền `ndis` chung và nêu rằng `ndis` trong C1 là trung bình toàn query. Giá trị nội suy là fractional estimate, không phải quan sát `missed` nhị thức: không đưa trực tiếp vào GEE Bernoulli. Nếu muốn phân tích GEE ở cùng chi phí cần thiết kế và dữ liệu nhị thức thực đo phù hợp.
- Đối chiếu các giá trị trong báo cáo với JSON, manifest và dữ liệu đã khóa; nêu hạn chế query ID test, thay đổi đồ thị/chi phí, số seed và phụ thuộc theo ảnh. Trình bày kết quả âm tính hoặc bất định trung thực; không xem tương tác hay tương quan là bằng chứng nhân quả.
