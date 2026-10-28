"""Report L2 invariance and paired seed/query retention differences."""
from pathlib import Path
import json,csv
import numpy as np
P=Path(__file__).resolve().parent

def main():
    meta=json.loads((P/'run_manifest.json').read_text(encoding='utf-8')); models={}; rows=[]
    lines=['# C3 — Đối chứng tịnh tiến dưới L2','','## 1. Câu hỏi và dự đoán','','Dịch đồng thời query và gallery bởi cùng mean có bảo toàn khoảng cách L2 và exact ranking, và HNSW có cho retention gần nhau không? Xem [kế hoạch](./ke_hoach_C3.md).','','## 2. Thiết kế','','CIRCO 1.020 query; hai model; HNSWFlat L2 M=32, efConstruction=200, efSearch=128, năm seed. So exact top-10 và squared L2 theo 10.000 cặp ngẫu nhiên, ngưỡng tuyệt đối 1e-5. Bootstrap chéo ghép cặp seed/query 2.000 lần, CI percentile 95%.','','## 3. Kết quả','']
    for model in ['searle','pic2word']:
        exact=json.loads((P/'data'/f'{model}_exact.json').read_text(encoding='utf-8'))
        if not exact['identical_top10'] or max(exact['max_top10_distance_error'],exact['max_sampled_pair_distance_error'])>exact['tolerance_squared_l2']: raise ValueError('Exact validation failed')
        vals={}
        for variant in ['original_l2','centered_l2']:
            vals[variant]=[]
            for seed in [42,43,44,45,46]:
                with np.load(P/'data'/f'{model}_{seed}_{variant}.npz') as z:
                    if str(z['signature'])!=meta['signature']: raise ValueError('Checkpoint mismatch')
                    ret=z['retention'].copy(); ndis=float(z['ndis']); edges=int(z['edges'])
                vals[variant].append(ret); rows.append({'model':model,'seed':seed,'variant':variant,'retention':float(ret.mean()),'ndis_per_query':ndis,'layer0_edges':edges})
        delta=np.stack(vals['centered_l2'])-np.stack(vals['original_l2']); rng=np.random.default_rng(42); bs=[]
        for _ in range(2000):
            s=rng.integers(0,5,5); q=rng.integers(0,delta.shape[1],delta.shape[1]); bs.append(delta[s][:,q].mean())
        ci=np.percentile(bs,[2.5,97.5]); result={'exact':exact,'mean_delta':float(delta.mean()),'ci_lower':float(ci[0]),'ci_upper':float(ci[1]),'per_seed_delta':delta.mean(axis=1).tolist()}; models[model]=result
        lines += [f'### {model.upper()}','',f"Exact top-10 giống nhau: {exact['identical_top10']}; sai số squared L2 lớn nhất trong top-10: {exact['max_top10_distance_error']:.3g}; trong 10.000 cặp mẫu: {exact['max_sampled_pair_distance_error']:.3g}.",'','| Seed | Original retention | Centered retention | Chênh lệch điểm % | Original ndis | Centered ndis | Original cạnh | Centered cạnh |','|---:|---:|---:|---:|---:|---:|---:|---:|']
        for seed in [42,43,44,45,46]:
            a=next(r for r in rows if r['model']==model and r['seed']==seed and r['variant']=='original_l2'); b=next(r for r in rows if r['model']==model and r['seed']==seed and r['variant']=='centered_l2')
            lines.append(f"| {seed} | {a['retention']*100:.2f}% | {b['retention']*100:.2f}% | {(b['retention']-a['retention'])*100:+.2f} | {a['ndis_per_query']:.1f} | {b['ndis_per_query']:.1f} | {a['layer0_edges']} | {b['layer0_edges']} |")
        lines += ['',f"Trung bình centered − original: {delta.mean()*100:+.3f} điểm %, CI 95% [{ci[0]*100:+.3f}, {ci[1]*100:+.3f}].",'']
    lines += ['## 4. Diễn giải và giới hạn','','Exact ranking đã qua kiểm tra theo ngưỡng được ghi trước. Sai khác HNSW được báo theo từng seed; CI chứa 0 không chứng minh tương đương. So sánh tại cùng efSearch không đảm bảo cùng ndis; dựng đa luồng có thể làm thay đổi đồ thị. Bằng chứng này không tự chứng minh cơ chế centering IP hay thay thế C2. Test query IDs chưa xác minh độc lập từng hàng; workspace dirty và provenance lưu bằng hash.','','## 5. Đầu ra','', '[JSON](./results.json) · [bảng từng seed](./per_seed.csv) · [manifest](./run_manifest.json) · [kế hoạch](./ke_hoach_C3.md).']
    (P/'results.json').write_text(json.dumps({'metadata':meta,'models':models,'bootstrap_replicates':2000},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (P/'per_seed.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (P/'bao_cao_C3.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
