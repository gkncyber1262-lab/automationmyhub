@echo off
title NCRP WhatsApp Automation Gateway & Cloudflare Tunnel
chcp 65001 >nul
cls

echo ======================================================================================
echo      DELHI POLICE CYBER CRIME INVESTIGATION - WHATSAPP & n8n AUTOMATION GATEWAY
echo ======================================================================================
echo.
echo [1/2] Starting NCRP Webhook Service on http://localhost:5005 ...
cd /d "%~dp0NCRP_Master_Agent"
start "NCRP Webhook Service (Port 5005)" cmd /k "python whatsapp_webhook_service.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Cloudflare Secure HTTPS Tunnel ...
echo.
echo ======================================================================================
echo Below is your Public HTTPS URL for n8n Webhook:
echo Copy the 'https://*.trycloudflare.com' URL and set it in your n8n workflow!
echo ======================================================================================
echo.
cloudflared tunnel --url http://localhost:5005
pause
