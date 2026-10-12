@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Preview - intermediate period for grades 2-4
cd /d "%~dp0.."

echo ============================================================
echo   PREVIEW (nothing is changed on the server)
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python not found. Run 1_setup.bat first.
    pause
    exit /b 1
)

if not exist "config.json" (
    echo [!] config.json missing. Run 1_setup.bat first.
    pause
    exit /b 1
)

python scripts\assign_intermediate_2_4.py

echo.
echo ------------------------------------------------------------
echo This was preview only. To apply, run 3_apply.bat
echo ------------------------------------------------------------
echo.
pause
