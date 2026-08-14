import os
import sys
import argparse
import pickle
import numpy as np
import pandas as pd

# Fix Unicode print on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn để import các module trong src/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from evaluation.eval_harness import FaissEvaluator
from scripts.run_eval_benchmark import (
    compute_all_metrics, build_index_configs,
    N_HNSW_BUILDS, N_HNSW_TRIALS_PER_BUILD, N_SEARCH_TRIALS
)

def flatten(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]

def run_subsample(model: str, subset_size: int):
    """
    Chạy sweep FAISS trên CIRCO gallery đã được subsample.
    """
    dataset = "circo"
    tag = dataset
    
    gallery_feat_path = os.path.join("data", "embeddings", model, f"{tag}_gallery.npy")
    gallery_name_path = os.path.join("data", "embeddings", model, f"{tag}_names.npy")
    query_path = os.path.join("data", "queries", model, f"{tag}_queries.pkl")

    if not os.path.exists(gallery_feat_path) or not os.path.exists(query_path):
        print(f"[LỖI] Không tìm thấy dữ liệu cho {model} trên {tag}.")
        return []

    print(f"\n=== FAISS SUBSAMPLE SWEEP: {model.upper()} trên {tag.upper()} (N={subset_size}) ===")
    
    gallery_features = np.load(gallery_feat_path)
    gallery_names = np.load(gallery_name_path).astype(str)
    
    with open(query_path, 'rb') as f:
        query_data = pickle.load(f)

    query_features = query_data["query_features"]
    target_ids = query_data["target_ids"]
    group_members = query_data["group_members"]
    
    # 1. Thu thập tất cả target IDs để giữ lại
    all_target_names = set(flatten(target_ids))
    # Loại bỏ các target rỗng
    all_target_names.discard("")
    
    # Tìm index của các target trong gallery
    target_mask = np.isin(gallery_names, list(all_target_names))
    target_indices = np.where(target_mask)[0]
    
    if len(target_indices) > subset_size:
        print(f"[CẢNH BÁO] Số lượng target ({len(target_indices)}) lớn hơn subset_size ({subset_size}). Sẽ tự động tăng subset_size.")
        subset_size = len(target_indices)
        
    # 2. Random sample phần còn lại
    non_target_indices = np.where(~target_mask)[0]
    n_fill = subset_size - len(target_indices)
    
    rng = np.random.RandomState(42)
    fill_indices = rng.choice(non_target_indices, size=n_fill, replace=False)
    
    # 3. Combine và sort (để đảm bảo thứ tự ngẫu nhiên hoặc ít nhất là deterministically sorted)
    subset_indices = np.sort(np.concatenate([target_indices, fill_indices]))
    sub_gallery_features = gallery_features[subset_indices]
    sub_gallery_names = gallery_names[subset_indices].tolist()
    
    print(f"Đã tạo subsample: {len(sub_gallery_features)} ảnh (bao gồm {len(target_indices)} targets).")
    
    dimension = sub_gallery_features.shape[1]
    indexes = build_index_configs(len(sub_gallery_features))
    
    rows = []
    flatip_indices = None
    
    for idx_config in indexes:
        label = f"{idx_config['type']}[{idx_config['tag']}]"
        print(f"\n--- Benchmarking {label} (N={subset_size}) ---")
        try:
            if idx_config['type'] == 'HNSWFlat':
                all_latencies, all_qpss = [], []
                metric_samples = []
                memory_bytes_list = []
                last_indices = None
                for build_i in range(N_HNSW_BUILDS):
                    evaluator = FaissEvaluator(idx_config['type'], dimension, **idx_config['params'])
                    evaluator.add_gallery(sub_gallery_features)
                    distances, indices, tstats = evaluator.search_repeated(
                        query_features, top_k=50, batch_size=256, n_trials=N_HNSW_TRIALS_PER_BUILD)
                    all_latencies.append(tstats["latency_ms_mean"])
                    all_qpss.append(tstats["qps_mean"])
                    memory_bytes_list.append(evaluator.get_memory_bytes())
                    m = compute_all_metrics(dataset, indices, sub_gallery_names, target_ids,
                                             None, group_members, flatip_indices)
                    metric_samples.append(m)
                    last_indices = indices
                    print(f"  [build {build_i+1}/{N_HNSW_BUILDS}] latency={tstats['latency_ms_mean']:.3f}ms "
                          f"qps={tstats['qps_mean']:.1f}")

                latency_mean, latency_std = float(np.mean(all_latencies)), float(np.std(all_latencies))
                qps_mean, qps_std = float(np.mean(all_qpss)), float(np.std(all_qpss))
                memory_bytes = float(np.mean(memory_bytes_list))

                metrics_mean, metrics_std = {}, {}
                for key in metric_samples[0]:
                    vals = [m[key] for m in metric_samples]
                    metrics_mean[key] = float(np.mean(vals))
                    metrics_std[key] = float(np.std(vals))

            else:
                evaluator = FaissEvaluator(idx_config['type'], dimension, **idx_config['params'])
                evaluator.add_gallery(sub_gallery_features)

                print(f"Running Batch Search x{N_SEARCH_TRIALS} trials...")
                distances, indices, tstats = evaluator.search_repeated(
                    query_features, top_k=50, batch_size=256, n_trials=N_SEARCH_TRIALS)

                if idx_config['type'] == 'FlatIP':
                    flatip_indices = indices

                latency_mean, latency_std = tstats["latency_ms_mean"], tstats["latency_ms_std"]
                qps_mean, qps_std = tstats["qps_mean"], tstats["qps_std"]
                memory_bytes = evaluator.get_memory_bytes()

                metrics_mean = compute_all_metrics(dataset, indices, sub_gallery_names, target_ids,
                                                    None, group_members, flatip_indices)
                metrics_std = {k: 0.0 for k in metrics_mean}

            res_row = {
                "Model": model,
                "Dataset": f"circo_sub_{subset_size}",
                "Category": "-",
                "GallerySize": len(sub_gallery_features),
                "Index": idx_config['type'],
                "Params": idx_config['tag'],
                "Role": idx_config['role'],
                "N_runs": N_HNSW_BUILDS if idx_config['type'] == 'HNSWFlat' else 1,
                "Latency (ms)": round(latency_mean, 3),
                "Latency_std": round(latency_std, 4),
                "QPS": round(qps_mean, 2),
                "QPS_std": round(qps_std, 2),
                "Memory (MB)": round(memory_bytes / (1024 * 1024), 3),
            }
            res_row.update({k: round(v, 2) for k, v in metrics_mean.items()})
            res_row.update({f"{k}_std": round(v, 3) for k, v in metrics_std.items()})
            rows.append(res_row)

            print(f"Latency: {latency_mean:.3f}+/-{latency_std:.4f} ms/query | "
                  f"QPS: {qps_mean:.2f}+/-{qps_std:.2f} | Memory: {memory_bytes/1024/1024:.2f} MB")
            for k, v in metrics_mean.items():
                print(f"{k}: {v:.2f} (+/- {metrics_std[k]:.3f})")

        except Exception as e:
            print(f"[LỖI] Benchmark {label} thất bại: {e}")

    return rows

def main():
    parser = argparse.ArgumentParser(description="FAISS Benchmarking Evaluation for Subsampled CIRCO")
    parser.add_argument("--model", type=str, required=True, choices=["searle", "pic2word"])
    parser.add_argument("--sizes", type=int, nargs='+', default=[10000, 30000, 60000], help="Subset sizes")

    args = parser.parse_args()

    all_rows = []
    for size in args.sizes:
        rows = run_subsample(args.model, size)
        all_rows.extend(rows)

    if not all_rows:
        print("[LỖI] Không có kết quả nào được tạo ra.")
        sys.exit(1)

    out_dir = os.path.join("data", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_csv = os.path.join(out_dir, f"benchmark_{args.model}_circo_subsampled.csv")

    df = pd.DataFrame(all_rows)
    df.to_csv(out_csv, index=False)
    print(f"\n[THÀNH CÔNG] Đã lưu báo cáo benchmark tại: {out_csv}")

if __name__ == "__main__":
    main()
