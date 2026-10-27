# Kết quả hoàn thiện P0, P1 và P2b

> Phạm vi đợt này: sửa P0, tích hợp giao thức P1 và hoàn thiện A.1 P2b. Không đóng P2a/P2c/P3/P4.

## 1. Trạng thái nghiệm thu

| Hạng mục | Đã thực hiện | Giới hạn còn lại |
|---|---|---|
| P0 | 13 evidence; sửa A.2–A.5/tổng kết; renderer từ JSON và hình A.4 đúng dải | Bản legacy được giữ trong archive; không gán cấu hình mới cho dữ liệu cũ |
| P1 | Loader/schema/RC/LID/timing dùng chung; entrypoint Stage A nối pipeline chuẩn; chạy lại A.2/A.3, anchor A.4, RC/LID tám gallery | Chuỗi scale mở rộng không tái xác nhận: cần P3a kiểm định distractor. Metadata lịch sử thiếu vẫn ghi unknown |
| P2b | 1020 query, neighbor/in-degree counts+CI, GEE M0–M2, 5 cặp build mỗi model, full exact-rank check và paired CI | Test ID tái dựng từ extraction order; chưa kiểm chứng độc lập embedding test. Một seed cho hồi quy; chưa làm stress |

## 2. Kết quả A.1 reference mới

| Model | Retention trước (%) | Sau (%) | Delta (điểm %) | CI 95% delta (điểm %) |
|---|---:|---:|---:|---|
| searle | 96.7353 | 96.9843 | 0.2490 | [-0.1078, 0.5765] |
| pic2word | 90.8745 | 94.9647 | 4.0902 | [3.5647, 4.6413] |

Beta Pic2Word: M0=1.075712; M1=0.776995; M2=-0.035190. p M2=0.767919.

Giữ riêng ý nghĩa thực nghiệm của cải thiện retention và kết luận nhân quả về hubness. Query-N10 không đổi theo phép biến đổi; graph được đo trực tiếp trước–sau. CI dùng paired query/seed bootstrap; không đọc giảm beta thành tỷ lệ tác động nhân quả.

## 3. Kiểm tra đã chạy

- active Python syntax
- metadata, config hash, input hashes and actual FAISS threads: 18 artifacts
- 20400 neighbor rows, 1020 paired query IDs, 10 neighbors each; counts and CI bounds
- 20 HNSW builds; edge conservation; raw query deltas; full rank checks; seven timing repeats
- GEE convergence, common scale, sample and cluster counts
- 13 P0 evidence files and seven-section reports A.2–A.5

Kiểm tra số học độc lập trên mẫu nhỏ: `python Phase_2_Q1_Journal/R2_Audit/scripts/check_protocol.py` (graph theo vòng lặp, LID dense exact, centering identity, paired bootstrap và timing).

## 4. Artifact và lệnh tái lập

- [Báo cáo A.1 đầy đủ](../reports/stage_A/module_a1_hubness_report.md).
- [Checklist P0](./P0_AUDIT_CHECKLIST.md).
- [P1 protocol](./p1_reference/PROTOCOL.md) và [danh mục kết quả](./p1_reference/REPORT.md).
- [JSON A.1](./module_a1_revision/results/) và [dữ liệu từng query](./module_a1_revision/data/centering_per_query.parquet).
- [Kết quả kiểm tra máy đọc](./verification.json).

## 5. Việc chưa thuộc phạm vi đợt này

P2a signed-noise/swap curve, P2c N cố định/quét N, P3a distractor/matched quality, P3b H-MG và P4 Pareto còn mở. Chỉ hoàn thiện hồ sơ P0–P2 để gửi mentor sau khi bổ sung P2a/P2c. Không có thao tác gửi thông tin ra ngoài trong đợt này.
