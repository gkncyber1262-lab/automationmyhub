# -*- coding: utf-8 -*-
"""
Auto-sync Cloudflare Tunnel URL with UltraMsg Webhook.
Automatically starts cloudflared, extracts the active trycloudflare.com URL,
and configures UltraMsg instance settings with zero manual effort.
"""

import os
import sys
import re
import time
import json
import subprocess
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "whatsapp_credentials.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def find_cloudflared():
    paths = [
        r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
        r"C:\Program Files\cloudflared\cloudflared.exe",
        "cloudflared"
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return "cloudflared"

def update_ultramsg_webhook(instance_id: str, token: str, new_url: str):
    webhook_url = f"{new_url.rstrip('/')}/webhook/whatsapp"
    api_url = f"https://api.ultramsg.com/{instance_id}/instance/settings"
    payload = {
        "token": token,
        "webhook_url": webhook_url,
        "webhook_message_received": "true",
        "webhook_message_create": "false",
        "webhook_message_ack": "false",
        "webhook_message_download_media": "true"
    }
    try:
        r = requests.post(api_url, data=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        print(f"  ✅ UltraMsg Webhook updated successfully to:\n     {webhook_url}")
        print(f"  Response: {r.json()}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to update UltraMsg: {e}")
        return False

def main():
    cfg = load_config()
    um_cfg = cfg.get("gateways", {}).get("ultramsg") or cfg.get("ultramsg") or {}
    instance_id = um_cfg.get("instance_id") or cfg.get("instance_id", "instance196090")
    token = um_cfg.get("token") or cfg.get("token", "gs4m9i7tr8cmi8iq")
    
    bin_path = find_cloudflared()
    print("=" * 75)
    print("  DELHI POLICE NCRP AGENT - CLOUDFLARE TUNNEL AUTO-SYNC")
    print(f"  UltraMsg Instance: {instance_id}")
    print(f"  Cloudflared Binary: {bin_path}")
    print("=" * 75)
    print("\n⏳ Starting Cloudflare Tunnel...")
    
    cmd = [bin_path, "tunnel", "--url", "http://localhost:5005"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )
    
    tunnel_url = None
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
    
    for line in iter(proc.stdout.readline, ''):
        print(line, end="")
        if not tunnel_url:
            match = url_pattern.search(line)
            if match:
                tunnel_url = match.group(0)
                print("\n" + "★" * 75)
                print(f"  🎯 DETECTED PUBLIC TUNNEL URL: {tunnel_url}")
                print("★" * 75)
                update_ultramsg_webhook(instance_id, token, tunnel_url)
                print("=" * 75 + "\n")

    proc.stdout.close()
    proc.wait()

if __name__ == "__main__":
    main()
