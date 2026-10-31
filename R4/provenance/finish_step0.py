"""Wait for active extraction runs, resume incomplete batches, then compare."""
from pathlib import Path
import ctypes,json,os,subprocess,sys
P=Path(__file__).resolve().parent;SNAP=P/'source_snapshot'
k=ctypes.windll.kernel32;k.OpenProcess.restype=ctypes.c_void_p
for pid in map(int,sys.argv[1:]):
    handle=k.OpenProcess(0x00100000,False,pid)
    if handle:k.WaitForSingleObject(ctypes.c_void_p(handle),0xffffffff);k.CloseHandle(ctypes.c_void_p(handle))
commit=subprocess.check_output(['git','-c',f'safe.directory={SNAP.as_posix()}','-C',str(SNAP),'rev-parse','HEAD'],text=True).strip()
os.environ['R4_SNAPSHOT_COMMIT']=commit
for model in ['searle','pic2word']:
    folder=P/'data'/model;manifest=folder/'manifest.json'
    if not manifest.exists():raise RuntimeError(f'Missing {model} extraction manifest')
    size=json.loads(manifest.read_text(encoding='utf-8'))['batch_size']
    if any(not (folder/f'batch_{i:04d}.npz').exists() for i in range(0,800,size)):
        print('Resuming',model,flush=True);subprocess.run([sys.executable,str(SNAP/'extract_test_with_ids.py'),'--model',model,'--batch-size',str(size),'--threads','8'],check=True)
subprocess.run([sys.executable,str(P/'inventory_step0.py')],check=True)
compare=subprocess.run([sys.executable,str(P/'compare_extractions.py')])
subprocess.run([sys.executable,str(P/'render_step0.py')],check=True)
if compare.returncode:raise SystemExit('Comparison requires investigation; see comparison.json')
print('Step 0 comparison complete; inspect report and remaining provenance limitations.',flush=True)
