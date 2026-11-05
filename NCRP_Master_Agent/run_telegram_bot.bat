@echo off
title NCRP Cyber Crime Agent - Live Telegram Bot Service
chcp 65001 >nul
cls

echo ======================================================================================
echo      DELHI POLICE CYBER CRIME INVESTIGATION - LIVE TELEGRAM BOT SERVICE
echo ======================================================================================
echo.
echo [*] Starting NCRP Telegram Bot Service (Long Polling)...
echo.

cd /d "%~dp0"
python telegram_bot_service.py

echo.
pause
