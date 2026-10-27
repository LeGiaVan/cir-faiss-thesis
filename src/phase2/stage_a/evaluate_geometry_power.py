import os
import sys
import json
import math
import pickle
import time
import numpy as np
import pandas as pd
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

def compute_relative_contrast(gallery, num_samples=None):
    from phase2.protocol import geometry
    r = geometry(gallery)
    return r['relative_contrast'], r['rc_mean_distance'], r['rc_mean_nearest_distance']

def compute_lid_levina_bickel(gallery, k=None, num_samples=None):
    from phase2.protocol import geometry
    r = geometry(gallery)
    return r['lid_mean'], r['lid_median']

def compute_hubness_skewness(gallery: np.ndarray, k: int = 10, batch_size: int = 3000):
    """
    Tính Skewness của k-occurrence.
    """
    N, d = gallery.shape
    index = faiss.IndexFlatIP(d)
    index.add(gallery)

    counts = np.zeros(N, dtype=np.int32)
    for i in range(0, N, batch_size):
        end_idx = min(i + batch_size, N)
        batch_q = gallery[i:end_idx]
        _, indices = index.search(batch_q, k + 1)
        for row_idx, self_idx in enumerate(range(i, end_idx)):
            row_nbrs = indices[row_idx]
            valid_nbrs = [idx for idx in row_nbrs if idx != self_idx][:k]
            for nbr in valid_nbrs:
                counts[nbr] += 1

    skewness = float(stats.skew(counts))
    anti_hub_ratio = float(np.mean(counts == 0) * 100.0)
    return skewness, anti_hub_ratio

def run_geometry_evaluation(base_dir: str):
    # Load sweep csv
    sweep_csv = os.path.join(base_dir, "data", "results", "consolidated_sweep.csv")
    df = pd.read_csv(sweep_csv)

    # Định nghĩa các tập dữ liệu và model cần khảo sát
    datasets_models = [
        ("searle", "circo", "data/embeddings/searle/circo_gallery.npy"),
        ("pic2word", "circo", "data/embeddings/pic2word/circo_gallery.npy"),
        ("clip4cir", "cirr", "data/embeddings/clip4cir/cirr_gallery.npy"),
        ("searle", "cirr", "data/embeddings/searle/cirr_gallery.npy"),
        ("pic2word", "cirr", "data/embeddings/pic2word/cirr_gallery.npy"),
        ("clip4cir", "fashioniq", "data/embeddings/clip4cir/fashioniq_dress_gallery.npy"),
        ("searle", "fashioniq", "data/embeddings/searle/fashioniq_dress_gallery.npy"),
        ("pic2word", "fashioniq", "data/embeddings/pic2word/fashioniq_dress_gallery.npy"),
    ]

    records = []

    for model, dataset, rel_path in datasets_models:
        full_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(full_path):
            print(f"Skipping {model} {dataset} (path not found: {full_path})")
            continue

        print(f"\nProcessing Geometry for {model.upper()} on {dataset.upper()}...")
        gal = np.load(full_path).astype(np.float32)
        faiss.normalize_L2(gal)
        N, d = gal.shape

        # 1. Tính Relative Contrast
        rc, _, _ = compute_relative_contrast(gal)
        # 2. Tính LID
        lid_mean, _ = compute_lid_levina_bickel(gal, k=20)
        # 3. Tính Hubness
        skewness, anti_hub_pct = compute_hubness_skewness(gal, k=10)

        # 4. Lấy HNSW Retention@10 (lấy config chuẩn M16_ef32 - cấu hình thách thức nhất)
        hnsw_row = df[(df["model"] == model) & (df["dataset"] == dataset) &
                      (df["index"] == "HNSWFlat") & (df["params"] == "M16_ef32")]

        if len(hnsw_row) == 0:
            # Thử tìm config HNSW bất kỳ
            hnsw_row = df[(df["model"] == model) & (df["dataset"] == dataset) &
                          (df["index"] == "HNSWFlat") & (df["role"].str.contains("ef32", na=False))]

        if len(hnsw_row) > 0:
            retention_hnsw = float(hnsw_row.iloc[0]["retention_at10"])
        else:
            retention_hnsw = None

        print(f"  N={N}, d={d} | RC={rc:.3f} | LID={lid_mean:.1f} | Skewness={skewness:.2f} | Anti-hub={anti_hub_pct:.1f}% | HNSW Retention={retention_hnsw}%")

        records.append({
            "model": model,
            "dataset": dataset,
            "N": N,
            "dimension": d,
            "relative_contrast": rc,
            "lid": lid_mean,
            "hubness_skewness": skewness,
            "anti_hub_ratio": anti_hub_pct,
            "hnsw_retention_m16_ef32": retention_hnsw
        })

    # Phân tích tương quan Spearman & Pearson
    valid_records = [r for r in records if r["hnsw_retention_m16_ef32"] is not None]
    rcs = [r["relative_contrast"] for r in valid_records]
    lids = [r["lid"] for r in valid_records]
    skews = [r["hubness_skewness"] for r in valid_records]
    rets = [r["hnsw_retention_m16_ef32"] for r in valid_records]

    def get_corrs(x, y):
        s_rho, s_p = stats.spearmanr(x, y)
        p_r, p_p = stats.pearsonr(x, y)
        return {
            "spearman_rho": float(s_rho),
            "spearman_p": float(s_p),
            "pearson_r": float(p_r),
            "pearson_p": float(p_p)
        }

    correlations = {
        "relative_contrast_vs_retention": get_corrs(rcs, rets),
        "lid_vs_retention": get_corrs(lids, rets),
        "hubness_skewness_vs_retention": get_corrs(skews, rets)
    }

    print("\n=======================================================")
    print("CORRELATION ANALYSIS WITH HNSW RETENTION@10:")
    print("=======================================================")
    for k, v in correlations.items():
        print(f"  {k:35s}: Spearman rho = {v['spearman_rho']:+.3f} (p={v['spearman_p']:.4f}) | Pearson r = {v['pearson_r']:+.3f}")
    print("=======================================================\n")

    return records, correlations

def plot_geometry_comparison(records: list, correlations: dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    valid = [r for r in records if r["hnsw_retention_m16_ef32"] is not None]
    rets = [r["hnsw_retention_m16_ef32"] for r in valid]

    metrics = [
        ("relative_contrast", "Relative Contrast (Beyer et al.)", "relative_contrast_vs_retention", axes[0], "blue"),
        ("lid", "Local Intrinsic Dim (LID Levina-Bickel)", "lid_vs_retention", axes[1], "green"),
        ("hubness_skewness", "Hubness Skewness (Radovanović et al.)", "hubness_skewness_vs_retention", axes[2], "red")
    ]

    for key, title, corr_key, ax, color in metrics:
        vals = [r[key] for r in valid]
        ax.scatter(vals, rets, color=color, s=80, alpha=0.85, edgecolors='black', zorder=3)

        # Add linear fit line
        m, b = np.polyfit(vals, rets, 1)
        x_pts = np.linspace(min(vals), max(vals), 50)
        ax.plot(x_pts, m*x_pts + b, linestyle='--', color=color, alpha=0.7, zorder=2)

        for r in valid:
            ax.annotate(f"{r['model'][:3]}-{r['dataset'][:4]}", (r[key], r['hnsw_retention_m16_ef32']),
                        fontsize=8, xytext=(4, 4), textcoords="offset points")

        rho = correlations[corr_key]["spearman_rho"]
        p_val = correlations[corr_key]["spearman_p"]

        ax.set_title(f"{title}\nSpearman ρ = {rho:+.3f} (p={p_val:.3f})", fontsize=11, fontweight='bold')
        ax.set_xlabel(title, fontsize=10)
        ax.set_ylabel("HNSWFlat Retention@10 (%)", fontsize=10)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, "geometry_metrics_vs_retention_scatter.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved geometry scatter plot: {plot_path}")

def generate_geometry_markdown_report(*args, **kwargs):
    raise RuntimeError('Legacy prose renderer retired. Run render_p0_reports.py for historical results or run_p1_reference.py --render-only for new reference results.')

def main():
    import runpy
    runner = runpy.run_path(str(PROTOCOL_ROOT / 'Phase_2_Q1_Journal/R2_Audit/scripts/run_p1_reference.py'))
    runner['run_modules'](['a5'])

if __name__ == "__main__":
    main()
