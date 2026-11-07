# -*- coding: utf-8 -*-
"""
========================================================================================
     DELHI POLICE CYBER CRIME INVESTIGATION - LIVE TELEGRAM BOT SERVICE
     (टेलीग्राम एंड-टू-एंड ऑटोमेशन बॉट सर्विस - NCRP मास्टर एजेंट)
========================================================================================
Architecture:
  1. Long Polling Connection:
     - Connects directly to Telegram servers via official Telegram Bot API (PTB v22+).
     - NO tunnels, NO port-forwarding, NO public IP required!
  2. Multi-turn State Machine & Interactive Inline Buttons:
     - Step 0 (Start): Greet IO & prompt for NCRP Complaint PDF.
     - Step 1 (PDF Upload): Downloads PDF, parses fraud metrics, sends summary card.
     - Step 2 (IO Select): [SI Arvind Kumar] / [SI Renu] / [HC Rajendra] (1-tap buttons).
     - Step 3 (FIR Reference): [Only NCRP Complaint] / [Registered FIR] (Asks FIR No).
     - Step 3.1 (FIR Date): If FIR, prompt for FIR Date [Today / Custom].
     - Step 4 (Notice Date): Prompt for Notice Date [Today / Custom].
     - Step 5 (Notice Type): [Both Bank & ATM] / [Bank Only] / [ATM CCTV Only].
     - Step 6 (Layer Range): [Layer 1] / [Layer 2] / [Layer 3] / [Layer 4] / [Layer 5] / [All Layers].
     - Step 7 (Notice No): Starting notice number (Default: 5744 or custom).
     - Step 8 (Email Choice): [Default NIC] / [Custom Email] / [No Email (Telegram only)].
  3. Execution & Delivery:
     - Executes full case pipeline in worker thread with pythoncom CoInitialize.
     - Delivers Combine DOCX, Pure White Flowchart Photo, Individual Bank Notice PDFs,
       ATM CCTV Notices, and a complete ZIP bundle directly into Telegram chat!
     - Optional Email Automation via Gmail dispatch.
========================================================================================
"""

import os
import sys
import json
import time
import re
import shutil
import glob
import zipfile
import datetime
import asyncio
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from ncrp_master_agent import NCRPUnifiedAgent

# Telegram Imports
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile
)
from telegram.constants import ChatAction, ParseMode
from telegram.request import HTTPXRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Config path
TG_CONFIG_FILE = os.path.join(BASE_DIR, "config", "telegram_credentials.json")

# Initialize Agent
agent = NCRPUnifiedAgent(base_dir=BASE_DIR)

# Thread pool for non-blocking pipeline execution (MS Word COM automation)
EXECUTOR = ThreadPoolExecutor(max_workers=2)

# In-memory session tracking per user/chat ID
USER_SESSIONS: Dict[int, Dict[str, Any]] = {}


def load_telegram_credentials() -> Dict[str, Any]:
    """Loads Telegram configuration safely."""
    cfg = {}
    if os.path.exists(TG_CONFIG_FILE):
        try:
            with open(TG_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            print(f"[Config Warning] Error reading {TG_CONFIG_FILE}: {e}")

    # Fallback to environment variable
    env_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if env_token:
        cfg["bot_token"] = env_token

    env_admin = os.environ.get('TELEGRAM_ADMIN_CHAT_ID')
    if env_admin:
        try:
            a_id = int(env_admin)
            admins = cfg.setdefault('admin_chat_ids', [])
            if a_id not in admins:
                admins.append(a_id)
            alloweds = cfg.setdefault('allowed_chat_ids', [])
            if a_id not in alloweds:
                alloweds.append(a_id)
        except Exception:
            pass

    return cfg


def save_telegram_token(token: str):
    """Saves Telegram Bot Token to config."""
    cfg = load_telegram_credentials()
    cfg["bot_token"] = token.strip()
    os.makedirs(os.path.dirname(TG_CONFIG_FILE), exist_ok=True)
    with open(TG_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"[Config] Telegram bot token saved to {TG_CONFIG_FILE}")


def parse_date_input(val: str) -> str:
    """Parses arbitrary user date input into standard DD/MM/YYYY format."""
    s = val.strip().lower()
    today_str = datetime.datetime.now().strftime("%d/%m/%Y")
    if s in ["today", "aaj", "t", "now", "default", "y", "yes", "d"]:
        return today_str
    m = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', s)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        return f"{d:02d}/{mth:02d}/{y:04d}"
    return today_str


def parse_io_details(raw_input: str) -> Dict[str, str]:
    """
    Parses Investigating Officer input accurately:
    Preserves exact custom name, extracts mobile number if given,
    and accurately identifies rank without overriding custom names.
    """
    s = (raw_input or "").strip()
    if not s:
        return {
            "name": "SI ARVIND KUMAR",
            "rank": "SUB INSPECTOR",
            "mobile": "8750871987"
        }

    # Extract mobile number if included (10 digits)
    io_mobile = ""
    m_mob = re.search(r'\b([6-9]\d{9})\b', s)
    if m_mob:
        io_mobile = m_mob.group(1)
        s = re.sub(r'[\(\[\{]?\b' + io_mobile + r'\b[\)\]\}]?', '', s).strip()
        s = re.sub(r'(?i)\b(mob|mobile|phone|ph|no|contact)\b[:.-]?', '', s).strip()

    s_clean = re.sub(r'\s+', ' ', s).strip()
    s_upper = s_clean.upper()

    # Pre-configured known officers (strict exact/shorthand matches)
    if s_upper in ["1", "ARVIND", "SI ARVIND", "SI ARVIND KUMAR"]:
        return {
            "name": "SI ARVIND KUMAR",
            "rank": "SUB INSPECTOR",
            "mobile": "8750871987"
        }
    if s_upper in ["2", "RENU", "SI RENU", "W/SI RENU", "WSI RENU"]:
        return {
            "name": "SI RENU",
            "rank": "SUB INSPECTOR",
            "mobile": "9899959840"
        }
    if s_upper in ["3", "RAJENDRA", "HC RAJENDRA", "HC RAJENDRA KUMAR"]:
        return {
            "name": "HC RAJENDRA",
            "rank": "HEAD CONSTABLE",
            "mobile": "9818036472"
        }

    # Extract rank if prefixed
    rank_map = {
        "W/SI": "SUB INSPECTOR",
        "WSI": "SUB INSPECTOR",
        "SI": "SUB INSPECTOR",
        "SUB INSPECTOR": "SUB INSPECTOR",
        "HC": "HEAD CONSTABLE",
        "HEAD CONSTABLE": "HEAD CONSTABLE",
        "ASI": "ASSISTANT SUB INSPECTOR",
        "ASST SUB INSPECTOR": "ASSISTANT SUB INSPECTOR",
        "INSP": "INSPECTOR",
        "INSPECTOR": "INSPECTOR",
        "SHO": "SHO / INSPECTOR",
        "CT": "CONSTABLE",
        "CONSTABLE": "CONSTABLE"
    }

    m_rank = re.match(r'^(W/SI|WSI|SUB INSPECTOR|SI|HEAD CONSTABLE|HC|ASST SUB INSPECTOR|ASI|INSPECTOR|INSP|SHO|CONSTABLE|CT)\b\s*(.*)', s_clean, re.I)
    if m_rank:
        r_key = m_rank.group(1).upper()
        io_rank = rank_map.get(r_key, r_key)
        # Keep full name as entered in upper case e.g. "SI RAMESH"
        io_name = s_upper
    else:
        io_rank = "INVESTIGATING OFFICER"
        io_name = s_upper

    return {
        "name": io_name,
        "rank": io_rank,
        "mobile": io_mobile
    }


def get_user_session(user_id: int) -> Dict[str, Any]:
    """Gets or initializes session state for a user."""
    today_str = datetime.datetime.now().strftime("%d/%m/%Y")
    if user_id not in USER_SESSIONS:
        USER_SESSIONS[user_id] = {
            "state": "idle",
            "pdf_path": None,
            "ack_no": None,
            "io_name": "SI ARVIND KUMAR",
            "io_rank": "SUB INSPECTOR",
            "io_mobile": "8750871987",
            "fir_details": {"is_fir": False, "fir_no": "", "fir_date": today_str},
            "fir_date": today_str,
            "notice_date": today_str,
            "notice_type": "both",
            "max_layer": 5,
            "notice_no": 5744,
            "email_settings": {"send_email": False, "target_email": None}
        }
    return USER_SESSIONS[user_id]


def reset_user_session(user_id: int):
    """Resets session for a user."""
    today_str = datetime.datetime.now().strftime("%d/%m/%Y")
    USER_SESSIONS[user_id] = {
        "state": "awaiting_pdf",
        "pdf_path": None,
        "ack_no": None,
        "io_name": "SI ARVIND KUMAR",
        "fir_details": {"is_fir": False, "fir_no": "", "fir_date": today_str},
        "fir_date": today_str,
        "notice_date": today_str,
        "notice_type": "both",
        "max_layer": 5,
        "notice_no": 5744,
        "email_settings": {"send_email": False, "target_email": None}
    }


def save_telegram_credentials(cfg: dict):
    """Persists config safely to telegram_credentials.json."""
    os.makedirs(os.path.dirname(TG_CONFIG_FILE), exist_ok=True)
    with open(TG_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def is_admin(chat_id: int) -> bool:
    """Checks if a chat_id has administrative rights."""
    cfg = load_telegram_credentials()
    admins = cfg.get("admin_chat_ids", [])
    if not admins:
        admins = [8160205906]
    return str(chat_id).strip() in {str(a).strip() for a in admins}


def is_authorized(chat_id: int) -> bool:
    """Checks if a chat_id is allowed to interact with the bot."""
    if is_admin(chat_id):
        return True
    cfg = load_telegram_credentials()
    allowed = cfg.get("allowed_chat_ids", [])
    if not allowed:
        return True
    allowed_str_set = {str(item).strip() for item in allowed if str(item).strip()}
    return str(chat_id).strip() in allowed_str_set


def add_allowed_chat_id(new_id: int) -> bool:
    """Adds a new chat_id to allowed list in config."""
    cfg = load_telegram_credentials()
    allowed = cfg.get("allowed_chat_ids", [])
    target = int(str(new_id).strip())
    existing = [int(str(x).strip()) for x in allowed if str(x).strip().isdigit()]
    if target not in existing:
        existing.append(target)
        cfg["allowed_chat_ids"] = existing
        save_telegram_credentials(cfg)
        return True
    return False


def remove_allowed_chat_id(target_id: int) -> bool:
    """Removes a chat_id from allowed list in config."""
    cfg = load_telegram_credentials()
    allowed = cfg.get("allowed_chat_ids", [])
    target_str = str(target_id).strip()
    new_allowed = [x for x in allowed if str(x).strip() != target_str]
    if len(new_allowed) != len(allowed):
        cfg["allowed_chat_ids"] = new_allowed
        save_telegram_credentials(cfg)
        return True
    return False


async def check_access(update: Update) -> bool:
    """Verifies user authorization before processing any command, document or query."""
    # Allow request access callback through unconditionally
    if update.callback_query and update.callback_query.data and update.callback_query.data.startswith("req_access:"):
        return True

    chat = update.effective_chat
    if not chat:
        return False
    chat_id = chat.id
    if not is_authorized(chat_id):
        user_name = update.effective_user.first_name if update.effective_user else "Officer"
        msg = (
            f"🚫 *अनाधिकृत पहुंच (Access Restricted)*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"नमस्ते {user_name}, यह आधिकारिक PDF TO BANK NOTICE FOR CYBER INVESTIGATION बॉट है।\n\n"
            f"• *आपकी Chat ID*: `{chat_id}`\n\n"
            f"⚠️ यह बॉट केवल अधिकृत जांच अधिकारियों हेतु सीमित है।\n"
            f"यदि आप जांच अधिकारी हैं, तो कृपया नीचे दिए गए बटन पर क्लिक करके एडमिन से पहुंच की अनुमति मांगें:"
        )
        keyboard = [
            [InlineKeyboardButton("📩 एडमिन से एक्सेस की अनुमति मांगें (Request Access)", callback_data=f"req_access:{chat_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.message:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        print(f"[AUTH DENIED] Unauthorized access attempt from Chat ID: {chat_id}")
        return False
    return True


def extract_amount_value(amt_val) -> float:
    """Extracts a numeric float value from amount strings such as '1,50,000.00' or 'Rs. 50000'."""
    if amt_val is None:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', str(amt_val))
    try:
        return float(cleaned)
    except Exception:
        return 0.0


def create_case_zip_bundle(case_dir: str) -> Optional[str]:
    """Creates an optimized, non-redundant ZIP archive of all generated notices and files (strictly under 45MB)."""
    try:
        base_name = os.path.basename(case_dir)
        zip_path = os.path.join(case_dir, f"All_Notices_Bundle_{base_name}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(case_dir):
                rel_root = os.path.relpath(root, case_dir).lower()
                # Exclude duplicate individual_notices directory to keep under 50MB
                if 'individual_notices' in rel_root:
                    continue
                for f in files:
                    if f.endswith(('.docx', '.pdf', '.png', '.jpg', '.xlsx', '.html')) and not f.endswith('.zip'):
                        fp = os.path.join(root, f)
                        rel_path = os.path.relpath(fp, case_dir)
                        zf.write(fp, rel_path)
        sz_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"[ZIP Bundle Created] {zip_path} ({sz_mb:.2f} MB)")
        if sz_mb > 48.0:
            print(f"[ZIP Warning] Archive exceeds 48MB ({sz_mb:.2f} MB). Skipping zip to prevent upload freeze.")
            return None
        return zip_path
    except Exception as e:
        print(f"[ZIP Warning] Could not create zip: {e}")
        return None


async def safe_send_document(
    bot,
    chat_id: int,
    file_path: str,
    caption: str = "",
    parse_mode = None,
    retries: int = 3
) -> bool:
    """Sends document with automatic retries, extended timeouts (180s), and error resilience."""
    if not file_path or not os.path.exists(file_path):
        print(f"[Send Doc] File not found: {file_path}")
        return False

    for attempt in range(1, retries + 1):
        try:
            with open(file_path, "rb") as f:
                await bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    caption=caption,
                    parse_mode=parse_mode,
                    read_timeout=180.0,
                    write_timeout=180.0,
                    connect_timeout=60.0
                )
            return True
        except Exception as ex:
            print(f"[Send Doc Retry {attempt}/{retries}] {os.path.basename(file_path)}: {ex}")
            if attempt < retries:
                await asyncio.sleep(2 * attempt)
            else:
                print(f"[Send Doc Failed] {file_path}: {ex}")
                return False
    return False


async def safe_send_photo(
    bot,
    chat_id: int,
    photo_path: str,
    caption: str = "",
    parse_mode = None,
    retries: int = 3
) -> bool:
    """Sends photo with automatic retries and extended timeouts (180s)."""
    if not photo_path or not os.path.exists(photo_path):
        return False

    for attempt in range(1, retries + 1):
        try:
            with open(photo_path, "rb") as f:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=caption,
                    parse_mode=parse_mode,
                    read_timeout=180.0,
                    write_timeout=180.0,
                    connect_timeout=60.0
                )
            return True
        except Exception as ex:
            print(f"[Send Photo Retry {attempt}/{retries}]: {ex}")
            if attempt < retries:
                await asyncio.sleep(2 * attempt)
            else:
                return False
    return False


# ========================================================================================
# PIPELINE EXECUTION WORKER (RUNS IN SEPARATE THREAD)
# ========================================================================================
def execute_pipeline_sync(
    pdf_path: str,
    io_name: str,
    notice_no: int,
    fir_details: Optional[Dict[str, Any]] = None,
    notice_date: Optional[str] = None,
    notice_type: str = "both",
    max_layer: int = 5,
    email_settings: Optional[Dict[str, Any]] = None,
    io_rank: Optional[str] = None,
    io_mobile: Optional[str] = None,
    same_notice_number: bool = True
) -> Dict[str, Any]:
    """Synchronous pipeline runner wrapped with COM apartment initialization."""
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception as e:
        print(f"[COM Init Warning]: {e}")

    try:
        # Strictly preserve the passed IO details, fallback to parse_io_details only if missing
        if not io_rank or not io_mobile:
            parsed = parse_io_details(io_name)
            io_name = io_name or parsed["name"]
            io_rank = io_rank or parsed["rank"]
            io_mobile = io_mobile or parsed["mobile"]

        io_override = {
            "name": io_name,
            "rank": io_rank or "INVESTIGATING OFFICER",
            "belt_no": io_mobile or "",
            "mobile": io_mobile or ""
        }

        active_fir = fir_details if (fir_details and fir_details.get("is_fir")) else {"is_fir": False}
        n_date = notice_date or datetime.datetime.now().strftime("%d/%m/%Y")

        # Run unified master pipeline
        res = agent.run_case_pipeline(
            case_file_or_target=pdf_path,
            fir_details=active_fir,
            io_override=io_override,
            start_notice_no=notice_no,
            notice_date_override=n_date,
            sign_mode="both",
            notice_type=notice_type,
            max_layer=max_layer,
            same_notice_number=same_notice_number,
            suspect_mobiles=session.get("suspect_mobiles", []),
            imei_list=session.get("imei_list", [])
        )

        ack = res.get("acknowledgement_no") or res.get("case_meta", {}).get("acknowledgement_no", "")
        case_dir = res.get("case_dir")

        if not case_dir or not os.path.exists(case_dir):
            if active_fir.get("is_fir") and active_fir.get("fir_no"):
                clean_fir = re.sub(r'[^a-zA-Z0-9_-]', '_', str(active_fir.get("fir_no")))
                case_dir = os.path.join(agent.output_dir, f"FIR_{clean_fir}")
            elif ack:
                case_dir = os.path.join(agent.output_dir, f"Case_{ack}")

            if not case_dir or not os.path.exists(case_dir):
                all_cases = glob.glob(os.path.join(agent.output_dir, "Case_*")) + glob.glob(os.path.join(agent.output_dir, "FIR_*"))
                if all_cases:
                    case_dir = max(all_cases, key=os.path.getmtime)

        # Optional Email Automation
        email_summary = None
        email_cfg = email_settings or {"send_email": False}
        if email_cfg.get("send_email") and case_dir:
            target_email = email_cfg.get("target_email") or "rajendra.28082016@delhipolice.gov.in"
            try:
                from email_dispatch_agent import EmailDispatchAgent
                email_agent = EmailDispatchAgent()
                email_agent.config.setdefault("forwarding_target", {})["nic_email"] = target_email
                email_results = email_agent.dispatch_case_notices(
                    case_dir_or_ack=case_dir,
                    provider="gmail",
                    mode="forward_to_nic",
                    dry_run=False
                )
                success_count = sum(1 for r in email_results if 'SUCCESS' in r.get('status', ''))
                email_summary = {
                    "success": True,
                    "target_email": target_email,
                    "count": success_count,
                    "total": len(email_results)
                }
            except Exception as em_err:
                print(f"[Email Dispatch Error]: {em_err}")
                email_summary = {"success": False, "error": str(em_err)}

        return {
            "success": True,
            "case_dir": case_dir,
            "ack": ack,
            "active_fir": active_fir,
            "io_name": io_name,
            "notice_no": notice_no,
            "notice_date": n_date,
            "notice_type": notice_type,
            "max_layer": max_layer,
            "email_summary": email_summary
        }

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[Pipeline Execution Error]:\n{tb}")
        frames = traceback.extract_tb(sys.exc_info()[2])
        loc = f"{os.path.basename(frames[-1].filename)}:{frames[-1].lineno}" if frames else "unknown"
        return {"success": False, "error": f"{e} (at {loc})\n\n{tb}"}
    finally:
        try:
            import pythoncom
            pythoncom.CoUninitialize()
        except Exception:
            pass


# ========================================================================================
# REUSABLE PROMPT FUNCTIONS (INLINE UI & BUTTONS)
# ========================================================================================
async def prompt_fir_date_selection(target_ui, session: Dict[str, Any]):
    """Prompts for FIR Date."""
    session["state"] = "awaiting_fir_date"
    today_str = datetime.datetime.now().strftime("%d/%m/%Y")
    fir_no = session.get("fir_details", {}).get("fir_no", "N/A")

    msg_text = (
        f"✅ दर्ज e-FIR नंबर: *{fir_no}*\n\n"
        f"📅 *[सवाल 2b] e-FIR दर्ज होने की तारीख (FIR Date):*\n"
        f"कृपया e-FIR की तारीख चुनें या सीधे टाइप करें (उदा. `DD/MM/YYYY`):"
    )
    keyboard = [
        [InlineKeyboardButton(f"📅 आज की तारीख ({today_str}) [Default]", callback_data="firdate:today")],
        [InlineKeyboardButton("✏️ अन्य तारीख टाइप करें", callback_data="firdate:custom")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if hasattr(target_ui, "edit_message_text"):
        await target_ui.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await target_ui.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def prompt_notice_date_selection(target_ui, session: Dict[str, Any], prefix_msg: str = ""):
    """Prompts for Notice Date."""
    session["state"] = "awaiting_notice_date"
    today_str = datetime.datetime.now().strftime("%d/%m/%Y")

    is_fir = session.get("fir_details", {}).get("is_fir", False)
    ref_info = f"e-FIR No. {session.get('fir_details', {}).get('fir_no', '')} (Dated: {session.get('fir_date', today_str)})" if is_fir else f"NCRP Ack {session.get('ack_no', '')} (राशि < ₹1 लाख)"

    msg_text = (
        f"{prefix_msg}"
        f"✅ केस संदर्भ: *{ref_info}*\n\n"
        f"📅 *[सवाल 3] नोटिस जारी करने की तारीख (Notice Date):*\n"
        f"बैंक व ATM नोटिसों पर कौन-सी तारीख अंकित करनी है?"
    )
    keyboard = [
        [InlineKeyboardButton(f"📅 आज की तारीख ({today_str}) [Default]", callback_data="noticedate:today")],
        [InlineKeyboardButton("✏️ अन्य तारीख टाइप करें", callback_data="noticedate:custom")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if hasattr(target_ui, "edit_message_text"):
        await target_ui.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await target_ui.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def prompt_notice_type_selection(target_ui, session: Dict[str, Any]):
    """Prompts for Notice Type (Bank Notices, ATM CCTV, or Both)."""
    session["state"] = "awaiting_notice_type"
    n_date = session.get("notice_date", datetime.datetime.now().strftime("%d/%m/%Y"))

    msg_text = (
        f"✅ चयनित नोटिस तारीख: *{n_date}*\n\n"
        f"📑 *[सवाल 4] नोटिस का प्रकार चुनें (Notice Type):*\n"
        f"आप किस प्रकार के कानूनी नोटिस तैयार करना चाहते हैं?"
    )
    keyboard = [
        [InlineKeyboardButton("🏦 बैंक नोटिस (Bank Notices Only) [Default]", callback_data="ntype:bank")],
        [InlineKeyboardButton("📑 दोनों (Bank व ATM CCTV दोनों)", callback_data="ntype:both")],
        [InlineKeyboardButton("🏧 केवल ATM CCTV नोटिस (ATM Only)", callback_data="ntype:atm")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if hasattr(target_ui, "edit_message_text"):
        await target_ui.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await target_ui.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def prompt_layer_selection(target_ui, session: Dict[str, Any]):
    """Prompts for Bank Notice Layer Range."""
    session["state"] = "awaiting_layer"
    ntype_str = "बैंक व ATM दोनों" if session.get("notice_type") == "both" else "केवल बैंक नोटिस"

    msg_text = (
        f"✅ चयनित नोटिस प्रकार: *{ntype_str}*\n\n"
        f"🌐 *[सवाल 5] बैंक नोटिस लेयर रेंज (Layer Limit):*\n"
        f"बैंक नोटिस किस लेयर तक तैयार करने हैं?\n"
        f"(अनुशंसित: सभी लेयर्स के नोटिस तैयार करने के लिए पहला बटन दबाएं):"
    )
    keyboard = [
        [InlineKeyboardButton("🌐 सभी लेयर्स के नोटिस (Layers 1-5+) [Default]", callback_data="layer:all")],
        [InlineKeyboardButton("1️⃣ केवल 1st Layer (Entry Mules)", callback_data="layer:1")],
        [InlineKeyboardButton("2️⃣ 2nd Layer तक (Layers 1-2)", callback_data="layer:2")],
        [InlineKeyboardButton("3️⃣ 3rd Layer तक (Layers 1-3)", callback_data="layer:3")],
        [InlineKeyboardButton("4️⃣ 4th Layer तक (Layers 1-4)", callback_data="layer:4")],
        [InlineKeyboardButton("5️⃣ 5th Layer तक (Layers 1-5)", callback_data="layer:5")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if hasattr(target_ui, "edit_message_text"):
        await target_ui.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await target_ui.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def prompt_notice_scheme_selection(target_ui, session: Dict[str, Any]):
    """[Step 6a] Prompts user whether to keep the SAME notice number for all notices or use sequential numbers."""
    session["state"] = "awaiting_notice_scheme"
    max_l = session.get("max_layer", 999)
    layer_desc = "सभी लेयर्स (1-5+)" if max_l >= 900 else f"लेयर {max_l} तक"

    msg_text = (
        f"✅ चयनित लेयर रेंज: *{layer_desc}*\n\n"
        f"🔢 *[सवाल 6a] नोटिस नंबरिंग का तरीका चुनें:*\n\n"
        f"क्या केस/FIR के सभी नोटिसों पर एक ही नोटिस नंबर रखना है या प्रत्येक नोटिस पर अलग-अलग क्रमिक नंबर (5744, 5745...) लगाना है?"
    )
    keyboard = [
        [InlineKeyboardButton("📋 सभी नोटिसों पर एक ही नंबर रखें (Same Notice Number) [Default]", callback_data="nscheme:same")],
        [InlineKeyboardButton("🔢 प्रत्येक नोटिस पर अलग-अलग क्रमिक नंबर लगाएं (Sequential Numbers)", callback_data="nscheme:seq")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if hasattr(target_ui, "edit_message_text"):
        await target_ui.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await target_ui.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def prompt_notice_no_selection(target_ui, session: Dict[str, Any]):
    """[Step 6b] Prompts for Starting Notice Number."""
    session["state"] = "awaiting_notice_no"
    same_no = session.get("same_notice_number", True)
    scheme_desc = "सभी नोटिसों पर एक ही नंबर" if same_no else "अलग-अलग क्रमिक नंबर"

    msg_text = (
        f"✅ चयनित नंबरिंग मोड: *{scheme_desc}*\n\n"
        f"🔢 *[सवाल 6b] शुरुआती नोटिस नंबर (Starting Notice No.):*\n"
        f"क्या आप डिफ़ॉल्ट नोटिस नंबर *5744* रखना चाहते हैं?"
    )
    keyboard = [
        [InlineKeyboardButton("🔢 डिफ़ॉल्ट नोटिस नंबर (5744) [Default]", callback_data="noticeno:5744")],
        [InlineKeyboardButton("✏️ अन्य नोटिस नंबर टाइप करें", callback_data="noticeno:custom")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if hasattr(target_ui, "edit_message_text"):
        await target_ui.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await target_ui.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def prompt_email_selection(target_ui, session: Dict[str, Any]):
    """Prompts for Email Automation."""
    session["state"] = "awaiting_email_choice"
    notice_no = session.get("notice_no", 5744)
    msg_text = (
        f"✅ चयनित नोटिस नंबर: *{notice_no}*\n\n"
        f"📧 *[सवाल 7] नोटिस ईमेल बैकअप:*\n"
        f"क्या सभी तैयार नोटिस आपके आधिकारिक ईमेल पर प्राप्त करने हैं?\n"
        f"🔒 *सुरक्षा नियम:* नोटिस सीधे किसी बैंक को नहीं भेजे जाते हैं, केवल जांच अधिकारी के अधिकृत ईमेल पर भेजे जाते हैं।"
    )
    keyboard = [
        [InlineKeyboardButton("📧 डिफ़ॉल्ट ईमेल (rajendra.28082016@delhipolice.gov.in) [Default]", callback_data="email:default")],
        [InlineKeyboardButton("✉️ अन्य ईमेल पता दर्ज करें", callback_data="email:custom")],
        [InlineKeyboardButton("⏭️ ईमेल न भेजें (केवल Telegram पर चाहिए)", callback_data="email:skip")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if hasattr(target_ui, "edit_message_text"):
        await target_ui.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await target_ui.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def prompt_cdr_selection(target_ui, session: Dict[str, Any]):
    """[Step 8] Prompts whether IO wants to generate a Telecom CDR Requisition Letter for Suspect Mobile/IMEI."""
    session["state"] = "awaiting_cdr_choice"
    msg_text = (
        "📱 *[सवाल 8] दूरसंचार CDR/CAF/SDR मांग पत्र (Telecom CDR Letter):*\n\n"
        "क्या आप इस केस में किसी संदिग्ध (Suspect) मोबाइल नंबर या IMEI का वैधानिक CDR पत्र तैयार करना चाहते हैं?\n\n"
        "🔒 *नियम:* यदि शिकायत में कोई संदिग्ध नंबर नहीं है या केवल परिवादी (Complainant) का नंबर है, "
        "तो परिवादी के नंबर से CDR पत्र नहीं बनाया जाएगा। संदिग्ध नंबर न होने पर कृपया *'छोड़ें'* चुनें।"
    )
    keyboard = [
        [InlineKeyboardButton("⏭️ छोड़ें (कोई CDR पत्र न बनाएं) [Default]", callback_data="cdr:skip")],
        [InlineKeyboardButton("📱 सस्पेक्ट मोबाइल/IMEI व Source दर्ज करें", callback_data="cdr:add")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if hasattr(target_ui, "edit_message_text"):
        await target_ui.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await target_ui.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


# ========================================================================================
# TELEGRAM BOT COMMAND HANDLERS
# ========================================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start command with rich welcome card & inline quick actions."""
    if not await check_access(update):
        return
    user = update.effective_user
    chat_id = update.effective_chat.id
    reset_user_session(chat_id)

    welcome_text = (
        f"👮‍♂️ *नमस्ते {user.first_name if user else 'सर'}!*\n"
        f"*PDF TO BANK NOTICE FOR CYBER INVESTIGATION*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 *आपकी Telegram Chat ID*: `{chat_id}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 *यह बॉट कैसे कार्य करता है?*\n"
        f"1️⃣ आप यहाँ सीधे अपनी *NCRP शिकायत की PDF फ़ाइल* भेजें (Document के रूप में)।\n"
        f"2️⃣ बॉट तुरंत पीड़ित, फ्रॉड राशि, और सभी बैंक लेयर्स (Layer 1-5) का विश्लेषण करेगा।\n"
        f"3️⃣ आपसे IO, FIR, नोटिस तारीख, नोटिस का प्रकार (Bank/ATM) व लेयर रेंज पूछेगा।\n"
        f"4️⃣ इसके बाद सभी *बैंक नोटिस (PDF व DOCX)*, *ATM CCTV मांग पत्र*, *कंबाइंड मांग पत्र*, *बैंक खाता व IFSC शाखा पता निर्देशिका (DOCX)*, *व्हाइट बैकग्राउंड 3D फ्लोचार्ट* और *ऑल-इन-वन ZIP बंडल* सीधे आपके Telegram पर भेज देगा!\n\n"
        f"👉 *शुरू करने के लिए अभी अपनी NCRP शिकायत PDF यहाँ भेजें*, या नीचे दिए गए बटन पर टैप करें:"
    )

    keyboard = [
        [InlineKeyboardButton("📁 टेस्ट हेतु सैंपल केस लोड करें", callback_data="act:load_sample")],
        [InlineKeyboardButton("ℹ️ सहायता व निर्देश (/help)", callback_data="act:help")],
        [InlineKeyboardButton("🔄 सेशन रीसेट करें (/reset)", callback_data="act:reset")]
    ]
    if is_admin(chat_id):
        keyboard.append([InlineKeyboardButton("👥 यूजर मैनेजमेंट (User Management)", callback_data="admin:menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /help command."""
    if not await check_access(update):
        return
    help_text = (
        "📖 *PDF TO BANK NOTICE FOR CYBER INVESTIGATION - उपयोग निर्देश*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 *कमांड्स:*\n"
        "• `/start` - बॉट को पुनः प्रारंभ करें\n"
        "• `/sample` - सिस्टम में पहले से मौजूद सैंपल NCRP PDF प्रोसेस करें\n"
        "• `/status` - सिस्टम व इंजन स्थिति जांचें\n"
        "• `/resend` - नवीनतम केस की सभी फाइल्स पुनः Telegram पर भेजें\n"
        "• `/reset` - वर्तमान प्रक्रिया को रद्द करें\n\n"
        "🔹 *दस्तावेज़ कैसे भेजें?*\n"
        "Telegram के 'Attach File' (Paperclip 📎 आइकन) पर क्लिक करके NCRP शिकायत की PDF फ़ाइल चुनें।\n\n"
        "🔹 *आउटपुट में क्या-क्या मिलेगा?*\n"
        "• 📊 शुद्ध सफेद बैकग्राउंड वाला फोरेंसिक 3D मनी ट्रेल फ्लोचार्ट (Photo)\n"
        "• 📄 कंबाइंड बैंक नोटिस (Combine Notice DOCX)\n"
        "• 🏢 बैंक खाता व IFSC शाखा भौतिक पता निर्देशिका (Layer-wise DOCX)\n"
        "• 📑 सभी बैंकों के नोटिस (धारा 94 BNSS - हस्ताक्षरित PDF व DOCX)\n"
        "• 🏧 ATM CCTV फुटेज मांग पत्र (DOCX)\n"
        "• 📦 सम्पूर्ण केस बंडल (ZIP फ़ाइल - एक क्लिक में सब डाउनलोड)\n"
        "• 📧 वैकल्पिक: NIC ईमेल पर सीधा प्रेषण\n"
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /reset command."""
    if not await check_access(update):
        return
    chat_id = update.effective_chat.id
    reset_user_session(chat_id)
    msg = "🔄 सेशन रीसेट कर दिया गया है। नया केस शुरू करने के लिए कृपया अपनी NCRP शिकायत PDF फ़ाइल भेजें।"
    if update.message:
        await update.message.reply_text(msg)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg)



# ========================================================================================
# USER MANAGEMENT & ADMIN COMMANDS
# ========================================================================================
async def show_admin_dashboard(target_msg, chat_id: int):
    """Displays the Admin User Management Dashboard."""
    cfg = load_telegram_credentials()
    allowed = cfg.get("allowed_chat_ids", [])
    admins = cfg.get("admin_chat_ids", [8160205906])

    text = (
        f"👥 *यूजर मैनेजमेंट डैशबोर्ड (User Management)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *कुल अधिकृत यूज़र्स*: {len(allowed)}\n"
        f"• *सुपर एडमिन Chat ID*: `{admins[0] if admins else chat_id}`\n\n"
        f"यहाँ से आप नए यूज़र्स को बॉट उपयोग की अनुमति दे सकते हैं अथवा हटा सकते हैं:\n\n"
        f"👉 `/adduser <chat_id>` - नया यूजर जोड़ें\n"
        f"👉 `/removeuser <chat_id>` - यूजर हटाएं\n"
        f"👉 `/users` - सभी अधिकृत यूज़र्स की सूची देखें\n"
    )
    keyboard = [
        [InlineKeyboardButton("➕ नया यूजर जोड़ें (Add User)", callback_data="admin:add_user")],
        [InlineKeyboardButton("📋 अधिकृत यूज़र्स देखें (List Users)", callback_data="admin:list_users")],
        [InlineKeyboardButton("➖ यूजर हटाएं (Remove User)", callback_data="admin:remove_menu")],
        [InlineKeyboardButton("🔙 मुख्य मेनू (Main Menu)", callback_data="act:reset")]
    ]
    if hasattr(target_msg, "edit_text"):
        try:
            await target_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
            return
        except Exception:
            pass
    await target_msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /admin command."""
    chat_id = update.effective_chat.id
    if not is_admin(chat_id):
        await update.message.reply_text("⛔ यह कमांड केवल बॉट एडमिनिस्ट्रेटर हेतु उपलब्ध है।")
        return
    await show_admin_dashboard(update.message, chat_id)


async def adduser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to authorize a new user: /adduser <chat_id>"""
    chat_id = update.effective_chat.id
    if not is_admin(chat_id):
        await update.message.reply_text("⛔ यह कमांड केवल बॉट एडमिन हेतु उपलब्ध है।")
        return

    args = context.args
    if not args:
        session = get_user_session(chat_id)
        session["state"] = "awaiting_new_user_id"
        await update.message.reply_text(
            "📝 *कृपया जिस यूजर को जोड़ना है उसकी Telegram Chat ID भेजें:*\n\n"
            "उदा: `987654321`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    raw_id = args[0].strip()
    m = re.search(r'(\d{6,15})', raw_id)
    if not m:
        await update.message.reply_text("⚠️ कृपया एक वैध अंकीय Chat ID दर्ज करें (उदा. `/adduser 987654321`)।")
        return

    target_id = int(m.group(1))
    added = add_allowed_chat_id(target_id)
    if added:
        await update.message.reply_text(
            f"✅ *यूजर अधिकृत कर दिया गया है!*\n"
            f"• *Chat ID*: `{target_id}`\n\n"
            f"अब यह यूजर बॉट पर NCRP शिकायत PDF भेजकर सभी नोटिस तैयार कर सकता है।",
            parse_mode=ParseMode.MARKDOWN
        )
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="🎉 *बधाई हो!* एडमिन द्वारा आपकी Chat ID अधिकृत कर दी गई है।\n"
                     "शुरू करने के लिए /start भेजें या सीधे अपनी NCRP शिकायत की PDF अपलोड करें!",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass
    else:
        await update.message.reply_text(f"ℹ️ Chat ID `{target_id}` पहले से ही अधिकृत सूची में मौजूद है।")


async def removeuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to revoke access: /removeuser <chat_id>"""
    chat_id = update.effective_chat.id
    if not is_admin(chat_id):
        await update.message.reply_text("⛔ यह कमांड केवल बॉट एडमिन हेतु उपलब्ध है।")
        return

    args = context.args
    if not args:
        await update.message.reply_text("⚠️ उपयोग: `/removeuser <chat_id>`\nउदा: `/removeuser 987654321`", parse_mode=ParseMode.MARKDOWN)
        return

    raw_id = args[0].strip()
    m = re.search(r'(\d{6,15})', raw_id)
    if not m:
        await update.message.reply_text("⚠️ कृपया वैध अंकीय Chat ID दर्ज करें।")
        return

    target_id = int(m.group(1))
    if target_id == 8160205906 or is_admin(target_id):
        await update.message.reply_text("⚠️ सुपर एडमिन को हटाया नहीं जा सकता।")
        return

    removed = remove_allowed_chat_id(target_id)
    if removed:
        await update.message.reply_text(f"✅ Chat ID `{target_id}` की पहुंच सफलतापूर्वक निरस्त (Revoked) कर दी गई है।", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(f"ℹ️ Chat ID `{target_id}` अधिकृत सूची में नहीं मिली।")


async def listusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to list all authorized users: /users"""
    chat_id = update.effective_chat.id
    if not is_admin(chat_id):
        await update.message.reply_text("⛔ यह कमांड केवल बॉट एडमिन हेतु उपलब्ध है।")
        return

    cfg = load_telegram_credentials()
    allowed = cfg.get("allowed_chat_ids", [])
    admins = {str(a).strip() for a in cfg.get("admin_chat_ids", [8160205906])}

    if not allowed:
        await update.message.reply_text("ℹ️ वर्तमान में कोई अलग यूजर आईडी नहीं है (ओपन एक्सेस)।")
        return

    rows = []
    for idx, uid in enumerate(allowed, 1):
        s_uid = str(uid).strip()
        role = "👑 सुपर एडमिन" if s_uid in admins else "👮‍♂️ अधिकृत यूजर"
        rows.append(f"*{idx}.* `{s_uid}` - {role}")

    msg = (
        f"📋 *अधिकृत यूज़र्स की सूची (Authorized Users)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
        "\n".join(rows) +
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *कुल संख्या*: {len(allowed)}\n\n"
        f"किसी यूजर को हटाने हेतु: `/removeuser <chat_id>`"
    )
    if update.message:
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /status command."""
    if not await check_access(update):
        return
    output_cases = glob.glob(os.path.join(agent.output_dir, "Case_*")) + glob.glob(os.path.join(agent.output_dir, "FIR_*"))
    status_text = (
        "🟢 *NCRP Unified Master Agent: सक्रिय (ONLINE)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *वर्जन*: 3.6.0 (White Flowchart & Custom Filters)\n"
        f"• *आधार निर्देशिका*: `{BASE_DIR}`\n"
        f"• *कुल प्रोसेस्ड केस*: {len(output_cases)}\n"
        f"• *कानूनी ढांचा*: धारा 94/106 BNSS 2023, IT Act 66D\n"
        f"• *समय*: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
    )
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)


async def sheet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /sheet command to display Mule Account Database status and Google Sheet URL."""
    if not await check_access(update):
        return
    
    from google_sheets_sync import get_sheets_config
    cfg = get_sheets_config()
    
    excel_path = os.path.join(BASE_DIR, "output", "Mule_Account_Master_Database.xlsx")
    total_records = 0
    if os.path.exists(excel_path):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(excel_path, read_only=True)
            ws = wb.active
            total_records = max(0, ws.max_row - 1)
        except Exception:
            pass

    webhook_url = cfg.get("apps_script_webhook_url", "").strip()
    sheet_url = cfg.get("google_sheet_id_or_url", "").strip()
    sa_path = os.path.join(BASE_DIR, cfg.get("google_service_account_file", "config/google_service_account.json"))
    has_sa = os.path.exists(sa_path)

    sync_status = "⚠️ लोकल मास्टर एक्सेल में सक्रिय (Google Sheet लिंक पेंडिंग)"
    if webhook_url:
        sync_status = "✅ Google Apps Script Webhook से लाइव कनेक्टेड"
    elif has_sa:
        sync_status = "✅ Google Service Account से कनेक्टेड"

    txt = (
        "📊 *म्यूल अकाउंट मास्टर डेटाबेस (Mule Account Database)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔹 *डेटाबेस स्थिति*: {sync_status}\n"
        f"🔹 *कुल दर्ज सस्पेक्ट खाते*: `{total_records}` खाते\n"
        f"🔹 *लोकल मास्टर एक्सेल*: `output/Mule_Account_Master_Database.xlsx`\n"
        f"🔹 *स्प्रेडशीट नाम*: `{cfg.get('spreadsheet_name')}`\n"
    )
    if webhook_url:
        txt += f"🔹 *Apps Script URL*: `{webhook_url[:45]}...`\n"
    if sheet_url:
        txt += f"🔹 *Google Sheet*: [यहाँ क्लिक करें]({sheet_url})\n"

    txt += (
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *कमांड विकल्प:*\n"
        "• `/muleexcel` — वर्तमान मास्टर एक्सेल फाइल डाउनलोड करें\n"
        "• `/setsheeturl <URL>` — Apps Script Webhook URL सेट करें\n"
    )

    keyboard = [
        [InlineKeyboardButton("📥 मास्टर एक्सेल डाउनलोड करें (/muleexcel)", callback_data="act:get_mule_excel")],
        [InlineKeyboardButton("🔄 रिफ्रेश स्थिति (/sheet)", callback_data="act:refresh_sheet")]
    ]
    if update.message:
        await update.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))


async def muleexcel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends current Mule_Account_Master_Database.xlsx to user."""
    if not await check_access(update):
        return
    chat_id = update.effective_chat.id
    excel_path = os.path.join(BASE_DIR, "output", "Mule_Account_Master_Database.xlsx")
    if not os.path.exists(excel_path):
        await update.message.reply_text("⚠️ मास्टर एक्सेल डेटाबेस अभी नहीं बना है। पहले कोई NCRP कंप्लेंट PDF प्रोसेस करें।")
        return

    await update.message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
    await safe_send_document(
        bot=context.bot,
        chat_id=chat_id,
        file_path=excel_path,
        caption="📊 *म्यूल अकाउंट मास्टर डेटाबेस (Mule Account Master Database)*\nसभी लेयर्स के सस्पेक्ट खातों का सेंट्रलाइज्ड रिकॉर्ड।",
        parse_mode=ParseMode.MARKDOWN
    )


async def setsheeturl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets Google Apps Script Webhook URL: /setsheeturl <url>"""
    if not await check_access(update):
        return
    chat_id = update.effective_chat.id
    if not is_admin(chat_id):
        await update.message.reply_text("⛔ केवल एडमिन ही Google Sheet URL कॉन्फ़िगर कर सकते हैं।")
        return

    args = context.args
    if not args:
        await update.message.reply_text("⚠️ कृपया Webhook URL भी दें:\nउदाहरण: `/setsheeturl https://script.google.com/macros/s/.../exec`", parse_mode=ParseMode.MARKDOWN)
        return

    new_url = args[0].strip()
    from google_sheets_sync import get_sheets_config, DEFAULT_CONFIG_PATH, COLUMNS_HEADER
    cfg = get_sheets_config()
    cfg["apps_script_webhook_url"] = new_url
    with open(DEFAULT_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    # Immediately push existing excel records to the Google Sheet
    synced_info = ""
    excel_path = os.path.join(BASE_DIR, "output", "Mule_Account_Master_Database.xlsx")
    if os.path.exists(excel_path):
        try:
            import openpyxl, requests
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            ws = wb.active
            rows = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and any(row):
                    rows.append([str(c if c is not None else '') for c in row])
            if rows:
                payload = {
                    "action": "append_rows",
                    "spreadsheet_name": cfg.get("spreadsheet_name", "Mule Account Database"),
                    "sheet_tab": cfg.get("sheet_tab_name", "Mule_Accounts"),
                    "headers": COLUMNS_HEADER,
                    "rows": rows
                }
                resp = requests.post(new_url, json=payload, timeout=15)
                if resp.status_code in [200, 201]:
                    synced_info = f"\n🚀 *मौजूदा {len(rows)} सस्पेक्ट खाते तुरंत Google Sheet में भेज दिए गए हैं!*"
        except Exception as se:
            synced_info = f"\n(नोट: {se})"

    await update.message.reply_text(f"✅ *Google Apps Script Webhook URL सफलतापूर्वक सेट हो गया!*\n`{new_url}`{synced_info}\n\nअब प्रत्येक केस का डेटा सीधे इस Google Sheet में लाइव अपडेट होगा।", parse_mode=ParseMode.MARKDOWN)


async def sample_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes existing sample NCRP complaint for testing."""
    if not await check_access(update):
        return
    chat_id = update.effective_chat.id
    sample_pdf = os.path.join(agent.input_dir, "AcknowledgementNo_30810260096039.pdf")
    if not os.path.exists(sample_pdf):
        await update.message.reply_text("⚠️ सैंपल फ़ाइल उपलब्ध नहीं है। कृपया अपनी NCRP शिकायत PDF फ़ाइल भेजें।")
        return

    await process_received_pdf(sample_pdf, update.effective_message, chat_id)


async def resend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resends all files from the latest generated case directly to Telegram."""
    if not await check_access(update):
        return
    chat_id = update.effective_chat.id
    all_cases = glob.glob(os.path.join(agent.output_dir, "Case_*")) + glob.glob(os.path.join(agent.output_dir, "FIR_*"))
    if not all_cases:
        msg = "⚠️ कोई प्रोसेस्ड केस उपलब्ध नहीं है। कृपया पहले अपनी PDF भेजें।"
        if update.message:
            await update.message.reply_text(msg)
        elif update.callback_query:
            await update.callback_query.message.reply_text(msg)
        return

    latest_case = max(all_cases, key=os.path.getmtime)
    cname = os.path.basename(latest_case)
    status_txt = f"📦 नवीनतम केस (`{cname}`) की सभी फाइल्स Telegram पर भेजी जा रही हैं..."
    if update.message:
        await update.message.reply_text(status_txt, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.message.reply_text(status_txt, parse_mode=ParseMode.MARKDOWN)

    await dispatch_case_files(
        bot=context.bot,
        chat_id=chat_id,
        case_dir=latest_case,
        notice_no=5744,
        io_name="INVESTIGATING OFFICER",
        ref_str=cname,
        notice_type="both"
    )


# ========================================================================================
# DOCUMENT / PDF HANDLER
# ========================================================================================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Politely guides users when an image/photo is sent instead of a PDF."""
    if not await check_access(update):
        return
    msg = update.effective_message
    if msg:
        await msg.reply_text(
            "⚠️ *आपने फोटो/इमेज भेजी है!*\n\n"
            "NCRP साइबर पोर्टल की शिकायत केवल *PDF फ़ाइल (Document)* के रूप में मान्य होती है।\n"
            "कृपया अपनी NCRP शिकायत को फ़ाइल (File / Document) के रूप में भेजें ताकि उसका मनी ट्रेल विश्लेषण किया जा सके।",
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives and processes any newly uploaded document / PDF with automatic session reset."""
    if not await check_access(update):
        return
    message = update.effective_message
    if not message:
        return
    doc = message.document
    chat_id = update.effective_chat.id

    if not doc:
        await message.reply_text("⚠️ कृपया एक वैध NCRP शिकायत PDF फ़ाइल भेजें।")
        return

    fname = doc.file_name or "complaint.pdf"
    is_pdf = (
        fname.lower().endswith(".pdf") or
        doc.mime_type in ["application/pdf", "application/x-pdf", "binary/octet-stream", "application/octet-stream"] or
        "acknowledgement" in fname.lower() or
        "ncrp" in fname.lower()
    )
    if not is_pdf:
        await message.reply_text(
            f"⚠️ *अमान्य फ़ाइल प्रकार:* `{fname}`\n\n"
            f"केवल NCRP शिकायत की PDF फ़ाइलें ही स्वीकार्य हैं। कृपया `.pdf` फ़ाइल भेजें।",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    status_msg = await message.reply_text(
        f"📥 *नई NCRP शिकायत फ़ाइल प्राप्त हो रही है:*\n`{fname}`\n\n"
        f"कृपया कुछ क्षण प्रतीक्षा करें, डाउनलोडिंग जारी है...",
        parse_mode=ParseMode.MARKDOWN
    )

    ts = int(time.time())
    clean_fname = re.sub(r'[^a-zA-Z0-9_.-]', '_', fname)
    if not clean_fname.lower().endswith(".pdf"):
        clean_fname += ".pdf"

    os.makedirs(agent.input_dir, exist_ok=True)
    local_pdf_path = os.path.join(agent.input_dir, f"TG_{chat_id}_{ts}_{clean_fname}")

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(local_pdf_path)
        print(f"[Telegram Download] Saved {local_pdf_path} ({os.path.getsize(local_pdf_path)} bytes)")
    except Exception as e:
        try:
            await status_msg.edit_text(f"❌ फ़ाइल डाउनलोड करने में त्रुटि आई: {e}")
        except Exception:
            await message.reply_text(f"❌ फ़ाइल डाउनलोड करने में त्रुटि आई: {e}")
        return

    try:
        await status_msg.delete()
    except Exception:
        pass

    await process_received_pdf(local_pdf_path, message, chat_id, context)


async def process_received_pdf(pdf_path: str, message, chat_id: int, context: Optional[ContextTypes.DEFAULT_TYPE] = None):
    """Parses PDF and presents the interactive questionnaire with Inline Buttons."""
    session = get_user_session(chat_id)
    # CRITICAL: Always reset session state cleanly whenever a new file arrives!
    session.clear()
    session["chat_id"] = chat_id
    session["pdf_path"] = pdf_path
    session["state"] = "awaiting_io"
    session["io_name"] = None
    session["io_rank"] = None
    session["io_mobile"] = None

    prog_msg = await message.reply_text("⏳ *NCRP शिकायत का विश्लेषण व मनी ट्रेल एक्सट्रैक्शन जारी है...*", parse_mode=ParseMode.MARKDOWN)

    temp_dir = os.path.join(agent.output_dir, "_tg_temp")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        loop = asyncio.get_running_loop()
        ctx = await loop.run_in_executor(EXECUTOR, agent.parse_ncrp_pdf, pdf_path, temp_dir)
    except Exception as parse_err:
        import traceback
        tb = traceback.format_exc()
        print(f"[PDF Parse Error]:\n{tb}")
        try:
            await prog_msg.edit_text(
                f"❌ *NCRP PDF विश्लेषण में त्रुटि आई:*\n`{str(parse_err)[:350]}`\n\n"
                f"कृपया सुनिश्चित करें कि यह NCRP पोर्टल की वैध शिकायत PDF है।",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await message.reply_text(f"❌ NCRP PDF विश्लेषण में त्रुटि आई: {parse_err}")
        session["state"] = "idle"
        return

    meta = ctx.get("case_meta", {})
    comp = ctx.get("complainant", {})
    fin = ctx.get("financial_summary", {})
    ack_no = meta.get("acknowledgement_no", "N/A")
    session["ack_no"] = ack_no
    session["alleged_amount"] = fin.get("alleged_amount") or fin.get("defrauded_amount") or "0"

    try:
        await prog_msg.delete()
    except Exception:
        pass

    amt_val = extract_amount_value(session["alleged_amount"])
    summary_card = (
        f"📋 *NCRP शिकायत प्राप्त व विश्लेषित!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Ack No.*: `{ack_no}`\n"
        f"• *पीड़ित का नाम*: {comp.get('name', 'N/A')}\n"
        f"• *ठगी की राशि*: Rs. {fin.get('alleged_amount', '0')}\n"
        f"• *होल्ड राशि*: Rs. {fin.get('total_lien_amount', '0')}\n"
        f"• *केस वर्गीकरण*: {'⚖️ e-FIR (राशि ₹1 लाख या अधिक)' if amt_val > 99999 else '📄 NCRP शिकायत (राशि < ₹1 लाख)'}\n"
        f"• *बैंक लेयर्स*: 1 से 5+ (CCTV व चेक पूर्णतः विश्लेषित)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *[सवाल 1] कृपया जांच अधिकारी (IO) का चयन करें:*"
    )

    keyboard = [
        [InlineKeyboardButton("👮‍♂️ SI ARVIND KUMAR [Default]", callback_data="io:arvind")],
        [InlineKeyboardButton("👮‍♀️ SI RENU", callback_data="io:renu")],
        [InlineKeyboardButton("👮‍♂️ HC RAJENDRA", callback_data="io:rajendra")],
        [InlineKeyboardButton("✏️ अन्य IO का नाम टाइप करें (Type Custom IO)", callback_data="io:custom")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(summary_card, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


# ========================================================================================
# CALLBACK QUERY HANDLER (INLINE BUTTONS)
# ========================================================================================
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles 1-tap interactive inline button clicks."""
    if not await check_access(update):
        return
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = update.effective_chat.id
    session = get_user_session(chat_id)

    if data == "act:get_mule_excel":
        excel_path = os.path.join(BASE_DIR, "output", "Mule_Account_Master_Database.xlsx")
        if os.path.exists(excel_path):
            await safe_send_document(
                bot=query.bot,
                chat_id=chat_id,
                file_path=excel_path,
                caption="📊 *म्यूल अकाउंट मास्टर डेटाबेस (Mule Account Master Database)*",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.message.reply_text("⚠️ मास्टर एक्सेल फाइल अभी मौजूद नहीं है।")
        return

    if data == "act:refresh_sheet":
        await sheet_command(update, context)
        return

    # Admin & User Access Callbacks
    if data.startswith("req_access:"):
        req_chat_id = int(data.split(":")[1])
        u_name = query.from_user.full_name or "जांच अधिकारी"
        u_user = f"@{query.from_user.username}" if query.from_user.username else "कोई यूजरनेम नहीं"
        await query.edit_message_text(
            "⏳ *आपका पहुंच अनुरोध एडमिन को प्रेषित कर दिया गया है!*\n\n"
            "जैसे ही एडमिन द्वारा स्वीकृति प्राप्त होगी, आपको स्वतः सूचित कर दिया जाएगा।",
            parse_mode=ParseMode.MARKDOWN
        )
        cfg = load_telegram_credentials()
        admins = cfg.get("admin_chat_ids", [8160205906])
        admin_req_text = (
            f"🔔 *नए यूजर द्वारा एक्सेस का अनुरोध (Access Request)*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *नाम*: {u_name}\n"
            f"• *यूजरनेम*: {u_user}\n"
            f"• *Chat ID*: `{req_chat_id}`\n\n"
            f"क्या आप इस यूजर को बॉट उपयोग की अनुमति देना चाहते हैं?"
        )
        admin_kb = [
            [
                InlineKeyboardButton("✅ अनुमति दें (Approve)", callback_data=f"admin_appr:{req_chat_id}"),
                InlineKeyboardButton("❌ अस्वीकार करें (Reject)", callback_data=f"admin_rejc:{req_chat_id}")
            ]
        ]
        for a_id in admins:
            try:
                await context.bot.send_message(
                    chat_id=int(a_id),
                    text=admin_req_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(admin_kb)
                )
            except Exception as notify_err:
                print(f"[Admin Notify Error]: {notify_err}")
        return

    elif data.startswith("admin_appr:"):
        target_id = int(data.split(":")[1])
        add_allowed_chat_id(target_id)
        await query.edit_message_text(f"✅ *Chat ID `{target_id}` को सफलतापूर्वक अधिकृत कर दिया गया है!*", parse_mode=ParseMode.MARKDOWN)
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="🎉 *बधाई हो!* एडमिन द्वारा आपकी Chat ID अधिकृत कर दी गई है।\n\n"
                     "शुरू करने के लिए /start भेजें या सीधे अपनी NCRP शिकायत की PDF भेजें!",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass
        return

    elif data.startswith("admin_rejc:"):
        target_id = int(data.split(":")[1])
        await query.edit_message_text(f"❌ *Chat ID `{target_id}` का अनुरोध अस्वीकार कर दिया गया।*", parse_mode=ParseMode.MARKDOWN)
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="🚫 क्षमा करें, आपका अनुरोध एडमिन द्वारा अस्वीकार कर दिया गया है।",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            pass
        return

    elif data == "admin:menu":
        if not is_admin(chat_id):
            await query.answer("एडमिन अधिकार आवश्यक हैं", show_alert=True)
            return
        await show_admin_dashboard(query.message, chat_id)
        return

    elif data == "admin:add_user":
        if not is_admin(chat_id):
            await query.answer("एडमिन अधिकार आवश्यक हैं", show_alert=True)
            return
        session["state"] = "awaiting_new_user_id"
        await query.message.reply_text(
            "📝 *कृपया जिस यूजर को जोड़ना है उसकी Telegram Chat ID टाइप करके भेजें:*\n\n"
            "उदा: `987654321`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    elif data == "admin:list_users":
        if not is_admin(chat_id):
            await query.answer("एडमिन अधिकार आवश्यक हैं", show_alert=True)
            return
        await listusers_command(update, context)
        return

    elif data == "admin:remove_menu":
        if not is_admin(chat_id):
            await query.answer("एडमिन अधिकार आवश्यक हैं", show_alert=True)
            return
        cfg = load_telegram_credentials()
        allowed = cfg.get("allowed_chat_ids", [])
        admins = {str(a).strip() for a in cfg.get("admin_chat_ids", [8160205906])}
        removable = [u for u in allowed if str(u).strip() not in admins]
        if not removable:
            await query.message.reply_text("ℹ️ हटाने योग्य कोई अन्य यूजर उपलब्ध नहीं है।")
            return
        kb = []
        for u in removable:
            kb.append([InlineKeyboardButton(f"❌ Chat ID {u} हटाएं", callback_data=f"admin_rm:{u}")])
        kb.append([InlineKeyboardButton("🔙 वापस", callback_data="admin:menu")])
        await query.message.reply_text("🗑️ *किस यूजर की पहुंच हटाना चाहते हैं?*", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))
        return

    elif data.startswith("admin_rm:"):
        if not is_admin(chat_id):
            await query.answer("एडमिन अधिकार आवश्यक हैं", show_alert=True)
            return
        target_id = int(data.split(":")[1])
        remove_allowed_chat_id(target_id)
        await query.edit_message_text(f"✅ *Chat ID `{target_id}` को अधिकृत सूची से हटा दिया गया है।*", parse_mode=ParseMode.MARKDOWN)
        return

    # Actions from menu
    if data == "act:load_sample":
        sample_pdf = os.path.join(agent.input_dir, "AcknowledgementNo_30810260096039.pdf")
        if os.path.exists(sample_pdf):
            await process_received_pdf(sample_pdf, query.message, chat_id)
        else:
            await query.message.reply_text("⚠️ सैंपल फ़ाइल उपलब्ध नहीं है। कृपया अपनी PDF भेजें।")
        return

    elif data == "act:help":
        await help_command(update, context)
        return

    elif data == "act:reset":
        await reset_command(update, context)
        return

    elif data == "act:resend":
        await resend_command(update, context)
        return

    # Step 1: IO Selection
    if data.startswith("io:"):
        choice = data.split(":")[1]
        if choice == "custom":
            session["state"] = "awaiting_custom_io"
            await query.edit_message_text(
                "📝 *कृपया जांच अधिकारी (IO) का नाम टाइप करके भेजें:*\n\n"
                "उदा: `SI VIKAS SHARMA` या `HC DINESH` (मोबाइल नंबर भी लिख सकते हैं)",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        elif choice == "renu":
            parsed = parse_io_details("2")
        elif choice == "rajendra":
            parsed = parse_io_details("3")
        else:
            parsed = parse_io_details("1")

        session["io_name"] = parsed["name"]
        session["io_rank"] = parsed["rank"]
        session["io_mobile"] = parsed["mobile"]

        amt_val = extract_amount_value(session.get("alleged_amount", 0))
        if amt_val <= 99999:
            # Under ₹1 Lakh (<= 99,999) -> Strictly NCRP Complaint, NO e-FIR prompt
            session["fir_details"] = {"is_fir": False}
            formatted_amt = f"{amt_val:,.2f}"
            notify_text = (
                f"✅ चयनित जांच अधिकारी: *{parsed['name']}* ({parsed['rank']})\n"
                f"ℹ️ ठगी की राशि: *Rs. {formatted_amt}* (₹1 लाख से कम)\n"
                f"👉 नियम अनुसार इसे *NCRP शिकायत (धारा 94 BNSS)* के रूप में प्रोसेस किया जा रहा है। (e-FIR की आवश्यकता नहीं है)\n\n"
            )
            await prompt_notice_date_selection(query, session, prefix_msg=notify_text)
            return
        else:
            # ₹1 Lakh or more (> 99,999) -> Strictly e-FIR, prompt for FIR Number & Date
            session["state"] = "awaiting_fir_number"
            formatted_amt = f"{amt_val:,.2f}"
            prompt_fir_no = (
                f"✅ चयनित जांच अधिकारी: *{parsed['name']}* ({parsed['rank']})\n"
                f"⚖️ ठगी की राशि: *Rs. {formatted_amt}* (₹1 लाख या अधिक)\n"
                f"👉 नियम अनुसार इसे *e-FIR* के रूप में ट्रीट किया जा रहा है।\n\n"
                f"📝 *[सवाल 2a] कृपया e-FIR नंबर दर्ज करें:*\n"
                f"उदा. `45/2026` या `282/2026` लिखकर भेजें:"
            )
            await query.edit_message_text(prompt_fir_no, parse_mode=ParseMode.MARKDOWN)
            return

    # Step 2: FIR Selection
    if data.startswith("fir:"):
        choice = data.split(":")[1]
        if choice == "registered":
            session["state"] = "awaiting_fir_number"
            prompt_fir_no = (
                "📝 *कृपया FIR नंबर दर्ज करें:*\n\n"
                "उदा. `45/2026` या `282/2026` लिखकर मैसेज भेजें:"
            )
            await query.edit_message_text(prompt_fir_no, parse_mode=ParseMode.MARKDOWN)
            return
        else:
            session["fir_details"] = {"is_fir": False}
            # Directly move to Step 3: Notice Date Selection
            await prompt_notice_date_selection(query, session)
            return

    # Step 2b: FIR Date Selection
    if data.startswith("firdate:"):
        choice = data.split(":")[1]
        if choice == "today":
            today_str = datetime.datetime.now().strftime("%d/%m/%Y")
            session["fir_date"] = today_str
            if session.get("fir_details"):
                session["fir_details"]["fir_date"] = today_str
            await prompt_notice_date_selection(query, session)
            return
        else:
            session["state"] = "awaiting_fir_date_input"
            await query.edit_message_text("📝 *कृपया e-FIR दर्ज होने की तारीख (DD/MM/YYYY) लिखकर भेजें:*", parse_mode=ParseMode.MARKDOWN)
            return

    # Step 3: Notice Date Selection
    if data.startswith("noticedate:"):
        choice = data.split(":")[1]
        if choice == "today":
            today_str = datetime.datetime.now().strftime("%d/%m/%Y")
            session["notice_date"] = today_str
            await prompt_notice_type_selection(query, session)
            return
        else:
            session["state"] = "awaiting_notice_date_input"
            await query.edit_message_text("📝 *कृपया नोटिस जारी करने की तारीख (DD/MM/YYYY) लिखकर भेजें:*", parse_mode=ParseMode.MARKDOWN)
            return

    # Step 4: Notice Type Selection
    if data.startswith("ntype:"):
        ntype = data.split(":")[1]
        session["notice_type"] = ntype
        if ntype in ["both", "bank"]:
            await prompt_layer_selection(query, session)
        else:
            # For ATM only, skip layer selection and set max_layer=5
            session["max_layer"] = 5
            await prompt_notice_scheme_selection(query, session)
        return

    # Step 5: Layer Limit Selection
    if data.startswith("layer:"):
        val = data.split(":")[1]
        if val == "all":
            max_l = 999
        else:
            try:
                max_l = int(val)
            except:
                max_l = 5
        session["max_layer"] = max_l
        await prompt_notice_scheme_selection(query, session)
        return

    # Step 6a: Notice Number Scheme Selection
    if data.startswith("nscheme:"):
        choice = data.split(":")[1]
        session["same_notice_number"] = (choice == "same")
        await prompt_notice_no_selection(query, session)
        return

    # Step 6b: Notice Number Selection
    if data.startswith("noticeno:"):
        val = data.split(":")[1]
        if val == "custom":
            session["state"] = "awaiting_notice_no_input"
            await query.edit_message_text("📝 *कृपया इच्छित नोटिस नंबर लिखकर भेजें (उदा. 5745):*", parse_mode=ParseMode.MARKDOWN)
            return
        else:
            session["notice_no"] = int(val)
            await prompt_email_selection(query, session)
            return

    # Step 7: Email Selection
    if data.startswith("email:"):
        choice = data.split(":")[1]
        if choice == "custom":
            session["state"] = "awaiting_custom_email"
            await query.edit_message_text("📝 *कृपया गंतव्य ईमेल पता दर्ज करें (उदा. officer@delhipolice.gov.in):*", parse_mode=ParseMode.MARKDOWN)
            return
        elif choice == "skip":
            session["email_settings"] = {"send_email": False, "target_email": None}
            await prompt_cdr_selection(query.message, session)
            return
        else:
            session["email_settings"] = {"send_email": True, "target_email": "rajendra.28082016@delhipolice.gov.in"}
            await prompt_cdr_selection(query.message, session)
            return



    # Step 8: CDR Selection Callback
    if data.startswith("cdr:"):
        choice = data.split(":")[1]
        if choice == "add":
            session["state"] = "awaiting_cdr_input"
            req_msg = (
                "📝 *कृपया संदिग्ध (Suspect) का 10-अंकीय मोबाइल नंबर या 15-अंकीय IMEI तथा उसका स्रोत (Source) भेजें:*\n\n"
                "उदा: `9876543210, Complainant WhatsApp interaction`\n"
                "या: `861234567890123, Mobile used by suspect`\n\n"
                "*(नोट: एक से अधिक नंबर हों तो अलग-अलग पंक्तियों में लिखें, या रद्द करने हेतु `skip` भेजें)*"
            )
            await query.edit_message_text(req_msg, parse_mode=ParseMode.MARKDOWN)
            return
        else: # skip
            session["suspect_mobiles"] = []
            session["imei_list"] = []
            session["suspect_sources"] = {}
            await query.edit_message_text("⏭️ *सीडीआर पत्र छोड़ा गया (केवल बैंक नोटिस तैयार किए जाएंगे)।*", parse_mode=ParseMode.MARKDOWN)
            await trigger_execution_telegram(query.message, chat_id, session, context)
            return

# ========================================================================================
# TEXT MESSAGE HANDLER (FOR MANUAL TYPING & INPUTS)
# ========================================================================================
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text replies from user for current state or commands."""
    if not await check_access(update):
        return
    message = update.message
    text = (message.text or "").strip()
    chat_id = update.effective_chat.id
    session = get_user_session(chat_id)
    current_state = session.get("state", "idle")

    # Quick global commands by text
    if text.lower() in ["hi", "hello", "start", "shuru", "reset"]:
        await start_command(update, context)
        return

    # State: Awaiting new user ID for authorization
    if current_state == "awaiting_new_user_id":
        if not is_admin(chat_id):
            session["state"] = "idle"
            await message.reply_text("⛔ एडमिन अधिकार आवश्यक हैं।")
            return
        m = re.search(r'(\d{6,15})', text)
        if m:
            new_id = int(m.group(1))
            session["state"] = "idle"
            added = add_allowed_chat_id(new_id)
            if added:
                await message.reply_text(
                    f"✅ *सफलतापूर्वक अधिकृत (Authorized)!*\n\n"
                    f"• *Chat ID*: `{new_id}`\n\n"
                    f"यह यूजर अब बॉट पर NCRP शिकायत PDF भेजकर सभी नोटिस बना सकता है।",
                    parse_mode=ParseMode.MARKDOWN
                )
                try:
                    await context.bot.send_message(
                        chat_id=new_id,
                        text="🎉 *बधाई हो!* एडमिन द्वारा आपकी Chat ID अधिकृत कर दी गई है।\n\n"
                             "शुरू करने के लिए /start भेजें या सीधे अपनी NCRP शिकायत की PDF भेजें!",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception:
                    pass
            else:
                await message.reply_text(f"ℹ️ Chat ID `{new_id}` पहले से ही अधिकृत सूची में मौजूद है।", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text("⚠️ कृपया एक वैध अंकीय Chat ID दर्ज करें (उदा. `987654321`)।")
        return

    # State: Awaiting IO by typing or custom IO name
    if current_state in ["awaiting_io", "awaiting_custom_io"]:
        parsed = parse_io_details(text)
        session["io_name"] = parsed["name"]
        session["io_rank"] = parsed["rank"]
        session["io_mobile"] = parsed["mobile"]

        amt_val = extract_amount_value(session.get("alleged_amount", 0))
        if amt_val <= 99999:
            # Under ₹1 Lakh (<= 99,999) -> Strictly NCRP Complaint, NO e-FIR prompt
            session["fir_details"] = {"is_fir": False}
            formatted_amt = f"{amt_val:,.2f}"
            notify_text = (
                f"✅ चयनित जांच अधिकारी: *{parsed['name']}* ({parsed['rank']})\n"
                f"ℹ️ ठगी की राशि: *Rs. {formatted_amt}* (₹1 लाख से कम)\n"
                f"👉 नियम अनुसार इसे *NCRP शिकायत (धारा 94 BNSS)* के रूप में प्रोसेस किया जा रहा है। (e-FIR की आवश्यकता नहीं है)\n\n"
            )
            await prompt_notice_date_selection(message, session, prefix_msg=notify_text)
            return
        else:
            # ₹1 Lakh or more (> 99,999) -> Strictly e-FIR, prompt for FIR Number & Date
            session["state"] = "awaiting_fir_number"
            formatted_amt = f"{amt_val:,.2f}"
            prompt_fir_no = (
                f"✅ चयनित जांच अधिकारी: *{parsed['name']}* ({parsed['rank']})\n"
                f"⚖️ ठगी की राशि: *Rs. {formatted_amt}* (₹1 लाख या अधिक)\n"
                f"👉 नियम अनुसार इसे *e-FIR* के रूप में ट्रीट किया जा रहा है।\n\n"
                f"📝 *[सवाल 2a] कृपया e-FIR नंबर दर्ज करें:*\n"
                f"उदा. `45/2026` या `282/2026` लिखकर भेजें:"
            )
            await message.reply_text(prompt_fir_no, parse_mode=ParseMode.MARKDOWN)
            return

    # State: Awaiting FIR choice
    if current_state == "awaiting_fir_choice":
        if text.strip().lower() in ["2", "yes", "y", "fir", "haan"]:
            session["state"] = "awaiting_fir_number"
            await message.reply_text("📝 कृपया FIR नंबर दर्ज करें (उदा. `45/2026`):", parse_mode=ParseMode.MARKDOWN)
            return
        else:
            session["fir_details"] = {"is_fir": False}
            await prompt_notice_date_selection(message, session)
            return

    # State: Awaiting FIR Number
    if current_state == "awaiting_fir_number":
        fir_no_input = text.strip()
        today_str = datetime.datetime.now().strftime("%d/%m/%Y")
        session["fir_details"] = {
            "is_fir": True,
            "fir_no": fir_no_input,
            "fir_date": today_str,
            "fir_sections": "318(4) BNS",
            "police_station": "CYBER POLICE STATION NORTH DISTRICT"
        }
        await prompt_fir_date_selection(message, session)
        return

    # State: Awaiting FIR Date Input
    if current_state in ["awaiting_fir_date", "awaiting_fir_date_input"]:
        parsed_d = parse_date_input(text)
        session["fir_date"] = parsed_d
        if session.get("fir_details"):
            session["fir_details"]["fir_date"] = parsed_d
        await prompt_notice_date_selection(message, session)
        return

    # State: Awaiting Notice Date Input
    if current_state in ["awaiting_notice_date", "awaiting_notice_date_input"]:
        parsed_nd = parse_date_input(text)
        session["notice_date"] = parsed_nd
        await prompt_notice_type_selection(message, session)
        return

    # State: Awaiting Notice Type
    if current_state == "awaiting_notice_type":
        s = text.lower().strip()
        if "atm" in s or s == "3":
            session["notice_type"] = "atm"
            session["max_layer"] = 5
            await prompt_notice_no_selection(message, session)
        elif "bank" in s or s == "2":
            session["notice_type"] = "bank"
            await prompt_layer_selection(message, session)
        else:
            session["notice_type"] = "both"
            await prompt_layer_selection(message, session)
        return

    # State: Awaiting Layer
    if current_state == "awaiting_layer":
        s = text.lower().strip()
        if "all" in s or "sab" in s or "6" in s:
            session["max_layer"] = 999
        elif s in ["1", "2", "3", "4", "5"]:
            session["max_layer"] = int(s)
        else:
            session["max_layer"] = 5
        await prompt_notice_no_selection(message, session)
        return

    # State: Awaiting Notice Number
    if current_state in ["awaiting_notice_no", "awaiting_notice_no_input"]:
        notice_val = 5744
        if text.isdigit():
            notice_val = int(text)
        session["notice_no"] = notice_val
        await prompt_email_selection(message, session)
        return

    # State: Awaiting Email Choice
    if current_state == "awaiting_email_choice":
        if text.strip().lower() in ["3", "no", "n", "nahi", "skip"]:
            session["email_settings"] = {"send_email": False, "target_email": None}
            await prompt_cdr_selection(message, session)
            return
        elif text.strip().lower() in ["2", "custom", "other"]:
            session["state"] = "awaiting_custom_email"
            await message.reply_text("📝 कृपया गंतव्य ईमेल पता दर्ज करें:")
            return
        else:
            session["email_settings"] = {"send_email": True, "target_email": "rajendra.28082016@delhipolice.gov.in"}
            await prompt_cdr_selection(message, session)
            return

    # State: Awaiting Custom Email
    if current_state == "awaiting_custom_email":
        custom_mail = text.strip()
        if "@" in custom_mail and "." in custom_mail:
            session["email_settings"] = {"send_email": True, "target_email": custom_mail}
            await prompt_cdr_selection(message, session)
            return
        else:
            await message.reply_text("⚠️ अमान्य ईमेल पता! कृपया सही ईमेल दर्ज करें (उदा. officer@gmail.com):")
            return

    # State: Awaiting CDR Input
    if current_state == "awaiting_cdr_input":
        if text.strip().lower() in ["skip", "no", "nahi", "n", "cancel"]:
            session["suspect_mobiles"] = []
            session["imei_list"] = []
            session["suspect_sources"] = {}
            await message.reply_text("⏭️ *सीडीआर पत्र छोड़ा गया।*", parse_mode=ParseMode.MARKDOWN)
            await trigger_execution_telegram(message, chat_id, session, context)
            return

        mobiles = []
        imeis = []
        sources = {}

        lines = text.split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            parts = [p.strip() for p in line_str.replace(" - ", ",").replace("-", ",").split(",") if p.strip()]
            num_part = parts[0] if parts else ""
            src_part = parts[1] if len(parts) > 1 else "Provided by IO during investigation"

            m_mob = re.search(r'\b([6-9]\d{9})\b', num_part)
            m_imei = re.search(r'\b(\d{15})\b', num_part)

            if m_mob:
                m_num = m_mob.group(1)
                mobiles.append(m_num)
                sources[m_num] = src_part
            elif m_imei:
                im_num = m_imei.group(1)
                imeis.append(im_num)
                sources[im_num] = src_part
            elif len(num_part) >= 10:
                mobiles.append(num_part)
                sources[num_part] = src_part

        if not mobiles and not imeis:
            await message.reply_text("⚠️ कोई वैध 10-अंकीय मोबाइल नंबर या IMEI नहीं मिला! कृपया पुनः प्रयास करें या `skip` भेजें:")
            return

        session["suspect_mobiles"] = mobiles
        session["imei_list"] = imeis
        session["suspect_sources"] = sources
        await message.reply_text(f"✅ *सस्पेक्ट नंबर दर्ज:* {len(mobiles)} मोबाइल, {len(imeis)} IMEI\n🚀 अब केस पाइपलाइन प्रारंभ की जा रही है...", parse_mode=ParseMode.MARKDOWN)
        await trigger_execution_telegram(message, chat_id, session, context)
        return

    # Fallback default
    if session.get("pdf_path"):
        await message.reply_text("👮‍♂️ जांच जारी रखने के लिए कृपया ऊपर दिए गए विकल्पों में से चयन करें, या नया केस शुरू करने के लिए `/start` भेजें।")
    else:
        await message.reply_text("👮‍♂️ नमस्ते सर! NCRP साइबर अपराध अन्वेषण शुरू करने के लिए कृपया अपनी *NCRP शिकायत की PDF फ़ाइल* भेजें या `/sample` लिखकर भेजें।", parse_mode=ParseMode.MARKDOWN)


# ========================================================================================
# EXECUTION & TELEGRAM MEDIA DISPATCH
# ========================================================================================
async def trigger_execution_telegram(message, chat_id: int, session: Dict[str, Any], context: ContextTypes.DEFAULT_TYPE):
    """Executes the case pipeline in worker thread and streams all files to Telegram."""
    pdf_path = session.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        sample_pdf = os.path.join(agent.input_dir, "AcknowledgementNo_30810260096039.pdf")
        pdf_path = sample_pdf

    io_name = session.get("io_name") or "SI ARVIND KUMAR"
    io_rank = session.get("io_rank") or "SUB INSPECTOR"
    io_mobile = session.get("io_mobile") or "8750871987"
    notice_no = session.get("notice_no", 5744)
    fir_details = session.get("fir_details", {"is_fir": False})
    notice_date = session.get("notice_date", datetime.datetime.now().strftime("%d/%m/%Y"))
    notice_type = session.get("notice_type", "both")
    max_layer = session.get("max_layer", 999)
    email_settings = session.get("email_settings", {"send_email": False})

    session["state"] = "processing"

    ntype_label = "बैंक व ATM CCTV दोनों" if notice_type == "both" else ("केवल बैंक नोटिस" if notice_type == "bank" else "केवल ATM CCTV नोटिस")
    layer_label = "सभी लेयर्स (1-5+)" if max_layer >= 900 else f"लेयर {max_layer} तक"
    case_ref_label = f"Case FIR No. {fir_details['fir_no']} Dt: {fir_details.get('fir_date', notice_date)}" if fir_details.get("is_fir") else f"NCRP Ack {session.get('ack_no', '')}"

    start_banner = (
        f"🚀 *केस प्रोसेसिंग प्रारंभ हो चुकी है!* ⏳\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *जांच अधिकारी*: {io_name}\n"
        f"• *केस संदर्भ*: {case_ref_label}\n"
        f"• *नोटिस तारीख*: {notice_date}\n"
        f"• *नोटिस प्रकार*: {ntype_label}\n"
        f"• *लेयर रेंज*: {layer_label}\n"
        f"• *शुरुआती नोटिस*: #{notice_no}\n"
        f"• *ईमेल ऑटोमेशन*: {'सक्रिय (' + email_settings.get('target_email', '') + ')' if email_settings.get('send_email') else 'अक्रिय'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ *प्रक्रिया प्रगति:* मनी ट्रेल विश्लेषण, शुद्ध सफेद बैकग्राउंड 3D फ्लोचार्ट, धारा 94 BNSS नोटिस, कंबाइंड मांग पत्र तैयार किए जा रहे हैं...\n"
        f"कृपया *25-35 सेकंड* प्रतीक्षा करें..."
    )
    try:
        status_msg = await context.bot.send_message(chat_id=chat_id, text=start_banner, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        status_msg = await context.bot.send_message(chat_id=chat_id, text=start_banner.replace('*', ''))

    same_notice_no = session.get("same_notice_number", True)
    # Launch background executor
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(
        EXECUTOR,
        execute_pipeline_sync,
        pdf_path,
        io_name,
        notice_no,
        fir_details,
        notice_date,
        notice_type,
        max_layer,
        email_settings,
        io_rank,
        io_mobile,
        same_notice_no
    )

    if not res.get("success"):
        err = str(res.get("error", "Unknown error"))
        # Cleanly display error with traceback safely
        clean_err = err[:1500]
        try:
            await status_msg.edit_text(f"❌ *केस निष्पादन में त्रुटि आई:*\n```\n{clean_err}\n```", parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await status_msg.edit_text(f"❌ केस निष्पादन में त्रुटि आई:\n{clean_err}")
        session["state"] = "idle"
        return

    case_dir = res.get("case_dir")
    ack = res.get("ack", "")
    active_fir = res.get("active_fir", {})
    ref_str = f"FIR No. {active_fir['fir_no']}" if active_fir.get("is_fir") else f"ACK No. {ack}"
    safe_ref = ref_str.replace('_', ' ')

    try:
        await status_msg.edit_text(
            f"✅ *सफलतापूर्वक तैयार!* ({safe_ref})\n"
            f"कानूनी नोटिस (PDF व DOCX), व्हाइट बैकग्राउंड 3D फ्लोचार्ट और सम्पूर्ण ZIP बंडल आपके Telegram पर भेजे जा रहे हैं...",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        await context.bot.send_message(chat_id=chat_id, text=f"✅ सफलतापूर्वक तैयार! ({safe_ref})\nसभी फाइलें भेजी जा रही हैं...")

    bot = context.bot

    try:
        await dispatch_case_files(
            bot=context.bot,
            chat_id=chat_id,
            case_dir=case_dir,
            notice_no=notice_no,
            io_name=io_name,
            ref_str=ref_str,
            notice_type=notice_type,
            email_summary=res.get("email_summary")
        )
    finally:
        session["state"] = "idle"


async def dispatch_case_files(
    bot,
    chat_id: int,
    case_dir: str,
    notice_no: int,
    io_name: str,
    ref_str: str,
    notice_type: str = "both",
    email_summary: Optional[Dict[str, Any]] = None
):
    """
    Delivers all generated notices and files to Telegram safely.
    Strategy:
      1. Deliver Complete ZIP Archive FIRST (guarantees officer has 100% of files in 1 tap!).
      2. Deliver Combine Notice DOCX (if bank notices generated).
      3. Deliver White Background Forensic Money Trail Flowchart Photo.
      4. Deliver Individual Bank Notice PDFs (if bank notices generated) with safe retries & 1s delay.
      5. Deliver ATM CCTV Notices (if ATM requested).
      6. Deliver Completion Card.
    """
    safe_ref = ref_str.replace('_', ' ')
    sent_pdf_count = 0
    sent_atm_count = 0

    try:
        # 0. DELIVER COMPLETE CASE ZIP BUNDLE FIRST (All notices, diagrams, directories in 1 bundle)
        try:
            zip_file = create_case_zip_bundle(case_dir)
            if zip_file and os.path.exists(zip_file):
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
                await safe_send_document(
                    bot=bot,
                    chat_id=chat_id,
                    file_path=zip_file,
                    caption=f"📦 *संपूर्ण केस नोटिस बंडल (Complete Case Bundle ZIP)*\n• {safe_ref}\n• (सभी बैंक नोटिस DOCX व PDF, ATM CCTV नोटिस, कंबाइंड मांग पत्र व 3D फ्लोचार्ट)",
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(1.5)
        except Exception as ze:
            print(f"[ZIP Dispatch Error Non-fatal]: {ze}")

        # 1. DELIVER COMBINE NOTICE DOCX (If bank notices enabled)
        if notice_type in ["both", "bank"]:
            combine_candidates = (
                glob.glob(os.path.join(case_dir, "combine_notice", "*.docx")) or
                glob.glob(os.path.join(case_dir, "Notice_DOCX_Files", "Combine_Notice*.docx"))
            )
            if combine_candidates:
                combine_docx = combine_candidates[0]
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
                await safe_send_document(
                    bot=bot,
                    chat_id=chat_id,
                    file_path=combine_docx,
                    caption=f"📄 *कंबाइंड बैंक मांग पत्र (Combine Notice #{notice_no})*\nसभी लेयर्स के बैंकों हेतु एकीकृत वैधानिक मांग पत्र (DOCX)",
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(1.5)

        # 2. DELIVER LAYER-WISE IFSC BRANCH ADDRESS DIRECTORY DOCX (If bank notices enabled)
        ifsc_candidates = []
        if notice_type in ["both", "bank"]:
            ifsc_candidates = (
                glob.glob(os.path.join(case_dir, "Bank_Accounts_IFSC_Branch_Directory*.docx")) or
                glob.glob(os.path.join(case_dir, "Notice_DOCX_Files", "Bank_Accounts_IFSC_Branch_Directory*.docx"))
            )
            if ifsc_candidates:
                ifsc_docx = ifsc_candidates[0]
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
                await safe_send_document(
                    bot=bot,
                    chat_id=chat_id,
                    file_path=ifsc_docx,
                    caption="🏢 *बैंक खाता व IFSC शाखा भौतिक पता निर्देशिका (Layer-wise DOCX)*\nसभी लेयर्स के बैंक खातों के IFSC कोड एवं RBI API से सत्यापित बैंक शाखा का पूर्ण भौतिक पता (Branch Physical Address)।",
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(1.5)

        # 3. DELIVER WHITE FORENSIC MONEY TRAIL FLOWCHART PHOTO (Pure White Background & Deep Black Text)
        radar_imgs = (
            glob.glob(os.path.join(case_dir, "forensic_money_trail_3d*.png")) or
            glob.glob(os.path.join(case_dir, "forensic_money_trail_3d*.jpg"))
        )
        if radar_imgs:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
            await safe_send_photo(
                bot=bot,
                chat_id=chat_id,
                photo_path=radar_imgs[0],
                caption="📊 *फोरेंसिक मनी ट्रेल 3D फ्लोचार्ट (HD)*\n(शुद्ध सफेद बैकग्राउंड, बैंक लोगो, स्पष्ट ब्लैक फॉन्ट एवं API से सत्यापित बैंक शाखा का पता)",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1.5)

        # 3b. DELIVER 3D ANIMATED FLOWCHART GIF (Live Animated Pulse)
        anim_gifs = glob.glob(os.path.join(case_dir, "forensic_money_trail_3d*animated*.gif"))
        if anim_gifs:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
            await safe_send_document(
                bot=bot,
                chat_id=chat_id,
                file_path=anim_gifs[0],
                caption="🎬 *3D एनिमेटेड फोरेंसिक मनी ट्रेल (Animated GIF)*\n(लेयर्स में पैसों के 3D फ्लो व गति का लाइव एनिमेशन)",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1.5)

        # 3c. DELIVER 3D MOVABLE INTERACTIVE HTML VISUALIZER FILE
        html_candidates = glob.glob(os.path.join(case_dir, "money_trail_3d_visualizer*.html"))
        if html_candidates:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
            await safe_send_document(
                bot=bot,
                chat_id=chat_id,
                file_path=html_candidates[0],
                caption="🌐 *3D मूवेबल इंटरएक्टिव मनी ट्रेल विजुअलाइज़र (HTML File)*\n(इसे किसी भी ब्राउज़र में खोलकर नोड्स को 3D में मूव/ड्रैग व ज़ूम करें)",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1.5)

        # 3d. DELIVER FORENSIC MONEY TRAIL PRESENTATION DOCX (PPT-style for case/court file)
        ppt_candidates = (
            glob.glob(os.path.join(case_dir, 'Forensic_Money_Trail_Presentation*.docx')) or
            glob.glob(os.path.join(case_dir, 'Notice_DOCX_Files', 'Forensic_Money_Trail_Presentation*.docx'))
        )
        if ppt_candidates:
            ppt_docx = ppt_candidates[0]
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
            await safe_send_document(
                bot=bot,
                chat_id=chat_id,
                file_path=ppt_docx,
                caption='📑 *मनी ट्रेल प्रेजेंटेशन रिपोर्ट (PPT-Style Forensic Report DOCX)*\nकेस/कोर्ट फाइल में लगाने हेतु तैयार स्टेप-बाई-स्टेप मनी ट्रेल प्रेजेंटेशन (विक्टिम से फर्स्ट लेयर व आगे की लेयर्स का पूर्ण विवरण)।',
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1.5)

        # 4. DELIVER INDIVIDUAL BANK NOTICES ONE BY ONE (If bank notices enabled)
        if notice_type in ["both", "bank"]:
            pdf_dir = os.path.join(case_dir, "Notice_PDF_Files")
            docx_dir = os.path.join(case_dir, "Notice_DOCX_Files")
            bank_pdfs = []
            if os.path.isdir(pdf_dir):
                bank_pdfs = sorted([
                    os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir)
                    if f.endswith(".pdf") and not any(k in f.lower() for k in ["atm", "cctv", "combine"])
                ])
            if bank_pdfs:
                for idx, p in enumerate(bank_pdfs, 1):
                    bname = os.path.basename(p)
                    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
                    ok = await safe_send_document(
                        bot=bot,
                        chat_id=chat_id,
                        file_path=p,
                        caption=f"📑 [{idx}/{len(bank_pdfs)}] बैंक नोटिस (Sec 94 BNSS):\n`{bname}`",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    if ok:
                        sent_pdf_count += 1
                    await asyncio.sleep(1.5)
            elif os.path.isdir(docx_dir):
                bank_docxs = sorted([
                    os.path.join(docx_dir, f) for f in os.listdir(docx_dir)
                    if f.endswith(".docx") and f.startswith("Notice_") and not any(k in f.lower() for k in ["atm", "cctv", "combine"])
                ])
                for idx, doc in enumerate(bank_docxs, 1):
                    bname = os.path.basename(doc)
                    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
                    ok = await safe_send_document(
                        bot=bot,
                        chat_id=chat_id,
                        file_path=doc,
                        caption=f"📝 [{idx}/{len(bank_docxs)}] बैंक मांग पत्र (DOCX):\n`{bname}`",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    if ok:
                        sent_pdf_count += 1
                    await asyncio.sleep(1.5)

        # 5. DELIVER ATM CCTV NOTICES ONE BY ONE (If ATM requested)
        if notice_type in ["both", "atm"]:
            pdf_dir = os.path.join(case_dir, "Notice_PDF_Files")
            docx_dir = os.path.join(case_dir, "Notice_DOCX_Files")
            atm_files = []
            if os.path.isdir(pdf_dir):
                atm_files = sorted([
                    os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir)
                    if f.endswith(".pdf") and any(k in f.lower() for k in ["atm", "cctv"])
                ])
            if not atm_files and os.path.isdir(docx_dir):
                atm_files = sorted([
                    os.path.join(docx_dir, f) for f in os.listdir(docx_dir)
                    if f.endswith(".docx") and any(k in f.lower() for k in ["atm", "cctv"])
                ])
            for idx, atm in enumerate(atm_files, 1):
                bname = os.path.basename(atm)
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
                ok = await safe_send_document(
                    bot=bot,
                    chat_id=chat_id,
                    file_path=atm,
                    caption=f"🏧 [{idx}/{len(atm_files)}] ATM CCTV मांग पत्र:\n`{bname}`",
                    parse_mode=ParseMode.MARKDOWN
                )
                if ok:
                    sent_atm_count += 1
                await asyncio.sleep(1.5)

        # 6. DELIVER CASE DIARY & CDR ONLY IF FIR IS REGISTERED
        is_fir = "FIR" in ref_str.upper()
        if is_fir:
            cd_files = glob.glob(os.path.join(case_dir, "Case_Diaries", "*.docx"))
            for cd in cd_files:
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
                await safe_send_document(
                    bot=bot,
                    chat_id=chat_id,
                    file_path=cd,
                    caption=f"📖 पुलिस केस डायरी (Zimni No. 02): `{os.path.basename(cd)}`",
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(1.5)

            cdr_files = glob.glob(os.path.join(case_dir, "CDR_Notice", "*.*"))
            for cdr in cdr_files:
                if cdr.endswith((".pdf", ".docx")):
                    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
                    await safe_send_document(
                        bot=bot,
                        chat_id=chat_id,
                        file_path=cdr,
                        caption=f"📞 टेलिकॉम CDR रिक्विजिशन पत्र: `{os.path.basename(cdr)}`",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await asyncio.sleep(1.5)

        # 6. DELIVERY SUMMARY CARD
        email_str = "छोड़ा गया"
        if email_summary:
            if email_summary.get("success"):
                email_str = f"✅ {email_summary.get('count')}/{email_summary.get('total')} नोटिस प्रेषित ({email_summary.get('target_email')})"
            else:
                email_str = f"⚠️ विफल ({email_summary.get('error')})"

        safe_email = email_str.replace('_', ' ')
        summary_done = (
            f"🎉 *टेलीग्राम डिलीवरी संपन्न!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *केस संदर्भ*: {safe_ref}\n"
            f"• *जांच अधिकारी*: {io_name}\n"
            f"• *डिलीवरी मोड*: ✅ सभी नोटिस वन-बाई-वन Telegram पर प्रेषित\n"
            f"• *बैंक नोटिस (PDF)*: {sent_pdf_count} फाइल्स प्रेषित\n"
            f"• *ATM CCTV नोटिस*: {sent_atm_count} फाइल्स प्रेषित\n"
            f"• *IFSC शाखा पता निर्देशिका*: {'✅ 1 DOCX प्रेषित' if ifsc_candidates else 'उपलब्ध नहीं'}\n"
            f"• *फ्लोचार्ट*: 1 फोटो प्रेषित (Pure White Background)\n"
            f"• *ईमेल ऑटोमेशन*: {safe_email}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ *नया केस शुरू करने के लिए कभी भी नई NCRP शिकायत PDF भेजें या /start लिखें।*\n"
            f"*(यदि कभी कोई फाइल दोबारा चाहिए तो /resend लिखें)*"
        )
        keyboard = [
            [InlineKeyboardButton("📁 एक और केस शुरू करें (/start)", callback_data="act:reset")],
            [InlineKeyboardButton("📊 मास्टर एक्सेल डाउनलोड (/muleexcel)", callback_data="act:get_mule_excel")],
            [InlineKeyboardButton("🔄 इस केस की फाइल्स फिर भेजें (/resend)", callback_data="act:resend")]
        ]
        await bot.send_message(
            chat_id=chat_id,
            text=summary_done,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        await bot.send_message(chat_id=chat_id, text=f"⚠️ डिलीवरी के दौरान कुछ फाइल्स भेजने में समस्या: {e}\n(आप /resend लिखकर पुनः प्रयास कर सकते हैं)")


# ========================================================================================
# MAIN ENTRYPOINT
# ========================================================================================
def main():
    print("=" * 80)
    print("  PDF TO BANK NOTICE FOR CYBER INVESTIGATION - LIVE TELEGRAM BOT")
    print("=" * 80)

    cfg = load_telegram_credentials()
    token = cfg.get("bot_token", "").strip()

    # Prompt console if token not set
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("\n[!] Telegram Bot Token not found in config/telegram_credentials.json.")
        print("[*] Please get a bot token from @BotFather on Telegram (send /newbot).")
        try:
            token = input("Enter your Telegram Bot Token: ").strip()
            if token:
                save_telegram_token(token)
            else:
                print("[ERROR] Token cannot be empty. Exiting...")
                sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            sys.exit(1)

    print(f"\n[*] Starting Telegram Bot with token: {token[:8]}...{token[-4:] if len(token) > 12 else ''}")
    print("[*] Using Long Polling (No Webhook/Tunnel required).")
    print("[*] Bot is listening for incoming NCRP Complaint PDFs...\n")

    app = build_telegram_app(token)
    app.run_polling(drop_pending_updates=True)


def build_telegram_app(token: Optional[str] = None):
    """Factory to build and configure Telegram Application with all handlers."""
    cfg = load_telegram_credentials()
    tok = token or cfg.get("bot_token", "").strip()
    if not tok:
        raise ValueError("Telegram Bot Token is required!")

    request_config = HTTPXRequest(
        connection_pool_size=16,
        connect_timeout=60.0,
        read_timeout=180.0,
        write_timeout=180.0,
        media_write_timeout=180.0,
        pool_timeout=60.0
    )
    app = ApplicationBuilder().token(tok).request(request_config).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("sample", sample_command))
    app.add_handler(CommandHandler("resend", resend_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("adduser", adduser_command))
    app.add_handler(CommandHandler("removeuser", removeuser_command))
    app.add_handler(CommandHandler("users", listusers_command))
    app.add_handler(CommandHandler("listusers", listusers_command))
    app.add_handler(CommandHandler("sheet", sheet_command))
    app.add_handler(CommandHandler("muleexcel", muleexcel_command))
    app.add_handler(CommandHandler("setsheeturl", setsheeturl_command))

    # Documents (PDFs)
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Photos / Images (Guiding user)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Interactive Inline Buttons
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # Text inputs
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    return app


if __name__ == "__main__":
    main()
