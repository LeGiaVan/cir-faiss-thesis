# D2 — Độ trung tâm, norm centered và N10 phía gallery

**Trạng thái:** kế hoạch chờ duyệt. Áp dụng [kế hoạch chung Bước 1](../ke_hoach_buoc_1.md) và [feedback R4](../../mentor_feedback_r4.txt).

## Câu hỏi và dự đoán

Trong từng backbone, ảnh trung tâm có thường là exact neighbor của các ảnh gallery khác không; sau centering, ảnh có norm centered lớn có xuất hiện thường hơn không? Dự đoán mentor: `ρ(a, N10_gallery_original)>0` và `ρ(||x−μ||, N10_gallery_centered)>0`.

`N10_gallery(j)` là số ảnh gallery khác chọn ảnh `j` trong 10 láng giềng exact; **không phải** in-degree của HNSW hoặc số query CIR chọn ảnh đó. Chỉ mục IP centered không normalize lại. Norm centered trong công thức được tính từ vector gallery, không từ query CIR.

## Thiết kế

1. Nạp `a` và norm centered từ bước chung; đối chiếu phép tính norm trực tiếp với `1−2ma+m²` trong tolerance được khóa. Nạp vector N10 gốc/sau từ C4 chỉ khi signature/hash, model, gallery order và định nghĩa IP khớp; xác minh 123.403 giá trị không âm, tổng mỗi vector bằng `10N`, `k=10` và self đã bị loại theo ID. Nếu provenance hoặc phép kiểm tra không đạt, dừng; thiết kế/tính lại exact có checkpoint trước khi thay thế.
2. Tính hai tương quan Spearman cho từng model, báo số lượng ties, CI mô tả và toàn bộ thống kê kiểm tra. Bổ sung skewness, số/tỷ lệ `N10=0`, phần vị và max để nhận diện thay đổi phân phối; không coi giảm `N10=0` tương đương giảm skewness hoặc chứng minh cải thiện chất lượng retrieval.
3. Bootstrap ảnh 2.000 lần với RNG 42 để tạo CI **mô tả có điều kiện**; các N10 cùng phát sinh từ một gallery nên không coi ảnh là các quan sát độc lập tuyệt đối. Đối chiếu bằng đồ thị phân vị/binned và báo đủ bốn tương quan chính ở hai model. Nếu báo p-value, nêu tập kiểm định và cách hiệu chỉnh, không chọn lọc sau khi thấy kết quả.

## Đầu ra và cổng

`manifest.json`, bảng tương quan/CI/ties theo model, thống kê N10 trước/sau, hình độ trung tâm/norm với N10 và báo cáo đánh giá từng dự đoán. Dừng khi lỗi hash/order, thiếu N10 hoặc tổng `10N` không khớp. Snapshot code trích xuất Bước 0 không tự xác nhận code D2; khóa đúng script/config vào commit sạch trước khi gắn nhãn confirmatory.
