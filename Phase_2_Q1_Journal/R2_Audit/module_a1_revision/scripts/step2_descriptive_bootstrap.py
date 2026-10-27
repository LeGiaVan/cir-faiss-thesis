"""
Bước 2: Phân Tích Mô Tả & Khoảng Tin Cậy Bootstrap 95%
=========================================================
Input : data/neighbor_level_data.parquet (từ step1)
Output: results/step2_bootstrap_ci.json
        plots/fig1_miss_rate_by_k_group.png

Quy tắc bắt buộc (mentor-audit-protocol):
  - Dùng Bootstrap 95% CI (1.000 lượt), lấy mẫu theo cụm query_id.
  - KHÔNG dùng ±1 std (vì retention bị chặn [0,100]).
  - Thanh sai số không được vượt [0%, 100%].
"""

import os, sys, json, datetime, pathlib
import numpy as np
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / 'src'))
from phase2.protocol import setup, metadata, write_json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = pathlib.Path(__file__).parent.parent / "results"
DATA_DIR    = pathlib.Path(__file__).parent.parent / "data"
PLOTS_DIR   = pathlib.Path(__file__).parent.parent / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

CFG = setup()
N_BOOTSTRAP = CFG['audit']['bootstrap_replicates']
RANDOM_SEED = CFG['experiment_metadata']['random_seed']
rng = np.random.default_rng(RANDOM_SEED)

K_GROUPS = [
    ("Anti-hub (N10=0)",  lambda x: x == 0),
    ("N10 = 1-4",        lambda x: (x >= 1)  & (x <= 4)),
    ("N10 = 5-9",        lambda x: (x >= 5)  & (x <= 9)),
    ("N10 = 10-29",      lambda x: (x >= 10) & (x <= 29)),
    ("Hub (N10≥30)",     lambda x: x >= 30),
]


def clustered_bootstrap_miss_rate(df: pd.DataFrame, n_boot: int = N_BOOTSTRAP):
    """Bootstrap theo cụm query_id → 95% CI của miss_rate."""
    per_query = (
        df.groupby("query_id")["missed"]
        .agg(missed_sum="sum", n_obs="count")
        .reset_index(drop=True)
    )
    missed_sum = per_query["missed_sum"].to_numpy(dtype=np.float64)
    n_obs = per_query["n_obs"].to_numpy(dtype=np.float64)
    sampled = rng.integers(0, len(per_query), size=(n_boot, len(per_query)))
    boot_means = missed_sum[sampled].sum(axis=1) / n_obs[sampled].sum(axis=1)
    return {
        "miss_rate": float(df["missed"].mean()),
        "ci_lower": float(np.percentile(boot_means, 2.5)),
        "ci_upper": float(np.percentile(boot_means, 97.5)),
        "n_observations": int(len(df)),
        "n_queries": int(df['query_id'].nunique()),
        "n_unique_neighbors": int(df['neighbor_id'].nunique()),
        "n_missed": int(df['missed'].sum()),
        "boundary_degenerate": bool(df['missed'].nunique() == 1),
        "ci_caution": ("Empirical cluster bootstrap is degenerate with constant outcomes; not evidence of zero uncertainty in the population." if df['missed'].nunique() == 1 else None),
    }


def main():
    df = pd.read_parquet(DATA_DIR / "neighbor_level_data.parquet")
    results = {}

    for model in ["searle", "pic2word"]:
        mdf = df[df["model"] == model].copy()
        results[model] = {}
        for label, cond in K_GROUPS:
            subset = mdf[cond(mdf["k_occurrence"])]
            if len(subset) == 0:
                results[model][label] = None
                continue
            results[model][label] = clustered_bootstrap_miss_rate(subset)

    degree_results = {}
    bins = CFG['audit']['graph_degree_bins']
    for model in ['searle', 'pic2word']:
        mdf = df[df['model'] == model]
        degree_results[model] = {}
        for i, lower in enumerate(bins):
            upper = bins[i + 1] if i + 1 < len(bins) else None
            label = f'{lower}–{upper-1}' if upper else f'>={lower}'
            subset = mdf[(mdf.in_degree_hnsw >= lower) & ((mdf.in_degree_hnsw < upper) if upper else True)]
            degree_results[model][label] = clustered_bootstrap_miss_rate(subset) if len(subset) else None

    # Vẽ biểu đồ
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    group_labels = [g[0] for g in K_GROUPS]
    colors = {"searle": "#2563EB", "pic2word": "#DC2626"}

    for ax, model in zip(axes, ["searle", "pic2word"]):
        miss_rates = [results[model][g]["miss_rate"] * 100 if results[model][g] else 0 for g in group_labels]
        ci_lowers  = [results[model][g]["ci_lower"]  * 100 if results[model][g] else 0 for g in group_labels]
        ci_uppers  = [results[model][g]["ci_upper"]  * 100 if results[model][g] else 0 for g in group_labels]
        yerr_low  = [m - l for m, l in zip(miss_rates, ci_lowers)]
        yerr_high = [u - m for m, u in zip(miss_rates, ci_uppers)]

        ax.bar(group_labels, miss_rates, color=colors[model], alpha=0.75, label=model.upper())
        ax.errorbar(group_labels, miss_rates,
                    yerr=[yerr_low, yerr_high],
                    fmt="none", color="black", capsize=4, linewidth=1.5)
        ax.set_title(f"{model.upper()} — Miss Rate by k-Occurrence Group")
        ax.set_ylabel("Miss Rate (%) [100% - Retention@10]")
        ax.set_ylim(0, 100)
        ax.tick_params(axis="x", rotation=20)

    plt.tight_layout()
    plot_path = PLOTS_DIR / "fig1_miss_rate_by_k_group.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {plot_path}")

    output = {
        "metadata": {
            "module": "module_a1_hubness",
            "step": "step2_bootstrap_ci",
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "random_seed": RANDOM_SEED,
            "n_bootstrap": N_BOOTSTRAP,
            "bootstrap_method": "clustered_by_query_id",
            "ci_level": 0.95,
        },
        "results": results,
        "indegree_results": degree_results,
    }
    parent = json.loads((RESULTS_DIR / 'step1_hnsw_indegree.json').read_text(encoding='utf-8'))['metadata']
    output['metadata'] = metadata('module_a1_hubness', inputs=[DATA_DIR/'neighbor_level_data.parquet',RESULTS_DIR/'step1_hnsw_indegree.json'], model=list(results), gallery_size=parent['gallery_size'],num_queries=int(df.query_id.nunique()),index_config=parent['index_config'],step='step2_bootstrap_ci',n_bootstrap=N_BOOTSTRAP,bootstrap_method='clustered_by_query_id_within_group',ci_level=.95,parent_metadata=parent)
    out_path = RESULTS_DIR / "step2_bootstrap_ci.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
