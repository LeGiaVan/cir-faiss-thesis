import os
import sys
import json
import time
import pickle
import argparse
import numpy as np
import pandas as pd
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

def generate_or_load_distractors(distractor_path: str, dimension: int, num_distractors: int, seed: int = 42):
    """
    Tải hoặc tạo mảng vector distractor (chuẩn hoá L2) để benchmark quy mô 1M.
    Nếu file đã tồn tại, load bằng memmap để tiết kiệm RAM.
    """
    if os.path.exists(distractor_path):
        print(f"Loading existing distractors from {distractor_path}...")
        distractors = np.load(distractor_path, mmap_mode='r')
        if distractors.shape[0] >= num_distractors and distractors.shape[1] == dimension:
            return distractors[:num_distractors]
        else:
            print(f"Existing file shape {distractors.shape} does not match required ({num_distractors}, {dimension}). Re-generating...")

    print(f"Generating {num_distractors} synthetic distractors in {dimension}-d (Spherical Random / Gaussian)...")
    np.random.seed(seed)
    os.makedirs(os.path.dirname(distractor_path), exist_ok=True)

    # Sinh theo lô 100.000 để tránh tràn RAM
    batch_sz = 100000
    fp = np.memmap(distractor_path, dtype='float32', mode='w+', shape=(num_distractors, dimension))

    for start_idx in range(0, num_distractors, batch_sz):
        end_idx = min(start_idx + batch_sz, num_distractors)
        cur_sz = end_idx - start_idx
        batch_vecs = np.random.randn(cur_sz, dimension).astype(np.float32)
        faiss.normalize_L2(batch_vecs)
        fp[start_idx:end_idx] = batch_vecs
        print(f"  Generated {end_idx}/{num_distractors} distractors ({end_idx/num_distractors*100:.1f}%)")

    fp.flush()
    print(f"Distractors saved to {distractor_path}.")
    return fp

def run_scale_benchmark(*args, **kwargs):
    raise RuntimeError('Use P1 latency anchor; extended-gallery runs require P3a provenance validation.')

def plot_scale_crossover(results: list, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    scales = [r["scale"] for r in results]
    flat_lat = [r["flat_latency_ms"] for r in results]
    hnsw_lat = [r["hnsw_latency_ms"] for r in results]
    ivf_lat = [r["ivf_latency_ms"] for r in results]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(scales, flat_lat, marker='s', linewidth=2.5, color='#d9534f', label='FlatIP')
    ax.plot(scales, ivf_lat, marker='^', linewidth=2.0, color='#f0ad4e', label='IVFFlat (Inverted File)')
    ax.plot(scales, hnsw_lat, marker='o', linewidth=2.5, color='#337ab7', label='HNSWFlat')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Gallery Size N (Images in Gallery)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Search Latency per Query (ms) [Log Scale]', fontsize=12, fontweight='bold')
    ax.set_title(f'Scale benchmark: {min(scales):,}–{max(scales):,} vectors', fontsize=13, fontweight='bold')
    ax.grid(True, which="both", ls="--", alpha=0.3)
    ax.legend(fontsize=11)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, "scale_crossover_measured.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved scale crossover plot: {plot_path}")

def generate_scale_markdown_report(*args, **kwargs):
    raise RuntimeError('Legacy prose renderer retired. Run render_p0_reports.py for historical results or run_p1_reference.py --render-only for new reference results.')

def main():
    import runpy
    runner = runpy.run_path(str(PROTOCOL_ROOT / 'Phase_2_Q1_Journal/R2_Audit/scripts/run_p1_reference.py'))
    runner['run_modules'](['a4'])

if __name__ == "__main__":
    main()
