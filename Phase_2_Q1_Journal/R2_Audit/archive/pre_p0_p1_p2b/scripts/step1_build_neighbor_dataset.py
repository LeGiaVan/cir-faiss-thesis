"""
Bước 1: Xây dựng Neighbor-Level Dataset (N = ~20.400 hàng)
===========================================================
Input files (đường dẫn thực tế đã xác minh):
  Gallery : data/embeddings/{model}/circo_gallery.npy
  Queries : data/queries/{model}/circo_queries.pkl  (key: "query_features")
  Names   : data/embeddings/{model}/circo_names.npy

Output:
  data/neighbor_level_data.parquet
  results/step1_hnsw_indegree.json  (với metadata header đầy đủ theo P1)

Ghi chú kỹ thuật HNSW In-degree:
  FAISS HNSWFlat lưu danh sách kề trong mảng phẳng hnsw.neighbors.
  Với mỗi node, Layer-0 neighbors nằm trong đoạn [begin, end) được
  trả về bởi get_node_neighbors_at_layer(node_id, 0).
  Ta đếm số lần mỗi node xuất hiện trong danh sách kề của nodes khác.
"""

import os, sys, json, pickle, time, datetime, pathlib
import numpy as np
import pandas as pd
import scipy.stats
import faiss

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ─── ĐƯỜNG DẪN (đã xác minh) ─────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[4]   # cir_faiss_thesis/
OUT_DIR    = pathlib.Path(__file__).parent.parent / "results"
DATA_DIR   = pathlib.Path(__file__).parent.parent / "data"
OUT_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

GALLERY_PATHS = {
    "searle":   ROOT / "data" / "embeddings" / "searle"   / "circo_gallery.npy",
    "pic2word": ROOT / "data" / "embeddings" / "pic2word" / "circo_gallery.npy",
}
QUERY_1020_PATHS = {
    "searle":   DATA_DIR / "circo_1020_queries_searle.pkl",
    "pic2word": DATA_DIR / "circo_1020_queries_pic2word.pkl",
}
QUERY_VAL_PATHS = {
    "searle":   ROOT / "data" / "queries" / "searle"   / "circo_queries.pkl",
    "pic2word": ROOT / "data" / "queries" / "pic2word" / "circo_queries.pkl",
}

# ─── CẤU HÌNH HNSW (Reference — mentor-audit-protocol P1) ────────────────────
HNSW_M              = 32
HNSW_EF_SEARCH      = 128
HNSW_EF_CONSTRUCTION= 200
TOP_K               = 10

# ─── TIỆN ÍCH ─────────────────────────────────────────────────────────────────

def load_model_data(model: str):
    gallery = np.load(GALLERY_PATHS[model]).astype(np.float32)
    faiss.normalize_L2(gallery)
    
    # Ưu tiên tập 1.020 queries (R2 Audit - mentor recommendation) nếu đã tồn tại
    if QUERY_1020_PATHS[model].exists():
        q_path = QUERY_1020_PATHS[model]
        print(f"[{model.upper()}] Sử dụng tập 1.020 queries từ: {q_path.name}")
    else:
        q_path = QUERY_VAL_PATHS[model]
        print(f"[{model.upper()}] Sử dụng tập 220 val queries từ: {q_path.name}")

    with open(q_path, "rb") as f:
        q_data = pickle.load(f)
    queries = q_data["query_features"].astype(np.float32)
    faiss.normalize_L2(queries)
    return gallery, queries


def compute_query_k_occurrence(query_vecs: np.ndarray, flat_index: faiss.IndexFlatIP, k: int = TOP_K) -> np.ndarray:
    """
    N_k(x): số lần x xuất hiện trong top-k của mọi query.
    Lưu ý: đây là k-occurrence theo query (không phải gallery-vs-gallery),
    đúng với đơn vị phân tích neighbor-level của chúng ta.
    """
    n = flat_index.ntotal
    _, indices = flat_index.search(query_vecs, k)   # (n_queries, k)
    counts = np.bincount(indices.ravel(), minlength=n).astype(np.int32)
    return counts


def get_hnsw_layer0_indegree(hnsw_index: faiss.IndexHNSWFlat, n: int) -> np.ndarray:
    """
    Đếm In-degree tại Layer 0 của HNSW.

    FAISS layout (đã xác minh):
      - hnsw.neighbors  : mảng phẳng chứa tất cả cạnh của đồ thị.
      - hnsw.offsets[i] : vị trí bắt đầu của block node i trong mảng neighbors.
      - Layer 0 luôn nằm ở đầu block: [offsets[i], offsets[i] + nb_neighbors(0))
        (vì cum_nb_neighbors(0) = 0).
      - Slot có giá trị -1 là slot rỗng (chưa điền đủ láng giềng).
    """
    hnsw      = hnsw_index.hnsw
    nbr_arr   = faiss.vector_to_array(hnsw.neighbors)    # int32 flat
    off_arr   = faiss.vector_to_array(hnsw.offsets)      # uint64, len = n+1
    nb0       = hnsw.nb_neighbors(0)                     # = 2*M, layer-0 slots

    # Layer-0 slots cho node i: [off_arr[i], off_arr[i] + nb0)
    # cum_nb_neighbors(0)=0 → layer-0 luôn ở đầu block của mỗi node.
    # Vectorized extraction: tạo ma trận index (n, nb0) bằng outer-sum
    t0 = time.perf_counter()
    node_starts = off_arr[:n].astype(np.int64)            # (n,)
    slot_idx    = node_starts[:, None] + np.arange(nb0)   # (n, nb0)
    slot_idx    = np.clip(slot_idx, 0, len(nbr_arr) - 1)  # guard out-of-bounds
    layer0_mat  = nbr_arr[slot_idx]                        # (n, nb0) int32

    # Lọc bỏ slot rỗng (-1) rồi bincount
    valid  = layer0_mat.ravel()
    valid  = valid[(valid >= 0) & (valid < n)]
    in_deg = np.bincount(valid, minlength=n).astype(np.int32)
    print(f"  in-degree: done ({time.perf_counter()-t0:.2f}s) | "
          f"indeg0={float((in_deg==0).mean()):.3f} | max={int(in_deg.max())}")
    return in_deg


def compute_query_features(query_vecs: np.ndarray, flat_index: faiss.IndexFlatIP, top_n: int = 100):
    """Tính s1 và c_contrast = s1 - s100 cho mỗi query."""
    sims, _ = flat_index.search(query_vecs, top_n)
    s1        = sims[:, 0]
    s100      = sims[:, top_n - 1]
    c_contrast = s1 - s100
    return s1, c_contrast


# ─── XỬ LÝ TỪNG MODEL ────────────────────────────────────────────────────────

def process_model(model: str) -> tuple[pd.DataFrame, dict]:
    print(f"\n{'='*60}")
    print(f" MODEL: {model.upper()}")
    print(f"{'='*60}")

    gallery, queries = load_model_data(model)
    n_gallery, d  = gallery.shape
    n_queries     = queries.shape[0]
    print(f"  Gallery: {n_gallery} x {d}  |  Queries: {n_queries}")

    # 1. FlatIP index (exact top-k)
    flat_idx = faiss.IndexFlatIP(d)
    flat_idx.add(gallery)
    print(f"  [FlatIP] Searching exact top-{TOP_K}...")
    t0 = time.perf_counter()
    _, exact_nbrs = flat_idx.search(queries, TOP_K)      # (n_queries, 10)
    print(f"  [FlatIP] done ({time.perf_counter()-t0:.1f}s)")

    # 2. k-occurrence (query-centric)
    print(f"  [k-occ] Computing query-centric k-occurrence...")
    k_occ = compute_query_k_occurrence(queries, flat_idx, TOP_K)

    # 3. HNSW index
    print(f"  [HNSW] Building index (M={HNSW_M}, efC={HNSW_EF_CONSTRUCTION})...")
    t0 = time.perf_counter()
    hnsw_idx = faiss.IndexHNSWFlat(d, HNSW_M, faiss.METRIC_INNER_PRODUCT)
    hnsw_idx.hnsw.efConstruction = HNSW_EF_CONSTRUCTION
    hnsw_idx.add(gallery)
    hnsw_idx.hnsw.efSearch = HNSW_EF_SEARCH
    print(f"  [HNSW] built ({time.perf_counter()-t0:.1f}s)")

    print(f"  [HNSW] Searching top-{TOP_K}...")
    t0 = time.perf_counter()
    _, hnsw_nbrs = hnsw_idx.search(queries, TOP_K)       # (n_queries, 10)
    print(f"  [HNSW] done ({time.perf_counter()-t0:.1f}s)")

    # 4. In-degree Layer 0
    print(f"  [In-deg] Computing HNSW Layer-0 in-degree for {n_gallery} nodes...")
    in_deg = get_hnsw_layer0_indegree(hnsw_idx, n_gallery)

    # 5. Query features: s1, c_contrast
    print(f"  [Query] Computing s1, c_contrast (top-100)...")
    s1_arr, c_contrast_arr = compute_query_features(queries, flat_idx, top_n=100)

    # 6. Build neighbor-level DataFrame
    print(f"  [Build] Assembling neighbor-level rows...")
    rows = []
    for q_idx in range(n_queries):
        exact_set = set(int(x) for x in exact_nbrs[q_idx] if x >= 0)
        hnsw_set  = set(int(x) for x in hnsw_nbrs[q_idx]  if x >= 0)
        for rank, x_idx in enumerate(exact_nbrs[q_idx], start=1):
            if x_idx < 0:
                continue
            rows.append({
                "model":          model,
                "query_id":       int(q_idx),
                "neighbor_id":    int(x_idx),
                "rank":           int(rank),
                "missed":         int(x_idx not in hnsw_set),
                "k_occurrence":   int(k_occ[x_idx]),
                "in_degree_hnsw": int(in_deg[x_idx]),
                "s1":             float(s1_arr[q_idx]),
                "c_contrast":     float(c_contrast_arr[q_idx]),
            })

    df = pd.DataFrame(rows)
    overall_miss  = float(df["missed"].mean())
    retention_at10 = 1.0 - overall_miss
    antihub_gal   = int((k_occ == 0).sum())

    summary = {
        "n_rows":           len(df),
        "n_queries":        int(n_queries),
        "n_gallery":        int(n_gallery),
        "dim":              int(d),
        "overall_miss_rate":     overall_miss,
        "retention_at_10":       retention_at10,
        "antihub_gallery_count": antihub_gal,
        "antihub_gallery_ratio": float(antihub_gal / n_gallery),
        "k_occurrence_skewness": float(scipy.stats.skew(k_occ)),
        "in_degree_indeg0_ratio": float((in_deg == 0).mean()),
    }
    print(f"  Retention@10: {retention_at10:.4f}  |  Anti-hub ratio: {antihub_gal/n_gallery:.4f}")
    return df, summary


# ─── MAIN ────────────────────────────────────────────────────────────────────

def get_git_commit() -> str:
    try:
        import subprocess
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode().strip()
    except Exception:
        return "unknown"


def main():
    all_dfs = []
    all_summaries = {}

    for model in ["searle", "pic2word"]:
        df, summary = process_model(model)
        all_dfs.append(df)
        all_summaries[model] = summary

    combined = pd.concat(all_dfs, ignore_index=True)
    out_parquet = DATA_DIR / "neighbor_level_data.parquet"
    combined.to_parquet(out_parquet, index=False)
    print(f"\nSaved: {out_parquet}  ({len(combined):,} rows total)")

    # Metadata header bắt buộc theo mentor-audit-protocol P1
    output = {
        "metadata": {
            "module":       "module_a1_hubness",
            "step":         "step1_build_neighbor_dataset",
            "timestamp":    datetime.datetime.utcnow().isoformat() + "Z",
            "git_commit":   get_git_commit(),
            "random_seed":  42,
            "hardware": {
                "cpu":     os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
                "threads": faiss.omp_get_max_threads(),
            },
            "dataset":      "circo",
            "index_config": {
                "type":            "HNSWFlat",
                "M":               HNSW_M,
                "efSearch":        HNSW_EF_SEARCH,
                "efConstruction":  HNSW_EF_CONSTRUCTION,
            },
        },
        "results": all_summaries,
    }

    out_json = OUT_DIR / "step1_hnsw_indegree.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved: {out_json}")

    # In tóm tắt nhanh
    print("\n=== SUMMARY ===")
    for model, s in all_summaries.items():
        print(f"  {model.upper()}: Retention@10={s['retention_at_10']:.4f} | "
              f"Anti-hub={s['antihub_gallery_ratio']:.3f} | "
              f"InDeg0={s['in_degree_indeg0_ratio']:.3f}")


if __name__ == "__main__":
    main()
