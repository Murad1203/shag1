@echo off
chcp 65001 >nul
title Применить — промежуточный период у 2-4 классов
cd /d "%~dp0\.."

echo ============================================================
echo   ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ на сервере myschool.05edu.ru
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python не найден. Сначала запустите 1_Установка.bat
    pause
    exit /b 1
)

if not exist "config.json" (
    echo [!] Нет config.json. Сначала запустите 1_Установка.bat
    pause
    exit /b 1
)

echo Будет проставлен промежуточный аттестационный период
echo всем группам 2, 3 и 4 классов.
echo.
set /p ANSWER="Продолжить? Напишите да и нажмите Enter: "
if /i not "%ANSWER%"=="да" (
    echo Отменено.
    pause
    exit /b 0
)
echo.

python scripts\assign_intermediate_2_4.py --match "промеж" --apply

echo.
echo ------------------------------------------------------------
echo Готово. Проверьте результат в журнале.
echo ------------------------------------------------------------
echo.
pause
