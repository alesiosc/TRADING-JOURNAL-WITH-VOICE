@echo off
title Trading Journal Pro
echo.
echo ========================================
echo   Trading Journal Pro
echo ========================================
echo.
echo Starting application...
echo.

cd /d "%~dp0"
python.exe trading_journal_final.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start application
    echo.
    pause
)
