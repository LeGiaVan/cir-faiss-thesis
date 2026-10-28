"""C4 geometry, exact gallery hubness and provenance-checked graph data."""
from pathlib import Path
import sys,json,pickle,hashlib,time,platform,os,datetime
import numpy as np,faiss
from scipy.stats import skew
P=Path(__file__).resolve().parent; ROOT=P.parents[1]; sys.path.insert(0,str(ROOT/'src'))
from phase2.protocol import setup,normalized,search,sha256
DATA=ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data'
SEEDS=[42,43,44,45,46]

def lfhash(p): return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def save(p,obj):
    tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8'); tmp.replace(p)

def main():
    setup(); stage=json.loads((ROOT/'R3/stage0_manifest.json').read_text(encoding='utf-8')); ref=json.loads((ROOT/'R3/C1/run_manifest.json').read_text(encoding='utf-8'))
    inputs={p:sha256(ROOT/p) for p in ref['inputs_sha256']}
    for p,expected in ref['inputs_sha256'].items():
        if inputs[p].upper()!=expected and not (p=='configs/reference.yaml' and lfhash(ROOT/p).upper()==expected): raise ValueError(f'Input hash changed: {p}')
    protocol=ROOT/'src/phase2/protocol.py'; oldscript=ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/run_reference_audit.py'
    for path in [protocol,oldscript]:
        rel=path.relative_to(ROOT).as_posix()
        if lfhash(path).upper()!=stage['frozen_inputs_sha256'][rel]: raise ValueError(f'R2 source changed: {rel}')
    code=sha256(Path(__file__)); sig=hashlib.sha256((json.dumps(inputs,sort_keys=True)+code+sha256(protocol)+faiss.__version__).encode()).hexdigest()
    meta={'module':'R3_C4','created_utc':datetime.datetime.now(datetime.UTC).isoformat(),'signature':sig,'inputs_sha256':inputs,'script_sha256':code,'protocol_sha256':sha256(protocol),'r2_protocol_lf_sha256':lfhash(protocol),'r2_script_lf_sha256':lfhash(oldscript),'git_commit_stage0':stage['repository']['head_commit'],'git_dirty':True,'cpu':os.environ.get('PROCESSOR_IDENTIFIER',platform.processor()),'threads':faiss.omp_get_max_threads(),'faiss':faiss.__version__,'numpy':np.__version__,'seeds':SEEDS,'M':32,'efConstruction':200,'efSearch':128,'gallery_size':123403,'num_queries':1020,'query_identity':'test IDs reconstructed by feature order, not independently verified','r2_checkpoint_policy':'verify full concatenated source, config and input hashes; graph and found from same checkpoint'}
    path=P/'run_manifest.json'
    if path.exists() and json.loads(path.read_text(encoding='utf-8'))['signature']!=sig: raise ValueError('Run signature mismatch')
    if not path.exists(): save(path,meta)
    out=P/'data'; out.mkdir(exist_ok=True)
    for model in ['searle','pic2word']:
        print('Loading',model,flush=True)
        gp=ROOT/f'data/embeddings/{model}/circo_gallery.npy'; qp=DATA/f'circo_1020_queries_{model}.pkl'
        g=normalized(np.load(gp))
        with qp.open('rb') as f: q=normalized(pickle.load(f)['query_features'])
        n,d=g.shape
        if n!=123403 or len(q)!=1020: raise ValueError('Unexpected data shape')
        mu=g.mean(axis=0); gc=np.ascontiguousarray(g-mu,dtype=np.float32)
        norms=np.linalg.norm(gc,axis=1)
        if np.any(norms==0) or not np.isfinite(norms).all(): raise ValueError('Zero or invalid centered vector')
        unit=gc/norms[:,None]; su=np.sum(unit,axis=0,dtype=np.float64); sumsq=np.sum(unit.astype(np.float64)**2)
        mu64=np.mean(g,axis=0,dtype=np.float64); norms0=np.linalg.norm(g,axis=1)
        geo={'n':n,'dimension':d,'mean_norm_original':float(np.linalg.norm(mu64)),'mean_norm_centered':float(np.linalg.norm(np.mean(gc,axis=0,dtype=np.float64))),'mcs_original_unit_formula':float((n*np.dot(mu64,mu64)-1)/(n-1)),'mcs_centered_cosine':float((np.dot(su,su)-sumsq)/(n*(n-1))),'original_norm_max_error':float(np.max(np.abs(norms0-1))),'centered_zero_vectors':int(np.sum(norms==0)),'mcs_centered_note':'cosine measured on normalized centered copy; index is not renormalized'}
        save(out/f'{model}_geometry.json',geo); del unit
        flat=faiss.IndexFlatIP(d); flat.add(g); score,ids=search(flat,q,100); truth=ids[:,:10]
        check=faiss.IndexFlatIP(d); check.add(gc); _,ids_c=search(check,q,10)
        if not np.array_equal(truth,ids_c): raise ValueError('CIR exact rank changed')
        np.savez_compressed(out/f'{model}_queries.npz',truth=truth,s1=score[:,0],s100=score[:,99],n10_query=np.bincount(truth.ravel(),minlength=n),signature=sig)
        del flat,check
        numerical=lfhash(oldscript)+lfhash(protocol)
        expected=sha256(gp)+sha256(qp)+ref['inputs_sha256']['configs/reference.yaml'].lower()+numerical
        for seed in SEEDS:
            for variant in ['before','after']:
                source=DATA/f'reference_{model}_{seed}_{variant}.npz'
                with np.load(source) as ck:
                    if str(ck['signature'])!=expected: raise ValueError(f'R2 checkpoint signature mismatch: {source}')
                    indeg=ck['indegree'].copy(); outdeg=ck['outdegree'].copy(); found=ck['found'].copy()
                if len(indeg)!=n or found.shape!=(len(q),10) or int(indeg.sum())!=int(outdeg.sum()) or not np.isin(found,[0,1]).all(): raise ValueError('Invalid R2 checkpoint')
                dest=out/f'{model}_{seed}_{variant}.npz'; np.savez_compressed(dest,signature=sig,indegree=indeg,outdegree=outdeg,found=found,source_sha256=sha256(source))
        print(model,'R2 graph checkpoints verified',flush=True)
        for variant,X in [('before',g),('after',gc)]:
            final=out/f'{model}_{variant}_n10.npz'
            if final.exists():
                with np.load(final) as z:
                    if str(z['signature'])!=sig or int(z['counts'].sum())!=10*n: raise ValueError('N10 checkpoint mismatch')
                continue
            print(model,variant,'building exact gallery index',flush=True); index=faiss.IndexFlatIP(d); index.add(X)
            counts=np.zeros(n,dtype=np.int64); start=0; progress=out/f'{model}_{variant}_progress.npz'
            if progress.exists():
                with np.load(progress) as z:
                    if str(z['signature'])!=sig: raise ValueError('Progress signature mismatch')
                    counts=z['counts'].copy(); start=int(z['next_row'])
                if int(counts.sum())!=10*start: raise ValueError('Progress count inconsistent')
            batch=256; t0=time.perf_counter()
            for s in range(start,n,batch):
                end=min(s+batch,n); _,i=index.search(X[s:end],11)
                if (i<0).any() or (i>=n).any(): raise ValueError('Invalid gallery neighbor ID')
                for row,neighbors in enumerate(i):
                    keep=neighbors[neighbors!=(s+row)][:10]
                    if len(keep)!=10 or (keep==(s+row)).any(): raise ValueError('Self-removal failed')
                    np.add.at(counts,keep,1)
                if s==start: print(model,variant,'first batch seconds',round(time.perf_counter()-t0,3),'batch',end-s,'estimated remaining batches',(n-end+batch-1)//batch,flush=True)
                if end%4096==0 or end==n:
                    tmp=progress.with_suffix('.tmp.npz'); np.savez_compressed(tmp,signature=sig,counts=counts,next_row=end); tmp.replace(progress)
                    print(model,variant,'rows',end,'/',n,'elapsed_s',round(time.perf_counter()-t0,1),flush=True)
            if int(counts.sum())!=10*n: raise ValueError('N10 sum mismatch')
            tmp=final.with_suffix('.tmp.npz'); np.savez_compressed(tmp,signature=sig,counts=counts); tmp.replace(final)
            stats={'skewness':float(skew(counts)),'zero_count':int((counts==0).sum()),'zero_ratio':float((counts==0).mean()),'max':int(counts.max()),'quantiles':np.quantile(counts,[0,.25,.5,.75,.9,.95,.99,1]).tolist(),'sum':int(counts.sum()),'k':10,'self_removed_by_id':True}
            save(out/f'{model}_{variant}_n10_stats.json',stats)
            del index
    print('C4 acquisition complete',flush=True)

if __name__=='__main__': main()
