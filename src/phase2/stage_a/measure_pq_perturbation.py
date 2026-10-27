import os
import sys
import json
import math
import pickle
import time
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

# Ensure matplotlib uses a non-interactive backend
plt.switch_backend('Agg')

# Fix stdout encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import faiss

# P1_SHARED_ENTRYPOINT: all current runs use the same configuration and metadata.
from pathlib import Path
PROTOCOL_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROTOCOL_ROOT / 'src'))
from phase2.protocol import config as protocol_config
PROTOCOL = protocol_config()

def load_data(model_name: str, base_dir: str):
    """
    Tải gallery embedding và queries cho model đã chọn trên CIRCO.
    """
    gal_path = os.path.join(base_dir, "data", "embeddings", model_name, "circo_gallery.npy")
    query_path = os.path.join(base_dir, "data", "queries", model_name, "circo_queries.pkl")
    names_path = os.path.join(base_dir, "data", "embeddings", model_name, "circo_names.npy")

    print(f"[{model_name.upper()}] Loading gallery from {gal_path}...")
    gallery = np.load(gal_path).astype(np.float32)
    # L2 normalize
    faiss.normalize_L2(gallery)

    print(f"[{model_name.upper()}] Loading queries from {query_path}...")
    with open(query_path, "rb") as f:
        q_data = pickle.load(f)
    queries = q_data["query_features"].astype(np.float32)
    faiss.normalize_L2(queries)

    target_ids = q_data.get("target_ids", [])
    names = np.load(names_path)

    return gallery, queries, target_ids, names

def run_pq_perturbation_analysis(model_name: str, gallery: np.ndarray, queries: np.ndarray,
                                m_list=None, nlist=None, nprobe=None):
    """
    Thực hiện phân tích nhiễu điểm số delta thực nghiệm của IVFPQ đối chiếu với Cauchy-Schwarz.
    """
    m_list = m_list or PROTOCOL['ivfpq']['audit_m_list']
    nlist = nlist or PROTOCOL['ivfpq']['nlist']
    nprobe = nprobe or PROTOCOL['ivfpq']['default_nprobe']
    N, d = gallery.shape
    num_queries = len(queries)
    sqrt_d = math.sqrt(d)

    print(f"\n=======================================================")
    print(f"MODEL: {model_name.upper()} (N={N}, Dimension d={d}, sqrt(d)={sqrt_d:.2f})")
    print(f"=======================================================")

    # 1. Tìm exact top-k bằng FlatIP để đo rank-10/11 score gap
    print("-> Computing exact FlatIP top-50 search for true score gaps...")
    flat_index = faiss.IndexFlatIP(d)
    flat_index.add(gallery)
    true_distances, true_indices = flat_index.search(queries, 50)

    # Rank-10/11 gap: difference between 10th score (index 9) and 11th score (index 10)
    # Vì distances được sắp xếp giảm dần theo inner product
    rank_10_scores = true_distances[:, 9]
    rank_11_scores = true_distances[:, 10]
    rank_10_11_gaps = rank_10_scores - rank_11_scores
    mean_gap = float(np.mean(rank_10_11_gaps))
    median_gap = float(np.median(rank_10_11_gaps))
    print(f"   True rank-10/11 Score Gap: Mean={mean_gap:.6f}, Median={median_gap:.6f}")

    results_by_m = {}

    for m in m_list:
        print(f"\n--- Testing IVFPQ with m={m} (d/m = {d//m} dims/sub-quantizer) ---")
        quantizer = faiss.IndexFlatIP(d)
        index = faiss.IndexIVFPQ(quantizer, d, nlist, m, PROTOCOL["ivfpq"]["nbits"], faiss.METRIC_INNER_PRODUCT)
        index.cp.seed = PROTOCOL["experiment_metadata"]["random_seed"]
        index.pq.cp.seed = PROTOCOL["experiment_metadata"]["random_seed"]
        index.nprobe = nprobe

        # Train & Add
        t0 = time.perf_counter()
        index.train(gallery)
        t_train = time.perf_counter() - t0

        t0 = time.perf_counter()
        index.add(gallery)
        t_add = time.perf_counter() - t0
        print(f"   Trained in {t_train:.2f}s, Added in {t_add:.2f}s")

        # Đánh giá Recall Retention@10 thực tế
        pq_distances, pq_indices = index.search(queries, 10)
        # Tính retention: % các ứng viên top-10 của FlatIP vẫn xuất hiện trong top-10 của IVFPQ
        retention_counts = [len(set(pq_indices[i]).intersection(set(true_indices[i, :10]))) for i in range(num_queries)]
        mean_retention_10 = float(np.mean(retention_counts) / 10.0 * 100.0)
        print(f"   Actual Recall Retention@10: {mean_retention_10:.2f}%")

        # Trích xuất vector tái tạo x_hat
        print("   Reconstructing quantized gallery vectors via index.reconstruct_n()...")
        index.make_direct_map()
        t0 = time.perf_counter()
        gallery_hat = index.reconstruct_n(0, N)
        t_recon = time.perf_counter() - t0
        print(f"   Reconstructed {N} vectors in {t_recon:.2f}s")

        # 2. Đo sai số tái tạo Euclidean: e = x - x_hat
        E = gallery - gallery_hat
        norm_e = np.linalg.norm(E, axis=1)
        mean_norm_e = float(np.mean(norm_e))
        std_norm_e = float(np.std(norm_e))
        rms_norm_e = float(np.sqrt(np.mean(norm_e**2)))
        print(f"   Euclidean Reconstruction Error ||x - x^||_2:")
        print(f"     Mean = {mean_norm_e:.4f} +/- {std_norm_e:.4f}, RMS = {rms_norm_e:.4f}")

        # Dự báo lý thuyết
        pred_rms_delta = rms_norm_e / sqrt_d
        pred_mean_delta = math.sqrt(2.0 / math.pi) * pred_rms_delta
        print(f"   Theoretical Prediction (via High-dim Orthogonality):")
        print(f"     Pred RMS(Delta_s)  = {rms_norm_e:.4f} / {sqrt_d:.2f} = {pred_rms_delta:.6f}")
        print(f"     Pred Mean(Delta_s) = sqrt(2/pi) * RMS = {pred_mean_delta:.6f}")

        # 3. Đo thực nghiệm Delta_s trên các tập ứng viên
        # Tập A: Top-10 ứng viên thật của mỗi query (vùng nhạy cảm nhất)
        top10_deltas = []
        for i in range(num_queries):
            cands = true_indices[i, :10]
            # True scores vs Reconstructed scores
            true_s = true_distances[i, :10]
            recon_s = np.dot(gallery_hat[cands], queries[i])
            delta_s = np.abs(true_s - recon_s)
            top10_deltas.extend(delta_s.tolist())
        top10_deltas = np.array(top10_deltas, dtype=np.float32)

        # Tập B: Top-100 ứng viên thật
        top100_deltas = []
        # Chạy top-100 search
        true_dist_100, true_idx_100 = flat_index.search(queries, 100)
        for i in range(num_queries):
            cands = true_idx_100[i]
            true_s = true_dist_100[i]
            recon_s = np.dot(gallery_hat[cands], queries[i])
            delta_s = np.abs(true_s - recon_s)
            top100_deltas.extend(delta_s.tolist())
        top100_deltas = np.array(top100_deltas, dtype=np.float32)

        # Tập C: 100,000 cặp ngẫu nhiên (Query, Gallery)
        np.random.seed(42)
        rand_q_idx = np.random.randint(0, num_queries, size=100000)
        rand_g_idx = np.random.randint(0, N, size=100000)
        rand_true_s = np.sum(queries[rand_q_idx] * gallery[rand_g_idx], axis=1)
        rand_recon_s = np.sum(queries[rand_q_idx] * gallery_hat[rand_g_idx], axis=1)
        rand_deltas = np.abs(rand_true_s - rand_recon_s)

        # Tính thống kê thực nghiệm
        def calc_stats(arr):
            return {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "rms": float(np.sqrt(np.mean(arr**2))),
                "median": float(np.median(arr)),
                "p90": float(np.percentile(arr, 90)),
                "p95": float(np.percentile(arr, 95)),
                "p99": float(np.percentile(arr, 99)),
                "max": float(np.max(arr))
            }

        stats_top10 = calc_stats(top10_deltas)
        stats_top100 = calc_stats(top100_deltas)
        stats_random = calc_stats(rand_deltas)

        # So sánh Tỉ số cũ (Cauchy-Schwarz) vs Tỉ số thực tế
        old_ratio = mean_norm_e / mean_gap
        emp_ratio_mean = stats_top10["mean"] / mean_gap
        emp_ratio_rms = stats_top10["rms"] / mean_gap
        emp_ratio_p95 = stats_top10["p95"] / mean_gap
        inflation_factor = old_ratio / emp_ratio_rms

        print(f"\n   === EMPIRICAL RESULTS FOR m={m} ===")
        print(f"   Top-10 Candidates Score Perturbation |q · (x - x^)|:")
        print(f"     Empirical Mean   : {stats_top10['mean']:.6f}  (Predicted: {pred_mean_delta:.6f})")
        print(f"     Empirical RMS    : {stats_top10['rms']:.6f}  (Predicted: {pred_rms_delta:.6f})")
        print(f"     Empirical Median : {stats_top10['median']:.6f}")
        print(f"     Empirical 95th percentile (not CI) : {stats_top10['p95']:.6f}")
        print(f"   -------------------------------------------------")
        print(f"   COMPARISON AGAINST SCORE GAP ({mean_gap:.6f}):")
        print(f"     Cauchy-Schwarz Bound Ratio (ICRCV) : {old_ratio:.1f}x")
        print(f"     Empirical RMS Perturbation Ratio   : {emp_ratio_rms:.1f}x")
        print(f"     Empirical Mean Perturbation Ratio  : {emp_ratio_mean:.1f}x")
        print(f"     Empirical 95th Percentile Ratio    : {emp_ratio_p95:.1f}x")
        print(f"     Inflation Factor (Old / RMS)       : {inflation_factor:.2f}x (Theory sqrt(d) = {sqrt_d:.2f})")
        print(f"   =================================================\n")

        results_by_m[m] = {
            "m": m,
            "subspace_dim": d // m,
            "retention_at_10": mean_retention_10,
            "norm_e": {
                "mean": mean_norm_e,
                "std": std_norm_e,
                "rms": rms_norm_e
            },
            "theoretical_prediction": {
                "sqrt_d": sqrt_d,
                "pred_rms": pred_rms_delta,
                "pred_mean": pred_mean_delta
            },
            "score_gap": {
                "mean": mean_gap,
                "median": median_gap
            },
            "stats_top10": stats_top10,
            "stats_top100": stats_top100,
            "stats_random": stats_random,
            "ratios": {
                "cauchy_schwarz_ratio": old_ratio,
                "empirical_mean_ratio": emp_ratio_mean,
                "empirical_rms_ratio": emp_ratio_rms,
                "empirical_p95_ratio": emp_ratio_p95,
                "inflation_factor": inflation_factor
            },
            "sample_arrays": {
                "top10_deltas": top10_deltas[:2000].tolist(),
                "rand_deltas": rand_deltas[:2000].tolist()
            }
        }

    return results_by_m

def plot_perturbation_figures(all_results: dict, output_dir: str):
    """
    Vẽ các biểu đồ chuẩn mực khoa học phục vụ bài báo Journal và Báo cáo Giai đoạn A.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Figure: Distribution Histogram vs Theoretical Half-Normal
    for model_name, m_data in all_results.items():
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        for idx, m in enumerate([8, 16]):
            if m not in m_data:
                continue
            ax = axes[idx]
            res = m_data[m]
            top10_vals = np.array(res["sample_arrays"]["top10_deltas"])
            gap = res["score_gap"]["mean"]
            rms = res["stats_top10"]["rms"]
            mean_val = res["stats_top10"]["mean"]
            pred_rms = res["theoretical_prediction"]["pred_rms"]
            old_bound = res["norm_e"]["mean"]

            # Histogram of empirical deltas
            counts, bins, _ = ax.hist(top10_vals, bins=50, density=True, alpha=0.6,
                                     color="#2b5c8f", edgecolor="black", label="Empirical |q · (x - x^)|")

            # Overlay Theoretical Half-Normal curve
            x_pts = np.linspace(0, max(top10_vals), 200)
            half_norm_pdf = stats.halfnorm.pdf(x_pts, scale=pred_rms)
            ax.plot(x_pts, half_norm_pdf, 'r--', linewidth=2.5,
                    label=f"Theory Half-Normal (scale=||e||/√d = {pred_rms:.4f})")

            # Reference lines
            ax.axvline(mean_val, color='green', linestyle='-', linewidth=2,
                       label=f"Empirical Mean = {mean_val:.4f} ({mean_val/gap:.1f}x gap)")
            ax.axvline(rms, color='darkorange', linestyle=':', linewidth=2,
                       label=f"Empirical RMS = {rms:.4f} ({rms/gap:.1f}x gap)")
            ax.axvline(gap, color='purple', linestyle='-.', linewidth=2,
                       label=f"Rank-10/11 Gap = {gap:.5f}")

            ax.set_title(f"{model_name.upper()} CIRCO (m={m}): Actual Perturbation vs Gap", fontsize=12, fontweight='bold')
            ax.set_xlabel("Score Perturbation |q · (x - x^)|", fontsize=11)
            ax.set_ylabel("Probability Density", fontsize=11)
            ax.legend(loc="upper right", fontsize=9)
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"{model_name}_perturbation_distribution.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()
        print(f"Saved distribution plot: {plot_path}")

    # 2. Figure: Comparison Bar Chart (Cauchy-Schwarz vs Empirical vs Score Gap)
    fig, ax = plt.subplots(figsize=(10, 6))

    categories = []
    old_ratios = []
    rms_ratios = []
    mean_ratios = []

    for model_name, m_data in all_results.items():
        for m in [8, 16]:
            if m in m_data:
                categories.append(f"{model_name.upper()}\nm={m}")
                old_ratios.append(m_data[m]["ratios"]["cauchy_schwarz_ratio"])
                rms_ratios.append(m_data[m]["ratios"]["empirical_rms_ratio"])
                mean_ratios.append(m_data[m]["ratios"]["empirical_mean_ratio"])

    x = np.arange(len(categories))
    width = 0.25

    rects1 = ax.bar(x - width, old_ratios, width, label='ICRCV Cauchy-Schwarz Bound (|q·e| ≤ ||e||)', color='#d9534f', edgecolor='black')
    rects2 = ax.bar(x, rms_ratios, width, label='Empirical RMS Perturbation (|q·e|_RMS)', color='#f0ad4e', edgecolor='black')
    rects3 = ax.bar(x + width, mean_ratios, width, label='Empirical Mean Perturbation (E[|q·e|])', color='#5cb85c', edgecolor='black')

    ax.set_ylabel('Ratio to Rank-10/11 Score Gap (Times larger than gap)', fontsize=12, fontweight='bold')
    ax.set_title('Resolving the Overestimation: Cauchy-Schwarz (439-470x) vs True Empirical Noise (15-19x)', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    # Add values on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}x',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9, fontweight='bold')

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)

    # Reference line at ratio = 1 (boundary for ranking preservation)
    ax.axhline(1.0, color='red', linestyle='--', linewidth=1.5, label='Safety Margin (Ratio = 1x)')

    plt.tight_layout()
    bar_path = os.path.join(output_dir, "ratio_comparison_cauchy_vs_empirical.png")
    plt.savefig(bar_path, dpi=300)
    plt.close()
    print(f"Saved bar comparison plot: {bar_path}")

def generate_markdown_report(*args, **kwargs):
    raise RuntimeError('Legacy prose renderer retired. Run render_p0_reports.py for historical results or run_p1_reference.py --render-only for new reference results.')

def main():
    import runpy
    runner = runpy.run_path(str(PROTOCOL_ROOT / 'Phase_2_Q1_Journal/R2_Audit/scripts/run_p1_reference.py'))
    runner['run_modules'](['a2'])

if __name__ == "__main__":
    main()
