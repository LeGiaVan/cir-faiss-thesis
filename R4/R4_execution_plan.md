# Kế hoạch thực hiện R4 theo phản biện mentor

**Trạng thái:** kế hoạch đề xuất, chưa chạy thực nghiệm R4.  
**Nguồn:** [feedback R4](./mentor_feedback_r4.txt), [kết quả C1–C5 R3](../R3/tong_hop_C1_C5.md), [đăng ký trước R3](../R3/stage0_preregistration.md) và các manifest/kết quả gốc của từng thí nghiệm.

## 1. Mục tiêu và cách tiếp cận

R4 cần kiểm tra một giả thuyết cụ thể: centering gallery có thể thay đổi phân bố cạnh HNSW theo **độ trung tâm của ảnh**, từ đó thay đổi khả năng tìm lại láng giềng của query CIR. Đồng thời, phải kiểm tra liệu lợi thế ở cùng chi phí của Pic2Word còn tồn tại khi cấu trúc đồ thị được đối chứng gần hơn về số cạnh.

Không coi giả thuyết đó là kết luận. Trước mỗi phép đo mới, ghi dự đoán, đại lượng chính, quy tắc quyết định, CI, cấu hình và đường dẫn dữ liệu; khóa phiên bản trước khi xem kết quả của phép đo đó. Giữ nguyên các dự đoán và kết quả đã đăng ký ở R3; mọi phân tích R4 sau khi đã biết kết quả R3 được ghi là **bổ sung dựa trên dữ liệu đã quan sát**, không gọi là kiểm định độc lập đã đăng ký từ đầu.

### Kết quả R3 cần giữ đúng khi bắt đầu

- **C1:** Pic2Word có lợi thế retention ở cùng `ndis` trong vùng khảo sát; với SEARLE, CI tại các ngân sách khảo sát chứa 0. Cùng `ndis` chưa kiểm soát mật độ hay bộ nhớ.
- **C3:** kết quả đối chứng L2 phù hợp với tính bất biến khi dịch cả hai phía; một query SEARLE đảo thứ tự hai ảnh gần hòa và tiêu chí xử lý được bổ sung sau quan sát. Không cần chạy lại C3 chỉ để lặp kết quả R3; không nói đồ thị giống hệt từng cạnh hay suy ra cơ chế IP đã được chứng minh.
- **C2:** trong các mức `M` đã thử, không đạt tiêu chí median số cạnh lệch ≤2%; đây là kết quả thực nghiệm và không phải đối chứng cùng mật độ.
- **C5:** kết quả tuyệt đối của Pic2Word ủng hộ một phần so sánh hai nhóm đầu cuối, nhưng không thỏa quy tắc đơn điệu đã đăng ký. So sánh này ở cùng `efSearch`, chưa khớp `ndis`.
- **C4:** MCS và N10 gallery thay đổi, phân phối in-degree thay đổi; chưa chứng minh nguyên nhân hay khẳng định HNSW mắc lỗi. Cần phân biệt N10 gallery, N10 theo query CIR và bậc vào đồ thị.

## 2. Thứ tự, cổng và sản phẩm

| Bước | Việc ưu tiên | Sản phẩm và điều kiện tiếp tục |
|---|---|---|
| 0 | Provenance, ID test, snapshot mã/config | Manifest ID và hash, đối chiếu vector cũ/mới; snapshot có commit sạch cho kết quả xác nhận hoặc báo rõ phần chưa đạt |
| 1 | D1–D3: độ trung tâm, N10, in-degree, exact neighbor | Bảng tương quan và phân phối; đánh giá các dự đoán trước khi mở rộng diễn giải |
| 2 | C2 mới: cắt cạnh centered để khớp bậc ra từng nút | Kiểm tra tính hợp lệ đồ thị; bảng độ khớp và hình retention–`ndis`, hai quy tắc cắt |
| 3 | Centering từng phần theo `λ` | Hình retention cùng `ndis`, số cạnh và tương quan độ trung tâm–in-degree theo `λ` |
| 4 | Tổng hợp bước 1–3 | Một trang dự đoán/kết quả/nhãn trạng thái, hình và hạn chế để người dùng có thể gửi mentor |
| 5 | C5 tương đối, GEE, so cùng `ndis`; bổ sung chi phí C1 | Bảng giảm miss tuyệt đối/tương đối, mô hình bổ sung, chi phí tại retention mục tiêu và bộ nhớ |
| 6 | Đối chứng query ảnh: D4 và mở rộng D3/D5 | Bảng so sánh loại query, độ trung tâm, retention/gain và giới hạn đối chứng |
| 7 | C6: độ khái quát | Thiết kế và bảng multi-dataset/config theo điều kiện dữ liệu và tài nguyên thực tế |

Feedback yêu cầu ưu tiên D1–D3 vì có thể chuẩn bị từ dữ liệu sẵn có, đồng thời xếp **xác minh ID test và commit sạch trước kết quả xác nhận**. Vì vậy có thể kiểm kê, viết mã và thực hiện kiểm tra thăm dò D1–D3 trên snapshot R3 trước trong khi giải quyết Bước 0; phải gắn nhãn thăm dò, không thay thế lần chạy xác nhận hay kết luận có provenance đầy đủ.

## 3. Bước 0 — Khóa provenance và xác minh 800 test query

1. Kiểm kê commit nền, working tree và submodule, phần cứng, môi trường FAISS/Python, config, model weights, gallery embeddings, query caches, annotation, scripts và kết quả R3; lập manifest SHA-256, seed và trạng thái tracked/untracked. Không dọn, ghi đè hoặc commit chung các thay đổi sẵn có của workspace.
2. Kiểm tra pipeline extractor và tính sẵn có của dataset/checkpoint. Trích lại 800 test query **gắn source ID trong cùng batch tạo feature**, kèm model, preprocessing, checkpoint, thứ tự và split. Đối chiếu mỗi ID với annotation, kiểm tra trùng/thiếu/số lượng; xác minh validation prefix và thứ tự target như R3.
3. So sánh feature mới với cache cũ theo ID, norm/cosine và sai số số học; đặt tolerance dựa trên môi trường/phương pháp trước khi thực hiện. Nếu thứ tự, nguồn ảnh, trọng số hoặc feature khác đáng kể, **không gán lại ID bằng suy đoán**: ghi khác biệt, xác định ảnh hưởng đến exact top-10 và retention; chạy lại các kết quả bị ảnh hưởng từ snapshot mới. Nếu không thể tái trích, báo rõ blocker và giữ mọi phân tích cũ theo nhãn hạn chế, không coi row-to-ID đã xác minh.
4. Chuẩn bị checkout/worktree hoặc snapshot mã/config có commit sạch, chứa đúng các tệp cần thiết mà không bao gồm embedding/data lớn; lưu hash data/weights riêng. Kiểm tra submodule và dependency dirty; commit phải mô tả chính xác mã chạy chứ không chỉ commit rỗng. Cách cô lập phải bảo toàn mọi thay đổi hiện có. Mỗi kết quả xác nhận phải có commit, config, SHA-256 đầu vào và metadata; nếu không đạt, không gắn nhãn confirmatory.
5. R3 có một số artifact nằm trong `.gitignore`; manifest phải ghi đường dẫn, kích thước, hash và nguồn khôi phục. Không giả định một clone sạch có sẵn các file local đó.

## 4. Bước 1 — D1–D3: kiểm định độ trung tâm

### 4.1. Đại lượng và dữ liệu

Với gallery đã L2-normalize, `μ = mean(x_j)`, `m = ||μ||`, `u = μ/m`, `a_j = x_j·u`, `a_z = (a_j − mean(a))/std(a)` trong **từng model**; `||x_j−μ||` được tính trực tiếp và đối chiếu đồng nhất thức `1 − 2m a_j + m²`. Kiểm tra `m>0`, norm vector, mean `a ≈ m`, sai số float và các giá trị không hợp lệ.

Dùng gallery CIRCO, hai backbone, exact top-10 CIR, N10 gallery trước/sau, in-degree trước/sau và năm seed từ R3 nếu chữ ký checkpoint xác minh được. Checkpoint C4 lưu `indegree`, `outdegree`, `found` cùng lượt dựng; giữ nguyên cặp original/centered theo seed và kiểm tra hash. **Các checkpoint C1/C2 không lưu đồ thị FAISS hoàn chỉnh**, nên không suy ra danh sách cạnh hay coi đồ thị dựng lại giống từng cạnh; nếu cần cạnh, phải dựng/lưu lại và gắn provenance mới.

### 4.2. Dự đoán và phép đo

- **D1:** tính Spearman `ρ(a, indegree_original)`, `ρ(a, indegree_centered)` và `ρ(a, indegree_centered − indegree_original)` cho từng model/seed; dự đoán lần lượt dương, âm, âm. Lưu từng seed, phân vị, ties và CI mô tả. Báo phân phối `a` theo quantile và bậc vào/ra; không rút ra nhân quả từ hệ số tương quan.
- **D2:** tính `ρ(a, N10_gallery_original)` và `ρ(||x−μ||, N10_gallery_centered)` riêng mỗi model; exact N10 là phía gallery, loại self theo ID. Dự đoán dương; đồng thời báo skewness/tỷ lệ N10=0 và phân vị, không diễn giải skewness một mình như chất lượng ngữ nghĩa.
- **D3:** so phân phối `a_z` của toàn gallery với các exact neighbor CIR, báo trung bình và phân vị 10/50/90, số ảnh khác nhau và số occurrence; dự đoán exact neighbor thiên về ngoại vi hơn trung bình gallery, và mức lệch Pic2Word lớn hơn sau chuẩn hóa trong từng model. Đơn vị chính là **query**: tính trung bình `a_z` của top-10 mỗi query rồi bootstrap query; không xem 10 neighbor và ảnh lặp giữa query là độc lập. Báo thêm thống kê theo ảnh duy nhất như độ nhạy; kiểm tra khả năng phụ thuộc do chia sẻ ảnh. So sánh hai backbone có CI/độ bất định, không kết luận từ chỉ hai giá trị điểm hay coi chuẩn hóa biến chúng thành cùng không gian.
- D1/D2 đo trên toàn gallery hữu hạn: báo hệ số từng seed; bootstrap ảnh chỉ là độ bất định mô tả có điều kiện, vì các bậc/N10 phụ thuộc cùng đồ thị và gallery. Dùng bootstrap theo seed khi phù hợp và ghi rõ nguồn bất định, không xem 123.403 nút như mẫu độc lập tuyệt đối. Nếu tính nhiều tương quan, báo CI/p-value, số phép so sánh và phương án hiệu chỉnh hoặc gắn nhãn thăm dò; không chỉ chọn tương quan đẹp.

**Cổng quyết định:** báo riêng từng dự đoán D1–D3 là ủng hộ, ủng hộ một phần, chưa kết luận hoặc không được ủng hộ theo dấu, độ lớn và CI. Nếu kết quả trái dự đoán, không diễn giải theo cơ chế đã định; giải thích liệu dữ liệu loại trừ dự đoán cụ thể hay CI còn rộng. Đề xuất ưu tiên bước tiếp theo dựa trên dữ liệu, không tự khẳng định mọi biến thể của giả thuyết bị bác bỏ chỉ từ một hệ số.

## 5. Bước 2 — C2 mới: khớp bậc ra từng nút bằng cắt cạnh

### 5.1. Thiết kế

Trong từng model và seed, dựng và lưu **cặp đồ thị mới**: original IP `M=32` và centered IP `M=32`, `efConstruction=200`; giữ cùng input, thứ tự ID thêm, metric và seed, nhưng không giả định đa luồng dựng được đồ thị giống R3. Đếm số cạnh có hướng hợp lệ tầng 0, bậc vào/ra, tỉ lệ nút đạt trần `2M`, số slot/ô trống, và mức khác nhau từng nút. Tỉ lệ sát trần thấp là bằng chứng về mức sử dụng slot trong đồ thị đo, không tự chứng minh nguyên nhân hoặc toàn bộ hành vi của bộ lọc.

Với mỗi nút `i`, đặt `k_i = outdegree_original(i)`. Tạo **hai bản sao độc lập của cùng đồ thị centered** rồi chỉ sửa tầng 0:

1. **Nearest:** giữ tối đa `k_i` cạnh hiện có có IP lớn nhất trong không gian gallery centered không chuẩn hóa lại; khóa quy tắc xử lý tie theo ID.
2. **Random:** chọn tối đa `k_i` cạnh hiện có theo ngẫu nhiên, lặp **3 seed cắt** cho mỗi seed dựng. Ba phép cắt lồng trong cùng đồ thị, không coi là 15 seed dựng độc lập.

Nếu centered có ít hơn `k_i` cạnh tại nút nào, giữ toàn bộ cạnh hiện có; báo số/tỷ lệ nút thiếu, tổng chênh cạnh và phân phối sai lệch từng nút. Vì vậy không gọi là khớp chính xác toàn bộ dãy bậc khi vẫn có nút thiếu. Tầng trên được giữ nguyên; cả hai bản cắt phải cùng xuất phát từ bản centered chưa cắt, không cắt nối tiếp.

### 5.2. Kiểm thử bắt buộc trước phép đo

- Kiểm tra trực tiếp bố trí `offsets`, số slot tầng 0 và ý nghĩa `-1` bằng FAISS 1.15.1; tạo chỉ mục nhỏ để kiểm thử việc sửa bộ nhớ SWIG, compact ID hợp lệ lên đầu và lấp `-1` phía sau. Không sửa slot thuộc tầng trên; xác minh hash/cấu trúc các tầng trên trước/sau.
- Xác minh tất cả ID cạnh hợp lệ, không cạnh tự thân/ID lặp nếu cấu trúc gốc có yêu cầu đó; tổng in-degree bằng tổng out-degree; bậc ra sau cắt đạt target với mọi nút đủ cạnh, báo các nút thiếu. Kiểm tra exact ranking không đổi, tìm thử nhiều query, không crash/không trả ID lỗi; đo số nút không có cạnh ra và khả năng truy cập, báo nếu xuất hiện vấn đề kết nối. Ghi rõ cắt cạnh có hướng có thể phá tính đối xứng/kết nối của đồ thị gốc.
- So original, centered chưa cắt, centered cắt nearest và centered cắt random. Quét `efSearch=[32,48,64,96,128,160,192,256,384]`, 5 seed dựng; đo `ndis/query`, retention@10, latency, cạnh, bậc vào và metadata. Lưu theo từng query/seed/cắt và giữ original/centered trước cắt làm đối chứng.

### 5.3. Phân tích và diễn giải

Chọn trước 5 ngân sách `ndis` cách đều trên thang log trong miền giao của các đường được so sánh; nội suy retention tuyến tính theo `ndis`, không ngoại suy; báo độ nhạy theo log-`ndis`. Bootstrap ghép cặp seed dựng/query, lồng seed cắt ngẫu nhiên theo đồ thị, 2.000 lần; báo CI từng điểm và tất cả seed. Nếu không có miền giao hoặc độ khớp cạnh kém, báo giới hạn và không gọi là so sánh cùng mật độ.

Nếu lợi thế giảm, mất đi hoặc còn lại, mô tả mức chênh và CI. Việc cắt cạnh thay đổi **cả số lượng, danh tính cạnh, bậc vào và khả năng kết nối**; ngay cả khi bậc ra khớp hoàn toàn, kết quả không tự tách nhân quả hoàn toàn “mật độ” khỏi “cạnh nào được giữ”. So hai quy tắc nearest/random để kiểm tra độ nhạy, không gọi CI chứa 0 là chứng minh lợi ích biến mất.

Chiều ngược lại — bổ sung cạnh cho original từ exact top-100 — là **đối chứng tùy chọn**, chỉ làm sau khi thiết kế, quy tắc chọn cạnh, tính hợp lệ và chi phí được ghi trước; không tự coi đồ thị bổ sung là HNSW dựng chuẩn.

## 6. Bước 3 — Liều–đáp ứng với centering từng phần

Dựng `y_j = x_j − λμ` với `λ ∈ {0, 0.25, 0.5, 0.75, 1, 1.25}`, không chuẩn hóa lại. Khóa trước M, `efConstruction`, seed, sweep efSearch và ngân sách chung; dùng cùng gallery/query, ID và exact ground truth IP. Với mọi `λ`, kiểm tra đồng nhất thức `q·(x−λμ)=q·x−λq·μ`, sai số float và exact top-10/tie trước khi diễn giải.

Với từng model/`λ`/seed: đo retention–`ndis`, số cạnh tầng 0, phân phối bậc vào và `ρ(a, indegree)`, thời gian/bộ nhớ dựng nếu đo được. So tại các `ndis` chung có dữ liệu của tất cả đường cần so, nội suy như C1 và báo CI ghép cặp; không ngoại suy. Báo cả đường từng seed và trung bình, các điểm `λ=0`/`1` là mốc R4 dựng lại, không khẳng định giống đồ thị R3.

**Dự đoán:** tương quan in-degree với `a` có xu hướng giảm/đổi dấu khi `λ` tăng và Pic2Word có thể cải thiện retention cùng chi phí. Báo cả trường hợp phi đơn điệu, cực đại tại `λ` trung gian, hiệu ứng âm hoặc CI chồng 0. Liều–đáp ứng hỗ trợ một cơ chế khả dĩ nhưng số cạnh và topology cũng thay đổi; không gọi là bằng chứng nhân quả quyết định hay chọn `λ` tốt nhất trên cùng bộ dữ liệu rồi báo như xác nhận độc lập.

## 7. Bước 4 — Gói kết quả gửi mentor

Sau Bước 1–3, tạo báo cáo và một trang tóm tắt gồm: dự đoán đã ghi trước, kết quả từ JSON theo từng model, nhãn trạng thái, CI, số seed và giới hạn provenance; bảng D1–D2, phân phối D3, hình C2 khớp bậc với số nút không khớp, và hình `λ`. Nêu rõ nhánh thăm dò nếu Bước 0 chưa đạt. Soạn nội dung sẵn để người dùng duyệt; **không tự gửi email/tin nhắn cho mentor**.

## 8. Bước 5 — C5 trên thang tương đối và bổ sung C1

### 8.1. C5 và hiệu ứng trần

Giữ nguyên bảng gain tuyệt đối và quy tắc 5 nhóm đã đăng ký R3. Với từng backbone và quintile `s1`, tính `miss_before=1−ret_before`, `miss_after=1−ret_after`, giảm tuyệt đối và giảm tương đối `(miss_before−miss_after)/miss_before`; ghi rõ tính **tỷ số của miss trung bình nhóm**, không nhầm với trung bình tỷ số từng query. Nếu mẫu số bằng 0 hoặc gần 0, báo không xác định/CI không ổn định; không chia cho 0. Bootstrap query ghép cặp và độ nhạy query×seed, 2.000 lần; báo CI, số query và biến thiên theo seed.

Khớp GEE nhị thức bổ sung `missed ~ s1z * centered`, cluster query, trên dữ liệu neighbor/seed/biến thể đã ghép; khóa cách chuẩn hóa `s1z` trong từng model, cấu trúc tương quan làm việc, SE/CI và kiểm tra hội tụ trước khi chạy. Chú ý cùng ảnh có thể xuất hiện ở nhiều query và cùng query lặp qua seed: cluster query chưa xử lý hết phụ thuộc; báo độ nhạy theo ảnh/seed nếu khả thi. Hệ số tương tác ước lượng thay đổi **trên thang log-odds/odds ratio**, không đồng nhất với giảm miss tương đối trên thang risk ratio. Tương tác không có ý nghĩa hoặc CI chứa 0 **không chứng minh hiệu ứng đồng đều**; chỉ đánh giá tương đương nếu ngưỡng và kiểm định tương đương được đăng ký trước.

Làm lại C5 tại cùng `ndis` bằng per-query C1: trước tiên xác định các điểm ngân sách và miền giao giữa mọi seed/biến thể; nội suy retention từng query như C1 rồi phân nhóm theo `s1` cố định, báo CI ghép cặp và độ nhạy nội suy. Nếu muốn diễn giải miss/relative reduction từ nội suy, ghi rõ đó là ước lượng dựa trên nội suy, không phải miss nhị thức quan sát tại một efSearch. GEE chính ở trên dùng dữ liệu nhị thức quan sát; không đưa fractional miss nội suy vào GEE như quan sát Bernoulli. Nếu một nhóm không có hỗ trợ chi phí, không ngoại suy.

### 8.2. Chi phí tại cùng retention

Mở rộng sweep **original Pic2Word** với `efSearch=512,768` trên đủ năm seed để kiểm tra mục tiêu 97%; giữ nguyên dữ liệu sweep R3, lưu lượt bổ sung và manifest riêng. Nhất quán cấu hình và truy vấn; nếu phải dựng lại đồ thị vì R3 chưa lưu index, ghép sweep cũ/mới chỉ khi cùng đồ thị được xác minh, nếu không thì đo lại toàn bộ đường trên các đồ thị mới và báo riêng.

Tại các retention mục tiêu `{90%,95%,97%}`, chỉ nội suy log-`ndis` trong miền đo đạt mục tiêu; không ngoại suy. Quy định trước cách xử lý đường phi đơn điệu, điểm hòa và mục tiêu không đạt; báo số seed/bootstrap không đạt, không bỏ các lần thất bại rồi trình bày CI như mẫu đầy đủ. Bootstrap ghép seed/query; báo CI cho chi phí từng phương án và tỷ lệ tiết kiệm, phương án lấy trung bình trước/sau nội suy và độ nhạy.

#### Giao thức chi phí theo làm rõ của mentor ngày 29/10/2026

**`ndis/query` vẫn là đại lượng chi phí chính** để kết luận về centering; latency là số liệu bổ sung phụ thuộc máy và cách chạy. Không dùng các cột latency R3 đo bằng vòng lặp `search` từng query (`batch=1`) làm latency cho bảng R4. Giữ R3 để truy vết, ghi rõ giao thức khác nhau.

Đo latency ở **hai chế độ**, dùng cùng tập query, metric, `k`, cấu hình máy và phạm vi bấm giờ giữa các phương án trong từng chế độ. Chuẩn bị sẵn query liên tục `float32`, không tính thời gian tạo query/chuẩn hóa/dựng index; ghi rõ phần slice, gọi FAISS và gom kết quả nào nằm trong thời gian đo. Chạy trên máy không có thí nghiệm nặng đồng thời, ghi CPU, số lõi/luồng khả dụng thực tế, phiên bản FAISS, hệ điều hành, batch, `k`, số lần đo, số luồng FAISS và các giá trị thời gian thô.

1. **Đơn luồng, toàn bộ query:** gọi `faiss.omp_set_num_threads(1)`, xác nhận bằng `faiss.omp_get_max_threads()`. Mỗi lượt đo thực hiện **một lần** `index.search` với toàn bộ 1.020 query; báo thời gian cả lô và thời gian cả lô chia 1.020 theo ms/query. Để thống nhất thực hành trong kế hoạch này, dùng 1 lượt warm-up và 7 lượt đo, lấy median, đồng thời lưu từng lượt và độ phân tán. Đây là thời gian trung bình phân bổ theo lô, không phải phân phối latency của từng query đơn lẻ.
2. **Theo giao thức ICRCV để tính speedup:** dùng batch **256** và toàn bộ luồng khả dụng trên máy hiện tại; xác định và ghi cả số luồng được chọn lẫn giá trị `faiss.omp_get_max_threads()` sau khi đặt. Với 1.020 query, một lượt search lần lượt gọi 4 batch: `256 + 256 + 256 + 252`. Mỗi index/config có 1 lượt warm-up, 7 lượt đo trên cùng tập query và lấy median; báo tổng thời gian, ms/query và từng lượt. Đây là chế độ tính `speedup = latency_FlatIP / latency_HNSW`; FlatIP và HNSW original/centered phải được đo **cùng máy, số luồng, batch, tập query, metric, k và giao thức**. Không thay batch 256 bằng toàn bộ query trong chế độ này vì hiệu năng FlatIP và speedup phụ thuộc batch size.

Trước khi đặt kết quả cạnh ICRCV, ghi rõ sự khác nhau giữa **bản thảo** và code cũ: bản thảo ghi batch 256, 28 luồng và `k`/giao thức tương ứng; code cũ gọi `top_k=50`, HNSW chạy 3 lượt đo cho mỗi lần dựng trong khi nhánh index khác có 7 lượt. R4 làm theo hướng dẫn mới là 7 lượt, nên không mô tả là tái lập nguyên trạng toàn bộ code cũ. Chọn và khóa `k` cho từng bảng: phép chính tại retention@10 cần ghi `k=10` nếu thực sự search top-10; nếu thêm bảng đối chiếu ICRCV với `k=50`, chạy và báo riêng, tính retention@10 từ top-10 của kết quả, không trộn latency của hai `k`.

**Hàng neo ICRCV:** chạy lại FlatIP và HNSW gốc trên SEARLE/CIRCO, `M=32`, `efSearch=128`, theo chế độ batch 256 và toàn bộ luồng máy hiện tại. Đặt latency, retention và speedup mới cạnh số được báo trong bài ICRCV, cùng CPU, số luồng, batch, `k`, tập query và số lượt đo. Bản thảo ICRCV ghi i7-14700 và 28 luồng, nhưng code cũ chưa xác nhận số luồng thực tế bằng metadata; không mặc định đặt 28 luồng trên máy mới hoặc quy toàn bộ chênh lệch cho phần cứng khi còn khác giao thức/dữ liệu. Nếu máy i7-14700 còn sử dụng được, ưu tiên đo bảng cuối trên máy đó và ghi lại môi trường thực tế.

**Đo tại cùng retention:** với mỗi seed và phương án, chọn cấu hình efSearch **thực đo** đạt ít nhất ngưỡng mục tiêu theo quy tắc đã khóa, báo retention thực tế, sai lệch giữa hai nhánh và trạng thái không đạt. Đo latency mới tại chính các cấu hình đó; giá trị `ndis`/retention nội suy chỉ là ước lượng và không tạo ra một cấu hình efSearch thực ở điểm nội suy. Nếu chênh lệch retention thực tế còn đáng kể, báo rõ, không gọi là khớp chính xác. Không nội suy latency một cách thiếu kiểm soát hoặc so tốc độ tại hai mức chất lượng chưa được công bố.

**Bộ nhớ và thời gian dựng:** kiểm tra `len(faiss.serialize_index(index))` cho từng seed/biến thể và tách kích thước vector, cấu trúc chỉ mục nếu có thể; kiểm tra slot `2M` và ô trống `−1`, thay vì giả định thêm cạnh không tốn bộ nhớ. Báo thời gian dựng thực đo kèm môi trường và cùng điều kiện; số khoảng 38,2 → 43,2 giây trong feedback chỉ là mốc R3 cần đối chiếu nguồn, không chuyển thành kết quả R4 khi chưa đo/kiểm tra. Không tuyên bố tiết kiệm bộ nhớ hoặc latency khi chưa có số đo tương ứng.

## 9. Bước 6 — Query ảnh đối chứng và D4–D6

Kiểm kê dữ liệu query ảnh từ R2 và xác minh ID, backbone, preprocessing, split, kích thước và quy tắc chọn mẫu. Xác định trước ảnh query có nằm trong gallery không; nếu có phải loại self theo ID cho cả exact và ANN hoặc chọn query độc lập, giữ cùng quy tắc giữa các nhánh. Tránh so hai tập query khác nhau về kích thước hoặc ngữ nghĩa mà gọi đó là hiệu ứng modality thuần túy.

- **D4:** tính `b_q=u·q` cho CIR và query ảnh, so phân phối theo từng backbone; trong CIR đo quan hệ `b_q`, `s1` và retention gốc, kèm CI/độ nhạy.
- **D3 mở rộng:** so `a_z` của exact neighbor CIR và ảnh so với gallery, dùng bootstrap theo query, báo số ảnh trùng và khả năng phụ thuộc.
- **D5:** chia theo phân vị `a_j` đã khóa riêng từng model, đo miss trước/sau trên cùng neighbor, seed và query; dự đoán mức giảm khác nhau theo độ trung tâm, có thể có nhóm tăng miss. Báo mẫu/CI từng nhóm, tính lại tại cùng `ndis` nếu có thể, điều chỉnh hoặc ghi giới hạn so sánh nhiều nhóm.
- **D6:** đối chiếu bằng chứng D3 giữa hai model và lợi ích C1/`λ`; đây là giả thuyết giải thích cần kiểm tra, không thể kết luận D3 là nguyên nhân duy nhất hay MCS không có vai trò chỉ từ hai model.

So retention/gain của query CIR và query ảnh trên cùng gallery/index/config, có đối chứng chi phí `ndis`; giữ khác biệt giữa tập truy vấn và kiểm tra vùng chồng lấp của `s1`/`b_q`. Kết quả âm tính hoặc không đủ hỗ trợ được báo đầy đủ.

## 10. Bước 7 — C6 và xác định phạm vi đóng góp

Sau khi có kết quả bước 1–6 và kiểm kê tài nguyên, lập preregistration riêng cho stress (`M=16`, `efSearch=32`), CIRR, FashionIQ, CLIP4Cir và gallery 500K theo feedback. Với từng dataset cần xác nhận weights/embedding/ID/split, lọc distractor, `N`, query count và ground truth; không giả định dữ liệu hay compute đã sẵn có. Báo retention–`ndis`, chi phí, bộ nhớ, seed và các cấu hình thất bại; không khái quát từ CIRCO duy nhất.

Đọc và kiểm tra toàn văn các công trình mentor nêu (Liu, Morozov–Babenko, Chen, Suzuki, Herman) và tìm thêm công trình liên quan đến dịch/centering trước HNSW. Ghi bài toán, hình học/normalization, dữ liệu, phạm vi và khác biệt với thiết kế CIR; chỉ tuyên bố tính mới sau kiểm tra nguồn. Hướng chọn vector dịch khác `μ` để sau giai đoạn cơ chế và cần thiết kế riêng, không mở rộng trong R4 mặc định.

## 11. Chuẩn dữ liệu, báo cáo và điều kiện dừng

- Tách thư mục theo bước (`provenance`, `D1_D3`, `C2_pruning`, `lambda`, `C5_relative`, `image_control`, `C6`); mỗi bước có kế hoạch/preregistration, script, manifest, output, báo cáo và hình với liên kết tương đối.
- Metadata gồm timestamp, commit, trạng thái tree/submodule, hash mã/config/data/weights, phiên bản FAISS/Python, CPU, threads, model, dataset, query count, gallery size, seed, index config và bootstrap. Lưu checkpoint có chữ ký; không ghi đè dữ liệu R3.
- Kết quả báo cáo/bảng/hình phải sinh hoặc kiểm tra từ JSON/CSV tương ứng, lưu theo từng seed; giữ kết quả âm tính và các trường hợp không đạt. Ghi rõ khi so sánh là thăm dò, kiểm định sau khi xem R3, hay xác nhận trên snapshot mới.
- Dừng và điều tra khi thiếu ID/đầu vào, sai hash hoặc exact rank ngoài tolerance/tie, đồ thị cắt không hợp lệ, số nút không khớp cao, CI/tỷ số không xác định, hoặc không có miền chi phí chung. Nếu ID hoặc commit sạch chưa giải quyết, chỉ tiếp tục phần độc lập hoặc thăm dò có gắn hạn chế; không dùng kết quả đó như confirmatory.
- Thời lượng trong feedback là ước lượng, không phải cam kết; đo thử batch/khả năng dựng, ghi runtime và bộ nhớ trước khi dự báo thời gian hoàn tất.
