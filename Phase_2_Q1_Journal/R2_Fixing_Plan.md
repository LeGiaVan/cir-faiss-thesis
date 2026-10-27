Thầy đã xem các module, em đã cố gắng làm rất tốt. Tuy nhiên, khi đối chiếu, thầy thấy nhiều kết luận trong lời văn không khớp, có chỗ ngược hẳn với chính bảng số liệu của em. Đây là việc quan trọng cần sửa, quan trọng hơn mọi thí nghiệm mới vì một phản biện chỉ cần phát hiện một chỗ như vậy là sẽ không tin phần còn lại của bài.
1. Tóm tắt
Trạng thái thật của từng kết quả, sau khi thầy tính lại từ số liệu gốc:
Module
Báo cáo của em viết
Số liệu của em thực sự cho thấy
Trạng thái
A.2
Nhiễu PQ
Khớp hoàn hảo lý thuyết; tỉ số 16–18×
Đúng bậc độ lớn. Nhưng đại lượng quyết định xếp hạng là nhiễu trên top-10 (RMS 0,045), và nó có độ lệch hệ thống, một phát hiện em chưa khai thác
Ủng hộ, cần đo lại đúng đại lượng
A.1
Hubness
Xác nhận hoàn toàn; p < 0,05
Độ lệch hubness hai model bằng nhau (2,659 / 2,659); p = 0,20 và 0,54; khoảng cách hai model nằm ngay trong nhóm Normal
Chưa xác nhận
A.5
Dự báo hình học
Hubness là chỉ số duy nhất dự báo được
LID mạnh hơn hubness; log N mạnh nhất (ρ = −0,945); kiểm soát N thì mọi chỉ số mất ý nghĩa
Không được ủng hộ
A.3
Định tuyến IVF
Chứng minh định lý
Đúng, nhưng là đồng nhất thức theo cấu trúc của IVFFlat, xác nhận cài đặt đúng, không phải phát hiện
Đạt (kiểm tra cài đặt)
A.4
Quy mô
10K–1M; tăng tốc 25–50×
Dừng ở 500K; tăng tốc 11–137×; retention HNSW gần như phẳng từ 123K–500K → cần kiểm định distractor
Cần kiểm định

 
Thứ tự làm việc (chi tiết ở Mục 7):
1. P0: Sửa báo cáo cho khớp số liệu (Mục 3). Không chạy thí nghiệm mới trước khi xong việc này.
2. P1: Chuẩn hoá cấu hình dùng chung cho mọi module, chạy lại các số bị ảnh hưởng (Mục 3.2).
3. P2: Làm lại ba kiểm định quyết định: nhiễu PQ có dấu và đường cong hoán vị (4.1), hubness theo từng láng giềng (4.2), dự báo hình học ở N cố định (4.3).
4. P3: Kiểm định distractor và thí nghiệm modality gap (4.5 và Mục 5).
5. P4: Baseline giai đoạn C (Mục 6). Gửi thầy kết quả P0–P2 trước khi làm P3–P4.
2. Những điểm em làm tốt
- Tổ chức thực nghiệm thành module, mỗi module có báo cáo, JSON và hình riêng. Cấu trúc này dễ kiểm tra và dễ tái lập.
- Lưu số liệu thô (retention từng truy vấn, mẫu nhiễu từng cặp).
- Bảng kiểm định trong A.1 được ghi trung thực (cột "Significant: False"). Vấn đề chỉ nằm ở lời văn bên dưới.
- A.2 phát hiện một điều thầy không dự đoán: nhiễu trên các ứng viên top-10 lớn gấp khoảng 3 lần nhiễu trên cặp ngẫu nhiên (2,8–3,2 lần tuỳ model và m). Đây là phát hiện có giá trị thật, và Mục 4.1 giải thích vì sao nó quan trọng.
- A.3 cho kết quả khớp chính xác giữa retention và tỉ lệ bao phủ bằng chứng pipeline IVF của em cài đặt đúng.
- A.4 đã dựng được trục quy mô tới 500K và cho thấy xu hướng tăng tốc rõ ràng. Đây là hướng đúng để trả lời phản biện "gallery nhỏ thì không cần ANN".
- Em đã chủ động đặt ra bước tiếp theo (OPQ, QB-Norm). Hướng đi đúng, chỉ cần điều chỉnh danh sách (Mục 6).
3. Vấn đề xuyên suốt (cần sửa trước tiên)
3.1. Kết luận không khớp số liệu (P0)
Danh sách dưới đây đối chiếu trong báo cáo với số liệu trong chính JSON. Em sửa lần lượt từng dòng.
#
Báo cáo viết
Số liệu cho thấy
1
A.1: "Pic2Word có độ lệch hubness (skewness) cao hơn rõ rệt"; bảng ghi "Pic2Word lệch hơn 1,00×"
Skewness SEARLE 2,659, Pic2Word 2,659 - bằng nhau đến chữ số thứ ba. "1,00×" nghĩa là không khác.
2
A.1: "Pic2Word có đuôi phân phối dày hơn nhiều"
Ngược lại: kurtosis SEARLE 13,75 > Pic2Word 11,74; hub lớn nhất SEARLE 231 > Pic2Word 182.
3
A.1: "độ sụt giảm rõ rệt với ý nghĩa thống kê rất cao (p < 0,05)"
p = 0,20 (SEARLE) và 0,54 (Pic2Word); chính bảng của em ghi "Significant: False".
4
A.1: anti-hub "hoàn toàn không có cạnh đi vào trong quá trình dựng đồ thị HNSW"
N10 = 0 là trong đồ thị kNN chính xác, không phải đồ thị HNSW. HNSW thêm cạnh ngược khi chèn điểm, nên điểm có N10 = 0 vẫn có thể có cạnh vào. Phải đo trực tiếp (Phụ lục B).
5
A.5: LID (ρ = −0,881) được đánh giá "Yếu / Không phản ánh được độ khó"
LID có |ρ| lớn hơn hubness (0,857) và p nhỏ hơn (0,0039 so với 0,0065).
6
A.5: "Hubness Skewness là đại lượng duy nhất có tương quan chặt chẽ"
Sai theo dòng 5, và log N còn mạnh hơn cả hai (ρ = −0,945). Xem 4.3.
7
A.3: "nprobe = 8: tỉ lệ ứng viên được probe 91,5%, retention 91,5%"; "SEARLE nprobe = 16 đạt 96,1%"; "Pic2Word nprobe = 32 đạt 96,8%"
Bảng: 86,18% / 92,36% / 96,05%. Lời văn không khớp bảng (có thể đã lấy số từ một lần chạy khác).
8
A.4: tiêu đề "10K – 1M"; "ở 10K FlatIP ~0,25 ms, tăng tốc 2–5×"; "ở 1M tăng tốc 25–50×"; hình ghi "1 Million Vectors"
Dữ liệu dừng ở 500K; ở 10K FlatIP 0,553 ms, tăng tốc 11,1×; ở 500K tăng tốc 137,4×.
9
A.4 và chú thích hình: HNSW có chi phí "O(log N)"
Khớp log–log trên số liệu của em: độ trễ HNSW tăng theo N^0,42 (FlatIP N^1,07; IVFFlat N^0,60). Không phải logarit.
10
A.2: RMS thực đo "gần như trùng khít dự báo lý thuyết", "khớp hoàn hảo"
Chỉ cặp ngẫu nhiên mới gần lý thuyết (0,0160 so với 0,0189, lệch 15%). Hình phân phối vẽ histogram top-10 nhưng chồng đường half-normal của cặp ngẫu nhiên - hình đang cho thấy không khớp. Xem 4.1.
11
A.2: "ε = 2δ ≈ 0,038 – 0,050"
Nếu δ là nhiễu top-10 (0,045) thì 2δ = 0,09; nếu là nhiễu toàn cục (0,019) thì 2δ = 0,038. Khoảng 0,038–0,050 không ứng với δ nào.
12
A.3: "Chứng minh định lý: IVFFlat là chỉ mục không nhiễu"
Là đồng nhất thức theo cấu trúc, không cần chứng minh bằng thực nghiệm. Xem 4.4.
13
Tổng kết: "Hoàn thành 100%", "Đột phá khoa học", "Phát hiện mới đầu tiên trong CIR"
Hai trong năm kết luận chính chưa đứng được. Bỏ các cụm từ này.

 
3.2. Cấu hình không thống nhất giữa các module (P1)
Cùng một đại lượng, retention@10 của HNSWFlat trên CIRCO đang có ba giá trị khác nhau trong ba nơi:
Nguồn
Cấu hình HNSW
SEARLE
Pic2Word
Bài ICRCV (Bảng V)
M = 32, efSearch = 128
97,0%
91,5%
A.1 (và A.4 với SEARLE)
Không ghi
93,6%
86,7%
A.5
M = 16, efSearch = 32
74,1%
56,0%

 
Tương tự, giá trị Relative Contrast và LID trong A.5 (RC 3,864 / 3,553; LID 12,2 / 11,9) khác hẳn Bảng VIII bài ICRCV (RC 1,130 / 1,148; LID 25,7 / 25,2), trong khi báo cáo A.1 lại trích số cũ. Hai cách tính khác nhau đang được dùng lẫn lộn. FlatIP trên CIRCO 123K cũng đo được 7,66 ms trong A.4 so với khoảng 3,3 ms trong bài ICRCV.
Việc cần làm:
1. Tạo một file cấu hình duy nhất (ví dụ configs/reference.yaml) chứa: cấu hình HNSW tham chiếu (dùng đúng M = 32, efSearch = 128 như ICRCV) và một cấu hình "chịu tải" (M = 16, efSearch = 32 - nhiều lỗi hơn nên có nhiều sự kiện để phân tích cơ chế); efConstruction; nlist, nprobe cho IVF; m, nprobe cho IVFPQ; tập truy vấn; số luồng, batch, số lần đo lặp.
2. Mỗi file JSON đầu ra phải ghi kèm: cấu hình đã dùng, model, bộ dữ liệu, số truy vấn, seed, ngày chạy và mã commit git.
3. Chọn một định nghĩa RC và LID (ghi công thức, giá trị k, cỡ mẫu) và tính lại cho mọi nơi. Ghi rõ vì sao khác ICRCV.
4. Giải thích chênh lệch FlatIP 7,66 ms so với 3,3 ms (máy, số luồng, batch). Giao thức đo phải giống ICRCV: 1 lượt khởi động, 7 lần đo.
3.3. Một số điểm trong hướng dẫn R1 trước đó cần hiệu chỉnh
Một số vấn đề thiết kế trong báo cáo này bắt nguồn từ gợi ý của thầy ở bản nhận xét R1 trước đó:
- Thiết kế phân nhóm truy vấn theo hubness của ảnh mục tiêu và dùng độ lệch (skewness) làm thống kê chính (R1, Mục 5.4), thầy xem lại kết quả cho thấy thiết kế này đo sai đơn vị và thiếu lực thống kê (Mục 4.2).
- Gợi ý so sánh sức mạnh dự báo "trên toàn bộ các cặp (model, dataset)" (R1, Mục 5.4), thiết kế này sẽ bị nhiễu bởi kích thước gallery (Mục 4.3).
- R1 viết chung chung "fine-tune phía truy vấn (Combiner)", trong khi SEARLE và Pic2Word không có Combiner (Mục 4.4).
- Con số 15–19× ở R1 chỉ là ước lượng cho hướng ngẫu nhiên, không phải đại lượng quyết định xếp hạng. Em đã đo được đại lượng đúng hơn (Mục 4.1), nên không cần viết theo hướng "khớp dự đoán của thầy".
3.4. Quy tắc viết báo cáo từ nay
- Viết kết luận sau khi đọc bảng, không viết trước. Mọi con số trong lời văn phải được sinh từ JSON (ví dụ một script đọc JSON và điền vào mẫu markdown). Cách này loại bỏ hoàn toàn lỗi kiểu dòng 7–8 ở Mục 3.1.
- Mỗi giả thuyết kết thúc bằng một nhãn trạng thái: Xác nhận / Ủng hộ một phần / Chưa kết luận / Bác bỏ, kèm bằng chứng quyết định (con số, kiểm định, khoảng tin cậy).
- Kết quả âm tính là kết quả. "Dữ liệu không ủng hộ giả thuyết hubness ở cấp độ mục tiêu" là một câu khoa học có giá trị; viết ngược lại thì không.
- Không dùng: "đột phá", "hoàn hảo", "đanh thép", "không thể chối cãi", "chứng minh dứt khoát", "định lý" (khi không có chứng minh toán học), "khớp dự đoán của Mentor". Dùng: "nhất quán với", "ủng hộ", "không ủng hộ", "chưa đủ bằng chứng".
- Luôn báo cáo kèm: cỡ mẫu, khoảng tin cậy (không chỉ độ lệch chuẩn), cỡ hiệu ứng, và kiểm định hai phía trừ khi có lý do đặt trước.
- Đường dẫn trong báo cáo dùng dạng tương đối (./plots/...), không dùng file:///d:/... vì người khác không mở được.
Khung chuẩn cho mỗi báo cáo module: (1) Câu hỏi; (2) Giả thuyết và dự đoán định lượng - viết trước khi chạy; (3) Thiết kế: dữ liệu, cấu hình, số truy vấn, kiểm định; (4) Kết quả: bảng và hình; (5) Kết luận có nhãn trạng thái; (6) Hạn chế; (7) Việc tiếp theo.
4. Nhận xét và hướng dẫn theo từng module
4.1. Module A.2: Nhiễu điểm số IVFPQ
Đây là module tốt nhất. Phép đo đúng, và retention IVFPQ của em (SEARLE m = 16: 20,4%; Pic2Word m = 16: 16,4%) khớp Bảng V bài ICRCV, nên số liệu đáng tin. Điều cần làm là chuyển trọng tâm từ con số toàn cục sang con số cục bộ, và giải thích được vì sao chúng khác nhau.
Điều em đã phát hiện nhưng chưa khai thác
Nhiễu trên ứng viên top-10 lớn hơn hẳn nhiễu trên cặp ngẫu nhiên (SEARLE m = 16: RMS 0,045 so với 0,016). Quan trọng hơn, phân phối trên top-10 có hình dạng khác: histogram trong hình của em có đỉnh quanh 0,035 và gần như không có giá trị sát 0. Kiểm tra định lượng: nếu nhiễu đối xứng quanh 0 thì |δ| tuân theo half-normal, với tỉ số trung bình / độ lệch chuẩn = 1,32. Số liệu của em:
SEARLE, m = 16
Trung bình |δ|
Độ lệch chuẩn |δ|
Tỉ số
Cặp ngẫu nhiên
0,0125
0,0100
1,25 — khớp half-normal
Ứng viên top-10
0,0401
0,0203
1,97 — không khớp

 
Nghĩa là nhiễu trên top-10 có độ lệch hệ thống (trung bình khác 0), không phải nhiễu đối xứng. Hiện JSON chỉ lưu giá trị tuyệt đối nên chưa thấy được dấu.
Giải thích cơ chế để em kiểm chứng
Tách sai số tái tạo e = x − x̂ thành phần song song với x và phần trực giao: e = (e·x)·x + e⊥. Khi đó:
δ = q·e = (e·x)(q·x) + q·e⊥
Với vector trên mặt cầu đơn vị có hằng đẳng thức e·x = (1 + ‖e‖² − ‖x̂‖²)/2. Nếu ‖x̂‖ ≈ 1 thì e·x ≈ ‖e‖²/2 luôn dương. Từ đó:
- Cặp ngẫu nhiên: q·x ≈ 0 nên chỉ còn q·e⊥, đối xứng quanh 0, độ lớn khoảng ‖e‖/√d. Đúng cái em đo được.
- Ứng viên top-10: q·x ≈ 0,35–0,45 (số em ghi trong báo cáo), nên có thêm độ lệch dương ≈ 0,4 × 0,428²/2 ≈ 0,037. Số em đo: trung bình |δ| = 0,040.
Nói cách khác: PQ đánh giá thấp một cách hệ thống điểm số của chính các láng giềng thật. Đây đúng là hiện tượng mà ScaNN (Guo et al., ICML 2020) xây dựng anisotropic loss để sửa, phạt thành phần sai số song song nặng hơn thành phần trực giao. Số liệu CIR của em đang tái hiện động lực của ScaNN, rất đáng đưa vào bài.
Hệ quả quan trọng: phần lệch (e·x)(q·x) gần như tỉ lệ với điểm số, nên phần lớn của nó KHÔNG làm đảo thứ hạng (nhân mọi điểm với cùng một hệ số thì thứ tự giữ nguyên). Cái làm đảo thứ hạng là chênh lệch nhiễu giữa hai ứng viên liền kề, d = δ_r − δ_(r+1). Ước tính thô từ số của em: độ dao động của ‖e‖ (độ lệch chuẩn 0,080) tạo ra dao động phần song song ≈ 0,4 × 0,428 × 0,080 ≈ 0,014; cộng phần trực giao ≈ 0,016 cho √(0,014² + 0,016²) ≈ 0,021 khớp với độ lệch chuẩn đo được trên top-10 (0,020). Nếu nhiễu của hai ứng viên độc lập thì σ_d ≈ √2 × 0,020 ≈ 0,028–0,030, tức khoảng 40 lần trung vị gap (0,00069). Kết luận "IVFPQ m ≤ 16 thất bại" vẫn vững, nhưng con số đúng để báo cáo là σ_d đo trực tiếp.
Việc cần làm
1. Lưu δ CÓ DẤU (δ = q·x − q·x̂) cho cả cặp ngẫu nhiên và top-50 chính xác. Báo cáo trung bình và độ lệch chuẩn riêng biệt.
2. Tách δ thành phần song song (e·x)(q·x) và phần trực giao q·e⊥ (Phụ lục A). Kiểm tra dự đoán: phần song song ≈ 0,037 trên top-10 của SEARLE m = 16; phần trực giao đối xứng, độ lớn ≈ 0,016.
3. Đo ‖x̂‖ và kiểm tra hằng đẳng thức e·x = (1 + ‖e‖² − ‖x̂‖²)/2.
4. Vẽ "đường cong hoán vị": với mọi cặp hạng liền kề (r, r+1) trong top-50 chính xác, trục hoành là gap g = s_r − s_(r+1), trục tung là tỉ lệ cặp bị đảo thứ tự trong điểm ADC. Chồng lên đường lý thuyết Φ((μ_d − g)/σ_d). Đọc ra g_5% gap mà dưới nó tỉ lệ đảo vượt 5%. Đây là "ngân sách" thật của họ chỉ mục nén, và hình này thay thế Bảng VII bài ICRCV tốt hơn mọi tỉ số.
5. Lặp bước 4 cho m ∈ {8, 16, 32, 64} để thấy ngân sách co lại thế nào khi tăng m. Số liệu này dùng trực tiếp cho giai đoạn C.
6. Báo cáo phân phối gap (trung vị 0,00069), không chỉ trung bình (0,00098), phân phối gap lệch phải.
Quyết định chiến lược kèm theo
Nếu σ_d ≈ 0,03 thì g_5% ≈ 1,645 × 0,03 ≈ 0,05. Khi đó Score-Gap Loss cần (điểm hạng 1 − điểm hạng 10) ≥ 9 × 0,05 = 0,45 bằng toàn bộ điểm hạng 1 (≈ 0,4–0,45). Bất khả thi. Nghĩa là với IVFPQ m ≤ 16, không thể sửa bằng cách GIÃN GAP; chỉ có thể sửa bằng cách giảm nhiễu (m lớn hơn, OPQ, anisotropic quantization, phép chiếu học được, hoặc xếp hạng lại danh sách ngắn bằng vector gốc). Cần xác nhận bằng số đo ở bước 4 trước khi thiết kế giai đoạn D, nhưng em nên chuẩn bị tinh thần: Score-Gap Loss ở dạng ban đầu có thể phải bỏ, hoặc chuyển thành trọng số trong một hàm mục tiêu giảm nhiễu như R1 Mục 6.2 đã gợi ý.
4.2. Module A.1: Hubness và HNSWFlat
Kết luận đúng của module này là: giả thuyết hubness CHƯA được xác nhận. Đây không phải thất bại, đây là một kết quả. Tính lại từ JSON:
Chỉ số
SEARLE
Pic2Word
Độ lệch hubness S_N10
2,659
2,659
Kurtosis / hub lớn nhất
13,75 / 231
11,74 / 182
Tỉ lệ anti-hub trong gallery
8,48%
10,72%
Số truy vấn: anti-hub / normal / hub
47 / 170 / 3
46 / 168 / 6
Retention@10: anti-hub so với normal
91,70 so với 94,06 (−2,36)
85,43 so với 86,67 (−1,23)
KTC 95% bootstrap của chênh lệch
[−8,35; +2,42]
[−9,07; +5,65]
Mann–Whitney p (một phía / hai phía)
0,20 / 0,41
0,54 / 0,91
Cỡ hiệu ứng Cohen d
0,15
0,06
Số truy vấn mỗi nhóm cần cho lực 80%
≈ 670
≈ 4.800

 
Phát hiện quyết định
Khoảng cách giữa hai model nằm ngay trong nhóm Normal: 94,06% so với 86,67% (chênh 7,4 điểm, p < 0,0001) còn lớn hơn khoảng cách chung (6,9 điểm). Nếu tính lại retention của Pic2Word với cơ cấu nhóm giống hệt SEARLE thì kết quả chỉ thay đổi −0,16 điểm. Tức là với cách đo hiện tại, việc ảnh mục tiêu là anti-hub giải thích gần như 0% khoảng cách SEARLE–Pic2Word. Cơ chế thật (dù là gì) tác động lên mọi truy vấn, không riêng truy vấn có mục tiêu anti-hub. Hình cột của em cũng cho thấy điều này: khoảng cách giữa hai màu xuất hiện ở cả ba nhóm.
Năm vấn đề thiết kế
1. Sai đơn vị phân tích. Retention@10 đo việc HNSW tìm lại 10 láng giềng chính xác của truy vấn không liên quan trực tiếp tới ảnh ground truth. Phân nhóm theo ảnh mục tiêu là đo lệch đối tượng. Đơn vị đúng là từng láng giềng trong top-10 chính xác.
2. Thiếu lực thống kê. 220 truy vấn, nhóm hub chỉ 3 và 6. Retention không cần ground truth, nên em dùng được cả tập test của CIRCO: tổng 1.020 truy vấn. Phân tích theo láng giềng cho khoảng 10.200 quan sát mỗi model.
3. Quy tắc gán nhóm chưa rõ. 21,4% truy vấn rơi vào nhóm anti-hub trong khi chỉ 8,5% ảnh gallery là anti-hub. Có thể do CIRCO có nhiều ground truth mỗi truy vấn và em gán "anti-hub nếu có ít nhất một ground truth là anti-hub"? Ghi rõ quy tắc.
4. Đại lượng đại diện chưa đúng. N10 của đồ thị kNN chính xác không phải bậc vào trong đồ thị HNSW. Phải đo bậc vào tầng 0 trực tiếp từ đồ thị FAISS (Phụ lục B).
5. Hình chưa chuẩn. Thanh sai số ±1 độ lệch chuẩn vượt quá 100% vô nghĩa với đại lượng bị chặn trên. Dùng khoảng tin cậy bootstrap 95%.
Việc cần làm
1. Dựng bảng dữ liệu theo láng giềng: mỗi dòng = (model, truy vấn q, láng giềng x ∈ top-10 chính xác). Cột: missed (HNSW không trả x), rank của x, N10(x), bậc vào HNSW của x, s1(q) = điểm top-1 của q, độ tương phản cục bộ c(q) = s1 − s100. Dùng cả 1.020 truy vấn.
2. Mô tả: tỉ lệ bị bỏ sót theo nhóm N10 (0; 1–4; 5–9; 10–29; ≥ 30) và theo nhóm bậc vào, có khoảng tin cậy. Đo luôn: bao nhiêu nút có bậc vào HNSW bằng 0?
3. Hồi quy logistic ba mô hình lồng nhau (Phụ lục C), sai số chuẩn cụm theo truy vấn: M0 = chỉ biến model; M1 = thêm rank, log(1+N10), log(1+bậc vào); M2 = thêm s1 và c(q).
4. Đọc kết quả bằng một câu hỏi duy nhất: hệ số của biến model giảm bao nhiêu khi thêm nhóm biến hubness (M1), và khi thêm nhóm biến truy vấn (M2)? Nhóm nào làm hệ số model giảm nhiều nhất là ứng viên cơ chế giải thích khoảng cách SEARLE–Pic2Word.
5. Can thiệp bằng chứng nhân quả: giảm hubness bằng centering bảo toàn thứ hạng (Phụ lục D), đo lại độ lệch, tỉ lệ anti-hub, bậc vào và retention ở CÙNG cấu hình. Nếu hubness giảm mà retention không tăng → bằng chứng mạnh chống lại giả thuyết. Nếu retention tăng, nhất là với Pic2Word → bằng chứng nhân quả ủng hộ.
Về centering: với mỗi truy vấn, q·(x − μ) = q·x − q·μ, mà q·μ là hằng số, nên thứ tự top-10 chính xác KHÔNG đổi — chỉ có các cạnh của đồ thị HNSW thay đổi. Vì vậy retention vẫn được tính so với top-10 chính xác gốc. Lưu ý phải dựng đồ thị bằng METRIC_INNER_PRODUCT; nếu dùng L2 thì centering không đổi gì vì khoảng cách L2 bất biến khi tịnh tiến.
4.3. Module A.5: Sức mạnh dự báo của các chỉ số hình học
Kết luận "hubness là chỉ số duy nhất dự báo được" không được số liệu ủng hộ. Thầy tính lại trên đúng 8 điểm của em:
Chỉ số
Spearman thô (p)
Riêng phần, kiểm soát log N (p)
Trong cùng bộ dữ liệu (r)
Relative Contrast
−0,143 (0,74)
+0,19 (0,69)
+0,34
LID
−0,881 (0,004)
+0,11 (0,81)
+0,11
Hubness skewness
−0,857 (0,007)
−0,22 (0,63)
−0,06
Tỉ lệ anti-hub
−0,667 (0,07)
−0,24 (0,61)
−0,44
log₁₀ N (kích thước gallery)
−0,945 (0,0004)
—
—

 
- Kích thước gallery giải thích tốt hơn mọi chỉ số hình học. Hubness và LID đều tương quan chặt với log N (ρ = 0,87 và 0,95) và với nhau (0,93). Kiểm soát log N thì không chỉ số nào còn ý nghĩa.
- Tám điểm thực chất là ba cụm theo bộ dữ liệu (CIRR, FashionIQ, CIRCO), nên bậc tự do hiệu dụng rất thấp. Tương quan đang đo sự khác nhau giữa ba bộ dữ liệu.
- Đúng ở nơi có dị thường cần giải thích, CIRCO, độ lệch hubness hai model bằng nhau (2,659) trong khi retention chênh 18 điểm (74,1% so với 56,0%). Trên FashionIQ quan hệ còn đảo chiều: SEARLE có độ lệch cao nhất (2,16) nhưng retention 78,7% cao hơn CLIP4Cir (76,4%, độ lệch 1,33).
- Tín hiệu duy nhất đáng theo dõi: tỉ lệ anti-hub có tương quan đúng chiều trong cùng bộ dữ liệu (r = −0,44). Với 8 điểm thì mới là gợi ý.
Câu kết luận có thể viết trung thực ngay bây giờ: "Ở cấp độ bộ dữ liệu, các chỉ số hình học toàn cục (RC, LID, độ lệch hubness) không dự báo được retention của HNSW sau khi kiểm soát kích thước gallery". Đây là một kết quả âm tính có giá trị, vì nó cho thấy cần đi xuống cấp truy vấn.
Việc cần làm
1. Thiết kế hai yếu tố: (a) cố định N = 2.000 cho cả 8 tổ hợp (model, dataset) bằng cách lấy mẫu con, rồi so chỉ số hình học và retention ở cùng N; (b) trong CIRCO, quét N ∈ {2K, 10K, 50K, 123K} để đo riêng tác động của N.
2. Mỗi mức lấy mẫu con lặp 3 lần với seed khác nhau để có độ dao động.
3. Chuyển phân tích chính xuống cấp truy vấn và láng giềng (Mục 4.2). Một con số toàn cục cho cả bộ dữ liệu không thể giải thích vì sao truy vấn này hỏng còn truy vấn kia không.
4. Luôn báo cáo tương quan riêng phần (kiểm soát log N) cạnh tương quan thô, và dùng cấu hình HNSW tham chiếu (Mục 3.2).
4.4. Module A.3: Sai số định tuyến IVFFlat
Kết quả "retention trùng khớp 100% với tỉ lệ bao phủ" là đúng, nhưng là đồng nhất thức. IVFFlat tính khoảng cách chính xác với mọi vector trong các cụm được quét, nên một láng giềng chính xác bị bỏ sót khi và chỉ khi nó nằm trong cụm không được quét. Điều này đúng với mọi bộ dữ liệu và mọi model, không cần thực nghiệm để chứng minh. Kết quả khớp 100% chứng minh cài đặt của em đúng và nên đưa vào bài như một câu kiểm tra trong phần phương pháp, không phải như một phát hiện.
- Sửa ba con số trong lời văn (dòng 7, Mục 3.1).
- Cột "Routing Margin" chưa có định nghĩa: giá trị giảm từ 0,0136 xuống 0,0002 nhưng người đọc không biết là gì.
- "Can thiệp phía Combiner" không áp dụng được: SEARLE và Pic2Word không có Combiner (chỉ CLIP4Cir có), và A.3 chưa đo CLIP4Cir. Núm vặn phía truy vấn của SEARLE là mạng Φ, của Pic2Word là mạng ánh xạ ảnh thành token.
Câu hỏi khoa học thật của module này là: truy vấn nào bị định tuyến sai, và vì sao Pic2Word bị nhiều hơn SEARLE ở mọi nprobe (nprobe = 1: retention 34,95% so với 46,09%)?
Việc cần làm
1. Định nghĩa "thứ hạng cụm" r(q, x): thứ hạng của tâm cụm chứa x khi xếp mọi tâm cụm theo q·μ giảm dần. x được bao phủ khi và chỉ khi r(q, x) ≤ nprobe. Biên định tuyến: m(q, x) = q·μ_c(x) − q·μ_(nprobe), với μ_(nprobe) là tâm cụm thứ nprobe. Ghi công thức này vào báo cáo.
2. Báo cáo phân phối r(q, x) của các láng giềng chính xác. Từ một phân phối này em suy ra được retention ở MỌI nprobe mà không cần chạy lại.
3. Mất cân bằng cụm: Pic2Word có kích thước cụm phân tán hơn (độ lệch chuẩn 170,9 so với 139,5; cụm lớn nhất 1.366 so với 1.175). Báo cáo imbalance factor (FAISS có sẵn) có thể liên quan tới hubness và tới tỉ lệ định tuyến sai.
4. Chạy đối chứng truy vấn ảnh ở Mục 5.
4.5. Module A.4: Quy mô gallery
Xu hướng tăng tốc rõ ràng và đúng hướng (HNSW từ 11,1× ở 10K lên 137,4× ở 500K). Nhưng trước khi tin con số này cần kiểm tra một điểm đáng ngờ.
Điểm đáng ngờ
Retention HNSW gần như phẳng từ 123K đến 500K (93,6% → 92,9% → 93,1%), trong khi distractor chiếm 51% rồi 75% gallery. Nếu distractor là ảnh thật cùng miền, retention ở tham số cố định thường tiếp tục giảm. Nếu distractor là vector ngẫu nhiên thì thí nghiệm vô giá trị: vector ngẫu nhiên 512 chiều có cosine ≈ 0 ± 0,044 với mọi thứ, không bao giờ lọt vào top-10 của truy vấn có điểm 0,35–0,45, nên gallery chỉ "to" về con số chứ không khó hơn. Báo cáo hiện chưa ghi nguồn distractor.
Các vấn đề khác: con số trong lời văn và tiêu đề không khớp bảng (dòng 8–9, Mục 3.1); tăng tốc được so ở tham số cố định chứ không ở retention khớp ở 500K cả HNSW (93,1%) lẫn IVFFlat (93,9%) đều dưới 95%, nên không cùng chuẩn chất lượng với bài ICRCV; chưa ghi model, nlist/nprobe, M/efSearch; chưa báo cáo mAP@10 theo N.
Việc cần làm (Phụ lục F)
1. Ghi rõ nguồn distractor: bộ ảnh, số lượng, bộ mã hoá (phải là bộ mã hoá ảnh của chính model đó), đã loại trùng với COCO unlabeled chưa.
2. Đo tỉ lệ distractor xuất hiện trong top-10 chính xác ở mỗi N. Nếu gần 0 thì distractor "vô hình" và thí nghiệm phải làm lại với ảnh thật.
3. Kiểm tra gần-trùng: có bao nhiêu ảnh ground truth có distractor với cosine > 0,95.
4. Báo cáo mAP@10 (theo ground truth) ở mỗi N. Thêm distractor thật thì bài toán phải khó lên.
5. Quy trình "retention khớp" như ICRCV: với mỗi N, chỉnh efSearch (HNSW) và nprobe (IVF) để đạt ≥ 95% rồi mới đo tăng tốc.
6. Báo cáo độ dốc log–log đo được thay vì gắn nhãn O(log N).
7. Chỉ khi các bước 1–6 đạt mới mở rộng lên 1M. Không cần vội.
5. Một thí nghiệm mới nên làm sớm: truy vấn CIR nằm ngoài đa tạp ảnh
Đây là gợi ý mới, chưa có trong R1. Thầy nghĩ nó có thể trở thành phát hiện trung tâm của bài, và chi phí rất thấp.
Lý do
SEARLE và Pic2Word tạo vector truy vấn bằng bộ mã hoá VĂN BẢN của CLIP (token giả cộng câu chỉnh sửa), còn vector gallery do bộ mã hoá ẢNH tạo ra. Không gian CLIP có khoảng cách giữa hai phương thức đã được ghi nhận rõ (Liang et al., "Mind the Gap", NeurIPS 2022). Chính em đã ghi nhận top-10 chỉ có điểm 0,35–0,45: truy vấn CIR nằm xa mọi ảnh trong gallery. Một truy vấn nằm xa đa tạp ảnh sẽ "nhìn" mọi ứng viên với điểm na ná nhau, và điều đó có thể gây lỗi cho cả ba họ chỉ mục cùng lúc: gap nhỏ (họ nén), tín hiệu chọn cụm yếu (họ phân hoạch), duyệt tham lam thiếu hướng (họ đồ thị).
Giả thuyết H-MG
Lỗi của cả ba họ chỉ mục nặng hơn đáng kể với truy vấn CIR so với truy vấn ảnh→ảnh trên cùng một chỉ mục, và mức chênh tăng theo khoảng cách của truy vấn tới đa tạp ảnh (đo bằng s1).
Thiết kế (Phụ lục E)
1. Chọn ngẫu nhiên 1.000 ảnh gallery không phải ground truth của truy vấn nào, loại khỏi gallery, dùng vector ảnh của chúng làm truy vấn ảnh.
2. Dựng IVFFlat, HNSWFlat, IVFPQ trên phần gallery còn lại với cấu hình tham chiếu.
3. Chạy cả truy vấn CIR và truy vấn ảnh trên cùng chỉ mục. Với mỗi loại truy vấn đo: s1, gap hạng 10/11, độ tương phản s1 − s100; IVF: phân phối thứ hạng cụm; HNSW: retention; IVFPQ: σ_d và tỉ lệ hoán vị.
4. Phân tầng theo s1 để so sánh ở mức "xa đa tạp" tương đương, nhằm tách tác động của khoảng cách khỏi tác động của phương thức.
Diễn giải: nếu H-MG đúng, đây là phát hiện đặc thù CIR, hợp nhất cả ba họ chỉ mục dưới một nguyên nhân, và chỉ thẳng tới can thiệp phía truy vấn (ví dụ dịch truy vấn về phía đa tạp ảnh). Nếu sai, em đã loại được một giải thích hiển nhiên mà phản biện chắc chắn sẽ hỏi. Cả hai kết cục đều đưa được vào bài. Biến s1 và c(q) trong hồi quy ở Mục 4.2 cũng chính là phép thử H-MG ở cấp truy vấn bên trong từng model.
6. Điều chỉnh kế hoạch giai đoạn C (baseline không huấn luyện)
Kế hoạch của em có OPQ, hạ nhiệt độ τ và QB-Norm. Thầy điều chỉnh như sau:
- Bỏ "hạ nhiệt độ τ" khỏi giai đoạn này. Ở lúc suy luận, chia mọi điểm cho τ không làm thay đổi thứ hạng của bất kỳ truy vấn nào, và FAISS không dùng τ. Nhiệt độ chỉ có tác dụng khi huấn luyện, nên thuộc giai đoạn D.
- Đặt tên giai đoạn khớp R1 để tránh nhầm: A (đo đạc) đã làm; B (quy mô) đã làm một phần, chờ kiểm định distractor; C (baseline không huấn luyện) là bước tiếp theo.
Danh sách baseline tối thiểu:
Họ chỉ mục
Baseline
Nén (IVFPQ)
PQ với m ∈ {8, 16, 32, 64, 128}; OPQ; PCA rồi PQ; ScalarQuantizer 8-bit và fp16; IVFPQ + xếp hạng lại danh sách ngắn (k′ = 100) bằng vector gốc, ghi rõ chi phí bộ nhớ của vector gốc; tuỳ chọn: thư viện ScaNN (anisotropic quantization).
Đồ thị (HNSW)
M ∈ {16, 32, 48, 64} (bài ICRCV đã đề xuất M > 32 cho Pic2Word), quét efSearch; HNSW + SQ8; centering bảo toàn thứ hạng (Phụ lục D).
Phân hoạch (IVF)
Quét nlist và nprobe; báo cáo phân phối thứ hạng cụm (4.4).
Chuẩn hoá hubness
QB-Norm hoặc DBNorm. Lưu ý: hai phương pháp này thay đổi thứ hạng chính xác, nên phải đánh giá bằng mAP/Recall theo ground truth, không chỉ retention.

 
Quy tắc báo cáo giai đoạn C: so sánh ở cùng ngân sách bộ nhớ hoặc cùng mức retention; vẽ biên Pareto (retention – độ trễ – bộ nhớ); HNSW dựng 5 lần như ICRCV; mọi cấu hình lấy từ file cấu hình chuẩn.
7. Thứ tự thực hiện và khối lượng ước tính
Bước
Nội dung
Ước lượng
Sản phẩm
P0
Sửa 13 chỗ ở Mục 3.1; viết lại kết luận A.1, A.3, A.5 theo nhãn trạng thái; viết script sinh bảng từ JSON
1–2 ngày
Báo cáo đã sửa
P1
File cấu hình chuẩn; chạy lại các số bị ảnh hưởng; thống nhất định nghĩa RC/LID
1–2 ngày
reference.yaml; JSON có metadata
P2a
A.2: nhiễu có dấu, tách thành phần, đường cong hoán vị cho m ∈ {8, 16, 32, 64}
2 ngày
Hình đường cong hoán vị; bảng g_5%
P2b
A.1: bảng theo láng giềng (1.020 truy vấn), bậc vào HNSW, hồi quy M0–M2, can thiệp centering
3–4 ngày
Bảng hệ số; kết luận có nhãn
P2c
A.5: thiết kế N cố định và quét N
2 ngày
Bảng tương quan thô và riêng phần
—
Gửi thầy kết quả P0–P2, trao đổi trước khi đi tiếp
 
 
P3a
A.4: kiểm định distractor; retention khớp; mAP theo N
2 ngày
Báo cáo kiểm định
P3b
Mục 5: đối chứng truy vấn ảnh (H-MG)
2–3 ngày
Bảng so sánh CIR với ảnh
P4
Giai đoạn C (Mục 6)
khoảng 1 tuần
Biên Pareto

 
Tổng cộng khoảng 3–4 tuần làm việc. Nếu phần nào khó (đặc biệt hồi quy logistic với sai số chuẩn cụm, hoặc đọc đồ thị HNSW trong FAISS), em nhắn thầy.
8. Cần nộp ở báo cáo kế tiếp
- Bản sửa của 5 báo cáo module và bản tổng kết, kèm bảng đối chiếu: mỗi dòng ở Mục 3.1 đã sửa thế nào.
- File cấu hình chuẩn và JSON mới có đủ metadata.
- A.2: số liệu nhiễu có dấu; bảng phần song song và trực giao; đường cong hoán vị và g_5% theo m.
- A.1: bảng tỉ lệ bỏ sót theo nhóm N10 và bậc vào; bảng hệ số M0–M2; kết quả can thiệp centering; kết luận có nhãn.
- A.5: bảng tương quan ở N cố định và kết quả quét N.
- Nếu đã làm: kiểm định distractor và kết quả H-MG.
- Một trang tóm tắt cuối: mỗi giả thuyết một dòng, nhãn trạng thái, bằng chứng quyết định.
9. Tài liệu đọc thêm
1. Guo et al., "Accelerating Large-Scale Inference with Anisotropic Vector Quantization", ICML 2020 - đọc lại phần score-aware loss sau khi làm xong 4.1.
2. Liang et al., "Mind the Gap: Understanding the Modality Gap in Multi-modal Contrastive Representation Learning", NeurIPS 2022 - nền tảng cho Mục 5.
3. Suzuki et al., "Centering Similarity Measures to Reduce Hubs", EMNLP 2013; Hara et al., "Localized Centering: Reducing Hubness in Large-Sample Data", AAAI 2015 - nền tảng cho can thiệp centering.
4. "Balance Act: Mitigating Hubness in Cross-Modal Retrieval with Query and Gallery Banks" (arXiv 2310.11612) - DBNorm, biến thể của QB-Norm.
5. Radovanović et al., "Hubs in Space", JMLR 2010 - đọc lại phần định nghĩa N_k và anti-hub.
6. Mã nguồn FAISS: faiss/impl/HNSW.h (cấu trúc neighbors, offsets, cum_nneighbor_per_level) - phục vụ Phụ lục B.
 
Em đang đi đúng hướng, và các thí nghiệm em đã chạy đều dùng lại được. Điều cần thay đổi là cách em đọc và viết kết quả: để số liệu nói trước, rồi mới viết kết luận.
PHỤ LỤC — MÃ THAM KHẢO
Các đoạn mã dưới đây là khung tham khảo bằng Python/FAISS/NumPy. Em cần kiểm tra lại với phiên bản thư viện đang dùng và với cách em lưu dữ liệu. Biến xb là vector gallery (đã chuẩn hoá L2, float32), xq là vector truy vấn.
Phụ lục A — Nhiễu có dấu, tách thành phần, đường cong hoán vị (IVFPQ)
import numpy as np, faiss
ivfpq.make_direct_map()                   # cho phép reconstruct với IVF
xh = ivfpq.reconstruct_n(0, xb.shape[0])  # x^ (giải nén, gồm tâm IVF)
e  = xb - xh                              # sai số tái tạo
a  = (e * xb).sum(1)                      # a_i = e_i . x_i (song song)
nx = np.linalg.norm(xh, axis=1)           # ||x^||, kiểm tra hằng đẳng thức
flat = faiss.IndexFlatIP(xb.shape[1]); flat.add(xb)
S, I = flat.search(xq, 50)                # top-50 chính xác
rows = []
for qi in range(len(xq)):
    ids, s = I[qi], S[qi]
    shat  = xh[ids] @ xq[qi]              # điểm ADC = q . x^
    delta = s - shat                      # nhiễu CÓ DẤU
    par   = a[ids] * s                    # (e.x)(q.x)
    orth  = delta - par                   # q . e_perp
    for r in range(49):                   # cặp hạng liền kề (r, r+1)
        rows.append(dict(qid=qi, rank=r + 1,
                         gap=s[r] - s[r + 1],
                         d=delta[r] - delta[r + 1],
                         swapped=bool(shat[r] < shat[r + 1]),
                         delta=delta[r], par=par[r], orth=orth[r]))
# Đường cong: chia gap theo bin log, tính tỉ lệ swapped mỗi bin,
# so với scipy.stats.norm.cdf((mean(d) - gap) / std(d))

Phụ lục B — Bậc vào tầng 0 của đồ thị HNSW
h   = hnsw_index.hnsw
nb  = faiss.vector_to_array(h.neighbors)
off = faiss.vector_to_array(h.offsets)
cum = faiss.vector_to_array(h.cum_nneighbor_per_level)
indeg = np.zeros(hnsw_index.ntotal, dtype=np.int64)
for i in range(hnsw_index.ntotal):
    v = nb[off[i] + cum[0] : off[i] + cum[1]]    # láng giềng tầng 0 của nút i
    v = v[v >= 0]                                # bỏ ô trống (-1)
    np.add.at(indeg, v, 1)                       # cạnh i -> v
print("so nut co bac vao = 0:", (indeg == 0).sum())

Phụ lục C — Hồi quy logistic theo láng giềng
import statsmodels.formula.api as smf
# df: mỗi dòng = (model, qid, x) với x thuộc top-10 chính xác của truy vấn qid
# cột: missed (0/1), model, qid, rank (1..10), log_nk = log1p(N10(x)),
#      log_indeg = log1p(indeg(x)), s1, contrast = s1 - s100
kw = dict(cov_type="cluster", cov_kwds={"groups": df["qid"]})
m0 = smf.logit("missed ~ C(model)", df).fit(**kw)
m1 = smf.logit("missed ~ C(model) + rank + log_nk + log_indeg",
               df).fit(**kw)
m2 = smf.logit("missed ~ C(model) + rank + log_nk + log_indeg"
               " + s1 + contrast", df).fit(**kw)
for m in (m0, m1, m2):
    print(m.params.filter(like="model"), m.bse.filter(like="model"))
# Câu hỏi: hệ số của biến model giảm bao nhiêu từ m0 -> m1 -> m2 ?

Phụ lục D — Centering bảo toàn thứ hạng cho HNSW
mu = xb.mean(axis=0, keepdims=True)
xc = (xb - mu).astype("float32")                 # KHÔNG chuẩn hoá lại
idx = faiss.IndexHNSWFlat(xb.shape[1], M, faiss.METRIC_INNER_PRODUCT)
idx.hnsw.efConstruction = EF_CONSTRUCTION        # giữ như cấu hình chuẩn
idx.add(xc)
idx.hnsw.efSearch = EF_SEARCH
_, I_c = idx.search(xq, 10)
# q.(x - mu) = q.x - q.mu ; q.mu là hằng số với mỗi truy vấn
# => top-10 chính xác không đổi; tính retention của I_c so với
#    top-10 chính xác GỐC
# Đo thêm N10 (bằng tích vô hướng trên xc) và bậc vào; so trước/sau centering

Phụ lục E — Đối chứng truy vấn ảnh (giả thuyết H-MG)
rng   = np.random.default_rng(42)
nongt = np.setdiff1d(np.arange(len(xb)), all_gt_ids)   # ảnh không phải GT
hold  = rng.choice(nongt, 1000, replace=False)
keep  = np.setdiff1d(np.arange(len(xb)), hold)
xb_ctrl, xq_img = xb[keep], xb[hold]   # gallery còn lại / truy vấn ảnh
# Dựng IVFFlat, HNSWFlat, IVFPQ trên xb_ctrl (cấu hình chuẩn).
# Chạy CẢ xq_img và xq_cir trên cùng chỉ mục; với mỗi loại truy vấn đo:
#   s1, gap hạng 10/11, s1 - s100, thứ hạng cụm IVF, retention HNSW,
#   sigma_d và tỉ lệ hoán vị của IVFPQ. Phân tầng kết quả theo s1.

Phụ lục F — Kiểm định distractor
# is_distr: mảng bool độ dài N, True nếu là distractor
S, I = flat_full.search(xq, 10)
frac = is_distr[I].mean()     # tỉ lệ distractor trong top-10 chính xác
gt  = xb_full[all_gt_ids]
fi  = faiss.IndexFlatIP(xb_full.shape[1]); fi.add(xb_full[is_distr])
smax, _ = fi.search(gt, 1)
n_dup = int((smax[:, 0] > 0.95).sum())           # GT có distractor gần trùng
# Báo cáo frac, n_dup và mAP@10 theo GT ở từng N

 

