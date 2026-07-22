@echo off
setlocal EnableDelayedExpansion

echo =======================================================
echo    FAISS BENCHMARKING PIPELINE - MASTER SCRIPT
echo =======================================================
echo.

set PYTHON_CMD=python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Khong tim thay lenh python. Vui long cai dat Python hoac kich hoat moi truong ao.
    exit /b 1
)

set MODELS=clip4cir searle pic2word
set DATASETS=fashioniq circo cirr

:: Kịch bản menu tương tác nếu không truyền tham số
set PHASE=%1
if "%PHASE%"=="" (
    echo Vui long chon giai doan de chay:
    echo [1] Phase 1: Trich xuat Gallery (Feature Extraction)
    echo [2] Phase 2: Trich xuat Queries va Benchmark FAISS
    echo [3] Chay toan bo he thong (Phase 1 + Phase 2)
    set /p PHASE="Nhap lua chon (1/2/3): "
)

if "%PHASE%"=="3" set PHASE=all

if "%PHASE%"=="all" goto phase1
if "%PHASE%"=="1" goto phase1
if "%PHASE%"=="2" goto phase2

echo [ERROR] Lua chon khong hop le.
exit /b 1

:phase1
echo.
echo =======================================================
echo [PHASE 1] TRICH XUAT DAC TRUNG (GALLERY)
echo =======================================================
for %%M in (%MODELS%) do (
    for %%D in (%DATASETS%) do (
        echo.
        echo -------------------------------------------------------
        echo [TIME: !time!] Bat dau trich xuat %%M tren %%D
        echo -------------------------------------------------------
        %PYTHON_CMD% src\scripts\extract_features.py --model %%M --dataset %%D --batch-size 128
        
        if !ERRORLEVEL! NEQ 0 (
            echo [ERROR] Trich xuat that bai cho %%M tren %%D!
            exit /b 1
        )
        
        :: Setup paths for integrity check
        if "%%M"=="clip4cir" set DIM=640
        if "%%M"=="searle" set DIM=512
        if "%%M"=="pic2word" set DIM=768
        
        set NPY_FILE=data\embeddings\%%M\%%D_gallery.npy
        
        echo [*] [TIME: !time!] Checking Data Integrity cho %%M tren %%D...
        %PYTHON_CMD% src\scripts\check_data_integrity.py --file !NPY_FILE! --dim !DIM!
        
        if !ERRORLEVEL! NEQ 0 (
            echo [ERROR] Data Integrity Check Failed cho !NPY_FILE!
            exit /b 1
        )
        echo [OK] Hoan thanh Phase 1 cho %%M tren %%D.
    )
)
if "%PHASE%"=="1" goto end

:phase2
echo.
echo =======================================================
echo [PHASE 2] TRICH XUAT QUERIES VA BENCHMARK FAISS
echo =======================================================
for %%M in (%MODELS%) do (
    for %%D in (%DATASETS%) do (
        echo.
        echo -------------------------------------------------------
        echo [TIME: !time!] Trich xuat Queries cho %%M tren %%D
        echo -------------------------------------------------------
        %PYTHON_CMD% src\scripts\extract_queries.py --model %%M --dataset %%D --batch-size 64
        
        if !ERRORLEVEL! NEQ 0 (
            echo [ERROR] Query extraction failed cho %%M tren %%D!
            exit /b 1
        )
        
        echo -------------------------------------------------------
        echo [TIME: !time!] Chay FAISS Benchmark cho %%M tren %%D
        echo -------------------------------------------------------
        %PYTHON_CMD% src\scripts\run_eval_benchmark.py --model %%M --dataset %%D
        
        if !ERRORLEVEL! NEQ 0 (
            echo [ERROR] Benchmark Evaluation Failed cho %%M tren %%D
            exit /b 1
        )
        echo [OK] Hoan thanh Phase 2 cho %%M tren %%D.
    )
)

:end
echo.
echo =======================================================
echo [TIME: !time!] HOAN TAT TOAN BO TIEN TRINH!
echo =======================================================
endlocal
