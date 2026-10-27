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
    name_to_idx = {str(name): idx for idx, name in enumerate(names)}

    return gallery, queries, target_ids, names, name_to_idx

def analyze_ivf_routing(gallery: np.ndarray, queries: np.ndarray, target_ids: list,
                       name_to_idx: dict, nlist: int = None,
                       nprobe_list = None):
    """
    Đo đạc chính xác sai số định tuyến của IVFFlat:
    - Huấn luyện coarse quantizer (K-means 351 tâm)
    - Xác định cụm của từng ảnh gallery
    - Với mỗi query, xếp hạng 351 tâm cụm
    - Đo Misrouting Rate theo nprobe
    - Đối chiếu trực tiếp với Recall Retention@10
    - Đo Routing Margin (biên định tuyến)
    """
    nlist = nlist or PROTOCOL["ivf"]["nlist"]
    nprobe_list = nprobe_list or PROTOCOL["ivf"]["nprobe_list"]
    N, d = gallery.shape
    num_queries = len(queries)

    # 1. Exact FlatIP search for ground truth ranking & retention baseline
    print("Computing exact FlatIP top-10...")
    flat_index = faiss.IndexFlatIP(d)
    flat_index.add(gallery)
    exact_dist, exact_idx = flat_index.search(queries, 10)

    # 2. Train Coarse Quantizer (K-Means)
    print(f"Training IVF coarse quantizer (nlist={nlist})...")
    quantizer = faiss.IndexFlatIP(d)
    kmeans = faiss.Kmeans(d, nlist, niter=25, verbose=False, spherical=True, seed=PROTOCOL["experiment_metadata"]["random_seed"])
    kmeans.train(gallery)
    centroids = kmeans.centroids  # shape: (nlist, d)
    faiss.normalize_L2(centroids)
    quantizer.add(centroids)

    # 3. Gán mỗi ảnh gallery vào cụm gần nhất
    print("Assigning each gallery vector to its closest centroid...")
    _, gallery_clusters = quantizer.search(gallery, 1)
    gallery_clusters = gallery_clusters.flatten()  # shape: (N,)

    # Phân phối kích thước cụm
    cluster_sizes = np.bincount(gallery_clusters, minlength=nlist)
    print(f"Centroid assignment done. Cluster sizes: Mean={np.mean(cluster_sizes):.1f}, Min={np.min(cluster_sizes)}, Max={np.max(cluster_sizes)}")

    # 4. Xếp hạng 351 cụm cho mỗi query
    print("Ranking all centroids for each query...")
    q_to_centroid_sims, q_ranked_centroids = quantizer.search(queries, nlist)

    # 5. Xây dựng index IVFFlat chuẩn để đo retention thực tế
    ivf_index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_INNER_PRODUCT)
    # quantizer is already trained
    ivf_index.is_trained = True
    ivf_index.add(gallery)

    results_by_nprobe = {}

    for nprobe in nprobe_list:
        nprobe_eff = min(nprobe, nlist)
        ivf_index.nprobe = nprobe_eff
        ivf_dist, ivf_idx = ivf_index.search(queries, 10)

        # Tính Recall Retention@10 thực tế
        retentions = [len(set(ivf_idx[i]).intersection(set(exact_idx[i, :10]))) / 10.0 * 100.0 for i in range(num_queries)]
        mean_retention = float(np.mean(retentions))

        # Kiểm tra Misrouting Rate trên Ground Truth Target
        # Một target bị coi là misrouted nếu cụm của nó KHÔNG nằm trong top-nprobe cụm của query
        target_misrouted_flags = []
        top10_exact_misrouted_flags = []
        routing_margins = []

        for q_i in range(num_queries):
            probed_clusters = set(q_ranked_centroids[q_i, :nprobe_eff])

            # Kiểm tra cho ground truth targets
            t_ids = target_ids[q_i]
            target_indices = [name_to_idx[str(tid)] for tid in t_ids if str(tid) in name_to_idx]
            if target_indices:
                t_clusters = [gallery_clusters[t_idx] for t_idx in target_indices]
                # Nếu không có cụm nào của target được probe -> query này bị rơi sai cụm
                any_probed = any(tc in probed_clusters for tc in t_clusters)
                target_misrouted_flags.append(not any_probed)

            # Kiểm tra cho top-10 exact candidates của FlatIP
            top10_cand_clusters = [gallery_clusters[c_idx] for c_idx in exact_idx[q_i, :10]]
            probed_cand_count = sum(1 for tc in top10_cand_clusters if tc in probed_clusters)
            top10_exact_misrouted_flags.append((10 - probed_cand_count) / 10.0 * 100.0)

            # Tính Routing Margin: khoảng cách điểm cosine từ query tới centroid thứ nprobe
            # so với centroid thứ nprobe+1
            if nprobe_eff < nlist:
                margin = float(q_to_centroid_sims[q_i, nprobe_eff - 1] - q_to_centroid_sims[q_i, nprobe_eff])
                routing_margins.append(margin)

        target_misrouting_rate = float(np.mean(target_misrouted_flags) * 100.0) if target_misrouted_flags else 0.0
        candidate_lost_rate = float(np.mean(top10_exact_misrouted_flags))
        mean_margin = float(np.mean(routing_margins)) if routing_margins else 0.0

        results_by_nprobe[nprobe] = {
            "nprobe": nprobe_eff,
            "retention_at_10": mean_retention,
            "candidate_lost_by_partition": candidate_lost_rate,
            "target_misrouting_rate": target_misrouting_rate,
            "retained_candidate_ratio": 100.0 - candidate_lost_rate,
            "mean_routing_margin": mean_margin
        }

        print(f"  nprobe={nprobe_eff:3d} | Retention@10: {mean_retention:6.2f}% | Candidate Covered: {100.0-candidate_lost_rate:6.2f}% | Target Misroute: {target_misrouting_rate:5.2f}% | Margin: {mean_margin:.6f}")

    return {
        "nlist": nlist,
        "cluster_size_stats": {
            "mean": float(np.mean(cluster_sizes)),
            "std": float(np.std(cluster_sizes)),
            "min": int(np.min(cluster_sizes)),
            "max": int(np.max(cluster_sizes))
        },
        "by_nprobe": results_by_nprobe
    }

def plot_ivf_routing_figures(all_results: dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    for model, res in all_results.items():
        by_np = res["by_nprobe"]
        nprobes = [v["nprobe"] for v in by_np.values()]
        retentions = [v["retention_at_10"] for v in by_np.values()]
        coverage = [v["retained_candidate_ratio"] for v in by_np.values()]

        color = '#337ab7' if model == 'searle' else '#d9534f'

        ax.plot(nprobes, retentions, marker='o', linewidth=2.5, color=color,
                label=f"{model.upper()} Recall Retention@10")
        ax.plot(nprobes, coverage, linestyle='--', linewidth=1.8, color=color, alpha=0.7,
                label=f"{model.upper()} Candidate Routing Coverage (%)")

    ax.axhline(95.0, color='green', linestyle=':', linewidth=2, label="Retention Target 95%")
    ax.set_xscale('log', base=2)
    ax.set_xlabel("nprobe (Number of Centroids Probed)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Percentage (%)", fontsize=11, fontweight='bold')
    ax.set_title("IVFFlat: Retention Loss Perfectly Explained by Routing Error (Partition Miss)", fontsize=12, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, "ivf_routing_curve.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved IVF routing plot: {plot_path}")

def generate_ivf_markdown_report(*args, **kwargs):
    raise RuntimeError('Legacy prose renderer retired. Run render_p0_reports.py for historical results or run_p1_reference.py --render-only for new reference results.')

def main():
    import runpy
    runner = runpy.run_path(str(PROTOCOL_ROOT / 'Phase_2_Q1_Journal/R2_Audit/scripts/run_p1_reference.py'))
    runner['run_modules'](['a3'])

if __name__ == "__main__":
    main()
