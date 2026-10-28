"""Wait for both C2 processes, require its completed report, then run C3."""
import ctypes, subprocess, sys
from pathlib import Path
P=Path(__file__).resolve().parent
k=ctypes.windll.kernel32; k.OpenProcess.restype=ctypes.c_void_p
for pid in map(int,sys.argv[1:]):
    h=k.OpenProcess(0x00100000,False,pid)
    if h:
        k.WaitForSingleObject(ctypes.c_void_p(h),0xffffffff); k.CloseHandle(ctypes.c_void_p(h))
if not (P.parent/'C2/bao_cao_C2.md').exists(): raise RuntimeError('C2 did not complete; C3 not started')
subprocess.run([sys.executable,str(P/'run_c3.py')],check=True)
subprocess.run([sys.executable,str(P/'analyze_c3.py')],check=True)
