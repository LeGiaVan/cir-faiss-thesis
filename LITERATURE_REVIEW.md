# Tổng hợp Nghiên cứu Cơ sở (Literature Review)

Tài liệu này tóm tắt chi tiết về mặt kiến trúc, tư duy thiết kế, và đóng góp của 3 công trình State-of-the-art (SOTA) trong lĩnh vực Truy xuất Ảnh Kết hợp (Composed Image Retrieval - CIR). Tài liệu này có thể được sử dụng trực tiếp làm tư liệu để viết phần **Related Work** trong báo cáo Khóa luận.

---

## 1. CLIP4Cir (ACM TOMM 2023)
**Tên bài báo:** *CLIP4Cir: An Empirical Study of CLIP for Composed Image Retrieval* (Baldrati et al.)
**Phương pháp tiếp cận:** Supervised Learning (Học có giám sát)

### Ý tưởng cốt lõi:
Trước CLIP4Cir, các mô hình CIR thường phải huấn luyện các kiến trúc ResNet kết hợp với RNN/LSTM từ đầu (scratch) rất phức tạp. CLIP4Cir đặt ra câu hỏi: *"Liệu chúng ta có thể tận dụng không gian biểu diễn (embedding space) vốn đã rất mạnh của OpenAI CLIP không?"*

### Kiến trúc (Architecture):
1. **Backbone:** Dùng mạng CLIP (chủ yếu là ResNet50x4) làm bộ trích xuất đặc trưng cơ sở.
2. **Combiner Network:** Khác biệt cốt lõi nằm ở đây. Tác giả đóng băng (hoặc fine-tune nhẹ) CLIP, và xây dựng một mạng MLP (Multi-Layer Perceptron) nhỏ gọi là Combiner. 
3. **Cách hoạt động:** 
   - Ảnh tham chiếu đi qua CLIP Image Encoder $\rightarrow$ Vector ảnh.
   - Văn bản điều chỉnh đi qua CLIP Text Encoder $\rightarrow$ Vector văn bản.
   - Combiner lấy 2 vector này, dùng một cơ chế "Dynamic Scalar" (Cổng vô hướng động) để quyết định xem nên giữ lại bao nhiêu % thông tin hình ảnh, và đưa vào bao nhiêu % thông tin văn bản, từ đó hợp nhất chúng thành **1 Vector Truy vấn duy nhất**.

### Đóng góp cho đồ án của bạn:
- Đây là đại diện tiêu biểu nhất cho mô hình học có giám sát truyền thống. Vector sinh ra bởi Combiner của CLIP4Cir rất phù hợp để đo đạc sự đánh đổi (trade-off) trong FAISS.

---

## 2. SEARLE (ICCV 2023)
**Tên bài báo:** *Zero-Shot Composed Image Retrieval with Textual Inversion* (Baldrati et al.)
**Phương pháp tiếp cận:** Zero-Shot Learning (Không giám sát trên dữ liệu CIR)

### Ý tưởng cốt lõi:
Nhược điểm của CLIP4Cir là nó "học vẹt". Dạy nó quần áo (FashionIQ), nó sẽ không biết tìm kiếm chó mèo. SEARLE giải quyết bài toán Open-domain (Miền mở) bằng phương pháp **Zero-Shot**. Thay vì dạy mô hình cách "kết hợp" ảnh và chữ, SEARLE dạy mô hình cách **biến một bức ảnh thành một từ vựng mới**.

### Kiến trúc (Architecture):
1. Dựa trên khái niệm *Textual Inversion* (đang rất thịnh hành trong Stable Diffusion).
2. Tác giả thiết kế một mạng gọi là $\Phi$ (Phi). Mạng này nhận đầu vào là 1 bức ảnh tham chiếu, và xuất ra một **Pseudo-word Token** (ký hiệu là $S*$).
3. **Cách hoạt động:** Khi người dùng nhập "một chiếc váy giống hình này nhưng màu xanh". Hệ thống sẽ quy bức ảnh váy thành từ $S*$. Cả câu truy vấn được gom thành dạng text: `"a photo of [S*] that is blue"`. 
4. Câu text lai này được đẩy thẳng vào CLIP Text Encoder (đã đóng băng) để lấy ra Vector Truy vấn.

### Đóng góp cho đồ án của bạn:
- SEARLE đánh dấu một bước chuyển mình của ngành CIR. Việc nó Zero-shot nghĩa là nó có thể áp dụng lên bất kỳ kho ảnh khổng lồ nào (như COCO 120,000 ảnh). Điều này làm nền tảng cực tốt để đưa FAISS vào so sánh tốc độ trên quy mô lớn. Công trình này cũng đề xuất bộ Dataset **CIRCO** mà bạn sẽ sử dụng.

---

## 3. Pic2Word (CVPR 2023)
**Tên bài báo:** *Pic2Word: Mapping Pictures to Words for Zero-shot Composed Image Retrieval* (Saito et al., Google Research)
**Phương pháp tiếp cận:** Zero-Shot Learning

### Ý tưởng cốt lõi:
Rất tình cờ, Pic2Word (của Google) và SEARLE (của ĐH Florence) được phát triển song song và cùng ra mắt năm 2023. Tư duy của chúng giống hệt nhau: **Biến ảnh thành 1 Token văn bản giả (Pseudo-token)**. 

### Kiến trúc (Architecture):
- Thay vì dùng Textual Inversion phức tạp, Pic2Word sử dụng một mạng MLP đơn giản làm Mapping Network. Mạng này được huấn luyện trên bộ dữ liệu khổng lồ gồm các cặp Ảnh - Chú thích (như CC3M).
- Nó ép (force) vector của ảnh phải nằm gọn trong không gian từ vựng của ngôn ngữ. Từ đó bức ảnh đóng vai trò như một danh từ.
- **Cách hoạt động:** Tương tự SEARLE, câu query sẽ là: `"a picture of [Image Token] [modifier]"`.

### Đóng góp cho đồ án của bạn:
- Mặc dù kiến trúc train khác nhau, nhưng ở bước Inference (trích xuất), Pic2Word và SEARLE dùng chung một triết lý (Ảnh $\rightarrow$ Text Token $\rightarrow$ CLIP Encoder). Trong khóa luận, Pic2Word sẽ được đóng vai trò là một "Đối chiếu chéo" (Cross-reference baseline) nhằm chứng minh rằng: *"Việc ứng dụng FAISS để tăng tốc truy vấn là đúng đắn cho TẤT CẢ các mô hình CIR theo hệ phái biến ảnh thành từ, chứ không riêng gì SEARLE."* 

---

## 💡 Góc nhìn tổng quan cho Hướng nghiên cứu của Khóa luận

Cả 3 mô hình trên đều vắt kiệt chất xám để giải quyết câu chuyện ở **Tầng Model** (Làm sao để sinh ra 1 vector truy vấn chính xác nhất).
Tuy nhiên, cả 3 công trình này đều "bỏ quên" **Tầng Index** (Làm sao để so sánh vector truy vấn đó với hàng triệu vector trong thư viện một cách nhanh nhất). Trong code gốc của họ, họ lấy vector truy vấn nhân chéo (Matrix Multiplication / Dot Product) với toàn bộ Gallery để tính Cosine Similarity. Quá trình quét cạn (Brute-force) này tốn $O(N)$ thời gian. 

Đây chính là **Khe hở nghiên cứu (Research Gap)** tuyệt vời mà Khóa luận của bạn nhắm tới: Thay thế phép tính $O(N)$ đó bằng các cấu trúc cây và lượng tử hóa (IVFPQ, HNSW) của hệ thống **FAISS**, giảm thời gian tìm kiếm xuống $O(\log N)$ mà chỉ hi sinh $<1\%$ độ chính xác (Recall).
