"""Wait for acquisition, resume validated checkpoints, then analyze C2."""
import ctypes
import subprocess
import sys
from pathlib import Path

here=Path(__file__).resolve().parent
kernel=ctypes.windll.kernel32
kernel.OpenProcess.restype=ctypes.c_void_p
handle=kernel.OpenProcess(0x00100000,False,int(sys.argv[1]))
if handle:
    kernel.WaitForSingleObject(ctypes.c_void_p(handle),0xffffffff)
    kernel.CloseHandle(ctypes.c_void_p(handle))
subprocess.run([sys.executable,str(here/'run_c2.py')],check=True)
subprocess.run([sys.executable,str(here/'analyze_c2.py')],check=True)
