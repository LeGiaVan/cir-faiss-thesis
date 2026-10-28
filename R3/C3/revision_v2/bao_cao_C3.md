# C3 — Đối chứng tịnh tiến dưới L2

## 1. Câu hỏi và dự đoán

Dịch đồng thời query và gallery bởi cùng mean có bảo toàn khoảng cách L2 và exact ranking, và HNSW có cho retention gần nhau không? Xem [kế hoạch](../ke_hoach_C3.md).

## 2. Thiết kế

CIRCO 1.020 query; hai model; HNSWFlat L2 M=32, efConstruction=200, efSearch=128, năm seed. So exact top-10 và squared L2 theo 10.000 cặp ngẫu nhiên, ngưỡng tuyệt đối 1e-5. Sau khi kiểm tra sai khác đầu tiên, phiên bản này yêu cầu tập top-10 khớp và chỉ chấp nhận đảo thứ tự nếu mỗi cặp đảo có chênh lệch khoảng cách ở cả hai nhánh không quá 1e-5. Đây là điều chỉnh sau quan sát, được ghi riêng, không phải điều kiện đăng ký trước. Bootstrap chéo ghép cặp seed/query 2.000 lần, CI percentile 95%.

## 3. Kết quả

### SEARLE

Thứ tự top-10 giống hệt: False; số query khác thứ tự: 1; số query khác tập top-10: 0; sai số squared L2 lớn nhất trong top-10: 9.54e-07; trong 10.000 cặp mẫu: 8.61e-08. Chi tiết đảo thứ tự: [diagnostics](../exact_diagnostics.json).

| Seed | Original retention | Centered retention | Chênh lệch điểm % | Original ndis | Centered ndis | Original cạnh | Centered cạnh |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 96.68% | 96.68% | +0.00 | 1881.8 | 1881.8 | 2657637 | 2657637 |
| 43 | 96.70% | 96.70% | +0.00 | 1878.2 | 1878.2 | 2650795 | 2650795 |
| 44 | 96.88% | 96.88% | +0.00 | 1880.6 | 1880.6 | 2658926 | 2658923 |
| 45 | 96.86% | 96.86% | +0.00 | 1876.4 | 1876.4 | 2657720 | 2657713 |
| 46 | 96.56% | 96.56% | +0.00 | 1876.7 | 1876.7 | 2654611 | 2654611 |

Trung bình centered − original: +0.000 điểm %, CI 95% [+0.000, +0.000].

### PIC2WORD

Thứ tự top-10 giống hệt: True; số query khác thứ tự: 0; số query khác tập top-10: 0; sai số squared L2 lớn nhất trong top-10: 8.34e-07; trong 10.000 cặp mẫu: 3.96e-08. Chi tiết đảo thứ tự: [diagnostics](../exact_diagnostics.json).

| Seed | Original retention | Centered retention | Chênh lệch điểm % | Original ndis | Centered ndis | Original cạnh | Centered cạnh |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | 90.83% | 90.83% | +0.00 | 1856.4 | 1856.4 | 2259515 | 2259515 |
| 43 | 91.15% | 91.15% | +0.00 | 1861.4 | 1861.4 | 2256146 | 2256146 |
| 44 | 90.66% | 90.66% | +0.00 | 1856.8 | 1856.8 | 2263112 | 2263112 |
| 45 | 90.95% | 90.95% | +0.00 | 1866.5 | 1866.5 | 2257802 | 2257802 |
| 46 | 90.78% | 90.78% | +0.00 | 1863.1 | 1863.1 | 2265521 | 2265521 |

Trung bình centered − original: +0.000 điểm %, CI 95% [+0.000, +0.000].

## 4. Diễn giải và giới hạn

Tiêu chí thứ tự exact ban đầu không đạt; phiên bản này kiểm tra tập top-10 và sai số ở các cặp gần hòa theo điều chỉnh sau quan sát. Sai khác HNSW được báo theo từng seed; CI chứa 0 không chứng minh tương đương. So sánh tại cùng efSearch không đảm bảo cùng ndis; dựng đa luồng có thể làm thay đổi đồ thị. Bằng chứng này không tự chứng minh cơ chế centering IP hay thay thế C2. Test query IDs chưa xác minh độc lập từng hàng; workspace dirty và provenance lưu bằng hash.

## 5. Đầu ra

[JSON](./results.json) · [bảng từng seed](./per_seed.csv) · [manifest](./run_manifest.json) · [kế hoạch](../ke_hoach_C3.md).
