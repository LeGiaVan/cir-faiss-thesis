"""Read-only inventory of R4 inputs, dirty workspace and environment."""
from pathlib import Path
import datetime,hashlib,importlib.metadata,json,os,platform,subprocess,sys
import faiss,numpy as np,torch
P=Path(__file__).resolve().parent; ROOT=P.parents[1]

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(8*1024*1024),b''):h.update(part)
    return h.hexdigest()
def git(path,*args):
    p=subprocess.run(['git','-c',f'safe.directory={path.as_posix()}','-C',str(path),*args],capture_output=True,text=True)
    return {'exit_code':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip()}

def main():
    old=json.loads((ROOT/'R3/stage0_manifest.json').read_text(encoding='utf-8')); snapshot=P/'source_snapshot'
    rels=list(old['frozen_inputs_sha256'])
    rels=[p for p in rels if not p.endswith('_at_stage0_start')]
    rels += ['R3/C1/results.json','R3/C2/results.json','R3/C2/edge_selection.json','R3/C2/sweep.csv','R3/C2/bao_cao_C2.md','R3/C3/revision_v2/results.json','R3/C4/results.json','R3/C5/results.json','R4/mentor_feedback_r4.txt','R4/R4_execution_plan.md','R4/provenance/preflight_kiem_dinh.md','R4/provenance/extract_test_with_ids.py']
    rels += [f'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/reference_{m}_{s}_{v}.npz' for m in ['searle','pic2word'] for s in [42,43,44,45,46] for v in ['before','after']]
    files=[]
    for rel in sorted(set(rels)):
        p=ROOT/rel
        rec={'path':rel,'exists':p.is_file()}
        if p.is_file():
            h=sha(p);rec.update(bytes=p.stat().st_size,sha256=h,tracked=git(ROOT,'ls-files','--error-unmatch','--',rel)['exit_code']==0)
            if rel in old['frozen_inputs_sha256']:
                expected=old['frozen_inputs_sha256'][rel].lower();rec['stage0_sha256']=expected;rec['stage0_byte_match']=h==expected
                if p.suffix.lower() in ['.py','.yaml','.json','.md']:
                    rec['lf_normalized_sha256']=hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest();rec['stage0_lf_match']=rec['lf_normalized_sha256']==expected
        files.append(rec)
    weights=[ROOT/'checkpoints/pic2word_vit_l_14.pt',Path.home()/'.cache/clip/ViT-B-32.pt',Path.home()/'.cache/clip/ViT-L-14.pt',Path(torch.hub.get_dir())/'checkpoints/SEARLE_ViT-B32.pt']
    weight_data=[{'path':str(p),'exists':p.is_file(),**({'bytes':p.stat().st_size,'sha256':sha(p)} if p.is_file() else {})} for p in weights]
    packages={}
    for name in ['torch','torchvision','faiss-cpu','numpy','scipy','pandas','Pillow','PyYAML','clip','open-clip-torch']:
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]=None
    clipmod=__import__('clip');clip_root=Path(clipmod.__file__).parent
    clip_files=[{'path':str(p),'sha256':sha(p)} for p in sorted(clip_root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix.lower() in ['.py','.gz','.pyd','.so']]
    result={'created_utc':datetime.datetime.now(datetime.UTC).isoformat(),'scope':'R4 step 0 inventory; no experimental data mutated','project':{'head':git(ROOT,'rev-parse','HEAD'),'status':git(ROOT,'status','--porcelain=v1','--untracked-files=all'),'submodules':git(ROOT,'submodule','status'),'extractor_submodule_status':git(ROOT/'third_party/composed_image_retrieval','status','--porcelain=v1','--untracked-files=all')},'isolated_snapshot':{'path':str(snapshot),'head':git(snapshot,'rev-parse','HEAD'),'status':git(snapshot,'status','--porcelain=v1','--untracked-files=all'),'scope':'source-only extraction snapshot; external packages, model weights, inputs and later experiment scripts are not covered by commit'},'environment':{'python':sys.version,'platform':platform.platform(),'cpu':os.environ.get('PROCESSOR_IDENTIFIER',platform.processor()),'logical_cpus':os.cpu_count(),'faiss_threads_at_inventory':faiss.omp_get_max_threads(),'cuda':torch.cuda.is_available(),'packages':packages,'clip_python_files':clip_files},'files':files,'external_weights':weight_data,'recovery_note':'Raw gallery images, model weights, caches and ignored R3 artifacts remain outside Git; recover only from original sources with matching hashes. Snapshot includes a local SEARLE hub source copy; dependencies external to snapshot are not frozen by its commit.'}
    (P/'inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Inventory saved; input entries',len(files),'missing',sum(not x['exists'] for x in files),flush=True)

if __name__=='__main__':main()
