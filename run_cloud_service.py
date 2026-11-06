# -*- coding: utf-8 -*-
"""
========================================================================================
     DELHI POLICE CYBER CRIME INVESTIGATION - 24/7 CLOUD SERVICE RUNNER (KOYEB / DOCKER)
========================================================================================
Features:
  1. High-availability HTTP Web Service listening on $PORT (Default: 8000).
  2. Health Check endpoints: '/' and '/health' for Koyeb / UptimeRobot (Always HTTP 200).
  3. Manages Telegram Bot (Long Polling) in a resilient background supervisor process.
     - Auto-restarts Telegram bot if network connection drops.
  4. Keeps container active 24/7 with zero maintenance.
========================================================================================
"""
import os
import sys
import time
import subprocess
import threading
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
NCRP_DIR = os.path.join(BASE_DIR, "NCRP_Master_Agent")
if NCRP_DIR not in sys.path:
    sys.path.append(NCRP_DIR)

START_TIME = datetime.datetime.now()
BOT_PROCESS = None
IS_RUNNING = True


def telegram_bot_supervisor():
    """Supervises and auto-restarts Telegram Bot process in background."""
    global BOT_PROCESS, IS_RUNNING
    tg_script = os.path.join(NCRP_DIR, "telegram_bot_service.py")

    while IS_RUNNING:
        print(f"\n[Cloud Supervisor] Starting Telegram Bot Service: {tg_script} ...")
        try:
            BOT_PROCESS = subprocess.Popen(
                [sys.executable, tg_script],
                cwd=NCRP_DIR,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            ret_code = BOT_PROCESS.wait()
            print(f"[Cloud Supervisor] Telegram Bot exited with code {ret_code}.")
        except Exception as e:
            print(f"[Cloud Supervisor Error] Exception running Telegram Bot: {e}")

        if IS_RUNNING:
            print("[Cloud Supervisor] Restarting Telegram Bot in 5 seconds...")
            time.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    t = threading.Thread(target=telegram_bot_supervisor, daemon=True)
    t.start()
    print("[Cloud Runner] Telegram Bot Supervisor thread started successfully.")
    yield
    # Shutdown
    global IS_RUNNING, BOT_PROCESS
    IS_RUNNING = False
    if BOT_PROCESS and BOT_PROCESS.poll() is None:
        try:
            BOT_PROCESS.terminate()
            BOT_PROCESS.wait(timeout=5)
        except Exception:
            BOT_PROCESS.kill()


app = FastAPI(
    title="Delhi Police NCRP Cyber Investigation Bot",
    description="24x7 Cloud API & Health Check Service for Telegram Bot",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/")
def root():
    uptime_sec = int((datetime.datetime.now() - START_TIME).total_seconds())
    return {
        "status": "online",
        "service": "Delhi Police NCRP Investigation Agent",
        "telegram_bot": "active" if (BOT_PROCESS and BOT_PROCESS.poll() is None) else "starting",
        "uptime_seconds": uptime_sec,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@app.get("/health")
def health_check():
    # Health check endpoint for Koyeb / UptimeRobot
    return {
        "status": "healthy",
        "telegram_running": bool(BOT_PROCESS and BOT_PROCESS.poll() is None),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"==========================================================================")
    print(f" [*] DELHI POLICE CYBER CRIME INVESTIGATION - 24/7 CLOUD SERVICE")
    print(f" [*] Koyeb HTTP Port: {port} | Healthcheck: /health")
    print(f"==========================================================================")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
