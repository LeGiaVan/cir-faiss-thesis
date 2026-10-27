"""P1/P2b: shared-config reference, five paired HNSW builds, full rank check."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
import datetime
import json
import pickle
import shutil
import time
import numpy as np
import pandas as pd
import faiss
from scipy.stats import skew,kurtosis
from phase2.protocol import setup,metadata,write_json,normalized,search,hnsw,graph_degrees,sha256,timed_search

MODULE=Path(__file__).resolve().parent.parent
DATA=MODULE/'data';RESULTS=MODULE/'results';PLOTS=MODULE/'plots'


def bootstrap_paired(values, n_boot, seed):
    """Resample build pairs and query clusters independently; retain before/after pairing."""
    rng=np.random.default_rng(seed);b,n=values.shape
    dist=np.empty(n_boot)
    for i in range(n_boot):
        builds=rng.integers(b,size=b);queries=rng.integers(n,size=n)
        dist[i]=values[np.ix_(builds,queries)].mean()
    return {'mean':float(values.mean()),'ci_lower':float(np.percentile(dist,2.5)),
            'ci_upper':float(np.percentile(dist,97.5)),
            'method':'crossed bootstrap of paired build seeds and query IDs; percentile',
            'n_bootstrap':n_boot,'n_builds':b,'n_queries':n}


def hub_stats(counts):
    return {'skewness':float(skew(counts)),'kurtosis':float(kurtosis(counts)),
            'antihub_ratio':float((counts==0).mean()),'max_hub':int(counts.max())}


def degree_stats(indeg,outdeg):
    return {'indegree_mean':float(indeg.mean()),'indegree_zero_ratio':float((indeg==0).mean()),
            'indegree_max':int(indeg.max()),'indegree_skewness':float(skew(indeg)),
            'outdegree_mean':float(outdeg.mean()),'outdegree_zero_ratio':float((outdeg==0).mean()),
            'edges':int(indeg.sum())}


def main():
    cfg=setup();seeds=cfg['audit']['hnsw_build_seeds'];k=cfg['datasets']['circo']['k_eval']
    for p in [DATA,RESULTS,PLOTS]:p.mkdir(parents=True,exist_ok=True)
    archive=MODULE.parent/'archive/pre_p0_p1_p2b/a1'
    for folder in ['results','plots']:
        (archive/folder).mkdir(parents=True,exist_ok=True)
        for p in (MODULE/folder).glob('*'):
            if p.is_file() and not (archive/folder/p.name).exists():shutil.copy2(p,archive/folder/p.name)
    (archive/'data').mkdir(exist_ok=True)
    old=DATA/'neighbor_level_data.parquet'
    if old.exists() and not (archive/'data'/old.name).exists():shutil.copy2(old,archive/'data'/old.name)
    summaries={};center={};frames=[];inputs=[];query_manifest={};all_rets=[]
    ann_paths=[ROOT/f'data/annotations/circo/{split}.json' for split in ['val','test']]
    annotations=[json.loads(p.read_text(encoding='utf-8')) for p in ann_paths]
    ids=[f'{split}:{r["id"]}' for split,items in zip(['val','test'],annotations) for r in items]
    expected=cfg['datasets']['circo']['query_profiles']['val_test_retention']['num_queries']
    if len(ids)!=expected or len(set(ids))!=expected:raise ValueError('Invalid query IDs')
    numerical_code_hash = sha256(Path(__file__)) + sha256(ROOT/'src/phase2/protocol.py')
    for model in ['searle','pic2word']:
        gp=ROOT/f'data/embeddings/{model}/circo_gallery.npy';qp=DATA/f'circo_1020_queries_{model}.pkl'
        vp=ROOT/f'data/queries/{model}/circo_queries.pkl';paths=[gp,qp,vp,*ann_paths];inputs.extend(paths)
        print(f'Loading {model}',flush=True)
        g=normalized(np.load(gp));bundle=pickle.load(qp.open('rb'));q=normalized(bundle['query_features'])
        val=pickle.load(vp.open('rb'));v=normalized(val['query_features'])
        if len(q)!=expected or not np.allclose(q[:len(v)],v,atol=2e-6):raise ValueError('Val feature prefix mismatch')
        canonical=lambda values:sorted(str(int(x)) for x in values)
        if any(canonical(a)!=canonical(b['gt_img_ids']) for a,b in zip(val['target_ids'],annotations[0])):
            raise ValueError('Val target order differs from annotations')
        query_manifest[model]={'query_ids':ids,'query_file_sha256':sha256(qp),
                              'val_alignment':'verified feature prefix and GT order against val annotations',
                              'test_alignment':'reconstructed from step0 extraction loop and test annotation order; original bundle has no per-row IDs',
                              'normalization':'L2 before search'}
        n,d=g.shape;flat=faiss.IndexFlatIP(d);flat.add(g)
        scores,exact=search(flat,q,100);truth=exact[:,:k]
        counts=np.bincount(truth.ravel(),minlength=n)
        gc=np.ascontiguousarray(g-g.mean(axis=0),dtype=np.float32)
        flat_c=faiss.IndexFlatIP(d);flat_c.add(gc)
        score_c,ids_c=search(flat_c,q,k)
        rank_ok=bool(np.array_equal(truth,ids_c))
        if not rank_ok:raise ValueError('Exact top-k changed; inspect near ties before proceeding')
        shift=np.einsum('ij,j->i',q,g.mean(axis=0))
        residual=float(np.max(np.abs(score_c-(scores[:,:k]-shift[:,None]))))
        before=[];after=[];builds=[];parent_meta=metadata('module_a1_hubness',inputs=paths,model=model,
             gallery_size=n,num_queries=len(q),index_config=cfg['hnsw']['reference'],query_profile='val_test_retention')
        sig=sha256(gp)+sha256(qp)+parent_meta['config_sha256']+numerical_code_hash
        for seed in seeds:
            rets={};dg={};durations={}
            for variant,gallery in [('before',g),('after',gc)]:
                cache=DATA/f'reference_{model}_{seed}_{variant}.npz'
                # Only reuse checkpoints created under the identical config AND source/data hashes.
                if cache.exists():
                    ck=np.load(cache)
                    reuse=str(ck['signature'])==sig
                else:reuse=False
                if reuse:
                    found=ck['found'];indeg=ck['indegree'];outdeg=ck['outdegree'];duration=float(ck['build_seconds'])
                    timing=json.loads(str(ck['timing']))
                    print(f'{model} seed={seed} {variant}: reuse checkpoint',flush=True)
                else:
                    print(f'{model} seed={seed} {variant}: build HNSW',flush=True);t=time.perf_counter()
                    idx=hnsw(gallery,seed);duration=time.perf_counter()-t
                    _,approx,timing=timed_search(idx,q,k)
                    found=np.array([[int(j in set(a)) for j in tr] for a,tr in zip(approx,truth)],dtype=np.int8)
                    indeg,outdeg=graph_degrees(idx)
                    np.savez_compressed(cache,found=found,indegree=indeg,outdegree=outdeg,signature=sig,
                                        build_seconds=duration,timing=json.dumps(timing))
                    del idx
                rets[variant]=found.mean(axis=1);dg[variant]=degree_stats(indeg,outdeg);durations[variant]=duration
                all_rets.extend({'model':model,'seed':seed,'variant':variant,'query_id':qid,'retention':float(ret)} for qid,ret in zip(ids,rets[variant]))
                if seed==seeds[0] and variant=='before':
                    frame=pd.DataFrame({'model':model,'query_id':np.repeat(ids,k),'neighbor_id':truth.ravel(),
                        'rank':np.tile(np.arange(1,k+1),len(q)),'missed':(1-found).ravel(),
                        'k_occurrence':counts[truth].ravel(),'in_degree_hnsw':indeg[truth].ravel(),
                        's1':np.repeat(scores[:,0],k),'c_contrast':np.repeat(scores[:,0]-scores[:,99],k)})
                    frames.append(frame)
                    summaries[model]={'n_rows':len(frame),'n_queries':len(q),'n_gallery':n,'dim':d,
                        'overall_miss_rate':float(frame.missed.mean()),'retention_at_10':float(rets[variant].mean()),
                        'antihub_gallery_count':int((counts==0).sum()),'antihub_gallery_ratio':float((counts==0).mean()),
                        'k_occurrence_skewness':float(skew(counts)),'in_degree_indeg0_ratio':float((indeg==0).mean()),
                        'primary_seed':seed,'graph':dg[variant]}
                builds.append({'seed':seed,'variant':variant,'retention_at_10':float(rets[variant].mean()),
                               'graph':dg[variant],'build_seconds':duration,'latency':timing})
                print(f'{model} seed={seed} {variant}: retention={rets[variant].mean():.6f}, build={duration:.1f}s',flush=True)
            before.append(rets['before']);after.append(rets['after'])
        b=np.array(before);a=np.array(after)
        delta=bootstrap_paired(a-b,cfg['audit']['bootstrap_replicates'],cfg['experiment_metadata']['random_seed'])
        center[model]={'rank_invariance_verified':rank_ok,'rank_check_queries':len(q),
            'max_score_identity_residual':residual,'centering_variant':'subtract_gallery_mean_without_renormalization',
            'before':{**hub_stats(counts),'retention_at_10':float(b.mean())},
            'after':{**hub_stats(counts),'retention_at_10':float(a.mean())},
            'delta_retention':float((a-b).mean()),'delta_skewness':0.0,'paired_delta_ci':delta,
            'per_seed_delta':[float(x) for x in (a-b).mean(axis=1)],'builds':builds,
            'indegree_mean_before':float(np.mean([r['graph']['indegree_mean'] for r in builds if r['variant']=='before'])),
            'indegree_mean_after':float(np.mean([r['graph']['indegree_mean'] for r in builds if r['variant']=='after']))}
        write_json(RESULTS/f'centering_{model}_checkpoint.json',{'metadata':parent_meta,'results':center[model]})
    write_json(DATA/'query_manifest.json',{'metadata':metadata('a1_query_manifest',inputs=ann_paths,model=['searle','pic2word'],num_queries=expected,profile='val_test_retention'), 'ids':ids,'models':query_manifest,
                                         'limitations':'test IDs reconstructed, not embedded in original feature bundle'})
    combined=pd.concat(frames,ignore_index=True);combined.to_parquet(DATA/'neighbor_level_data.parquet',index=False)
    pd.DataFrame(all_rets).to_parquet(DATA/'centering_per_query.parquet',index=False)
    meta=metadata('module_a1_hubness',inputs=list(dict.fromkeys(inputs))+[DATA/'query_manifest.json'],
        model=['searle','pic2word'],gallery_size={m:s['n_gallery'] for m,s in summaries.items()},
        num_queries=expected,index_config=cfg['hnsw']['reference'],query_profile='val_test_retention',
        normalization='gallery/query L2; centered gallery not renormalized',build_seeds=seeds,
        nondeterminism_note='OpenMP HNSW insertion may differ even with identical RNG seed',
        query_alignment_limitations=query_manifest['searle']['test_alignment'])
    write_json(RESULTS/'step1_hnsw_indegree.json',{'metadata':{**meta,'step':'step1_build_neighbor_dataset','primary_seed':seeds[0]},'results':summaries})
    write_json(RESULTS/'step4_centering.json',{'metadata':{**meta,'step':'step4_centering','centering_variant':'subtract_gallery_mean_without_renormalization','aggregation':'mean over build seeds and queries'},'results':center,'causal_label':{m:'inconclusive_for_hubness_causality' for m in center}})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots();x=np.arange(2)
    ax.bar(x-.17,[center[m]['before']['retention_at_10']*100 for m in center],.34,label='Before (5 builds)')
    ax.bar(x+.17,[center[m]['after']['retention_at_10']*100 for m in center],.34,label='Centered (5 builds)')
    ax.set_xticks(x,list(center));ax.set_ylabel('Retention@10 (%)');ax.legend();fig.tight_layout();fig.savefig(PLOTS/'fig3_centering_before_after.png',dpi=160);plt.close(fig)
    print('Reference A.1 complete; run step2, step3 and report renderer.',flush=True)


if __name__=='__main__':main()
