# Báo cáo Thực nghiệm Module A.5: Hình học, quy mô và retention

> Bản sửa P0; sinh từ JSON legacy bằng `render_p0_reports.py`. Không gán cấu hình reference mới cho số liệu lịch sử.

## 1. Câu hỏi nghiên cứu

Các chỉ số hình học có liên hệ với retention độc lập với quy mô N không?

## 2. Giả thuyết và dự đoán

Hậu kiểm phát biểu hubness là chỉ số duy nhất có liên hệ mạnh. Phân tích này không thay thế thiết kế N cố định của P2c.

## 3. Thiết kế thực nghiệm

Nguồn: `data/results/phase2_stageA/json/module_a5_geometry_power.json`, 8 cặp model/dataset. Retention lấy từ sweep stress M16/ef32; legacy RC/LID chưa đồng nhất giao thức mới. Tương quan riêng phần: residual hóa ranks của x,y theo rank(log N), Pearson residual; p xấp xỉ t với n−3 bậc tự do, không điều chỉnh đa kiểm định.

## 4. Kết quả

LID rho=-0.880952, p=0.003850; hubness rho=-0.857143, p=0.006530. Đây là tương quan trong mẫu, chưa đo sức dự báo ngoài mẫu.

| Biến | Spearman thô | p hai phía | Riêng phần rank | log N | p xấp xỉ |
|---|---|---|---|---|
| relative_contrast | -0.142857 | 0.735765 | 0.186168 | 0.689399 |
| lid | -0.880952 | 0.003850 | 0.111111 | 0.812534 |
| hubness_skewness | -0.857143 | 0.006530 | -0.220755 | 0.634299 |
| anti_hub_ratio | -0.666667 | 0.070988 | -0.237322 | 0.608360 |
| log10_N | -0.944911 | 0.000401 | N/A | N/A |

## 5. Kết luận và trạng thái

**BÁC BỎ** phát biểu hubness là chỉ số duy nhất có tương quan mạnh trong mẫu: LID có |rho| lớn hơn, log N còn mạnh hơn. **CHƯA KẾT LUẬN** về sức dự báo độc lập với N; các tương quan riêng phần chưa đạt mức 0,05.

## 6. Hạn chế

Chỉ có 8 điểm, nhiều điểm chia sẻ model/dataset, p xấp xỉ và không có đánh giá ngoài mẫu. Không coi tương quan thô là cơ chế nhân quả. Không gán định nghĩa RC/LID mới cho giá trị legacy.

## 7. Các bước tiếp theo

P2c chưa thực hiện: tính RC/LID thống nhất, thiết kế N cố định và quét N có lấy mẫu lặp; báo cáo CI và phụ thuộc giữa các tập con.

### Cập nhật P1 — profile chuẩn hóa

RC là mean cosine distance cặp non-self / mean nearest non-self cosine distance; LID dùng Euclidean chord và MLE k=20. LID legacy dùng 1−cosine (bình phương khoảng cách Euclidean chia hai), có thể làm thay đổi thang ước lượng. Sai khác còn do chọn mẫu và xử lý zero-distance; chưa khẳng định khớp ICRCV khi chưa có cấu hình gốc.

- clip4cir/cirr: RC=4.058937, LID=11.276208; loại 6 neighborhood không hợp lệ. [JSON](../../R2_Audit/p1_reference/results/a5_geometry_clip4cir_cirr.json).
- clip4cir/fashioniq: RC=3.492911, LID=16.865797; loại 104 neighborhood không hợp lệ. [JSON](../../R2_Audit/p1_reference/results/a5_geometry_clip4cir_fashioniq.json).
- pic2word/circo: RC=3.543633, LID=23.834063; loại 4 neighborhood không hợp lệ. [JSON](../../R2_Audit/p1_reference/results/a5_geometry_pic2word_circo.json).
- pic2word/cirr: RC=3.046162, LID=14.356925; loại 4 neighborhood không hợp lệ. [JSON](../../R2_Audit/p1_reference/results/a5_geometry_pic2word_cirr.json).
- pic2word/fashioniq: RC=3.002600, LID=20.517780; loại 117 neighborhood không hợp lệ. [JSON](../../R2_Audit/p1_reference/results/a5_geometry_pic2word_fashioniq.json).
- searle/circo: RC=3.858151, LID=24.346827; loại 6 neighborhood không hợp lệ. [JSON](../../R2_Audit/p1_reference/results/a5_geometry_searle_circo.json).
- searle/cirr: RC=3.266991, LID=14.343337; loại 6 neighborhood không hợp lệ. [JSON](../../R2_Audit/p1_reference/results/a5_geometry_searle_cirr.json).
- searle/fashioniq: RC=3.055838, LID=20.221886; loại 100 neighborhood không hợp lệ. [JSON](../../R2_Audit/p1_reference/results/a5_geometry_searle_fashioniq.json).
