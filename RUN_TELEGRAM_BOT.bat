@echo off
title NCRP Cyber Crime Agent - Live Telegram Bot Service
chcp 65001 >nul
cls

echo ======================================================================================
echo      DELHI POLICE CYBER CRIME INVESTIGATION - LIVE TELEGRAM BOT SERVICE
echo ======================================================================================
echo.
echo [*] Starting NCRP Telegram Bot Service (Long Polling)...
echo [*] Note: No public URL or Cloudflare/Ngrok tunnel required for Telegram!
echo.

cd /d "%~dp0NCRP_Master_Agent"
python telegram_bot_service.py

echo.
echo ======================================================================================
echo Telegram Bot stopped. Press any key to exit...
echo ======================================================================================
pause >nul
