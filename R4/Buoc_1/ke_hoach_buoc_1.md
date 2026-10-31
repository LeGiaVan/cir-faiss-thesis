# Kế hoạch Bước 1 — Kiểm định giả thuyết độ trung tâm D1–D3

**Trạng thái:** kế hoạch chờ duyệt; chưa chạy D1–D3. Nguồn: [feedback R4](../mentor_feedback_r4.txt), [execution plan R4](../R4_execution_plan.md) và [kiểm kê Bước 0](../provenance/bao_cao_buoc_0.md).

## Mục tiêu

Kiểm tra liệu ảnh gần hướng trung bình của gallery có quan hệ khác với cấu trúc HNSW và láng giềng exact so với ảnh ngoại vi. Đây là ba kiểm định riêng của cùng một giả thuyết cơ chế; không coi một tương quan hoặc một kết quả có ý nghĩa thống kê là chứng minh nhân quả.

| Kiểm định | Câu hỏi | Kế hoạch |
|---|---|---|
| D1 | Độ trung tâm liên quan thế nào tới bậc vào HNSW trước/sau centering? | [D1](./D1/ke_hoach_D1.md) |
| D2 | Độ trung tâm/norm liên quan thế nào tới N10 phía gallery? | [D2](./D2/ke_hoach_D2.md) |
| D3 | Exact neighbor của query CIR có nằm ngoại vi hơn gallery không? | [D3](./D3/ke_hoach_D3.md) |

## Dữ liệu và định nghĩa chung

- CIRCO, 123.403 ảnh gallery; SEARLE 512 chiều và Pic2Word 768 chiều. Với D3 có 1.020 query/model. Dùng cùng snapshot embeddings, query cache, thứ tự gallery ID, cấu hình reference và phép normalize đã khóa ở R3; kiểm tra hash thực tế trước khi dùng.
- Với vector gallery đơn vị `x_j`, tính `μ = mean_j(x_j)`, `m = ||μ||`, `u = μ/m`, `a_j = x_j·u` và `a_z = (a−mean(a))/std(a)` **riêng từng model**. Khi đo norm centered, dùng `y_j=x_j−μ`, không normalize lại. Kiểm tra vector hữu hạn, norm, `m>0`, `std(a)>0`, `mean(a)≈m` và `||y_j||²≈1−2ma_j+m²`; ghi sai số số học và tolerance trước khi tính.
- D1 dùng in-degree HNSW tầng 0 từ checkpoint gốc/centered tương ứng cùng seed 42–46; D2 dùng `N10_gallery` exact tự loại self theo ID; D3 dùng ID top-10 exact của các query CIR. Phân biệt `N10_gallery`, số lần xuất hiện trong top-10 của query CIR và bậc vào HNSW.
- Kiểm tra input, script, config, checkpoint signature, commit và hash; lưu metadata và đầu ra riêng tại từng thư mục. Nếu kiểm tra không đạt, dừng diễn giải và báo rõ. Không coi graph rebuild là cùng đồ thị R3 chỉ vì cùng seed.

## Cổng provenance trước khi chạy

Bước 0 đã tái trích test với ID: 800/800 hàng của mỗi model khớp cache cũ trong tolerance. Tuy nhiên, **test:251 và test:631** có feature khó phân biệt trong cả hai model; cache cũ không lưu ID nguồn, nên không thể chứng minh bằng hash lịch sử ánh xạ của hai hàng này. D3 cần giữ giới hạn đó và kiểm tra độ nhạy khi loại cặp query này. D1–D2 không dùng ID của test query nhưng vẫn cần đúng gallery/graph provenance.

Snapshot commit sạch của Bước 0 chỉ bao phủ mã trích xuất, **chưa tự bao phủ script D1–D3**. Trước khi gọi kết quả mới là confirmatory, khóa từng script/config thực sự chạy vào snapshot/commit sạch và ghi hash của data, weights và dependency ngoài commit. Bước 0 cũng ghi thiếu một số output C2 và một script R2 khác hash lịch sử; kiểm tra ảnh hưởng theo từng nguồn, không mặc định mọi artifact thiếu đều chặn D1–D3. Nếu chưa đạt cổng, chỉ thực hiện thăm dò có gắn nhãn và không trình bày như xác nhận độc lập.

## Thứ tự và quy tắc báo cáo

1. Trước khi xem kết quả mới, lưu preregistration dùng các kế hoạch D1–D3, ghi config, dataset, seed, tolerance số học, phép đo, bootstrap và quy tắc đánh giá; đánh dấu các dự đoán là R4 được đề xuất sau khi đã thấy R3.
2. Kiểm tra dữ liệu chung, tính và lưu vector `a`, `a_z`, norm centered cùng manifest/hash; mỗi kiểm định dùng đúng cùng artifact được kiểm tra.
3. Chạy D1, D2, D3; lưu kết quả từng model/seed/query, CI và hình theo kế hoạch riêng. Đối chiếu báo cáo với JSON/CSV bằng script.
4. Tổng hợp từng dự đoán thành **ủng hộ / ủng hộ một phần / chưa kết luận / không được ủng hộ** dựa trên dấu, độ lớn và độ bất định. Không thay đổi tiêu chí sau khi thấy số liệu; báo kết quả âm và dữ liệu không đủ. Nêu rõ các CI theo từng phép không mặc định là CI đồng thời.
5. Nếu D1–D3 không ủng hộ hướng dự đoán, trình bày lại giả thuyết và đề xuất bước sau dựa trên bằng chứng; không khẳng định mọi cơ chế đã bị loại trừ. Kết quả này chưa thay thế C2 cắt cạnh hay chứng minh causal mediation.

## Đầu ra chung

Mỗi thư mục D1/D2/D3 có script, manifest, JSON/CSV, hình và báo cáo được tạo từ dữ liệu; các file lớn để dưới `data/` và kiểm tra `.gitignore` trước khi thêm Git. Bước 1 có báo cáo tổng hợp liên kết đến từng kiểm định, giới hạn và bảng một trang cho mentor; không tự gửi tin nhắn. Không chạy C2 pruning, thí nghiệm `λ`, D4–D6 hoặc C6 trong bước này.
