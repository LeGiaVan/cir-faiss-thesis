"""R3 C1: paired HNSW search-cost sweep; resumable, immutable input hashes."""
from pathlib import Path
import sys, json, pickle, time, hashlib, platform, os, datetime
import numpy as np
import faiss

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from phase2.protocol import setup, normalized, search, sha256, timed_search

EF = [32, 48, 64, 96, 128, 160, 192, 256, 384]
SEEDS = [42, 43, 44, 45, 46]
VARIANTS = ['original_ip', 'centered_ip', 'centered_l2']
DATA = ROOT / 'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data'

def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')

def main():
    cfg = setup()
    stage = json.loads((HERE.parent/'stage0_manifest.json').read_text(encoding='utf-8'))
    paths = ['configs/reference.yaml'] + [f'data/embeddings/{m}/circo_gallery.npy' for m in ['searle','pic2word']] + [f'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/circo_1020_queries_{m}.pkl' for m in ['searle','pic2word']]
    hashes = {p: sha256(ROOT/p).upper() for p in paths}
    for p in paths:
        if hashes[p] != stage['frozen_inputs_sha256'][p]:
            raise RuntimeError(f'Input hash differs from stage 0: {p}')
    signature = hashlib.sha256((json.dumps(hashes,sort_keys=True)+sha256(Path(__file__))).encode()).hexdigest()
    meta = {'timestamp_utc': datetime.datetime.now(datetime.UTC).isoformat(), 'module':'R3_C1', 'signature':signature, 'inputs_sha256':hashes, 'script_sha256':sha256(Path(__file__)), 'git_commit_stage0':stage['repository']['head_commit'], 'git_dirty':True, 'provenance_note':'Input hashes pinned; working tree dirty and test feature row IDs are reconstructed, not independently verified.', 'cpu':os.environ.get('PROCESSOR_IDENTIFIER',platform.processor()), 'threads':faiss.omp_get_max_threads(), 'python':platform.python_version(), 'faiss':faiss.__version__, 'numpy':np.__version__, 'seeds':SEEDS, 'efSearch':EF, 'M':32, 'efConstruction':200, 'k':10, 'query_count':1020, 'latency':'1 warmup, 7 measured runs, median ms/query, batch size 1 including Python overhead'}
    save(HERE/'run_manifest.json',meta)
    out=HERE/'data'; out.mkdir(exist_ok=True)
    for model in ['searle','pic2word']:
        print('Loading', model, flush=True)
        g=normalized(np.load(ROOT/f'data/embeddings/{model}/circo_gallery.npy'))
        with (DATA/f'circo_1020_queries_{model}.pkl').open('rb') as f: q=normalized(pickle.load(f)['query_features'])
        if g.shape[0] != 123403 or q.shape[0] != 1020: raise ValueError('Unexpected input shape')
        mu=g.mean(axis=0); gc=np.ascontiguousarray(g-mu,dtype=np.float32); qc=np.ascontiguousarray(q-mu,dtype=np.float32)
        flat=faiss.IndexFlatIP(g.shape[1]); flat.add(g); score,truth=search(flat,q,10)
        flatc=faiss.IndexFlatIP(g.shape[1]); flatc.add(gc); scorec,truthc=search(flatc,q,10)
        if not np.array_equal(truth,truthc): raise ValueError('Exact IP top-10 differs after centering')
        residual=float(np.max(np.abs(scorec-(score-(q@mu)[:,None]))))
        del flat,flatc
        flatl=faiss.IndexFlatL2(g.shape[1]); flatl.add(gc); _,truthl=search(flatl,qc,10); del flatl
        save(out/f'{model}_exact.json',{'ip_top10_identical':True,'ip_max_score_shift_residual':residual,'n_queries':len(q),'n_gallery':len(g),'dimension':g.shape[1], 'l2_truth':'centered gallery and centered query; separate exact L2 ranking'})
        for seed in SEEDS:
            for variant in VARIANTS:
                path=out/f'{model}_{seed}_{variant}.npz'
                if path.exists():
                    with np.load(path) as ck:
                        if str(ck['signature'])!=signature: raise ValueError(f'Checkpoint signature mismatch: {path}')
                    print('Reuse',path.name,flush=True); continue
                print('Build',model,seed,variant,flush=True); t=time.perf_counter()
                gallery=g if variant=='original_ip' else gc
                queries=qc if variant=='centered_l2' else q
                gt=truthl if variant=='centered_l2' else truth
                metric=faiss.METRIC_L2 if variant=='centered_l2' else faiss.METRIC_INNER_PRODUCT
                idx=faiss.IndexHNSWFlat(g.shape[1],32,metric)
                idx.hnsw.rng=faiss.RandomGenerator(seed); idx.hnsw.efConstruction=200; idx.add(gallery)
                build=time.perf_counter()-t; records=[]; all_ids=[]; all_ret=[]
                for ef in EF:
                    idx.hnsw.efSearch=ef
                    faiss.cvar.hnsw_stats.reset()
                    _,ids=search(idx,queries,10)
                    ndis=faiss.cvar.hnsw_stats.ndis/len(q)
                    ret=(ids[:,:,None]==gt[:,None,:]).any(axis=2).sum(axis=1)/10.0
                    _,_,timing=timed_search(idx,queries,10)
                    records.append({'efSearch':ef,'ndis_per_query':ndis,'retention':float(ret.mean()),'latency':timing})
                    all_ids.append(ids); all_ret.append(ret)
                    print(model,seed,variant,ef,round(ndis,1),round(ret.mean(),5),flush=True)
                tmp=path.with_suffix('.tmp.npz')
                np.savez_compressed(tmp, signature=signature, records=json.dumps(records), ids=np.array(all_ids), retention=np.array(all_ret), build_seconds=build)
                tmp.replace(path)
                del idx
    print('C1 sweep complete',flush=True)

if __name__=='__main__': main()
