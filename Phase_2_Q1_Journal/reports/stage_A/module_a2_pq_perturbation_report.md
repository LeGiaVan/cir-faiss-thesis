# Báo cáo Thực nghiệm Module A.2: Nhiễu điểm số IVFPQ

> Bản sửa P0; sinh từ JSON legacy bằng `render_p0_reports.py`. Không gán cấu hình reference mới cho số liệu lịch sử.

## 1. Câu hỏi nghiên cứu

Nhiễu trên cặp ngẫu nhiên có đại diện cho nhiễu trên các láng giềng exact không?

## 2. Giả thuyết và dự đoán

Đánh giá hậu kiểm giả thuyết nhiễu đẳng hướng toàn cục. Chưa có đăng ký dự đoán định lượng trước lần chạy legacy; không tạo dự đoán hồi tố.

## 3. Thiết kế thực nghiệm

Nguồn: `data/results/phase2_stageA/json/module_a2_pq_perturbation.json` (đường dẫn từ gốc repo). Code legacy dùng CIRCO val, nlist=351, nprobe=32, m=8/16; JSON không có metadata đầy đủ. Tỷ lệ retention trong JSON có đơn vị phần trăm. Nhiễu lưu dạng trị tuyệt đối, chưa đo mean nhiễu có dấu.

## 4. Kết quả

| Model | m | RMS dự báo legacy | RMS random | RMS top-10 | Mean gap 10/11 | Median gap 10/11 | Retention@10 |
|---|---|---|---|---|---|---|---|
| searle | 8 | 0.020321 | 0.017543 | 0.050729 | 0.00097655 | 0.00068790 | 13.86% |
| searle | 16 | 0.018932 | 0.016038 | 0.044928 | 0.00097655 | 0.00068790 | 20.36% |
| pic2word | 8 | 0.017855 | 0.022305 | 0.071288 | 0.00100332 | 0.00072476 | 11.32% |
| pic2word | 16 | 0.017074 | 0.020707 | 0.065726 | 0.00100332 | 0.00072476 | 16.36% |

SEARLE m=16: RMS random=0.016038; dự báo legacy=0.018932; RMS top-10=0.044928. Sai lệch random/dự báo=15.29%.

Nếu delta là RMS top-10 thực đo, 2 delta=0.089856; nếu delta là dự báo RMS random legacy, 2 delta=0.037865. RMS không phải cận trên sai số từng cặp; 2 RMS không phải ngưỡng bảo đảm thứ hạng.

## 5. Kết luận và trạng thái

**ỦNG HỘ MỘT PHẦN:** xấp xỉ toàn cục có thể gần RMS random trong một số cấu hình; không đại diện nhiễu top-10. **CHƯA KẾT LUẬN** về cơ chế nhiễu có dấu và ngưỡng hoán vị g_5% vì chưa có phép đo P2a.

## 6. Hạn chế

Không suy ra bias có dấu từ histogram trị tuyệt đối. Các mảng lưu bị cắt và không có query ID, chưa đủ cho CI theo query đáng tin cậy. Phân vị p95 không phải CI 95%. Chưa dùng kết quả này làm bảo đảm Score-Gap Loss.

## 7. Các bước tiếp theo

P2a: lưu delta có dấu/top-50, tách song song/trực giao, đo d giữa hai hạng liền kề; quét m=8/16/32/64 và tính g_5% cùng CI.

### Cập nhật P1 — profile chuẩn hóa

Cấu hình nlist/nprobe/m lấy từ JSON mới; không so chênh lệch với legacy như một hiệu ứng chỉ do m.

- pic2word, m=8: RMS random=0.021289, top-10=0.062202; retention=14.73%. [JSON](../../R2_Audit/p1_reference/results/a2_pic2word.json).
- pic2word, m=16: RMS random=0.019739, top-10=0.058217; retention=19.59%. [JSON](../../R2_Audit/p1_reference/results/a2_pic2word.json).
- searle, m=8: RMS random=0.016695, top-10=0.043706; retention=16.64%. [JSON](../../R2_Audit/p1_reference/results/a2_searle.json).
- searle, m=16: RMS random=0.015230, top-10=0.038439; retention=24.41%. [JSON](../../R2_Audit/p1_reference/results/a2_searle.json).
