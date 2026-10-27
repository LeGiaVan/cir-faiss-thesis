"""
Bước 0 (Audit R2): Xây dựng Bộ 1.020 Queries CIRCO (Val + Test)
================================================================
Theo yêu cầu phản biện của Mentor:
  "2. Thiếu lực thống kê. 220 truy vấn, nhóm hub chỉ 3 và 6.
      Retention không cần ground truth, nên em dùng được cả tập test của CIRCO:
      tổng 1.020 truy vấn. Phân tích theo láng giềng cho khoảng 10.200 quan sát mỗi model."

Script này:
  1. Tái sử dụng 220 query val đã có trong data/queries/{model}/circo_queries.pkl
  2. Nạp 800 query test từ data/annotations/circo/test.json
  3. Trích xuất đặc trưng cho 800 query test bằng adapter của model (Pic2Word / SEARLE)
  4. Nối (concatenate) thành 1.020 queries (1.020 x dim)
  5. Lưu tại: Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/circo_1020_queries_{model}.pkl
"""

import os
import sys
import json
import time
import pickle
import pathlib
import argparse
import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

# Fix UTF-8 stdout trên Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Thiết lập đường dẫn gốc repo
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
ROOT_DIR = MODULE_DIR.parents[2]   # cir_faiss_thesis/
sys.path.append(str(ROOT_DIR / "src"))

# Patch an toàn cho torch để tránh prompt tương tác và lỗi PyTorch 2.6+
try:
    torch.hub._TRUSTED_LIST.add('miccunifi_SEARLE')
    torch.hub._TRUSTED_LIST.add('miccunifi/SEARLE')
except Exception:
    pass

_orig_hub_load = torch.hub.load
def _safe_hub_load(*args, **kwargs):
    kwargs['trust_repo'] = True
    return _orig_hub_load(*args, **kwargs)
torch.hub.load = _safe_hub_load

_orig_torch_load = torch.load
def _safe_torch_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _orig_torch_load(*args, **kwargs)
torch.load = _safe_torch_load


def get_adapter(model_name: str, device: str = "cpu"):
    if model_name == "searle":
        from extractors.searle_adapter import SearleAdapter
        adapter = SearleAdapter(device=device)
        adapter.load_model()
        return adapter, 512
    elif model_name == "pic2word":
        from extractors.pic2word_adapter import Pic2WordAdapter
        adapter = Pic2WordAdapter(device=device)
        adapter.load_model()
        return adapter, 768
    else:
        raise ValueError(f"Model không hợp lệ: {model_name}. Chỉ hỗ trợ 'searle' hoặc 'pic2word'.")


def build_1020_queries(model_name: str, batch_size: int = 32, device: str = "cpu"):
    out_dir = MODULE_DIR / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"circo_1020_queries_{model_name}.pkl"

    if out_file.exists():
        print(f"[SKIP] File {out_file.name} đã tồn tại, bỏ qua trích xuất!")
        return out_file

    print(f"\n=======================================================")
    print(f"BẮT ĐẦU XÂY DỰNG 1.020 QUERIES CIRCO CHO: {model_name.upper()}")
    print(f"=======================================================")

    # 1. Nạp 220 val queries đã trích xuất sẵn
    val_pkl_path = ROOT_DIR / "data" / "queries" / model_name / "circo_queries.pkl"
    if not val_pkl_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file query val gốc: {val_pkl_path}")

    with open(val_pkl_path, "rb") as f:
        val_data = pickle.load(f)
    val_feats = val_data["query_features"]
    assert val_feats.shape[0] == 220, f"Expected 220 val queries, got {val_feats.shape[0]}"
    print(f"[1/4] Đã nạp 220 val queries từ {val_pkl_path.name}: shape = {val_feats.shape}")

    # 2. Nạp annotation test (800 queries)
    test_anno_path = ROOT_DIR / "data" / "annotations" / "circo" / "test.json"
    with open(test_anno_path, "r", encoding="utf-8") as f:
        test_items = json.load(f)
    assert len(test_items) == 800, f"Expected 800 test queries, got {len(test_items)}"
    print(f"[2/4] Đã nạp 800 test annotations từ {test_anno_path.name}")

    # 3. Khởi tạo adapter và trích xuất 800 test queries
    adapter, expected_dim = get_adapter(model_name, device=device)
    assert val_feats.shape[1] == expected_dim, f"Dim mismatch: {val_feats.shape[1]} vs {expected_dim}"

    img_dir = ROOT_DIR / "data" / "raw" / "circo" / "unlabeled2017"
    print(f"[3/4] Trích xuất đặc trưng 800 test queries (batch_size={batch_size})...")

    test_features_list = []
    t0 = time.time()

    for i in tqdm(range(0, len(test_items), batch_size), desc=f"Extracting {model_name} test"):
        batch_items = test_items[i : i + batch_size]
        batch_imgs = []
        batch_caps = []
        for it in batch_items:
            img_path = img_dir / f"{str(it['reference_img_id']).zfill(12)}.jpg"
            img = Image.open(img_path).convert("RGB")
            batch_imgs.append(img)
            batch_caps.append(it["relative_caption"])

        with torch.no_grad():
            batch_feats = adapter.extract_query_features(batch_imgs, batch_caps)
        test_features_list.append(batch_feats)

    test_feats = np.vstack(test_features_list).astype(np.float32)
    assert test_feats.shape == (800, expected_dim), f"Unexpected test shape: {test_feats.shape}"
    print(f"Trích xuất 800 test queries hoàn tất trong {time.time() - t0:.2f}s!")

    # 4. Gộp thành 1.020 queries
    all_query_features = np.vstack([val_feats, test_feats]).astype(np.float32)
    assert all_query_features.shape == (1020, expected_dim)

    # Đảm bảo L2 normalized
    norms = np.linalg.norm(all_query_features, axis=1, keepdims=True)
    all_query_features = all_query_features / np.maximum(norms, 1e-12)

    bundle = {
        "model": model_name,
        "dataset": "circo",
        "num_queries": 1020,
        "split_counts": {"val": 220, "test": 800},
        "query_features": all_query_features,
        "val_target_ids": val_data.get("target_ids", []),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(out_file, "wb") as f:
        pickle.dump(bundle, f)

    print(f"[4/4] ĐÃ LƯU THÀNH CÔNG BỘ 1.020 QUERIES:")
    print(f"      File: {out_file}")
    print(f"      Shape: {all_query_features.shape} (dtype: {all_query_features.dtype})")
    print(f"=======================================================\n")
    return out_file


def main():
    parser = argparse.ArgumentParser(description="Trích xuất và gộp 1.020 queries CIRCO (Val + Test)")
    parser.add_argument("--model", type=str, default="all", choices=["searle", "pic2word", "all"],
                        help="Tên mô hình cần trích xuất (searle | pic2word | all)")
    parser.add_argument("--batch-size", type=int, default=32, help="Kích thước batch trích xuất")
    parser.add_argument("--device", type=str, default="cpu", help="Thiết bị ('cpu' hoặc 'cuda')")
    args = parser.parse_args()

    models = ["searle", "pic2word"] if args.model == "all" else [args.model]
    for m in models:
        build_1020_queries(m, batch_size=args.batch_size, device=args.device)


if __name__ == "__main__":
    main()
