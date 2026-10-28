"""Select by edge counts first, then perform paired matched-budget analysis."""
from pathlib import Path
import json, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

P=Path(__file__).resolve().parent
SEEDS=[42,43,44,45,46]; MS=[32,40,48,64]
GROUPS=[('centered_ip',32)]+[('original_ip',m) for m in MS]

def main():
    meta=json.loads((P/'run_manifest.json').read_text(encoding='utf-8'))
    edge_rows=[]; selected={}
    # The choice is frozen and persisted before any search results are read.
    for model in ['searle','pic2word']:
        counts={}
        for variant,m in GROUPS:
            vals=[]
            for seed in SEEDS:
                p=P/'data'/f'{model}_{variant}_M{m}_{seed}.npz'
                with np.load(p) as z:
                    if str(z['signature'])!=meta['signature']: raise ValueError(f'Signature mismatch: {p}')
                    vals.append(int(z['edges']))
            counts[(variant,m)]=vals
        target=float(np.median(counts[('centered_ip',32)]))
        ranking=sorted((abs(float(np.median(counts[('original_ip',m)]))/target-1),m) for m in MS)
        mismatch,m=ranking[0]
        selected[model]={'selected_M':m,'centered_median_edges':target,'original_median_edges':float(np.median(counts[('original_ip',m)])),'median_relative_deviation':float(np.median(counts[('original_ip',m)])/target-1),'matched_within_2_percent':bool(mismatch<=.02)}
        for (variant,m),vals in counts.items():
            for seed,edges in zip(SEEDS,vals):
                edge_rows.append({'model':model,'variant':variant,'M':m,'seed':seed,'edges':edges,'median_edges':float(np.median(vals)),'median_relative_deviation_from_centered':float(np.median(vals)/target-1),'paired_relative_deviation_from_centered':float(edges/counts[('centered_ip',32)][seed-42]-1) if variant=='original_ip' else 0.0})
    selection_path=P/'edge_selection.json'
    if selection_path.exists():
        old=json.loads(selection_path.read_text(encoding='utf-8'))
        if old['signature']!=meta['signature'] or old['selection']!=selected: raise ValueError('Prior selection differs')
    else: selection_path.write_text(json.dumps({'signature':meta['signature'],'selection':selected},indent=2)+'\n',encoding='utf-8')
    result={'metadata':meta,'selection':selected,'analysis':{'bootstrap':'crossed paired seeds and queries, percentile CI, ndis fixed','replicates':2000,'interpolation':'linear in ndis, common support of all selected builds','sensitivity':'linear interpolation in log ndis, point estimates only'},'models':{}}
    sweep=[]; compare=[]
    for model in ['searle','pic2word']:
        data={}
        for variant,m in GROUPS:
            data[(variant,m)]=[]
            for seed in SEEDS:
                with np.load(P/'data'/f'{model}_{variant}_M{m}_{seed}.npz') as z:
                    rec=json.loads(str(z['records'])); ret=z['retention'].copy(); edges=int(z['edges'])
                x=np.array([r['ndis_per_query'] for r in rec])
                if np.any(np.diff(x)<=0): raise ValueError(f'Nonmonotonic ndis: {model} {variant} {m} {seed}')
                data[(variant,m)].append((x,ret))
                for r in rec:
                    sweep.append({'model':model,'variant':variant,'M':m,'seed':seed,'edges':edges,'efSearch':r['efSearch'],'ndis_per_query':r['ndis_per_query'],'retention':r['retention'],'latency_median_ms':r['latency']['ms_per_query'],'latency_std_ms':r['latency']['std_ms']})
        chosen=selected[model]['selected_M']; keys=[('original_ip',chosen),('centered_ip',32)]
        pairs=[entry for key in keys for entry in data[key]]
        lo=max(x[0] for x,_ in pairs); hi=min(x[-1] for x,_ in pairs)
        entry={'common_support':[float(lo),float(hi)],'comparison':[],'exact_check':json.loads((P/'data'/f'{model}_exact.json').read_text(encoding='utf-8'))}
        if lo<hi:
            grid=np.geomspace(lo,hi,5); arr={}; logarr={}
            for key in keys:
                arr[key]=np.stack([np.stack([np.interp(grid,x,ret[:,q]) for q in range(ret.shape[1])],axis=1) for x,ret in data[key]])
                logarr[key]=np.stack([np.stack([np.interp(np.log(grid),np.log(x),ret[:,q]) for q in range(ret.shape[1])],axis=1) for x,ret in data[key]])
            delta=arr[keys[1]]-arr[keys[0]]; rng=np.random.default_rng(42); boot=np.empty((2000,5))
            for b in range(2000):
                si=rng.integers(0,5,5); qi=rng.integers(0,delta.shape[2],delta.shape[2])
                boot[b]=delta[si][:,:,qi].mean(axis=(0,2))
            ci=np.percentile(boot,[2.5,97.5],axis=0)
            for i,budget in enumerate(grid):
                p={'ndis_per_query':float(budget),'original_retention':float(arr[keys[0]][:,i,:].mean()),'centered_retention':float(arr[keys[1]][:,i,:].mean()),'delta':float(delta[:,i,:].mean()),'ci_lower':float(ci[0,i]),'ci_upper':float(ci[1,i]),'per_seed_delta':delta[:,i,:].mean(axis=1).tolist(),'log_ndis_delta':float((logarr[keys[1]][:,i,:]-logarr[keys[0]][:,i,:]).mean())}
                entry['comparison'].append(p); compare.append({'model':model,**{k:v for k,v in p.items() if k!='per_seed_delta'}})
            fig,(ax,bx)=plt.subplots(2,1,figsize=(9,8),sharex=True,gridspec_kw={'height_ratios':[2,1]})
            dense=np.geomspace(lo,hi,120)
            for key,color,label in [(keys[0],'#2666aa',f'Original M={chosen}'),(keys[1],'#dc6a15','Centered M=32')]:
                curves=[]
                for x,ret in data[key]:
                    y=ret.mean(axis=1)*100; ax.plot(x,y,color=color,alpha=.25,lw=1); curves.append(np.interp(dense,x,y))
                ax.plot(dense,np.mean(curves,axis=0),color=color,lw=2.5,label=label)
            ys=np.array([p['delta'] for p in entry['comparison']])*100; low=ci[0]*100; high=ci[1]*100
            bx.errorbar(grid,ys,yerr=[ys-low,high-ys],fmt='o',color='black',capsize=4); bx.axhline(0,color='grey'); bx.set_ylabel('Chênh lệch (điểm %)'); bx.set_xlabel('ndis / query (log)')
            ax.set_xscale('log'); ax.set_ylabel('Retention@10 (%)'); ax.set_title(f'{model.upper()}: so sánh theo số cạnh và chi phí'); ax.legend(); ax.grid(alpha=.25); bx.grid(alpha=.25); fig.tight_layout(); fig.savefig(P/f'c2_{model}.png',dpi=160); plt.close(fig)
        else: entry['note']='No common ndis support; no matched-cost comparison.'
        fig,ax=plt.subplots(figsize=(9,5))
        for key in GROUPS:
            for x,ret in data[key]: ax.plot(x,ret.mean(axis=1)*100,alpha=.15,lw=1)
            xx=np.mean([x for x,_ in data[key]],axis=0); yy=np.mean([r.mean(axis=1) for _,r in data[key]],axis=0)*100
            ax.plot(xx,yy,marker='o',markersize=3,label=f'{key[0]} M={key[1]}')
        ax.set_xscale('log'); ax.set_xlabel('ndis / query'); ax.set_ylabel('Retention@10 (%)'); ax.legend(); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(P/f'c2_{model}_all_m.png',dpi=160); plt.close(fig)
        result['models'][model]=entry
    (P/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for name,rows in [('edges.csv',edge_rows),('sweep.csv',sweep),('comparison.csv',compare)]:
        if rows:
            with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    render(result,edge_rows)

def render(result,edges):
    lines=['# C2: Centering so với tăng mật độ đồ thị gốc','','## 1. Câu hỏi nghiên cứu','','Tăng M cho HNSW original có đạt retention tương tự centered M=32 khi số cạnh gần nhau và chi phí ndis tương đương? Xem [kế hoạch](./ke_hoach_C2.md) và [đăng ký trước](../stage0_preregistration.md).','','## 2. Giả thuyết và quy tắc','','Chọn M original theo median số cạnh gần centered nhất, trước khi phân tích retention. Chỉ gọi khớp mật độ nếu chênh lệch median không quá 2%. Chênh lệch centered − original có CI dương hỗ trợ lợi thế trong điều kiện được khảo sát; CI chứa 0 không chứng minh tương đương.','','## 3. Thiết kế','','CIRCO 123.403 gallery và 1.020 query, SEARLE và Pic2Word; original M=32,40,48,64, centered M=32; efConstruction=200, 5 seed, 9 mức efSearch. Cạnh là cạnh có hướng hợp lệ tầng 0, kiểm tra tổng bậc vào và ra. Tại cùng ndis: 5 điểm trong miền giao, nội suy tuyến tính, bootstrap ghép cặp seed/query 2.000 lần, CI 95% theo từng điểm; ndis được giữ cố định.','','## 4. Kết quả','','### 4.1 Số cạnh và lựa chọn M','', '| Model | Biến thể | M | Các seed 42–46 | Median | Lệch median so với centered |','|---|---|---:|---|---:|---:|']
    for model in ['searle','pic2word']:
        for variant,m in GROUPS:
            rows=[r for r in edges if r['model']==model and r['variant']==variant and r['M']==m]
            lines.append(f"| {model} | {variant} | {m} | {', '.join(str(r['edges']) for r in rows)} | {rows[0]['median_edges']:.0f} | {rows[0]['median_relative_deviation_from_centered']*100:+.2f}% |")
        s=result['selection'][model]; desc='đạt tiêu chí ≤2%' if s['matched_within_2_percent'] else 'không đạt ≤2%, chỉ là mức gần nhất'
        lines += ['',f"**{model}:** chọn original M={s['selected_M']}; lệch median {s['median_relative_deviation']*100:+.2f}% so với centered M=32: {desc}.",'']
    lines += ['### 4.2 Retention tại cùng ndis','']
    for model in ['searle','pic2word']:
        e=result['models'][model]; s=result['selection'][model]
        lines += [f'#### {model.upper()}','']
        if not e['comparison']:
            lines += ['Không có miền ndis chung: chưa thể so tại cùng chi phí.','']; continue
        lines += [f"Miền chung: {e['common_support'][0]:.1f}–{e['common_support'][1]:.1f} phép tính/query.",'',f'![{model}](./c2_{model}.png)','','| ndis | Original | Centered | Chênh lệch điểm % | CI 95% điểm % |','|---:|---:|---:|---:|---:|']
        for p in e['comparison']:
            lines.append(f"| {p['ndis_per_query']:.1f} | {p['original_retention']*100:.2f}% | {p['centered_retention']*100:.2f}% | {p['delta']*100:+.2f} | [{p['ci_lower']*100:+.2f}, {p['ci_upper']*100:+.2f}] |")
        pts=e['comparison']; change=max(abs(p['log_ndis_delta']-p['delta']) for p in pts)*100
        lines += ['',f"Có {sum(p['ci_lower']>0 for p in pts)}/5 CI dương, {sum(p['ci_upper']<0 for p in pts)}/5 CI âm; chênh lệch ước lượng thay đổi tối đa {change:.3f} điểm % khi nội suy theo log ndis. [Hình các mức M](./c2_{model}_all_m.png).",'']
    lines += ['## 5. Kết luận','']
    for model in ['searle','pic2word']:
        s=result['selection'][model]; pts=result['models'][model]['comparison']; matched=s['matched_within_2_percent']
        if not pts: conclusion='Chưa kết luận: không có miền ndis chung.'
        elif not matched: conclusion='So sánh xấp xỉ: không đạt tiêu chí khớp số cạnh; không kết luận ở cùng mật độ.'
        elif all(p['ci_lower']>0 for p in pts): conclusion='Dữ liệu hỗ trợ lợi thế centered ở năm ngân sách trong điều kiện khớp median số cạnh.'
        elif all(p['ci_upper']<0 for p in pts): conclusion='Dữ liệu hỗ trợ original có retention cao hơn ở năm ngân sách khảo sát.'
        else: conclusion='Kết quả khác nhau theo ngân sách hoặc CI chứa 0; không suy ra hai phương án tương đương.'
        lines += [f'**{model}:** {conclusion}','']
    lines += ['## 6. Hạn chế','','Đồ thị dựng đa luồng có thể khác giữa lần chạy; ghép median không bảo đảm từng seed có cùng số cạnh. Chỉ có năm seed; CI không điều chỉnh đa điểm, giữ ndis cố định. Nội suy không thay thế số đo tại mọi ngân sách. Dữ liệu test chưa xác minh ID từng hàng. Workspace dirty, các đầu vào và mã được hash; cấu hình C1 chỉ khác kiểu xuống dòng LF/CRLF, đã xác minh hash sau chuẩn hóa. So sánh không xác lập cơ chế nhân quả.','','## 7. Tiếp theo','','Thực hiện C3 đối chứng L2, sau đó C4–C5 theo kế hoạch R3.','', '[Kết quả JSON](./results.json) · [chọn M](./edge_selection.json) · [bảng số cạnh](./edges.csv) · [sweep](./sweep.csv) · [so sánh](./comparison.csv) · [manifest](./run_manifest.json).']
    (P/'bao_cao_C2.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
