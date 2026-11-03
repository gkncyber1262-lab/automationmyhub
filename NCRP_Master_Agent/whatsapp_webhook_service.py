# -*- coding: utf-8 -*-
"""
========================================================================================
     DELHI POLICE CYBER CRIME INVESTIGATION - LIVE WHATSAPP AUTOMATION SERVICE
     (व्हाट्सएप एंड-टू-एंड ऑटोमेशन वेबहुक सर्विस - NCRP मास्टर एजेंट)
========================================================================================
Architecture:
  1. Inbound Webhook:
     - Listens on /webhook/whatsapp or /webhook/n8n for incoming WhatsApp messages/PDFs.
     - Supports UltraMsg, Green API, Meta WhatsApp Cloud API, and n8n Workflows.
  2. Multi-turn State Machine per Officer (Phone Number):
     - Step 0 (Start): Greet IO & prompt for NCRP Complaint PDF.
     - Step 1 (PDF Upload): Downloads PDF, parses fraud metrics, sends summary card.
     - Step 2 (IO & Scheme Select): Offers 1-click IO selection (SI Arvind Kumar, SI Renu, HC Rajendra).
     - Step 3 (Auto-Execution): Generates Bank Notices, ATM CCTV Notices, Combine DOCX, 3D Radar.
     - Step 4 (Document Dispatch): Automatically attaches & sends documents directly on WhatsApp.
  3. Optional Email Trigger:
     - Dispatches notices to official Bank Nodal Officers via email_dispatch_agent.
========================================================================================
"""

import os
import sys
import json
import time
import re
import shutil
import datetime
import requests
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from ncrp_master_agent import NCRPUnifiedAgent

app = FastAPI(
    title="NCRP Master Agent - WhatsApp Automation Webhook Service",
    description="Automated WhatsApp bot for NCRP complaint analysis and notice dispatch",
    version="3.0.0"
)

# Agent instance
agent = NCRPUnifiedAgent(base_dir=BASE_DIR)

# Load WhatsApp credentials if available
WA_CONFIG_FILE = os.path.join(BASE_DIR, "config", "whatsapp_credentials.json")
WA_CONFIG = {}
if os.path.exists(WA_CONFIG_FILE):
    try:
        with open(WA_CONFIG_FILE, "r", encoding="utf-8") as f:
            WA_CONFIG = json.load(f)
    except Exception:
        pass


def get_gateway_credentials():
    """Extracts active gateway and credentials safely from config."""
    cfg = {}
    if os.path.exists(WA_CONFIG_FILE):
        try:
            with open(WA_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = WA_CONFIG
    else:
        cfg = WA_CONFIG

    gateway = cfg.get("active_gateway") or cfg.get("gateway") or "ultramsg"
    gateways = cfg.get("gateways", {})
    
    # UltraMsg
    um = gateways.get("ultramsg") or cfg.get("ultramsg") or {}
    um_instance = um.get("instance_id") or cfg.get("instance_id", "instance196090")
    um_token = um.get("token") or cfg.get("token", "gs4m9i7tr8cmi8iq")
    
    # GreenAPI
    ga = gateways.get("green_api") or gateways.get("greenapi") or cfg.get("greenapi") or {}
    ga_inst = ga.get("id_instance") or ga.get("idInstance") or ""
    ga_token = ga.get("api_token_instance") or ga.get("api_token") or ""
    
    return gateway.lower(), um_instance, um_token, ga_inst, ga_token


# In-memory session tracking per phone number
USER_SESSIONS: Dict[str, Dict[str, Any]] = {}


def send_whatsapp_text(to_number: str, text: str):
    """Sends a text message via configured WhatsApp Gateway (UltraMsg / Green API)."""
    clean_phone = re.sub(r'[^0-9]', '', str(to_number))
    gateway, um_instance, um_token, ga_inst, ga_token = get_gateway_credentials()

    if gateway == "ultramsg" and um_instance and um_token:
        url = f"https://api.ultramsg.com/{um_instance}/messages/chat"
        payload = {"token": um_token, "to": clean_phone, "body": text}
        try:
            r = requests.post(url, data=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            print(f"[WA Send] Text to {clean_phone}: HTTP {r.status_code}")
            return True
        except Exception as e:
            print(f"[WA Error] Text send failed: {e}")

    elif gateway in ["greenapi", "green_api"] and ga_inst and ga_token:
        url = f"https://api.green-api.com/waInstance{ga_inst}/sendMessage/{ga_token}"
        payload = {"chatId": f"{clean_phone}@c.us", "message": text}
        try:
            r = requests.post(url, json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            print(f"[GreenAPI Send] Text to {clean_phone}: HTTP {r.status_code}")
            return True
        except Exception as e:
            print(f"[WA Error] Text send failed: {e}")

    print(f"[DRY-RUN WA TEXT to {to_number}]:\n{text}\n")
    return False


def send_whatsapp_document(to_number: str, file_path: str, caption: str = ""):
    """Sends a document (DOCX/PDF) or image via WhatsApp Gateway."""
    clean_phone = re.sub(r'[^0-9]', '', str(to_number))
    if not os.path.exists(file_path):
        return False

    gateway, um_instance, um_token, ga_inst, ga_token = get_gateway_credentials()
    fname = os.path.basename(file_path)

    if gateway == "ultramsg" and um_instance and um_token:
        url = f"https://api.ultramsg.com/{um_instance}/messages/document"
        payload = {
            "token": um_token,
            "to": clean_phone,
            "filename": fname,
            "caption": caption
        }
        try:
            with open(file_path, "rb") as f:
                files = {"file": (fname, f)}
                r = requests.post(url, data=payload, files=files, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
                print(f"[WA Send] Doc {fname} to {clean_phone}: HTTP {r.status_code}")
            return True
        except Exception as e:
            print(f"[WA Error] Document send failed: {e}")

    print(f"[DRY-RUN WA DOC to {to_number}]: {fname} ({caption})")
    return False


def process_case_background(sender: str, pdf_path: str, io_name: str, notice_no: int):
    """Executes the pipeline in background and dispatches files to WhatsApp."""
    try:
        send_whatsapp_text(sender, "⏳ जांच प्रगति पर है... बैंक नोटिस, कंबाइंड DOCX, 3D फ्लोचार्ट और केस डायरी तैयार की जा रही है। कृपया 20-30 सेकंड प्रतीक्षा करें...")

        # Resolve IO details
        io_mobile = "8750871987"
        io_rank = "SUB INSPECTOR"
        if "rajendra" in io_name.lower():
            io_rank = "HEAD CONSTABLE"
            io_mobile = "9818036472"

        io_override = {
            "name": io_name,
            "rank": io_rank,
            "belt_no": io_mobile,
            "mobile": io_mobile
        }

        # Run pipeline
        res = agent.run_case_pipeline(
            case_file_or_target=pdf_path,
            fir_details={"is_fir": False},
            io_override=io_override,
            start_notice_no=notice_no,
            notice_date_override=datetime.datetime.now().strftime("%d/%m/%Y"),
            sign_mode="both"
        )

        ack = res.get("acknowledgement_no", "")
        case_dir = os.path.join(agent.output_dir, f"Case_{ack}")

        # Send completion card
        send_whatsapp_text(sender, f"✅ सफलता! केस ACK No. {ack} के सभी नोटिस व दस्तावेज़ तैयार कर दिए गए हैं। अब फाइल्स प्रेषित की जा रही हैं...")

        # 1. Send Combine Notice DOCX (Consolidated)
        combine_docx = os.path.join(case_dir, "combine_notice", f"Combine_Notice_All_Banks_{notice_no}.docx")
        if os.path.exists(combine_docx):
            send_whatsapp_document(sender, combine_docx, caption=f"📄 कंबाइंड बैंक नोटिस (Combine Notice #{notice_no}) - सभी बैंकों हेतु एकल DOCX फ़ाइल")

        # 2. Send 3D Money Trail Image
        radar_img = os.path.join(case_dir, f"forensic_money_trail_3d_{ack}.png")
        if os.path.exists(radar_img):
            send_whatsapp_document(sender, radar_img, caption="📊 फोरेंसिक मनी ट्रेल 3D विज़ुअल चार्ट (Layer 1 से Layer 5)")

        # 3. Send Individual Bank Notice PDFs
        pdf_dir = os.path.join(case_dir, "Notice_PDF_Files")
        if os.path.isdir(pdf_dir):
            pdfs = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
            # Send up to first 5 primary notices directly
            for p in pdfs[:5]:
                send_whatsapp_document(sender, p, caption=f"📑 {os.path.basename(p)}")

        send_whatsapp_text(sender, f"📁 संपूर्ण केस दस्तावेज़ सर्वर पर सुरक्षित हैं:\n📂 Case Folder: Case_{ack}/\nकुल तैयार नोटिस: {len(pdfs) if os.path.isdir(pdf_dir) else 0}\n\nनया केस शुरू करने के लिए 'Start' लिखें।")

    except Exception as e:
        send_whatsapp_text(sender, f"❌ केस निष्पादन में त्रुटि आई: {str(e)}")


@app.get("/")
def home():
    return {
        "service": "NCRP Unified Master Agent - WhatsApp Automation Gateway",
        "status": "ONLINE",
        "supported_gateways": ["UltraMsg", "Green API", "Meta WhatsApp Cloud API", "n8n Webhook"],
        "time": datetime.datetime.now().isoformat()
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "NCRP WhatsApp Gateway", "port": 5005}


@app.post("/webhook/whatsapp")
@app.post("/webhook/n8n")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook receiver for incoming WhatsApp messages and PDF uploads.
    Handles UltraMsg, GreenAPI, and n8n forwarded payloads seamlessly.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    # Support UltraMsg wrapped 'data' payload or flat JSON
    data = body.get("data", body) if isinstance(body.get("data"), dict) else body

    # Ignore outgoing messages sent by the bot itself
    if data.get("fromMe") is True or body.get("fromMe") is True:
        return JSONResponse({"status": "ignored", "reason": "outgoing message from self"})

    # Extract sender, text, and media
    sender = data.get("from") or data.get("chatId") or data.get("sender") or body.get("from") or body.get("sender") or ""
    msg_type = data.get("type", "chat")
    text = (data.get("body") or data.get("text") or data.get("message") or body.get("body") or "").strip()
    
    # In UltraMsg, document URLs are in data['media'] or data['body'] when type == 'document'
    media_url = ""
    if msg_type in ["document", "image", "audio", "video"] or text.startswith("http"):
        media_url = data.get("media") or data.get("body") or body.get("mediaUrl") or body.get("documentUrl") or ""
        if media_url.startswith("http"):
            text = ""  # Clean text so it doesn't collide with commands
            
    media_name = data.get("filename") or data.get("caption") or body.get("filename") or "complaint.pdf"

    if not sender:
        return JSONResponse({"status": "ignored", "reason": "no sender identified"})

    sender_clean = re.sub(r'[^0-9]', '', sender)
    session = USER_SESSIONS.setdefault(sender_clean, {"state": 0})

    # Greeting / Reset command
    if text.lower() in ["hi", "hello", "start", "shuru", "reset"]:
        USER_SESSIONS[sender_clean] = {"state": 1}
        greeting = (
            "👮‍♂️ *नमस्ते सर! दिल्ली पुलिस NCRP साइबर अपराध अन्वेषण ऑटोमेशन में आपका स्वागत है।*\n\n"
            "कृपया अपनी *NCRP शिकायत की PDF फ़ाइल* यहाँ WhatsApp पर अपलोड करें।\n"
            "मैं तुरंत मनी ट्रेल का विश्लेषण कर सभी बैंकों के नोटिस व 3D चार्ट तैयार कर दूंगा।"
        )
        send_whatsapp_text(sender, greeting)
        return {"status": "prompted_for_pdf"}

    # Handle incoming PDF upload
    if media_url or (session.get("state") == 1 and text.endswith(".pdf")):
        target_pdf_path = os.path.join(agent.input_dir, f"WA_{int(time.time())}_{media_name}")
        
        # Download media if URL provided
        if media_url.startswith("http"):
            try:
                r = requests.get(media_url, timeout=30)
                with open(target_pdf_path, "wb") as f:
                    f.write(r.content)
            except Exception as e:
                send_whatsapp_text(sender, f"❌ PDF डाउनलोड करने में विफल: {e}")
                return {"status": "download_failed"}
        else:
            # Fallback to sample if testing
            sample_pdf = os.path.join(agent.input_dir, "AcknowledgementNo_30810260096039.pdf")
            if os.path.exists(sample_pdf):
                shutil.copy2(sample_pdf, target_pdf_path)

        # Parse basic metrics for confirmation card
        temp_dir = os.path.join(agent.output_dir, "_wa_temp")
        ctx = agent.parse_ncrp_pdf(target_pdf_path, temp_dir)
        meta = ctx.get("case_meta", {})
        comp = ctx.get("complainant", {})
        fin = ctx.get("financial_summary", {})

        session["state"] = 2
        session["pdf_path"] = target_pdf_path
        session["ack_no"] = meta.get("acknowledgement_no", "")

        summary_card = (
            f"📋 *NCRP शिकायत प्राप्त व विश्लेषित!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"• *Ack No.*: {meta.get('acknowledgement_no')}\n"
            f"• *पीड़ित का नाम*: {comp.get('name')}\n"
            f"• *ठगी की राशि*: Rs. {fin.get('alleged_amount')}\n"
            f"• *होल्ड राशि*: Rs. {fin.get('total_lien_amount')}\n"
            f"• *बैंक लेयर्स*: 1 से 5 (CCTV व चेक पूर्णतः बहिष्कृत)\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *कृपया जांच अधिकारी (IO) का चयन करें:*\n"
            f"*[1]* SI ARVIND KUMAR (हस्ताक्षर: arvind.png)\n"
            f"*[2]* SI RENU (हस्ताक्षर: renu sign.png)\n"
            f"*[3]* HC RAJENDRA (हस्ताक्षर: rajendra sign.png)\n\n"
            f"👉 उत्तर में केवल *1*, *2* या *3* लिखकर भेजें:"
        )
        send_whatsapp_text(sender, summary_card)
        return {"status": "pdf_received_awaiting_io"}

    # Handle IO Selection
    if session.get("state") == 2:
        io_choice = text.strip()
        io_name = "SI ARVIND KUMAR"
        if io_choice == "2":
            io_name = "SI RENU"
        elif io_choice == "3":
            io_name = "HC RAJENDRA"

        session["io_name"] = io_name
        session["state"] = 3

        prompt_notice_no = (
            f"✅ चयनित जांच अधिकारी: *{io_name}*\n\n"
            f"📌 *नोटिस नंबर दर्ज करें:*\n"
            f"डिफ़ॉल्ट नोटिस नंबर *5744* रखने के लिए केवल *Y* भेजें, या अपना इच्छित नोटिस नंबर टाइप करें (उदा. 5745):"
        )
        send_whatsapp_text(sender, prompt_notice_no)
        return {"status": "awaiting_notice_no"}

    # Handle Notice Number & Trigger Execution
    if session.get("state") == 3:
        ans_num = text.strip()
        notice_no = 5744
        if ans_num.isdigit():
            notice_no = int(ans_num)

        pdf_path = session.get("pdf_path")
        io_name = session.get("io_name", "SI ARVIND KUMAR")
        session["state"] = 0  # Reset session

        # Launch processing in background
        background_tasks.add_task(process_case_background, sender, pdf_path, io_name, notice_no)
        return {"status": "processing_started", "notice_no": notice_no, "io": io_name}

    # Default fallback
    send_whatsapp_text(sender, "नमस्ते सर! नया केस शुरू करने के लिए कृपया *Start* लिखें।")
    return {"status": "help_sent"}


if __name__ == "__main__":
    print("=" * 80)
    print("  DELHI POLICE NCRP AGENT - LIVE WHATSAPP WEBHOOK SERVICE")
    print("  Starting FastAPI server on http://127.0.0.1:5005 ...")
    print("=" * 80)
    uvicorn.run(app, host="0.0.0.0", port=5005)
