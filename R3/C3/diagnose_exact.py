"""Inspect L2 rank differences without modifying experimental inputs."""
from pathlib import Path
import sys,json,pickle
import numpy as np,faiss
P=Path(__file__).resolve().parent; ROOT=P.parents[1]; sys.path.insert(0,str(ROOT/'src'))
from phase2.protocol import setup,normalized,search
setup(); data=ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data'; result={}
for model in ['searle','pic2word']:
    g=normalized(np.load(ROOT/f'data/embeddings/{model}/circo_gallery.npy'))
    with (data/f'circo_1020_queries_{model}.pkl').open('rb') as f: q=normalized(pickle.load(f)['query_features'])
    mu=g.mean(0); gc=np.ascontiguousarray(g-mu,dtype=np.float32); qc=np.ascontiguousarray(q-mu,dtype=np.float32)
    a=faiss.IndexFlatL2(g.shape[1]); a.add(g); da,ia=search(a,q,11)
    b=faiss.IndexFlatL2(g.shape[1]); b.add(gc); db,ib=search(b,qc,11)
    diffs=[]
    for i in np.flatnonzero(np.any(ia[:,:10]!=ib[:,:10],axis=1)):
        ids=[int(j) for j in sorted(set(ia[i,:11])|set(ib[i,:11]))]; orig=np.sum((g[ids].astype(np.float64)-q[i].astype(np.float64))**2,axis=1); cent=np.sum((gc[ids].astype(np.float64)-qc[i].astype(np.float64))**2,axis=1)
        diffs.append({'row_index':int(i),'same_top10_set':set(ia[i,:10])==set(ib[i,:10]),'original_ids':ia[i,:11].tolist(),'centered_ids':ib[i,:11].tolist(),'original_distances':da[i,:11].tolist(),'centered_distances':db[i,:11].tolist(),'candidate_ids':ids,'candidate_l2_float64_original':orig.tolist(),'candidate_l2_float64_centered':cent.tolist()})
    result[model]={'different_order_rows':len(diffs),'different_top10_sets':sum(not x['same_top10_set'] for x in diffs),'rows':diffs}
    print(model,'different_order_rows',len(diffs),'different_top10_sets',result[model]['different_top10_sets'],flush=True)
(P/'exact_diagnostics.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
