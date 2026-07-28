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
set FIQ_CATEGORIES=dress shirt toptee

:: Menu tuong tac neu khong truyen tham so
set PHASE=%1
if "%PHASE%"=="" (
    echo Vui long chon giai doan de chay:
    echo [1] Phase 1: Trich xuat Gallery - Feature Extraction
    echo [2] Phase 2: Trich xuat Queries va Benchmark FAISS
    echo [3] Chay toan bo he thong - Phase 1 + Phase 2
    set /p PHASE=Nhap lua chon 1, 2 hoac 3:
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
echo [PHASE 1] TRICH XUAT DAC TRUNG - GALLERY
echo =======================================================
for %%M in (%MODELS%) do (
    rem CLIP4Cir khong co checkpoint chinh chu train tren CIRCO - paper goc chi cong bo
    rem ket qua tren FashionIQ va CIRR. Loai circo khoi danh sach dataset cua rieng clip4cir.
    rem Xem AUDIT_AND_REVISED_PLAN.md.
    set CUR_DATASETS=%DATASETS%
    if "%%M"=="clip4cir" (
        set CUR_DATASETS=fashioniq cirr
        echo [SKIP] clip4cir tren circo - khong co checkpoint chinh chu, xem AUDIT_AND_REVISED_PLAN.md.
    )
    for %%D in (!CUR_DATASETS!) do (
        if "%%D"=="fashioniq" (
            for %%C in (%FIQ_CATEGORIES%) do (
                call :extract_gallery %%M %%D %%C
            )
        ) else (
            call :extract_gallery %%M %%D ""
        )
    )
)
if "%PHASE%"=="1" goto end

:phase2
echo.
echo =======================================================
echo [PHASE 2] TRICH XUAT QUERIES VA BENCHMARK FAISS
echo =======================================================
for %%M in (%MODELS%) do (
    set CUR_DATASETS=%DATASETS%
    if "%%M"=="clip4cir" (
        set CUR_DATASETS=fashioniq cirr
        echo [SKIP] clip4cir tren circo - khong co checkpoint chinh chu.
    )
    for %%D in (!CUR_DATASETS!) do (
        if "%%D"=="fashioniq" (
            for %%C in (%FIQ_CATEGORIES%) do (
                call :extract_query %%M %%D %%C
            )
        ) else (
            call :extract_query %%M %%D ""
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
goto end

:extract_gallery
:: %1=model %2=dataset %3=category (co the rong)
setlocal
set M=%~1
set D=%~2
set C=%~3
set CAT_ARG=
if not "%C%"=="" set CAT_ARG=--category %C%

echo.
echo -------------------------------------------------------
echo [TIME: !time!] Bat dau trich xuat %M% tren %D% %C%
echo -------------------------------------------------------
%PYTHON_CMD% src\scripts\extract_features.py --model %M% --dataset %D% %CAT_ARG% --batch-size 128
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Trich xuat that bai cho %M% tren %D% %C%!
    exit /b 1
)

if "%M%"=="clip4cir" set DIM=640
if "%M%"=="searle" set DIM=512
if "%M%"=="pic2word" set DIM=768

if "%C%"=="" (
    set NPY_FILE=data\embeddings\%M%\%D%_gallery.npy
) else (
    set NPY_FILE=data\embeddings\%M%\%D%_%C%_gallery.npy
)

echo [*] [TIME: !time!] Checking Data Integrity cho %M% tren %D% %C%...
%PYTHON_CMD% src\scripts\check_data_integrity.py --file !NPY_FILE! --dim !DIM!
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Data Integrity Check Failed cho !NPY_FILE!
    exit /b 1
)
echo [OK] Hoan thanh Phase 1 cho %M% tren %D% %C%.
endlocal
goto :eof

:extract_query
:: %1=model %2=dataset %3=category (co the rong)
setlocal
set M=%~1
set D=%~2
set C=%~3
set CAT_ARG=
if not "%C%"=="" set CAT_ARG=--category %C%

echo -------------------------------------------------------
echo [TIME: !time!] Trich xuat Queries cho %M% tren %D% %C%
echo -------------------------------------------------------
%PYTHON_CMD% src\scripts\extract_queries.py --model %M% --dataset %D% %CAT_ARG% --batch-size 64
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Query extraction failed cho %M% tren %D% %C%!
    exit /b 1
)
endlocal
goto :eof

:end
echo.
echo =======================================================
echo [TIME: !time!] HOAN TAT TOAN BO TIEN TRINH!
echo =======================================================
endlocal
