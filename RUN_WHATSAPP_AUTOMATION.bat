@echo off
title NCRP Cyber Crime Agent - Live WhatsApp Automation Service
chcp 65001 >nul
cls

echo ======================================================================================
echo      DELHI POLICE CYBER CRIME INVESTIGATION - LIVE WHATSAPP BOT SERVICE
echo ======================================================================================
echo.
echo [1/2] Starting NCRP Webhook Service on http://localhost:5005 ...
cd /d "%~dp0NCRP_Master_Agent"
start "NCRP Webhook Service (Port 5005)" cmd /k "python whatsapp_webhook_service.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Cloudflare Tunnel and Auto-Syncing with UltraMsg...
echo.
python sync_tunnel_ultramsg.py
pause
