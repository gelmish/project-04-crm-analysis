@echo off
echo.
echo ============================================================
echo  PipelineIQ -- CRM System Analysis
echo  Project 4 -- Gelmish Technology Ltd
echo  Deploy Script
echo ============================================================
echo.

:: ── Step 1: Install dependencies ─────────────────────────────────
echo [1/5] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Check Python installation.
    pause
    exit /b 1
)
echo       Done.
echo.

:: ── Step 2: Generate raw data ─────────────────────────────────────
echo [2/5] Generating CRM data...
python python\generate_data.py
if %errorlevel% neq 0 (
    echo ERROR: Data generation failed.
    pause
    exit /b 1
)
echo       Done.
echo.

:: ── Step 3: Clean data ────────────────────────────────────────────
echo [3/5] Cleaning data...
python python\data_cleaning.py
if %errorlevel% neq 0 (
    echo ERROR: Data cleaning failed.
    pause
    exit /b 1
)
echo       Done.
echo.

:: ── Step 4: Run analysis ──────────────────────────────────────────
echo [4/5] Running analysis...
python python\eda.py
python python\analysis.py
if %errorlevel% neq 0 (
    echo ERROR: Analysis failed.
    pause
    exit /b 1
)
echo       Done.
echo.

:: ── Step 5: Generate dashboard data ──────────────────────────────
echo [5/5] Building dashboard data...
python python\generate_dashboard_data.py
if %errorlevel% neq 0 (
    echo ERROR: Dashboard data generation failed.
    pause
    exit /b 1
)
echo       Done.
echo.

:: ── Open dashboard ───────────────────────────────────────────────
echo ============================================================
echo  All steps complete.
echo  Opening dashboard...
echo ============================================================
echo.
start dashboard\index.html

pause