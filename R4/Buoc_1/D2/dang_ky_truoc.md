# D2 — Đăng ký phân tích trước khi tính tương quan

**Phạm vi:** phân tích bổ sung theo feedback R4 sau khi đã biết kết quả tổng hợp R3; không phải dự đoán được đăng ký độc lập trước R3. Nguồn: [kế hoạch D2](./ke_hoach_D2.md), [Bước 1](../ke_hoach_buoc_1.md) và [feedback R4](../../mentor_feedback_r4.txt).

## Câu hỏi và dự đoán

Với từng backbone trên toàn gallery CIRCO, dự đoán Spearman midrank `ρ(a, N10_gallery_original)>0` và `ρ(||x−μ||, N10_gallery_centered)>0`. `N10_gallery` đếm số ảnh gallery khác chọn một ảnh trong exact top-10 IP; không phải in-degree HNSW hay số query CIR. Trước centering dùng gallery L2-normalize; sau centering, cả query gallery và index dùng `x−μ` **không normalize lại**, loại self theo ID.

## Dữ liệu và kiểm tra

- Dùng `a`, norm centered và `μ` được tạo ở D1, kiểm tra hash với manifest D1, hash gallery với manifest R3/C4 và shape/hữu hạn. Đối chiếu norm với `1−2ma+m²`; ngưỡng sai số squared L2 tuyệt đối `2e-6`, giống ngưỡng đã khóa D1.
- Chỉ dùng N10 C4 khi signature trùng manifest C4, code tính C4 có SHA-256 như trong manifest, data gallery trùng snapshot, N10 123.403 số nguyên không âm có tổng `10N`, và progress checkpoint hoàn tất có signature/đếm trùng file cuối. Đối chiếu thống kê C4 đã lưu: sum, k=10, self-removal theo ID, skewness, tỷ lệ bằng 0 và max.
- Kiểm tra bổ sung 128 ảnh query gallery chọn ngẫu nhiên bằng RNG 42: tìm lại exact top-11, loại self theo ID và bảo đảm đóng góp của mẫu vào mỗi N10 không lớn hơn tổng N10 tương ứng. Đây chỉ là kiểm tra mẫu, không chứng minh toàn bộ N10 đúng.
- Checkpoint C4 không lưu danh sách exact neighbor cho từng ảnh và manifest R3 không khóa hash riêng của vector N10 tại thời điểm tạo. Vì vậy các kiểm tra signature, tiến độ và thống kê chỉ chứng minh tính nhất quán với nguồn đã ghi; **không xác minh độc lập từng lần loại self hay chứng minh vector N10 chưa từng thay đổi**. Ghi rõ giới hạn và hash thực tế của từng vector ở thời điểm D2; nếu bất kỳ kiểm tra bắt buộc thất bại thì dừng, không tự diễn giải.

## Phân tích và quy tắc đánh giá

- Báo đủ bốn hệ số (2 model × 2 biến), số ảnh, số giá trị hòa, CI percentile 95% từ 2.000 bootstrap ảnh, RNG 42; dùng Spearman midrank và tính lại ranks có ties ở mỗi mẫu bootstrap. Bản vẽ phân nhóm chỉ minh họa; hệ số chính tính trên toàn gallery.
- Một dự đoán được gọi **phù hợp trên gallery khảo sát** nếu ước lượng dương và CI bootstrap mô tả của nó hoàn toàn dương; CI chứa 0 thì chưa kết luận, CI hoàn toàn âm thì không ủng hộ hướng dương. Quy tắc này chỉ mang tính mô tả có điều kiện; không báo p-value hay coi 4 CI là đồng thời.
- Các ảnh không độc lập vì N10 được tính từ cùng tập gallery, do đó bootstrap ảnh không nắm bắt đầy đủ phụ thuộc và không tự cho phép suy rộng ngoài gallery. Không gọi hệ số tương quan là tác động nhân quả.
- Báo skewness, số/tỷ lệ `N10=0`, phân vị và max như thống kê mô tả riêng. Không xem giảm `N10=0`, thay đổi skewness và chất lượng truy hồi là cùng một đại lượng.

## Đầu ra

Khóa script và đăng ký này trong snapshot có commit sạch trước khi phân tích; lưu hash input/script/config và nguồn dependency trong manifest. Tạo JSON, bảng CSV, hình và báo cáo dựa trực tiếp trên kết quả. Không dùng ID của test query trong D2 và không thực hiện D3.
