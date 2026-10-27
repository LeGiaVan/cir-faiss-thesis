# Kế hoạch thực hiện theo feedback Mentor R3

**Mục tiêu:** giải quyết theo thứ tự các câu hỏi quyết định trong feedback R3, tạo kết quả có thể kiểm tra lại từ dữ liệu/mã nguồn, và chỉ mở rộng phạm vi khi các cổng trước đạt yêu cầu.

**Nguyên tắc thực hiện**

- Trước mỗi thí nghiệm, ghi trước giả thuyết, đại lượng chính, cách tính CI và quy tắc quyết định. Không sửa dự đoán sau khi xem kết quả.
- Mọi bảng/hình cuối cùng phải truy xuất được về JSON, manifest, cấu hình và commit tạo ra chúng. Lưu riêng kết quả từng seed; không chép số thủ công.
- Dùng exact search làm ground truth, giữ nguyên định nghĩa metric và tập query khi so sánh các phương án.
- Báo cáo kết quả âm tính và không kết luận nhân quả chỉ từ hệ số hồi quy hay p-value.
- Kế hoạch này chỉ mô tả công việc; chưa sửa script, dữ liệu hoặc chạy thí nghiệm.

## Trạng thái Chặng 0 — 2026-10-27

**Đã hoàn thành phần kiểm kê và preregistration:** cấu hình reference, environment, commit nền, trạng thái working tree, hash của config/script/embeddings/query caches/annotations/results hiện có, cùng dự đoán và quy tắc phân tích đã được lưu trong [`stage0_manifest.json`](./stage0_manifest.json) và [`stage0_preregistration.md`](./stage0_preregistration.md).

**Chặng 0 hoàn tất có giới hạn provenance:** repository đang dirty; nhiều thư mục nguồn/config Phase 2 là untracked, và submodule extractor cũng có thay đổi. Không tạo commit hay dọn workspace vì sẽ đụng tới các thay đổi sẵn có. Hash theo file khóa snapshot đã kiểm tra nhưng không thay thế clean commit. Ngoài ra, 800 test feature rows chưa có ID nguồn từng hàng; phép ghép hiện tại dựa trên thứ tự annotation/extraction. Phải xác minh lại ID này trước khi chốt A.1/GEE theo query.

Không có script, dữ liệu thực nghiệm hoặc kết quả R2 nào được sửa/chạy trong Chặng 0. C1–C3 có thể được chuẩn bị từ snapshot đã hash; trước khi gọi lần chạy confirmatory, cần xác nhận cách cô lập/ghi nhận dirty-tree và giữ đúng snapshot. Việc xác minh test row IDs là cổng bắt buộc trước khi diễn giải A.1 theo cụm query.

## Lộ trình tổng quan và các cổng quyết định

| Chặng | Công việc | Ước lượng theo feedback | Đầu ra / cổng |
|---|---|---:|---|
| 0 | Khóa provenance, cấu hình và dự đoán trước chạy | 0,5 ngày | Manifest và kế hoạch phân tích được ghi lại |
| 1 | C1–C3: centering ở cùng chi phí/mật độ và đối chứng L2 | 2 ngày | Đường retention–ndis, so sánh số cạnh, kiểm tra âm tính |
| 2 | C4–C5: cơ chế và nhóm query được lợi | 1–2 ngày | Bảng MCS/N10/in-degree và lợi ích theo phân vị `s1` |
| **Cổng Mentor 1** | Gửi kết quả Chặng 1–2 để nhận xét | — | Chưa chuyển sang công việc mở rộng nếu chưa chốt cách đọc kết quả |
| 3 | Sửa A.1: N10, GEE, phân rã xác suất, phụ thuộc theo ảnh, ID test | 2 ngày | Bộ kết quả và report A.1 mới |
| 4 | H-MG: đối chứng CIR query với image query | 2–3 ngày | Bảng MMD, `s1`/`s100`, lỗi ANN theo loại query |
| 5 | Đọc Herman và Bao, định vị đóng góp | 1 ngày, làm xen kẽ | Hai ghi chú nửa trang và bảng công trình gần nhất cập nhật |
| **Cổng Mentor 2** | Gửi A.1/H-MG và cập nhật novelty | — | Chốt phạm vi P2a và C6 |
| 6 | P2a: nhiễu PQ có dấu và đường cong hoán vị | 2 ngày | Đường cong perturbation/swap và CI |
| 7 | C6: tổng quát hóa centering | 2–3 ngày | Bảng nhiều cấu hình/dataset, chỉ thực hiện nếu C1 ủng hộ hiệu ứng |
| Tạm hoãn | P2c: N cố định/quét N | Chưa xếp lịch | Không làm trong vòng R3 hiện tại |

Thời lượng là ước lượng từ feedback, chưa gồm thời gian chờ chạy dài hoặc sửa lỗi dữ liệu. Chặng 5 chạy song song với các chặng 1–4, nhưng phải hoàn tất trước khi chốt tuyên bố tính mới.

## Chặng 0 — Khóa dữ liệu, provenance và dự đoán

### Việc làm

1. Tạo bản ghi run mới: commit sạch, `git_dirty = False`, phiên bản FAISS (feedback yêu cầu kiểm tra 1.15.1), CPU/thread count, config hash, đường dẫn và SHA256 của embeddings, annotations, query features, gallery features và các kết quả đầu vào.
2. Lưu cấu hình dùng chung cho tất cả thí nghiệm: hai backbone, gallery/query profile, exact metric, `M`, `efConstruction`, danh sách `efSearch`, seed, số query, và cách tính ground truth.
3. Khóa cách ghép query ID giữa SEARLE/Pic2Word và val/test. Không dùng lại ID tái dựng theo vị trí nếu có thể trích xuất lại query features kèm ID nguồn.
4. Viết trước dự đoán cho C1–C5 và H-MG, gồm hướng hiệu ứng, đại lượng đánh giá chính, bootstrap/CI, và trường hợp nào được gọi là kết quả dương/âm.

### Điều kiện qua chặng

- Tất cả query có ID ổn định; thứ tự annotation và ground truth được xác minh.
- Có thể chạy lại một smoke run nhỏ và truy xuất số liệu về đúng config/data hash.
- Dự đoán và quy tắc quyết định đã được lưu trước khi chạy đủ 5 seed.

## Chặng 1 — Kiểm tra centering có lợi ở cùng chi phí không (C1–C3)

### C1. So retention ở cùng số phép tính khoảng cách

**Câu hỏi:** centering có tăng retention khi ngân sách tìm kiếm thực tế tương đương, hay chỉ tăng retention vì đồ thị centering dày hơn/tốn nhiều phép tính hơn?

**Thiết kế:** với mỗi backbone, dựng đồ thị cho 5 seed ở cùng `M=32`, `efConstruction=200`; so ba trạng thái:

1. Gallery gốc, metric inner product.
2. Gallery đã trừ mean, metric inner product, không chuẩn hóa lại.
3. Gallery đã trừ mean, metric L2 (đối chứng âm; chi tiết kiểm tra ở C3).

Ở nhánh centered IP, dùng `g_center = g − μ` và giữ query IP như pipeline reference; khi đó mỗi query trừ cùng hằng số `q·μ` khỏi mọi điểm gallery nên exact ranking được bảo toàn. Ở nhánh L2 đối chứng, phải center cả hai phía như C3. Không dùng chung quy tắc biến đổi query cho hai metric.

Quét `efSearch ∈ {32, 48, 64, 96, 128, 160, 192, 256, 384}`. Ở mỗi điểm, lưu retention@10, `ndis` trung bình mỗi query từ FAISS HNSW stats, và latency. Dùng retention theo `ndis` làm kết quả chính; latency là kết quả phụ vì phụ thuộc máy và overhead Python. So sánh hai đường tại vùng `ndis` chung bằng nội suy, không ngoại suy ngoài vùng đo.

**Độ bất định:** giữ cặp seed và query khi bootstrap; báo CI cho đường và chênh lệch retention tại các mức `ndis` chung. Hiển thị từng seed bên cạnh trung bình để không che biến thiên giữa các lần dựng.

**Quy tắc diễn giải đã định trước:**

- Centering IP nằm cao hơn đồ thị gốc tại cùng `ndis`, với CI của chênh lệch hỗ trợ mức tăng: có bằng chứng centering cải thiện recall–compute frontier trong cấu hình này.
- Hai đường trùng/CI chênh lệch chứa 0: chưa có bằng chứng centering cải thiện ở cùng chi phí; mức tăng ở `efSearch` cố định có thể do tốn thêm công tìm kiếm.
- Không dùng tiêu chí “đường trông cao hơn” nếu chưa xét CI và vùng `ndis` chồng lấp.

**Đầu ra:** JSON theo seed; hình retention–`ndis` cho từng backbone; bảng retention/ndis/latency; bảng chênh lệch tại các điểm ngân sách chung.

### C2. So sánh ở cùng mật độ đồ thị

**Câu hỏi:** centering có lợi hơn cách đơn giản là tăng `M` trên gallery gốc?

**Thiết kế:** dựng gallery gốc với `M ∈ {32, 40, 48, 64}`, giữ `efConstruction=200`, và so với gallery centering IP tại `M=32`. Trước hết báo số cạnh thực tế mỗi seed; sau đó chọn/ghép mức `M` có số cạnh gần mức centering (Pic2Word tham chiếu khoảng 3,12 triệu cạnh trong feedback). So sánh retention tại cùng số cạnh và, nếu có vùng chung, tại cùng `ndis`.

**Đầu ra:** bảng `M`, số cạnh, retention và `ndis` theo backbone/seed; kết luận centering có lợi riêng hay chỉ tạo hiệu ứng tương đương tăng mật độ.

### C3. Đối chứng âm với L2

**Mục đích:** kiểm tra hiệu ứng có đặc thù với inner product trên gallery đã center hay không.

**Điều kiện toán học bắt buộc:** khoảng cách L2 bất biến khi tịnh tiến **cả query lẫn gallery** cùng một vector: `||q−μ − (x−μ)||₂ = ||q−x||₂`. Vì vậy, ở nhánh L2 phải trừ cùng `μ` khỏi cả hai phía. Nếu chỉ center gallery mà giữ query gốc, đây không còn là đối chứng bất biến và không kiểm tra được tuyên bố của feedback.

**Kiểm tra:** so phân phối khoảng cách/neighbor exact và retention với L2 gốc; kiểm tra thứ hạng exact theo ID. Ghi sai số số học và khác biệt giữa seed. Nếu FAISS HNSW có khác biệt nhỏ do floating point/thứ tự thêm nút, báo rõ mức đó thay vì gọi là đồng nhất tuyệt đối.

**Đầu ra:** bảng kiểm tra invariance theo model/seed; nếu L2 không tương đương, dừng và sửa implementation trước khi diễn giải C1.

### Cổng Mentor 1

Sau C1–C3, cộng thêm kết quả C4–C5 ở chặng kế tiếp, gửi Mentor đúng các sản phẩm được nêu tại Mục 7 feedback: hình retention–`ndis` cho ba trạng thái, bảng cùng số cạnh, bảng MCS/N10 gallery và mức tăng theo `s1`. Không bắt đầu mở rộng C6 trước khi giải thích được tăng retention có tồn tại ở cùng chi phí hay không.

## Chặng 2 — Cơ chế centering và query nào được lợi (C4–C5)

### C4. Đo hình học gallery và cơ chế qua hubness/đồ thị

1. Với gallery gốc đã L2-normalize, tính mean vector `μ`, norm `||μ||`, và MCS theo công thức feedback. Sau centering không chuẩn hóa lại vector; vì thế không áp dụng công thức MCS giả định mọi vector có norm 1 một cách máy móc. Nếu báo MCS sau centering, tính trực tiếp cosine trung bình giữa các cặp ảnh khác nhau và ghi rõ định nghĩa/chuẩn hóa; đồng thời vẫn báo `||μ_center||` để xác nhận mean gần 0.
2. Tính **N10 phía gallery**: dùng từng ảnh gallery làm query đối với gallery; tìm exact top-10 và loại chính ảnh đó bằng ID (không loại bằng điều kiện điểm số). Làm riêng cho gallery gốc và gallery centered theo định nghĩa phù hợp với phép biến đổi đang xét.
3. Phân biệt rõ `N10_gallery` với `N10_query`. Với dữ liệu query-level, tạo `N10_loo = N10_query − 1` để loại lần xuất hiện của chính query đang xét.
4. Tính phân phối in-degree của HNSW trước/sau; với exact neighbor, báo phân phối bậc vào và miss rate theo nhóm bậc vào. Chọn bins trước khi xem kết quả hoặc dùng bins có cỡ mẫu đủ, đồng thời ghi số ảnh mỗi nhóm.
5. Thực hiện phân rã xác suất chênh lệch miss giữa hai model theo công thức/phụ lục C của feedback, rồi lặp theo hai thứ tự đưa nhóm biến vào: bậc vào trước rồi query features, và ngược lại. Bootstrap theo query; ghi rõ đây là decomposition mô tả, phụ thuộc thứ tự/tham số hóa, không phải causal mediation.

**Câu hỏi cơ chế phải trả lời:** centering đổi phân phối bậc vào của các exact neighbor hay làm giảm miss ngay trong cùng nhóm bậc vào? Có thay đổi `N10_gallery`/MCS phù hợp với cơ chế được đề xuất không?

### C5. Truy vấn nào nhận được lợi ích từ centering?

Từ `centering_per_query.parquet`, ghép theo `(model, query_id)`, tính gain = retention sau − trước, trung bình cặp theo 5 seed. Chia `s1` thành 5 phân vị riêng trong từng backbone; báo trung bình gain, số query và bootstrap CI cho từng bin. Có thể báo thêm `s100` để diễn giải tương đồng chung, nhưng không đổi đại lượng chính sau khi xem kết quả.

**Đầu ra C4–C5:** bảng `||μ||`, MCS, N10 gallery và tỉ lệ N10=0; bảng/hình phân phối in-degree; phân rã miss-rate; gain retention theo quintile `s1` với CI.

## Chặng 3 — Làm lại A.1: N10, hồi quy và độ nhạy

### 3.1. Sửa định nghĩa và mô tả hubness

- Không gọi tỷ lệ `N10_query=0` là tỷ lệ anti-hub gallery; với số query hiện tại, nó có sàn do chỉ có 10.200 vị trí top-10.
- Báo số ảnh khác nhau trong hợp top-10 và tỷ lệ phủ query-side như thống kê mô tả.
- Tính và đặt tên tách biệt `N10_gallery`, `N10_query`, và `N10_loo`; ghi đơn vị, tập query/gallery, k và cách loại self.
- Thay ngưỡng cố định tạo nhóm quá nhỏ bằng phân vị/các bin có số ảnh đủ; công bố số ảnh, không chỉ số dòng neighbor.

### 3.2. Viết lại hồi quy và phân rã trên thang xác suất

- Dùng `s1` và `s100` thay cho cặp `s1` và `c_contrast`, vì `c_contrast = s1 − s100` chứa lại `s1` và làm hệ số khó đọc. Giữ M0–M2 để so sánh, nhưng M2 chính dùng dạng đã tham số hóa lại.
- Cập nhật mô hình với `N10_gallery`, `N10_loo`, in-degree, rank, `s1`, `s100` và model. Báo hệ số/CI, nhưng trọng tâm diễn giải là dự đoán miss probability và phân rã xác suất.
- Phân rã chênh lệch dùng mô hình riêng theo model theo phụ lục C. Báo phần do khác phân phối đặc trưng và phần do khác hệ số; lặp cả hai chiều chuẩn hóa (SEARLE coefficients trên đặc trưng Pic2Word và ngược lại). Nếu phân rã theo nhóm biến, báo cả hai thứ tự thêm biến.
- Bootstrap theo query để lấy CI; không gọi tỷ lệ phân rã là tác động nhân quả.

### 3.3. Khác biệt backbone và tương tác

- Báo phân vị 5/25/50/75/95 của `s1` và `s100` riêng từng model, cùng vùng chồng lấp.
- Khớp pooled model trong vùng chồng lấp để tránh so sánh bằng ngoại suy giữa các backbone.
- Khớp riêng từng backbone với similarity chuẩn hóa bên trong model; thêm model×predictor để kiểm tra độ dốc khác nhau. Báo cách chuẩn hóa và đơn vị hệ số.
- Không hiểu `s1 = x` là cùng mức hình học ở hai backbone nếu phân phối/vùng hỗ trợ không xác nhận điều đó.

### 3.4. Phụ thuộc quan sát và provenance

- Chạy GEE với cụm `query_id` như hiện tại, sau đó chạy độ nhạy với cụm `neighbor_id` (ảnh). So hệ số, robust SE, CI và kết luận; lưu ý mỗi cách gom cụm bảo vệ trước một dạng phụ thuộc khác nhau.
- Trích lại 800 query test cùng ID nguồn, xác minh ghép CIR/SEARLE/Pic2Word và exact GT. Tạo manifest có ID thực thay cho tái dựng chỉ từ thứ tự annotation.
- Tạo kết quả cuối từ commit sạch; ghi commit/hash trong mọi JSON. Đối chiếu mọi số trong report với JSON cùng run.

### 3.5. Giả thuyết và report

Gắn trạng thái riêng cho H1a (in-degree thấp), H1b (N10 gallery), H1c (N10_loo), H2 (chênh lệch model và biến đồ thị/query). Dùng nhãn “ủng hộ một phần/chưa kiểm định/chưa kết luận/bác bỏ” theo kết quả, không ép các giả thuyết hội tụ về một kết luận. Chuyển phần giải thích dài của GEE sang ghi chú; thân report giữ câu hỏi, thiết kế, bảng/hình, kết luận, hạn chế và bước tiếp theo.

## Chặng 4 — H-MG: đối chứng query CIR với query ảnh

**Câu hỏi:** ở cùng mức gần gallery, query CIR có gây lỗi ANN nhiều hơn truy vấn ảnh→ảnh không?

### Thiết kế

1. Với từng backbone, lấy 1.000 ảnh gallery không phải ground truth của bất kỳ query CIR nào; loại toàn bộ 1.000 ảnh này khỏi gallery và không dùng chúng làm candidate/ground truth. Ghi seed lấy mẫu và kiểm tra không rò rỉ.
2. Dùng vector ảnh của các ảnh đã loại làm image queries. Chạy CIR queries và image queries trên đúng cùng gallery rút gọn, cùng chỉ mục dựng sẵn và cùng tham số trong từng so sánh.
3. Dựng exact ground truth riêng cho từng query type trên gallery rút gọn. Bảo đảm image query không tự khớp ảnh nguồn vì ảnh nguồn đã bị loại.
4. Đo `s1`, `s100`, gap/contrast và chỉ số lỗi của từng họ chỉ mục. Với HNSW báo retention; với IVF/IVFPQ báo chỉ số phù hợp (recall/retention so với exact, candidate coverage hoặc score/rank perturbation) mà không trộn các đại lượng khác định nghĩa.
5. Đo MMD² giữa query và gallery theo từng model, RBF kernel, bandwidth median heuristic; lấy 5.000 vector gallery theo quy trình cố định. Báo cách lấy mẫu/ước lượng và CI. Không so trực tiếp trị số MMD thô giữa backbone nếu kernel scale khác nhau.
6. Chia theo quintile `s1` trong từng model để so CIR và image queries ở mức tương đồng gần nhất tương đương. Báo số query và CI bootstrap theo query cho từng nhóm.

### Dự đoán cần đăng ký trước

Theo feedback: (a) MMD của CIR query cao hơn image query; (b) image queries có lỗi thấp hơn; (c) trong mỗi model, các query có `s1` thấp hơn có lỗi cao hơn. Ghi rõ dự đoán nào là chính và cách xử lý khi chỉ một phần được ủng hộ.

### Diễn giải

- CIR lỗi cao hơn image query ở tầng `s1` tương đương: ủng hộ có khác biệt liên quan loại query/modality ngoài mức gần gallery đo bằng `s1`.
- Chênh lệch biến mất sau phân tầng `s1`: kết quả phù hợp hơn với giải thích khoảng cách tới gallery; không kết luận riêng modality gây lỗi.
- MMD không đồng biến với lỗi: báo kết quả âm tính; không dùng MMD như bằng chứng thay thế cho recall.

**Đầu ra:** manifest query ảnh và gallery rút gọn; MMD²; bảng/hình error theo loại query và `s1`; CI; report H-MG nêu hạn chế của cỡ mẫu/đại lượng.

## Chặng 5 — Đọc hai công trình và định vị đóng góp (chạy xen kẽ)

### Herman (2026), arXiv:2609.00364

Đọc toàn văn và ghi nửa trang: câu hỏi, đại lượng dự báo/biến đổi, họ chỉ mục, giả định, kết quả, giới hạn, phần trùng lặp và phần CIR còn khác. Kiểm tra bản/version hiện hành và không mô tả preprint như bài đã qua phản biện nếu chưa xác minh trạng thái. Cập nhật bảng “công trình gần nhất”; đánh giá lại mọi tuyên bố dự báo recall từ embedding stats, score margin, centering/MCS và novelty của đề tài.

### Bao et al. (Findings of EMNLP 2025)

Đọc toàn văn; ghi nửa trang về OOD query/base mismatch, MMD, các ANN family, phương pháp can thiệp và phạm vi dữ liệu. Tách rõ kết quả họ đo trên text retrieval khỏi giả thuyết mở rộng sang CIR. Định vị H-MG là kiểm định cho query đa phương thức, không tuyên bố đã được Bao et al. chứng minh.

**Sản phẩm:** hai ghi chú nửa trang; bảng so sánh (vấn đề, dữ liệu, thống kê, chỉ mục, can thiệp, điểm trùng, khoảng trống); cập nhật Related Work và câu novelty sau khi có kết quả H-MG.

## Chặng 6 — P2a: nhiễu PQ có dấu (sau centering và H-MG)

1. Xác nhận data/query manifest, ground truth và mã nguồn sạch.
2. Chạy phép đo perturbation có dấu trên random pairs và exact top-50 theo feedback R2; giữ query ID để bootstrap theo cụm.
3. Quét `m ∈ {8, 16, 32, 64}` và mọi model được đăng ký; lưu vector gốc/tái tạo cần thiết, norm, phần song song/trực giao và sai số.
4. Tính chênh nhiễu của cặp kề nhau, sự kiện đảo thứ tự và đường cong swap/recall; không ép phân phối khớp Gaussian nếu số liệu không hỗ trợ.
5. Báo CI, cỡ mẫu và `g_5%` thực nghiệm/dự báo; kết luận Score-Gap Loss chỉ sau khi đối chiếu tính khả thi và công trình Herman.

**Điều kiện bắt đầu:** C1–C3 đã được diễn giải và đã hoàn thành H-MG theo thứ tự Mentor yêu cầu. Nếu kết quả centering/H-MG làm thay đổi câu hỏi PQ, cập nhật kế hoạch trước khi chạy.

## Chặng 7 — C6: tổng quát hóa centering (có điều kiện)

Chỉ triển khai nếu C1 cho thấy hiệu ứng ở cùng `ndis` đáng để kiểm tra thêm, hoặc Mentor yêu cầu kiểm tra độ khái quát. Ưu tiên theo feedback:

1. **Stress config:** `M=16`, `efSearch=32`, kiểm tra SEARLE đang gần trần ở reference nhưng có thể còn khoảng cải thiện ở stress.
2. **Dataset khác:** CIRR, FashionIQ, CLIP4Cir; khóa đúng ground truth, gallery và query profile cho từng bộ.
3. **Gallery 500K:** chỉ sau khi hoàn tất kiểm định provenance/dedup/distractor của P3a; không mở rộng quy mô trước điều kiện này.
4. **Chất lượng đầu ra:** mAP@10 theo ground truth trên 220 val queries trước/sau centering, ngoài retention. Giữ exact ranking/metric rõ ràng; không suy ra mAP tăng chỉ từ retention.

**Đầu ra:** bảng recall/retention, latency, ndis, memory/cạnh và mAP theo dataset/config; tối thiểu 5 lần dựng HNSW; CI và giới hạn tổng quát hóa.

## Việc tạm hoãn và lý do

- **P2c (N cố định/quét N):** tạm hoãn theo feedback; không đưa vào lịch hiện tại.
- **C6:** có điều kiện, không ưu tiên hơn kiểm định công bằng centering/A.1/H-MG.
- **Tuyên bố “centering cải thiện HNSW”:** chỉ dùng nếu có lợi ở cùng `ndis` (và báo rõ miền ngân sách); nếu chỉ có lợi ở cùng `efSearch`, mô tả là trade-off recall–chi phí.
- **Tuyên bố nhân quả từ GEE/M2:** không dùng nếu chưa có thiết kế can thiệp phù hợp.

## Bảng sản phẩm cần gửi Mentor

### Đợt 1 — sau C1–C5

- Hình retention theo `ndis`: gốc IP, centered IP, centered L2; 5 seed × 2 model.
- Bảng cùng số cạnh (C2).
- Bảng `||μ||`, MCS, N10 gallery và tỷ lệ N10=0 trước/sau centering.
- Bảng/hình gain retention theo quintile `s1`, kèm CI.
- Một trang tóm tắt: dự đoán đã đăng ký, kết quả, nhãn trạng thái, quyết định C1.

### Đợt 2 — sau A.1 và H-MG

- Report A.1 mới với định nghĩa N10 tách biệt, hồi quy đã tham số hóa lại, phân rã xác suất, độ nhạy query/image cluster và provenance test IDs.
- Bảng so CIR/image query theo `s1`, MMD² và lỗi chỉ mục, kèm CI.
- Hai ghi chú literature và bảng định vị novelty.
- Danh sách câu hỏi cần Mentor chốt trước khi bắt đầu P2a/C6.

## Danh sách kiểm tra trước khi gọi một chặng là hoàn tất

- [ ] Dự đoán, metric chính, cấu hình, seed và cách tính CI đã lưu trước khi xem kết quả.
- [ ] Mỗi hàng trong bảng truy ngược được tới JSON/run ID; không có số dán tay không kiểm chứng.
- [ ] Query IDs, ground truth, self-exclusion và gallery loại trừ đã được kiểm tra.
- [ ] So sánh được ghép cặp ở cùng query/seed/ngân sách khi thiết kế yêu cầu.
- [ ] Kết quả âm tính, CI rộng, thiếu chồng lấp và lệch thang đo đều được ghi rõ.
- [ ] Report phân biệt association, prediction và causal claim.
- [ ] Bản cuối chạy từ commit sạch, metadata đầy đủ, report số liệu khớp JSON.

## Nguồn

- Feedback chính: [`mentor_feedback_R3.md`](./mentor_feedback_R3.md)
- Herman, *Closed Forms and Synthetic Twins: Predicting Approximate Nearest Neighbor Recall from Embedding Statistics*, [arXiv:2609.00364](https://arxiv.org/abs/2609.00364).
- Bao et al., *Alleviating Performance Degradation Caused by Out-of-Distribution Issues in Embedding-Based Retrieval*, [Findings of EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.340/).
