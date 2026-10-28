# Kế hoạch C4 — Hình học gallery và cơ chế centering

**Trạng thái: kế hoạch, chờ duyệt; chưa chạy C4.** Nguồn: [feedback R3](../mentor_feedback_R3.md), [kế hoạch R3](../R3_execution_plan.md), [đăng ký trước](../stage0_preregistration.md), [C1](../C1/bao_cao_C1.md), [C2](../C2/bao_cao_C2.md) và [C3](../C3/revision_v2/bao_cao_C3.md).

## 1. Câu hỏi nghiên cứu

Với SEARLE và Pic2Word trên CIRCO, centering gallery không chuẩn hóa lại làm thay đổi hình học gallery, `N10_gallery` và bậc vào của HNSW như thế nào? Các exact neighbor được phân bố lại giữa các nhóm bậc vào, hay miss rate thay đổi ngay trong cùng nhóm? Kết quả dùng để mô tả các cơ chế khả dĩ, không xác lập quan hệ nhân quả.

## 2. Dự đoán và quy tắc trước khi chạy

- Theo đăng ký trước: dự đoán MCS gallery gốc của Pic2Word cao hơn SEARLE; centering có thể thay đổi `N10_gallery` và in-degree, chưa khóa hướng hay độ lớn. Không suy ra MCS gây ra lợi ích từ so sánh hai backbone.
- Phân biệt hai quan sát: thay đổi phân bố in-degree của exact neighbor và thay đổi miss rate trong từng nhóm in-degree. Báo cả hai, kể cả khi kết quả không ủng hộ giả thuyết.
- C1 cho thấy hiệu ứng Pic2Word tại cùng `ndis`, còn C2 không đạt tiêu chí khớp số cạnh 2%; không tuyên bố C2 đã loại trừ giải thích do mật độ. C4 chủ yếu mô tả tại cấu hình reference `M=32, efSearch=128`, không coi kiểm soát in-degree là kiểm soát chi phí tìm kiếm.

## 3. Dữ liệu, cấu hình và kiểm tra provenance

- CIRCO: gallery 123.403 ảnh, 1.020 query/model; SEARLE 512 chiều, Pic2Word 768 chiều. Dùng gallery và query cache đã khóa trong [manifest C1](../C1/run_manifest.json), đối chiếu hash và kiểm tra thứ tự input trước khi tính. Chấp nhận khác biệt LF/CRLF của config chỉ khi hash sau chuẩn hóa khớp chính xác C1; ghi cả hash gốc.
- Gốc: L2-normalize gallery/query rồi dùng inner product. Centered: chỉ trừ mean gallery `μ` khỏi gallery, **không** chuẩn hóa lại; query CIR giữ nguyên. Kiểm tra exact top-10 CIR theo ID trước/sau.
- HNSW reference: `M=32`, `efConstruction=200`, `efSearch=128`, năm seed 42–46. Lưu cấu hình, mã, thư viện, CPU, số luồng, seed và trạng thái workspace. ID nguồn của 800 test feature rows chưa xác minh độc lập: phân tích ghép theo hàng ổn định, không khẳng định ánh xạ ID.
- Các checkpoint R2 chứa `indegree`, `outdegree`, `found`; chỉ tái sử dụng khi xác minh đầy đủ hash đầu vào, cấu hình, mã và định nghĩa với manifest. Nếu không chứng minh được cùng provenance, dựng lại đồ thị; lưu in-degree, neighbor IDs và trạng thái miss cùng một lượt dựng, không ghép bậc từ đồ thị khác với kết quả tìm kiếm. Checkpoint C1/C2 không lưu đầy đủ in-degree và không đủ để tự động tái tạo cơ chế.

## 4. Tính hình học và `N10_gallery`

1. Tính `||μ||` của gallery gốc và norm mean sau centering. Với gallery gốc đã chuẩn hóa, tính MCS toàn bộ cặp khác self theo `(N ||μ||² − 1)/(N−1)`; kiểm tra norm vector và độ ổn định số học.
2. Sau centering vector không còn unit norm: tính **cosine** trung bình giữa hai ảnh khác nhau bằng cách chuẩn hóa bản sao vector đã centered để đo cosine, không dùng bản sao này cho tìm kiếm IP. Tính chính xác bằng tổng các vector đơn vị: `(||Σu_i||² − Σ||u_i||²)/(N(N−1))`, tích lũy float64; kiểm tra/ghi số vector có norm bằng 0 và dừng hoặc báo phương án xử lý trước khi diễn giải. Nêu rõ đây là cosine sau centering, không phải mean IP hay phép chuẩn hóa lại index.
3. Thực hiện exact gallery-to-gallery top-10 bằng `IndexFlatIP` theo từng batch, cho gốc và centered IP không chuẩn hóa lại. Loại self bằng **ID**, không giả định self đứng đầu; lấy đủ 10 neighbor hợp lệ mỗi hàng. Nếu self không có trong top-11, vẫn lấy 10 ID đầu khác self. Kiểm tra tổng `N10_gallery = 10N`, ID hợp lệ và không có self. Lưu vector đếm theo ảnh, skewness, phần vị, max, số và tỷ lệ `N10_gallery=0`; dùng cùng định nghĩa trên hai nhánh.
4. Phân biệt `N10_gallery` với số lần ảnh xuất hiện trong top-10 của các CIR query (`N10_query`); với từng cặp query–neighbor, `N10_loo=N10_query−1`. Ghi rõ k, đơn vị và tập nguồn; không gọi tỷ lệ `N10_query=0` là tỷ lệ anti-hub của gallery.

## 5. Bậc vào, miss rate và phân rã mô tả

- Đo in-degree có hướng ở tầng 0 từ cạnh hợp lệ, kiểm tra tổng bậc vào bằng bậc ra; báo phân phối trên toàn gallery và trên các exact neighbor theo model, seed và biến thể. Dựng bảng có query row, neighbor ID, exact rank, `N10_gallery`, `N10_loo`, bậc vào trước/sau, miss trước/sau, `s1` và `s100`.
- **Chọn bin trước khi xem kết quả C4:** dùng quintile bậc vào từ phân bố gộp hai biến thể trong từng model, dựa trên các exact-neighbor occurrences qua seed; cùng ranh giới cho trước/sau. Nếu các ngưỡng trùng do giá trị rời rạc, gộp các bin trùng theo quy tắc `unique edges`, ghi bin thực tế và số query, số ảnh khác nhau, số dòng trong mỗi nhóm; không điều chỉnh bin để đạt kết quả mong muốn.
- Báo bảng chuyển nhóm in-degree trước→sau và tỷ lệ miss theo nhóm trước/sau; thêm so sánh các neighbor giữ cùng nhóm để mô tả thay đổi miss trong nhóm. Vì nhóm giữ nguyên là tập chọn lọc và phân bố đặc trưng có thể đổi, không diễn giải so sánh này như tác động nhân quả.
- Bootstrap ghép cặp seed và query 2.000 lần, giữ cả 10 neighbor của query và hai biến thể cùng nhau; báo CI 95% cho chênh lệch miss/retention theo nhóm và chuyển nhóm khi đủ dữ liệu. Đồng thời báo số ảnh riêng biệt và độ nhạy gom theo ảnh nếu khả thi; bootstrap theo query không loại bỏ phụ thuộc do ảnh xuất hiện ở nhiều query. Với nhóm quá nhỏ hoặc không ổn định, báo CI/giới hạn, không khẳng định hiệu ứng.
- Theo kế hoạch R3 và phụ lục C, phân rã mô tả chênh lệch miss **giữa hai model** bằng mô hình logistic riêng, trên thang xác suất: `rank`, `log1p(indeg)`, `log1p(N10_gallery)`, `s1`, `s100`. Báo hai chiều tham chiếu (hệ số SEARLE trên đặc trưng Pic2Word và ngược lại), phân rã theo nhóm biến bằng hai thứ tự (bậc vào trước/query features trước), bootstrap theo query 2.000 lần. Ghi rõ cách xử lý dữ liệu, seed, CI và các lần fit lỗi; kiểm tra hội tụ, overlap và độ ổn định. Nếu tách biệt dữ liệu hoặc thiếu overlap làm mô hình không đáng tin, báo không kết luận thay vì ép ước lượng. Phân rã phụ thuộc mô hình/thứ tự và **không phải mediation nhân quả**; không đồng nhất phân rã giữa model với phân rã hiệu ứng centering.

## 6. Đầu ra và kiểm thử

- Manifest và checkpoint có hash; bảng `||μ||`, MCS, `N10_gallery` gốc/sau, skewness và tỷ lệ bằng 0; lưu vector đếm và định nghĩa để kiểm tra lại.
- Bảng/hình phân phối in-degree, bảng chuyển nhóm, miss rate theo nhóm và CI; số query, số ảnh và số dòng. Bảng phân rã giữa model theo hai chiều và hai thứ tự, cùng chẩn đoán hội tụ.
- Báo cáo theo 7 phần: câu hỏi, dự đoán, thiết kế, kết quả, đánh giá, hạn chế, bước tiếp theo; số liệu sinh từ JSON/bảng, liên kết hình tương đối. Kiểm tra exact invariance, loại self, tổng `10N`, tổng bậc, tính ghép cặp và tính nhất quán số báo cáo với đầu ra.
- Gallery-to-gallery exact là phép tính lớn `N×N`; đo thử một batch để ước lượng thời gian/bộ nhớ rồi chạy có checkpoint và ghi thời gian. Không ước lượng thời gian hoàn tất khi chưa đo.

## 7. Điều kiện dừng và phạm vi

Dừng diễn giải nếu hash input không khớp, exact rank CIR thay đổi ngoài sai số/tie đã kiểm tra, dữ liệu miss và in-degree không cùng đồ thị, self-removal hoặc tổng cạnh không đạt, hoặc provenance không đủ. Trình bày các khác biệt số học và mọi thay đổi thiết kế sau khi xem dữ liệu như phân tích bổ sung. C5 theo quintile `s1` là bước riêng; kế hoạch này không tự chạy C5 hay gửi kết quả cho mentor.
