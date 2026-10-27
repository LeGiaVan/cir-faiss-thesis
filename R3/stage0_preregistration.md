# Đăng ký trước phân tích R3 — khóa trước C1–C5 và H-MG

**Ngày khóa:** 2026-10-27 (Asia/Bangkok)  
**Nguồn yêu cầu:** [`mentor_feedback_R3.md`](./mentor_feedback_R3.md)  
**Provenance:** xem [`stage0_manifest.json`](./stage0_manifest.json).  
**Trạng thái:** dự đoán dưới đây được viết trước khi chạy C1–C5/H-MG của R3. Chúng là dự đoán làm việc dựa trên feedback và kết quả reference R2 đã có, không phải kết quả mới hay xác nhận độc lập. Không sửa dự đoán sau khi xem các đường cong R3; nếu cần đổi thiết kế, ghi phiên bản và lý do trước khi chạy phần mới.

## Dữ liệu và cấu hình khóa

- CIRCO: 123.403 gallery images; query profile hiện có gồm 220 val + 800 test = 1.020 query cho mỗi model.
- SEARLE: CLIP ViT-B/32, 512 chiều. Pic2Word: CLIP ViT-L/14, 768 chiều.
- HNSW reference: `M=32`, `efConstruction=200`, `efSearch=128`, inner product; seeds `[42,43,44,45,46]`.
- Bootstrap replicate count: 2.000; dùng resampling có ghép cặp theo seed/query khi phép so sánh có cấu trúc ghép cặp.
- C1 sweep: `efSearch=[32,48,64,96,128,160,192,256,384]`.
- C2 original graph sweep: `M=[32,40,48,64]`, `efConstruction=200`.
- Với centered IP: center gallery, giữ quy trình query IP reference; kiểm tra exact rank invariance. Với đối chứng L2: center query và gallery bằng cùng `μ`.
- Kết quả được đánh giá theo exact neighbors trong gallery tương ứng; không trộn retention, recall, candidate coverage và mAP như thể chúng là cùng một metric.

## Estimand và suy luận chung

1. C1 estimand chính là chênh lệch retention@10 giữa centered IP và original IP **tại cùng số phép tính khoảng cách trung bình `ndis/query`**, riêng cho từng backbone. Latency là kết quả phụ.
2. Chỉ so trong miền `ndis` mà tất cả đường cần so sánh có dữ liệu; không ngoại suy. Lập lưới 5 điểm đều trên thang log trong phần giao nhau của các miền hỗ trợ. Dùng nội suy tuyến tính theo retention giữa hai điểm đo kề nhau và báo độ nhạy nếu kết luận phụ thuộc điểm nội suy.
3. Với CI, giữ pairing theo seed và query; bootstrap chéo seed/query 2.000 lần theo config. Báo mọi seed và CI của chênh lệch. Nếu 5 seed làm CI không ổn định, nêu giới hạn cỡ mẫu seed; không diễn giải CI như kiểm định nhân quả.
4. C2 báo số cạnh thực tế và retention–`ndis`. “Cùng số cạnh” được xem là đạt nếu median edge count lệch không quá 2% so với centered M=32; nếu không có M thỏa điều kiện, báo mức gần nhất và không gọi đó là so sánh chính xác cùng mật độ.
5. Mọi so sánh theo `s1`/MMD được thực hiện trong từng backbone trước. Không diễn giải cosine/MMD thô giữa hai backbone như cùng thang đo nếu chưa kiểm tra phân bố và kernel bandwidth.

## Dự đoán và quy tắc đọc từng phần

### C1 — centering ở cùng chi phí tìm kiếm

**Dự đoán làm việc:** hiệu ứng ở Pic2Word nhiều khả năng nhỏ đi đáng kể khi chuyển từ so sánh cùng `efSearch` sang cùng `ndis`, vì feedback ghi đồ thị centered Pic2Word có nhiều cạnh và độ trễ cao hơn. Vẫn kiểm tra khả năng đường retention–`ndis` của centered IP nằm trên đường gốc, nhất là Pic2Word; không giả định rằng mức tăng +4,09 điểm tại reference `efSearch` giữ nguyên ở cùng `ndis`. Dự đoán cho SEARLE là hiệu ứng nhỏ hơn Pic2Word.

**Quy tắc:** chỉ gọi là cải thiện ở ngân sách đã khảo sát nếu chênh lệch retention centered−original dương và CI paired hỗ trợ điều đó tại các mức `ndis` trong miền chung. Nếu CI chứa 0 hoặc đường trùng nhau, kết luận “chưa có bằng chứng tăng hiệu quả ở cùng chi phí”, dù retention tại cùng `efSearch` có tăng.

### C2 — cùng mật độ đồ thị

Đây là đối chứng cho lời giải thích “đồ thị dày hơn”. Nếu original với `M` lớn hơn có retention gần với centered M=32 tại cùng số cạnh và `ndis`, kết quả phù hợp với việc centering đổi mật độ/chi phí chứ chưa cho thấy lợi thế riêng. Nếu centered có retention cao hơn trong điều kiện khớp được, điều đó ủng hộ lợi thế hình học bổ sung. Không dự đoán trước rằng một mức `M` cụ thể chắc chắn khớp; báo sai lệch edge count thực tế.

### C3 — đối chứng âm L2

**Dự đoán:** dịch đồng thời mọi query và gallery cùng một `μ` trong L2 không đổi khoảng cách cặp, exact ranking và do đó kết quả tìm kiếm lý tưởng. Kiểm tra trực tiếp `max |d_before−d_after|`, exact top-10 IDs và retention theo seed. Dùng tolerance floating-point được ghi trước khi chạy; nếu có sai khác vượt tolerance, kiểm tra thứ tự thêm node, ties và precision trước khi dùng C3 làm đối chứng.

### C4 — MCS, N10 gallery và in-degree

**Dự đoán làm việc từ feedback:** MCS của Pic2Word cao hơn SEARLE; centering có thể làm thay đổi cấu trúc N10 gallery/in-degree. Không khóa trước hướng hoặc tỷ lệ thay đổi N10/in-degree vì feedback nêu đây là cơ chế cần phân biệt, chưa phải kết quả đã kiểm định.

Phân biệt hai khả năng: (a) centering đổi cơ cấu bậc vào của exact neighbors và thay đổi miss thông qua việc chuyển nhóm; (b) centering làm miss đổi ngay trong cùng nhóm bậc vào. Báo cả hai; không gọi decomposition là trung gian nhân quả.

### C5 — query nào được lợi

**Dự đoán:** trong từng model, gain retention sau centering lớn hơn ở các query có `s1` thấp; dự đoán quan hệ đơn điệu theo quintile nhưng không áp đặt ngưỡng cỡ hiệu ứng. Dùng gain trung bình qua 5 seed trên cùng `query_id`, cùng chiều bootstrap query. Nếu xu hướng không đơn điệu hoặc CI rộng, báo như vậy; không gộp bins sau khi xem dữ liệu để tạo xu hướng.

### H-MG — loại query và khoảng cách query/gallery

**Dự đoán theo feedback:** (1) MMD² giữa CIR queries và gallery cao hơn đối chứng image queries trong từng backbone; (2) image-query miss thấp hơn CIR-query miss; (3) trong từng loại/model, miss tăng khi `s1` giảm. So CIR và image queries tại quintile `s1` tương đương; giữ cùng gallery/index/config trong mỗi so sánh.

Nếu chỉ có khác biệt thô nhưng không còn trong nhóm `s1` tương đương, diễn giải là kết quả phù hợp với khoảng cách gần gallery, chưa phải bằng chứng riêng cho modality. Nếu MMD cao nhưng lỗi không cao hơn, MMD ở thiết kế này không được xem là giải thích đủ cho lỗi ANN.

## Định nghĩa biến phải giữ cố định

- `s1`: exact top-1 similarity giữa query và gallery.
- `s100`: exact top-100 similarity.
- `c_contrast = s1 − s100`; trong hồi quy A.1, mô hình chính sẽ tham số hóa bằng `s1` và `s100` thay vì diễn giải đồng thời hai biến `s1` và `c_contrast`.
- `N10_gallery`: số gallery queries lấy mỗi ảnh làm query mà ảnh đó xuất hiện trong exact top-10 gallery, self bị loại theo ID.
- `N10_query`: số query CIR lấy ảnh gallery vào exact top-10.
- `N10_loo = N10_query − 1` cho một neighbor trong top-10 của chính query đó; đơn vị và tập query phải được ghi rõ.
- `missed`: chỉ báo neighbor trong exact top-10 không xuất hiện trong ANN top-10.

## Ràng buộc provenance trước phân tích xác nhận

- `stage0_manifest.json` ghi repository đang dirty; HEAD hiện tại không đại diện đầy đủ source/config đang dùng vì nhiều thư mục Phase 2 chưa tracked. SHA256 đã khóa snapshot được kiểm tra, nhưng đây không tương đương một clean commit.
- Test features hiện chưa có source ID theo từng hàng. Query ID dựng từ thứ tự annotation/extraction phải được xác minh trước kết luận A.1/GEE có cụm theo query. Không diễn giải nhãn test như đã kiểm toán độc lập.
- Chưa bắt đầu chạy C1–C5/H-MG trong giai đoạn này. Nếu môi trường/data/code thay đổi, tạo manifest phiên bản mới và ghi rõ phần nào đổi.
