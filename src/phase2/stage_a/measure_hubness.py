import os
import sys
import json
import math
import pickle
import time
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

plt.switch_backend('Agg')

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import faiss

# P1_SHARED_ENTRYPOINT: all current runs use the same configuration and metadata.
from pathlib import Path
PROTOCOL_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROTOCOL_ROOT / 'src'))
from phase2.protocol import config as protocol_config
PROTOCOL = protocol_config()

def load_circo_data(model_name: str, base_dir: str):
    gal_path = os.path.join(base_dir, "data", "embeddings", model_name, "circo_gallery.npy")
    query_path = os.path.join(base_dir, "data", "queries", model_name, "circo_queries.pkl")
    names_path = os.path.join(base_dir, "data", "embeddings", model_name, "circo_names.npy")

    print(f"[{model_name.upper()}] Loading gallery from {gal_path}...")
    gallery = np.load(gal_path).astype(np.float32)
    faiss.normalize_L2(gallery)

    print(f"[{model_name.upper()}] Loading queries from {query_path}...")
    with open(query_path, "rb") as f:
        q_data = pickle.load(f)
    queries = q_data["query_features"].astype(np.float32)
    faiss.normalize_L2(queries)

    target_ids = q_data.get("target_ids", [])
    names = np.load(names_path)
    # Create name to index dictionary
    name_to_idx = {str(name): idx for idx, name in enumerate(names)}

    return gallery, queries, target_ids, names, name_to_idx

def compute_k_occurrence(gallery: np.ndarray, k: int = 10, batch_size: int = 2000):
    """
    Tính phân phối k-occurrence N_k(x) trên toàn bộ gallery.
    Tìm k láng giềng gần nhất cho mọi x trong gallery (bỏ chính nó).
    """
    N, d = gallery.shape
    index = faiss.IndexFlatIP(d)
    index.add(gallery)

    # Đếm số lần mỗi điểm xuất hiện trong top-k của điểm khác
    occurrence_counts = np.zeros(N, dtype=np.int32)

    print(f"Computing k-occurrence (k={k}) for {N} vectors in batches of {batch_size}...")
    t0 = time.perf_counter()

    for i in range(0, N, batch_size):
        end_idx = min(i + batch_size, N)
        batch_q = gallery[i:end_idx]
        # Search k+1 để loại bỏ chính nó (self-match)
        _, indices = index.search(batch_q, k + 1)

        # Lọc bỏ self-match
        # Thông thường cột 0 là chính nó, nhưng để an toàn lọc theo điều kiện != self_idx
        for row_idx, self_idx in enumerate(range(i, end_idx)):
            row_nbrs = indices[row_idx]
            valid_nbrs = [idx for idx in row_nbrs if idx != self_idx][:k]
            for nbr in valid_nbrs:
                occurrence_counts[nbr] += 1

        if (i // batch_size) % 15 == 0 or end_idx == N:
            print(f"  Processed {end_idx}/{N} vectors ({end_idx/N*100:.1f}%) in {time.perf_counter()-t0:.1f}s")

    t_total = time.perf_counter() - t0
    print(f"k-occurrence computation finished in {t_total:.2f}s.")
    return occurrence_counts

def analyze_hubness_distribution(counts: np.ndarray, k: int = 10):
    """
    Tính các chỉ số đo lường hubness chuẩn mực:
    - Skewness (S_{N_k})
    - Tỉ lệ Anti-hubs (N_k == 0)
    - Tỉ lệ Hubs (N_k >= 3*k)
    - Robin Hood index (độ bất bình đẳng)
    """
    N = len(counts)
    mean_val = float(np.mean(counts))
    std_val = float(np.std(counts))
    skewness = float(stats.skew(counts))
    kurtosis = float(stats.kurtosis(counts))

    anti_hubs = np.where(counts == 0)[0]
    anti_hub_ratio = float(len(anti_hubs) / N * 100.0)

    hubs = np.where(counts >= 3 * k)[0]
    hub_ratio = float(len(hubs) / N * 100.0)

    super_hubs = np.where(counts >= 5 * k)[0]
    super_hub_ratio = float(len(super_hubs) / N * 100.0)

    max_count = int(np.max(counts))

    # Robin Hood Index (HTI): tổng phần trăm kết nối mà top 10% điểm nắm giữ
    sorted_counts = np.sort(counts)[::-1]
    top_1_pct_links = float(np.sum(sorted_counts[:int(0.01 * N)]) / np.sum(counts) * 100.0)
    top_5_pct_links = float(np.sum(sorted_counts[:int(0.05 * N)]) / np.sum(counts) * 100.0)
    top_10_pct_links = float(np.sum(sorted_counts[:int(0.10 * N)]) / np.sum(counts) * 100.0)

    return {
        "mean": mean_val,
        "std": std_val,
        "skewness": skewness,
        "kurtosis": kurtosis,
        "anti_hub_count": int(len(anti_hubs)),
        "anti_hub_ratio": anti_hub_ratio,
        "hub_count": int(len(hubs)),
        "hub_ratio": hub_ratio,
        "super_hub_count": int(len(super_hubs)),
        "super_hub_ratio": super_hub_ratio,
        "max_occurrence": max_count,
        "top_1_pct_links": top_1_pct_links,
        "top_5_pct_links": top_5_pct_links,
        "top_10_pct_links": top_10_pct_links
    }

def evaluate_hnsw_by_target_hubness(gallery: np.ndarray, queries: np.ndarray,
                                   target_ids: list, name_to_idx: dict, counts: np.ndarray,
                                   k: int = 10, M: int = 32, efSearch: int = 64):
    """
    Đo Recall Retention@10 của HNSWFlat phân theo từng nhóm query:
    - Nhóm Anti-Hub Target (ảnh mục tiêu có N_k = 0)
    - Nhóm Normal Target (1 <= N_k < 30)
    - Nhóm Hub Target (N_k >= 30)
    """
    N, d = gallery.shape
    num_queries = len(queries)

    # 1. Exact FlatIP search
    flat_index = faiss.IndexFlatIP(d)
    flat_index.add(gallery)
    flat_dist, flat_idx = flat_index.search(queries, 10)

    # 2. HNSWFlat search (chạy 3 lần để lấy trung bình ổn định)
    hnsw_retentions_all = []
    print(f"Building and searching HNSWFlat (M={M}, efSearch={efSearch})...")
    hnsw_index = faiss.IndexHNSWFlat(d, M, faiss.METRIC_INNER_PRODUCT)
    hnsw_index.hnsw.efSearch = efSearch
    hnsw_index.add(gallery)
    hnsw_dist, hnsw_idx = hnsw_index.search(queries, 10)

    # 3. Phân loại từng query dựa trên ảnh mục tiêu
    query_categories = []
    query_retentions = []

    for q_i in range(num_queries):
        # Retention của query này
        exact_set = set(flat_idx[q_i, :10])
        hnsw_set = set(hnsw_idx[q_i, :10])
        retention = len(exact_set.intersection(hnsw_set)) / 10.0 * 100.0
        query_retentions.append(retention)

        # Lấy target IDs
        t_ids = target_ids[q_i]
        # Tìm chỉ số gallery của target
        target_indices = [name_to_idx[str(tid)] for tid in t_ids if str(tid) in name_to_idx]

        if not target_indices:
            query_categories.append("unknown")
            continue

        # Lấy k-occurrence của các target
        target_counts = [counts[idx] for idx in target_indices]
        # Phân loại theo min count (nếu có ít nhất 1 target là anti-hub)
        min_c = min(target_counts)
        avg_c = np.mean(target_counts)

        if min_c == 0:
            query_categories.append("anti_hub")
        elif avg_c >= 3 * k:
            query_categories.append("hub")
        else:
            query_categories.append("normal")

    # Thống kê retention theo nhóm
    group_stats = {}
    for cat in ["anti_hub", "normal", "hub"]:
        cat_retentions = [query_retentions[i] for i, c in enumerate(query_categories) if c == cat]
        if cat_retentions:
            group_stats[cat] = {
                "num_queries": len(cat_retentions),
                "mean_retention": float(np.mean(cat_retentions)),
                "std_retention": float(np.std(cat_retentions)),
                "median_retention": float(np.median(cat_retentions)),
                "raw_retentions": cat_retentions
            }
        else:
            group_stats[cat] = {
                "num_queries": 0,
                "mean_retention": 0.0,
                "std_retention": 0.0,
                "median_retention": 0.0,
                "raw_retentions": []
            }

    # Chạy kiểm định thống kê: Anti-hub vs Normal
    anti_ret = group_stats.get("anti_hub", {}).get("raw_retentions", [])
    norm_ret = group_stats.get("normal", {}).get("raw_retentions", [])

    if anti_ret and norm_ret:
        # Mann-Whitney U test (non-parametric)
        u_stat, p_val = stats.mannwhitneyu(anti_ret, norm_ret, alternative='less')
    else:
        u_stat, p_val = 0.0, 1.0

    group_stats["statistical_test"] = {
        "test_name": "Mann-Whitney U (Anti-hub vs Normal)",
        "alternative": "Retention(Anti-hub) < Retention(Normal)",
        "u_statistic": float(u_stat),
        "p_value": float(p_val),
        "is_significant_005": bool(p_val < 0.05),
        "is_significant_001": bool(p_val < 0.01)
    }

    group_stats["overall_retention"] = float(np.mean(query_retentions))
    return group_stats

def plot_hubness_results(all_results: dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    # 1. Plot Histogram of k-occurrence distributions
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for idx, model in enumerate(["searle", "pic2word"]):
        if model not in all_results:
            continue
        ax = axes[idx]
        counts = np.array(all_results[model]["raw_counts"])
        stats_data = all_results[model]["distribution"]

        # Plot counts histogram (log scale y-axis for heavy tail)
        # Limit x to 100 for visibility
        ax.hist(counts, bins=np.arange(0, 105, 2), color='#337ab7' if model=='searle' else '#d9534f',
                alpha=0.7, edgecolor='black', log=True)

        ax.axvline(stats_data["mean"], color='green', linestyle='--', linewidth=2,
                   label=f"Mean = {stats_data['mean']:.1f}")
        ax.axvline(30, color='darkorange', linestyle=':', linewidth=2,
                   label="Hub Threshold (N_k ≥ 30)")

        ax.set_title(f"{model.upper()} CIRCO (k=10)\nSkewness = {stats_data['skewness']:.2f} | Anti-hubs = {stats_data['anti_hub_ratio']:.1f}%",
                     fontsize=12, fontweight='bold')
        ax.set_xlabel("k-occurrence N_10(x)", fontsize=11)
        ax.set_ylabel("Number of Vectors (Log Scale)", fontsize=11)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    hist_path = os.path.join(output_dir, "hubness_distribution_comparison.png")
    plt.savefig(hist_path, dpi=300)
    plt.close()
    print(f"Saved histogram plot: {hist_path}")

    # 2. Box plot / Bar chart of Retention by Target Category
    fig, ax = plt.subplots(figsize=(8, 5))
    models = ["searle", "pic2word"]
    categories = ["anti_hub", "normal", "hub"]
    bar_width = 0.35
    x = np.arange(len(categories))

    for i, model in enumerate(models):
        if model not in all_results:
            continue
        ret_data = all_results[model]["hnsw_breakdown"]
        means = [ret_data[c]["mean_retention"] for c in categories]
        stds = [ret_data[c]["std_retention"] for c in categories]
        counts_n = [ret_data[c]["num_queries"] for c in categories]

        offset = (i - 0.5) * bar_width
        rects = ax.bar(x + offset, means, bar_width, yerr=stds, capsize=4,
                       label=f"{model.upper()} (Overall: {ret_data['overall_retention']:.1f}%)",
                       color='#337ab7' if model=='searle' else '#d9534f', alpha=0.85, edgecolor='black')

        for rect, mean_val, cnt in zip(rects, means, counts_n):
            ax.annotate(f"{mean_val:.1f}%\n(n={cnt})",
                        xy=(rect.get_x() + rect.get_width() / 2, mean_val / 2),
                        ha='center', va='center', fontsize=9, fontweight='bold', color='white')

    ax.set_ylabel("HNSWFlat Recall Retention@10 (%)", fontsize=11, fontweight='bold')
    ax.set_title("HNSWFlat Retention Disaggregated by Ground Truth Hubness Group", fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(["Anti-Hub Targets\n(N_10 = 0)", "Normal Targets\n(1 ≤ N_10 < 30)", "Hub Targets\n(N_10 ≥ 30)"], fontsize=11)
    ax.set_ylim(0, 115)
    ax.legend(fontsize=10, loc="lower right")
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    breakdown_path = os.path.join(output_dir, "hnsw_retention_by_target_hubness.png")
    plt.savefig(breakdown_path, dpi=300)
    plt.close()
    print(f"Saved retention breakdown plot: {breakdown_path}")

def generate_hubness_markdown_report(*args, **kwargs):
    raise RuntimeError('Legacy prose renderer retired. Run render_p0_reports.py for historical results or run_p1_reference.py --render-only for new reference results.')

def main():
    import runpy
    runpy.run_path(str(PROTOCOL_ROOT / 'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/run_reference_audit.py'), run_name='__main__')

if __name__ == "__main__":
    main()
