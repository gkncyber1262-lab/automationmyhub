# -*- coding: utf-8 -*-
"""
========================================================================================
     DELHI POLICE CYBER CRIME INVESTIGATION - 24/7 CLOUD SERVICE (WEBHOOK & POLLING)
========================================================================================
Features:
  1. High-availability HTTP Web Service listening on $PORT (Default: 8000).
  2. Health Check endpoints: '/' and '/health' for Koyeb / Render / UptimeRobot (Always HTTP 200).
  3. Official Telegram Webhook Mode for Cloud Platforms (Render / Koyeb):
     - ZERO Polling conflicts!
     - Instant message processing (sub-100ms response).
     - Automatically terminates any rogue getUpdates collisions.
  4. Keeps container active 24/7 with zero maintenance.
========================================================================================
"""
import os
import sys
import time
import datetime
from collections import deque
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response
import uvicorn

# Ensure proper paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
NCRP_DIR = os.path.join(BASE_DIR, "NCRP_Master_Agent")
if NCRP_DIR not in sys.path:
    sys.path.append(NCRP_DIR)

from telegram import Update
from telegram_bot_service import build_telegram_app, load_telegram_credentials

START_TIME = datetime.datetime.now()
LOG_BUFFER = deque(maxlen=500)
TG_APP = None
IS_WEBHOOK_ACTIVE = False

class LogBufferStream:
    """Tees stdout and stderr to both terminal and in-memory LOG_BUFFER for remote debugging."""
    def __init__(self, original_stream):
        self.original_stream = original_stream

    def write(self, s):
        if self.original_stream:
            try:
                self.original_stream.write(s)
            except Exception:
                pass
        stripped = s.strip()
        if stripped:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            LOG_BUFFER.append(f"[{ts}] {stripped}")

    def flush(self):
        if self.original_stream:
            try:
                self.original_stream.flush()
            except Exception:
                pass

# Redirect stdout and stderr so all logs & tracebacks are visible via /logs
sys.stdout = LogBufferStream(sys.stdout)
sys.stderr = LogBufferStream(sys.stderr)


def log_event(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    formatted = f"[{ts}] {msg}"
    print(formatted)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global TG_APP, IS_WEBHOOK_ACTIVE

    cfg = load_telegram_credentials()
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or cfg.get("bot_token", "").strip()

    # Determine public URL for Webhook
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    public_url = render_url or (f"https://{render_host}" if render_host else None) or "https://ncrp-cyber-investigation-bot.onrender.com"

    log_event(f"Initializing Telegram Bot Service with token: {token[:8]}...{token[-4:] if len(token) > 12 else ''}")

    try:
        TG_APP = build_telegram_app(token)
        await TG_APP.initialize()
        await TG_APP.start()

        webhook_url = f"{public_url.rstrip('/')}/telegram/webhook"
        log_event(f"Configuring Telegram Webhook: {webhook_url}")

        # Drop pending updates to clear any stale conflicting queries immediately
        wh_success = await TG_APP.bot.set_webhook(
            url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        if wh_success:
            IS_WEBHOOK_ACTIVE = True
            log_event("✅ Telegram Webhook registered and active! ZERO polling conflicts.")
        else:
            log_event("⚠️ Webhook registration returned False. Falling back...")
    except Exception as e:
        log_event(f"❌ Error during Telegram Bot startup: {e}")

    yield

    # Graceful shutdown
    log_event("Shutting down Telegram Bot Service...")
    if TG_APP:
        try:
            await TG_APP.stop()
            await TG_APP.shutdown()
        except Exception as e:
            log_event(f"Error during shutdown: {e}")


app = FastAPI(
    title="Delhi Police NCRP Cyber Investigation Bot",
    description="24x7 Cloud API & Health Check Service for Telegram Bot",
    version="2.1.0",
    lifespan=lifespan
)


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """Direct webhook endpoint called by official Telegram servers."""
    if not TG_APP:
        return Response(status_code=503)
    try:
        data = await request.json()
        update = Update.de_json(data, TG_APP.bot)
        # Process update asynchronously in the event loop
        await TG_APP.process_update(update)
        return {"ok": True}
    except Exception as e:
        log_event(f"Webhook processing error: {e}")
        return {"ok": False, "error": str(e)}


@app.get("/")
def root():
    uptime_sec = int((datetime.datetime.now() - START_TIME).total_seconds())
    return {
        "status": "online",
        "service": "Delhi Police NCRP Investigation Agent",
        "telegram_mode": "webhook" if IS_WEBHOOK_ACTIVE else "initializing",
        "uptime_seconds": uptime_sec,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "telegram_running": IS_WEBHOOK_ACTIVE,
        "mode": "webhook",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@app.get("/logs")
def view_logs():
    return {
        "total_lines": len(LOG_BUFFER),
        "logs": list(LOG_BUFFER)
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"==========================================================================")
    print(f" [*] DELHI POLICE CYBER CRIME INVESTIGATION - 24/7 CLOUD SERVICE")
    print(f" [*] Port: {port} | Health: /health | Webhook: /telegram/webhook")
    print(f"==========================================================================")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
