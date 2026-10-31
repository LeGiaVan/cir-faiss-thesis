# D1 — Đăng ký phân tích trước khi tính kết quả R4

**Phạm vi:** Phân tích bổ sung theo feedback R4 sau khi đã biết các kết quả R3; không gọi đây là giả thuyết độc lập được đăng ký trước R3. Nguồn: [kế hoạch D1](./ke_hoach_D1.md), [Bước 1](../ke_hoach_buoc_1.md) và [feedback R4](../../mentor_feedback_r4.txt).

## Dự đoán và đại lượng

Trên từng backbone SEARLE/Pic2Word và mỗi seed 42–46, dự đoán hệ số Spearman giữa độ trung tâm gallery `a` và lần lượt `in-degree original`, `in-degree centered`, `in-degree centered − original` có dấu **dương, âm, âm**. Không định nghĩa ngưỡng độ lớn cho từ “mạnh” sau khi xem dữ liệu. Đại lượng là hệ số Spearman midrank trên toàn gallery, gồm cả các giá trị bậc hòa.

Tính `a = x·u` với `x` là gallery L2-normalize như R3; `u=μ/||μ||`, `μ=mean(x)`; centered là `x−μ`, không normalize lại. In-degree tính theo cạnh có hướng tầng 0 đã lưu cùng đồ thị C4/R2, không phải N10 hay cạnh toàn tầng. Kiểm tra provenance từng checkpoint, 123.403 vector, tính hữu hạn, tổng in-degree bằng out-degree, không giá trị âm và đúng chữ ký. Không cần test query ID để tính D1.

## Kiểm tra số học trước phân tích

Tích lũy mean và `a` bằng float64 từ vector R3 đã chuẩn hóa float32; yêu cầu sai số norm vector tối đa ≤`1e-6`, `||μ||>0`, độ lệch chuẩn `a>0`, sai số `|mean(a)−||μ|||| ≤ 1e-8`. Kiểm tra `||x−μ||² = 1−2||μ||a+||μ||²` với sai số tuyệt đối tối đa ≤`2e-6` (phụ thuộc norm float32). Dừng để điều tra nếu không đạt, không âm thầm đổi tolerance.

## Độ bất định và quy tắc đọc

Cho mỗi model/seed/biến, bootstrap ảnh gallery 2.000 lần với RNG seed 42, lấy lại theo cặp cùng chỉ số ảnh cho original/centered; tính lại Spearman midrank, CI percentile 95%. Đây là CI mô tả **có điều kiện trên gallery và đồ thị**, không điều chỉnh đầy đủ phụ thuộc nút do cùng một đồ thị; không dùng như bằng chứng suy rộng độc lập. Báo đủ 30 hệ số và CI (2 model × 5 seed × 3 phép), cùng trung bình, trung vị, miền giá trị giữa seed và tỷ lệ seed theo dấu. Không báo p-value hay tuyên bố kiểm định đa giả thuyết; CI theo từng phép không phải CI đồng thời.

Ở mỗi backbone, một hướng được gọi **phù hợp với dự đoán trên cả năm lượt dựng** nếu cả năm hệ số có dấu dự đoán và CI mô tả từng seed không chứa 0 theo cùng hướng. Nếu có seed ngược hướng hoặc CI chứa 0, báo các trường hợp cụ thể và nhãn phù hợp một phần hoặc chưa kết luận; nếu tất cả hệ số/CI cho thấy dấu đối lập, báo không ủng hộ dự đoán tương ứng. Đây là quy tắc mô tả có điều kiện đã đặt trước, không phải kiểm định nhân quả hay bằng chứng xác nhận độc lập. Dùng nhãn chung cho ba hướng theo từng backbone sau khi báo từng hướng; không chọn kết quả thuận lợi.

## Đầu ra và provenance

Trước khi phân tích, khóa script và file này trong snapshot có commit sạch; hash gallery, config, script, checkpoint C4 và checkpoint R2 gốc; kiểm tra nguồn và signature thay vì chỉ dựa vào tên file. Lưu `manifest.json`, vector `a`/`a_z`/norm centered, bảng theo seed, CI, mô tả phân vị/ties, hình và báo cáo có thể tái tạo. Mã phân tích đọc từ snapshot commit; dữ liệu và dependency ngoài commit được ghi hash/phiên bản, không gọi môi trường hoàn toàn clean. Nếu lỗi hash, thứ tự, graph provenance hoặc số học thì dừng và báo.
