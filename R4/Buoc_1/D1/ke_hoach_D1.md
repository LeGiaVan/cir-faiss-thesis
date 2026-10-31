# D1 — Độ trung tâm và bậc vào HNSW

**Trạng thái:** kế hoạch chờ duyệt. Áp dụng [kế hoạch chung Bước 1](../ke_hoach_buoc_1.md) và [feedback R4](../../mentor_feedback_r4.txt).

## Câu hỏi và dự đoán

Với từng backbone, độ trung tâm `a_j` của ảnh gallery có liên hệ với bậc vào HNSW trước/sau centering không? Dự đoán mentor: `ρ(a, indeg_original)>0`, `ρ(a, indeg_centered)<0`, và `ρ(a, indeg_centered−indeg_original)<0`. Từ “mạnh” trong feedback chưa có ngưỡng định lượng; không tự gán ngưỡng sau khi xem kết quả. Báo hệ số và độ bất định thay vì kết luận chỉ từ p-value.

## Thiết kế

1. Tính `a` từ gallery đơn vị theo kế hoạch chung. Dùng checkpoint C4/R2 có chữ ký khớp, in-degree có hướng tầng 0 và đồ thị original/centered cùng seed 42–46. Kiểm tra số hàng, thứ tự gallery ID, cạnh hợp lệ và tổng in-degree = tổng out-degree. Lưu nguồn/hash từng checkpoint; không ghép chỉ số từ các lượt dựng khác nhau.
2. Với từng model và seed, tính ba tương quan Spearman nói trên; báo số nút, số giá trị hòa, phân vị của `a`, in-degree và thay đổi in-degree. Vẽ scatter có lấy mẫu cố định hoặc binned/hexbin để không làm mất đuôi phân phối; biểu đồ binned chỉ minh họa, không thay thế tương quan toàn bộ gallery.
3. Báo 5 seed và trung bình/trung vị hệ số. Dùng bootstrap ảnh có seed và số lần khóa trước trong preregistration (mặc định theo R4: 2.000 lần, seed RNG 42) để mô tả CI có điều kiện trên gallery/đồ thị đã đo; báo độ nhạy theo seed riêng. Các nút liên kết trong cùng đồ thị, nên CI bootstrap ảnh không tự xử lý toàn bộ phụ thuộc. Không coi các seed hoặc ảnh là xác nhận độc lập ngoài tập CIRCO.
4. Có sáu tương quan chính ở hai model, mỗi tương quan có năm seed: công bố toàn bộ thay vì chọn kết quả thuận lợi. Nếu báo p-value, ghi rõ tập kiểm định và cách hiệu chỉnh; CI theo từng phép không phải CI đồng thời. Không khẳng định dấu đảo nếu CI/biến thiên seed còn không rõ.

## Đầu ra và cổng

`manifest.json`; vector/bảng có hash; bảng `model, seed, variant, rho, CI, n, ties`; bảng tóm tắt dấu và biến thiên theo seed; hình độ trung tâm–bậc vào; báo cáo mô tả kết quả và giới hạn. Dừng khi input hash/chữ ký không khớp, không xác minh được thứ tự ảnh hoặc kiểm tra tổng bậc thất bại. Kết quả chỉ xác nhận khi script thực thi thuộc commit sạch bao phủ đúng nguồn; nếu không thì gắn nhãn thăm dò.
