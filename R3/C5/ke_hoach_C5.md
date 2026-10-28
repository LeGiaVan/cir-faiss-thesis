# Kế hoạch C5 — Query nào được lợi từ centering?

**Trạng thái: đề xuất, chờ duyệt; chưa phân tích hay chạy C5.** Nguồn: [feedback mentor R3](../mentor_feedback_R3.md), [kế hoạch R3](../R3_execution_plan.md), [đăng ký trước](../stage0_preregistration.md), cùng kết quả [C1](../C1/bao_cao_C1.md), [C2](../C2/bao_cao_C2.md) và [C4](../C4/bao_cao_C4_chi_tiet.md).

## 1. Câu hỏi và mục tiêu

Trong từng backbone, những query có `s1` thấp — tức điểm inner product với ảnh gần nhất trong gallery thấp — có nhận được mức tăng retention lớn hơn sau centering không?

C5 tập trung **ai được lợi**, bổ sung cho C1 (lợi ích tại cùng chi phí) và C4 (thay đổi cấu trúc gallery/đồ thị). Kết quả chính của C5 dựa trên đồ thị reference ở **cùng `efSearch=128`**, chưa khớp số cạnh hoặc `ndis`; không dùng kết quả này để khẳng định hiệu quả tại cùng chi phí hay quan hệ nhân quả.

## 2. Dự đoán và tiêu chí đọc kết quả

Đăng ký trước R3 dự đoán, trong từng model, gain sau centering lớn hơn ở query có `s1` thấp và có xu hướng giảm đơn điệu khi đi từ nhóm `s1` thấp đến cao. Không đặt trước ngưỡng cỡ hiệu ứng.

- Đại lượng chính là gain retention@10 của từng query, trung bình qua 5 cặp seed: `gain(q) = mean_seed(ret_after(q, seed) − ret_before(q, seed))`. Đơn vị là tỷ lệ; khi trình bày chênh lệch giữa hai retention dùng **điểm phần trăm**.
- Báo năm nhóm `s1` từ thấp đến cao, gain trung bình và CI 95%. Chênh lệch nhóm thấp nhất trừ nhóm cao nhất và CI bootstrap là đối chiếu bổ sung được định trước; **không coi CI từng nhóm chứa/không chứa 0 là kiểm định khác biệt giữa hai nhóm**.
- Gọi dữ liệu phù hợp với dự đoán đơn điệu nếu các trung bình điểm theo thứ tự năm nhóm không tăng và chênh lệch nhóm thấp nhất trừ cao nhất dương với CI 95% hoàn toàn trên 0. Đây là quy tắc làm việc mô tả, không phải kiểm định xu hướng đồng thời. Nếu không đơn điệu hoặc CI rộng/chứa 0, nêu rõ chưa đủ bằng chứng; không gộp hoặc đổi nhóm để tạo xu hướng.
- Làm riêng SEARLE và Pic2Word; không coi cùng giá trị `s1` thô ở hai backbone là cùng trạng thái hình học. Đối chiếu với C1/C2/C4 mà không suy ra tác động nhân quả hay khẳng định H-MG đã được kiểm chứng.

## 3. Dữ liệu và xác minh ghép cặp

Nguồn retention theo yêu cầu mentor: `Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/centering_per_query.parquet`. Kiểm kê ban đầu cho thấy file có cột `model`, `seed`, `variant`, `query_id`, `retention`, với các biến thể `before`/`after`; đó là định dạng dọc, không phải hai cột `ret_before`/`ret_after` trong mã tham khảo.

1. Kiểm tra hash file parquet với [manifest Chặng 0](../stage0_manifest.json); xác minh provenance và chữ ký các checkpoint R2 gốc, cấu hình, model, seed và định nghĩa retention. Với từng `(model, seed, query_id)` yêu cầu đúng một hàng before và một hàng after; kiểm tra không trùng, không thiếu, giá trị nằm trong [0,1], đủ seed `[42,43,44,45,46]` và 1.020 query/model.
2. Lấy `s1`, `s100` từ kết quả exact C4 (`C4/data/*_queries.npz`) nếu signature và input hash khớp. Nếu không chứng minh được provenance, tính lại exact IP từ cùng query cache/gallery đã khóa. `s1` là điểm top-1 exact trên gallery gốc đã chuẩn hóa; không dùng điểm HNSW hay điểm sau centering.
3. Ghép `query_id` vào đặc trưng theo **manifest thứ tự query**, kiểm tra không trùng/không thiếu và kiểm chứng phần validation với feature prefix/annotation như nguồn R2. Không ghép hai bảng chỉ bằng vị trí nếu chưa xác minh mapping; đối chiếu retention và query row với checkpoint nguồn. Lưu manifest ghép và hash của từng nguồn.
4. **Giới hạn quan trọng:** 800 test feature rows không có ID nguồn gắn trực tiếp; mapping hiện được tái dựng từ thứ tự extraction và annotation. Kiểm tra trên chỉ xác nhận tính nhất quán với snapshot hiện có, không chứng minh độc lập từng ID test. Ghi rõ trong báo cáo; nếu mapping nội bộ không nhất quán, dừng trước khi phân tích, không tự sửa thứ tự.
5. Kiểm tra exact top-10 trước/sau không đổi, seed và query được ghép đúng; so trung bình retention gốc/sau từ file query-level với checkpoint R2 tương ứng. Dữ liệu C1 dựng riêng; không ghép per-query từ đồ thị C1 với bậc vào hoặc retention của một đồ thị R2 khác.

## 4. Phương pháp phân nhóm và tính CI

1. Với từng `(model, query_id)`, ghép before/after theo seed, tính chênh lệch, rồi lấy trung bình 5 seed. Giữ thêm các gain theo từng seed để kiểm tra biến thiên; không coi 5 × 1.020 dòng là 5.100 query độc lập.
2. Trong **từng backbone**, chia 1.020 query thành 5 nhóm theo phân vị `s1` của chính backbone đó. Ranh giới được xác định từ `s1` trước khi xem gain, áp dụng cùng ranh giới cho before và after. Dùng phân vị theo thứ tự tăng, công bố biên, số query và phân bố `s1` trong từng nhóm.
3. Nếu `s1` trùng tại ranh giới và không thể tạo 5 nhóm không tách các giá trị bằng nhau, báo số tie và số nhóm thực tế; không chia tùy ý sau khi xem gain. Nếu cần thay đổi phương pháp hoặc không đủ 5 nhóm, ghi phiên bản/ảnh hưởng trước khi diễn giải và không gọi là kiểm tra đầy đủ dự đoán 5 quintile.
4. Bootstrap percentile 95%, **2.000 lần, seed ngẫu nhiên 42**: lấy mẫu lại query trong từng nhóm sau khi cố định ranh giới; lấy toàn bộ gain đã trung bình trên 5 seed của query được chọn. Tính đồng thời chênh lệch trung bình nhóm thấp nhất trừ nhóm cao nhất trong từng lần bootstrap. CI này mô tả bất định lấy mẫu query **có điều kiện trên 5 đồ thị và ranh giới quan sát**, không bao gồm biến thiên dựng đồ thị hoặc bất định của ngưỡng phân vị.
5. Độ nhạy được định trước: bootstrap chéo query và cặp seed để đánh giá biến thiên 5 lần dựng, giữ cùng seed trước/sau và cùng query; báo riêng CI độ nhạy, không thay thế CI chính. Nếu số seed nhỏ làm CI không ổn định, nêu rõ. CI theo từng nhóm không phải CI đồng thời; không suy luận mạnh từ nhiều so sánh nhóm.
6. Có thể trình bày `s100` theo nhóm như mô tả bổ sung, giữ `s1` là biến phân nhóm chính. Không dùng `s100`, đổi ngưỡng hay bổ sung kiểm định chọn sau khi xem kết quả làm tiêu chí chính.

## 5. Đầu ra dự kiến

- Trong `R3/C5`, lưu mã phân tích, manifest (hash input/mã/config, phiên bản, thời gian, seed bootstrap, ghi nhận dirty workspace), bảng ghép query-level và gain theo seed/query, ngưỡng nhóm, JSON kết quả.
- Bảng cho mỗi backbone: nhóm `s1`, khoảng `s1`, số query, retention gốc/sau, gain trung bình theo điểm phần trăm, CI bootstrap query và CI độ nhạy seed/query. Bảng riêng chênh lệch nhóm thấp nhất − cao nhất, CI và thứ tự gain của cả năm nhóm.
- Hình theo từng backbone: trục hoành nhóm `s1` thấp→cao, trục tung gain theo điểm phần trăm, CI 95%, đường tham chiếu 0; thể hiện số query và, nếu phù hợp, các ước lượng theo seed.
- Báo cáo theo 7 phần: câu hỏi, dự đoán trước, dữ liệu và phương pháp, bảng/hình kết quả, đánh giá dự đoán, hạn chế, bước tiếp theo. Số liệu trong báo cáo/hình được sinh hoặc kiểm tra trực tiếp từ JSON/bảng, có liên kết tương đối và phân biệt kết quả âm tính với chưa đủ bằng chứng.

## 6. Giới hạn và điều kiện dừng

C5 tại cùng `efSearch` có thể phản ánh khác biệt `ndis` và mật độ; C1 đã kiểm tra riêng cùng `ndis`, còn C2 chưa khớp mật độ trong ngưỡng định trước. CI query không xử lý đầy đủ phụ thuộc khi một ảnh xuất hiện trong nhiều query; 800 test row IDs chưa xác minh độc lập. Hai backbone có phân bố điểm và đơn vị hình học khác nhau; không so sánh trực tiếp quintile như cùng một khoảng `s1`.

Dừng trước kết luận nếu input hash/provenance không khớp, ghép query không kiểm chứng được, thiếu cặp seed/variant, retention không khớp checkpoint hoặc exact rank thay đổi ngoài sai số đã điều tra. Đây là kế hoạch C5; không tự mở rộng sang H-MG/C6 hoặc gửi kết quả ra ngoài.
