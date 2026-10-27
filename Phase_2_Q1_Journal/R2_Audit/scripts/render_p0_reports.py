"""Read-only legacy analysis; regenerate corrected P0 reports and evidence."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import sys
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from phase2.protocol import metadata
PHASE = ROOT / 'Phase_2_Q1_Journal'
AUDIT = PHASE / 'R2_Audit'
REPORTS = PHASE / 'reports/stage_A'
SOURCE = ROOT / 'data/results/phase2_stageA/json'
OUT = AUDIT / 'p0_audit_checklist'


def read(name):
    return json.loads((SOURCE / (name + '.json')).read_text(encoding='utf-8'))


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '|' + '---|' * len(headers)] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def report(name, title, question, hypothesis, design, results, conclusion, limits, next_steps):
    sections = [('Câu hỏi nghiên cứu', question), ('Giả thuyết và dự đoán', hypothesis),
                ('Thiết kế thực nghiệm', design), ('Kết quả', results),
                ('Kết luận và trạng thái', conclusion), ('Hạn chế', limits), ('Các bước tiếp theo', next_steps)]
    text = f'# Báo cáo Thực nghiệm Module {title}\n\n> Bản sửa P0; sinh từ JSON legacy bằng `render_p0_reports.py`. Không gán cấu hình reference mới cho số liệu lịch sử.\n\n'
    text += '\n\n'.join(f'## {i}. {heading}\n\n{body}' for i, (heading, body) in enumerate(sections, 1))
    (REPORTS / name).write_text(text + '\n', encoding='utf-8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    backup = AUDIT / 'archive/pre_p0_p1_p2b/reports'
    backup.mkdir(parents=True, exist_ok=True)
    for p in REPORTS.glob('*.md'):
        if not (backup / p.name).exists():
            shutil.copy2(p, backup / p.name)
    a1, a2, a3, a4, a5 = [read(n) for n in ['module_a1_hubness','module_a2_pq_perturbation',
                           'module_a3_ivf_routing','module_a4_scale_benchmark','module_a5_geometry_power']]
    evidence = {}
    evidence[1] = table(['Model','Skewness gallery→gallery'], [[m, f"{r['distribution']['skewness']:.9f}"] for m,r in a1.items()]) + '\n\nHai giá trị gần bằng nhau trong mẫu này; không suy ra tác động nhân quả của số chiều.'
    evidence[2] = table(['Model','Kurtosis','Max occurrence'], [[m,f"{r['distribution']['kurtosis']:.6f}",r['distribution']['max_occurrence']] for m,r in a1.items()])
    evidence[3] = table(['Model','p lưu trong JSON','Alternative','p hai phía tái tính'], [[m,f"{r['hnsw_breakdown']['statistical_test']['p_value']:.6f}",r['hnsw_breakdown']['statistical_test']['alternative'],f"{stats.mannwhitneyu(r['hnsw_breakdown']['anti_hub']['raw_retentions'],r['hnsw_breakdown']['normal']['raw_retentions'],alternative='two-sided').pvalue:.6f}"] for m,r in a1.items()])
    evidence[4] = 'N10=0 của exact kNN không đồng nghĩa in-degree HNSW=0. A.1 R2 đo trực tiếp các cạnh tầng 0; xem hàm `graph_degrees` trong `src/phase2/protocol.py` và `run_reference_audit.py`. Thiết kế query→gallery R2 được phân biệt với gallery→gallery legacy.'
    rows = []
    for m, by_m in a2.items():
        for code, r in by_m.items():
            rows.append([m, code, f"{r['theoretical_prediction']['pred_rms']:.6f}",f"{r['stats_random']['rms']:.6f}",f"{r['stats_top10']['rms']:.6f}",f"{r['score_gap']['mean']:.8f}",f"{r['score_gap']['median']:.8f}",f"{r['retention_at_10']:.2f}%"])
    r = a2['searle']['16']
    evidence[10] = f"SEARLE m=16: RMS random={r['stats_random']['rms']:.6f}; dự báo legacy={r['theoretical_prediction']['pred_rms']:.6f}; RMS top-10={r['stats_top10']['rms']:.6f}. Sai lệch random/dự báo={abs(r['stats_random']['rms']/r['theoretical_prediction']['pred_rms']-1)*100:.2f}%."
    evidence[11] = f"Nếu delta là RMS top-10 thực đo, 2 delta={2*r['stats_top10']['rms']:.6f}; nếu delta là dự báo RMS random legacy, 2 delta={2*r['theoretical_prediction']['pred_rms']:.6f}. RMS không phải cận trên sai số từng cặp; 2 RMS không phải ngưỡng bảo đảm thứ hạng."
    report('module_a2_pq_perturbation_report.md','A.2: Nhiễu điểm số IVFPQ',
           'Nhiễu trên cặp ngẫu nhiên có đại diện cho nhiễu trên các láng giềng exact không?',
           'Đánh giá hậu kiểm giả thuyết nhiễu đẳng hướng toàn cục. Chưa có đăng ký dự đoán định lượng trước lần chạy legacy; không tạo dự đoán hồi tố.',
           'Nguồn: `data/results/phase2_stageA/json/module_a2_pq_perturbation.json` (đường dẫn từ gốc repo). Code legacy dùng CIRCO val, nlist=351, nprobe=32, m=8/16; JSON không có metadata đầy đủ. Tỷ lệ retention trong JSON có đơn vị phần trăm. Nhiễu lưu dạng trị tuyệt đối, chưa đo mean nhiễu có dấu.',
           table(['Model','m','RMS dự báo legacy','RMS random','RMS top-10','Mean gap 10/11','Median gap 10/11','Retention@10'],rows)+'\n\n'+evidence[10]+'\n\n'+evidence[11],
           '**ỦNG HỘ MỘT PHẦN:** xấp xỉ toàn cục có thể gần RMS random trong một số cấu hình; không đại diện nhiễu top-10. **CHƯA KẾT LUẬN** về cơ chế nhiễu có dấu và ngưỡng hoán vị g_5% vì chưa có phép đo P2a.',
           'Không suy ra bias có dấu từ histogram trị tuyệt đối. Các mảng lưu bị cắt và không có query ID, chưa đủ cho CI theo query đáng tin cậy. Phân vị p95 không phải CI 95%. Chưa dùng kết quả này làm bảo đảm Score-Gap Loss.',
           'P2a: lưu delta có dấu/top-50, tách song song/trực giao, đo d giữa hai hạng liền kề; quét m=8/16/32/64 và tính g_5% cùng CI.')
    rows=[]
    thresholds=[]
    for m,r in a3.items():
        for n,v in sorted(r['by_nprobe'].items(),key=lambda t:int(t[0])):
            rows.append([m,r['nlist'],n,f"{v['retention_at_10']:.2f}%",f"{v['retained_candidate_ratio']:.2f}%",f"{v['mean_routing_margin']:.6f}"])
        accepted=[v for v in r['by_nprobe'].values() if v['retention_at_10']>=95]
        v=min(accepted,key=lambda v:v['nprobe'])
        thresholds.append(f"{m}: nprobe nhỏ nhất trong dải đã đo đạt ≥95% là {v['nprobe']} ({v['retention_at_10']:.2f}%).")
    evidence[7]=' '.join(thresholds)+'\n\n'+table(['Model','nlist','nprobe','Retention','Coverage','Margin'],rows)
    evidence[12]='IVFFlat tính inner product trực tiếp trên vector trong các cụm được probe; coverage của exact top-k và retention trùng nhau theo cấu trúc khi cùng metric, candidate set và xử lý ties nhất quán. Đây là kiểm tra cài đặt, không phải phát hiện nhân quả.'
    report('module_a3_ivf_routing_report.md','A.3: Sai số định tuyến IVFFlat',
           'Recall retention có bằng tỷ lệ exact neighbor nằm trong các cụm đã probe không?',
           'Kiểm tra đồng nhất thức cấu trúc coverage/retention, không đặt giả thuyết về nhiễu lượng tử hóa cho IVFFlat.',
           'Nguồn: `data/results/phase2_stageA/json/module_a3_ivf_routing.json`. Profile legacy nlist=351, CIRCO val; chưa áp cấu hình reference mới. Margin là chênh điểm giữa centroid thứ nprobe và nprobe+1.',
           evidence[7], '**XÁC NHẬN (kiểm tra cài đặt):** '+evidence[12],
           'Chưa có CI và metadata lịch sử đầy đủ. Kết quả không chứng minh quan hệ nhân quả giữa hubness và định tuyến. SEARLE/Pic2Word không có mạng Combiner riêng để fine-tune.',
           'Chuẩn hóa cấu hình; bổ sung thứ hạng cụm của exact neighbor và imbalance factor; chỉ so sánh nprobe trong cùng nlist/profile.')
    x=np.log([r['scale'] for r in a4])
    slopes={k:float(np.polyfit(x,np.log([r[k+'_latency_ms'] for r in a4]),1)[0]) for k in ['flat','hnsw','ivf']}
    evidence[8]=f"Dải đã đo {min(r['scale'] for r in a4):,}–{max(r['scale'] for r in a4):,}; speedup HNSW ở hai đầu {a4[0]['hnsw_speedup']:.2f}× và {a4[-1]['hnsw_speedup']:.2f}×."
    evidence[9]='; '.join(f'{k}: slope log–log={v:.4f}' for k,v in slopes.items())+'. Đây là khớp thực nghiệm trên dải hữu hạn, không phải chứng minh độ phức tạp tiệm cận.'
    plots=REPORTS/'plots';plots.mkdir(exist_ok=True)
    fig,ax=plt.subplots()
    for key in slopes: ax.loglog([r['scale'] for r in a4],[r[key+'_latency_ms'] for r in a4],'o-',label=f'{key} (slope {slopes[key]:.2f})')
    ax.set(xlabel='Gallery vectors N',ylabel='Legacy latency (ms/query)',title='Legacy scale benchmark: 10K–500K');ax.legend();fig.tight_layout();fig.savefig(plots/'scale_legacy_10k_500k.png',dpi=160);plt.close(fig)
    rows=[[r['scale'],f"{r['flat_latency_ms']:.3f}",f"{r['hnsw_latency_ms']:.3f}",f"{r['hnsw_speedup']:.2f}",f"{r['hnsw_retention']:.2f}%",f"{r['ivf_latency_ms']:.3f}",f"{r['ivf_retention']:.2f}%"] for r in a4]
    report('module_a4_scale_report.md','A.4: Quy mô gallery 10K–500K',
           'Độ trễ và retention thay đổi thế nào theo kích thước gallery trong benchmark đã lưu?',
           'Phân tích mô tả legacy; chưa xác nhận giả thuyết độ khó truy hồi ảnh thật tăng theo quy mô.',
           'Nguồn: `data/results/phase2_stageA/json/module_a4_scale_benchmark.json`. JSON chưa ghi provenance distractor/hardware. Code cũ dùng HNSW M=32, efSearch=64 và một lần đo; không phải giao thức reference mới. Không gán các tham số suy từ code thành metadata đã xác minh của lần chạy cũ.',
           table(['N','Flat ms','HNSW ms','Speedup','HNSW retention','IVF ms','IVF retention'],rows)+'\n\n'+evidence[8]+'\n\n'+evidence[9]+'\n\n![Độ trễ legacy](./plots/scale_legacy_10k_500k.png)',
           '**ỦNG HỘ MỘT PHẦN:** có tăng tốc trên dữ liệu đã lưu. **CHƯA KẾT LUẬN** cho gallery ảnh thật mở rộng hoặc speedup ở cùng chất lượng.',
           'Distractor chưa có provenance được xác minh; code có nhánh Gaussian. Ở 500K, các cấu hình trong bảng chưa đạt retention 95%. Chưa có mAP theo N, CI độ trễ hoặc 7 lần đo. Không so trực tiếp độ trễ khác máy/threads/batch với ICRCV.',
           'P3a: kiểm kê nguồn ảnh/encoder, đo distractor top-10, near-duplicates và mAP; tune tới retention ≥95% rồi đo latency chuẩn. Chưa mở rộng 1M.')
    rec=a5['records']; y=np.array([r['hnsw_retention_m16_ef32'] for r in rec]);z=np.log10([r['N'] for r in rec])
    corrs={}
    for name,values in [(k,[r[k] for r in rec]) for k in ['relative_contrast','lid','hubness_skewness','anti_hub_ratio']]+[('log10_N',z)]:
        rho,p=stats.spearmanr(values,y)
        item={'rho':float(rho),'p_two_sided':float(p)}
        if name!='log10_N':
            design=np.column_stack([np.ones(len(y)),stats.rankdata(z)])
            rx=stats.rankdata(values);ry=stats.rankdata(y)
            ex=rx-design@np.linalg.lstsq(design,rx,rcond=None)[0];ey=ry-design@np.linalg.lstsq(design,ry,rcond=None)[0]
            partial=float(np.corrcoef(ex,ey)[0,1]);df=len(y)-3
            item.update(partial_rho=partial,partial_p=float(2*stats.t.sf(abs(partial)*np.sqrt(df/(1-partial**2)),df)))
        corrs[name]=item
    rows=[[k,f"{v['rho']:.6f}",f"{v['p_two_sided']:.6f}",f"{v['partial_rho']:.6f}" if 'partial_rho' in v else 'N/A',f"{v['partial_p']:.6f}" if 'partial_p' in v else 'N/A'] for k,v in corrs.items()]
    evidence[5]=f"LID rho={corrs['lid']['rho']:.6f}, p={corrs['lid']['p_two_sided']:.6f}; hubness rho={corrs['hubness_skewness']['rho']:.6f}, p={corrs['hubness_skewness']['p_two_sided']:.6f}. Đây là tương quan trong mẫu, chưa đo sức dự báo ngoài mẫu."
    evidence[6]=table(['Biến','Spearman thô','p hai phía','Riêng phần rank | log N','p xấp xỉ'],rows)
    report('module_a5_geometry_power_report.md','A.5: Hình học, quy mô và retention',
           'Các chỉ số hình học có liên hệ với retention độc lập với quy mô N không?',
           'Hậu kiểm phát biểu hubness là chỉ số duy nhất có liên hệ mạnh. Phân tích này không thay thế thiết kế N cố định của P2c.',
           f"Nguồn: `data/results/phase2_stageA/json/module_a5_geometry_power.json`, {len(rec)} cặp model/dataset. Retention lấy từ sweep stress M16/ef32; legacy RC/LID chưa đồng nhất giao thức mới. Tương quan riêng phần: residual hóa ranks của x,y theo rank(log N), Pearson residual; p xấp xỉ t với n−3 bậc tự do, không điều chỉnh đa kiểm định.",
           evidence[5]+'\n\n'+evidence[6],
           '**BÁC BỎ** phát biểu hubness là chỉ số duy nhất có tương quan mạnh trong mẫu: LID có |rho| lớn hơn, log N còn mạnh hơn. **CHƯA KẾT LUẬN** về sức dự báo độc lập với N; các tương quan riêng phần chưa đạt mức 0,05.',
           'Chỉ có 8 điểm, nhiều điểm chia sẻ model/dataset, p xấp xỉ và không có đánh giá ngoài mẫu. Không coi tương quan thô là cơ chế nhân quả. Không gán định nghĩa RC/LID mới cho giá trị legacy.',
           'P2c chưa thực hiện: tính RC/LID thống nhất, thiết kế N cố định và quét N có lấy mẫu lặp; báo cáo CI và phụ thuộc giữa các tập con.')
    evidence[13]='Tổng kết hiện hành viết lại theo trạng thái từng giả thuyết; loại kết luận tuyệt đối, đề xuất Combiner và link file:///. Các bản lịch sử được giữ trong archive và không phải báo cáo hiện hành.'
    summary='''# Tổng kết Stage A — bản sửa P0

> Bản làm việc; đã sửa diễn giải legacy, chưa hoàn tất toàn bộ R2. Số liệu đọc từ JSON; P2a/P2c/P3/P4 chưa được xác nhận hoàn thành.

| Module | Kết luận hiện được dữ liệu hỗ trợ | Trạng thái | Báo cáo |
|---|---|---|---|
| A.1 | Phân biệt query-N10 và kết nối HNSW; không suy nhân quả từ hệ số giảm | Chưa kết luận nhân quả | [A.1](./module_a1_hubness_report.md) |
| A.2 | RMS random và top-10 khác nhau; chưa có signed-noise R2 | Ủng hộ một phần | [A.2](./module_a2_pq_perturbation_report.md) |
| A.3 | Retention/coverage nhất quán với cấu trúc IVFFlat | Xác nhận kiểm tra cài đặt | [A.3](./module_a3_ivf_routing_report.md) |
| A.4 | Tăng tốc legacy; chưa kiểm định distractor và matched quality | Chưa kết luận cho ảnh thật mở rộng | [A.4](./module_a4_scale_report.md) |
| A.5 | Không ủng hộ tính duy nhất của hubness; chưa kiểm soát N bằng thiết kế | Bác bỏ tính duy nhất; chưa kết luận dự báo độc lập | [A.5](./module_a5_geometry_power_report.md) |

## Bằng chứng định lượng legacy

'''+evidence[10]+'\n\n'+evidence[7].split('\n\n')[0]+'\n\n'+evidence[8]+'\n\n'+evidence[5]+'''

## Điều kiện nộp P0–P2

Hoàn thiện P1 và P2b; tiếp tục P2a/P2c trước khi đóng gói đủ hồ sơ. Không dùng kết quả legacy khác cấu hình để xác nhận kết quả reference. Xem [checklist P0](../../R2_Audit/P0_AUDIT_CHECKLIST.md) và [kế hoạch hiện trạng](../../R2_Current_Status_and_Completion_Plan.md).
'''
    (REPORTS/'stage_a_master_summary.md').write_text(summary,encoding='utf-8')
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.glob('module_a*.json')}
    derived={'metadata':metadata('P0_legacy_reanalysis',inputs=sorted(SOURCE.glob('module_a*.json')),profile='legacy_reanalysis',dataset='multiple',analysis='P0 legacy reanalysis; not new ANN runs',source_sha256=sources,historical_hardware='unknown; runtime hardware below refers only to reanalysis'),'scale_slopes':slopes,'geometry_correlations':corrs}
    (OUT/'p0_derived_statistics.json').write_text(json.dumps(derived,indent=2,ensure_ascii=False),encoding='utf-8')
    checklist=['# P0 — đối chiếu 13 mục đã sửa','', 'P0 chỉ xác nhận sửa báo cáo; không thay thế nghiệm thu P1/P2. Evidence được sinh lại từ JSON legacy, không trộn định nghĩa N10 với A.1 R2.','', '| Mục | Trạng thái | Bằng chứng |','|---|---|---|']
    for i in range(1,14):
        file=f'p0_{i:02d}_verified.md'
        sources_by_item={1:'module_a1_hubness',2:'module_a1_hubness',3:'module_a1_hubness',4:'module_a1_hubness',5:'module_a5_geometry_power',6:'module_a5_geometry_power',7:'module_a3_ivf_routing',8:'module_a4_scale_benchmark',9:'module_a4_scale_benchmark',10:'module_a2_pq_perturbation',11:'module_a2_pq_perturbation',12:'module_a3_ivf_routing'}
        source=sources_by_item.get(i)
        link=f'[JSON nguồn](../../../data/results/phase2_stageA/json/{source}.json)' if source else '[Các JSON nguồn](../../../data/results/phase2_stageA/json/)'
        (OUT/file).write_text(f'# P0.{i} — bằng chứng sửa báo cáo\n\n**Trạng thái:** ĐÃ SỬA P0.\n\n'+evidence[i]+f'\n\n{link}; hash và phép tính bổ sung tại [p0_derived_statistics.json](./p0_derived_statistics.json). Xem [báo cáo hiện hành](../../reports/stage_A/).\n',encoding='utf-8')
        checklist.append(f'| P0.{i} | Đã sửa và đối chiếu | [Evidence](./p0_audit_checklist/{file}) |')
    (AUDIT/'P0_AUDIT_CHECKLIST.md').write_text('\n'.join(checklist)+'\n',encoding='utf-8')
    print('P0: regenerated A.2–A.5, master summary, 13 evidence files and derived JSON.')


if __name__=='__main__':
    main()
