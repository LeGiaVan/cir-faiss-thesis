# Bước 0: kiểm định provenance trước khi trích lại

Tài liệu này khóa trước các ngưỡng đối chiếu, trước khi xem kết quả trích xuất mới. Không ghi đè query cache R2/R3.

- Trích lại từng batch, gắn trực tiếp `test:<annotation id>`, reference image ID, caption và vector tương ứng; kiểm tra đủ 800 ID duy nhất theo đúng annotation. Mỗi batch lưu checkpoint riêng, kèm chữ ký mã/đầu vào, có thể tiếp tục.
- Đối chiếu validation: 220 feature prefix với cache validation, thứ tự target ID với annotation và cấu trúc ID của manifest R2. Test cache cũ không có ID nguồn: so từng hàng mới theo annotation order với hàng cũ để kiểm tra giả định, không nói so sánh này chứng minh tính lịch sử nếu encoder/weights khác.
- Đối chiếu vector đã L2-normalize theo từng dòng: cosine tối thiểu `0.99999` và sai số tuyệt đối mỗi tọa độ tối đa `1e-4`; báo cả phân phối, số dòng không đạt và sai khác norm. Đây là ngưỡng kiểm tra thực dụng cho phép tính FP32 qua môi trường/batch, không phải khẳng định mọi khác biệt trong ngưỡng vô hại.
- Nếu có dòng vượt ngưỡng hoặc khác thứ tự, điều tra nguồn, so exact top-10 và retention trực tiếp của vector mới/cũ; không tự gán lại ID cũ theo kết quả gần nhất. Không tiếp tục gọi kết quả R3 là xác nhận lại nếu chưa có bằng chứng.
- Ghi hash từng input, model/CLIP weights, encoder source và môi trường. Snapshot nguồn riêng chỉ áp dụng cho các mã thực sự nằm trong snapshot; dependency ngoài snapshot phải ghi hash và phiên bản, không gọi toàn bộ môi trường là clean commit.
