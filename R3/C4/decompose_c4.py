"""Descriptive cross-backbone logit decomposition, query bootstrap, seed 42."""
from pathlib import Path
import json,warnings
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
P=Path(__file__).resolve().parent; D=P/'data'; FEATURES=['rank','log1p_indegree','log1p_n10_gallery','s1','s100']

def load(model,signature):
    with np.load(D/f'{model}_queries.npz') as z:
        if str(z['signature'])!=signature:raise ValueError('query signature mismatch')
        ids=z['truth'].copy(); s1=z['s1'].copy();s100=z['s100'].copy()
    with np.load(D/f'{model}_before_n10.npz') as z:n10=z['counts'].copy()
    with np.load(D/f'{model}_42_before.npz') as z:
        if str(z['signature'])!=signature:raise ValueError('graph signature mismatch')
        degree=z['indegree'].copy(); y=(1-z['found']).copy()
    X=np.stack([np.broadcast_to(np.arange(1,11),(len(ids),10)),np.log1p(degree[ids]),np.log1p(n10[ids]),np.broadcast_to(s1[:,None],ids.shape),np.broadcast_to(s100[:,None],ids.shape)],axis=2)
    return X,y

def fit(x,y):
    m=LogisticRegression(penalty=None,solver='lbfgs',max_iter=500,tol=1e-7)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always',ConvergenceWarning);m.fit(x,y)
        if any(issubclass(v.category,ConvergenceWarning) for v in w):raise ValueError('logit nonconvergence')
    if np.max(np.abs(m.coef_))>100 or not np.isfinite(m.coef_).all():raise ValueError('unstable coefficients')
    return m

def perform(xs,ys,xp,yp,mu,sd):
    s=(xs.reshape(-1,5)-mu)/sd;p=(xp.reshape(-1,5)-mu)/sd
    ms=fit(s,ys.ravel());mp=fit(p,yp.ravel()); obs_s=float(ys.mean());obs_p=float(yp.mean()); gap=obs_p-obs_s
    def pred(model,x):return float(model.predict_proba(x)[:,1].mean())
    # Pointwise query-row/rank pairing is a descriptive coupling, not identification.
    def components(m,base,donor):
        start=pred(m,base); end=pred(m,donor); node=base.copy();node[:,:3]=donor[:,:3];query=base.copy();query[:,3:]=donor[:,3:]
        n=pred(m,node); q=pred(m,query)
        return {'node_then_query':[n-start,end-n],'query_then_node':[end-q,q-start]}
    fwd=pred(ms,p)-obs_s;rev=obs_p-pred(mp,s)
    return {'gap':gap,'forward_explained':fwd,'forward_unexplained':gap-fwd,'reverse_explained':rev,'reverse_unexplained':gap-rev,'forward_groups':components(ms,s,p),'reverse_groups':components(mp,s,p)}

def main():
    meta=json.loads((P/'run_manifest.json').read_text(encoding='utf-8')); xs,ys=load('searle',meta['signature']);xp,yp=load('pic2word',meta['signature'])
    pooled=np.concatenate([xs.reshape(-1,5),xp.reshape(-1,5)]);mu=pooled.mean(axis=0);sd=pooled.std(axis=0)
    if (sd==0).any():raise ValueError('constant predictor')
    overlap={}
    for j,name in enumerate(FEATURES):
        a=xs[:,:,j].ravel();b=xp[:,:,j].ravel();overlap[name]={'searle_minmax':[float(a.min()),float(a.max())],'pic2word_minmax':[float(b.min()),float(b.max())],'intersection':[float(max(a.min(),b.min())),float(min(a.max(),b.max()))]}
    point=perform(xs,ys,xp,yp,mu,sd); out=P/'decomposition_bootstrap.npz'; sig=meta['signature']; estimates=[];failures=0;start=0
    if out.exists():
        with np.load(out) as z:
            if str(z['signature'])!=sig:raise ValueError('bootstrap signature mismatch')
            estimates=z['estimates'].tolist();failures=int(z['failures']);start=int(z['completed'])
    rng=np.random.default_rng(42)
    for i in range(2000):
        a=rng.integers(0,len(xs),len(xs)); b=rng.integers(0,len(xp),len(xp))
        if i<start:continue
        try:
            v=perform(xs[a],ys[a],xp[b],yp[b],mu,sd)
            estimates.append([v['gap'],v['forward_explained'],v['forward_unexplained'],v['reverse_explained'],v['reverse_unexplained'],*v['forward_groups']['node_then_query'],*v['forward_groups']['query_then_node'],*v['reverse_groups']['node_then_query'],*v['reverse_groups']['query_then_node']])
        except (ValueError,FloatingPointError):failures+=1
        if (i+1)%20==0 or i==1999:
            tmp=out.with_suffix('.tmp.npz');np.savez_compressed(tmp,signature=sig,estimates=np.asarray(estimates),failures=failures,completed=i+1);tmp.replace(out);print('decomposition bootstrap',i+1,'/ 2000, failed',failures,flush=True)
    names=['gap','forward_explained','forward_unexplained','reverse_explained','reverse_unexplained','forward_node_first_node','forward_node_first_query','forward_query_first_node','forward_query_first_query','reverse_node_first_node','reverse_node_first_query','reverse_query_first_node','reverse_query_first_query']
    ci={name:np.percentile(np.asarray(estimates)[:,i],[2.5,97.5]).tolist() for i,name in enumerate(names)} if estimates else {}
    result={'seed':42,'sample':'original graphs, all queries and exact neighbors, 1 build per model','method':'unpenalized logistic regression; standardized predictors; counterfactual distributions use same row/rank coupling; ordered group replacement is descriptive and coupling-dependent','features':FEATURES,'point':point,'bootstrap_ci_95':ci,'bootstrap_attempts':2000,'bootstrap_success':len(estimates),'bootstrap_failed':failures,'predictor_ranges':overlap,'limitation':'query-level bootstrap does not address shared image clusters, cross-model covariate support and synthetic mixed rows may be implausible; no causal interpretation'}
    (P/'decomposition.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print('Decomposition complete',flush=True)

if __name__=='__main__':main()
