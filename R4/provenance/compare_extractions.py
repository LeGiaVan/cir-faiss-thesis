"""Compare ID-tagged test re-extraction to R2 cache with predeclared tolerance."""
from pathlib import Path
import json,pickle,hashlib
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
COS_MIN=0.99999; ABS_MAX=1e-4
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    val_ann=json.loads((ROOT/'data/annotations/circo/val.json').read_text(encoding='utf-8'))
    test_ann=json.loads((ROOT/'data/annotations/circo/test.json').read_text(encoding='utf-8'))
    query_manifest=json.loads((ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/query_manifest.json').read_text(encoding='utf-8'))
    output={}
    for model in ['searle','pic2word']:
        folder=P/'data'/model;manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'));features=[];ids=[];refs=[]
        for start in range(0,800,manifest['batch_size']):
            with np.load(folder/f'batch_{start:04d}.npz',allow_pickle=False) as z:
                if str(z['signature'])!=manifest['signature']:raise ValueError('Batch signature mismatch')
                features.append(z['features']);ids+=z['query_ids'].tolist();refs+=z['reference_img_ids'].tolist()
        expected=[f'test:{x["id"]}' for x in test_ann]; expected_refs=[str(x['reference_img_id']) for x in test_ann]
        if ids!=expected or refs!=expected_refs or len(set(ids))!=800:raise ValueError('ID or reference image mismatch')
        source=ROOT/f'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/circo_1020_queries_{model}.pkl'
        with source.open('rb') as f:old=pickle.load(f)['query_features']
        with (ROOT/f'data/queries/{model}/circo_queries.pkl').open('rb') as f:val=pickle.load(f)
        x=np.vstack(features).astype(np.float64);y=np.asarray(old[220:],dtype=np.float64)
        if x.shape!=y.shape or len(old)!=1020:raise ValueError('Feature shape mismatch')
        normx=np.linalg.norm(x,axis=1);normy=np.linalg.norm(y,axis=1);xn=x/normx[:,None];yn=y/normy[:,None]
        cos=np.einsum('ij,ij->i',xn,yn);err=np.max(np.abs(xn-yn),axis=1);passed=(cos>=COS_MIN)&(err<=ABS_MAX)
        val_x=np.asarray(old[:220],dtype=np.float64);val_y=np.asarray(val['query_features'],dtype=np.float64)
        val_x/=np.linalg.norm(val_x,axis=1)[:,None];val_y/=np.linalg.norm(val_y,axis=1)[:,None]
        canonical=lambda values:sorted(str(int(x)) for x in values)
        val_targets=all(canonical(a)==canonical(b['gt_img_ids']) for a,b in zip(val['target_ids'],val_ann))
        expected_full=[f'val:{r["id"]}' for r in val_ann]+expected
        manifest_match=query_manifest['ids']==expected_full and query_manifest['models'][model]['query_ids']==expected_full
        if not val_targets or not manifest_match or np.max(np.abs(val_x-val_y))>ABS_MAX:raise ValueError('Validation identity mismatch')
        # Identical/near-identical new embeddings cannot distinguish old historical IDs by vector alone.
        similarities=xn@xn.T;np.fill_diagonal(similarities,-2);ambiguous=[]
        for i in range(800):
            candidates=np.flatnonzero(similarities[i]>=COS_MIN)
            candidates=[int(j) for j in candidates if np.max(np.abs(xn[i]-xn[j]))<=ABS_MAX]
            if candidates:ambiguous.append({'query_id':ids[i],'indistinguishable_from':[ids[j] for j in candidates]})
        details=[{'query_id':ids[i],'row_index':i,'reference_img_id':refs[i],'cosine':float(cos[i]),'max_abs_difference':float(err[i]),'norm_new':float(normx[i]),'norm_old':float(normy[i]),'passes':bool(passed[i])} for i in range(800)]
        output[model]={'count':800,'id_unique':True,'validation_rows':220,'validation_target_order_verified':val_targets,'validation_feature_max_abs':float(np.max(np.abs(val_x-val_y))),'r2_manifest_consistent':manifest_match,'test_matched_rows':int(passed.sum()),'test_failed_rows':int((~passed).sum()),'min_cosine':float(cos.min()),'max_abs_difference':float(err.max()),'cosine_quantiles':np.quantile(cos,[0,.05,.5,.95,1]).tolist(),'max_abs_quantiles':np.quantile(err,[0,.5,.95,1]).tolist(),'ambiguous_new_feature_rows':len(ambiguous),'ambiguous_examples':ambiguous[:20],'old_cache_sha256':sha(source),'extraction_signature':manifest['signature'],'source_commit':manifest['source_commit'],'predeclared_cosine_min':COS_MIN,'predeclared_max_abs':ABS_MAX,'row_details':details}
        if not passed.all():output[model]['status']='MISMATCH: inspect differences and evaluate exact top-10 and retention before using old R3 results'
        elif ambiguous:output[model]['status']='Features agree by position; some feature duplicates cannot distinguish historical IDs'
        else:output[model]['status']='Features agree by position under tolerance; original historical cache lacks source IDs'
        print(model,output[model]['status'],'matched',int(passed.sum()),'ambiguous',len(ambiguous),flush=True)
    result={'results':output,'limitations':'Re-extraction checks positional reproducibility under current weights and code; original feature bundle did not embed source IDs. Exact historical identity cannot be cryptographically proven from old cache alone.','predeclared_threshold_source':'preflight_kiem_dinh.md'}
    (P/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    if any(v['test_failed_rows'] for v in output.values()):raise SystemExit('Re-extraction mismatch: impact audit required')
if __name__=='__main__':main()
