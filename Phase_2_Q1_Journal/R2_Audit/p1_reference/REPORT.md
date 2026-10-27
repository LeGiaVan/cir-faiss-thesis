# P1 — kết quả chạy lại theo cấu hình chung

Không trộn với JSON legacy; mỗi file chứa hash đầu vào, snapshot cấu hình, code hash, hardware và phiên bản thư viện.

| Run | Model | Dataset | Gallery | Query/sample | FAISS threads |
|---|---|---|---|---|---|
| [a2_pic2word](./results/a2_pic2word.json) | pic2word | circo | 123403 | 220 | 8 |
| [a2_searle](./results/a2_searle.json) | searle | circo | 123403 | 220 | 8 |
| [a3_pic2word](./results/a3_pic2word.json) | pic2word | circo | 123403 | 220 | 8 |
| [a3_searle](./results/a3_searle.json) | searle | circo | 123403 | 220 | 8 |
| [a4_anchor_pic2word](./results/a4_anchor_pic2word.json) | pic2word | circo | 123403 | 220 | 8 |
| [a4_anchor_searle](./results/a4_anchor_searle.json) | searle | circo | 123403 | 220 | 8 |
| [a5_geometry_clip4cir_cirr](./results/a5_geometry_clip4cir_cirr.json) | clip4cir | cirr | 2297 | 2297 | 8 |
| [a5_geometry_clip4cir_fashioniq](./results/a5_geometry_clip4cir_fashioniq.json) | clip4cir | fashioniq | 3817 | 3817 | 8 |
| [a5_geometry_pic2word_circo](./results/a5_geometry_pic2word_circo.json) | pic2word | circo | 123403 | 10000 | 8 |
| [a5_geometry_pic2word_cirr](./results/a5_geometry_pic2word_cirr.json) | pic2word | cirr | 2297 | 2297 | 8 |
| [a5_geometry_pic2word_fashioniq](./results/a5_geometry_pic2word_fashioniq.json) | pic2word | fashioniq | 3817 | 3817 | 8 |
| [a5_geometry_searle_circo](./results/a5_geometry_searle_circo.json) | searle | circo | 123403 | 10000 | 8 |
| [a5_geometry_searle_cirr](./results/a5_geometry_searle_cirr.json) | searle | cirr | 2297 | 2297 | 8 |
| [a5_geometry_searle_fashioniq](./results/a5_geometry_searle_fashioniq.json) | searle | fashioniq | 3817 | 3817 | 8 |

A.2 ở đây chỉ chạy lại phép đo trị tuyệt đối đã có, chưa thay thế P2a. A.5 tính lại định nghĩa RC/LID trên gallery gốc, chưa thay thế P2c N cố định. A.4 chỉ là anchor latency trên gallery gốc; chuỗi mở rộng/distractor cần P3a.
