import os
import sys
import argparse
import pickle
import numpy as np
import pandas as pd

# Thêm đường dẫn để import các module trong src/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from evaluation.eval_harness import FaissEvaluator, compute_fashioniq_cirr_recall, compute_cirr_subset_recall, compute_circo_map

def main():
    parser = argparse.ArgumentParser(description="FAISS Benchmarking Evaluation")
    parser.add_argument("--model", type=str, required=True, choices=["clip4cir", "searle", "pic2word"])
    parser.add_argument("--dataset", type=str, required=True, choices=["fashioniq", "circo", "cirr"])
    parser.add_argument("--limit", type=int, default=None, help="Suffix limit if testing on subset")
    
    args = parser.parse_args()
    
    print(f"=== FAISS BENCHMARK: {args.model.upper()} trên {args.dataset.upper()} ===")
    
    # 1. Load Gallery Embeddings
    suffix = f"_{args.limit}" if args.limit else ""
    gallery_feat_path = os.path.join("data", "embeddings", args.model, f"{args.dataset}_gallery{suffix}.npy")
    gallery_name_path = os.path.join("data", "embeddings", args.model, f"{args.dataset}_names{suffix}.npy")
    
    if not os.path.exists(gallery_feat_path):
        print(f"[LỖI] Không tìm thấy file Gallery: {gallery_feat_path}")
        sys.exit(1)
        
    print(f"Loading Gallery from {gallery_feat_path}...")
    gallery_features = np.load(gallery_feat_path)
    gallery_names = np.load(gallery_name_path).tolist()
    
    # 2. Load Query Embeddings
    query_path = os.path.join("data", "queries", args.model, f"{args.dataset}_queries{suffix}.pkl")
    
    if not os.path.exists(query_path):
        print(f"[LỖI] Không tìm thấy file Query: {query_path}")
        sys.exit(1)
        
    print(f"Loading Queries from {query_path}...")
    with open(query_path, 'rb') as f:
        query_data = pickle.load(f)
        
    query_features = query_data["query_features"]
    target_ids = query_data["target_ids"]
    group_members = query_data["group_members"]
    
    dimension = gallery_features.shape[1]
    
    # 3. Define FAISS Indexes to benchmark
    indexes = [
        {"type": "FlatIP", "params": {}},
        {"type": "IVFFlat", "params": {"nlist": max(int(np.sqrt(len(gallery_features))), 100), "nprobe": 8}},
        {"type": "HNSWFlat", "params": {"M": 32, "efSearch": 64}},
        {"type": "IVFPQ", "params": {"nlist": max(int(np.sqrt(len(gallery_features))), 100), "m": 8, "bits_per_code": 8, "nprobe": 8}}
    ]
    
    results = []
    
    for idx_config in indexes:
        print(f"\n--- Benchmarking {idx_config['type']} ---")
        try:
            evaluator = FaissEvaluator(idx_config['type'], dimension, **idx_config['params'])
            evaluator.add_gallery(gallery_features)
            
            # Batch search (Throughput)
            print("Running Batch Search (batch_size=256)...")
            distances, indices, latency_ms, qps = evaluator.search(query_features, top_k=50, batch_size=256)
            
            # Compute Metrics
            metrics = {}
            if args.dataset == "fashioniq":
                target_names_flat = [t[0] if len(t) > 0 else "" for t in target_ids]
                metrics = compute_fashioniq_cirr_recall(indices, gallery_names, target_names_flat)
            elif args.dataset == "circo":
                metrics = compute_circo_map(indices, gallery_names, target_ids)
            elif args.dataset == "cirr":
                target_names_flat = [t[0] if len(t) > 0 else "" for t in target_ids]
                metrics = compute_fashioniq_cirr_recall(indices, gallery_names, target_names_flat)
                subset_metrics = compute_cirr_subset_recall(indices, gallery_names, target_names_flat, group_members)
                metrics.update(subset_metrics)
                
            # Store results
            res_row = {
                "Model": args.model,
                "Dataset": args.dataset,
                "Index": idx_config['type'],
                "Latency (ms)": round(latency_ms, 2),
                "QPS": round(qps, 2)
            }
            res_row.update({k: round(v, 2) for k, v in metrics.items()})
            results.append(res_row)
            
            print(f"Latency: {latency_ms:.2f} ms/query | QPS: {qps:.2f}")
            for k, v in metrics.items():
                print(f"{k}: {v:.2f}")
                
        except Exception as e:
            print(f"[LỖI] Benchmark {idx_config['type']} thất bại: {e}")
            
    # 4. Lưu ra CSV
    out_dir = os.path.join("data", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_csv = os.path.join(out_dir, f"benchmark_{args.model}_{args.dataset}{suffix}.csv")
    
    df = pd.DataFrame(results)
    df.to_csv(out_csv, index=False)
    print(f"\n[THÀNH CÔNG] Đã lưu báo cáo benchmark tại: {out_csv}")
    
    print("\n--- BẢNG TỔNG KẾT ---")
    print(df.to_markdown(index=False))

if __name__ == "__main__":
    main()
