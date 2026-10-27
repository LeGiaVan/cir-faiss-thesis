"""Shared P1 configuration, provenance, geometry and timing. No legacy mutation."""
from pathlib import Path
import datetime
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import time
import numpy as np
import faiss
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / 'configs/reference.yaml'


def config():
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))
    if cfg['execution']['latency_benchmark']['measured_runs'] != 7:
        raise ValueError('Reference latency requires seven measured runs')
    return cfg


def setup():
    cfg = config()
    faiss.omp_set_num_threads(cfg['execution']['num_threads'])
    np.random.seed(cfg['experiment_metadata']['random_seed'])
    return cfg


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def provenance(paths):
    return [{'path':Path(p).resolve().relative_to(ROOT).as_posix(),
             'sha256':sha256(p),'bytes':Path(p).stat().st_size} for p in paths]


def metadata(module, *, inputs=(), model=None, dataset='circo', gallery_size=None,
             num_queries=None, index_config=None, profile='reference', **extra):
    cfg = config()
    try:
        commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,stderr=subprocess.DEVNULL,text=True).strip()
        dirty = bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())
    except (OSError,subprocess.CalledProcessError):
        commit, dirty = None, None
    versions = {}
    for name in ['numpy','scipy','pandas','statsmodels','faiss-cpu','PyYAML']:
        try: versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: versions[name] = None
    code_paths = sorted((ROOT/'src/phase2').rglob('*.py')) + sorted((ROOT/'Phase_2_Q1_Journal/R2_Audit').glob('scripts/*.py')) + sorted((ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts').glob('*.py'))
    code_hash = hashlib.sha256(''.join(p.relative_to(ROOT).as_posix()+sha256(p) for p in code_paths).encode()).hexdigest()
    return {'module':module,'timestamp':datetime.datetime.now(datetime.UTC).isoformat(),
            'git_commit':commit,'git_dirty':dirty,'source_tree_sha256':code_hash,
            'random_seed':cfg['experiment_metadata']['random_seed'],
            'hardware':{'cpu':os.environ.get('PROCESSOR_IDENTIFIER',platform.processor()),
                        'logical_cpus':os.cpu_count(),'threads':faiss.omp_get_max_threads()},
            'versions':versions,'model':model,'dataset':dataset,'gallery_size':gallery_size,
            'num_queries':num_queries,'profile':profile,'index_config':index_config,
            'config_sha256':sha256(CONFIG_PATH),'resolved_config':cfg,
            'inputs':provenance(inputs), **extra}


def write_json(path, data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def normalized(values):
    a=np.ascontiguousarray(values,dtype=np.float32).copy()
    if not np.isfinite(a).all() or np.any(np.linalg.norm(a,axis=1)==0):
        raise ValueError('Non-finite or zero vector')
    faiss.normalize_L2(a)
    return a


def search(index, queries, k, batch_size=None):
    batch_size=batch_size or config()['execution']['batch_size']
    ds,ids=[],[]
    for start in range(0,len(queries),batch_size):
        d,i=index.search(queries[start:start+batch_size],k);ds.append(d);ids.append(i)
    return np.vstack(ds),np.vstack(ids)


def timed_search(index, queries, k):
    cfg=config()['execution']['latency_benchmark']
    for _ in range(cfg['warmup_runs']):
        search(index,queries,k,cfg['query_batch_size'])
    samples=[]
    for _ in range(cfg['measured_runs']):
        t=time.perf_counter(); d,i=search(index,queries,k,cfg['query_batch_size'])
        samples.append((time.perf_counter()-t)*1000/len(queries))
    return d,i,{'ms_per_query':float(np.median(samples)),'std_ms':float(np.std(samples,ddof=1)),
                'runs_ms':samples,'warmup_runs':cfg['warmup_runs'],'measured_runs':len(samples),
                'query_batch_size':cfg['query_batch_size'],'scope':'search calls plus Python batch-loop overhead'}


def hnsw(gallery, seed=42, profile='reference'):
    c=config()['hnsw'][profile]
    idx=faiss.IndexHNSWFlat(gallery.shape[1],c['M'],faiss.METRIC_INNER_PRODUCT)
    idx.hnsw.rng=faiss.RandomGenerator(seed)
    idx.hnsw.efConstruction=c['efConstruction'];idx.hnsw.efSearch=c['efSearch']
    idx.add(gallery)
    return idx


def graph_degrees(index):
    h=index.hnsw;n=index.ntotal
    neighbors=faiss.vector_to_array(h.neighbors);offsets=faiss.vector_to_array(h.offsets).astype(np.int64)
    slots=offsets[:-1,None]+np.arange(h.nb_neighbors(0))
    if np.any(slots>=offsets[1:,None]):
        raise ValueError('Invalid layer-0 neighbor layout')
    mat=neighbors[slots];valid=mat[mat>=0]
    if np.any(valid>=n): raise ValueError('Invalid edge target')
    indeg=np.bincount(valid,minlength=n);outdeg=(mat>=0).sum(axis=1)
    assert indeg.sum()==outdeg.sum()
    return indeg,outdeg


def geometry(gallery):
    """RC cosine; LID Euclidean chord. Exact self removal by ID, no clipping LID."""
    cfg=config()['metrics'];rng=np.random.default_rng(config()['audit']['geometry_seed'])
    g=normalized(gallery);n,d=g.shape;k=cfg['local_intrinsic_dimensionality']['k_nn']
    if n<=k: raise ValueError('Gallery must exceed LID k')
    count=min(n,max(cfg['relative_contrast']['sample_size'],cfg['local_intrinsic_dimensionality']['sample_size']))
    sample=rng.choice(n,count,replace=False)
    idx=faiss.IndexFlatIP(d);idx.add(g)
    scores,ids=search(idx,g[sample],k+1)
    kept=np.array([s[i!=self_id][:k] for s,i,self_id in zip(scores,ids,sample)])
    cosine=np.maximum(1-kept,0)
    rc_n=min(n,cfg['relative_contrast']['sample_size']);lid_n=min(n,cfg['local_intrinsic_dimensionality']['sample_size'])
    pairs=cfg['relative_contrast']['random_pairs'];a=rng.integers(n,size=pairs);b=(a+rng.integers(1,n,size=pairs))%n
    mean_dist=float(np.mean(1-np.einsum('ij,ij->i',g[a],g[b])))
    nearest=float(np.mean(cosine[:rc_n,0]))
    distances=np.sqrt(2*cosine[:lid_n])
    valid=(distances>0).all(axis=1)
    vals=distances[valid];den=np.log(vals[:,-1,None]/vals[:,:-1]).sum(axis=1)
    good=np.isfinite(den)&(den>0)
    lid=(k-1)/den[good]
    return {'relative_contrast':mean_dist/nearest if nearest>0 else None,
            'rc_mean_distance':mean_dist,'rc_mean_nearest_distance':nearest,
            'lid_mean':float(lid.mean()) if len(lid) else None,
            'lid_median':float(np.median(lid)) if len(lid) else None,
            'lid_valid_neighborhoods':len(lid),'lid_excluded_neighborhoods':lid_n-len(lid),
            'rc_sample_size':rc_n,'lid_sample_size':lid_n,'lid_k':k,
            'sample_ids_sha256':hashlib.sha256(sample.tobytes()).hexdigest(),
            'definitions':cfg}
