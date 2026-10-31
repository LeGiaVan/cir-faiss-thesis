# D1–D3: giải thích kết quả và đề xuất thực nghiệm bổ sung

**Trạng thái:** phương án thăm dò sau khi đã xem D1–D3; chưa chạy các thí nghiệm bên dưới. Nguồn: [D1](../D1/bao_cao_D1.md), [D2](../D2/bao_cao_D2.md), [D3](./bao_cao_D3.md), [feedback R4](../../mentor_feedback_r4.txt). Các giả thuyết mới phải được ghi rõ là hình thành sau quan sát; trước khi thực hiện cần khóa định nghĩa, input, cấu hình, phép so sánh và CI.

## 1. D3 ngược dự đoán nào?

D3 **không ngược với các kết quả D1–D2**, vì chúng hỏi những câu khác nhau:

| | Đại lượng được so | Kết quả hiện có |
|---|---|---|
| D1 | Độ trung tâm ảnh với **in-degree HNSW** | Tương quan đổi từ dương ở original sang âm ở centered trên cả hai backbone. |
| D2 | Độ trung tâm/norm với **N10 phía gallery** | Hai tương quan theo hướng dự đoán đều dương trên cả hai backbone. |
| D3 | Trung bình độ trung tâm của **exact top-10 query CIR** với trung bình toàn gallery | Neighbor CIR có `a_z` trung bình **cao hơn** gallery: SEARLE +0,1775; Pic2Word +0,1527. |

Điều D3 **không ủng hộ** là dự đoán cụ thể “exact neighbor CIR có `a_z` trung bình thấp hơn trung bình gallery”. Chênh lệch Pic2Word − SEARLE là −0,0249, CI ghép cặp [−0,0536; +0,0051], nên chưa đủ bằng chứng Pic2Word lệch thấp hơn SEARLE. Điều này chưa bác bỏ kết quả D1/D2, cũng chưa loại trừ mọi vai trò của ảnh ngoại vi trong lỗi HNSW.

Ví dụ: một nhóm 10 ảnh có 7 ảnh khá trung tâm và 3 ảnh ngoại vi vẫn có thể có `a_z` trung bình dương. Nếu HNSW hay bỏ sót 3 ảnh ngoại vi, chúng vẫn có thể quan trọng đối với miss, dù trung bình của **cả 10 ảnh** không âm. Đây là ví dụ minh họa, không phải số đo từ CIRCO.

## 2. Giả thuyết H1 — Chọn top-10 làm nhóm neighbor khác gallery ngẫu nhiên

**Ý tưởng:** D3 so các ảnh được chọn vì có điểm IP cao với một ảnh gallery bất kỳ. Nếu query có thành phần dương theo hướng trung bình gallery, thành phần đó có thể làm ảnh trung tâm có lợi thế khi xếp hạng; phần còn lại của vector vẫn có thể chi phối hoặc đảo kết quả. Vì thế trung bình top-10 dương không đòi hỏi query CIR và ảnh gallery có cùng phân phối.

Với `u=μ/||μ||`, `a_j=x_j·u`, `b_q=q·u`, ta có đồng nhất thức `q·x_j = b_q a_j + q_perp·r_j`, trong đó `q_perp=q−b_qu` và `r_j=x_j−a_ju`. Đây là phân rã đại số, **không tự chứng minh** số hạng nào gây ra việc một ảnh được chọn.

**Thí nghiệm E1:**

1. Với từng model, lưu phân phối `b_q` của CIR và tính hai thành phần điểm số trên exact top-k. Kiểm tra tổng hai thành phần khớp điểm IP trong tolerance số học.
2. So `a_z` của top-10 với các mốc top-50/top-100 và mẫu gallery ngẫu nhiên. Làm theo query: lấy trung bình từng nhóm theo query rồi bootstrap query; báo CI và phân vị, không xem neighbor trong cùng query là độc lập.
3. Trong từng phân vị `b_q`, báo `a_z` trung bình của exact neighbor và CI. Nếu `b_q` dương nhưng phần dư vẫn quyết định thứ hạng, ghi rõ; không kết luận nguyên nhân chỉ từ tương quan `b_q`–`a_z`.

**Cách phân biệt:** nếu top-k có `a_z` cao hơn mẫu ngẫu nhiên và mức lệch thay đổi theo `b_q`, kết quả phù hợp với H1; nếu không, H1 đơn giản không được ủng hộ trong cấu hình này. Quan hệ quan sát vẫn có thể chịu ảnh hưởng của phần dư và ngữ nghĩa query.

## 3. Giả thuyết H2 — Trung bình dương che khuất nhóm neighbor ngoại vi bị bỏ sót

**Ý tưởng:** D3 lấy trung bình trên **mọi** exact neighbor; D1 và câu hỏi HNSW cần biết những ảnh **bị bỏ sót** nằm ở đâu. Một nhóm ngoại vi không chiếm đa số vẫn có thể đóng góp nhiều vào tổng số miss hoặc vào mức giảm miss sau centering. Chưa biết điều này đúng với dữ liệu hiện có.

**Thí nghiệm E2:**

1. Ghép từng `(model, query, rank, neighbor ID, seed)` với `a_z` và `found/missed` từ đúng checkpoint đồ thị original/centered cùng seed; kiểm tra hash, ID và ghép cặp. Khóa trước nhóm theo phân vị `a_z` của gallery trong từng model; công bố ranh giới, ties và số query/ảnh/occurrence.
2. Với từng nhóm, báo số và tỷ lệ occurrence, miss rate trước/sau, **đóng góp vào tổng số miss**, và chênh lệch miss có CI bootstrap ghép cặp query/seed. Kèm các lượng tuyệt đối và tương đối có xử lý mẫu số bằng 0. Không suy ra tổng đóng góp bằng cách so những tập đã đổi thành phần mà không theo dõi cùng ID.
3. Vẽ đường liên tục hoặc phân nhóm của `a_z` đối với miss và gain; nếu dùng mô hình, ghi trước biến điều chỉnh `rank`, `s1`, seed và cấu trúc cụm, báo overlap/số mẫu và độ nhạy theo ảnh. Đánh dấu mô hình là mô tả sau khi xem D3; không gọi hệ số là tác động nhân quả.
4. Thực hiện kiểm tra độ nhạy với `test:251` và `test:631` bị loại **cả hai**, còn kết quả chính giữ bộ test chính thức.

**Cách phân biệt:** H2 được ủng hộ mô tả nếu nhóm `a_z` thấp có tỷ lệ hoặc đóng góp miss/gain cao với CI phù hợp. Nếu không, không dùng “đuôi ngoại vi” để giải thích D3. Cùng `efSearch` không đảm bảo cùng `ndis`; nếu muốn nói hiệu quả theo chi phí, phải bổ sung đối chứng khớp `ndis`/mật độ ở E5.

## 4. Giả thuyết H3 — Mốc phù hợp là query ảnh, không chỉ toàn gallery

**Ý tưởng:** Cả query CIR và query ảnh có thể chọn exact neighbor trung tâm hơn ảnh gallery ngẫu nhiên. Khi đó, CIR có thể thấp hơn **query ảnh** nhưng vẫn cao hơn trung bình toàn gallery. D3 hiện tại chưa so CIR với query ảnh, nên chưa biết quan hệ này có tồn tại hay không.

**Thí nghiệm E3:**

1. Chọn và ghi trước cách lấy query ảnh, split, số lượng và cách ghép với query CIR; dùng cùng gallery/backbone/normalization. Nếu query ảnh có mặt trong gallery, loại self theo ID ở cả exact và phép đo tương ứng, và mô tả rõ khác biệt xử lý self giữa hai loại query; kiểm tra độ nhạy cùng chính sách loại reference khi có thể.
2. So `b_q`, `a_z` exact top-10, `s1`, retention original và gain centering giữa CIR và query ảnh, riêng theo model. Bootstrap theo query; ghép cặp chỉ khi có đối ứng thật sự và được xác minh. Báo cả phân vị, CI, số ảnh trùng, vùng chồng lấp của `s1`/`b_q` và độ nhạy theo nhóm `s1`.
3. Nếu query ảnh là reference của query CIR, ghi rõ đây là **đối chứng có ghép cặp** nhưng không tách riêng hoàn toàn loại modality với semantic modification. Nếu dùng ảnh ngẫu nhiên, không mặc định chúng có cùng phân phối ngữ nghĩa với CIR.

**Cách phân biệt:** nếu neighbor CIR có `a_z` thấp hơn neighbor query ảnh với CI của chênh lệch phù hợp, đó là bằng chứng mô tả cho H3 dù cả hai đều cao hơn gallery. Nếu không, không dùng modality gap theo hướng này để giải thích D3. Kiểm tra này cần làm D4/query ảnh trong kế hoạch R4, không tự động xem kết quả D3 là đã có đối chứng.

## 5. Giả thuyết H4 — Thành phần ngoài hướng trung tâm quan trọng hơn một thống kê toàn cục

**Ý tưởng:** `a_j` và MCS là tóm tắt một phần hình học; hai ảnh có `a_j` giống nhau vẫn có thể rất khác ở phần dư `r_j`. Tương quan D1–D2 có thể đúng trên toàn gallery, nhưng chưa đủ dự báo thứ hạng hay khả năng tìm thấy của từng query/neighbor. Đây là cách giải thích **có thể kiểm tra**, không phải kết luận đã đạt.

**Thí nghiệm E4:** trong từng model và các nhóm `a_z` đã khóa, báo phân phối `q_perp·r_j`, gap điểm số quanh rank 10/11, in-degree original/centered và miss. So hai backbone trong từng model trước; kiểm tra vùng chồng lấp trước khi đặt các thang điểm cạnh nhau. Nếu dùng hồi quy, chỉ gọi hệ số là liên hệ có điều kiện và kiểm tra tính đồng biến/collinearity, cụm query/ảnh và độ ổn định. Báo kết quả âm và CI.

## 6. Giả thuyết H5 — Thay đổi topology/mật độ có vai trò trong gain

**Ý tưởng:** D1 cho thấy quan hệ `a`–in-degree đổi dấu sau centering; C4 cho thấy đồ thị Pic2Word centered có nhiều cạnh hơn. Điều đó có thể liên quan đến khả năng tìm thấy, nhưng không chỉ ra lợi ích là do số cạnh, vị trí cạnh, tính kết nối hay tổ hợp các yếu tố. D3 không phân biệt được các khả năng này.

**Thí nghiệm E5:** thực hiện đối chứng C2 R4 đã lên kế hoạch: cắt tầng 0 của đồ thị centered theo bậc ra từng nút ở original, so hai quy tắc giữ cạnh (nearest và random), giữ các tầng trên; báo các nút không khớp, cạnh vào/ra, tính kết nối và retention trong miền `ndis` chung, đủ seed và CI. So đồng thời original, centered chưa cắt và hai bản cắt. Cắt cạnh cũng đổi danh tính cạnh, bậc vào và kết nối, nên không tự tạo can thiệp thuần túy chỉ thay mật độ. Thí nghiệm `λ` là đối chứng bổ sung; không gọi quan hệ liều–đáp ứng là chứng minh nhân quả hoàn toàn.

## 7. Kiểm tra kỹ thuật trước khi diễn giải

- Kiểm tra `a_z` tính trên gallery của đúng model, thứ tự gallery ID, hash embedding/graph/query và phép chuẩn hóa; D3 đã xác minh lại exact top-10 so với C4.
- Trong pipeline D3 hiện tại, exact CIR top-10 giữ nguyên quy tắc C4; cần kiểm tra protocol đánh giá có yêu cầu loại **reference image** hay không. Báo số query có reference xuất hiện, rồi chạy độ nhạy loại reference theo ID nếu mapping được xác minh. Giữ kết quả gốc để đối chiếu; không tự đổi định nghĩa ground truth hoặc gọi hiệu ứng là lỗi code khi chưa kiểm tra.
- Bootstrap theo query, giữ cặp trước/sau và seed; ghi nhận ảnh lặp giữa query và các giới hạn của CI. Đối chiếu chỉ số HNSW cùng `efSearch` với cùng `ndis`; không suy luận về lợi thế riêng khi chưa khớp mật độ.
- Tái dùng checkpoint chỉ khi provenance/signature và thứ tự ID khớp. Nếu có dữ liệu mới hoặc thay đổi thiết kế sau khi xem kết quả, ghi phiên bản, nhãn thăm dò và không gán là xác nhận độc lập.

## 8. Thứ tự đề xuất

1. **Ưu tiên rẻ:** kiểm tra reference/top-k và E1, sau đó E2 trên dữ liệu hiện có; hai bước trả lời vì sao trung bình top-10 và nhóm bị miss có thể kể hai câu chuyện khác nhau.
2. **Đối chứng cần thiết:** E3/query ảnh để kiểm tra nhận định CIR ngoại vi *tương đối với query ảnh*; E5 để đối chiếu cấu trúc đồ thị và chi phí.
3. **Cơ chế bổ sung:** E4 và thử `λ` theo nguồn lực; chỉ khẳng định phạm vi phù hợp sau khi kết quả được kiểm chứng và có CI.

Không có hướng nào ở trên được xem là kết quả mới cho đến khi thực nghiệm thực sự được chạy và báo cáo đầy đủ, kể cả kết quả trái dự đoán.
