"""
Bước 4: Can Thiệp Nhân Quả — Rank-Preserving Gallery Centering
===============================================================
Input : Feature files SEARLE & Pic2Word gallery/query
Output: results/step4_centering.json
        plots/fig3_centering_before_after.png

Lý thuyết:
  x_centered = x - mu  (mu = mean của gallery)
  q · (x - mu) = q·x - q·mu
  Vì q·mu là hằng số với mọi x → Rank của top-10 FlatIP KHÔNG ĐỔI.
  Nhưng cấu trúc đồ thị HNSW thay đổi → phân phối Hubness thay đổi.

Kết luận:
  Nếu Retention không tăng sau centering → Hubness-Retention là tương quan giả (spurious).
  Nếu Retention tăng vọt → Bằng chứng nhân quả ủng hộ giả thuyết Hubness.
"""

import os, sys, json, pickle, datetime, pathlib
import numpy as np
import faiss
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import skew, kurtosis

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = pathlib.Path(__file__).parent.parent / "results"
DATA_DIR    = pathlib.Path(__file__).parent.parent / "data"
PLOTS_DIR   = pathlib.Path(__file__).parent.parent / "plots"
PLOTS_DIR.mkdir(exist_ok=True)
ROOT = pathlib.Path(__file__).resolve().parents[4]

HNSW_M = 32
HNSW_EF_SEARCH = 128
HNSW_EF_CONSTRUCTION = 200
TOP_K = 10
VERIFY_SAMPLE_N = 50  # Số query ngẫu nhiên để verify rank invariance
RANDOM_SEED = 42

GALLERY_FEAT_PATHS = {
    "searle":   ROOT / "data" / "embeddings" / "searle"   / "circo_gallery.npy",
    "pic2word": ROOT / "data" / "embeddings" / "pic2word" / "circo_gallery.npy",
}
QUERY_FEAT_PATHS = {
    "searle":   DATA_DIR / "circo_1020_queries_searle.pkl",
    "pic2word": DATA_DIR / "circo_1020_queries_pic2word.pkl",
}
QUERY_VAL_PATHS = {
    "searle":   ROOT / "data" / "queries" / "searle"   / "circo_queries.pkl",
    "pic2word": ROOT / "data" / "queries" / "pic2word" / "circo_queries.pkl",
}


def compute_hubness_stats(gallery: np.ndarray, queries: np.ndarray, k: int = 10) -> dict:
    d = gallery.shape[1]
    flat = faiss.IndexFlatIP(d)
    flat.add(gallery)
    _, indices = flat.search(queries, k)
    n = gallery.shape[0]
    k_occ = np.bincount(indices.ravel(), minlength=n)
    antihub_ratio = float((k_occ == 0).mean())
    return {
        "skewness": float(skew(k_occ)),
        "kurtosis": float(kurtosis(k_occ, fisher=False)),
        "antihub_ratio": antihub_ratio,
        "max_hub": int(k_occ.max()),
    }


def compute_retention(gallery: np.ndarray, queries: np.ndarray, k: int = 10) -> float:
    d = gallery.shape[1]
    # Exact
    flat = faiss.IndexFlatIP(d)
    flat.add(gallery)
    _, exact_idx = flat.search(queries, k)
    # HNSW
    hnsw = faiss.IndexHNSWFlat(d, HNSW_M, faiss.METRIC_INNER_PRODUCT)
    hnsw.hnsw.efConstruction = HNSW_EF_CONSTRUCTION
    hnsw.add(gallery)
    hnsw.hnsw.efSearch = HNSW_EF_SEARCH
    _, hnsw_idx = hnsw.search(queries, k)
    # Retention = fraction of exact neighbors found by HNSW
    found = 0
    total = 0
    for q in range(queries.shape[0]):
        exact_set = set(exact_idx[q].tolist())
        hnsw_set  = set(hnsw_idx[q].tolist())
        found += len(exact_set & hnsw_set)
        total += k
    return found / total


def verify_rank_invariance(gallery_orig: np.ndarray, gallery_centered: np.ndarray,
                            queries: np.ndarray, n_sample: int = VERIFY_SAMPLE_N) -> bool:
    """Kiểm tra: Top-10 FlatIP không đổi sau centering (phải đúng về lý thuyết)."""
    rng = np.random.default_rng(RANDOM_SEED)
    sample_idx = rng.choice(queries.shape[0], size=n_sample, replace=False)
    d = gallery_orig.shape[1]

    flat_orig = faiss.IndexFlatIP(d)
    flat_orig.add(gallery_orig)
    _, idx_orig = flat_orig.search(queries[sample_idx], TOP_K)

    flat_cent = faiss.IndexFlatIP(d)
    flat_cent.add(gallery_centered)
    _, idx_cent = flat_cent.search(queries[sample_idx], TOP_K)

    match = np.all(idx_orig == idx_cent)
    print(f"  Rank invariance verified on {n_sample} queries: {'PASS' if match else 'FAIL'}")
    return bool(match)


def main():
    results = {}
    rng_seed = RANDOM_SEED

    for model in ["searle", "pic2word"]:
        print(f"\n[{model}] Loading features...")
        gallery_raw = np.load(GALLERY_FEAT_PATHS[model]).astype(np.float32)
        q_path = QUERY_FEAT_PATHS[model] if QUERY_FEAT_PATHS[model].exists() else QUERY_VAL_PATHS[model]
        print(f"[{model}] Using query file: {q_path.name}")
        with open(q_path, "rb") as f:
            q_data = pickle.load(f)
        queries_raw = q_data["query_features"].astype(np.float32)
        faiss.normalize_L2(gallery_raw)
        faiss.normalize_L2(queries_raw)

        # Centering. Keep the evaluated branch non-normalized so q·(x - mu)
        # differs from q·x only by the query-specific constant q·mu.
        mu = gallery_raw.mean(axis=0)
        gallery_cent = gallery_raw - mu

        print(f"[{model}] Verifying rank invariance (centered, no re-norm)...")
        rank_ok = verify_rank_invariance(gallery_raw, gallery_cent, queries_raw)

        print(f"[{model}] Computing BEFORE stats...")
        before_hub = compute_hubness_stats(gallery_raw, queries_raw)
        before_ret = compute_retention(gallery_raw, queries_raw)

        print(f"[{model}] Computing AFTER stats (centered, no re-norm)...")
        after_hub = compute_hubness_stats(gallery_cent, queries_raw)
        after_ret = compute_retention(gallery_cent, queries_raw)

        results[model] = {
            "rank_invariance_verified": rank_ok,
            "centering_variant": "subtract_gallery_mean_without_renormalization",
            "before": {**before_hub, "retention_at_10": before_ret},
            "after":  {**after_hub,  "retention_at_10": after_ret},
            "delta_retention": after_ret - before_ret,
            "delta_skewness":  after_hub["skewness"] - before_hub["skewness"],
        }

    # Vẽ biểu đồ before/after
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    metrics = ["skewness", "retention_at_10"]
    labels  = ["Hubness Skewness S_N10", "Retention@10"]

    for ax, metric, label in zip(axes, metrics, labels):
        models = ["searle", "pic2word"]
        before_vals = [results[m]["before"][metric] for m in models]
        after_vals  = [results[m]["after"][metric]  for m in models]
        x = np.arange(len(models))
        w = 0.35
        ax.bar(x - w/2, before_vals, w, label="Before Centering", color="#6B7280")
        ax.bar(x + w/2, after_vals,  w, label="After Centering",  color="#2563EB")
        ax.set_xticks(x)
        ax.set_xticklabels([m.upper() for m in models])
        ax.set_title(label)
        ax.legend()

    plt.suptitle("Rank-Preserving Centering Intervention: Before vs After", fontsize=13)
    plt.tight_layout()
    plot_path = PLOTS_DIR / "fig3_centering_before_after.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {plot_path}")

    causal_label = {}
    for model, res in results.items():
        dS = res["delta_skewness"]
        dR = res["delta_retention"]
        if dS < -0.5 and abs(dR) < 0.01:
            causal_label[model] = "spurious_correlation"
        elif dS < -0.5 and dR > 0.02:
            causal_label[model] = "causal_evidence_supports_hubness"
        else:
            causal_label[model] = "inconclusive"

    output = {
        "metadata": {
            "module": "module_a1_hubness",
            "step": "step4_centering_intervention",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "random_seed": RANDOM_SEED,
            "centering_variant": "subtract_gallery_mean_without_renormalization",
            "index_config": {
                "type": "HNSWFlat", "M": HNSW_M,
                "efSearch": HNSW_EF_SEARCH, "efConstruction": HNSW_EF_CONSTRUCTION,
            },
        },
        "results": results,
        "causal_label": causal_label,
    }
    out_path = RESULTS_DIR / "step4_centering.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
