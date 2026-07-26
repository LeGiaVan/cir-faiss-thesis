import os
import sys
import argparse
import pickle
import math
import numpy as np
import pandas as pd

# Fix Unicode print on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn để import các module trong src/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from evaluation.eval_harness import (
    FaissEvaluator, compute_fashioniq_cirr_recall, compute_cirr_subset_recall,
    compute_circo_map, compute_recall_retention
)

FASHIONIQ_CATEGORIES = ["dress", "shirt", "toptee"]
RETENTION_K_LIST = [1, 5, 10, 50]


def build_index_configs(gallery_size: int):
    """
    Lưới sweep tham số FAISS, với nlist THÍCH ỨNG theo quy mô gallery (thay vì số cố định) -
    tránh lỗi "quá ít điểm/cụm" (FAISS warning "please provide at least N training points")
    từng làm IVFPQ giảm recall bất thường trên các gallery nhỏ (CIRR ~2.3K, FashionIQ ~4-6K).

    Mỗi config có 2 nhãn:
    - "tag": hiển thị con số THẬT đã dùng (vd nlist62_nprobe8) - để đọc trực tiếp trong CSV.
    - "role": nhãn ỔN ĐỊNH không phụ thuộc N (vd IVFFlat_small_nprobe8) - dùng làm khoá gộp
      trung bình 3 category FashionIQ, vì mỗi category có N khác nhau nên nlist thật cũng khác
      nhau - nếu gộp theo "tag" (chứa số thật) sẽ không bao giờ khớp giữa 3 category.
    """
    nlist_small = max(int(round(math.sqrt(gallery_size))), 8)
    nlist_large = max(int(round(4 * math.sqrt(gallery_size))), nlist_small + 1)

    configs = [{"type": "FlatIP", "params": {}, "tag": "-", "role": "FlatIP"}]

    seen = set()

    def add(index_type, params, tag, role):
        key = (index_type, tuple(sorted(params.items())))
        if key in seen:
            return
        seen.add(key)
        configs.append({"type": index_type, "params": params, "tag": tag, "role": role})

    for size_label, nlist in [("small", nlist_small), ("large", nlist_large)]:
        for nprobe in [8, 32, 128]:
            nprobe_eff = min(nprobe, nlist)
            add("IVFFlat", {"nlist": nlist, "nprobe": nprobe_eff},
                tag=f"nlist{nlist}_nprobe{nprobe_eff}",
                role=f"IVFFlat_{size_label}nlist_nprobe{nprobe}")

    for M in [16, 32]:
        for efSearch in [32, 128]:
            add("HNSWFlat", {"M": M, "efSearch": efSearch},
                tag=f"M{M}_ef{efSearch}", role=f"HNSWFlat_M{M}_ef{efSearch}")

    # IVFPQ: ưu tiên nlist nhỏ (nlist_small) để cụm đủ điểm train ổn định.
    for m in [8, 16]:
        for nprobe in [32, 128]:
            nprobe_eff = min(nprobe, nlist_small)
            add("IVFPQ", {"nlist": nlist_small, "m": m, "bits_per_code": 8, "nprobe": nprobe_eff},
                tag=f"m{m}_nprobe{nprobe_eff}", role=f"IVFPQ_m{m}_nprobe{nprobe}")

    return configs


def run_one(model: str, dataset: str, category: str, limit: int):
    """
    Chạy sweep FAISS đầy đủ cho đúng 1 tổ hợp (model, dataset[, category]).
    Trả về list các dict kết quả (1 dict / cấu hình index).
    """
    tag = f"{dataset}_{category}" if category else dataset
    suffix = f"_{limit}" if limit else ""

    gallery_feat_path = os.path.join("data", "embeddings", model, f"{tag}_gallery{suffix}.npy")
    gallery_name_path = os.path.join("data", "embeddings", model, f"{tag}_names{suffix}.npy")
    query_path = os.path.join("data", "queries", model, f"{tag}_queries{suffix}.pkl")

    if not os.path.exists(gallery_feat_path):
        print(f"[LỖI] Không tìm thấy file Gallery: {gallery_feat_path} - bỏ qua {tag}")
        return []
    if not os.path.exists(query_path):
        print(f"[LỖI] Không tìm thấy file Query: {query_path} - bỏ qua {tag}")
        return []

    print(f"\n=== FAISS SWEEP: {model.upper()} trên {tag.upper()} ===")
    print(f"Loading Gallery from {gallery_feat_path}...")
    gallery_features = np.load(gallery_feat_path)
    gallery_names = np.load(gallery_name_path).tolist()

    print(f"Loading Queries from {query_path}...")
    with open(query_path, 'rb') as f:
        query_data = pickle.load(f)

    query_features = query_data["query_features"]
    target_ids = query_data["target_ids"]
    group_members = query_data["group_members"]

    dimension = gallery_features.shape[1]
    indexes = build_index_configs(len(gallery_features))

    rows = []
    flatip_indices = None  # baseline để tính Recall Retention

    for idx_config in indexes:
        label = f"{idx_config['type']}[{idx_config['tag']}]"
        print(f"\n--- Benchmarking {label} ---")
        try:
            evaluator = FaissEvaluator(idx_config['type'], dimension, **idx_config['params'])
            evaluator.add_gallery(gallery_features)

            print("Running Batch Search (batch_size=256)...")
            distances, indices, latency_ms, qps = evaluator.search(query_features, top_k=50, batch_size=256)

            if idx_config['type'] == 'FlatIP':
                flatip_indices = indices

            metrics = {}
            if dataset == "fashioniq":
                target_names_flat = [t[0] if len(t) > 0 else "" for t in target_ids]
                metrics = compute_fashioniq_cirr_recall(indices, gallery_names, target_names_flat)
            elif dataset == "circo":
                metrics = compute_circo_map(indices, gallery_names, target_ids)
            elif dataset == "cirr":
                target_names_flat = [t[0] if len(t) > 0 else "" for t in target_ids]
                metrics = compute_fashioniq_cirr_recall(indices, gallery_names, target_names_flat)
                subset_metrics = compute_cirr_subset_recall(indices, gallery_names, target_names_flat, group_members)
                metrics.update(subset_metrics)

            # Recall Retention: so trực tiếp với FlatIP (baseline luôn chạy trước tiên trong danh sách)
            retention = compute_recall_retention(indices, flatip_indices, RETENTION_K_LIST)

            memory_bytes = evaluator.get_memory_bytes()

            res_row = {
                "Model": model,
                "Dataset": dataset,
                "Category": category if category else "-",
                "GallerySize": len(gallery_features),
                "Index": idx_config['type'],
                "Params": idx_config['tag'],
                "Role": idx_config['role'],
                "Latency (ms)": round(latency_ms, 3),
                "QPS": round(qps, 2),
                "Memory (MB)": round(memory_bytes / (1024 * 1024), 3),
            }
            res_row.update({k: round(v, 2) for k, v in retention.items()})
            res_row.update({k: round(v, 2) for k, v in metrics.items()})
            rows.append(res_row)

            print(f"Latency: {latency_ms:.3f} ms/query | QPS: {qps:.2f} | Memory: {memory_bytes/1024/1024:.2f} MB")
            for k, v in retention.items():
                print(f"{k}: {v:.2f}")
            for k, v in metrics.items():
                print(f"{k}: {v:.2f}")

        except Exception as e:
            print(f"[LỖI] Benchmark {label} thất bại: {e}")

    return rows


def average_fashioniq_categories(rows: list) -> list:
    """
    FashionIQ: Recall@K cuối cùng phải là trung bình cộng của 3 category (dress/shirt/toptee),
    KHÔNG phải trộn chung gallery. Gộp theo "Role" (nhãn ổn định, không phụ thuộc N) chứ KHÔNG
    theo "Params" (chứa số nlist/nprobe thật, khác nhau giữa 3 category vì N khác nhau - nếu gộp
    theo Params sẽ gần như không bao giờ khớp đủ 3 category, làm rơi mất hầu hết IVFFlat/IVFPQ).
    """
    df = pd.DataFrame(rows)
    if df.empty:
        return rows

    numeric_cols = [c for c in df.columns if c not in ("Model", "Dataset", "Category", "Index", "Params", "Role")]

    avg_rows = []
    for (model_, index_, role_), group in df.groupby(["Model", "Index", "Role"]):
        if len(group) != len(FASHIONIQ_CATEGORIES):
            continue  # role không xuất hiện đủ ở cả 3 category -> bỏ qua dòng trung bình
        avg = group[numeric_cols].mean(numeric_only=True).round(2)
        params_display = " / ".join(sorted(group["Params"].unique()))  # liệt kê số thật từng category
        avg_row = {"Model": model_, "Dataset": "fashioniq", "Category": "AVERAGE(3 categories)",
                   "Index": index_, "Params": params_display, "Role": role_}
        avg_row.update(avg.to_dict())
        avg_rows.append(avg_row)

    return pd.concat([df, pd.DataFrame(avg_rows)], ignore_index=True).to_dict("records")


def main():
    parser = argparse.ArgumentParser(description="FAISS Benchmarking Evaluation (sweep + Recall Retention)")
    parser.add_argument("--model", type=str, required=True, choices=["clip4cir", "searle", "pic2word"])
    parser.add_argument("--dataset", type=str, required=True, choices=["fashioniq", "circo", "cirr"])
    parser.add_argument("--limit", type=int, default=None, help="Suffix limit if testing on subset")

    args = parser.parse_args()

    if args.dataset == "fashioniq":
        all_rows = []
        for cat in FASHIONIQ_CATEGORIES:
            all_rows.extend(run_one(args.model, args.dataset, cat, args.limit))
        results = average_fashioniq_categories(all_rows)
    else:
        results = run_one(args.model, args.dataset, None, args.limit)

    if not results:
        print("[LỖI] Không có kết quả nào được tạo ra.")
        sys.exit(1)

    # Lưu ra CSV
    out_dir = os.path.join("data", "results")
    os.makedirs(out_dir, exist_ok=True)
    suffix = f"_{args.limit}" if args.limit else ""
    out_csv = os.path.join(out_dir, f"benchmark_{args.model}_{args.dataset}{suffix}.csv")

    df = pd.DataFrame(results)
    df.to_csv(out_csv, index=False)
    print(f"\n[THÀNH CÔNG] Đã lưu báo cáo benchmark tại: {out_csv}")

    print("\n--- BẢNG TỔNG KẾT ---")
    print(df.to_markdown(index=False))


if __name__ == "__main__":
    main()
