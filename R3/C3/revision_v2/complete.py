"""Run acquisition and analyze only if acquisition succeeds."""
from pathlib import Path
import subprocess,sys
P=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(P/'run_c3.py')],check=True)
subprocess.run([sys.executable,str(P/'analyze_c3.py')],check=True)
