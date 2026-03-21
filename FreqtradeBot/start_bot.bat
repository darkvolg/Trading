@echo off
title TrendRider_CryptoBot - Paper Trading
cd /d "%~dp0"

echo Starting TrendRider_CryptoBot (Paper Trading)...
echo.

if not exist "config.json" (
    echo ERROR: config.json not found in %cd%
    echo.
    pause
    exit /b 1
)

if not exist "user_data\strategies\TrendRiderStrategy.py" (
    echo ERROR: TrendRiderStrategy.py not found in user_data\strategies\
    echo.
    pause
    exit /b 1
)

echo Press Ctrl+C to stop
echo.
freqtrade trade --config config.json --strategy TrendRiderStrategy
echo.
echo Freqtrade exited with code: %errorlevel%
echo.
pause
