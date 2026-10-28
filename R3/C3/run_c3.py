"""C3 negative control: translating both sides under squared L2."""
from pathlib import Path
import sys, json, pickle, hashlib, platform, os, datetime
import numpy as np
import faiss

P=Path(__file__).resolve().parent; ROOT=P.parents[1]; sys.path.insert(0,str(ROOT/'src'))
from phase2.protocol import setup, normalized, search, sha256, graph_degrees
SEEDS=[42,43,44,45,46]; DATA=ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data'

def save(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def main():
    setup(); ref=json.loads((P.parent/'C1/run_manifest.json').read_text(encoding='utf-8'))
    hashes={p:sha256(ROOT/p).upper() for p in ref['inputs_sha256']}
    config='configs/reference.yaml'; norm=hashlib.sha256((ROOT/config).read_bytes().replace(b'\r\n',b'\n')).hexdigest().upper()
    for p,h in hashes.items():
        if h!=ref['inputs_sha256'][p] and not (p==config and norm==ref['inputs_sha256'][p]): raise ValueError(f'Input changed: {p}')
    script=sha256(Path(__file__)); protocol=sha256(ROOT/'src/phase2/protocol.py')
    sig=hashlib.sha256((json.dumps(hashes,sort_keys=True)+script+protocol+faiss.__version__).encode()).hexdigest()
    meta={'module':'R3_C3','timestamp_utc':datetime.datetime.now(datetime.UTC).isoformat(),'signature':sig,'inputs_sha256':hashes,'config_lf_normalized_sha256':norm,'script_sha256':script,'protocol_sha256':protocol,'git_commit_stage0':ref['git_commit_stage0'],'git_dirty':True,'cpu':os.environ.get('PROCESSOR_IDENTIFIER',platform.processor()),'threads':faiss.omp_get_max_threads(),'python':platform.python_version(),'faiss':faiss.__version__,'numpy':np.__version__,'seeds':SEEDS,'M':32,'efConstruction':200,'efSearch':128,'metric':'squared L2','distance_absolute_tolerance':1e-5,'random_pair_count':10000,'random_pair_seed':42,'query_id_provenance':'800 test IDs reconstructed by row order and not independently verified'}
    manifest=P/'run_manifest.json'
    if manifest.exists() and json.loads(manifest.read_text(encoding='utf-8'))['signature']!=sig: raise ValueError('Existing manifest differs')
    if not manifest.exists(): save(manifest,meta)
    out=P/'data'; out.mkdir(exist_ok=True)
    for model in ['searle','pic2word']:
        print('Loading',model,flush=True)
        g=normalized(np.load(ROOT/f'data/embeddings/{model}/circo_gallery.npy'))
        with (DATA/f'circo_1020_queries_{model}.pkl').open('rb') as f: q=normalized(pickle.load(f)['query_features'])
        if len(g)!=123403 or len(q)!=1020: raise ValueError('Unexpected input dimensions')
        mu=g.mean(axis=0); gc=np.ascontiguousarray(g-mu,dtype=np.float32); qc=np.ascontiguousarray(q-mu,dtype=np.float32)
        a=faiss.IndexFlatL2(g.shape[1]); a.add(g); da,ia=search(a,q,10)
        b=faiss.IndexFlatL2(g.shape[1]); b.add(gc); db,ib=search(b,qc,10)
        rng=np.random.default_rng(42); qi=rng.integers(len(q),size=10000); gi=rng.integers(len(g),size=10000)
        d0=np.sum((q[qi].astype(np.float64)-g[gi])**2,axis=1); d1=np.sum((qc[qi].astype(np.float64)-gc[gi])**2,axis=1)
        audit={'identical_top10':bool(np.array_equal(ia,ib)),'different_top10_rows':int(np.any(ia!=ib,axis=1).sum()),'max_top10_distance_error':float(np.max(np.abs(da-db))),'max_sampled_pair_distance_error':float(np.max(np.abs(d0-d1))),'tolerance_squared_l2':1e-5,'n_sampled_pairs':10000,'n_queries':len(q),'n_gallery':len(g),'dimension':g.shape[1]}
        save(out/f'{model}_exact.json',audit)
        if not audit['identical_top10'] or max(audit['max_top10_distance_error'],audit['max_sampled_pair_distance_error'])>1e-5: raise ValueError(f'{model} exact L2 invariance failed; inspect near ties and precision')
        del a,b
        for seed in SEEDS:
            for variant in ['original_l2','centered_l2']:
                path=out/f'{model}_{seed}_{variant}.npz'
                if path.exists():
                    with np.load(path) as ck:
                        if str(ck['signature'])!=sig: raise ValueError('Checkpoint signature mismatch')
                    continue
                print('Build',model,seed,variant,flush=True)
                idx=faiss.IndexHNSWFlat(g.shape[1],32,faiss.METRIC_L2); idx.hnsw.rng=faiss.RandomGenerator(seed)
                idx.hnsw.efConstruction=200; idx.hnsw.efSearch=128; idx.add(g if variant=='original_l2' else gc)
                indeg,outdeg=graph_degrees(idx); faiss.cvar.hnsw_stats.reset()
                _,ids=search(idx,q if variant=='original_l2' else qc,10); ndis=faiss.cvar.hnsw_stats.ndis/len(q)
                ret=(ids[:,:,None]==ia[:,None,:]).any(axis=2).sum(axis=1)/10
                tmp=path.with_suffix('.tmp.npz'); np.savez_compressed(tmp,signature=sig,ids=ids,retention=ret,ndis=ndis,edges=int(indeg.sum()))
                tmp.replace(path); print('Done',model,seed,variant,float(ret.mean()),ndis,int(indeg.sum()),flush=True)
    print('C3 acquisition complete',flush=True)

if __name__=='__main__': main()
