"""Resume validated acquisition and produce C4 outputs after it finishes."""
import ctypes,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
k=ctypes.windll.kernel32;k.OpenProcess.restype=ctypes.c_void_p
h=k.OpenProcess(0x00100000,False,int(sys.argv[1]))
if h:
    k.WaitForSingleObject(ctypes.c_void_p(h),0xffffffff);k.CloseHandle(ctypes.c_void_p(h))
for name in ['acquire_c4.py','analyze_c4.py','decompose_c4.py','render_c4.py']:
    subprocess.run([sys.executable,str(P/name)],check=True)
