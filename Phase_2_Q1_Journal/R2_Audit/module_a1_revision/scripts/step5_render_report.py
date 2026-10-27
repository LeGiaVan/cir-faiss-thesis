"""
Step 5: render Module A.1 report from JSON outputs.

Rules from mentor-audit-protocol:
  1. All reported numbers must come from JSON outputs.
  2. Use neutral scientific language.
  3. Use one hypothesis label from:
     XAC NHAN | UNG HO MOT PHAN | CHUA KET LUAN | BAC BO
  4. Use relative plot paths.
  5. Follow the seven-section report template.
"""

import datetime
import json
import math
import pathlib
from string import Template


MODULE_DIR = pathlib.Path(__file__).parent.parent
RESULTS_DIR = MODULE_DIR / "results"
PLOTS_DIR = MODULE_DIR / "plots"
PHASE_DIR = pathlib.Path(__file__).resolve().parents[3]
REPORT_DIR = PHASE_DIR / "reports" / "stage_A"
REPORT_OUT = REPORT_DIR / "module_a1_hubness_report.md"

PLOT_NAMES = [
    "fig1_miss_rate_by_k_group.png",
    "fig2_logit_coef_path.png",
    "fig3_centering_before_after.png",
]


def load_json(name: str) -> dict:
    path = RESULTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing result file: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt(value, digits: int = 4) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def pct(value, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.{digits}f}%"


def ci_text(row: dict) -> str:
    if not row:
        return "N/A"
    caution = ' †' if row.get('boundary_degenerate') else ''
    return f"[{pct(row.get('ci_lower'))}, {pct(row.get('ci_upper'))}]{caution}"


def model_summary(step1: dict, model: str) -> dict:
    return step1.get("results", {}).get(model, {})


def copy_plots_for_report() -> None:
    center = load_json('step4_centering.json')['results']
    if all('paired_delta_ci' in row for row in center.values()):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        names = list(center)
        x = np.arange(len(names))
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        for offset, variant, label in [(-.18, 'before', 'Before'), (.18, 'after', 'Centered')]:
            bars = axes[0].bar(x+offset, [center[m][variant]['retention_at_10']*100 for m in names], .36, label=label)
            axes[0].bar_label(bars, fmt='%.2f', fontsize=9, padding=3)
        axes[0].set_xticks(x, names)
        axes[0].set_ylim(0, 108)
        axes[0].set_ylabel('Retention@10 (%)')
        axes[0].set_title('Mean retention across paired builds')
        axes[0].legend(loc='lower left')
        means = np.array([center[m]['delta_retention']*100 for m in names])
        lower = np.array([center[m]['paired_delta_ci']['ci_lower']*100 for m in names])
        upper = np.array([center[m]['paired_delta_ci']['ci_upper']*100 for m in names])
        axes[1].errorbar(means, x, xerr=[means-lower, upper-means], fmt='o', capsize=5)
        axes[1].axvline(0, color='gray', linestyle='--')
        axes[1].set_yticks(x, names)
        axes[1].set_ylim(-.5, len(names)-.5)
        axes[1].set_xlabel('Delta retention (percentage points)')
        axes[1].set_title('Paired query/build bootstrap: 95% CI')
        axes[1].grid(axis='x', alpha=.2)
        fig.tight_layout()
        fig.savefig(PLOTS_DIR/'fig3_centering_before_after.png', dpi=180)
        plt.close(fig)
    plot_out = REPORT_DIR / "plots"
    plot_out.mkdir(parents=True, exist_ok=True)
    for name in PLOT_NAMES:
        src = PLOTS_DIR / name
        if src.exists():
            (plot_out / name).write_bytes(src.read_bytes())


def beta_drop_fraction(beta_path: dict, a: str, b: str) -> float | None:
    va = beta_path.get(a)
    vb = beta_path.get(b)
    if va in (None, 0) or vb is None:
        return None
    return abs(va - vb) / abs(va)


def hypothesis_labels(step3: dict, step4: dict) -> tuple[str, str]:
    # No causal-status threshold on coefficient attenuation or invariant query-N10.
    return "CHƯA KẾT LUẬN", "CHƯA KẾT LUẬN"


def nested_logistic_explanation(step3: dict) -> str:
    """Render the teaching notes and derived odds ratios from saved estimates."""
    results = step3["results"]
    model_rows = [
        "| Mô hình | beta Pic2Word | CI 95% của beta | OR Pic2Word/SEARLE | CI 95% của OR | p-value |",
        "|---|---:|---|---:|---|---:|",
    ]
    for name in ("M0", "M1", "M2"):
        c = results[name]["coefficients"]["is_pic2word"]
        lo, hi = c["ci_95_lower"], c["ci_95_upper"]
        model_rows.append(
            f"| {name} | {c['coef']:.4f} | [{lo:.4f}, {hi:.4f}] | "
            f"{math.exp(c['coef']):.3f} | [{math.exp(lo):.3f}, {math.exp(hi):.3f}] | {c['p_value']:.3g} |"
        )
    c0 = results["M0"]["coefficients"]
    intercept = c0["Intercept"]["coef"]
    model_beta = c0["is_pic2word"]["coef"]
    example = (
        "```text\n"
        f"SEARLE:   z = {intercept:.6f}; p = {1 / (1 + math.exp(-intercept)):.4%}\n"
        f"Pic2Word: z = {intercept:.6f} + {model_beta:.6f}; "
        f"p = {1 / (1 + math.exp(-(intercept + model_beta))):.4%}\n"
        "```\n\nCác xác suất này khớp miss rate tổng thể sau làm tròn; "
        "OR là tỷ số odds, không phải tỷ số trực tiếp của hai miss rate."
    )
    c2 = results["M2"]["coefficients"]
    feature_rows = [
        "| Biến | beta M2 | CI 95% của beta | p-value |",
        "|---|---:|---|---:|",
    ]
    for name in ("rank", "log_n10", "log_indeg", "s1", "c_contrast"):
        c = c2[name]
        feature_rows.append(
            f"| `{name}` | {c['coef']:.4f} | [{c['ci_95_lower']:.4f}, {c['ci_95_upper']:.4f}] | {c['p_value']:.3g} |"
        )
    scaled = [
        f"- Rank tăng 1: odds nhân với {math.exp(c2['rank']['coef']):.3f}.",
        f"- N10 từ 1 lên 4: odds nhân với {math.exp(c2['log_n10']['coef'] * math.log(5 / 2)):.3f}.",
        f"- In-degree từ 9 lên 19: odds nhân với {math.exp(c2['log_indeg']['coef'] * math.log(20 / 10)):.3f}.",
        f"- s1 tăng 0,01, giữ c_contrast cố định: odds nhân với {math.exp(c2['s1']['coef'] * 0.01):.3f}.",
        f"- c_contrast tăng 0,01, giữ s1 cố định: odds nhân với {math.exp(c2['c_contrast']['coef'] * 0.01):.3f}.",
    ]
    template = pathlib.Path(__file__).with_name("nested_logistic_explanation.md")
    return Template(template.read_text(encoding="utf-8")).substitute(
        model_table="\n".join(model_rows),
        m0_example=example,
        feature_table="\n".join(feature_rows),
        scaled_examples="\n".join(scaled),
    ).strip()


def main() -> None:
    s1 = load_json("step1_hnsw_indegree.json")
    s2 = load_json("step2_bootstrap_ci.json")
    s3 = load_json("step3_nested_logit.json")
    s4 = load_json("step4_centering.json")

    meta1 = s1["metadata"]
    res2 = s2["results"]
    res4 = s4["results"]
    beta_path = s3.get("beta_model_path", {})
    causal_labels = s4.get("causal_label", {})

    searle1 = model_summary(s1, "searle")
    pic1 = model_summary(s1, "pic2word")
    n_queries = searle1.get("n_queries") or pic1.get("n_queries")
    n_gallery = searle1.get("n_gallery") or pic1.get("n_gallery")
    total_rows = sum((model_summary(s1, m).get("n_rows") or 0) for m in ["searle", "pic2word"])
    h1_label, h2_label = hypothesis_labels(s3, s4)
    timestamp = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    cfg = meta1.get('resolved_config', {})
    builds = s4.get('metadata', {}).get('build_seeds', [])

    copy_plots_for_report()

    groups = ["Anti-hub (N10=0)", "N10 = 1-4", "N10 = 5-9", "N10 = 10-29", "Hub (N10≥30)"]
    observed_minima = []
    for model, by_group in res2.items():
        observed = {label: row for label, row in by_group.items() if row}
        minimum = min(row['miss_rate'] for row in observed.values())
        labels = ', '.join(label for label, row in observed.items() if row['miss_rate'] == minimum)
        observed_minima.append(f"{model}: {labels} ({minimum*100:.2f}%)")
    group_note = ('**Nhận xét về k-occurrence và hubness:** Nhóm có miss rate thấp nhất trong seed reference hiện hành là ' + '; '.join(observed_minima) + '. '
                  'Đây là nhận xét mô tả của lần dựng đang dùng, không phải quy luật miss rate tăng đơn điệu theo N10. '
                  'Nhận xét nhóm N10=1–4 thấp hơn cả hai nhóm còn lại trong lần chạy trước phải được kiểm tra lại khi đổi lần dựng; không giữ nguyên lời kết luận nếu bảng mới không còn hỗ trợ.')
    report_lines = [
        "# Báo cáo Thực nghiệm Module A.1: Phân tích Hubness và Recall Retention của HNSW",
        "",
        f"> Sinh tự động bởi `step5_render_report.py` lúc {timestamp}.",
        "> Mọi số liệu trong báo cáo được đọc từ JSON trong `module_a1_revision/results/`.",
        "",
        "---",
        "",
        "## 1. Câu hỏi Nghiên cứu",
        "",
        "Hiện tượng hubness trong không gian embedding CIRCO có liên quan như thế nào đến xác suất HNSW bỏ sót các láng giềng exact top-10, và liệu các biến hubness/graph có giải thích được khoảng cách retention giữa SEARLE và Pic2Word hay không?",
        "",
        "## 2. Giả thuyết & Dự đoán Định lượng",
        "",
        "- **H1:** Các neighbor có k-occurrence thấp có tỷ lệ bị HNSW bỏ sót cao hơn các nhóm còn lại.",
        "- **H2:** Khoảng cách retention giữa SEARLE và Pic2Word được giải thích một phần bởi biến hubness/graph.",
        "- **Kế hoạch phân tích:** mô tả miss rate cùng CI bootstrap 95%, kiểm định Wald hai phía các hệ số GEE ở mức 0,05, và theo dõi beta Pic2Word qua M0–M2. Chưa có kiểm định trực tiếp mọi chênh lệch giữa nhóm hoặc ngưỡng cỡ hiệu ứng được đăng ký trước; giảm beta không được dùng làm tiêu chí xác nhận nhân quả hubness.",
        "",
        "## 3. Thiết kế Thực nghiệm",
        "",
        f"- **Dữ liệu & mô hình:** CIRCO, {n_queries} truy vấn, {n_gallery} ảnh gallery; SEARLE 512-d và Pic2Word 768-d.",
        f"- **Đơn vị phân tích:** neighbor-level, tổng cộng {total_rows} quan sát.",
        f"- **Run hiện hành:** profile reference; dataset neighbor-level/hồi quy dùng seed {meta1.get('primary_seed', 'legacy')}; centering báo cáo trung bình {len(builds)} cặp lần dựng. Không đồng nhất bảng một seed với trung bình nhiều seed.",
        f"- **Phần cứng/thực thi:** {meta1.get('hardware', {}).get('cpu')}; FAISS threads={meta1.get('hardware', {}).get('threads')}. Config hash: `{meta1.get('config_sha256', 'legacy unknown')}`.",
        "- **Truy xuất query:** phần val được đối chiếu vector và thứ tự GT; ID test tái dựng từ thứ tự annotation và vòng lặp extraction, do bundle cũ không chứa ID từng hàng. Đây là hạn chế provenance, không phải kiểm chứng độc lập toàn bộ test embedding.",
        f"- **Cấu hình chỉ mục:** HNSWFlat, M={meta1.get('index_config', {}).get('M')}, efSearch={meta1.get('index_config', {}).get('efSearch')}, efConstruction={meta1.get('index_config', {}).get('efConstruction')}.",
        "- **Phương pháp đo:** exact FlatIP top-10 làm mốc; HNSW retention là tỷ lệ exact neighbor được tìm lại trong HNSW top-10.",
        "- **Thống kê:** clustered bootstrap 95% CI theo `query_id`; GEE logistic regression với cụm `query_id`.",
        "",
        "## 4. Kết quả Thực nghiệm",
        "",
        "### 4.1. Tóm tắt Step 1",
        "",
        "| Mô hình | Retention@10 | Miss rate | Anti-hub gallery ratio | k-occurrence skewness | In-degree=0 ratio |",
        "|---|---:|---:|---:|---:|---:|",
        f"| SEARLE | {pct(searle1.get('retention_at_10'))} | {pct(searle1.get('overall_miss_rate'))} | {pct(searle1.get('antihub_gallery_ratio'))} | {fmt(searle1.get('k_occurrence_skewness'))} | {pct(searle1.get('in_degree_indeg0_ratio'), 4)} |",
        f"| Pic2Word | {pct(pic1.get('retention_at_10'))} | {pct(pic1.get('overall_miss_rate'))} | {pct(pic1.get('antihub_gallery_ratio'))} | {fmt(pic1.get('k_occurrence_skewness'))} | {pct(pic1.get('in_degree_indeg0_ratio'), 4)} |",
        "",
        "### 4.2. Miss rate theo nhóm k-occurrence",
        "",
        "| Nhóm | SEARLE Miss Rate | 95% CI | Pic2Word Miss Rate | 95% CI |",
        "|---|---:|---:|---:|---:|",
    ]

    for group in groups:
        searle_row = res2.get("searle", {}).get(group) or {}
        pic_row = res2.get("pic2word", {}).get(group) or {}
        report_lines.append(
            f"| {group} | {pct(searle_row.get('miss_rate'))} | {ci_text(searle_row)} | "
            f"{pct(pic_row.get('miss_rate'))} | {ci_text(pic_row)} |"
        )

    report_lines += [
        "",
        "Ghi chú: nhóm `N10=0` không có quan sát trong bảng neighbor-level vì một ảnh đã xuất hiện trong exact top-10 thì theo định nghĩa có `N10 >= 1`. Do đó kết quả này không được dùng để khẳng định kiểm định Anti-hub có ý nghĩa thống kê.",
        "",
        group_note,
        "",
        "Ở đây, N10 đo số query mà một ảnh xuất hiện trong exact top-10, phản ánh mức độ phổ biến của ảnh trong kết quả truy hồi (hubness theo tập query), không trực tiếp đo số cạnh đi vào hay khả năng tiếp cận ảnh trong đồ thị HNSW. Kết quả gợi ý mối liên hệ giữa mức độ phổ biến này và tỷ lệ bỏ sót trên từng lần xuất hiện, nhưng chưa xác lập quan hệ nhân quả giữa hubness và miss rate. Bảng phân nhóm chưa tách ảnh hưởng của thứ hạng, độ khó query và cấu trúc đồ thị; đồng thời không có quan sát ở các nhóm `N10 = 0` và `N10 ≥ 30`, nên chưa thể khái quát sang anti-hub hoặc hub cực trị.",
        "",
        "### 4.3. Trực quan hóa",
        "",
        "![Tỷ lệ bỏ sót theo nhóm k-occurrence](./plots/fig1_miss_rate_by_k_group.png)",
        "",
        "![Đường hệ số model qua các mô hình lồng nhau](./plots/fig2_logit_coef_path.png)",
        "",
        "![Can thiệp centering trước và sau](./plots/fig3_centering_before_after.png)",
        "",
        "### 4.4. Nested logistic regression",
        "",
        "| Mô hình | beta_model `is_pic2word` | QIC | Diễn giải thiết kế |",
        "|---|---:|---:|---|",
    ]

    for model_name, note in [
        ("M0", "Baseline: chỉ có biến model"),
        ("M1", "+ rank, log_n10, log_indeg"),
        ("M2", "+ s1, c_contrast"),
    ]:
        row = s3.get("results", {}).get(model_name, {})
        report_lines.append(
            f"| {model_name} | {fmt(beta_path.get(model_name))} | {fmt(row.get('qic'))} | {note} |"
        )

    report_lines += [
        "",
        nested_logistic_explanation(s3),
        "",
        "### 4.5. Can thiệp centering",
        "",
        f"Biến thể centering: `{s4.get('metadata', {}).get('centering_variant', 'N/A')}`.",
        "",
        "| Mô hình | Rank invariance | Delta skewness | Delta Retention (điểm phần trăm) | Nhãn nhân quả |",
        "|---|---:|---:|---:|---|",
    ]

    for model in ["searle", "pic2word"]:
        row = res4.get(model, {})
        report_lines.append(
            f"| {model.upper()} | {row.get('rank_invariance_verified')} | "
            f"{fmt(row.get('delta_skewness'))} | {fmt(row.get('delta_retention', 0)*100)} | "
            f"{causal_labels.get(model, 'N/A')} |"
        )

    report_lines += [
        '', '#### 4.5.1. Độ ổn định qua các lần dựng và khoảng tin cậy chênh lệch', '',
        '| Model | Trước (%) | Sau (%) | Delta (điểm %) | CI 95% delta (điểm %) | Các delta theo seed (điểm %) |',
        '|---|---:|---:|---:|---|---|',
    ]
    for model, row in res4.items():
        ci = row.get('paired_delta_ci', {})
        values = ', '.join(f'{x*100:.3f}' for x in row.get('per_seed_delta', []))
        report_lines.append(f"| {model} | {row['before']['retention_at_10']*100:.4f} | {row['after']['retention_at_10']*100:.4f} | {row['delta_retention']*100:.4f} | [{ci.get('ci_lower', 0)*100:.4f}, {ci.get('ci_upper', 0)*100:.4f}] | {values} |")
    report_lines += ['',
        'CI được tính bằng bootstrap lấy mẫu lại các cặp seed và query, giữ ghép cặp trước–sau. CI phản ánh tập seed và query đang đo; số lần dựng ít, các ảnh được lặp lại giữa query và dùng chung gallery vẫn là giới hạn. Không diễn giải CI này như bằng chứng giảm query-hubness.',
        '', '| Model | In-degree trung bình trước | Sau | Số query kiểm tra exact rank | Sai số lớn nhất đẳng thức điểm |',
        '|---|---:|---:|---:|---:|']
    for model,row in res4.items():
        report_lines.append(f"| {model} | {row.get('indegree_mean_before', 0):.4f} | {row.get('indegree_mean_after', 0):.4f} | {row.get('rank_check_queries', 'N/A')} | {row.get('max_score_identity_residual', 0):.3g} |")
    report_lines += ['',
        'Centering gallery không chuẩn hóa lại giữ query và thứ hạng exact: `q·(x−mu) = q·x − q·mu`. Vì vậy N10 theo query được giữ nguyên, nhưng inner product giữa các vector gallery có thể thay đổi và ảnh hưởng xây đồ thị. In-degree/out-degree được đo trực tiếp cho từng seed/biến thể và lưu trong JSON; đây là bằng chứng mô tả thay đổi graph, chưa phân lập đường dẫn nhân quả.',
        '',
        'Mức tăng retention là kết quả thực nghiệm có giá trị, ngay cả khi nhãn nhân quả là chưa kết luận. Không so trực tiếp số đo một lần dựng cũ với trung bình nhiều lần dựng mới như một hiệu ứng thuật toán; kết quả trước sửa được lưu tại `R2_Audit/archive/pre_p0_p1_p2b/a1/`.',
        '',
        'Dữ liệu từng query: `R2_Audit/module_a1_revision/data/centering_per_query.parquet`. JSON `step4_centering.json` lưu từng seed, thống kê graph, thời gian dựng và các lần đo độ trễ.',
    ]

    antihub_searle = res2.get("searle", {}).get("Anti-hub (N10=0)") or {}
    antihub_pic = res2.get("pic2word", {}).get("Anti-hub (N10=0)") or {}
    report_lines += [
        "",
        "## 5. Kết luận & Đánh giá Giả thuyết",
        "",
        f"- **Trạng thái H1:** **{h1_label}**.",
        f"- **Trạng thái H2:** **{h2_label}**.",
        "",
        "**Bằng chứng quyết định từ số liệu:**",
        f"- Anti-hub miss rate ở bảng neighbor-level: SEARLE {pct(antihub_searle.get('miss_rate'))}, Pic2Word {pct(antihub_pic.get('miss_rate'))}; hai giá trị là N/A do không có quan sát `N10=0` trong exact top-10.",
        f"- beta_model qua M0 -> M1 -> M2: {fmt(beta_path.get('M0'))} -> {fmt(beta_path.get('M1'))} -> {fmt(beta_path.get('M2'))}.",
        "",
        "Phân tích hiện tại chưa xác nhận H1 trên toàn bộ phổ anti-hub/hub; các nhóm quan sát và hệ số N10 phải được đọc theo đúng đơn vị query→gallery. H2 chưa được nhận diện nhân quả: giảm hệ số trong hồi quy logistic không tự động đo phần đóng góp của hubness. Centering được đánh giá riêng bằng mức tăng retention và CI, không yêu cầu query-N10 phải giảm.",
        "",
        "## 6. Hạn chế Thực nghiệm",
        "",
        f"- Phân tích dùng một gallery CIRCO gồm {n_gallery} ảnh và một cấu hình HNSW tham chiếu.",
        "- GEE không tương đương hồi quy logistic likelihood chuẩn; QIC được dùng khi thư viện hỗ trợ.",
        "- Bootstrap/GEE theo query chưa xử lý mọi phụ thuộc giữa các query cùng truy hồi một ảnh. Hồi quy dùng một seed reference; độ bền hệ số qua các seed chưa được khẳng định.",
        "- HNSW dựng đa luồng có thể không tái lập từng bit ngay cả khi cùng seed; cần đọc phân phối kết quả qua các lần dựng.",
        "- Can thiệp centering giữ thứ hạng exact bằng cách không re-normalize gallery sau khi trừ mean; kết quả có thể khác nếu thay đổi metric hoặc chuẩn hóa.",
        "",
        "## 7. Các bước Tiếp theo",
        "",
        "1. Chạy thêm cấu hình stress-test HNSW `M=16`, `efSearch=32` để kiểm tra độ bền.",
        "2. Kiểm tra độ nhạy theo neighbor ID và nhiều seed cho các hệ số hồi quy, trước khi đưa ra kết luận cơ chế mạnh hơn.",
        "3. Tiếp tục P2a/P2c theo kế hoạch chung; không coi A.1 hoàn tất là đã hoàn tất Stage A.",
    ]

    sample_lines = ['', '#### 4.2.1. Cỡ mẫu theo N10', '',
                    '| Model | Nhóm N10 | Dòng neighbor | Query | Neighbor duy nhất | Miss |', '|---|---|---:|---:|---:|---:|']
    for model, by_group in res2.items():
        for label, row in by_group.items():
            if row:
                sample_lines.append(f"| {model} | {label} | {row['n_observations']} | {row.get('n_queries', 'N/A')} | {row.get('n_unique_neighbors', 'N/A')} | {row.get('n_missed', 'N/A')} |")
    sample_lines += ['', '#### 4.2.2. Miss rate theo in-degree HNSW tầng 0', '',
                     '| Model | In-degree | Miss rate | CI 95% | Dòng neighbor | Query | Neighbor duy nhất | Miss |',
                     '|---|---|---:|---|---:|---:|---:|---:|']
    for model, by_group in s2.get('indegree_results', {}).items():
        for label, row in by_group.items():
            if row:
                sample_lines.append(f"| {model} | {label} | {pct(row['miss_rate'])} | {ci_text(row)} | {row['n_observations']} | {row['n_queries']} | {row['n_unique_neighbors']} | {row['n_missed']} |")
            else:
                sample_lines.append(f'| {model} | {label} | N/A | N/A | 0 | 0 | 0 | 0 |')
    sample_lines += ['', '† Khoảng bootstrap suy biến ở biên. Các nhóm không có quan sát được ghi N/A. Bootstrap lấy lại query trong từng nhóm. Nếu mọi quan sát đều không bị bỏ sót (hoặc đều bị bỏ sót), bootstrap thực nghiệm cho CI suy biến [0,0] (hoặc [1,1]); đó là giới hạn của phương pháp ở biên, không phải bảo đảm tỷ lệ thật bằng 0 hay 1. Không dùng CI suy biến để khẳng định độ chính xác cao ở nhóm nhỏ.', '']
    idx = report_lines.index('### 4.3. Trực quan hóa')
    report_lines[idx:idx] = sample_lines
    coef_lines=['', '#### 4.4.10. Bảng hệ số đầy đủ M0–M2', '',
                '| Mô hình | Biến | beta | SE robust | CI 95% | p hai phía |', '|---|---|---:|---:|---|---:|']
    for name, result in s3['results'].items():
        for variable, c in result['coefficients'].items():
            coef_lines.append(f"| {name} | {variable} | {c['coef']:.6f} | {c['std_err']:.6f} | [{c['ci_95_lower']:.6f}, {c['ci_95_upper']:.6f}] | {c['p_value']:.3g} |")
    coef_lines += ['', 'p được tính theo kiểm định Wald hai phía của GEE với sandwich SE; giá trị hiển thị 0 nếu xảy ra underflow số học không có nghĩa xác suất toán học đúng bằng 0. Các mô hình đều phải hội tụ trước khi lưu JSON.', '']
    idx = report_lines.index('### 4.5. Can thiệp centering')
    report_lines[idx:idx] = coef_lines
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Saved report: {REPORT_OUT}")


if __name__ == "__main__":
    main()
