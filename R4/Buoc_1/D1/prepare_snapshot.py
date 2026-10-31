"""Freeze D1 code and registration in an isolated source-only repository."""
from pathlib import Path
import shutil,subprocess
P=Path(__file__).resolve().parent; S=P/'source_snapshot'
if S.exists():raise SystemExit('Snapshot exists; inspect rather than overwrite')
S.mkdir()
for name in ['run_d1.py','dang_ky_truoc.md','ke_hoach_D1.md']:shutil.copy2(P/name,S/name)
(S/'.gitignore').write_text('__pycache__/\n*.pyc\n',encoding='utf-8')
def git(*args):subprocess.run(['git','-c',f'safe.directory={S.as_posix()}',*args],cwd=S,check=True)
git('init');git('add','--all');git('-c','user.name=R4 D1 snapshot','-c','user.email=r4-d1-snapshot@localhost','commit','-m','Freeze D1 code and analysis registration');git('status','--short')
