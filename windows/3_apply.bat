@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Apply - intermediate period for grades 2-4
cd /d "%~dp0.."

echo ============================================================
echo   APPLY changes on server myschool.05edu.ru
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

echo The intermediate attestation period will be set for ALL
echo groups of grades 2, 3 and 4.
echo.
set /p ANSWER="Continue? Type yes and press Enter: "
if /i not "%ANSWER%"=="yes" (
    echo Cancelled.
    pause
    exit /b 0
)
echo.

python scripts\assign_intermediate_2_4.py --apply

echo.
echo ------------------------------------------------------------
echo Done. Check the result in the journal.
echo ------------------------------------------------------------
echo.
pause
