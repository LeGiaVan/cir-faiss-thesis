"""
Bước 3: Hồi Quy Logistic Lồng Nhau (Nested Logistic Regression)
================================================================
Input : data/neighbor_level_data.parquet
Output: results/step3_nested_logit.json
        plots/fig2_logit_coef_path.png

Mục tiêu: Bóc tách vai trò của Hubness vs. Đặc tính Truy vấn
trong việc giải thích khoảng cách retention giữa SEARLE và Pic2Word.

Ba mô hình:
  M0: logit(p) = β0 + β_model · I(Pic2Word)
  M1: M0 + γ1·rank + γ2·log(1+N10) + γ3·log(1+InDegree)
  M2: M1 + θ1·s1(q) + θ2·c(q)

Sai số chuẩn cụm (Clustered SE) theo query_id.
"""

import os, sys, json, datetime, pathlib
import numpy as np
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[4] / 'src'))
from phase2.protocol import setup, metadata
CFG = setup()
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod import families

RESULTS_DIR = pathlib.Path(__file__).parent.parent / "results"
DATA_DIR    = pathlib.Path(__file__).parent.parent / "data"
PLOTS_DIR   = pathlib.Path(__file__).parent.parent / "plots"
PLOTS_DIR.mkdir(exist_ok=True)


def fit_model_with_clustered_se(df: pd.DataFrame, formula: str) -> dict:
    """Hồi quy Logistic với Clustered Standard Errors (GEE, independence working correlation)."""
    import statsmodels.formula.api as smf
    model = smf.gee(
        formula=formula,
        groups="query_id",
        data=df,
        family=families.Binomial(),
        cov_struct=sm.cov_struct.Independence(),
    )
    result = model.fit(maxiter=200, cov_type='robust')
    if not result.converged:
        raise RuntimeError('GEE did not converge')
    coefs = {}
    for name, coef, se, pval, ci_lo, ci_hi in zip(
        result.params.index,
        result.params.values,
        result.bse.values,
        result.pvalues.values,
        result.conf_int()[0].values,
        result.conf_int()[1].values,
    ):
        coefs[name] = {
            "coef": float(coef),
            "std_err": float(se),
            "p_value": float(pval),
            "ci_95_lower": float(ci_lo),
            "ci_95_upper": float(ci_hi),
        }
    diagnostics = {
        "converged": bool(result.converged),
        "n_observations": int(result.nobs),
        "n_clusters": int(df.query_id.nunique()),
        "scale": float(result.scale),
        "covariance": "robust_sandwich_query_cluster",
        "qic": None,
        "pseudo_r2_mcfadden": None,
        "pseudo_r2_note": "GEE is not ordinary maximum-likelihood logistic regression; use QIC when available.",
    }
    try:
        # Bernoulli scale is fixed at 1 for every model; compare QIC on common scale.
        qic, qicu = result.qic(scale=1.0)
        diagnostics["qic"] = float(qic)
        diagnostics["qicu"] = float(qicu)
    except Exception as exc:
        diagnostics["qic_note"] = f"QIC unavailable: {type(exc).__name__}: {exc}"
    return {"coefficients": coefs, **diagnostics}


def main():
    df = pd.read_parquet(DATA_DIR / "neighbor_level_data.parquet")
    df["is_pic2word"] = (df["model"] == "pic2word").astype(int)
    df["log_n10"] = np.log1p(df["k_occurrence"])
    df["log_indeg"] = np.log1p(df["in_degree_hnsw"])

    formulas = {
        "M0": "missed ~ is_pic2word",
        "M1": "missed ~ is_pic2word + rank + log_n10 + log_indeg",
        "M2": "missed ~ is_pic2word + rank + log_n10 + log_indeg + s1 + c_contrast",
    }

    model_results = {}
    beta_path = {}  # β_model across M0, M1, M2

    for mname, formula in formulas.items():
        print(f"Fitting {mname}: {formula}")
        res = fit_model_with_clustered_se(df, formula)
        model_results[mname] = res
        beta_path[mname] = res["coefficients"].get("is_pic2word", {}).get("coef", None)

    # Vẽ coefficient path
    fig, ax = plt.subplots(figsize=(7, 4))
    mnames = list(beta_path.keys())
    betas  = [beta_path[m] for m in mnames]
    ax.plot(mnames, betas, marker="o", linewidth=2, color="#2563EB")
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_ylabel("β_model (log-odds, Pic2Word vs SEARLE)")
    ax.set_title("Pic2Word coefficient across adjusted GEE models\nAssociation; coefficient changes do not identify causality")
    plt.tight_layout()
    plot_path = PLOTS_DIR / "fig2_logit_coef_path.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {plot_path}")

    output = {
        "metadata": {
            "module": "module_a1_hubness",
            "step": "step3_nested_logit",
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "method": "GEE_independence_clustered_by_query_id",
            "models": list(formulas.keys()),
        },
        "results": model_results,
        "beta_model_path": beta_path,
        "interpretation_note": (
            "Conditional associations, not a mediation or causal identification analysis. "
            "Coefficient changes across logistic models are not proportions of effect explained."
        ),
    }
    parent = json.loads((RESULTS_DIR/'step1_hnsw_indegree.json').read_text(encoding='utf-8'))['metadata']
    output['metadata'] = metadata('module_a1_hubness', inputs=[DATA_DIR/'neighbor_level_data.parquet',RESULTS_DIR/'step1_hnsw_indegree.json'],model=['searle','pic2word'],gallery_size=parent['gallery_size'],num_queries=int(df.query_id.nunique()),index_config=parent['index_config'],step='step3_nested_logit',method='GEE_independence_clustered_by_query_id',formulas=formulas,parent_metadata=parent)
    out_path = RESULTS_DIR / "step3_nested_logit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
