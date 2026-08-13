import matplotlib.pyplot as plt
import numpy as np
import os

# Create thesis_report/images directory if it doesn't exist
os.makedirs("d:/G.VAN/KLTN/cir_faiss_thesis/thesis_report/images", exist_ok=True)

# Define IEEE colors (approximate to what was likely used)
seriesOrange = "#FF7F0E"
seriesBlue = "#1F77B4"

def make_fig_crossover():
    plt.rcParams.update({'font.size': 9, 'font.family': 'serif'})
    fig, ax = plt.subplots(figsize=(6, 3.5))
    
    # Points
    x_points = np.array([3817, 6346, 5373, 2297, 10000, 30000, 60000, 123403])
    y_flat = np.array([0.041, 0.063, 0.054, 0.026, 0.211, 0.711, 1.468, 3.324])
    y_hnsw = np.array([0.036, 0.041, 0.041, 0.021, 0.041, 0.061, 0.099, 0.146])
    
    # Fits
    x_line = np.logspace(np.log10(2000), np.log10(130000), 100)
    flat_fit = 2.73e-5 * x_line - 0.085
    hnsw_fit = 0.028 * np.log(x_line) - 0.201
    
    # Plot Fits
    # Filter out negative values for log plot
    flat_valid = flat_fit > 0
    ax.plot(x_line[flat_valid], flat_fit[flat_valid], color=seriesOrange, linewidth=2, label="FlatIP fit ($R^2=0.999$)")
    
    hnsw_valid = hnsw_fit > 0
    ax.plot(x_line[hnsw_valid], hnsw_fit[hnsw_valid], color=seriesBlue, linewidth=2, linestyle='--', label="HNSWFlat fit ($R^2=0.885$)")
    
    # Plot Points
    ax.scatter(x_points, y_flat, color=seriesOrange, marker='o', s=30, zorder=5)
    ax.scatter(x_points, y_hnsw, color=seriesBlue, marker='s', s=30, zorder=5)
    
    # Axes
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel("Gallery size $N$ (log scale)", fontsize=9)
    ax.set_ylabel("Latency (ms, log scale)", fontsize=9)
    ax.grid(True, which='major', color='#E0E0E0', linestyle='-')
    
    # Legend
    ax.legend(loc='upper left', frameon=False, fontsize=8)
    
    plt.tight_layout()
    plt.savefig("d:/G.VAN/KLTN/cir_faiss_thesis/thesis_report/images/fig_crossover.pdf", format='pdf', bbox_inches='tight')
    plt.close()

def make_fig_msensitivity():
    plt.rcParams.update({'font.size': 8, 'font.family': 'serif'})
    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.8))
    
    datasets = ["CIRCO", "CIRR", "FashionIQ"]
    searle_gains = [6.11, 0.46, 5.05]
    pic2word_gains = [11.63, 1.17, 5.43]
    ylims = [(0, 14), (0, 1.6), (0, 7)]
    
    bar_width = 0.35
    x = np.array([0])
    
    for i, ax in enumerate(axes):
        # Draw bars
        rects1 = ax.bar(x - bar_width/2, searle_gains[i], bar_width, label='SEARLE (512-d)', color=seriesBlue, edgecolor='black', linewidth=0.5)
        rects2 = ax.bar(x + bar_width/2, pic2word_gains[i], bar_width, label='Pic2Word (768-d)', color=seriesOrange, edgecolor='black', linewidth=0.5)
        
        # Annotate text
        def autolabel(rects, is_searle):
            for rect in rects:
                height = rect.get_height()
                # Offset slightly to prevent overlap in CIRCO if needed, 
                # but with different X positions they shouldn't overlap horizontally.
                ax.annotate(f'{height:.2f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 2),  # 2 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=7)
        
        autolabel(rects1, True)
        autolabel(rects2, False)
        
        ax.set_title(datasets[i], fontsize=9)
        ax.set_ylim(ylims[i])
        ax.set_xticks([])
        
        if i == 0:
            ax.set_ylabel("Retention@10 gain (pts)", fontsize=9)
            ax.legend(loc='upper left', frameon=False, fontsize=7)
        
        ax.grid(axis='y', color='#E0E0E0', linestyle='-')
        ax.set_axisbelow(True)
        
    plt.tight_layout()
    plt.savefig("d:/G.VAN/KLTN/cir_faiss_thesis/thesis_report/images/fig_msensitivity.pdf", format='pdf', bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    make_fig_crossover()
    make_fig_msensitivity()
    print("Plots generated successfully in thesis_report/images/")
