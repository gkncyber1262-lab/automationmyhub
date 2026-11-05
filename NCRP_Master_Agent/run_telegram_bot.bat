@echo off
title PDF TO BANK NOTICE FOR CYBER INVESTIGATION - Telegram Bot
chcp 65001 >nul
cls

echo ======================================================================================
echo      PDF TO BANK NOTICE FOR CYBER INVESTIGATION - LIVE TELEGRAM BOT
echo ======================================================================================
echo.
echo [*] Starting NCRP Telegram Bot Service (Long Polling)...
echo.

cd /d "%~dp0"
python telegram_bot_service.py

echo.
pause
