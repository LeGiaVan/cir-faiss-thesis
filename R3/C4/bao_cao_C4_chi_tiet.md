# C4 — Giải thích chi tiết kết quả centering

Tài liệu này giải thích [báo cáo C4 gốc](./bao_cao_C4.md) bằng lời và ví dụ. Số liệu được lấy từ [results.json](./results.json), [degree_groups.csv](./degree_groups.csv), [degree_transitions.csv](./degree_transitions.csv) và [decomposition.json](./decomposition.json). Đơn vị chênh lệch giữa hai tỷ lệ là **điểm phần trăm**.

## 1. C4 đang tìm câu trả lời gì?

C1 đặt câu hỏi centering có cải thiện tìm kiếm ở cùng chi phí hay không. C4 đi tiếp: **sau centering, không gian ảnh và đồ thị HNSW thay đổi thế nào, và thay đổi nào đi cùng việc HNSW bỏ sót ít hơn?** C4 đưa ra mô tả và bằng chứng phù hợp với một số cách giải thích; nó không tự chứng minh nguyên nhân.

Trong cấu hình C4, Pic2Word có miss rate gốc **9.13%**, sau centering **5.04%**, tức giảm **4.09 điểm phần trăm**. SEARLE giảm từ **3.26%** xuống **3.02%**. Đây là so sánh tại cùng `efSearch=128`; chi phí `ndis` có thể khác nhau.

C1 có phép so sánh riêng tại cùng chi phí: ở khoảng **1927 ndis/query**, Pic2Word tăng retention từ **91.19%** lên **93.45%**. Hai con số này trả lời câu hỏi khác với mức giảm miss tại cùng `efSearch` ở trên. C2 chưa khớp mật độ trong ngưỡng 2%; với Pic2Word, mức original gần nhất vẫn lệch **-24.40%** số cạnh median so với centered. Vì vậy chưa thể loại trừ lời giải thích liên quan đến mật độ đồ thị. [Xem C1](../C1/bao_cao_C1.md), [C2](../C2/bao_cao_C2.md).

## 2. Trước hết: C4 đo những gì?

Mỗi model dùng **123,403 ảnh gallery**, **1,020 query** và **5 seed** dựng HNSW. Với mỗi query, exact search tìm 10 ảnh có điểm inner product cao nhất; đó là **exact top-10**. HNSW tìm xấp xỉ và có thể bỏ sót một số ảnh trong danh sách này.

- **Retention@10**: số ảnh trong exact top-10 mà HNSW tìm lại được, chia 10. Nếu tìm lại 9 ảnh thì retention là 90%.
- **Miss rate**: phần còn thiếu so với exact top-10; trong ví dụ trên là 10%. Với cùng tập query và cách lấy trung bình ở đây, miss rate = 1 − retention. Đây không phải tỷ lệ bỏ sót nhãn đúng do con người gán, cũng không phải mAP.
- **Centering gallery**: tính vector trung bình `μ` của gallery đã chuẩn hóa, rồi trừ `μ` khỏi từng vector gallery. Khi tìm bằng inner product, query CIR được giữ nguyên; không chuẩn hóa lại gallery đã trừ mean. Điều này trừ cùng một hằng số điểm cho tất cả ảnh với cùng query, nên thứ hạng exact CIR được giữ.

Mỗi dòng “neighbor occurrence” là một cặp query–ảnh trong exact top-10 ở một seed. Một ảnh có thể xuất hiện với nhiều query và lặp lại qua seed: số dòng trong bảng **không phải số ảnh độc lập**.

## 3. MCS và vector trung bình: không gian ảnh trông thế nào?

**Vector trung bình `μ`** là trung bình các vector ảnh trong gallery. **MCS** ở đây là cosine trung bình giữa hai ảnh gallery khác nhau: giá trị dương lớn hơn cho thấy các hướng vector nhìn chung giống nhau hơn. Nó là thống kê của toàn gallery, không đo trực tiếp lỗi HNSW của một query.

| Model | ‖μ‖ gốc | MCS gốc | ‖μ‖ sau centering | MCS sau centering |
|---|---:|---:|---:|---:|
| searle | 0.68407 | 0.46795 | 5e-06 | 0.00011 |
| pic2word | 0.70335 | 0.49470 | 4.7e-06 | 0.00014 |

MCS gốc của Pic2Word cao hơn SEARLE, phù hợp với dự đoán đã đăng ký. Sau khi trừ mean, mean vector gần 0 là kết quả được mong đợi từ chính phép biến đổi; MCS cũng gần 0. Để tính **cosine** sau centering, phép đo chuẩn hóa một bản sao các vector đã centered. Bản sao này chỉ dùng đo MCS; chỉ mục HNSW/IP vẫn dùng vector centered không chuẩn hóa lại. Vì vậy không thể lấy MCS gần 0 làm bằng chứng độc lập rằng centering gây giảm miss.

**Phản biện giả thuyết nón:** hai MCS gốc đều gần 0,5 và lệch nhau **0.02675**. Cả hai backbone có độ tập trung hướng đáng kể theo thống kê này, trong khi lợi ích centering quan sát được khác nhau. Dự đoán thứ tự MCS được hỗ trợ, nhưng **một mình MCS chưa giải thích được sự khác biệt hiệu ứng centering**. Chỉ có hai backbone và chưa có kiểm định tách riêng ảnh hưởng MCS, nên không thể khẳng định chênh lệch 0.02675 chắc chắn không có ý nghĩa hình học, cũng không thể bác bỏ mọi vai trò của MCS. Không dùng 'bung nón' làm lời giải thích đã được xác nhận.

## 4. N10 phía gallery: ảnh nào thường được các ảnh khác chọn?

**`N10_gallery(x)`** là số ảnh gallery khác có ảnh `x` trong 10 láng giềng exact gần nhất của chúng. Ví dụ, `N10_gallery(x)=25` nghĩa là `x` được 25 ảnh khác chọn vào top-10; bằng 0 nghĩa là không ảnh gallery nào chọn `x`. Khi đếm, ảnh đang làm query được loại theo ID để không tính chính nó. Tổng số lần chọn luôn bằng số ảnh nhân 10.

Đại lượng này khác **`N10_query`**, là số query CIR có ảnh `x` trong exact top-10. Một bên dùng ảnh gallery làm truy vấn, bên kia dùng query CIR; không thể đọc hai giá trị như cùng một số đo. Nó cũng khác **in-degree HNSW**, là số cạnh đồ thị đi vào một nút, giải thích ở phần sau.

| Model | Skewness N10 gốc | Skewness N10 centered | Tỷ lệ N10=0 gốc | Tỷ lệ N10=0 centered |
|---|---:|---:|---:|---:|
| searle | 2.659 | 4.624 | 8.48% | 9.91% |
| pic2word | 2.659 | 3.402 | 10.72% | 5.61% |

Với Pic2Word, số ảnh có `N10_gallery=0` giảm từ **13,230** xuống **6,919**; tỷ lệ giảm từ **10.72%** xuống **5.61%**. Trong khi đó skewness tăng từ **2.659** lên **3.402**. Hai quan sát không mâu thuẫn: tỷ lệ bằng 0 mô tả một điểm của phân phối; skewness phụ thuộc toàn bộ hình dạng và đuôi phân phối. Không thể chỉ dựa vào một trong hai để kết luận hubness nói chung tốt hơn hay xấu hơn.

Khi tính N10 centered, **cả ảnh dùng làm query gallery và ảnh trong chỉ mục đều là vector đã centered**, không chuẩn hóa lại. Vì vậy đây là phép đo quan hệ giữa ảnh–ảnh sau biến đổi; nó có thể thay đổi dù exact ranking của query CIR giữ nguyên.

**Vì sao hai backbone có thể đổi N10 theo hai hướng?** Với hai ảnh gallery `x, y`, sau centering điểm IP là `(x−μ)·(y−μ) = x·y − x·μ − y·μ + ‖μ‖²`. Khi cố định ảnh query `y`, các hạng `−y·μ + ‖μ‖²` là hằng số, còn `−x·μ` thay đổi theo ảnh ứng viên `x`; vì thế thứ hạng ảnh–ảnh và N10 có thể đổi. MCS chỉ tóm tắt một trung bình toàn cục, không mô tả phân bố các hình chiếu `x·μ`, norm, khoảng cách giữa các điểm gần nhau hay topology. Những khác biệt đó là các ứng viên cần đo để giải thích vì sao SEARLE và Pic2Word có chiều thay đổi tỷ lệ N10=0 trái nhau; C4 chưa xác định được cơ chế quyết định.

Tăng skewness và N10=0 của SEARLE là thay đổi phân phối quan sát được, chưa đủ để gọi không gian bị “méo” theo nghĩa chất lượng ngữ nghĩa suy giảm. Với Pic2Word, giảm N10=0 phía gallery không đồng nghĩa các nút cô lập trong HNSW được “cứu”, vì hai đại lượng đo hai cấu trúc khác nhau.

## 5. Bậc vào HNSW và sự chuyển nhóm

**In-degree** của một ảnh là số cạnh có hướng ở tầng 0 của đồ thị HNSW trỏ vào nút ảnh đó. Nó mô tả cấu trúc chỉ mục, không phải số lần ảnh được chọn bởi exact search. Bậc vào thấp có thể đi cùng miss rate cao hơn, nhưng một quan sát liên hệ không tự chứng minh rằng thêm cạnh sẽ cứu được ảnh.

Với Pic2Word, bậc vào trung bình của các exact-neighbor occurrence tăng từ **18.98** lên **26.92**. Các ranh giới nhóm dùng chung trước/sau là **[0.0, 11.0, 17.0, 23.0, 33.0, 131.0]**; nhóm 0 có bậc vào từ 0 đến dưới 11, nhóm 4 từ 33 đến 131.

Trong toàn bộ occurrence Pic2Word ghép cặp trước/sau, **57.47%** chuyển lên nhóm bậc vào cao hơn, **28.15%** giữ nhóm và **14.39%** chuyển xuống. Với SEARLE, các tỷ lệ tương ứng là **39.36%**, **32.86%**, **27.78%**. Đây là tỷ lệ theo occurrence gộp 5 seed, không phải tỷ lệ ảnh duy nhất; [bảng chuyển nhóm](./degree_transitions.csv) có từng ô và CI.

**Mật độ đồ thị là yếu tố cần kiểm soát.** Trong các đồ thị R2 được dùng cho C4, median số cạnh có hướng tầng 0 của Pic2Word tăng từ **2,259,515** lên **3,119,347**, tức thêm **859,832 cạnh** (38.1%). Ở nhóm 0, số occurrence giảm từ **14,145** xuống **3,464** (75.5%); đây là thay đổi thành phần nhóm, không phải các nút bị xóa. Ở nhóm 4, số occurrence tăng từ **6,747** lên **14,246**.

Các đồ thị C1 được dựng riêng cho thấy tại `efSearch=128`, Pic2Word dùng trung bình **1860.9 ndis/query** ở original và **2300.0** ở centered (+23.6%). Đây là phép đo từ C1, không phải số đo ndis trực tiếp trên checkpoint đồ thị R2 của C4. C4 không khớp mật độ hoặc ndis, nên mức giảm miss cùng efSearch không thể tách riêng lợi ích hình học khỏi thay đổi tài nguyên tìm kiếm.

Một giả thuyết cần kiểm tra là centering làm thay đổi quyết định giữ láng giềng khi HNSW xây đồ thị IP, dẫn tới nhiều cạnh hơn và phân bố bậc vào khác. Hiện chưa đo trực tiếp các quyết định của bộ lọc xây dựng; vì vậy chưa thể gọi đó là “lỗi”, khẳng định thuật toán chủ động thiên vị, hoặc gán toàn bộ mức giảm miss cho số cạnh tăng.

### Cách đọc bảng miss theo nhóm

Ví dụ Pic2Word nhóm 0: trước centering có **14,145** occurrence trong nhóm, miss **18.80%**; sau centering có **3,464** occurrence, miss **11.69%**. Hai tập này khác nhau vì một số occurrence chuyển nhóm. Mức giảm giữa hai tỷ lệ là mô tả nhóm trước/sau, không phải mức cải thiện của cùng các ảnh.

Để nhìn cùng tập hơn, xét riêng **1,980** occurrence giữ nhóm 0 ở cả hai nhánh, thuộc **971** ảnh khác nhau và **584** query. Với tập chọn lọc này, miss centered − original là **-3.13 điểm phần trăm**, CI 95% **[-6.18; -0.05]**. Điều này cho thấy một mức giảm được quan sát trong tập giữ nhóm, nhưng không chứng minh bậc vào gây ra mức giảm: chính việc chọn tập giữ nhóm có thể tạo khác biệt.

Các CI ở các nhóm khác nhau có thể chứa 0; cần đọc từng nhóm trong [bảng chi tiết](./degree_groups.csv), không khái quát kết luận nhóm 0 cho mọi nhóm. Các hình [Pic2Word](./c4_pic2word_miss.png) và [SEARLE](./c4_searle_miss.png) biểu diễn miss theo nhóm trước/sau; chúng không tự thể hiện thay đổi trên cùng tập occurrence.

**Đọc đúng CI nhóm 0:** khoảng tin cậy của tập giữ nhóm vừa chạm phía âm; đây là bằng chứng tại một nhóm được xét, với giới hạn do chọn nhóm và nhiều phép so sánh. Chưa thể xem kết quả này là bằng chứng xác định về một cơ chế dẫn đường độc lập với thay đổi chi phí.

## 6. Có thể và chưa thể kết luận gì?

**Có thể nói:** trên CIRCO và cấu hình này, Pic2Word có MCS gốc cao hơn; centering làm thay đổi phân phối N10 gallery và bậc vào, đồng thời nhiều exact-neighbor occurrence chuyển lên nhóm bậc vào cao hơn. Miss tại cùng `efSearch` giảm; C1 cung cấp thêm bằng chứng tăng retention tại các mức `ndis` chung đã khảo sát.

**Chưa thể nói:** MCS cao hoặc bậc vào thay đổi là nguyên nhân đã được chứng minh của lợi ích; centering tốt hơn mọi cách tăng mật độ; hoặc kết quả chắc chắn đúng trên backbone/dataset/cấu hình khác. C2 chưa khớp mật độ theo ngưỡng định trước.

Bootstrap giữ ghép cặp query và seed, nhưng một ảnh xuất hiện ở nhiều query nên các quan sát không hoàn toàn độc lập; chưa có kiểm tra độ nhạy gom cụm theo ảnh trong kết quả này. Có 5 seed; các CI là theo từng nhóm, không điều chỉnh đồng thời cho nhiều so sánh. ID nguồn của 800 test feature rows chưa được xác minh độc lập từng hàng. Những giới hạn này cần được giữ khi dùng kết quả trong báo cáo luận văn.

## 7. Hướng xử lý tiếp theo

C1 trả lời câu hỏi cùng chi phí tìm kiếm và vẫn cho thấy lợi thế Pic2Word trong các ngân sách đã khảo sát; C4 không xóa bỏ kết quả đó. Nhưng cùng ndis chưa tự kiểm soát số cạnh. C2 hiện chỉ tìm được mức M gần nhất, chưa đạt ngưỡng lệch median số cạnh 2% cho cả hai model, nên **chưa có kết luận tại cùng mật độ**. Cần thiết kế bổ sung để khớp số cạnh, đồng thời so retention ở miền ndis chung; ghi trước cách chọn cấu hình, chi phí dựng/bộ nhớ và sai lệch còn lại. Chỉ sau đối chứng đó mới đánh giá được mức lợi thế còn lại khi mật độ được kiểm soát gần hơn.

Phép phân rã giữa hai model của seed 42 được giữ tại [decomposition.json](./decomposition.json) để truy vết và tham khảo mô tả. Do phụ thuộc mô hình, thứ tự thay biến, ghép hàng và một seed, nó không phải bằng chứng chính cho cơ chế HNSW hoặc tác động centering.

## 8. Đọc tiếp từ đâu?

- [Báo cáo C4 gốc](./bao_cao_C4.md): bảng đầy đủ theo nhóm và phương pháp.
- [Bảng chuyển nhóm](./degree_transitions.csv) và [bảng nhóm](./degree_groups.csv): số dòng, số query, số ảnh và CI.
- [Kết quả tổng hợp](./results.json) và [manifest](./run_manifest.json): số liệu gốc và provenance.
- Bước C5 sẽ kiểm tra query nào được lợi theo nhóm `s1`; đó là câu hỏi tiếp theo, chưa được trả lời bởi C4.
