# R4 Bước 0 — Provenance và đối chiếu ID query

Ngày tạo UTC: 2026-10-31T06:03:26.606669+00:00

## 1. Phạm vi và trạng thái

Kiểm kê nguồn, dữ liệu và môi trường; trích lại query CIRCO test kèm ID tại thời điểm mã hóa; kiểm tra tương thích cache R2. Ngưỡng đối chiếu đã khóa trong [preflight](./preflight_kiem_dinh.md).

Snapshot mã trích xuất độc lập: commit `ec5b359f48c970a15237c128a5fb08d384458394`, working tree sạch. Snapshot nằm ở `source_snapshot/` và không có data, weights hay package cài ngoài; commit này không đại diện đầy đủ cho mọi mã thực nghiệm R4 tương lai.

Workspace nguồn: commit `cfb4be55d85020771d3ace862fced9b75a03d718`; trạng thái và submodule lưu trong [inventory.json](./inventory.json). Không sửa hoặc commit các thay đổi sẵn có của workspace nguồn.

## 2. Input và môi trường

Môi trường: Windows-11-10.0.26200-SP0; CPU `Intel64 Family 6 Model 186 Stepping 2, GenuineIntel`; CPU logic 12; CUDA: False; Python `3.12.7`; thư viện và hash được ghi trong manifest.

Tệp chưa có trong kiểm kê: `R3/C2/bao_cao_C2.md`, `R3/C2/edge_selection.json`, `R3/C2/results.json`, `R3/C2/sweep.csv`. Không suy diễn hoặc thay thế số liệu thiếu.

Tệp khác hash Chặng 0 ngay cả sau chuẩn hóa xuống dòng: `Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/step3_nested_logistic.py`. Không dùng chữ ký cũ để khẳng định đây là cùng mã.

Các tệp `.py`/YAML có thể khác byte LF/CRLF; inventory ghi cả hash gốc và hash chuẩn hóa. Input, weights, 800 ảnh tham chiếu và mã nguồn có hash; weights/data nằm ngoài commit, cần lưu trữ hoặc khôi phục đúng hash.

## 3. Kiểm tra trích xuất và mapping

| Model | Query test | Hàng khớp ngưỡng | Cosine nhỏ nhất | Sai số tọa độ lớn nhất | Hàng khó phân biệt |
|---|---:|---:|---:|---:|---:|
| searle | 800 | 800 | 1.000000000 | 3.2e-07 | 2 |
| pic2word | 800 | 800 | 1.000000000 | 7.42e-07 | 2 |

ID test và reference image ID được ghi cùng batch trích xuất mới. Validation prefix và thứ tự target được kiểm tra với annotation. So sánh vector theo thứ tự annotation với cache cũ; kết quả từng dòng và ngưỡng nằm trong [comparison.json](./comparison.json).

Không có dòng vượt tolerance đã đăng ký. Đây là bằng chứng cache mới nhất quán theo vị trí với cache cũ, không chứng minh bằng mật mã lịch sử ID cho cache cũ vì cache cũ không lưu ID trực tiếp.

## 4. Kết luận và cổng confirmatory

Không coi snapshot mã trích xuất là commit xác nhận cho các script R4 chưa được đưa vào snapshot. Mọi lượt chạy confirmatory tiếp theo cần commit sạch bao phủ đúng mã thực thi, dependency/submodule và input hash. Nếu nguồn/feature khác quá ngưỡng, kiểm tra ảnh hưởng và chạy lại kết quả chịu tác động theo kế hoạch.

Output chi tiết: [inventory](./inventory.json), [ngưỡng trước khi chạy](./preflight_kiem_dinh.md), [script đối chiếu](./compare_extractions.py) và dữ liệu local trong `data/` (được ignore).
