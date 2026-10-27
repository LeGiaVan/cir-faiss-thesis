# Báo cáo Thực nghiệm Module A.1: Phân tích Hubness và Recall Retention của HNSW

> Sinh tự động bởi `step5_render_report.py` lúc 2026-10-14T08:05:24.685975Z.
> Mọi số liệu trong báo cáo được đọc từ JSON trong `module_a1_revision/results/`.

---

## 1. Câu hỏi Nghiên cứu

Hiện tượng hubness trong không gian embedding CIRCO có liên quan như thế nào đến xác suất HNSW bỏ sót các láng giềng exact top-10, và liệu các biến hubness/graph có giải thích được khoảng cách retention giữa SEARLE và Pic2Word hay không?

## 2. Giả thuyết & Dự đoán Định lượng

- **H1:** Các neighbor có k-occurrence thấp có tỷ lệ bị HNSW bỏ sót cao hơn các nhóm còn lại.
- **H2:** Khoảng cách retention giữa SEARLE và Pic2Word được giải thích một phần bởi biến hubness/graph.
- **Dự đoán định lượng:** hiệu ứng hubness có ý nghĩa thực nghiệm nếu CI bootstrap cho thấy khác biệt ổn định giữa nhóm, và hệ số `is_pic2word` giảm đáng kể khi thêm `rank`, `log_n10`, `log_indeg` vào mô hình.

## 3. Thiết kế Thực nghiệm

- **Dữ liệu & mô hình:** CIRCO, 1020 truy vấn, 123403 ảnh gallery; SEARLE 512-d và Pic2Word 768-d.
- **Đơn vị phân tích:** neighbor-level, tổng cộng 20400 quan sát.
- **Cấu hình chỉ mục:** HNSWFlat, M=32, efSearch=128, efConstruction=200.
- **Phương pháp đo:** exact FlatIP top-10 làm mốc; HNSW retention là tỷ lệ exact neighbor được tìm lại trong HNSW top-10.
- **Thống kê:** clustered bootstrap 95% CI theo `query_id`; GEE logistic regression với cụm `query_id`.

## 4. Kết quả Thực nghiệm

### 4.1. Tóm tắt Step 1

| Mô hình | Retention@10 | Miss rate | Anti-hub gallery ratio | k-occurrence skewness | In-degree=0 ratio |
|---|---:|---:|---:|---:|---:|
| SEARLE | 96.98% | 3.02% | 93.25% | 6.7992 | 0.0008% |
| Pic2Word | 90.59% | 9.41% | 93.46% | 8.3298 | 0.0162% |

### 4.2. Miss rate theo nhóm k-occurrence

| Nhóm | SEARLE Miss Rate | 95% CI | Pic2Word Miss Rate | 95% CI |
|---|---:|---:|---:|---:|
| Anti-hub (N10=0) | N/A | N/A | N/A | N/A |
| N10 = 1-4 | 2.84% | [2.41%, 3.26%] | 9.14% | [8.20%, 10.07%] |
| N10 = 5-9 | 8.80% | [5.47%, 12.23%] | 12.21% | [9.09%, 15.35%] |
| N10 = 10-29 | 8.70% | [0.00%, 21.74%] | 31.82% | [21.42%, 44.62%] |
| Hub (N10≥30) | N/A | N/A | N/A | N/A |

Ghi chú: nhóm `N10=0` không có quan sát trong bảng neighbor-level vì một ảnh đã xuất hiện trong exact top-10 thì theo định nghĩa có `N10 >= 1`. Do đó kết quả này không được dùng để khẳng định kiểm định Anti-hub có ý nghĩa thống kê.

**Nhận xét về k-occurrence và hubness:** Trong dữ liệu hiện tại, nhóm có k-occurrence theo query thấp (`N10 = 1–4`) ghi nhận miss rate thấp hơn các nhóm `N10 = 5–9` và `N10 = 10–29` ở cả SEARLE và Pic2Word. Đây là nhận xét mô tả trên mẫu quan sát, chưa khẳng định mọi chênh lệch giữa các nhóm đều có ý nghĩa thống kê hoặc miss rate tăng đơn điệu theo N10; đặc biệt, nhóm SEARLE `N10 = 10–29` có ít quan sát và khoảng tin cậy rộng.

Ở đây, N10 đo số query mà một ảnh xuất hiện trong exact top-10, phản ánh mức độ phổ biến của ảnh trong kết quả truy hồi (hubness theo tập query), không trực tiếp đo số cạnh đi vào hay khả năng tiếp cận ảnh trong đồ thị HNSW. Kết quả gợi ý mối liên hệ giữa mức độ phổ biến này và tỷ lệ bỏ sót trên từng lần xuất hiện, nhưng chưa xác lập quan hệ nhân quả giữa hubness và miss rate. Bảng phân nhóm chưa tách ảnh hưởng của thứ hạng, độ khó query và cấu trúc đồ thị; đồng thời không có quan sát ở các nhóm `N10 = 0` và `N10 ≥ 30`, nên chưa thể khái quát sang anti-hub hoặc hub cực trị.

### 4.3. Trực quan hóa

![Tỷ lệ bỏ sót theo nhóm k-occurrence](./plots/fig1_miss_rate_by_k_group.png)

![Đường hệ số model qua các mô hình lồng nhau](./plots/fig2_logit_coef_path.png)

![Can thiệp centering trước và sau](./plots/fig3_centering_before_after.png)

### 4.4. Nested logistic regression

| Mô hình | beta_model `is_pic2word` | QIC | Diễn giải thiết kế |
|---|---:|---:|---|
| M0 | 1.2050 | 9127.2511 | Baseline: chỉ có biến model |
| M1 | 0.8987 | 8058.8983 | + rank, log_n10, log_indeg |
| M2 | 0.0901 | 7780.7805 | + s1, c_contrast |

#### 4.4.1. Phần này đang trả lời câu hỏi gì?

Bảng miss rate ở trên chỉ cho biết mô hình nào bỏ sót nhiều hơn. Hồi quy đặt thêm câu hỏi: **nếu xét cả thứ hạng láng giềng, tần suất xuất hiện, kết nối đồ thị và đặc tính query, chênh lệch gắn với tên mô hình còn lớn đến đâu?**

Ở đây có hai nghĩa khác nhau của từ “mô hình”: SEARLE/Pic2Word là mô hình tạo embedding; M0/M1/M2 là ba mô hình thống kê dùng để phân tích lỗi của các embedding đó. Hồi quy này không huấn luyện lại SEARLE, Pic2Word hoặc HNSW.

#### 4.4.2. Một dòng dữ liệu và biến cần dự đoán

Mỗi dòng là một bộ `(model, query_id, neighbor_id)`: một ảnh thuộc exact top-10 của một query, trong không gian embedding của một mô hình. Biến đầu ra là `missed`:

- `missed = 1`: ảnh thuộc exact top-10 nhưng không nằm trong HNSW top-10.
- `missed = 0`: ảnh đó cũng được HNSW trả về trong top-10.

Vì vậy, hồi quy dự đoán **xác suất một exact neighbor bị bỏ sót**, không dự đoán một query thất bại hoàn toàn, không dự đoán ảnh có đúng ngữ nghĩa hay không, và không trực tiếp dự đoán retention của cả query. Trung bình `missed` trên các dòng cho miss rate; retention tương ứng bằng một trừ miss rate.

#### 4.4.3. Logistic regression: từ điểm số đến xác suất

Hồi quy cộng các biến đầu vào sau khi nhân với hệ số để tạo một điểm số `z`, rồi biến đổi điểm số thành xác suất `p` trong khoảng 0–1:

```text
z = beta_0 + beta_1*x_1 + beta_2*x_2 + ...
p = 1 / (1 + exp(-z))
odds = p / (1 - p)
logit(p) = ln(odds) = z
```

`exp` là hàm mũ, `ln` là logarithm tự nhiên. `beta_0` (Intercept) là hằng số nền; các beta còn lại biểu thị thay đổi trên thang **log-odds** khi một biến tăng một đơn vị và các biến còn lại giữ nguyên. Phần mềm ước lượng hệ số từ dữ liệu `missed` và các biến đầu vào; người phân tích không tự chọn dấu hay độ lớn của hệ số.

Ví dụ thuần minh họa, **không phải số liệu thực nghiệm**: nếu xác suất bỏ sót là 20%, odds bằng `0,20 / 0,80 = 0,25`. Nếu odds tăng gấp đôi thành 0,50 thì xác suất mới là `0,50 / (1 + 0,50) = 33,33%`, không phải 40%. Do đó, “odds tăng gấp đôi” khác “xác suất tăng gấp đôi”.

Để đọc hệ số dễ hơn, chuyển thành **odds ratio**, viết tắt OR: `OR = exp(beta)`.

| Hệ số beta | Odds ratio | Ý nghĩa đối với sự kiện bị bỏ sót |
|---|---|---|
| Dương | OR > 1 | Odds bỏ sót cao hơn khi biến tăng, giữ các biến khác cố định |
| Bằng 0 | OR = 1 | Không có thay đổi odds theo biến đó trong mô hình |
| Âm | OR < 1 | Odds bỏ sót thấp hơn khi biến tăng, giữ các biến khác cố định |

Hệ số không phải phần trăm miss rate. Chẳng hạn, beta bằng 0,9 không có nghĩa miss rate tăng 90 điểm phần trăm. Cũng không thể so trực tiếp độ lớn beta của hai biến khác đơn vị để kết luận biến nào “quan trọng hơn”.

#### 4.4.4. “Nested” nghĩa là thêm dần biến vào cùng một bài toán

Các mô hình được gọi là **lồng nhau** vì tập biến của mô hình trước là tập con của mô hình sau. Chúng cùng dự đoán `missed` trên cùng tập dữ liệu:

```text
M0: chỉ biết ảnh đến từ SEARLE hay Pic2Word
  -> M1: thêm thứ hạng + k-occurrence + in-degree HNSW
    -> M2: thêm điểm tương đồng cao nhất + độ chênh điểm của query
```

Viết chính xác theo mã nguồn:

```text
M0: logit(p) = b0 + b_model*is_pic2word
M1: logit(p) = b0 + b_model*is_pic2word
              + b_rank*rank + b_n10*ln(1 + N10) + b_indeg*ln(1 + in_degree)
M2: logit(p) = b0 + b_model*is_pic2word
              + b_rank*rank + b_n10*ln(1 + N10) + b_indeg*ln(1 + in_degree)
              + b_s1*s1 + b_contrast*c_contrast
```

**Toàn bộ hệ số được ước lượng lại ở mỗi bước.** M1 không giữ nguyên hệ số đã tính ở M0; M2 cũng không giữ nguyên hệ số của M1. “Nested” ở đây nói về tập biến, không phải một mạng neural nhiều tầng hay một mô hình hiệu ứng ngẫu nhiên phân cấp.

| Biến trong code | Định nghĩa và cách đọc |
|---|---|
| `is_pic2word` | 1 nếu là Pic2Word, 0 nếu là SEARLE. SEARLE là nhóm tham chiếu. Hệ số của biến này so sánh Pic2Word với SEARLE. |
| `rank` | Thứ hạng của ảnh trong exact top-10, từ 1 đến 10. Tăng một đơn vị là lùi một hạng, ví dụ từ hạng 3 xuống hạng 4. |
| `log_n10` | `ln(1 + N10)`, trong đó N10 là số query có ảnh này trong exact top-10. Đây là tần suất theo query, không phải bậc đồ thị HNSW. |
| `log_indeg` | `ln(1 + in_degree_hnsw)`, với in-degree là số cạnh đi vào ảnh ở tầng 0 của HNSW. |
| `s1` | Điểm inner product của ảnh đứng đầu kết quả exact đối với query. Đây là đặc tính của query, không phải điểm riêng của từng neighbor. |
| `c_contrast` | `s1 - s100`, chênh lệch điểm exact giữa ảnh hạng 1 và hạng 100. Đây không phải khoảng cách điểm giữa hạng 10 và 11, và không mặc nhiên đồng nhất với định nghĩa Relative Contrast ở module khác. |

Biến đổi `ln(1 + x)` nén các giá trị đếm lớn và tính được cả khi x bằng 0. Một đơn vị tăng của `log_n10` **không phải** thêm một lần xuất hiện. Khi N10 chuyển từ a sang b, OR là `exp(beta_n10 * ln((1+b)/(1+a)))`. Tương tự cho in-degree.

#### 4.4.5. Vì sao dùng GEE và gom cụm theo query?

Các neighbor của cùng một query có chung điều kiện tìm kiếm nên có thể cùng dễ hoặc cùng khó bị bỏ sót. Nếu coi tất cả các dòng là các phép đo độc lập, mức độ chắc chắn của kết quả có thể bị đánh giá quá cao.

Mã nguồn dùng **GEE (Generalized Estimating Equations)** với phân phối Binomial, liên kết logit, `groups="query_id"` và cấu trúc tương quan làm việc `Independence`. GEE vẫn mô hình hóa xác suất bằng công thức logistic ở trên, nhưng dùng sai số chuẩn robust theo cụm để phục vụ suy luận. `Independence` là lựa chọn cấu trúc làm việc, không có nghĩa sai số chuẩn robust bắt buộc mọi dòng trong query phải độc lập. Xem [tài liệu GEE của statsmodels](https://www.statsmodels.org/stable/gee.html).

Do dữ liệu hai mô hình được gộp chung và nhóm bằng `query_id`, các dòng cùng mã query của cả SEARLE và Pic2Word được gom vào cùng một cụm. Cách này đòi hỏi mã query giữa hai mô hình phải cùng chỉ một truy vấn. Nó xử lý phụ thuộc trong query, nhưng không tự động xử lý mọi phụ thuộc giữa các query khác nhau do cùng truy hồi một ảnh hoặc cùng dùng chung đồ thị.

#### 4.4.6. Đọc beta, khoảng tin cậy và p-value

Trong JSON, `coef` là hệ số beta ước lượng; `std_err` là sai số chuẩn của hệ số; `ci_95_lower/upper` là khoảng tin cậy 95%; `p_value` kiểm định giả thuyết beta bằng 0 trong mô hình đang xét.

- CI của **beta** chứa 0: chưa loại trừ được trường hợp không có liên hệ theo kiểm định hai phía ở mức 5%.
- CI của **OR** chứa 1: cùng ý nghĩa trên, vì `exp(0) = 1`.
- p nhỏ hơn 0,05: có bằng chứng thống kê chống giả thuyết beta bằng 0, trong các giả định của mô hình. Không có nghĩa hiệu ứng lớn hoặc có quan hệ nhân quả.
- p lớn hơn 0,05: chưa đủ bằng chứng bác bỏ beta bằng 0. Không chứng minh beta thực sự bằng 0 hay hai nhóm tương đương.

P-value không phải xác suất giả thuyết không là đúng. CI 95% cũng không có nghĩa 95% số neighbor nằm trong khoảng đó; đây là khoảng bất định của **tham số ước lượng**. CI hồi quy ở phần này dựa trên sai số chuẩn GEE, khác CI bootstrap của miss rate ở mục 4.2.

Bảng dưới lấy beta, CI và p-value trực tiếp từ `step3_nested_logit.json`; OR và CI của OR được tính bằng hàm mũ từ các giá trị đó:

| Mô hình | beta Pic2Word | CI 95% của beta | OR Pic2Word/SEARLE | CI 95% của OR | p-value |
|---|---:|---|---:|---|---:|
| M0 | 1.2050 | [1.0469, 1.3632] | 3.337 | [2.849, 3.908] | 1.94e-50 |
| M1 | 0.8987 | [0.7326, 1.0648] | 2.456 | [2.080, 2.900] | 2.84e-26 |
| M2 | 0.0901 | [-0.1400, 0.3203] | 1.094 | [0.869, 1.377] | 0.443 |

**M0 — chênh lệch chưa điều chỉnh.** Chỉ có tên mô hình làm biến giải thích, nên hệ số phản ánh chênh lệch tổng thể trong mẫu. OR lớn hơn 1 nghĩa là odds bỏ sót của Pic2Word cao hơn SEARLE. Có thể kiểm tra bằng cách đổi điểm số M0 trở lại xác suất:

```text
SEARLE:   z = -3.469382; p = 3.0196%
Pic2Word: z = -3.469382 + 1.205018; p = 9.4118%
```

Các xác suất này khớp miss rate tổng thể sau làm tròn; OR là tỷ số odds, không phải tỷ số trực tiếp của hai miss rate.

**M1 — sau khi thêm rank, N10 và in-degree.** OR của Pic2Word vẫn lớn hơn 1 và CI không chứa 1. Nghĩa là khi điều chỉnh theo ba biến này, chênh lệch gắn với tên mô hình vẫn còn trong mô hình thống kê. Không được gán toàn bộ mức giảm beta cho hubness, vì M1 thêm cả rank và kết nối đồ thị cùng lúc.

**M2 — sau khi thêm s1 và c_contrast.** Hệ số Pic2Word tiến gần 0 hơn, CI của OR chứa 1 và p-value lớn hơn 0,05. Diễn giải phù hợp: sau khi điều chỉnh thêm các đặc tính query này, dữ liệu chưa cho thấy chênh lệch còn lại theo tên mô hình có ý nghĩa thống kê. Không diễn giải thành “SEARLE và Pic2Word bằng nhau” hoặc “đặc tính query đã được chứng minh là nguyên nhân”.

#### 4.4.7. Các biến còn lại trong M2 nói gì?

| Biến | beta M2 | CI 95% của beta | p-value |
|---|---:|---|---:|
| `rank` | 0.0580 | [0.0373, 0.0787] | 4.03e-08 |
| `log_n10` | 0.3884 | [0.2223, 0.5545] | 4.59e-06 |
| `log_indeg` | -1.4994 | [-1.6163, -1.3826] | 1.18e-139 |
| `s1` | -26.6774 | [-31.4652, -21.8897] | 9.15e-28 |
| `c_contrast` | 19.7197 | [14.4285, 25.0109] | 2.78e-13 |

Các dấu trong bảng là **liên hệ có điều kiện**: đọc từng biến khi các biến còn lại được giữ cố định trong mô hình.

- `rank` dương: neighbor ở thứ hạng thấp hơn (số rank lớn hơn) có odds bỏ sót cao hơn.
- `log_n10` dương: tần suất xuất hiện theo query cao hơn gắn với odds bỏ sót cao hơn sau điều chỉnh. Dấu này không ủng hộ dự đoán đơn giản “N10 thấp thì dễ bị bỏ sót hơn”.
- `log_indeg` âm: nhiều cạnh đi vào HNSW hơn gắn với odds bỏ sót thấp hơn. Điều này phù hợp với trực giác về khả năng tiếp cận trên đồ thị, dù chưa chứng minh quan hệ nhân quả.
- `s1` âm: điểm tương đồng cao nhất lớn hơn gắn với odds bỏ sót thấp hơn khi giữ cả c_contrast cố định.
- `c_contrast` dương: khi giữ s1 cố định, c_contrast tăng tương đương s100 giảm. Không thể đọc dấu này thành “query càng rõ ràng thì càng khó” vì đó là một so sánh có điều kiện, và hai biến cùng chứa s1 theo định nghĩa.

Để tránh đọc nhầm thang đo, các OR sau được tính từ hệ số M2; độ tăng là **tình huống minh họa**, không phải một thí nghiệm can thiệp:

- Rank tăng 1: odds nhân với 1.060.
- N10 từ 1 lên 4: odds nhân với 1.427.
- In-degree từ 9 lên 19: odds nhân với 0.354.
- s1 tăng 0,01, giữ c_contrast cố định: odds nhân với 0.766.
- c_contrast tăng 0,01, giữ s1 cố định: odds nhân với 1.218.

Intercept của M2 ứng với mọi biến đầu vào bằng 0, gồm cả rank bằng 0 — nằm ngoài miền rank quan sát. Vì vậy không nên diễn giải riêng Intercept thành miss rate điển hình của SEARLE.

#### 4.4.8. QIC là gì và vì sao giảm lại đáng chú ý?

**QIC (Quasi-likelihood under the Independence model Criterion)** là tiêu chí so sánh mô hình GEE, cân nhắc độ phù hợp với dữ liệu và độ phức tạp. Với cùng dữ liệu và cách tính tương thích, giá trị nhỏ hơn được ưu tiên. Giá trị QIC tuyệt đối không phải phần trăm lỗi; QIC giảm không có nghĩa retention tăng, vì HNSW không được thay đổi khi chạy hồi quy. Xem [tài liệu QIC của statsmodels](https://www.statsmodels.org/v0.11.1/generated/statsmodels.genmod.generalized_estimating_equations.GEE.qic.html).

Trong bảng hiện tại, QIC giảm từ M0 qua M1 đến M2. Điều này ủng hộ việc các biến bổ sung giúp mô tả dữ liệu theo tiêu chí QIC. Nó không thay thế kiểm định một nhóm hệ số, không chứng minh khả năng dự đoán trên dữ liệu mới, và không xác nhận cơ chế nhân quả. Mã hiện tại không báo cáo đánh giá ngoài mẫu hay kiểm định Wald chung cho từng nhóm biến. Không dùng máy móc likelihood-ratio test của logistic maximum likelihood cho các kết quả GEE này.

#### 4.4.9. Có thể kết luận gì từ đường beta M0 → M1 → M2?

**Có thể nói:** hệ số gắn với Pic2Word giảm sau khi bổ sung các biến neighbor/graph và giảm thêm khi bổ sung đặc tính query. Trong M2, N10 và in-degree có liên hệ với lỗi theo hai hướng khác nhau; chênh lệch còn lại theo tên mô hình chưa có ý nghĩa thống kê.

**Chưa thể nói:** “hubness giải thích chính xác bao nhiêu phần trăm chênh lệch” hoặc “query features là nguyên nhân duy nhất”. Ngoài việc thêm nhiều biến cùng lúc, odds ratio trong hồi quy logistic có tính *non-collapsibility*: hệ số trước và sau điều chỉnh có thể khác nhau ngay cả khi không có nhiễu theo nghĩa nhân quả. Vì thế, tỷ lệ giảm beta không tự động là tỷ lệ hiệu ứng được trung gian hóa. Xem [nghiên cứu phương pháp về thay đổi hệ số giữa các mô hình logistic lồng nhau](https://doi.org/10.1177/0081175012444861).

Ngoài ra, các biến như N10, in-degree và điểm tương đồng được đo trong không gian embedding riêng của từng mô hình. “Giữ các biến khác cố định” là cách diễn giải phương trình, không có nghĩa thí nghiệm đã thực sự tạo ra hai hệ embedding giống nhau ở mọi yếu tố còn lại. Cần kiểm tra miền giá trị chồng lấp, dạng hàm, tương tác, độ ổn định giữa các cấu hình và thiết kế can thiệp trước khi suy luận mạnh hơn.

**Câu kết luận dùng cho báo cáo:** “Phân tích GEE logistic với các tập biến lồng nhau cho thấy chênh lệch odds bỏ sót giữa Pic2Word và SEARLE giảm sau điều chỉnh các đặc tính neighbor, đồ thị và query. Kết quả gợi ý vai trò thống kê của các đặc tính này trong việc mô tả chênh lệch, nhưng chưa phân lập đóng góp nhân quả của hubness; việc hệ số mô hình không còn có ý nghĩa thống kê ở M2 không chứng minh hai mô hình tương đương.”

### 4.5. Can thiệp centering

Biến thể centering: `subtract_gallery_mean_without_renormalization`.

| Mô hình | Rank invariance | Delta skewness | Delta Retention@10 | Nhãn nhân quả |
|---|---:|---:|---:|---|
| SEARLE | True | 0.0000 | 0.09% | inconclusive |
| PIC2WORD | True | 0.0000 | 4.38% | inconclusive |

## 5. Kết luận & Đánh giá Giả thuyết

- **Trạng thái H1:** **CHƯA KẾT LUẬN**.
- **Trạng thái H2:** **CHƯA KẾT LUẬN**.

**Bằng chứng quyết định từ số liệu:**
- Anti-hub miss rate ở bảng neighbor-level: SEARLE N/A, Pic2Word N/A; hai giá trị là N/A do không có quan sát `N10=0` trong exact top-10.
- beta_model qua M0 -> M1 -> M2: 1.2050 -> 0.8987 -> 0.0901.

Phân tích hiện tại cho thấy cần diễn giải hubness như một yếu tố liên quan đến miss rate trong cấu hình đo cụ thể, không phải bằng chứng đơn lẻ đủ để khẳng định cơ chế nhân quả tổng quát. Kết luận cuối cùng phụ thuộc vào mức suy giảm của beta_model sau M1 và kết quả can thiệp centering trong JSON.

## 6. Hạn chế Thực nghiệm

- Phân tích dùng một gallery CIRCO gồm 123403 ảnh và một cấu hình HNSW tham chiếu.
- GEE không tương đương hồi quy logistic likelihood chuẩn; QIC được dùng khi thư viện hỗ trợ.
- Can thiệp centering giữ thứ hạng exact bằng cách không re-normalize gallery sau khi trừ mean; kết quả có thể khác nếu thay đổi metric hoặc chuẩn hóa.

## 7. Các bước Tiếp theo

1. Chạy thêm cấu hình stress-test HNSW `M=16`, `efSearch=32` để kiểm tra độ bền.
2. Tạo file bằng chứng P0.1-P0.4 trong `R2_Audit/p0_audit_checklist/` từ các JSON đã sinh.
3. Không cập nhật tổng kết Stage A cho tới khi các module A.2-A.5 được rà soát theo cùng quy tắc.
