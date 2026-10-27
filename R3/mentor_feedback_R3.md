Tệp hướng dẫn này tập trung vào ba việc: (1) kiểm tra công bằng kết quả centering, vì đây có thể là kết quả thực tiễn tốt nhất của đề tài từ đầu tới giờ; (2) sửa cách đo N10 và cách đọc hồi quy; (3) hai bài báo mới em cần đọc ngay vì liên quan trực tiếp tới tính mới của đề tài. Thầy cũng rút bớt khối lượng công việc ở Mục 6.
1. Tóm tắt
Kết quả
Số liệu
Đánh giá
Việc tiếp theo
Bậc vào HNSW và tỉ lệ bỏ sót
Khi bậc vào tăng từ nhóm 1–4 lên nhóm ≥ 30: SEARLE 33,7% → 0,9%; Pic2Word 28,7% → 2,4%. Chỉ 6 nút (SEARLE) và 14 nút (Pic2Word) có bậc vào bằng 0
Quan hệ liều–đáp ứng rõ và đơn điệu ở cả hai model. Bác bỏ bằng đo trực tiếp giả thuyết "anti-hub bị cô lập" ở Report_3
Cụm theo ảnh; vẽ hình; phân rã (3.2)
N10 phía truy vấn
Tỉ lệ "anti-hub" 93,3% và 93,5%; nhóm N10 = 10–29 chỉ có 2 và 5 ảnh
Đại lượng không đo được hubness với 1.020 truy vấn (3.1)
Thay bằng N10 phía gallery và N10 loại trừ chính truy vấn
GEE lồng nhau
β của Pic2Word: 1,08 → 0,78 → −0,04
Tín hiệu đáng chú ý nhất: mức tương đồng của truy vấn hấp thụ gần hết chênh lệch giữa hai model
Phân rã trên thang xác suất; xử lý khác biệt thang đo giữa hai backbone; làm H-MG (Mục 4)
Centering
Pic2Word +4,09 điểm [3,56; 4,64], thu hẹp 66% khoảng cách với SEARLE. SEARLE +0,25 [−0,11; 0,58]
Hiệu ứng thật ở cùng efSearch, nhưng đồ thị dày hơn 38% và chậm hơn 19%
So sánh ở cùng chi phí (Mục 2)
Tài liệu mới
Herman (arXiv 2609.00364, 31/08/2026); Bao et al. (EMNLP 2025 Findings)
Chồng lấn trực tiếp với một phần đóng góp dự kiến
Đọc ngay, định vị lại (Mục 5)

 
Thứ tự ưu tiên (chi tiết ở Mục 6):
1. Kiểm tra centering ở cùng chi phí và đối chứng âm với metric L2 (Mục 2). Kết quả này quyết định có đóng góp cho họ chỉ mục đồ thị hay không.
2. Sửa cách đo N10 và bổ sung phân tích hồi quy (Mục 3).
3. Thí nghiệm H-MG (Mục 4): M2 cho thấy đây là hướng có khả năng giải thích nhiều nhất.
4. Đọc hai bài mới (Mục 5), làm xen kẽ với các bước trên.
5. P2a (nhiễu PQ có dấu) làm sau. P2c tạm hoãn.
2. Centering: kết quả quan trọng nhất, nhưng chưa so sánh công bằng
2.1. Số liệu
Trung bình 5 lần dựng, thầy tính từ step4_centering.json:
Model
Retention@10
Độ trễ (ms/truy vấn)
Số cạnh tầng 0
Thời gian dựng
SEARLE
96,74% → 96,98%
0,581 → 0,624 (+7%)
2,66 → 2,88 triệu (+9%)
28,8 → 30,0 s
Pic2Word
90,87% → 94,96%
0,633 → 0,753 (+19%)
2,26 → 3,12 triệu (+38%)
38,2 → 43,2 s

 
Khoảng cách retention giữa hai model giảm từ 5,87 điểm xuống 2,02 điểm, tức centering thu hẹp khoảng 66% khoảng cách. Kết quả ổn định qua cả 5 seed (mức tăng của Pic2Word nằm trong khoảng 3,80–4,43 điểm), và em đã kiểm tra đúng việc thứ hạng chính xác không đổi (sai số lớn nhất 3·10⁻⁷). Đây là một kết quả có giá trị.
2.2. Vì sao chưa kết luận được
Sau centering, đồ thị Pic2Word có thêm 38% số cạnh. Nhiều khả năng là do bước chọn láng giềng của HNSW (giữ một ứng viên nếu nó gần nút đang xét hơn gần các láng giềng đã chọn) cho kết quả khác khi dùng tích vô hướng trên vector đã trừ trung bình và không chuẩn hoá lại, nên giữ lại nhiều cạnh hơn. Đồ thị dày hơn thì ở cùng efSearch mỗi truy vấn phải tính nhiều khoảng cách hơn: độ trễ tăng 19%.
Vì vậy một phần, có thể là phần lớn, mức tăng retention có thể chỉ là mua độ chính xác bằng chi phí, giống như tăng efSearch hoặc tăng M trên đồ thị gốc. Phản biện sẽ hỏi đúng câu này. Muốn gọi centering là một cải tiến, phải so ở cùng chi phí.
2.3. Thí nghiệm cần làm
C1. So sánh ở cùng chi phí tìm kiếm
Quét efSearch ∈ {32, 48, 64, 96, 128, 160, 192, 256, 384} cho cả đồ thị gốc và đồ thị centering (cùng M = 32, efConstruction = 200). Với mỗi điểm đo: retention@10, số phép tính khoảng cách trung bình mỗi truy vấn (ndis, lấy từ faiss.cvar.hnsw_stats) và độ trễ. Vẽ retention theo ndis, hai đường trên cùng một hình, 5 seed. Dùng ndis làm trục chính vì không phụ thuộc máy và không lẫn chi phí vòng lặp Python (JSON của em ghi độ trễ có tính cả phần này). Mã ở Phụ lục A.
C2. So sánh ở cùng mật độ đồ thị
Dựng đồ thị gốc với M ∈ {32, 40, 48, 64} và tìm M cho số cạnh xấp xỉ đồ thị centering M = 32 (khoảng 3,12 triệu với Pic2Word). So retention ở cùng số cạnh và cùng ndis. Nếu đồ thị gốc với M lớn hơn đạt được cùng kết quả thì centering chỉ là một cách gián tiếp để tăng mật độ.
C3. Đối chứng âm với metric L2
Dựng đồ thị centering với METRIC_L2. Vì khoảng cách L2 không đổi khi tịnh tiến, đồ thị phải tương đương đồ thị gốc, và retention phải bằng retention gốc (sai khác chỉ do ngẫu nhiên khi dựng). Nếu đúng như vậy, em chứng minh được hiệu ứng đến từ hình học tích vô hướng trên vector không chuẩn hoá. Đây là đối chứng rất rẻ nhưng làm lập luận chặt hơn nhiều.
C4. Cơ chế
1. Đo chuẩn của vector trung bình ‖μ‖ và cosine trung bình giữa các cặp ảnh khác nhau, MCS = (N‖μ‖² − 1)/(N − 1). MCS cao nghĩa là các vector dồn vào một hình nón hẹp (hiệu ứng "cone" mà Liang et al. 2022 mô tả cho CLIP). Bài của Herman (Mục 5) báo cáo centering có lợi cho các encoder có MCS cao (trong bối cảnh biểu diễn FDE của họ). Dự đoán cần kiểm tra: Pic2Word có MCS cao hơn SEARLE, điều đó giải thích vì sao Pic2Word được lợi nhiều hơn hẳn.
2. Đo N10 phía gallery trước và sau centering (Phụ lục B). Lưu ý: "Delta skewness = 0" trong báo cáo hiện tại là đương nhiên, vì N10 phía truy vấn không thể đổi khi thứ hạng chính xác không đổi. Đại lượng có thể thay đổi, và là ứng viên trung gian, là N10 phía gallery và bậc vào.
3. So phân phối bậc vào của các láng giềng chính xác trước và sau centering, và tỉ lệ bỏ sót theo nhóm bậc vào sau centering. Câu hỏi cần trả lời: centering cứu được láng giềng vì nâng bậc vào của chúng (dịch sang nhóm bậc vào cao), hay vì giảm tỉ lệ bỏ sót ngay trong cùng một nhóm bậc vào?
C5. Truy vấn nào được lợi
Dùng centering_per_query.parquet: tính mức tăng retention của từng truy vấn (trung bình 5 seed), so với s1 của truy vấn đó, chia s1 thành 5 nhóm phân vị trong từng model. Nếu lợi ích tập trung ở truy vấn có s1 thấp, centering và giả thuyết H-MG (Mục 4) đang nói về cùng một hiện tượng. Mã ở Phụ lục E.
C6. Tổng quát hoá
- Cấu hình stress (M = 16, efSearch = 32): ở đây SEARLE có nhiều lỗi hơn, nên kiểm tra được centering có giúp SEARLE hay không. Hiện SEARLE đã ở mức 96,7%, gần trần.
- CIRR, FashionIQ và CLIP4Cir; gallery 500K sau khi kiểm định distractor.
- mAP@10 theo ground truth (220 truy vấn val) của kết quả HNSW trước và sau centering. Thứ hạng chính xác không đổi nên mAP của tìm kiếm chính xác không đổi, nhưng mAP của kết quả HNSW phải tăng theo retention; cần báo cáo để chứng minh lợi ích tới được người dùng.
2.4. Quy tắc quyết định
Viết dự đoán của em vào báo cáo trước khi chạy C1, rồi đối chiếu:
- Đường centering nằm trên đường gốc ở cùng ndis, khoảng tin cậy tách rời: centering là cải tiến thật. Khi đó nó rất có thể trở thành đóng góp cho họ chỉ mục đồ thị: không huấn luyện, không đổi thứ hạng chính xác, không nhúng lại gallery, chỉ trừ một vector trung bình khi dựng chỉ mục.
- Hai đường trùng nhau: centering chỉ đổi chi phí lấy độ chính xác. Vẫn ghi vào bài như một quan sát, nhưng không phải đóng góp.
3. Module A.1: sửa cách đo và cách đọc
3.1. N10 phía truy vấn chưa đo được hubness
Báo cáo hiện tại định nghĩa N10(x) là số truy vấn có ảnh x trong top-10 chính xác. Với 1.020 truy vấn, đại lượng này có bốn vấn đề:
1. Tỉ lệ "anti-hub" có sàn toán học. 1.020 truy vấn × 10 vị trí = 10.200 vị trí, nên nhiều nhất 10.200 ảnh khác nhau có N10 ≥ 1. Tỉ lệ ảnh có N10 = 0 không thể thấp hơn 1 − 10.200/123.403 = 91,7%. Con số 93,3% và 93,5% là hệ quả của số truy vấn, không phải thuộc tính của không gian nhúng.
2. N10 ≥ 1 theo cấu trúc. Mỗi láng giềng trong bảng đã nằm trong top-10 của chính truy vấn đang xét (em đã nhận ra điều này). Phải dùng N10 loại trừ chính truy vấn đó: N10_loo = N10 − 1. Nhóm N10_loo = 0 khi đó có nghĩa rõ ràng: không truy vấn nào khác lấy ảnh này.
3. Nhóm nhỏ trông như có độ chính xác cao. Nhóm N10 = 10–29 chỉ có 2 ảnh (SEARLE) và 5 ảnh (Pic2Word). Bootstrap theo truy vấn coi 66 dòng của 5 ảnh như các quan sát gần độc lập, nên khoảng [19,7%; 42,7%] hẹp hơn thực tế rất nhiều. Với 5 ảnh, không kết luận được gì từ nhóm này.
4. Không so được với Report_3. Độ lệch 6,80 và 8,33 là của N10 phía truy vấn; con số 2,66 ở Report_3 là của N10 phía gallery. Hai đại lượng khác nhau phải có hai tên khác nhau trong báo cáo.
Có một thống kê phía truy vấn dùng được: độ phủ, tức số ảnh khác nhau xuất hiện trong hợp tất cả các top-10. Từ JSON của em: SEARLE 8.327 ảnh, Pic2Word 8.067 ảnh (81,6% và 79,1% của 10.200 vị trí). Pic2Word dồn truy vấn vào ít ảnh hơn một chút. Báo cáo con số này thay cho tỉ lệ anti-hub.
Việc cần làm: tính N10 phía gallery (k = 10, tích vô hướng, Phụ lục B); đưa cả N10 phía gallery và N10_loo vào hồi quy; chia nhóm theo phân vị thay vì ngưỡng cố định 0/5/10/30 để nhóm nào cũng đủ số ảnh.
3.2. Bậc vào HNSW: kết quả rõ nhất của module
Tỉ lệ bỏ sót giảm đơn điệu khi bậc vào tăng, ở cả hai model, với khoảng tin cậy hẹp. Đồng thời HNSW gần như không có nút cô lập: chỉ 6 nút (SEARLE) và 14 nút (Pic2Word) trên 123.403 có bậc vào bằng 0. Trong bài, viết rõ: cơ chế là bậc vào thấp, không phải bị cô lập; điều này sửa lại kết luận ở Report_3 bằng đo trực tiếp.
Thầy làm thử một phân rã đơn giản trên thang xác suất, chỉ dùng bảng 4.2.2 của em:
Chỉ số
SEARLE
Pic2Word
Tỉ lệ láng giềng chính xác có bậc vào dưới 10
12,7%
23,5%
Tỉ lệ bỏ sót thực tế
3,33%
9,16%
Tỉ lệ bỏ sót nếu mang cơ cấu bậc vào của model kia
4,88%
7,35%
Phần chênh lệch do cơ cấu bậc vào
1,55 điểm (27%)
1,81 điểm (31%)

 
Nghĩa là khác biệt về phân phối bậc vào giải thích khoảng 27–31% của chênh lệch 5,83 điểm. Khoảng 70% còn lại nằm bên trong từng nhóm bậc vào: ở cùng mức bậc vào, Pic2Word vẫn bỏ sót nhiều hơn (nhóm 10–29: 6,8% so với 2,5%; nhóm 5–9: 17,6% so với 8,5%). Kiểu con số này nên đưa vào bài thay cho đường đi của β: dễ hiểu và không vướng vấn đề non-collapsibility mà em đã nêu.
Việc cần làm: thay hình 1 bằng hình tỉ lệ bỏ sót theo bậc vào (trục hoành thang log, hai model, khoảng tin cậy, ghi số ảnh khác nhau ở mỗi nhóm); làm lại phân rã bằng mô hình (Phụ lục C) để thêm các biến khác; kiểm tra độ nhạy khi gom cụm theo ảnh (Phụ lục D).
3.3. Hồi quy GEE: đọc lại và bổ sung
(a) Tham số hoá lại s1 và c_contrast
c_contrast = s1 − s100 chứa s1, nên hai hệ số khó đọc riêng. Viết lại theo s1 và s100 (cùng một mô hình, chỉ đổi cách biểu diễn): hệ số của s1 = −28,19 + 16,87 = −11,32; hệ số của s100 = −16,87. Tăng 0,01 ở s1 (giữ s100) nhân odds bỏ sót với 0,893; tăng 0,01 ở s100 (giữ s1) nhân với 0,845. Cả hai đều âm: truy vấn có mức tương đồng chung với gallery thấp hơn thì dễ bị bỏ sót hơn. Cách đọc này rõ hơn và khớp trực tiếp với giả thuyết H-MG.
(b) Thang đo khác nhau giữa hai backbone
Theo file cấu hình của em, SEARLE dùng CLIP ViT-B/32 (512 chiều), Pic2Word dùng ViT-L/14 (768 chiều). Mức cosine của hai không gian không nhất thiết so sánh trực tiếp được. Việc s1 và s100 "hấp thụ" biến model ở M2 có thể do khác biệt hình học thật (truy vấn Pic2Word nằm xa gallery hơn), hoặc chỉ do hai không gian có thang cosine khác nhau. Cần:
- Báo cáo phân phối s1, s100 của từng model (phân vị 5–25–50–75–95) và vùng chồng lấp; khớp lại M2 chỉ trên vùng chồng lấp.
- Khớp riêng từng model với s1, s100 đã chuẩn hoá trong model, để xem chúng có dự báo lỗi bên trong mỗi model hay không. Đây là câu hỏi không bị ảnh hưởng bởi thang đo.
- Thí nghiệm H-MG (Mục 4) là cách phân xử dứt khoát, vì nó so truy vấn CIR với truy vấn ảnh bên trong cùng một không gian.
(c) Tương tác
Mô hình gộp giả định tác dụng của bậc vào và của s1 giống nhau ở hai không gian. Thêm các số hạng model × biến, hoặc khớp riêng từng model, rồi báo cáo hệ số của từng model cạnh nhau.
(d) Phân rã trên thang xác suất
Em đã trích đúng Karlson, Holm và Breen (2012) về việc mức giảm β không đo phần trung gian. Cách thực dụng: khớp mô hình riêng cho SEARLE, dùng nó dự báo trên dữ liệu Pic2Word, rồi tách chênh lệch tỉ lệ bỏ sót thành phần do khác biệt phân phối đặc trưng và phần do khác biệt hệ số (Phụ lục C). Phân rã chi tiết theo nhóm biến phụ thuộc thứ tự thêm biến, nên báo cáo cả hai thứ tự: bậc vào trước rồi đặc trưng truy vấn, và ngược lại.
(e) Phụ thuộc theo ảnh
Cùng một ảnh xuất hiện ở nhiều truy vấn. Chạy lại GEE với cụm theo ảnh (neighbor_id) và so sai số chuẩn với bản cụm theo truy vấn. Nếu sai số chuẩn thay đổi ít, kết luận vững.
(f) ID truy vấn tập test và trạng thái mã nguồn
- Báo cáo ghi ID truy vấn tập test được dựng lại từ thứ tự annotation. Vì GEE gom hai model theo query_id, sai lệch ID sẽ gom nhầm cụm. Trích lại vector của 800 truy vấn test kèm ID từng dòng; việc này nhanh và xoá được một hạn chế mà phản biện chắc chắn sẽ hỏi.
- Mọi JSON đều ghi git_dirty = True. Chạy bản kết quả cuối từ một commit sạch.
3.4. Viết lại giả thuyết và nhãn trạng thái
Giả thuyết
Nhãn
Bằng chứng
H1a: láng giềng có bậc vào HNSW thấp bị bỏ sót nhiều hơn
Ủng hộ (mô tả)
Đơn điệu ở cả hai model; cần kiểm tra khi cụm theo ảnh
H1b: hubness phía gallery (N10 gallery thấp) dẫn tới bậc vào thấp
Chưa kiểm định
Cần N10 phía gallery (3.1)
H1c: ảnh ít được truy vấn khác lấy (N10_loo thấp) bị bỏ sót nhiều hơn
Chưa kiểm định
Cần N10_loo (3.1)
H2: khoảng cách SEARLE–Pic2Word được giải thích một phần bởi biến đồ thị
Ủng hộ một phần
Khoảng 27–31% liên quan tới phân phối bậc vào; phần lớn còn lại gắn với mức tương đồng của truy vấn, chưa tách khỏi khác biệt thang đo

 
3.5. Trình bày
- Phần giải thích hồi quy logistic (mục 4.4.1–4.4.9) viết rất tốt cho việc học, nhưng làm báo cáo dài gấp ba. Chuyển sang một file ghi chú riêng; thân báo cáo giữ bảng, hình và kết luận.
- Câu nhận xét tự động ở mục 4.2 ("Nhóm có miss rate thấp nhất trong seed reference hiện hành là...") khó đọc. Với các câu diễn giải, sinh số tự động nhưng viết câu bằng tay.
- Hình 3: thêm hình retention theo ndis (C1). Hình cột từ trục 0 làm khó thấy chênh lệch; hình khoảng tin cậy bên phải đã tốt.
- Hình 1: không vẽ cột cho nhóm không có dữ liệu; trục tung đặt tới khoảng 40% thay vì 100%.
4. Tín hiệu từ M2: nên làm giả thuyết H-MG sớm
M2 cho thấy sau khi đưa mức tương đồng của truy vấn vào mô hình, chênh lệch gắn với tên model gần như biến mất. Kết hợp với bài của Bao et al. (Mục 5.2), vốn chứng minh truy vấn lệch phân phối so với gallery làm ANN phải làm nhiều việc hơn mới đạt cùng recall, giả thuyết H-MG ở R2 (truy vấn CIR nằm ngoài đa tạp ảnh) nay có cơ sở mạnh hơn nhiều. Bao et al. chỉ làm truy hồi văn bản và nêu truy hồi đa phương thức là hướng mở; CIR nằm đúng khoảng trống đó.
Thiết kế
1. Đo khoảng cách phân phối giữa tập truy vấn và gallery cho từng model bằng MMD bình phương (cách Bao et al. dùng), với kernel RBF và độ rộng chọn theo trung vị khoảng cách. Lấy mẫu 5.000 ảnh gallery để giảm chi phí.
2. Đối chứng truy vấn ảnh như R2 Phụ lục E: 1.000 ảnh gallery không phải ground truth làm truy vấn, loại khỏi gallery, chạy cùng chỉ mục với truy vấn CIR. So tỉ lệ bỏ sót, s1, s100 giữa hai loại truy vấn trong từng model.
3. Trong từng model: tỉ lệ bỏ sót theo 5 nhóm phân vị s1, có khoảng tin cậy.
4. Nối với centering: kết quả C5 (Mục 2.3).
Dự đoán cần viết trước khi chạy: Pic2Word có MMD lớn hơn SEARLE; truy vấn ảnh gần như không bị bỏ sót ở cả hai model; trong mỗi model, nhóm s1 thấp bỏ sót nhiều hơn. Nếu cả ba đúng, đây có thể là phát hiện trung tâm của bài, đặc thù cho CIR.
5. Hai bài báo mới cần đọc ngay
5.1. Herman (2026), "Closed Forms and Synthetic Twins: Predicting Approximate Nearest Neighbor Recall from Embedding Statistics"
arXiv 2609.00364, bản v1 ngày 31/08/2026, một tác giả độc lập, chưa qua phản biện. Theo tóm tắt và bản HTML:
- Dự báo recall của chỉ mục ANN trước khi dựng, theo từng họ: công thức đóng cho các họ lượng tử hoá (PQ), dạng có hằng số khớp cho IVF, và một "bản sao tổng hợp" cho HNSW (sai số tuyệt đối trung bình 0,039 trên 17 encoder).
- Coi biên điểm số (score margin) là thống kê then chốt mà không phép biến đổi hậu kỳ nào thay đổi được, và đề xuất huấn luyện encoder để làm sắc biên điểm số, báo cáo là tăng recall cho mọi họ chỉ mục.
- Bàn về centering và whitening như một sự đánh đổi giữa thay đổi ngữ nghĩa và lợi ích chỉ mục; trong bối cảnh FDE, centering có lợi cho encoder có MCS cao và có hại cho encoder có MCS thấp; hubness đo theo L2 bất biến khi centering và là chỉ số dự báo không nhất quán cho recall của đồ thị; có dùng biên định tuyến theo từng điểm cho IVF.
- Tóm tắt không nhắc tới CLIP, ảnh hay truy vấn đa phương thức.
Hệ quả cho đề tài:
- Score-Gap Loss ở dạng ban đầu vừa có thể bất khả thi với IVFPQ m ≤ 16 (R2, Mục 4.1), vừa đã được Herman đề xuất dưới dạng tổng quát. Nên bỏ hẳn hướng này như một đóng góp.
- Đóng góp "dự báo retention trước khi dựng chỉ mục" phải được phân biệt rõ với Herman, ví dụ bằng các thống kê đặc thù CIR phía truy vấn (MMD, s1), hoặc bỏ.
- Kết quả âm tính ở A.5 (hubness không dự báo được retention sau khi kiểm soát kích thước gallery) nay có đồng thuận từ một nguồn độc lập; nên trích dẫn.
- Centering của em chỉ có tác dụng với tích vô hướng trên vector không chuẩn hoá lại, khớp với nhận xét của Herman về tính bất biến của L2. Đối chứng C3 sẽ là bằng chứng trực tiếp cho điều này.
5.2. Bao et al. (2025), "Alleviating Performance Degradation Caused by Out-of-Distribution Issues in Embedding-Based Retrieval"
Findings of EMNLP 2025, nhóm Microsoft. Đo độ lệch phân phối giữa truy vấn và tài liệu bằng MMD bình phương; cho thấy truy vấn lệch phân phối cần nhiều công tìm kiếm hơn để đạt cùng recall, và huấn luyện InfoNCE làm khoảng lệch này rộng thêm; đề xuất một số hạng điều chuẩn L2 kéo truy vấn về phía tài liệu, không tốn thêm chi phí suy luận. Các chỉ mục được thử gồm HNSW, DiskANN, RoarGraph, IVF và IVFPQ; tăng tốc tới 2,6 lần (coCondenser) và 4,1 lần (RetroMAE) ở cùng recall, lợi ích lớn nhất ở các chỉ mục đồ thị. Thực nghiệm chỉ có văn bản; phần Limitations nêu truy hồi đa phương thức là câu hỏi mở.
Hệ quả: đây là căn cứ chính để định vị H-MG, và số hạng điều chuẩn của họ là một baseline tự nhiên nếu sau này em làm can thiệp có huấn luyện (giai đoạn D).
Việc cần làm: đọc toàn văn hai bài, viết cho mỗi bài nửa trang theo mẫu cũ (họ giải bài toán gì, đại lượng gì, ta khác ở đâu, có cần so sánh thực nghiệm không), và thêm cả hai vào bảng "công trình gần nhất".
6. Điều chỉnh phạm vi và thứ tự thực hiện
- Tạm hoãn P2c (A.5 ở N cố định). Phân tích theo láng giềng đã thay vai trò của nó; giữ câu kết luận âm tính trung thực từ R2, kèm trích dẫn Herman.
- Giữ P2a (nhiễu PQ có dấu, đường cong hoán vị) nhưng làm sau centering và H-MG.
 
#
Việc
Ước lượng
Sản phẩm
1
C1–C3: centering ở cùng chi phí, cùng mật độ, đối chứng L2
2 ngày
Hình retention theo ndis; bảng so sánh
2
C4–C5: cơ chế centering, truy vấn nào được lợi
1–2 ngày
Bảng ‖μ‖, MCS, N10 gallery trước/sau
 
Gửi thầy kết quả bước 1–2 trước khi đi tiếp
 
 
3
Sửa A.1 theo Mục 3 (N10, phân rã, cụm theo ảnh, ID test)
2 ngày
Báo cáo A.1 bản mới
4
H-MG (Mục 4)
2–3 ngày
Bảng so sánh truy vấn CIR và truy vấn ảnh
5
Đọc Herman và Bao, viết ghi chú (làm xen kẽ)
1 ngày
Hai ghi chú nửa trang
6
P2a
2 ngày
Đường cong hoán vị
7
C6: tổng quát hoá centering
2–3 ngày
Bảng nhiều bộ dữ liệu và cấu hình

 
7. Cần nộp lần tới
- Hình retention theo ndis cho đồ thị gốc, đồ thị centering (IP) và đồ thị centering (L2), 5 seed, hai model.
- Bảng so sánh ở cùng số cạnh (C2).
- Bảng ‖μ‖, MCS, độ lệch và tỉ lệ N10 = 0 phía gallery, trước và sau centering, cho hai model.
- Bảng mức tăng retention theo nhóm phân vị s1.
- Nếu đã làm: bản A.1 đã sửa và kết quả H-MG.
- Một trang tóm tắt: mỗi giả thuyết một dòng, nhãn trạng thái, bằng chứng quyết định, và dự đoán em đã viết trước khi chạy.
8. Tài liệu đọc thêm
1. Herman, "Closed Forms and Synthetic Twins: Predicting Approximate Nearest Neighbor Recall from Embedding Statistics", arXiv 2609.00364, 2026.
2. Bao et al., "Alleviating Performance Degradation Caused by Out-of-Distribution Issues in Embedding-Based Retrieval", Findings of EMNLP 2025, tr. 6418–6427.
3. Karlson, Holm, Breen, "Comparing Regression Coefficients Between Same-sample Nested Models Using Logit and Probit: A New Method", Sociological Methodology, 2012 (phương pháp KHB, nếu em muốn phân rã trên thang log-odds).
4. Liang et al., "Mind the Gap", NeurIPS 2022: đọc lại phần "cone effect" phục vụ C4.
5. Mã nguồn FAISS: faiss/impl/HNSW.h và HNSW.cpp (hàm chọn láng giềng shrink_neighbor_list, cấu trúc HNSWStats).
PHỤ LỤC: MÃ THAM KHẢO
Các đoạn mã là khung tham khảo; em kiểm tra lại với FAISS 1.15.1 và tên cột trong dữ liệu của em. xb là vector gallery (chuẩn hoá L2, float32), xq là vector truy vấn, gt10 là top-10 chính xác.
Phụ lục A. Retention theo số phép tính khoảng cách (C1)
import faiss, numpy as np
 
def sweep(index, xq, gt10, ef_list):
    out = []
    for ef in ef_list:
        index.hnsw.efSearch = ef
        faiss.cvar.hnsw_stats.reset()
        _, I = index.search(xq, 10)
        # số phép tính khoảng cách trung bình mỗi truy vấn
        ndis = faiss.cvar.hnsw_stats.ndis / len(xq)
        ret = np.mean([len(set(a) & set(b)) / 10 for a, b in zip(I, gt10)])
        out.append(dict(ef=ef, ndis=ndis, retention=ret))
    return out
 
EF = [32, 48, 64, 96, 128, 160, 192, 256, 384]
mu = xb.mean(0, keepdims=True)
for name, X, metric in [("goc", xb, faiss.METRIC_INNER_PRODUCT),
                        ("centering_IP", xb - mu, faiss.METRIC_INNER_PRODUCT),
                        ("centering_L2", xb - mu, faiss.METRIC_L2)]:
    idx = faiss.IndexHNSWFlat(X.shape[1], 32, metric)
    idx.hnsw.efConstruction = 200
    idx.add(np.ascontiguousarray(X, dtype="float32"))
    curve = sweep(idx, xq, gt10, EF)     # lặp cho 5 seed dựng đồ thị
# Vẽ retention theo ndis (trục hoành log); so ở cùng ndis bằng nội suy

Phụ lục B. N10 phía gallery và MCS, trước và sau centering (C4)
def gallery_kocc(X, k=10, bs=4096):
    idx = faiss.IndexFlatIP(X.shape[1]); idx.add(X)
    n = len(X); cnt = np.zeros(n, dtype=np.int64)
    for s in range(0, n, bs):
        _, I = idx.search(X[s:s + bs], k + 1)
        for r, row in enumerate(I):
            row = row[row != s + r][:k]   # bỏ chính nó theo ID
            np.add.at(cnt, row, 1)
    return cnt
 
n = len(xb); mu = xb.mean(0)
# cosine trung bình giữa các cặp ảnh khác nhau
mcs = (n * float(mu @ mu) - 1) / (n - 1)
n10_goc = gallery_kocc(xb)
n10_cen = gallery_kocc((xb - mu).astype("float32"))
# Báo cáo cho từng model: ||mu||, mcs, skewness và tỉ lệ N10 = 0
# của n10_goc và n10_cen

Lưu ý: sau centering, tích vô hướng của một vector với chính nó không còn chắc chắn lớn nhất, nên phải loại chính nó theo ID như trong mã.
Phụ lục C. Phân rã chênh lệch trên thang xác suất (3.3d)
import statsmodels.formula.api as smf
f = "missed ~ rank + log_indeg + log_n10_gal + s1 + s100"
S = df[df.model == "searle"];  Pw = df[df.model == "pic2word"]
fit_s = smf.logit(f, S).fit(disp=0)
gap   = Pw.missed.mean() - S.missed.mean()   # khoảng 5,83 điểm
cf    = fit_s.predict(Pw).mean()     # đặc trưng Pic2Word, hệ số SEARLE
expl  = cf - S.missed.mean()         # phần do khác phân phối đặc trưng
unexp = Pw.missed.mean() - cf        # phần do khác hệ số
print(gap, expl, unexp, expl / gap)
# Làm lại theo chiều ngược (hệ số Pic2Word trên đặc trưng SEARLE);
# phân rã chi tiết: thay lần lượt từng nhóm biến, báo cáo cả hai thứ tự;
# khoảng tin cậy: bootstrap theo truy vấn

Phụ lục D. Độ nhạy khi gom cụm theo ảnh (3.3e)
import pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf
fam = sm.families.Binomial()
form = "missed ~ is_pic2word + rank + log_n10_gal + log_indeg + s1 + s100"
by_q   = smf.gee(form, groups="query_id",    data=df, family=fam).fit()
by_img = smf.gee(form, groups="neighbor_id", data=df, family=fam).fit()
print(pd.DataFrame({"se_query": by_q.bse, "se_image": by_img.bse}))

Phụ lục E. Mức tăng do centering theo s1 (C5)
import pandas as pd
# đổi tên cột theo file của em
pq = pd.read_parquet("centering_per_query.parquet")
g = (pq.groupby(["model", "query_id"])[["ret_before", "ret_after"]]
       .mean().assign(gain=lambda d: d.ret_after - d.ret_before))
g = g.join(qfeat.set_index(["model", "query_id"])[["s1", "s100"]])
g["s1_bin"] = (g.groupby(level=0)["s1"]
               .transform(lambda v: pd.qcut(v, 5, labels=False)))
print(g.groupby([g.index.get_level_values(0), "s1_bin"])["gain"].mean())
# Kèm khoảng tin cậy bootstrap theo truy vấn cho từng nhóm

 

