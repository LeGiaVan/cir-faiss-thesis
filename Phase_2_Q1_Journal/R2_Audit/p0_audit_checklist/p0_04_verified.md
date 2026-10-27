# P0.4 — bằng chứng sửa báo cáo

**Trạng thái:** ĐÃ SỬA P0.

N10=0 của exact kNN không đồng nghĩa in-degree HNSW=0. A.1 R2 đo trực tiếp các cạnh tầng 0; xem hàm `graph_degrees` trong `src/phase2/protocol.py` và `run_reference_audit.py`. Thiết kế query→gallery R2 được phân biệt với gallery→gallery legacy.

[JSON nguồn](../../../data/results/phase2_stageA/json/module_a1_hubness.json); hash và phép tính bổ sung tại [p0_derived_statistics.json](./p0_derived_statistics.json). Xem [báo cáo hiện hành](../../reports/stage_A/).
