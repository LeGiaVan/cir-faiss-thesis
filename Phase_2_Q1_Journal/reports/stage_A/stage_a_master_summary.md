# Tổng kết Stage A — bản sửa P0

> Bản làm việc; đã sửa diễn giải legacy, chưa hoàn tất toàn bộ R2. Số liệu đọc từ JSON; P2a/P2c/P3/P4 chưa được xác nhận hoàn thành.

| Module | Kết luận hiện được dữ liệu hỗ trợ | Trạng thái | Báo cáo |
|---|---|---|---|
| A.1 | Phân biệt query-N10 và kết nối HNSW; không suy nhân quả từ hệ số giảm | Chưa kết luận nhân quả | [A.1](./module_a1_hubness_report.md) |
| A.2 | RMS random và top-10 khác nhau; chưa có signed-noise R2 | Ủng hộ một phần | [A.2](./module_a2_pq_perturbation_report.md) |
| A.3 | Retention/coverage nhất quán với cấu trúc IVFFlat | Xác nhận kiểm tra cài đặt | [A.3](./module_a3_ivf_routing_report.md) |
| A.4 | Tăng tốc legacy; chưa kiểm định distractor và matched quality | Chưa kết luận cho ảnh thật mở rộng | [A.4](./module_a4_scale_report.md) |
| A.5 | Không ủng hộ tính duy nhất của hubness; chưa kiểm soát N bằng thiết kế | Bác bỏ tính duy nhất; chưa kết luận dự báo độc lập | [A.5](./module_a5_geometry_power_report.md) |

## Bằng chứng định lượng legacy

SEARLE m=16: RMS random=0.016038; dự báo legacy=0.018932; RMS top-10=0.044928. Sai lệch random/dự báo=15.29%.

searle: nprobe nhỏ nhất trong dải đã đo đạt ≥95% là 32 (96.27%). pic2word: nprobe nhỏ nhất trong dải đã đo đạt ≥95% là 32 (96.05%).

Dải đã đo 10,000–500,000; speedup HNSW ở hai đầu 11.13× và 137.44×.

LID rho=-0.880952, p=0.003850; hubness rho=-0.857143, p=0.006530. Đây là tương quan trong mẫu, chưa đo sức dự báo ngoài mẫu.

## Điều kiện nộp P0–P2

Hoàn thiện P1 và P2b; tiếp tục P2a/P2c trước khi đóng gói đủ hồ sơ. Không dùng kết quả legacy khác cấu hình để xác nhận kết quả reference. Xem [checklist P0](../../R2_Audit/P0_AUDIT_CHECKLIST.md) và [kế hoạch hiện trạng](../../R2_Current_Status_and_Completion_Plan.md).


## Cập nhật đợt P0/P1/P2b

Đã hoàn thiện P0/P1/P2b trong phạm vi nêu ở [báo cáo đợt](../../R2_Audit/P0_P1_P2b_COMPLETION_REPORT.md). A.1 dùng số liệu reference mới, centering trung bình năm cặp build; A.2/A.3 có phần P1 mới tách khỏi legacy; A.4 có anchor timing, A.5 có định nghĩa RC/LID thống nhất. P2a/P2c còn thiếu nên chưa hoàn tất hồ sơ P0–P2.
