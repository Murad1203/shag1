@echo off
chcp 65001 >nul
title Установка — аттестационные периоды
cd /d "%~dp0\.."

echo ============================================================
echo   УСТАНОВКА
echo ============================================================
echo.

REM --- проверка Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python не найден.
    echo.
    echo     Установите Python с https://www.python.org/downloads/
    echo     ВАЖНО: при установке поставьте галочку
    echo     "Add python.exe to PATH" на первом экране установщика.
    echo.
    echo     После установки запустите этот файл ещё раз.
    echo.
    pause
    exit /b 1
)

echo [+] Python найден:
python --version
echo.

echo [*] Устанавливаю зависимости...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [!] Не удалось установить зависимости. См. сообщение выше.
    pause
    exit /b 1
)
echo.

REM --- создаём config.json из шаблона, если его ещё нет ---
if not exist "config.json" (
    copy "config.example.json" "config.json" >nul
    echo [+] Создан config.json из шаблона.
    echo.
    echo     Сейчас откроется config.json в Блокноте.
    echo     Вставьте в поле "cookie" значение из браузера
    echo     (как получить — написано в файле README.md),
    echo     сохраните файл (Ctrl+S) и закройте Блокнот.
    echo.
    pause
    notepad "config.json"
) else (
    echo [+] config.json уже есть — оставляю как есть.
)

echo.
echo ============================================================
echo   ГОТОВО. Теперь можно запускать:
echo     2_Предпросмотр.bat  — показать, что изменится
echo     3_Применить.bat     — применить изменения
echo ============================================================
echo.
pause
