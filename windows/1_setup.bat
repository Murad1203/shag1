@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Setup - attestation periods
cd /d "%~dp0.."

echo ============================================================
echo   SETUP / USTANOVKA
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python not found.
    echo     Install Python from https://www.python.org/downloads/
    echo     IMPORTANT: check "Add python.exe to PATH" during install.
    echo     Then run this file again.
    echo.
    pause
    exit /b 1
)

echo [+] Python:
python --version
echo.

echo [*] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [!] Failed to install dependencies. See message above.
    pause
    exit /b 1
)
echo.

if not exist "config.json" (
    copy "config.example.json" "config.json" >nul
    echo [+] config.json created from template.
    echo     Notepad will open now. Paste your Cookie into the "cookie"
    echo     field, save with Ctrl+S and close Notepad.
    echo     ^(How to get Cookie: see windows\CHITAY_MENYA.txt^)
    echo.
    pause
    notepad "config.json"
) else (
    echo [+] config.json already exists - kept as is.
)

echo.
echo ============================================================
echo   DONE. Now you can run:
echo     2_preview.bat  - show what will change (safe)
echo     3_apply.bat    - apply changes
echo ============================================================
echo.
pause
