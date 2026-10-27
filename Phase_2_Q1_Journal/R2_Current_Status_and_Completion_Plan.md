# Đánh giá hiện trạng và kế hoạch hoàn thiện R2 — Phase 2 Stage A

**Ngày đánh giá:** 15/10/2026.  
**Căn cứ:** [R2_Fixing_Plan.md](./R2_Fixing_Plan.md), đặc biệt Mục 7 (thứ tự và khối lượng), Mục 8 (hồ sơ cần nộp), và quy chuẩn mentor-audit-protocol.  
**Phạm vi:** kiểm kê và đọc mã nguồn, JSON, báo cáo đang có trong workspace; không chạy lại thí nghiệm nặng trong lần đánh giá này. Đây là kế hoạch triển khai, không phải xác nhận đã hoàn tất P0–P4.

## 1. Kết luận về hiện trạng

**Dự án đã có nền thực nghiệm cũ của cả năm module và một pipeline R2 khá đầy đủ cho A.1, nhưng chưa đủ điều kiện đóng gói báo cáo P0–P2 để nộp mentor.** Việc ưu tiên là sửa các mâu thuẫn còn tồn tại trong báo cáo, nối mã thực nghiệm vào cấu hình chung, rồi hoàn thiện A.2/A.5 và các thiếu sót của A.1.

- Checklist hiện ghi P0.1–P0.4 đã hoàn thành; có bốn file evidence tương ứng. P0.5–P0.13 còn mở. Đây là số mục được đánh dấu, **không phải phần trăm hoàn thành toàn dự án**.
- A.1 đã có dữ liệu neighbor-level, bốn JSON kết quả, ba hình và script sinh báo cáo. Có thể tái sử dụng phần lớn công việc, nhưng “đã chạy” chưa đồng nghĩa “đã đáp ứng toàn bộ giao thức R2”.
- A.2 R2 mới có `PLAN.md`; chưa thấy bộ script/kết quả R2 tại thư mục module này. A.5 chưa thấy sản phẩm của thiết kế N cố định/quét N theo R2.
- `reference.yaml` đã tồn tại, nhưng chưa trở thành nguồn cấu hình được các script Stage A và A.1 R2 đang kiểm tra đọc thống nhất.
- Bản tổng kết vẫn ghi “HOÀN THÀNH 100%” và giữ các kết luận cũ trái với trạng thái hiện tại. Không dùng bản này làm hồ sơ nộp hiện hành.

**Quy tắc trạng thái:** “Có artifact” nghĩa là tìm thấy sản phẩm; “Đạt nghiệm thu” yêu cầu đối chiếu dữ liệu, cấu hình, phương pháp, lời văn và khả năng tái lập. Với P3/P4, “chưa thấy” được giới hạn trong cây mã/kết quả Phase 2 và R2 đã rà soát, không khẳng định không có thử nghiệm ở mọi nơi khác.

## 2. Bản đồ tiến độ theo Mục 7

| Bước | Yêu cầu trong kế hoạch gốc | Hiện trạng có bằng chứng | Đánh giá hiện tại |
|---|---|---|---|
| P0 | Sửa 13 lỗi; viết lại kết luận; sinh bảng từ JSON | Checklist đóng 4 mục A.1; các lỗi A.2–A.5/tổng kết vẫn hiện diện | **Đang làm; chưa nghiệm thu toàn bộ** |
| P1 | Cấu hình chung; metadata; RC/LID; chạy lại phần bị ảnh hưởng | Có YAML nhưng còn tham số đặt trực tiếp, thiếu metadata và lệch số query/số luồng | **Có khung; chưa tích hợp đầy đủ** |
| P2a | A.2: nhiễu có dấu, phân rã, đường cong hoán vị, m = 8/16/32/64 | Có code/JSON cũ và kế hoạch A.2; chưa thấy kết quả R2 tương ứng | **Chưa triển khai pipeline R2** |
| P2b | A.1: 1.020 query, neighbor-level, in-degree, M0–M2, centering | Có pipeline và kết quả; báo cáo đã bổ sung giải thích hồi quy | **Đã có kết quả; cần bổ sung và chuẩn hóa** |
| P2c | A.5: N cố định và quét N | JSON cũ gồm 8 cặp model/dataset và tương quan thô | **Chưa thấy thực nghiệm R2 đáp ứng yêu cầu** |
| Mốc báo cáo | Gửi kết quả P0–P2 để trao đổi trước P3–P4 | Chưa đủ các sản phẩm A.2/A.5 và checklist P0 | **Chưa sẵn sàng** |
| P3a | Distractor, matched retention, mAP theo N | Có benchmark cũ đến 500K; nguồn distractor và chất lượng mở rộng chưa được nghiệm thu | **Có nền cũ; chưa đạt kiểm định R2** |
| P3b | Đối chứng truy vấn ảnh/CIR, H-MG | Chưa thấy pipeline/kết quả đối chứng tương ứng trong Phase 2/R2 | **Chưa có bằng chứng hoàn thành** |
| P4 | Baseline C, bộ nhớ/độ trễ/retention, Pareto | Chưa thấy bộ báo cáo Pareto R2 hoàn chỉnh | **Chưa nghiệm thu; làm sau mốc P0–P2** |

## 3. Bằng chứng và vấn đề cần giải quyết

### 3.1. P0: báo cáo vẫn chưa đồng bộ với dữ liệu

Nguồn kiểm tra: [checklist P0](./R2_Audit/P0_AUDIT_CHECKLIST.md), [evidence A.1](./R2_Audit/p0_audit_checklist/), và [các báo cáo Stage A](./reports/stage_A/).

| Phần | Quan sát trực tiếp | Việc cần hoàn thiện |
|---|---|---|
| A.1 / P0.1–P0.4 | Có evidence cho số liệu cũ; báo cáo hiện dùng N10 theo query và 1.020 query | Giữ rõ hai phiên bản thiết kế; không dùng skewness mới để thay thế hay “xác nhận lại” kết luận cũ |
| A.2 / P0.10–P0.11 | Báo cáo vẫn ghi “khớp hoàn hảo”, dựa vào dải 15–19 lần và diễn giải delta chưa thống nhất | Tách random/top-k, sửa nguồn delta, ghi rõ cái gì dữ liệu cũ chưa đo |
| A.3 / P0.7, P0.12 | Bảng SEARLE nprobe=8 là 86,18% nhưng lời văn 91,5%; nprobe=16 trong bảng là 92,36% nhưng lời văn 96,1% | Sinh cả bảng và câu diễn giải từ JSON; diễn giải là đồng nhất thức cấu trúc, sửa đề xuất Combiner |
| A.4 / P0.8–P0.9 | Tiêu đề hiện đã là 10K–500K; vẫn còn O(log N) và hình có tên `scale_crossover_1m.png` | Ghi P0.8 đã sửa một phần; kiểm tra hình thực tế; khớp log–log từ JSON, không gán độ phức tạp từ một dải đo hữu hạn |
| A.5 / P0.5–P0.6 | LID vẫn bị ghi “Yếu”; mục tiêu vẫn là chứng minh hubness “duy nhất” | Sửa bằng tương quan hiện có; tách tương quan thô khỏi ảnh hưởng N |
| Tổng kết / P0.13 | Vẫn có “HOÀN THÀNH 100%”, “định lý”, Combiner và link `file:///` | Viết lại trạng thái trung thực ngay ở P0; cập nhật kết quả cuối sau P2 |

JSON A.5 cũ xác nhận Spearman LID = −0,880952 (p = 0,003850), hubness = −0,857143 (p = 0,006530). Các giá trị này đủ bác bỏ cách mô tả LID “yếu hơn” trong báo cáo cũ, nhưng chưa chứng minh sức dự báo độc lập với N. Các kết quả riêng phần trong phản biện phải được tái tính và lưu thành artifact, không chép sang báo cáo như một kết quả mới đã chạy.

**Vấn đề quản lý tài liệu:** checklist có các đường dẫn bị vỡ dòng thành `esults/...`/`eports/...` và tên JSON không khớp tên file thực tế. Kế hoạch A.2 hiện nói `R2_Fixing_Plan.md` chủ yếu về A.1 và chưa có phản biện A.2; nhận định này đã lỗi thời so với bản R2 hiện có đầy đủ Mục 4.1. Cần cập nhật nguồn và tiêu chí A.2 trước triển khai.

### 3.2. P1: có file cấu hình nhưng chưa có giao thức thống nhất

Nguồn: [reference.yaml](../configs/reference.yaml), [script A.1](./R2_Audit/module_a1_revision/scripts/), [script Stage A cũ](../src/phase2/stage_a/).

| Hạng mục | Hiện trạng | Hành động cần làm |
|---|---|---|
| HNSW | YAML có reference/stress; script A.1 vẫn khai báo M/efSearch/efConstruction trực tiếp | Dùng loader chung; lưu cấu hình đã resolve cho từng run |
| Tập query | YAML ghi CIRCO 220 query; A.1 R2 dùng 1.020 query | Tách profile đo retention không cần GT và profile đánh giá có GT; lưu danh sách ID/split/hash |
| Số luồng | YAML yêu cầu 8; metadata Step 1 A.1 ghi 12 | Ghi số luồng thực tế, phân biệt số CPU logic và FAISS threads; chạy lại số chịu ảnh hưởng |
| Metadata | Step 1 có commit/hardware; Step 2–4 thiếu nhiều trường truy xuất nguồn | Dùng schema chung và liên kết tới run gốc; không điền ngược các thông tin lịch sử chưa biết như thể đã đo |
| IVF/PQ | YAML nlist=1024; báo cáo/code cũ có nlist=351 | Tách profile legacy/reference; không ghép kết quả thành một chuỗi đồng cấu hình |
| RC/LID | YAML đã nêu công thức/estimator/k/sample size; chưa có bằng chứng mọi module dùng cùng hàm | Cài đặt chung, nêu metric/k/self-neighbor/zero-distance; ghi khác biệt với ICRCV |
| Độ trễ | YAML có 1 warm-up và 7 lần đo | Xác nhận thực thi trong code; lưu CPU, threads, batch và từng lần đo |

Metadata mới tối thiểu gồm run ID, thời gian, seed, model/dataset, gallery/query size, split và ID/hash đầu vào, cấu hình index, chuẩn hóa vector, phần cứng, số luồng, phiên bản thư viện, commit hoặc lý do không có commit. Với bước phân tích hậu kỳ, lưu cả hash/đường dẫn artifact đầu vào. Không cần chạy lại bootstrap chỉ để đổi một trường mô tả đã xác minh; cần chạy lại khi thay đổi dữ liệu/cấu hình/phương pháp hoặc thiếu dữ liệu cần thiết.

### 3.3. P2b — A.1: kết quả có giá trị nhưng còn việc để nghiệm thu

Nguồn: [báo cáo A.1](./reports/stage_A/module_a1_hubness_report.md), [JSON R2](./R2_Audit/module_a1_revision/results/), [dữ liệu neighbor-level](./R2_Audit/module_a1_revision/data/neighbor_level_data.parquet).

**Đã có:** 1.020 query mỗi mô hình, tổng 20.400 dòng neighbor-level; đo in-degree tầng 0; bootstrap theo query; GEE logistic M0–M2; centering; script sinh báo cáo và giải thích chi tiết hồi quy.

**Kết quả cần giữ lại khi viết báo cáo cuối:**

- Nhóm N10=1–4 có miss rate quan sát thấp hơn các nhóm 5–9 và 10–29 ở cả hai mô hình; đây là nhận xét mô tả, không phải quy luật đơn điệu đã được chứng minh.
- Hệ số Pic2Word M0 → M1 → M2 là 1,2050 → 0,8987 → 0,0901; p của hệ số này ở M2 là 0,442658. Không chuyển mức giảm beta thành phần trăm tác động nhân quả của hubness.
- Centering Pic2Word: retention 90,5882% → 94,9706%, tăng 4,3824 điểm phần trăm; skewness theo query giữ nguyên 8,329795. Đây là cải thiện quan sát có giá trị, nhưng chưa chứng minh cơ chế “giảm hubness giúp tăng retention”.

**Phần còn thiếu/cần sửa:**

1. Bổ sung bảng miss rate theo **in-degree** cùng cỡ mẫu/CI; báo cáo hiện mới có bảng theo N10, còn in-degree chủ yếu xuất hiện trong thống kê tổng hợp và hồi quy.
2. Ghi số query, số neighbor duy nhất và số sự kiện miss trong từng nhóm. Nhóm SEARLE N10=10–29 chỉ có 23 dòng và 2 miss; CI chạm 0 là hệ quả bootstrap mẫu ít, không phải bảo đảm không lỗi.
3. Phân biệt N10 query→gallery và gallery→gallery trong báo cáo, tên trường và hình. N10=0 không thể xuất hiện trong bảng exact-neighbor; ngưỡng ≥30 không có quan sát trong kết quả hiện tại.
4. Đồng bộ cấu hình/metadata, xác minh query ID giữa hai mô hình và giải thích việc dùng GEE thay cho logit với clustered SE trong mã tham khảo của mentor.
5. Centering phải báo cáo thay đổi in-degree/cấu trúc đồ thị trước–sau. Query-N10 được bảo toàn về mặt toán học khi giữ query và không chuẩn hóa lại gallery; không dùng điều kiện “skewness query phải giảm” làm điều kiện để thí nghiệm được xem là có giá trị.
6. Sửa chú thích đầu script centering và nhãn trên hình đường beta: hiện còn suy diễn “retention tăng → bằng chứng nhân quả hubness” hoặc “beta giảm → giải thích cơ chế”. Giữ kết luận thận trọng đã bổ sung trong phần hồi quy của báo cáo.
7. Lưu miss/retention từng query trước–sau; tính CI cho chênh lệch bằng paired cluster bootstrap. Đề xuất xây HNSW lặp 5 lần để kiểm tra độ ổn định (yêu cầu 5 lần trong P4 được áp dụng sớm như tăng cường kiểm chứng, không gọi đây là kết quả đã có).
8. Kiểm tra rank invariance trên toàn bộ query; script hiện kiểm tra trực tiếp 50 query. Nếu chạy stress profile, tách kết quả khỏi reference.

### 3.4. P2a/P2c và phần tiếp theo

**A.2:** triển khai theo Mục 4.1 R2 mới nhất: lưu nhiễu có dấu trên random và exact top-50, phần song song/trực giao, norm vector tái tạo, kiểm tra đồng nhất thức, chênh nhiễu cặp liền kề và sự kiện đảo thứ tự. Quét m = 8/16/32/64; giữ query ID để tính CI theo cụm. Báo cáo g_5% thực nghiệm và dự báo, nêu rõ trường hợp dữ liệu không hỗ trợ một ngưỡng ổn định; không ép đường cong khớp Gaussian. Bảng g_5% chưa có thì chưa chốt hướng Score-Gap Loss.

**A.5:** JSON cũ chỉ gồm 8 cặp model/dataset với N khác nhau. Phải thiết kế lại hai nhánh: (a) so sánh hình học ở cùng N, với lấy mẫu lặp và truy xuất ID; (b) quét N trong cùng model/dataset. Báo cáo tương quan thô, riêng phần kiểm soát log N và bất định. Chọn N chung theo gallery khả dụng thực tế; không mặc định N=10K cho tập chỉ có vài nghìn ảnh. Tránh coi các tập con lặp chồng lấp là các quan sát độc lập hoàn toàn.

**A.3:** ngoài sửa P0, kế hoạch module cần có phân phối thứ hạng cụm của exact neighbor, imbalance factor và margin; xác minh đồng nhất thức coverage/retention với cùng metric và quy tắc xử lý ties. Phần mở rộng có thể triển khai sau P0/P1, không che lấp nghĩa vụ ưu tiên P2a–P2c.

**A.4:** mã `build_distractor_scale.py` có nhánh tạo distractor Gaussian chuẩn hóa khi không có file phù hợp, và có nhánh nạp file tồn tại. Đây là rủi ro cụ thể cần kiểm tra provenance của file đã dùng; chưa đủ để kết luận chắc chắn lần chạy cũ dùng nhánh nào. Nếu xác nhận distractor ngẫu nhiên, kết quả có thể giữ như benchmark tải tổng hợp nhưng không dùng để khẳng định độ khó truy hồi ảnh thật theo N.

## 4. Kế hoạch thực hiện và tiêu chí hoàn thành

Thứ tự ưu tiên giữ theo R2: **P0 → P1 → P2a/P2b/P2c → hồ sơ trao đổi mentor → P3 → P4**. A.1 đã làm trước được tận dụng; không cần làm lại toàn bộ, nhưng không dùng việc A.1 đã chạy để bỏ qua P0/P1 còn thiếu.

| Thứ tự | Công việc cụ thể | Sản phẩm cần có | Điều kiện đóng việc |
|---|---|---|---|
| 1 | Kiểm kê JSON legacy, sửa 9 mục P0 còn mở; rà lại evidence A.1 | 5 báo cáo + tổng kết có trạng thái đúng; 13 evidence; checklist sửa link | Mỗi số và kết luận truy xuất được; không còn lỗi P0 đã liệt kê; nhãn “chưa có dữ liệu” cho phần chưa chạy |
| 2 | Tích hợp config, metadata, query profile, RC/LID, timing | Loader/schema chung; YAML cập nhật; manifest run | Script ghi cấu hình thực dùng; có danh sách số phải chạy lại và lý do |
| 3 | A.2 smoke run rồi quét đủ m | Dữ liệu có dấu; decomposition; đường cong đảo hạng; bảng g_5%; report | Kiểm tra đại số đạt; đủ m/model; CI và cỡ mẫu rõ; không dùng p95 thay CI |
| 4 | Hoàn thiện A.1 và kiểm chứng centering | Bảng in-degree; bảng hệ số/OR; paired CI; kết quả lặp; report | Giữ rõ query-hubness/graph; metadata đầy đủ; không kết luận nhân quả từ beta/skewness |
| 5 | A.5 N cố định + quét N | Dataset manifest, RC/LID thống nhất, tương quan thô/riêng phần và CI | Kiểm soát N; nêu cỡ mẫu hiệu dụng; giả thuyết có nhãn theo dữ liệu |
| 6 | Audit chéo và đóng gói P0–P2 | Bộ hồ sơ Mục 5 dưới đây | Số liệu giữa JSON/bảng/hình/tổng kết khớp; hạn chế được ghi; sẵn sàng người dùng gửi mentor |
| 7 | P3a: provenance/dedup/distractor top-10/mAP/matched retention | Báo cáo kiểm định A.4 | Đạt điều kiện dữ liệu thật và chất lượng; chỉ báo speedup tại retention ≥95% nếu thực sự đạt |
| 8 | P3b: H-MG trên cùng gallery/index | CIR vs image query; phân tầng s1; CI | Ảnh query được loại khỏi gallery và không là GT; dùng cùng index; không trộn tập query |
| 9 | P4: baseline C | Bảng retention/latency/memory; biên Pareto | So ở ngân sách hoặc chất lượng tương đương; HNSW 5 lần dựng; tính cả bộ nhớ rerank |

P3/P4 chỉ thực hiện sau khi hoàn tất hồ sơ P0–P2 và có trao đổi theo mốc mentor yêu cầu. Lần lập tài liệu này không tự gửi thông tin cho mentor và không bắt đầu các thí nghiệm mới.

## 5. Kế hoạch báo cáo và hồ sơ nộp

### 5.1. Hồ sơ P0–P2

- [ ] Năm báo cáo A.1–A.5 theo khung 7 phần và bản tổng kết viết lại.
- [ ] Bảng đối chiếu đủ 13 mục P0: vấn đề cũ → số liệu nguồn → sửa ở đâu → evidence → trạng thái.
- [ ] YAML, schema metadata, run manifest và lệnh tái tạo bảng/hình; đánh dấu kết quả legacy/reference/stress.
- [ ] A.2: mean/std nhiễu có dấu, decomposition, norm reconstruction, sigma_d, đường cong hoán vị và g_5% theo m.
- [ ] A.1: miss rate theo N10 và in-degree, cỡ mẫu/CI, M0–M2, centering trước/sau, độ ổn định và kết luận có nhãn.
- [ ] A.5: thiết kế N cố định/quét N, bảng tương quan thô và riêng phần, hạn chế về cỡ mẫu.
- [ ] Một trang tổng hợp: mỗi giả thuyết một dòng gồm nhãn, bằng chứng quyết định, giới hạn và bước tiếp theo.

**Cấu trúc một dòng tổng kết:** `Giả thuyết | Đơn vị phân tích/profile | Kết quả/CI/p | Nhãn | Giới hạn | Link JSON/report`. Không ép mọi module phải có kết quả dương. Không dùng một nhãn “DONE” cho cả việc chạy chương trình và việc xác nhận giả thuyết.

### 5.2. Cách ghi nhận đóng góp A.1 trong báo cáo cuối

Giữ riêng ba lớp kết luận: (1) quan hệ thống kê giữa N10/in-degree và miss; (2) sự thay đổi hệ số qua M0–M2; (3) cải thiện retention quan sát được sau centering. Nhãn “chưa kết luận nhân quả hubness” không phủ nhận mức tăng 4,3824 điểm phần trăm của Pic2Word. Báo cáo phải ghi nhận cải thiện này cùng giới hạn: chưa có CI chênh lệch, lặp dựng chỉ mục và bằng chứng cấu trúc đồ thị trước–sau trong kết quả hiện tại.

### 5.3. Cập nhật tiến độ khi triển khai

Sau mỗi bước: cập nhật README R2, checklist P0 và tài liệu này; ghi ngày chạy/run ID, artifact mới, kết quả kiểm tra và việc còn thiếu. Các báo cáo đang được sửa phải ghi rõ “bản làm việc”; bản tổng kết cuối chỉ lấy từ các artifact đã nghiệm thu. Không sửa số liệu legacy; lưu lịch sử và liên kết sang bản thay thế.

## 6. Khối lượng còn lại và lịch đề xuất

Đây là **ước lượng ngày công**, không phải thời gian máy đã đo hoặc cam kết ngày kết thúc. Giả định một người phụ trách, dữ liệu/embedding hiện có dùng được và không phải tái tạo toàn bộ gallery. Thời gian chờ mentor, tải/encode ảnh, sửa lỗi dữ liệu và chạy máy lớn được tính riêng.

| Phần | Ước lượng Mục 7 gốc | Ước lượng còn lại từ hiện trạng | Lý do |
|---|---:|---:|---|
| P0 | 1–2 ngày | 1–2 ngày | 9 mục còn mở, thêm đồng bộ script và tổng kết |
| P1 | 1–2 ngày | 1–2 ngày | Có YAML nhưng cần tích hợp và metadata |
| P2a | 2 ngày | 2–3 ngày | Chưa có pipeline R2; thêm lưu raw/CI và kiểm tra reconstruction |
| P2b | 3–4 ngày | 1–2 ngày | Tái sử dụng pipeline; bổ sung in-degree, lặp/CI và sửa diễn giải |
| P2c | 2 ngày | 2–3 ngày | Thiết kế lại N và kiểm tra khả dụng dữ liệu |
| Audit/đóng gói P0–P2 | Chưa tách riêng | 1 ngày | Đối chiếu số liệu, link, bảng/hình và trang tóm tắt |
| P3a | 2 ngày | 2–4 ngày | Phụ thuộc provenance distractor; chưa tính tải/encode tập ảnh mới |
| P3b | 2–3 ngày | 2–3 ngày | Chưa có pipeline đối chứng được xác minh |
| P4 | Khoảng 1 tuần | 5–7 ngày | Quét baseline, lặp chỉ mục, đo bộ nhớ/latency và Pareto |

**Mốc P0–P2:** khoảng **8–13 ngày công** còn lại, chưa tính chờ máy/phản hồi. **P3–P4 sau đó:** khoảng **9–14 ngày công**. Tổng dự kiến **17–27 ngày công**, có thể vượt khung 3–4 tuần của kế hoạch gốc nếu phải thay distractor hoặc bổ sung embedding. Không cộng lại thời gian A.1 đã thực hiện.

Lịch triển khai tham chiếu: tuần đầu đóng P0/P1 và bắt đầu A.2; tuần tiếp theo hoàn thiện A.2/A.1/A.5; dành phần đầu tuần kế nếu cần để audit và chuẩn bị hồ sơ. Sau mốc trao đổi mentor mới lên lịch chi tiết P3/P4. Chốt lại ước lượng sau smoke run A.2 và kiểm kê dữ liệu A.5/distractor.

## 7. Rủi ro cần xử lý trước khi chạy lớn

| Rủi ro | Hệ quả | Cách xử lý |
|---|---|---|
| Mẫu query và profile bị trộn | So sánh retention lệch đơn vị | Manifest ID/split, tách đánh giá có GT và không GT |
| Tập CIRCO test không có GT khả dụng cục bộ | Không tính được mAP cho toàn bộ 1.020 query | Chỉ tính mAP trên split có nhãn hợp lệ hoặc giao thức đánh giá được phép; ghi rõ phạm vi |
| Query-N10 bị gọi là bậc HNSW hoặc gallery-hubness | Kết luận cơ chế sai | Tên biến/đồ thị/bảng nêu định nghĩa và đơn vị |
| Nhiều lần xuất hiện cùng một ảnh | CI gom query có thể chưa xử lý hết phụ thuộc | Báo số ảnh duy nhất; cân nhắc phân tích độ nhạy theo ảnh/query |
| Centering không đổi N10 nhưng thay quan hệ gallery | Nhãn nhân quả dựa trên skewness không phù hợp | Đo graph trước–sau, paired CI, lặp dựng; giới hạn kết luận |
| Distractor tổng hợp hoặc không rõ encoder | Speedup không đại diện bài toán ảnh thật lớn | Kiểm kê provenance, top-10 contribution và gần-trùng trước mở rộng |
| Script cũ sinh lại lời văn sai | Sửa Markdown bị ghi đè khi chạy lại | Sửa cả renderer, kiểm tra bảng/câu sinh từ JSON |
| Thiếu metadata lịch sử | Không tái lập được một con số cũ | Giữ legacy với trường unknown; chạy lại phần cần thiết, không tạo provenance giả |

## 8. Danh mục nguồn đã kiểm tra

- [Kế hoạch R2 đầy đủ](./R2_Fixing_Plan.md).
- [Checklist P0](./R2_Audit/P0_AUDIT_CHECKLIST.md) và [README trạng thái](./R2_Audit/README.md).
- [Evidence P0.1–P0.4](./R2_Audit/p0_audit_checklist/).
- [Cấu hình tham chiếu](../configs/reference.yaml).
- [Mã Stage A cũ](../src/phase2/stage_a/) và [JSON Stage A cũ](../data/results/phase2_stageA/json/).
- [Kế hoạch A.2 hiện có](./R2_Audit/module_a2/PLAN.md).
- [Mã A.1 R2](./R2_Audit/module_a1_revision/scripts/), [JSON A.1 R2](./R2_Audit/module_a1_revision/results/) và [báo cáo A.1](./reports/stage_A/module_a1_hubness_report.md).
- [Báo cáo A.2](./reports/stage_A/module_a2_pq_perturbation_report.md), [A.3](./reports/stage_A/module_a3_ivf_routing_report.md), [A.4](./reports/stage_A/module_a4_scale_report.md), [A.5](./reports/stage_A/module_a5_geometry_power_report.md), [tổng kết](./reports/stage_A/stage_a_master_summary.md).

**Giới hạn lần đánh giá:** xác minh sự tồn tại và nội dung artifact, không tái chạy pipeline thực nghiệm, không chứng nhận provenance của mọi embedding và không đo thời gian máy. Các mục kế hoạch/ước lượng ở trên là đề xuất để hoàn thiện; chỉ đổi trạng thái khi có sản phẩm và kiểm tra tương ứng.


## Cập nhật thực hiện P0/P1/P2b

Phần đánh giá phía trên là snapshot trước triển khai. P0/P1/P2b nay đã có sản phẩm và kiểm tra theo [báo cáo hoàn thiện](./R2_Audit/P0_P1_P2b_COMPLETION_REPORT.md); P1 không tái xác nhận chuỗi scale mở rộng thiếu provenance. P2a/P2c/P3/P4 còn mở. Ước lượng cũ không phải khối lượng còn lại sau đợt này.
