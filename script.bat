@echo off
title Radiant Historia - Undub

if "%~1"=="" (
    echo [ERROR] Please drag and drop a .cia file onto this script.
    echo.
    pause
    exit /b
)

python main.py "%~1"

echo.
pause
