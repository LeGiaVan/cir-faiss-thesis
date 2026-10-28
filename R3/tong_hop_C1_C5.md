# Tổng hợp kết quả R3: C1–C5

## Kết luận chính

Trên CIRCO và cấu hình đã khảo sát, centering cho Pic2Word tăng retention tại **cùng số phép tính khoảng cách** trong C1. Ví dụ, ở khoảng **1927 ndis/query**, retention tăng từ **91.19%** lên **93.45%**, chênh lệch **+2.26 điểm phần trăm** (CI 95% [+1.74; +2.81]). Tuy nhiên, C2 **chưa khớp được số cạnh** theo tiêu chí định trước, nên chưa xác định được lợi thế khi đồng thời kiểm soát mật độ đồ thị.

C4 cho thấy centering thay đổi cấu trúc đồ thị và các thống kê gallery; những thay đổi này là cơ chế cần kiểm tra, chưa phải bằng chứng nhân quả. C5 cho thấy query Pic2Word có `s1` thấp nhất nhận gain lớn hơn nhóm cao nhất tại cùng `efSearch`, nhưng chưa đạt xu hướng đơn điệu trên cả năm nhóm.

## Phạm vi và cách đọc

Các thí nghiệm dùng CIRCO, 123.403 ảnh gallery và 1.020 query mỗi backbone; HNSW reference `M=32`, `efConstruction=200`, năm seed. Retention@10 là tỷ lệ ảnh trong top-10 exact được HNSW tìm lại, không phải mAP hay recall theo nhãn. Chênh lệch retention/miss được báo bằng **điểm phần trăm**. Centering IP trừ mean khỏi gallery đã chuẩn hóa, không chuẩn hóa lại và giữ query CIR; exact ranking IP được kiểm tra trực tiếp.

## C1 — Cùng chi phí tìm kiếm

- **Pic2Word:** centered cao hơn original tại cả 5/5 ngân sách `ndis` chung; CI ghép cặp tại từng điểm đều dương. Khoảng khảo sát và kết quả từng điểm có trong [báo cáo C1](./C1/bao_cao_C1.md).
- **SEARLE:** 5/5 CI chênh lệch chứa 0. Chưa có bằng chứng lợi thế tại cùng `ndis`; không phải chứng minh hai phương án tương đương.

So sánh tại cùng `ndis` đã kiểm soát số phép tính tìm kiếm trung bình; nó chưa tự kiểm soát số cạnh, bộ nhớ hoặc chi phí dựng. CI theo từng điểm không phải CI đồng thời; nội suy và năm seed giới hạn kết luận.

## C2 — Cùng mật độ đồ thị

Ngưỡng khớp đã đăng ký là sai lệch median số cạnh tầng 0 không quá 2%. Trong các `M` original đã quét, mức gần nhất đều là `M=64`, nhưng Pic2Word vẫn lệch **-24.40%** so với centered `M=32`; SEARLE lệch **-3.06%**. **Không model nào đạt tiêu chí khớp.**

Các đường retention–ndis ở mức M gần nhất là so sánh xấp xỉ. Chưa thể dùng C2 để kết luận centering hơn hay tương đương original tại cùng mật độ. [Báo cáo C2](./C2/bao_cao_C2.md).

## C3 — Đối chứng tịnh tiến L2

Trừ cùng mean khỏi query và gallery giữ nguyên khoảng cách L2 về mặt toán học. Trong phép kiểm tra FAISS float32, tập exact top-10 giống nhau trên toàn bộ query ở cả hai model. SEARLE có một query đảo thứ tự hai ảnh gần hòa; Pic2Word không có query đổi thứ tự. Tiêu chí chấp nhận đảo thứ tự gần hòa được bổ sung **sau khi quan sát**, nên cần báo cùng kết quả ban đầu.

Trên năm seed ở `efSearch=128`, chênh lệch retention centered − original trung bình là **+0.000 điểm %** với SEARLE và **+0.000 điểm %** với Pic2Word; số cạnh hoặc `ndis` có sai khác nhỏ ở một số seed. Kết quả phù hợp với đối chứng L2, không tự chứng minh cơ chế của IP. [Báo cáo C3](./C3/revision_v2/bao_cao_C3.md).

## C4 — Hình học gallery và cấu trúc đồ thị

- MCS gốc: SEARLE **0.46795**, Pic2Word **0.49470**. Pic2Word cao hơn như dự đoán, nhưng chỉ riêng MCS chưa giải thích được khác biệt hiệu ứng centering giữa hai backbone.
- Với Pic2Word, tỷ lệ `N10_gallery=0` giảm từ **10.72%** xuống **5.61%**, trong khi skewness tăng từ **2.659** lên **3.402**. N10 gallery và bậc vào HNSW đo những cấu trúc khác nhau.
- Bậc vào trung bình của các exact-neighbor occurrence Pic2Word tăng từ **18.98** lên **26.92**. Miss tại cùng efSearch giảm từ **9.13%** xuống **5.04%**, nhưng so sánh này chưa khớp `ndis` hoặc mật độ.

C4 mô tả thay đổi phân phối và đồ thị, không chứng minh MCS hay bậc vào gây ra thay đổi retention. Phân rã giữa model dùng seed 42 là phân tích mô tả bổ sung, không phải phân rã nhân quả hiệu ứng centering. [Báo cáo C4 chi tiết](./C4/bao_cao_C4_chi_tiet.md).

## C5 — Query nào có gain lớn hơn?

Chia query thành năm nhóm `s1` riêng trong mỗi backbone, tại cùng `efSearch=128`. Với Pic2Word, gain trung bình nhóm `s1` thấp nhất là **+6.17 điểm %**, nhóm cao nhất là **+2.66 điểm %**; chênh lệch thấp nhất − cao nhất **+3.51 điểm %**, CI query 95% [+2.10; +4.89]. Dự đoán được **ủng hộ một phần**: hai đầu khác nhau theo hướng dự đoán nhưng năm giá trị trung bình không giảm đơn điệu hoàn toàn.

Với SEARLE, chênh lệch hai nhóm đầu cuối là **+0.72 điểm %**, CI 95% [-0.46; +1.83]; chưa đủ bằng chứng theo quy tắc đã đăng ký. C5 không khớp `ndis` theo từng nhóm. [Báo cáo C5](./C5/bao_cao_C5.md).

## Giới hạn chung và việc tiếp theo

- ID nguồn của 800 test feature rows chưa được xác minh độc lập từng hàng; việc ghép query dùng thứ tự extraction/annotation và được kiểm tra nhất quán nội bộ.
- Chỉ có năm seed; bootstrap theo query chưa giải quyết đầy đủ phụ thuộc do nhiều query cùng gặp một ảnh. Các CI theo từng điểm/nhóm không điều chỉnh đồng thời cho nhiều so sánh.
- Các kết quả chỉ áp dụng trực tiếp cho CIRCO, các backbone và cấu hình đã đo; workspace dirty nên provenance dựa vào hash tệp và manifest.
- Ưu tiên thiết kế đối chứng C2 bổ sung có số cạnh khớp theo ngưỡng đăng ký và miền `ndis` chung. Sau đó có thể đánh giá H-MG và tiếp tục theo kế hoạch R3; không xem C4/C5 là bằng chứng nhân quả.

Nguồn dữ liệu số: [C1](./C1/results.json), [C2](./C2/results.json), [C3](./C3/revision_v2/results.json), [C4](./C4/results.json), [C5](./C5/results.json).
