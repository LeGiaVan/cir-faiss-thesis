@echo off
echo ===================================================
echo CAI DAT MOI TRUONG TOI UU CHO RTX 3050 8GB
echo ===================================================

echo 1. Cai dat PyTorch voi CUDA 12.1 (Ho tro GPU NVIDIA)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.
echo 2. Cai dat cac thu vien con lai tu requirements.txt...
pip install -r requirements.txt

echo.
echo ===================================================
echo HOAN TAT!
echo Kiem tra GPU voi lenh: python -c "import torch; print('CUDA hien co:', torch.cuda.is_available())"
echo ===================================================
pause
