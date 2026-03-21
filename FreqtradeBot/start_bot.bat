@echo off
title VZIK_CryptoBot - Paper Trading
cd /d "%~dp0"
echo Starting VZIK_CryptoBot (Paper Trading)...
echo Press Ctrl+C to stop
echo.
freqtrade trade --config config.json --strategy VZIKStrategy_v6
pause
