"""C4 grouped degree, transitions and paired bootstrap from verified inputs."""
from pathlib import Path
import json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent; D=P/'data'; SEEDS=[42,43,44,45,46]

def write_csv(path,rows):
    if not rows:return
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    meta=json.loads((P/'run_manifest.json').read_text(encoding='utf-8')); result={'metadata':meta,'models':{},'bootstrap_replicates':2000,'bins':'pooled before/after exact-neighbor occurrences; unique quintile boundaries'}
    group_rows=[]; trans_rows=[]
    for model in ['searle','pic2word']:
        with np.load(D/f'{model}_queries.npz') as z:
            if str(z['signature'])!=meta['signature']: raise ValueError('query signature mismatch')
            truth=z['truth'].copy(); nquery=z['n10_query'].copy()
        nq=truth.shape[0]; geom=json.loads((D/f'{model}_geometry.json').read_text(encoding='utf-8')); summary={}
        for variant in ['before','after']:
            with np.load(D/f'{model}_{variant}_n10.npz') as z:
                if str(z['signature'])!=meta['signature'] or int(z['counts'].sum())!=10*geom['n']: raise ValueError('N10 invalid')
            summary[variant]=json.loads((D/f'{model}_{variant}_n10_stats.json').read_text(encoding='utf-8'))
        deg={};miss={}; gallery_degree={}
        for variant in ['before','after']:
            dd=[];mm=[];gg=[]
            for seed in SEEDS:
                with np.load(D/f'{model}_{seed}_{variant}.npz') as z:
                    if str(z['signature'])!=meta['signature']: raise ValueError('graph signature mismatch')
                    d=z['indegree']; dd.append(d[truth]); mm.append(1-z['found']); gg.append({'seed':seed,'mean':float(np.mean(d)),'quantiles':np.quantile(d,[0,.25,.5,.75,.95,1]).tolist(),'zero_count':int((d==0).sum())})
            deg[variant]=np.stack(dd); miss[variant]=np.stack(mm); gallery_degree[variant]=gg
        edges=np.unique(np.quantile(np.concatenate([deg['before'].ravel(),deg['after'].ravel()]),[0,.2,.4,.6,.8,1]))
        if len(edges)<2:raise ValueError('No degree variation')
        bins={v:np.searchsorted(edges[1:-1],deg[v],side='right') for v in ['before','after']}; nb=len(edges)-1
        rng=np.random.default_rng(42); indices=[(rng.integers(0,5,5),rng.integers(0,nq,nq)) for _ in range(2000)]
        for group in range(nb):
            row={'model':model,'bin':group,'lower':float(edges[group]),'upper':float(edges[group+1]),'note':'left closed, right open except final bin'}
            for variant in ['before','after']:
                mask=bins[variant]==group; row[f'{variant}_rows']=int(mask.sum());row[f'{variant}_queries']=int(mask.any(axis=(0,2)).sum());row[f'{variant}_images']=int(np.unique(np.broadcast_to(truth,mask.shape)[mask]).size)
                row[f'{variant}_miss_rate']=float(miss[variant][mask].mean()) if mask.any() else None
            same=(bins['before']==group)&(bins['after']==group); row['same_group_rows']=int(same.sum()); row['same_group_queries']=int(same.any(axis=(0,2)).sum());row['same_group_images']=int(np.unique(np.broadcast_to(truth,same.shape)[same]).size)
            difference=miss['after']-miss['before'];row['same_group_delta_miss']=float(difference[same].mean()) if same.any() else None
            dist=[]; marginal=[]
            for si,qi in indices:
                mask=same[si][:,qi,:]; v=difference[si][:,qi,:]
                if mask.any():dist.append(float(v[mask].mean()))
                mb=(bins['before'][si][:,qi,:]==group); ma=(bins['after'][si][:,qi,:]==group)
                if mb.any() and ma.any(): marginal.append(float(miss['after'][si][:,qi,:][ma].mean()-miss['before'][si][:,qi,:][mb].mean()))
            row['same_group_ci_low']=float(np.percentile(dist,2.5)) if dist else None; row['same_group_ci_high']=float(np.percentile(dist,97.5)) if dist else None; row['valid_bootstrap']=len(dist)
            row['conditional_delta_miss']=(row['after_miss_rate']-row['before_miss_rate']) if row['after_miss_rate'] is not None and row['before_miss_rate'] is not None else None
            row['conditional_ci_low']=float(np.percentile(marginal,2.5)) if marginal else None;row['conditional_ci_high']=float(np.percentile(marginal,97.5)) if marginal else None;row['conditional_valid_bootstrap']=len(marginal)
            group_rows.append(row)
        for i in range(nb):
            for j in range(nb):
                m=(bins['before']==i)&(bins['after']==j);dist=[]
                for si,qi in indices: dist.append(float(m[si][:,qi,:].mean()))
                trans_rows.append({'model':model,'from_bin':i,'to_bin':j,'rows':int(m.sum()),'proportion':float(m.mean()),'ci_low':float(np.percentile(dist,2.5)),'ci_high':float(np.percentile(dist,97.5))})
        result['models'][model]={'geometry':geom,'n10':summary,'degree_bins':edges.tolist(),'gallery_indegree':gallery_degree,'exact_neighbor_indegree':{v:{'quantiles':np.quantile(deg[v],[0,.25,.5,.75,.95,1]).tolist(),'mean':float(deg[v].mean())} for v in ['before','after']},'overall_miss':{v:float(miss[v].mean()) for v in ['before','after']},'n10_query_coverage':int((nquery>0).sum())}
        fig,ax=plt.subplots(figsize=(7,4));x=np.arange(nb); data=[r for r in group_rows if r['model']==model]
        ax.plot(x,[100*r['before_miss_rate'] if r['before_miss_rate'] is not None else np.nan for r in data],marker='o',label='Original');ax.plot(x,[100*r['after_miss_rate'] if r['after_miss_rate'] is not None else np.nan for r in data],marker='o',label='Centered');ax.set_xlabel('Nhóm bậc vào (ngưỡng chung)');ax.set_ylabel('Miss rate (%)');ax.set_title(model.upper());ax.grid(alpha=.25);ax.legend();fig.tight_layout();fig.savefig(P/f'c4_{model}_miss.png',dpi=160);plt.close(fig)
    write_csv(P/'degree_groups.csv',group_rows);write_csv(P/'degree_transitions.csv',trans_rows)
    (P/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print('Degree and geometry analysis complete',flush=True)

if __name__=='__main__':main()
