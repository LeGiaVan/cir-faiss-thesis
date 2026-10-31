"""Create isolated source-only R4 provenance snapshot, preserving workspace."""
from pathlib import Path
import shutil, subprocess, sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DST=HERE/'source_snapshot'
if DST.exists():raise SystemExit('Snapshot already exists; inspect it rather than overwriting')
DST.mkdir(parents=True)
ignore=shutil.ignore_patterns('__pycache__','*.pyc','.git','*.pt','*.pth','*.npy','*.npz','*.pkl','*.parquet')
for rel in ['src','configs','third_party/SEARLE/src','third_party/composed_image_retrieval/model','third_party/composed_image_retrieval/third_party/open_clip']:
    shutil.copytree(ROOT/rel,DST/rel,ignore=ignore)
hub=Path.home()/'.cache/torch/hub/miccunifi_SEARLE_main'
if not (hub/'hubconf.py').is_file():raise SystemExit('Missing SEARLE torch hub code')
(DST/'searle_hub/src').mkdir(parents=True)
shutil.copy2(hub/'hubconf.py',DST/'searle_hub/hubconf.py')
for name in ['phi.py','encode_with_pseudo_tokens.py']:shutil.copy2(hub/'src'/name,DST/'searle_hub/src'/name)
for source,dest in [(HERE/'extract_test_with_ids.py',DST/'extract_test_with_ids.py'),(HERE/'preflight_kiem_dinh.md',DST/'preflight_kiem_dinh.md'),(ROOT/'R4/R4_execution_plan.md',DST/'R4_execution_plan.md')]:shutil.copy2(source,dest)
(DST/'.gitignore').write_text('__pycache__/\n*.pyc\n',encoding='utf-8')
def git(*args):subprocess.run(['git','-c',f'safe.directory={DST.as_posix()}',*args],cwd=DST,check=True)
git('init');git('add','--all');git('-c','user.name=R4 provenance snapshot','-c','user.email=r4-snapshot@localhost','commit','-m','Freeze R4 provenance extraction source')
git('status','--short')
print('Snapshot created:',DST,flush=True)
