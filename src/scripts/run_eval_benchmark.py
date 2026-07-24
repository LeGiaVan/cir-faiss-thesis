import os
import sys
import argparse
import pickle
import numpy as np
import pandas as pd

# Thêm đường dẫn để import các module trong src/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from evaluation.eval_harness import FaissEvaluator, compute_fashioniq_cirr_recall, compute_cirr_subset_recall, compute_circo_map

FASHIONIQ_CATEGORIES = ["dress", "shirt", "toptee"]


def run_one(model: str, dataset: str, category: str, limit: int):
    """
    Chạy benchmark FAISS cho đúng 1 tổ hợp (model, dataset[, category]).
    Trả về list các dict kết quả (1 dict / loại index).
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

    print(f"\n=== FAISS BENCHMARK: {model.upper()} trên {tag.upper()} ===")
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

    # Định nghĩa các loại FAISS Index sẽ benchmark.
    # LƯU Ý: đây vẫn là cấu hình tham số CỐ ĐỊNH (1 điểm/index type). Sweep tham số đầy đủ
    # (nlist/nprobe/M/efSearch nhiều mức + Recall Retention so với brute-force) là việc của
    # Ngày 5 trong AUDIT_AND_REVISED_PLAN.md, chưa nằm trong đợt sửa bug lần này.
    indexes = [
        {"type": "FlatIP", "params": {}},
        {"type": "IVFFlat", "params": {"nlist": max(int(np.sqrt(len(gallery_features))), 100), "nprobe": 8}},
        {"type": "HNSWFlat", "params": {"M": 32, "efSearch": 64}},
        {"type": "IVFPQ", "params": {"nlist": max(int(np.sqrt(len(gallery_features))), 100), "m": 8, "bits_per_code": 8, "nprobe": 8}}
    ]

    rows = []
    for idx_config in indexes:
        print(f"\n--- Benchmarking {idx_config['type']} ---")
        try:
            evaluator = FaissEvaluator(idx_config['type'], dimension, **idx_config['params'])
            evaluator.add_gallery(gallery_features)

            print("Running Batch Search (batch_size=256)...")
            distances, indices, latency_ms, qps = evaluator.search(query_features, top_k=50, batch_size=256)

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

            res_row = {
                "Model": model,
                "Dataset": dataset,
                "Category": category if category else "-",
                "GallerySize": len(gallery_features),
                "Index": idx_config['type'],
                "Latency (ms)": round(latency_ms, 2),
                "QPS": round(qps, 2)
            }
            res_row.update({k: round(v, 2) for k, v in metrics.items()})
            rows.append(res_row)

            print(f"Latency: {latency_ms:.2f} ms/query | QPS: {qps:.2f}")
            for k, v in metrics.items():
                print(f"{k}: {v:.2f}")

        except Exception as e:
            print(f"[LỖI] Benchmark {idx_config['type']} thất bại: {e}")

    return rows


def average_fashioniq_categories(rows: list) -> list:
    """
    FashionIQ: Recall@K cuối cùng phải là trung bình cộng của 3 category (dress/shirt/toptee),
    KHÔNG phải trộn chung gallery. Hàm này gộp 3 dòng cùng (Model, Index) thành 1 dòng trung bình.
    """
    df = pd.DataFrame(rows)
    if df.empty:
        return rows

    numeric_cols = [c for c in df.columns if c not in ("Model", "Dataset", "Category", "Index")]
    avg_df = df.groupby(["Model", "Dataset", "Index"], as_index=False)[numeric_cols].mean(numeric_only=True)
    avg_df["Category"] = "AVERAGE(3 categories)"
    avg_df = avg_df.round(2)

    return pd.concat([df, avg_df], ignore_index=True).to_dict("records")


def main():
    parser = argparse.ArgumentParser(description="FAISS Benchmarking Evaluation")
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
