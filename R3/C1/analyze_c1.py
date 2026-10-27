"""Render C1 results from the completed per-build checkpoints."""
from pathlib import Path
import json, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
DATA=HERE/'data'
SEEDS=[42,43,44,45,46]
VARIANTS=['original_ip','centered_ip','centered_l2']

def main():
    manifest=json.loads((HERE/'run_manifest.json').read_text(encoding='utf-8'))
    result={'metadata':manifest,'analysis':{'bootstrap':'crossed paired seed and query percentile, fixed per-build ndis; 2000 resamples','interpolation':'linear retention on ndis; five log-spaced points within common support across IP builds','bootstrap_seed':42},'results':{}}
    rows=[]; comparisons=[]
    for model in ['searle','pic2word']:
        data={}
        for variant in VARIANTS:
            data[variant]=[]
            for seed in SEEDS:
                p=DATA/f'{model}_{seed}_{variant}.npz'
                if not p.exists(): raise FileNotFoundError(f'Missing checkpoint {p}')
                with np.load(p) as z:
                    if str(z['signature']) != manifest['signature']: raise ValueError('Checkpoint signature mismatch')
                    rec=json.loads(str(z['records'])); ret=z['retention'].copy()
                x=np.array([r['ndis_per_query'] for r in rec])
                if np.any(np.diff(x)<=0): raise ValueError(f'Nonmonotonic ndis: {p}')
                data[variant].append((x,ret))
                for r in rec:
                    rows.append({'model':model,'seed':seed,'variant':variant,'efSearch':r['efSearch'],'ndis_per_query':r['ndis_per_query'],'retention':r['retention'],'latency_median_ms':r['latency']['ms_per_query'],'latency_std_ms':r['latency']['std_ms']})
        ip=[v for key in VARIANTS[:2] for v in data[key]]
        lo=max(x[0] for x,_ in ip); hi=min(x[-1] for x,_ in ip)
        if lo>=hi: raise ValueError(f'No common ndis support for {model}')
        grid=np.geomspace(lo,hi,5)
        # Interpolate each query within each seed before crossed resampling.
        arr={}
        for variant in VARIANTS[:2]:
            arr[variant]=np.stack([np.stack([np.interp(grid,x,ret[:,q]) for q in range(ret.shape[1])],axis=1) for x,ret in data[variant]])
        delta=arr['centered_ip']-arr['original_ip']
        rng=np.random.default_rng(42); boot=np.empty((2000,5))
        for b in range(2000):
            si=rng.integers(0,5,5); qi=rng.integers(0,delta.shape[2],delta.shape[2])
            boot[b]=delta[si][:,:,qi].mean(axis=(0,2))
        ci=np.percentile(boot,[2.5,97.5],axis=0)
        points=[]
        for i,budget in enumerate(grid):
            point={'ndis_per_query':float(budget),'original_retention':float(arr['original_ip'][:,i,:].mean()),'centered_retention':float(arr['centered_ip'][:,i,:].mean()),'delta':float(delta[:,i,:].mean()),'ci_lower':float(ci[0,i]),'ci_upper':float(ci[1,i]),'per_seed_delta':[float(x) for x in delta[:,i,:].mean(axis=1)]}
            points.append(point); comparisons.append({'model':model,**{k:v for k,v in point.items() if k!='per_seed_delta'}})
        result['results'][model]={'exact_check':json.loads((DATA/f'{model}_exact.json').read_text(encoding='utf-8')),'common_support':[float(lo),float(hi)],'comparison':points}
        fig,ax=plt.subplots(figsize=(8,5))
        for variant,color,label in [('original_ip','tab:blue','Original IP'),('centered_ip','tab:orange','Centered IP'),('centered_l2','tab:green','Centered L2 (own exact L2 truth)')]:
            for x,ret in data[variant]: ax.plot(x,ret.mean(axis=1),color=color,alpha=.25,linewidth=1)
            # Aggregation at common efSearch, ndis remains measured; do not imply matching costs.
            xx=np.mean([x for x,_ in data[variant]],axis=0); ret_stack=np.stack([r for _,r in data[variant]]); yy=ret_stack.mean(axis=(0,2))
            curve_rng=np.random.default_rng(42); curve_boot=np.empty((2000,ret_stack.shape[1]))
            for b in range(2000):
                si=curve_rng.integers(0,5,5); qi=curve_rng.integers(0,ret_stack.shape[2],ret_stack.shape[2])
                curve_boot[b]=ret_stack[si][:,:,qi].mean(axis=(0,2))
            lower,upper=np.percentile(curve_boot,[2.5,97.5],axis=0)
            ax.fill_between(xx,lower,upper,color=color,alpha=.12)
            ax.plot(xx,yy,color=color,marker='o',label=label)
        ax.set_xscale('log'); ax.set_xlabel('Distance computations per query (ndis)'); ax.set_ylabel('Retention@10'); ax.set_title(f'C1 — {model}'); ax.grid(alpha=.3); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(HERE/f'c1_{model}.png',dpi=160); plt.close(fig)
    (HERE/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    for name,table in [('sweep.csv',rows),('comparison.csv',comparisons)]:
        with (HERE/name).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(table[0])); w.writeheader(); w.writerows(table)
    report=['# C1 — Retention ở cùng chi phí tìm kiếm','','## Câu hỏi và dự đoán','', 'Kiểm tra centering gallery có cải thiện retention@10 ở cùng số phép tính khoảng cách hay không. Dự đoán đã khóa trước khi chạy và thiết kế chi tiết: [kế hoạch C1](./ke_hoach_C1.md), [đăng ký trước](../stage0_preregistration.md).','','## Thiết kế','', 'CIRCO, 1.020 query, hai backbone; HNSW M=32, efConstruction=200; năm seed 42–46; efSearch từ 32 đến 384. Gallery và query được chuẩn hóa L2 trước phép biến đổi; centered IP chỉ trừ mean gallery và không chuẩn hóa lại. Đối chứng L2 trừ cùng mean ở cả hai phía và dùng ground truth L2 riêng.','', 'So sánh IP ở năm mức ndis cách đều theo log trong miền chung của toàn bộ 10 đồ thị IP, nội suy tuyến tính theo ndis, không ngoại suy. CI 95% percentile từ 2.000 lần bootstrap chéo seed/query, giữ ghép cặp; ndis quan sát được giữ cố định khi bootstrap. Hình thể hiện từng seed, trung bình tại cùng efSearch và CI bootstrap theo retention; trục hoành của đường trung bình là ndis trung bình ở efSearch đó.','','## Kết quả','', '| Model | ndis/query | Original | Centered | Chênh lệch | CI 95% |','|---|---:|---:|---:|---:|---:|']
    for model in ['searle','pic2word']:
        for p in result['results'][model]['comparison']:
            report.append(f"| {model} | {p['ndis_per_query']:.1f} | {p['original_retention']:.4f} | {p['centered_retention']:.4f} | {p['delta']:+.4f} | [{p['ci_lower']:+.4f}, {p['ci_upper']:+.4f}] |")
    report += ['', '![SEARLE](./c1_searle.png)', '', '![Pic2Word](./c1_pic2word.png)', '', '## Đánh giá','']
    for model in ['searle','pic2word']:
        pts=result['results'][model]['comparison']; positive=sum(p['ci_lower']>0 for p in pts); negative=sum(p['ci_upper']<0 for p in pts)
        report.append(f'- **{model}:** {positive}/5 mức ngân sách có CI chênh lệch hoàn toàn dương; {negative}/5 hoàn toàn âm. Các mức còn lại chưa đủ bằng chứng về hướng chênh lệch. Các CI là theo từng điểm, không phải CI đồng thời.')
    report += ['', '## Hạn chế','', 'Chỉ có năm lần dựng mỗi model; xây HNSW đa luồng có thể không tái lập từng cạnh ngay cả khi seed cố định. CI giữ ndis đo được cố định, không tính bất định của chi phí hoặc điều chỉnh kiểm định nhiều ngân sách. Nội suy tuyến tính là xấp xỉ giữa các điểm sweep và có thể ảnh hưởng kết luận cục bộ. ID nguồn của 800 test query chưa được xác minh độc lập từng hàng; phép ghép cặp ở đây dựa trên hàng feature ổn định, không xác nhận ánh xạ ID. Workspace dirty được ghi nhận bằng hash đầu vào và mã; commit nền không định danh toàn bộ workspace. Centered L2 dùng ground truth riêng; kiểm định bất biến với L2 gốc thuộc C3, chưa thể kết luận từ đường này.','','## Tệp dữ liệu','', '[JSON kết quả](./results.json), [sweep và latency](./sweep.csv), [so sánh tại cùng ndis](./comparison.csv), [manifest](./run_manifest.json), và checkpoint theo seed trong `data/`.']
    (HERE/'bao_cao_C1.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    import subprocess, sys
    subprocess.run([sys.executable, str(HERE/'render_c1_report.py')], check=True)
    print('Analysis complete')

if __name__=='__main__': main()
