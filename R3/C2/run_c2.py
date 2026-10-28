"""C2 acquisition: seed checkpoints with actual layer-zero edges and sweep."""
from pathlib import Path
import sys, json, pickle, time, hashlib, platform, os, datetime
import numpy as np
import faiss

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from phase2.protocol import setup, normalized, search, sha256, timed_search, graph_degrees

EF=[32,48,64,96,128,160,192,256,384]
SEEDS=[42,43,44,45,46]
DATA=ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data'

def save(path,obj):
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    tmp.replace(path)

def main():
    cfg=setup()
    ref=json.loads((HERE.parent/'C1/run_manifest.json').read_text(encoding='utf-8'))
    hashes={p:sha256(ROOT/p).upper() for p in ref['inputs_sha256']}
    config_path='configs/reference.yaml'
    normalized_config_sha=hashlib.sha256((ROOT/config_path).read_bytes().replace(b'\r\n',b'\n')).hexdigest().upper()
    for p,expected in ref['inputs_sha256'].items():
        if hashes[p]!=expected and not (p==config_path and normalized_config_sha==expected):
            raise ValueError(f'C1 input hash mismatch: {p}')
    protocol=ROOT/'src/phase2/protocol.py'
    script_hash=sha256(Path(__file__)); protocol_hash=sha256(protocol)
    signature=hashlib.sha256((json.dumps(hashes,sort_keys=True)+script_hash+protocol_hash+faiss.__version__).encode()).hexdigest()
    manifest={'timestamp_utc':datetime.datetime.now(datetime.UTC).isoformat(),'module':'R3_C2','signature':signature,'inputs_sha256':hashes,'config_lf_normalized_sha256':normalized_config_sha,'config_expected_c1_sha256':ref['inputs_sha256'][config_path],'config_change':'CRLF normalized to LF matches exact C1 bytes','script_sha256':script_hash,'protocol_sha256':protocol_hash,'git_commit_stage0':ref['git_commit_stage0'],'git_dirty':True,'provenance_note':'Dirty workspace; inputs and code hashed. Test feature row IDs reconstructed and not independently verified.','cpu':os.environ.get('PROCESSOR_IDENTIFIER',platform.processor()),'threads':faiss.omp_get_max_threads(),'python':platform.python_version(),'faiss':faiss.__version__,'numpy':np.__version__,'seeds':SEEDS,'efSearch':EF,'original_M':[32,40,48,64],'centered_M':32,'efConstruction':200,'gallery_size':123403,'num_queries':1020,'k':10,'layer_edge_definition':'directed nonnegative neighbor entries on layer 0','latency':'1 warmup, 7 measured runs, median ms/query, batch size 1; includes Python overhead'}
    old=HERE/'run_manifest.json'
    if old.exists() and json.loads(old.read_text(encoding='utf-8'))['signature']!=signature: raise ValueError('Existing run signature differs')
    if not old.exists(): save(old,manifest)
    out=HERE/'data'; out.mkdir(exist_ok=True)
    for model in ['searle','pic2word']:
        print('Loading',model,flush=True)
        g=normalized(np.load(ROOT/f'data/embeddings/{model}/circo_gallery.npy'))
        with (DATA/f'circo_1020_queries_{model}.pkl').open('rb') as f: q=normalized(pickle.load(f)['query_features'])
        if len(g)!=123403 or len(q)!=1020: raise ValueError('Unexpected input shape')
        mu=g.mean(axis=0); gc=np.ascontiguousarray(g-mu,dtype=np.float32)
        flat=faiss.IndexFlatIP(g.shape[1]); flat.add(g); scores,truth=search(flat,q,10)
        centered=faiss.IndexFlatIP(g.shape[1]); centered.add(gc); scores_c,truth_c=search(centered,q,10)
        if not np.array_equal(truth,truth_c): raise ValueError('Exact top-10 differs')
        residual=float(np.max(np.abs(scores_c-(scores-(q@mu)[:,None]))))
        save(out/f'{model}_exact.json',{'ip_top10_identical':True,'ip_max_score_shift_residual':residual,'n_queries':len(q),'n_gallery':len(g),'dimension':g.shape[1]})
        del flat,centered
        for variant,m in [('centered_ip',32),('original_ip',32),('original_ip',40),('original_ip',48),('original_ip',64)]:
            for seed in SEEDS:
                path=out/f'{model}_{variant}_M{m}_{seed}.npz'
                if path.exists():
                    with np.load(path) as ck:
                        if str(ck['signature'])!=signature: raise ValueError(f'Checkpoint mismatch {path}')
                    print('Reuse',path.name,flush=True); continue
                print('Build',model,variant,m,seed,flush=True); t=time.perf_counter()
                idx=faiss.IndexHNSWFlat(g.shape[1],m,faiss.METRIC_INNER_PRODUCT)
                idx.hnsw.rng=faiss.RandomGenerator(seed); idx.hnsw.efConstruction=200
                idx.add(gc if variant=='centered_ip' else g)
                duration=time.perf_counter()-t
                indeg,outdeg=graph_degrees(idx)
                edges=int(indeg.sum())
                if edges!=int(outdeg.sum()): raise ValueError('Edge counts inconsistent')
                print('Edges',model,variant,m,seed,edges,flush=True)
                records=[]; all_ids=[]; all_ret=[]
                for ef in EF:
                    idx.hnsw.efSearch=ef; faiss.cvar.hnsw_stats.reset()
                    _,ids=search(idx,q,10); ndis=faiss.cvar.hnsw_stats.ndis/len(q)
                    ret=(ids[:,:,None]==truth[:,None,:]).any(axis=2).sum(axis=1)/10.0
                    _,_,timing=timed_search(idx,q,10)
                    records.append({'efSearch':ef,'ndis_per_query':ndis,'retention':float(ret.mean()),'latency':timing})
                    all_ids.append(ids); all_ret.append(ret)
                    print(model,variant,m,seed,ef,round(ndis,1),round(ret.mean(),5),flush=True)
                tmp=path.with_suffix('.tmp.npz')
                np.savez_compressed(tmp,signature=signature,records=json.dumps(records),ids=np.array(all_ids),retention=np.array(all_ret),build_seconds=duration,edges=edges,nodes=len(g),mean_outdegree=float(outdeg.mean()))
                tmp.replace(path); del idx
    print('Acquisition complete',flush=True)

if __name__=='__main__': main()
