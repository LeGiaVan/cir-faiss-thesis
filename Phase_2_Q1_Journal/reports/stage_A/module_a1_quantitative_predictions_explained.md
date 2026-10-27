# Hướng dẫn đọc báo cáo Module A.1: Hubness và lỗi tìm kiếm HNSW

Tài liệu này giải thích [báo cáo Module A.1](./module_a1_hubness_report.md) qua các câu hỏi, cách đo và ví dụ. Ví dụ giả định được ghi rõ. Không bổ sung kết quả kiểm định mới.

> **Mốc số liệu:** các con số thực nghiệm trong hướng dẫn này là snapshot lần chạy ngày 14/10/2026, được giữ tại `R2_Audit/archive/pre_p0_p1_p2b/a1/results/`. Chúng phục vụ giải thích cách đọc, không phải kết quả reference nhiều lần dựng mới. Dùng báo cáo A.1 hiện hành và JSON liên kết trong đó để trích số liệu mới; không ghép số một lần dựng cũ với trung bình nhiều lần dựng mới.

## 1. Module A.1 nghiên cứu vấn đề gì?

Model CIR biến query và ảnh gallery thành vector embedding. Trên cùng các vector đó, ta chạy hai cách tìm kiếm:

1. **FlatIP:** tìm chính xác 10 ảnh có điểm tương đồng cao nhất với mỗi query.
2. **HNSW:** tìm gần đúng để giảm chi phí tìm kiếm; có thể bỏ sót một số ảnh trong top-10 của FlatIP.

A.1 hỏi: **HNSW thường bỏ sót neighbor có đặc điểm gì, và vì sao tỷ lệ bỏ sót khác nhau giữa embedding SEARLE và Pic2Word?**

“Neighbor chính xác” ở đây là ảnh gần query nhất theo điểm số embedding. Nó không nhất thiết là ảnh đúng ý người dùng theo nhãn ngữ nghĩa.

| Câu hỏi | Cách đánh giá |
|---|---|
| Model có tìm đúng ảnh theo yêu cầu người dùng không? | Cần nhãn relevance và metric CIR phù hợp |
| HNSW có tìm lại được top-10 FlatIP của cùng model không? | Đo retention hoặc miss rate; đây là trọng tâm A.1 |

Vì vậy, retention HNSW thấp hơn không tự động có nghĩa model hiểu ngữ nghĩa kém hơn.

## 2. N10 và missed được đo như thế nào?

### 2.1. N10: một ảnh xuất hiện trong top-10 của bao nhiêu query?

Với mỗi query, dùng FlatIP lấy exact top-10. Sau đó đếm mỗi ảnh gallery xuất hiện bao nhiêu lần trong toàn bộ kết quả.

**Ví dụ minh họa:** ảnh A xuất hiện trong top-10 của 4 query thì `N10(A) = 4`; ảnh B xuất hiện trong top-10 của 25 query thì `N10(B) = 25`.

- **Đơn vị:** số lần xuất hiện.
- **Gắn với:** một ảnh gallery, trong một tập query cụ thể.
- **Phụ thuộc vào:** embedding, tập query và gallery.
- **Không phụ thuộc vào:** kết quả HNSW, vì N10 được tính bằng FlatIP.

N10 cao không tự chứng minh ảnh hoặc model tốt hơn. Đây là phép đo **query → gallery**, không phải dùng từng ảnh gallery làm query.

### 2.2. Missed: HNSW có bỏ sót neighbor với query này không?

Với từng query:

1. Lấy 10 neighbor chính xác bằng FlatIP.
2. Lấy 10 kết quả bằng HNSW.
3. Với mỗi neighbor trong exact top-10, ghi `missed = 0` nếu HNSW trả về ảnh đó, hoặc `missed = 1` nếu không.

**Đơn vị quan sát là cặp query–neighbor, không phải riêng một ảnh.** Cùng ảnh có thể được tìm thấy với query này nhưng bị bỏ sót với query khác.

Ví dụ minh họa, giả sử ảnh A xuất hiện trong exact top-10 của đúng hai query:

| Query | Neighbor | N10 của ảnh | HNSW có tìm được ảnh? | missed |
|---|---|---:|---|---:|
| q1 | A | 2 | Có | 0 |
| q2 | A | 2 | Không | 1 |

N10 của ảnh A giống nhau ở hai dòng, nhưng kết quả missed khác nhau.

### 2.3. Miss rate: chuyển các giá trị 0/1 thành tỷ lệ

**Miss rate = số cặp bị bỏ sót / tổng số cặp được xét × 100%.**

Ví dụ minh họa: có 1.000 cặp trong một nhóm, 80 cặp bị bỏ sót thì miss rate bằng **8%**. Retention tương ứng bằng **92%**.

| Đại lượng | Ý nghĩa | Đơn vị |
|---|---|---|
| N10 | Số lần một ảnh xuất hiện trong exact top-10 | Số lần |
| missed | Một cặp query–neighbor có bị bỏ sót không | 0 hoặc 1 |
| Miss rate | Tỷ lệ các cặp bị bỏ sót | % |
| Retention@10 | Tỷ lệ exact neighbor được tìm lại | % |
| Chênh lệch hai miss rate | Hiệu hai tỷ lệ | Điểm phần trăm |

Ví dụ 8% so với 3% là chênh lệch **5 điểm phần trăm**.

Trong A.1 R2, mỗi model có 1.020 query × 10 neighbor = **10.200 cặp**; hai model có **20.400 cặp**. Đây không phải 20.400 ảnh khác nhau hoặc 20.400 quan sát độc lập.

### 2.4. N10 có phải bậc vào HNSW không?

Không. Hai đại lượng đếm hai thứ khác nhau:

| Đại lượng | Đếm điều gì? | Nguồn đo |
|---|---|---|
| N10(x) | Số query chọn ảnh x vào exact top-10 | Kết quả FlatIP |
| In-degree HNSW | Số cạnh đi vào node x ở tầng 0 | Cấu trúc đồ thị HNSW |

Ảnh có N10 bằng 0 vẫn có thể có cạnh đi vào trong HNSW.

## 3. H1: N10 thấp có đi kèm khả năng bị bỏ sót cao hơn không?

### 3.1. Câu hỏi dễ hiểu

> Trong cùng model và cấu hình HNSW, ảnh ít được query chọn vào exact top-10 có bị HNSW bỏ sót thường xuyên hơn không?

H1 dùng **N10 để chia nhóm**, rồi dùng **miss rate để so sánh kết quả**.

Đây là một giả thuyết cần kiểm tra, không phải quy luật đã biết trước.

### 3.2. Cách đo từng bước

1. Dùng FlatIP lấy exact top-10 cho mọi query.
2. Đếm N10 của từng ảnh gallery.
3. Chạy HNSW và ghi missed cho từng cặp query–neighbor.
4. Chia các cặp theo N10 của neighbor: 1–4, 5–9, 10–29, từ 30 trở lên.
5. Tính miss rate từng nhóm.

Ví dụ, miss rate nhóm 1–4 được tính bằng:

> Số cặp bị bỏ sót có neighbor thuộc nhóm N10 = 1–4, chia cho tổng số cặp có neighbor thuộc nhóm đó.

**Mẫu số là số cặp, không phải số ảnh khác nhau.** Một ảnh xuất hiện trong top-10 của 4 query đóng góp 4 quan sát. Đây là tỷ lệ theo lượt xuất hiện, không phải phép trung bình cho mỗi ảnh một trọng số bằng nhau.

### 3.3. Do embedding hay do HNSW quyết định?

**Cả hai tham gia, nhưng giữ vai trò khác nhau.**

| Thành phần | Phụ thuộc vào |
|---|---|
| N10 của ảnh | Embedding, tập query và gallery |
| Neighbor có bị bỏ sót không | Embedding, đồ thị đã dựng và cấu hình tìm kiếm HNSW |

Giữ nguyên embedding và tập query, thay `efSearch` không làm đổi N10, nhưng có thể làm đổi miss rate. Giữ nguyên cấu hình HNSW nhưng đổi model có thể làm đổi cả N10, cấu trúc đồ thị và miss rate.

Do đó, nên gọi yếu tố thứ nhất là **đặc tính hình học embedding**, thay vì mặc định gọi là “chất lượng embedding”. Miss rate cũng đo HNSW **trên dữ liệu và cấu hình cụ thể**, không phải điểm chất lượng độc lập với dữ liệu.

### 3.4. Dự đoán định lượng và bootstrap nghĩa là gì?

Đặt:

**Delta = miss rate nhóm N10 thấp − miss rate nhóm N10 cao.**

H1 dự đoán **Delta > 0**. Cần xác định rõ hai nhóm được so sánh trước khi kiểm định.

Bootstrap lấy mẫu lại các query có hoàn lại. Mỗi lần chọn một query, giữ các neighbor của query đó đi cùng nhau. Tính lại chênh lệch qua nhiều lần lấy mẫu để xây dựng khoảng tin cậy 95%.

| CI 95% của Delta | Cách đọc |
|---|---|
| Hoàn toàn lớn hơn 0 | Ủng hộ hướng H1: nhóm thấp bị bỏ sót nhiều hơn |
| Chứa 0 | Chưa đủ bằng chứng về hướng chênh lệch; không có nghĩa hai nhóm bằng nhau |
| Hoàn toàn nhỏ hơn 0 | Ủng hộ hướng ngược lại với H1 |

**CI riêng của từng nhóm chưa phải CI của chênh lệch.** Không chỉ nhìn hai CI có chồng lấp hay không rồi coi đó là kiểm định đầy đủ. Nếu so sánh nhiều cặp nhóm, cần nêu cách xử lý nhiều phép so sánh.

### 3.5. Kết quả hiện tại có ủng hộ H1 không?

Theo bảng 4.2 của báo cáo và `step2_bootstrap_ci.json`:

| Model | Miss rate N10 = 1–4 | Miss rate N10 = 5–9 |
|---|---:|---:|
| SEARLE | 2,84% | 8,80% |
| Pic2Word | 9,14% | 12,21% |

Nhóm N10 thấp lại bị bỏ sót **ít hơn** trong phép so sánh này. **Xu hướng mô tả không ủng hộ hướng dự đoán H1.**

Báo cáo đang gắn nhãn **CHƯA KẾT LUẬN**. Bảng kết quả chưa trình bày CI của chênh lệch hai nhóm; không tự chuyển quan sát mô tả thành một kết quả kiểm định mới.

### 3.6. Vì sao nhóm N10 = 0 là N/A?

Một ảnh đã xuất hiện trong exact top-10 thì phải có N10 ít nhất bằng 1. Vì bảng neighbor-level chỉ chứa các ảnh thuộc exact top-10, nó không có quan sát N10 = 0.

Vì vậy, **không thể đo miss rate của nhóm N10 = 0 bằng bảng này**. N/A không có nghĩa miss rate bằng 0%.

Nhóm N10 từ 30 trở lên cũng không có quan sát trong bảng kết quả hiện tại.

## 4. H2: Vì sao HNSW bỏ sót nhiều hơn trên Pic2Word?

### 4.1. H2 khác H1 ở đâu?

- **H1:** so sánh các nhóm neighbor theo N10.
- **H2:** giải thích khoảng cách bỏ sót giữa hai model.

Theo bảng 4.1 của báo cáo:

| Model | Retention@10 | Miss rate |
|---|---:|---:|
| SEARLE | 96,98% | 3,02% |
| Pic2Word | 90,59% | 9,41% |

H2 hỏi:

> Khi tính đến hubness và cấu trúc đồ thị, khoảng cách bỏ sót giữa Pic2Word và SEARLE có giảm đi không?

### 4.2. Có phải H2 chắc chắn chỉ do chất lượng HNSW?

**Không.** Sự kiện bỏ sót là lỗi tìm kiếm gần đúng so với FlatIP, nhưng độ khó tìm kiếm còn phụ thuộc các vector model tạo ra.

Cùng `M=32`, `efConstruction=200`, `efSearch=128` không có nghĩa hai model tạo ra đồ thị giống nhau hoặc dễ tìm kiếm như nhau. HNSW xây đồ thị từ những vector khác nhau.

H2 nghiên cứu **tương tác giữa embedding và HNSW**. Nó không trực tiếp kết luận Pic2Word kém về ngữ nghĩa, cũng không chứng minh riêng thuật toán HNSW gây ra khoảng cách.

### 4.3. M0, M1, M2 là gì?

Đây là **ba mô hình thống kê giải thích việc bỏ sót**, không phải ba cấu hình HNSW.

Ta giữ dữ liệu quan sát rồi bổ sung dần thông tin:

| Mô hình thống kê | Thông tin được cung cấp | Câu hỏi trực giác |
|---|---|---|
| M0 | Neighbor thuộc SEARLE hay Pic2Word | Chỉ biết tên model thì khác biệt bỏ sót là bao nhiêu? |
| M1 | Thêm rank, N10 và bậc vào HNSW | Tính đến các đặc điểm neighbor này thì khác biệt còn lại thế nào? |
| M2 | Thêm điểm top-1 và chênh lệch điểm top-1/top-100 | Tính thêm đặc điểm query thì khác biệt còn lại thế nào? |

Ý nghĩa các biến trong mã:

| Biến | Ý nghĩa |
|---|---|
| `is_pic2word` | 1 nếu thuộc Pic2Word, 0 nếu thuộc SEARLE |
| `rank` | Thứ hạng exact của neighbor, từ 1 đến 10 |
| `log_n10` | `log(1 + N10)`, nén thang giá trị k-occurrence |
| `log_indeg` | `log(1 + in_degree_hnsw)`, nén thang bậc vào |
| `s1` | Điểm tương đồng exact cao nhất của query |
| `c_contrast` | Điểm exact hạng 1 trừ điểm hạng 100 |

### 4.4. Đọc hệ số is_pic2word như thế nào?

Hệ số này mô tả khác biệt Pic2Word so với SEARLE trên thang **log-odds bị bỏ sót**, sau khi tính đến các biến khác. Với xác suất bỏ sót p, odds bằng `p/(1-p)`; log-odds là log của giá trị đó.

Để đọc bảng, cần nhớ:

- Hệ số dương: mô hình thống kê ước lượng odds bị bỏ sót của Pic2Word cao hơn SEARLE.
- Hệ số tiến gần 0: khác biệt còn lại nhỏ hơn trên thang này.
- Hệ số không phải phần trăm bỏ sót hoặc chênh lệch điểm phần trăm.

Theo bảng 4.4 và `step3_nested_logit.json`:

| Mô hình | Hệ số is_pic2word |
|---|---:|
| M0 | 1,2050 |
| M1 | 0,8987 |
| M2 | 0,0901 |

Hệ số giảm một phần khi thêm các đặc điểm neighbor ở M1, rồi giảm nhiều hơn khi thêm đặc tính query ở M2. Điều này gợi ý cần xem xét cả hai nhóm đặc điểm khi giải thích khoảng cách.

**Hệ số giảm không làm retention HNSW thực tế tăng lên.** Đây là thay đổi trong mô hình giải thích các lỗi đã quan sát, không phải một thao tác sửa index.

### 4.5. Vì sao chưa thể khẳng định hubness là nguyên nhân?

1. M1 thêm cả rank, không chỉ N10. Không thể quy toàn bộ mức giảm hệ số cho hubness.
2. Hệ số logistic giữa các mô hình không trực tiếp tạo thành phép phân rã khoảng cách retention. Không lấy tỷ lệ giảm hệ số rồi gọi là “phần trăm lỗi do hubness”.
3. Cụm “giảm đáng kể” chưa có ngưỡng hoặc kiểm định rõ ràng cho sự suy giảm. Chưa thể tự hiểu là có ý nghĩa thống kê.
4. Hệ số M2 gần 0 chưa chứng minh khác biệt bằng 0; vẫn cần xem độ bất định.

Báo cáo hiện giữ H2 ở trạng thái **CHƯA KẾT LUẬN**. Các mô hình cung cấp bằng chứng về liên hệ thống kê, chưa tách được nguyên nhân một cách chắc chắn.

## 5. Thí nghiệm centering bổ sung điều gì?

Hồi quy thay đổi cách giải thích dữ liệu. Centering **thay đổi vector gallery rồi dựng lại HNSW**, để xem kết quả tìm kiếm có thay đổi không.

Trong báo cáo, mỗi vector gallery được trừ vector trung bình mu và **không normalize lại**:

```text
x' = x - mu
q · x' = q · x - q · mu
```

Với một query cố định, mọi ảnh bị trừ cùng lượng điểm `q · mu`, nên thứ tự exact được bảo toàn về mặt toán học. Khi chạy máy vẫn cần kiểm tra sai số số học và ties.

**Nếu exact top-10 và tập query không đổi thì N10 cũng không đổi.** Vì vậy, can thiệp này không làm giảm k-occurrence query → gallery đang dùng trong A.1.

Bảng 4.5 ghi rank invariance là True cho cả hai model, delta skewness bằng 0 và retention thay đổi:

| Model | Thay đổi Retention@10 |
|---|---:|
| SEARLE | Tăng khoảng 0,09 điểm phần trăm |
| Pic2Word | Tăng khoảng 4,38 điểm phần trăm |

Bảng gốc hiển thị delta bằng ký hiệu %. Khi diễn đạt hiệu hai tỷ lệ retention, cách gọi rõ hơn là **điểm phần trăm**.

Kết quả cho thấy retention có thể thay đổi trong khi exact ranking và N10 giữ nguyên. Nó chưa chứng minh “giảm hubness làm retention tăng”, bởi N10 trong phép đo này không giảm. Báo cáo ghi nhãn can thiệp là `inconclusive` — chưa kết luận.

## 6. Đoạn dự đoán định lượng viết theo cách dễ hiểu

> **H1 — So sánh các nhóm neighbor:** Chúng tôi dự đoán neighbor có k-occurrence thấp bị HNSW bỏ sót thường xuyên hơn neighbor có k-occurrence cao. Để đánh giá, tính miss rate từng nhóm và CI bootstrap 95% của chênh lệch giữa các nhóm được xác định trước. Chênh lệch dương với CI hoàn toàn trên 0 sẽ ủng hộ hướng dự đoán.
>
> **H2 — Giải thích khoảng cách giữa hai model:** Chúng tôi dự đoán hubness, bậc vào HNSW và thứ hạng giúp giải thích một phần khác biệt bỏ sót giữa Pic2Word và SEARLE. Kiểm tra xem hệ số phân biệt hai model thay đổi thế nào khi bổ sung các biến này, rồi bổ sung đặc tính query. Hệ số tiến gần 0 là dấu hiệu cần xem xét, nhưng chưa đủ để quy nguyên nhân riêng cho hubness.

Đây là đề xuất làm rõ cách diễn đạt và tiêu chí đánh giá. Không coi các tiêu chí bổ sung ở đây là đã được xác lập trước lần chạy hiện có.

## 7. Những điểm cần nhớ khi đọc kết luận

| Dễ hiểu nhầm | Cách hiểu phù hợp |
|---|---|
| N10 thấp nghĩa là embedding kém | N10 mô tả tần suất xuất hiện trong exact top-10 của tập query đang xét |
| Miss rate là chất lượng độc lập của HNSW | Miss rate phụ thuộc embedding, dữ liệu, đồ thị và cấu hình tìm kiếm |
| M2 có hệ số thấp nghĩa là HNSW được cải thiện | M2 chỉ thay đổi mô hình thống kê giải thích các lỗi đã quan sát |
| N10 = 0 phải có miss rate cao | Nhóm này không xuất hiện trong bảng exact-neighbor nên kết quả là N/A |
| Retention thấp nghĩa là CIR tìm ảnh đúng kém | Retention so HNSW với FlatIP của cùng model; đánh giá CIR cần nhãn ngữ nghĩa |
| CHƯA KẾT LUẬN nghĩa là không có hiệu ứng | Bằng chứng hiện tại chưa đủ cho kết luận đang xét |

## 8. Nguồn đối chiếu

- [Báo cáo Module A.1](./module_a1_hubness_report.md).
- [JSON số liệu tổng quan và in-degree](../../R2_Audit/module_a1_revision/results/step1_hnsw_indegree.json).
- [JSON miss rate và bootstrap](../../R2_Audit/module_a1_revision/results/step2_bootstrap_ci.json).
- [JSON hồi quy lồng nhau](../../R2_Audit/module_a1_revision/results/step3_nested_logit.json).
- [JSON centering](../../R2_Audit/module_a1_revision/results/step4_centering.json).
- [Script tính N10 và bảng neighbor-level](../../R2_Audit/module_a1_revision/scripts/step1_build_neighbor_dataset.py).
- [Script hồi quy](../../R2_Audit/module_a1_revision/scripts/step3_nested_logistic.py).
