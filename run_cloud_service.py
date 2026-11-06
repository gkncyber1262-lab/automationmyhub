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
from collections import deque
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
LOG_BUFFER = deque(maxlen=200)
LAST_EXIT_INFO = {"code": None, "time": None}


def telegram_bot_supervisor():
    """Supervises and auto-restarts Telegram Bot process in background."""
    global BOT_PROCESS, IS_RUNNING, LAST_EXIT_INFO
    tg_script = os.path.join(NCRP_DIR, "telegram_bot_service.py")

    while IS_RUNNING:
        msg = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [Supervisor] Spawning: {sys.executable} {tg_script}"
        print(msg)
        LOG_BUFFER.append(msg)
        try:
            BOT_PROCESS = subprocess.Popen(
                [sys.executable, "-u", tg_script],
                cwd=NCRP_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            # Stream output into LOG_BUFFER and stdout
            for line in iter(BOT_PROCESS.stdout.readline, ''):
                clean_l = line.rstrip()
                if clean_l:
                    print(clean_l)
                    LOG_BUFFER.append(clean_l)
            BOT_PROCESS.wait()
            ret_code = BOT_PROCESS.returncode
            LAST_EXIT_INFO = {"code": ret_code, "time": datetime.datetime.now().strftime('%H:%M:%S')}
            exit_msg = f"[Supervisor] Bot exited with code {ret_code}."
            print(exit_msg)
            LOG_BUFFER.append(exit_msg)
        except Exception as e:
            err_msg = f"[Supervisor Error] {e}"
            print(err_msg)
            LOG_BUFFER.append(err_msg)

        if IS_RUNNING:
            wait_msg = "[Supervisor] Restarting in 5 seconds..."
            print(wait_msg)
            LOG_BUFFER.append(wait_msg)
            time.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    t = threading.Thread(target=telegram_bot_supervisor, daemon=True)
    t.start()
    print("[Cloud Runner] Telegram Bot Supervisor started.")
    yield
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
    is_active = bool(BOT_PROCESS and BOT_PROCESS.poll() is None)
    return {
        "status": "online",
        "service": "Delhi Police NCRP Investigation Agent",
        "telegram_bot": "active" if is_active else "restarting",
        "uptime_seconds": uptime_sec,
        "last_exit": LAST_EXIT_INFO,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


@app.get("/health")
def health_check():
    is_active = bool(BOT_PROCESS and BOT_PROCESS.poll() is None)
    return {
        "status": "healthy",
        "telegram_running": is_active,
        "last_exit": LAST_EXIT_INFO,
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
    print(f" [*] Port: {port} | Health: /health | Logs: /logs")
    print(f"==========================================================================")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
