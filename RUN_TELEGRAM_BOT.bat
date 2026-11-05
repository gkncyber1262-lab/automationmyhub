@echo off
title PDF TO BANK NOTICE FOR CYBER INVESTIGATION - Telegram Bot
chcp 65001 >nul
cls

echo ======================================================================================
echo      PDF TO BANK NOTICE FOR CYBER INVESTIGATION - LIVE TELEGRAM BOT
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
