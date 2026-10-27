"""Small numerical checks for shared geometry, graph extraction and paired bootstrap."""
from pathlib import Path
import sys
import importlib.util
import numpy as np
import faiss
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from phase2.protocol import setup,normalized,geometry,hnsw,graph_degrees,timed_search


def main():
    setup();rng=np.random.default_rng(7);g=normalized(rng.normal(size=(40,8)));q=normalized(rng.normal(size=(6,8)))
    idx=hnsw(g,7);indeg,outdeg=graph_degrees(idx)
    arr=faiss.vector_to_array(idx.hnsw.neighbors);off=faiss.vector_to_array(idx.hnsw.offsets)
    expected=np.zeros(len(g),dtype=int)
    for i in range(len(g)):
        row=arr[int(off[i]):int(off[i])+idx.hnsw.nb_neighbors(0)]
        np.add.at(expected,row[row>=0],1)
    assert np.array_equal(indeg,expected) and indeg.sum()==outdeg.sum()
    flat=faiss.IndexFlatIP(8);flat.add(g);s,ids=flat.search(q,10)
    gc=g-g.mean(axis=0);fc=faiss.IndexFlatIP(8);fc.add(gc);sc,ic=fc.search(q,10)
    assert np.array_equal(ids,ic)
    assert np.allclose(sc,s-(q@g.mean(axis=0))[:,None],atol=1e-6)
    r=geometry(g)
    # Independent dense exact calculation of the LID statistic (all 40 points sampled).
    sim=g@g.T;np.fill_diagonal(sim,-np.inf)
    scores=np.sort(sim,axis=1)[:,::-1][:,:20];dist=np.sqrt(np.maximum(2*(1-scores),0))
    lid=19/np.log(dist[:,-1,None]/dist[:,:-1]).sum(axis=1)
    assert np.isclose(r['lid_mean'],lid.mean(),rtol=2e-5)
    assert r['lid_valid_neighborhoods']==40
    _,_,timing=timed_search(flat,q,10)
    assert len(timing['runs_ms'])==7 and timing['warmup_runs']==1
    spec=importlib.util.spec_from_file_location('audit',ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/run_reference_audit.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    zero=module.bootstrap_paired(np.zeros((5,6)),100,42)
    assert zero['ci_lower']==zero['ci_upper']==0
    positive=module.bootstrap_paired(np.full((5,6),.2),100,42)
    assert np.isclose(positive['ci_lower'],.2) and np.isclose(positive['ci_upper'],.2)
    print('PASS: graph edges, centering identity, dense-reference LID, 1+7 timing, paired bootstrap.')


if __name__=='__main__':main()
