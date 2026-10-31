"""Extract CIRCO test features with source IDs; intended to run from clean snapshot."""
from pathlib import Path
import argparse, datetime, hashlib, importlib.metadata, json, os, pickle, sys, time
import numpy as np
import torch
from PIL import Image

SNAP=Path(__file__).resolve().parent
PROJECT=SNAP.parents[2]
OUT=PROJECT/'R4/provenance/data'
sys.path.insert(0,str(SNAP/'src'))

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def save_json(path,obj):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(path)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',required=True,choices=['searle','pic2word']);ap.add_argument('--batch-size',type=int,default=8);ap.add_argument('--threads',type=int,default=8);ap.add_argument('--max-batches',type=int,default=0);args=ap.parse_args()
    if args.batch_size<=0 or args.threads<=0:raise ValueError('Invalid batch/thread count')
    torch.set_num_threads(args.threads)
    anno=PROJECT/'data/annotations/circo/test.json'; rows=json.loads(anno.read_text(encoding='utf-8'))
    if len(rows)!=800 or len({str(r['id']) for r in rows})!=800:raise ValueError('Invalid test IDs')
    image_dir=PROJECT/'data/raw/circo/unlabeled2017'; path_for=lambda r:image_dir/(str(r['reference_img_id']).zfill(12)+'.jpg')
    missing=[str(path_for(r)) for r in rows if not path_for(r).is_file()]
    if missing:raise FileNotFoundError(f'{len(missing)} missing images; first: {missing[0]}')
    old=PROJECT/f'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/circo_1020_queries_{args.model}.pkl'
    clip=Path.home()/'.cache/clip'/('ViT-B-32.pt' if args.model=='searle' else 'ViT-L-14.pt')
    phi=Path(torch.hub.get_dir())/'checkpoints/SEARLE_ViT-B32.pt'
    weights=[clip,phi] if args.model=='searle' else [clip,PROJECT/'checkpoints/pic2word_vit_l_14.pt']
    for path in weights:
        if not path.is_file():raise FileNotFoundError(f'Missing weight {path}')
    image_list=[{'query_id':f'test:{r["id"]}','reference_img_id':str(r['reference_img_id']),'relative_caption':r['relative_caption'],'image_sha256':digest(path_for(r))} for r in rows]
    provenance={'model':args.model,'batch_size':args.batch_size,'torch_threads':torch.get_num_threads(),'torch':torch.__version__,'numpy':np.__version__,'python':sys.version,'device':'cpu','annotation_sha256':digest(anno),'old_cache_sha256':digest(old),'weights_sha256':{str(p):digest(p) for p in weights},'images_sha256':hashlib.sha256(json.dumps(image_list,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'source_commit':os.environ.get('R4_SNAPSHOT_COMMIT','unknown'),'clip_distribution':importlib.metadata.version('clip') if args.model=='searle' else None}
    signature=hashlib.sha256(json.dumps(provenance,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    folder=OUT/args.model;folder.mkdir(parents=True,exist_ok=True)
    run=folder/'manifest.json'
    if run.exists() and json.loads(run.read_text(encoding='utf-8'))['signature']!=signature:raise ValueError('Run signature mismatch; use a new output directory')
    if not run.exists():save_json(run,{'created_utc':datetime.datetime.now(datetime.UTC).isoformat(),'signature':signature,**provenance,'rows':image_list})
    orig_hub=torch.hub.load; orig_torch_load=torch.load
    def hub_loader(repo_or_dir,model,*a,**kw):
        if repo_or_dir=='miccunifi/SEARLE':
            kw.pop('trust_repo',None);kw.pop('force_reload',None);kw['source']='local';return orig_hub(str(SNAP/'searle_hub'),model,*a,**kw)
        raise RuntimeError(f'Network or unexpected torch hub source blocked: {repo_or_dir}')
    def trusted_load(*a,**kw):kw['weights_only']=False;return orig_torch_load(*a,**kw)
    torch.hub.load=hub_loader;torch.load=trusted_load
    if args.model=='searle':
        from extractors.searle_adapter import SearleAdapter
        adapter=SearleAdapter(device='cpu');adapter.load_model()
    else:
        from extractors.pic2word_adapter import Pic2WordAdapter
        adapter=Pic2WordAdapter(device='cpu');adapter.load_model(checkpoint_path=str(weights[1]))
    begin=time.perf_counter(); processed=0
    for start in range(0,800,args.batch_size):
        batch_rows=rows[start:start+args.batch_size]; target=folder/f'batch_{start:04d}.npz'
        if target.exists():
            with np.load(target,allow_pickle=False) as z:
                if str(z['signature'])!=signature or z['query_ids'].tolist()!=[f'test:{r["id"]}' for r in batch_rows]:raise ValueError('Batch checkpoint mismatch')
        else:
            images=[]
            for row in batch_rows:
                with Image.open(path_for(row)) as im: images.append(im.convert('RGB'))
            with torch.inference_mode():features=adapter.extract_query_features(images,[r['relative_caption'] for r in batch_rows])
            if features.shape[0]!=len(batch_rows) or not np.isfinite(features).all():raise ValueError('Invalid extracted features')
            tmp=target.with_suffix('.tmp.npz');np.savez_compressed(tmp,signature=signature,query_ids=np.asarray([f'test:{r["id"]}' for r in batch_rows]),reference_img_ids=np.asarray([str(r['reference_img_id']) for r in batch_rows]),features=features);tmp.replace(target)
        processed+=1;print(args.model,'rows',min(start+len(batch_rows),800),'elapsed_s',round(time.perf_counter()-begin,1),flush=True)
        if args.max_batches and processed>=args.max_batches:print('Pilot complete',flush=True);return
    print('Extraction complete:',args.model,flush=True)

if __name__=='__main__':main()
