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
     - Step 4 (Notice No): Starting notice number (Default: 5744 or custom).
     - Step 5 (Email Choice): [Default NIC] / [Custom Email] / [No Email (Telegram only)].
  3. Execution & Delivery:
     - Executes full case pipeline in worker thread with pythoncom CoInitialize.
     - Delivers Combine DOCX, 3D Chart Photo, ALL Individual Bank Notice PDFs,
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

    return cfg


def save_telegram_token(token: str):
    """Saves Telegram Bot Token to config."""
    cfg = load_telegram_credentials()
    cfg["bot_token"] = token.strip()
    os.makedirs(os.path.dirname(TG_CONFIG_FILE), exist_ok=True)
    with open(TG_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"[Config] Telegram bot token saved to {TG_CONFIG_FILE}")


def get_user_session(user_id: int) -> Dict[str, Any]:
    """Gets or initializes session state for a user."""
    if user_id not in USER_SESSIONS:
        USER_SESSIONS[user_id] = {
            "state": "idle",
            "pdf_path": None,
            "ack_no": None,
            "io_name": "SI ARVIND KUMAR",
            "fir_details": {"is_fir": False},
            "notice_no": 5744,
            "email_settings": {"send_email": False, "target_email": None}
        }
    return USER_SESSIONS[user_id]


def is_authorized(chat_id: int) -> bool:
    """
    Checks if a chat_id is allowed to interact with the bot.
    If 'allowed_chat_ids' is empty ([]), access is open to everyone.
    If list has IDs, only matching users/chats are permitted.
    """
    cfg = load_telegram_credentials()
    allowed = cfg.get("allowed_chat_ids", [])
    if not allowed:
        return True  # Open access when empty
    allowed_str_set = {str(item).strip() for item in allowed if str(item).strip()}
    return str(chat_id).strip() in allowed_str_set


async def check_access(update: Update) -> bool:
    """Verifies user authorization before processing any command, document or query."""
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
            f"पहुंच प्राप्त करने हेतु अपनी Chat ID को `config/telegram_credentials.json` में `allowed_chat_ids` सूची में जोड़ें:\n"
            f'```json\n"allowed_chat_ids": [{chat_id}]\n```'
        )
        if update.message:
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        elif update.callback_query:
            await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        print(f"[AUTH DENIED] Unauthorized access attempt from Chat ID: {chat_id}")
        return False
    return True


def reset_user_session(user_id: int):
    """Resets session for a user."""
    USER_SESSIONS[user_id] = {
        "state": "awaiting_pdf",
        "pdf_path": None,
        "ack_no": None,
        "io_name": "SI ARVIND KUMAR",
        "fir_details": {"is_fir": False},
        "notice_no": 5744,
        "email_settings": {"send_email": False, "target_email": None}
    }


def create_case_zip_bundle(case_dir: str) -> Optional[str]:
    """Creates a complete ZIP archive of all generated notices and files."""
    try:
        base_name = os.path.basename(case_dir)
        zip_path = os.path.join(case_dir, f"All_Notices_Bundle_{base_name}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(case_dir):
                for f in files:
                    if f.endswith(('.docx', '.pdf', '.png', '.xlsx')) and not f.endswith('.zip'):
                        fp = os.path.join(root, f)
                        rel_path = os.path.relpath(fp, case_dir)
                        zf.write(fp, rel_path)
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
    email_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Synchronous pipeline runner wrapped with COM apartment initialization."""
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception as e:
        print(f"[COM Init Warning]: {e}")

    try:
        # Resolve IO details
        io_mobile = "8750871987"
        io_rank = "SUB INSPECTOR"
        if "rajendra" in io_name.lower():
            io_rank = "HEAD CONSTABLE"
            io_mobile = "9818036472"
        elif "renu" in io_name.lower():
            io_rank = "SUB INSPECTOR"
            io_mobile = "9899959840"

        io_override = {
            "name": io_name,
            "rank": io_rank,
            "belt_no": io_mobile,
            "mobile": io_mobile
        }

        active_fir = fir_details if (fir_details and fir_details.get("is_fir")) else {"is_fir": False}

        # Run unified master pipeline
        res = agent.run_case_pipeline(
            case_file_or_target=pdf_path,
            fir_details=active_fir,
            io_override=io_override,
            start_notice_no=notice_no,
            notice_date_override=datetime.datetime.now().strftime("%d/%m/%Y"),
            sign_mode="both"
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
            "email_summary": email_summary
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    finally:
        try:
            import pythoncom
            pythoncom.CoUninitialize()
        except Exception:
            pass


# ========================================================================================
# TELEGRAM BOT HANDLERS
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
        f"3️⃣ आपसे IO, FIR और नोटिस नंबर के विकल्प पूछेगा।\n"
        f"4️⃣ इसके बाद सभी *17+ बैंक नोटिस (PDF व DOCX)*, *कंबाइंड मांग पत्र*, *3D मनी ट्रेल चार्ट* और *ऑल-इन-वन ZIP बंडल* सीधे आपके Telegram पर भेज देगा!\n\n"
        f"👉 *शुरू करने के लिए अभी अपनी NCRP शिकायत PDF यहाँ भेजें*, या नीचे दिए गए बटन पर टैप करें:"
    )

    keyboard = [
        [InlineKeyboardButton("📁 टेस्ट हेतु सैंपल केस लोड करें", callback_data="act:load_sample")],
        [InlineKeyboardButton("ℹ️ सहायता व निर्देश (/help)", callback_data="act:help")],
        [InlineKeyboardButton("🔄 सेशन रीसेट करें (/reset)", callback_data="act:reset")]
    ]
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
        "• `/reset` - वर्तमान प्रक्रिया को रद्द करें\n\n"
        "🔹 *दस्तावेज़ कैसे भेजें?*\n"
        "Telegram के 'Attach File' (Paperclip 📎 आइकन) पर क्लिक करके NCRP शिकायत की PDF फ़ाइल चुनें।\n\n"
        "🔹 *आउटपुट में क्या-क्या मिलेगा?*\n"
        "• 📄 कंबाइंड बैंक नोटिस (Combine Notice DOCX)\n"
        "• 📊 3D मनी ट्रेल विज़ुअल चार्ट (Photo)\n"
        "• 📑 सभी बैंकों के नोटिस (धारा 94 BNSS - हस्ताक्षरित PDF)\n"
        "• 🏧 ATM CCTV नोटिस (DOCX)\n"
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


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /status command."""
    if not await check_access(update):
        return
    output_cases = glob.glob(os.path.join(agent.output_dir, "Case_*")) + glob.glob(os.path.join(agent.output_dir, "FIR_*"))
    status_text = (
        "🟢 *NCRP Unified Master Agent: सक्रिय (ONLINE)*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *वर्जन*: 3.5.0 (Telegram Live Integration)\n"
        f"• *आधार निर्देशिका*: `{BASE_DIR}`\n"
        f"• *कुल प्रोसेस्ड केस*: {len(output_cases)}\n"
        f"• *कानूनी ढांचा*: धारा 94/106 BNSS 2023, IT Act 66D\n"
        f"• *समय*: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
    )
    await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)


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
        ref_str=cname
    )


# ========================================================================================
# DOCUMENT / PDF HANDLER
# ========================================================================================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives and processes uploaded document / PDF."""
    if not await check_access(update):
        return
    message = update.message
    doc = message.document
    chat_id = update.effective_chat.id

    if not doc:
        await message.reply_text("⚠️ कृपया एक वैध दस्तावेज़ (Document) अपलोड करें।")
        return

    fname = doc.file_name or "complaint.pdf"
    if not fname.lower().endswith(".pdf") and doc.mime_type != "application/pdf":
        await message.reply_text("⚠️ केवल PDF फ़ाइलें ही स्वीकार्य हैं। कृपया अपनी NCRP शिकायत की PDF फ़ाइल भेजें।")
        return

    # Send status
    status_msg = await message.reply_text(f"📥 फ़ाइल प्राप्त हो रही है: `{fname}`...\nकृपया कुछ क्षण प्रतीक्षा करें।", parse_mode=ParseMode.MARKDOWN)

    # Generate safe local file path
    ts = int(time.time())
    clean_fname = re.sub(r'[^a-zA-Z0-9_.-]', '_', fname)
    local_pdf_path = os.path.join(agent.input_dir, f"TG_{chat_id}_{ts}_{clean_fname}")

    try:
        tg_file = await doc.get_file()
        await tg_file.download_to_drive(local_pdf_path)
        print(f"[Telegram Download] Saved {local_pdf_path} ({os.path.getsize(local_pdf_path)} bytes)")
    except Exception as e:
        await status_msg.edit_text(f"❌ फ़ाइल डाउनलोड करने में त्रुटि: {e}")
        return

    await status_msg.delete()
    await process_received_pdf(local_pdf_path, message, chat_id)


async def process_received_pdf(pdf_path: str, message, chat_id: int):
    """Parses PDF and presents the 4-step interview card with Inline Buttons."""
    session = get_user_session(chat_id)
    session["pdf_path"] = pdf_path
    session["state"] = "awaiting_io"

    # Send typing / progress indicator
    prog_msg = await message.reply_text("⏳ *NCRP शिकायत का विश्लेषण व मनी ट्रेल एक्सट्रैक्शन जारी है...*", parse_mode=ParseMode.MARKDOWN)

    temp_dir = os.path.join(agent.output_dir, "_tg_temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Run parsing in executor
    loop = asyncio.get_running_loop()
    ctx = await loop.run_in_executor(EXECUTOR, agent.parse_ncrp_pdf, pdf_path, temp_dir)

    meta = ctx.get("case_meta", {})
    comp = ctx.get("complainant", {})
    fin = ctx.get("financial_summary", {})
    ack_no = meta.get("acknowledgement_no", "N/A")
    session["ack_no"] = ack_no

    await prog_msg.delete()

    summary_card = (
        f"📋 *NCRP शिकायत प्राप्त व विश्लेषित!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Ack No.*: `{ack_no}`\n"
        f"• *पीड़ित का नाम*: {comp.get('name', 'N/A')}\n"
        f"• *ठगी की राशि*: Rs. {fin.get('alleged_amount', '0')}\n"
        f"• *होल्ड राशि*: Rs. {fin.get('total_lien_amount', '0')}\n"
        f"• *बैंक लेयर्स*: 1 से 5 (CCTV व चेक पूर्णतः बहिष्कृत)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *[सवाल 1/4] कृपया जांच अधिकारी (IO) का चयन करें:*"
    )

    keyboard = [
        [InlineKeyboardButton("👮‍♂️ SI ARVIND KUMAR [Default]", callback_data="io:arvind")],
        [InlineKeyboardButton("👮‍♀️ SI RENU", callback_data="io:renu")],
        [InlineKeyboardButton("👮‍♂️ HC RAJENDRA", callback_data="io:rajendra")]
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
        if choice == "renu":
            io_name = "SI RENU"
        elif choice == "rajendra":
            io_name = "HC RAJENDRA"
        else:
            io_name = "SI ARVIND KUMAR"

        session["io_name"] = io_name
        session["state"] = "awaiting_fir_choice"

        prompt_fir = (
            f"✅ चयनित जांच अधिकारी: *{io_name}*\n\n"
            f"📌 *[सवाल 2/4] केस संदर्भ (Case Reference):*\n"
            f"क्या इस मामले में FIR दर्ज हो चुकी है?"
        )
        keyboard = [
            [InlineKeyboardButton("📄 केवल NCRP शिकायत (Sec 94 BNSS) [Default]", callback_data="fir:ncrp")],
            [InlineKeyboardButton("⚖️ दर्ज FIR (FIR नंबर दर्ज करें)", callback_data="fir:registered")]
        ]
        await query.edit_message_text(prompt_fir, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
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
            session["state"] = "awaiting_notice_no"
            prompt_notice_no = (
                "✅ केस संदर्भ: *NCRP शिकायत (Sec 94 BNSS)*\n\n"
                "📌 *[सवाल 3/4] नोटिस नंबर (Starting Notice No.):*\n"
                "क्या आप डिफ़ॉल्ट नोटिस नंबर *5744* रखना चाहते हैं?"
            )
            keyboard = [
                [InlineKeyboardButton("🔢 डिफ़ॉल्ट नोटिस नंबर (5744) [Default]", callback_data="noticeno:5744")],
                [InlineKeyboardButton("✏️ अन्य नोटिस नंबर टाइप करें", callback_data="noticeno:custom")]
            ]
            await query.edit_message_text(prompt_notice_no, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
            return

    # Step 3: Notice Number Selection
    if data.startswith("noticeno:"):
        val = data.split(":")[1]
        if val == "custom":
            session["state"] = "awaiting_notice_no_input"
            await query.edit_message_text("📝 *कृपया इच्छित नोटिस नंबर लिखकर भेजें (उदा. 5745):*", parse_mode=ParseMode.MARKDOWN)
            return
        else:
            session["notice_no"] = int(val)
            session["state"] = "awaiting_email_choice"
            await prompt_email_selection(query, session)
            return

    # Step 4: Email Selection
    if data.startswith("email:"):
        choice = data.split(":")[1]
        if choice == "custom":
            session["state"] = "awaiting_custom_email"
            await query.edit_message_text("📝 *कृपया गंतव्य ईमेल पता दर्ज करें (उदा. rajendra.28082016@delhipolice.gov.in या officer@gmail.com):*", parse_mode=ParseMode.MARKDOWN)
            return
        elif choice == "skip":
            session["email_settings"] = {"send_email": False, "target_email": None}
            await query.edit_message_text("ℹ️ *ईमेल ऑटोमेशन छोड़ा गया (केवल Telegram पर नोटिस प्राप्त होंगे)।*", parse_mode=ParseMode.MARKDOWN)
            await trigger_execution_telegram(query.message, chat_id, session, context)
            return
        else:
            # Default NIC Email
            session["email_settings"] = {"send_email": True, "target_email": "rajendra.28082016@delhipolice.gov.in"}
            await query.edit_message_text("✅ *ईमेल ऑटोमेशन: rajendra.28082016@delhipolice.gov.in पर निर्धारित।*", parse_mode=ParseMode.MARKDOWN)
            await trigger_execution_telegram(query.message, chat_id, session, context)
            return


async def prompt_email_selection(target_ui, session: Dict[str, Any]):
    """Prompts Question 4 for email automation."""
    notice_no = session.get("notice_no", 5744)
    prompt_email = (
        f"✅ चयनित नोटिस नंबर: *{notice_no}*\n\n"
        f"📧 *[सवाल 4/4] बैंक नोटिस ईमेल ऑटोमेशन:*\n"
        f"क्या सभी बैंक नोटिस ईमेल द्वारा भी भेजने हैं?\n"
        f"(ईमेल बॉडी में DOCX का पूरा ड्राफ्ट रहेगा और साथ में हस्ताक्षरित PDF फ़ाइल अटैच होगी)"
    )
    keyboard = [
        [InlineKeyboardButton("📧 डिफ़ॉल्ट NIC ईमेल (Gmail द्वारा) [Default]", callback_data="email:default")],
        [InlineKeyboardButton("✉️ अन्य ईमेल पता दर्ज करें", callback_data="email:custom")],
        [InlineKeyboardButton("⏭️ ईमेल न भेजें (केवल Telegram पर चाहिए)", callback_data="email:skip")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if hasattr(target_ui, "edit_message_text"):
        await target_ui.edit_message_text(prompt_email, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await target_ui.reply_text(prompt_email, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


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

    # Reset or Start by text
    if text.lower() in ["hi", "hello", "start", "shuru", "reset"]:
        await start_command(update, context)
        return

    # State: Awaiting IO by typing 1, 2, 3
    if current_state == "awaiting_io":
        io_name = "SI ARVIND KUMAR"
        if text == "2" or "renu" in text.lower():
            io_name = "SI RENU"
        elif text == "3" or "rajendra" in text.lower():
            io_name = "HC RAJENDRA"

        session["io_name"] = io_name
        session["state"] = "awaiting_fir_choice"

        prompt_fir = (
            f"✅ चयनित जांच अधिकारी: *{io_name}*\n\n"
            f"📌 *[सवाल 2/4] क्या FIR दर्ज हो चुकी है?*\n"
            f"*[1]* केवल NCRP शिकायत है [Default]\n"
            f"*[2]* FIR दर्ज हो चुकी है\n\n"
            f"👉 1 या 2 लिखकर भेजें:"
        )
        keyboard = [
            [InlineKeyboardButton("📄 केवल NCRP शिकायत (Sec 94 BNSS) [Default]", callback_data="fir:ncrp")],
            [InlineKeyboardButton("⚖️ दर्ज FIR (FIR नंबर दर्ज करें)", callback_data="fir:registered")]
        ]
        await message.reply_text(prompt_fir, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # State: Awaiting FIR choice
    if current_state == "awaiting_fir_choice":
        if text.strip().lower() in ["2", "yes", "y", "fir", "haan"]:
            session["state"] = "awaiting_fir_number"
            await message.reply_text("📝 कृपया FIR नंबर दर्ज करें (उदा. `45/2026`):", parse_mode=ParseMode.MARKDOWN)
            return
        else:
            session["fir_details"] = {"is_fir": False}
            session["state"] = "awaiting_notice_no"
            prompt_notice_no = (
                "📌 *[सवाल 3/4] नोटिस नंबर:*\n"
                "डिफ़ॉल्ट नोटिस नंबर *5744* रखने के लिए *Y* भेजें या इच्छित नोटिस नंबर टाइप करें:"
            )
            keyboard = [
                [InlineKeyboardButton("🔢 डिफ़ॉल्ट नोटिस नंबर (5744) [Default]", callback_data="noticeno:5744")],
                [InlineKeyboardButton("✏️ अन्य नोटिस नंबर टाइप करें", callback_data="noticeno:custom")]
            ]
            await message.reply_text(prompt_notice_no, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
            return

    # State: Awaiting FIR Number
    if current_state == "awaiting_fir_number":
        fir_no_input = text.strip()
        session["fir_details"] = {
            "is_fir": True,
            "fir_no": fir_no_input,
            "fir_date": datetime.datetime.now().strftime("%d/%m/%Y"),
            "fir_sections": "318(4) BNS & 66D IT Act",
            "police_station": "CYBER POLICE STATION NORTH DISTRICT"
        }
        session["state"] = "awaiting_notice_no"
        prompt_notice_no = (
            f"✅ दर्ज FIR नंबर: *{fir_no_input}*\n\n"
            f"📌 *[सवाल 3/4] नोटिस नंबर:*\n"
            f"डिफ़ॉल्ट नोटिस नंबर *5744* रखने के लिए *Y* भेजें या इच्छित नोटिस नंबर टाइप करें:"
        )
        keyboard = [
            [InlineKeyboardButton("🔢 डिफ़ॉल्ट नोटिस नंबर (5744) [Default]", callback_data="noticeno:5744")],
            [InlineKeyboardButton("✏️ अन्य नोटिस नंबर टाइप करें", callback_data="noticeno:custom")]
        ]
        await message.reply_text(prompt_notice_no, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # State: Awaiting Notice Number
    if current_state in ["awaiting_notice_no", "awaiting_notice_no_input"]:
        notice_val = 5744
        if text.isdigit():
            notice_val = int(text)
        session["notice_no"] = notice_val
        session["state"] = "awaiting_email_choice"
        await prompt_email_selection(message, session)
        return

    # State: Awaiting Email Choice
    if current_state == "awaiting_email_choice":
        if text.strip().lower() in ["3", "no", "n", "nahi", "skip"]:
            session["email_settings"] = {"send_email": False, "target_email": None}
            await message.reply_text("ℹ️ *ईमेल ऑटोमेशन छोड़ा गया (केवल Telegram पर नोटिस प्राप्त होंगे)।*", parse_mode=ParseMode.MARKDOWN)
            await trigger_execution_telegram(message, chat_id, session, context)
            return
        elif text.strip().lower() in ["2", "custom", "other"]:
            session["state"] = "awaiting_custom_email"
            await message.reply_text("📝 कृपया गंतव्य ईमेल पता दर्ज करें:")
            return
        else:
            session["email_settings"] = {"send_email": True, "target_email": "rajendra.28082016@delhipolice.gov.in"}
            await trigger_execution_telegram(message, chat_id, session, context)
            return

    # State: Awaiting Custom Email
    if current_state == "awaiting_custom_email":
        custom_mail = text.strip()
        if "@" in custom_mail and "." in custom_mail:
            session["email_settings"] = {"send_email": True, "target_email": custom_mail}
            await trigger_execution_telegram(message, chat_id, session, context)
            return
        else:
            await message.reply_text("⚠️ अमान्य ईमेल पता! कृपया सही ईमेल दर्ज करें (उदा. officer@gmail.com):")
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

    io_name = session.get("io_name", "SI ARVIND KUMAR")
    notice_no = session.get("notice_no", 5744)
    fir_details = session.get("fir_details", {"is_fir": False})
    email_settings = session.get("email_settings", {"send_email": False})

    session["state"] = "processing"

    start_banner = (
        f"🚀 *केस प्रोसेसिंग प्रारंभ हो चुकी है!* ⏳\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• *जांच अधिकारी*: {io_name}\n"
        f"• *नोटिस नंबर*: {notice_no}\n"
        f"• *केस संदर्भ*: {'FIR No. ' + fir_details['fir_no'] if fir_details.get('is_fir') else 'NCRP Ack'}\n"
        f"• *ईमेल ऑटोमेशन*: {'सक्रिय (' + email_settings.get('target_email', '') + ')' if email_settings.get('send_email') else 'अक्रिय'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ *प्रक्रिया प्रगति:* मनी ट्रेल विश्लेषण, धारा 94 नोटिस (PDF व DOCX), कंबाइंड नोटिस, 3D विज़ुअल फ्लोचार्ट तैयार किए जा रहे हैं...\n"
        f"कृपया *25-35 सेकंड* प्रतीक्षा करें..."
    )
    status_msg = await message.reply_text(start_banner, parse_mode=ParseMode.MARKDOWN)

    # Launch background executor
    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(
        EXECUTOR,
        execute_pipeline_sync,
        pdf_path,
        io_name,
        notice_no,
        fir_details,
        email_settings
    )

    if not res.get("success"):
        err = res.get("error", "Unknown error")
        await status_msg.edit_text(f"❌ *केस निष्पादन में त्रुटि आई:*\n`{err}`", parse_mode=ParseMode.MARKDOWN)
        session["state"] = "idle"
        return

    case_dir = res.get("case_dir")
    ack = res.get("ack", "")
    active_fir = res.get("active_fir", {})
    ref_str = f"FIR No. {active_fir['fir_no']}" if active_fir.get("is_fir") else f"ACK No. {ack}"
    safe_ref = ref_str.replace('_', ' ')

    await status_msg.edit_text(
        f"✅ *सफलतापूर्वक तैयार!* ({safe_ref})\n"
        f"सभी बैंक व ATM नोटिस, कंबाइंड DOCX, 3D चार्ट और सम्पूर्ण ZIP बंडल आपके Telegram पर भेजे जा रहे हैं...",
        parse_mode=ParseMode.MARKDOWN
    )

    bot = context.bot

    try:
        await dispatch_case_files(
            bot=context.bot,
            chat_id=chat_id,
            case_dir=case_dir,
            notice_no=notice_no,
            io_name=io_name,
            ref_str=ref_str,
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
    email_summary: Optional[Dict[str, Any]] = None
):
    """
    Delivers all generated notices and files to Telegram safely.
    Strategy:
      1. Deliver Complete ZIP Archive FIRST (guarantees officer has 100% of files in 1 tap!).
      2. Deliver Combine Notice DOCX.
      3. Deliver 3D Forensic Money Trail Photo.
      4. Deliver Individual Bank Notice PDFs with safe retries (180s timeout) & 1s delay.
      5. Deliver ATM CCTV Notices with safe retries.
      6. Deliver Completion Card.
    """
    safe_ref = ref_str.replace('_', ' ')
    sent_pdf_count = 0
    sent_atm_count = 0

    try:
        # 1. DELIVER COMPLETE ZIP ARCHIVE FIRST (All files in 1 click!)
        zip_bundle = create_case_zip_bundle(case_dir)
        zip_sent = False
        if zip_bundle and os.path.exists(zip_bundle):
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
            zip_sent = await safe_send_document(
                bot=bot,
                chat_id=chat_id,
                file_path=zip_bundle,
                caption=f"📦 *सम्पूर्ण केस बंडल (All-in-One ZIP Archive)*\nसभी बैंक व ATM नोटिस, कंबाइंड DOCX, 3D चार्ट व केस डायरी - 1 क्लिक में डाउनलोड करें।",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1)

        # 2. DELIVER COMBINE NOTICE DOCX
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
                caption=f"📄 *कंबाइंड बैंक नोटिस (Combine Notice #{notice_no})*\nसभी बैंकों हेतु एकीकृत मांग पत्र (केवल DOCX प्रारूप)",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1)

        # 3. DELIVER 3D MONEY TRAIL FLOWCHART PHOTO
        radar_imgs = glob.glob(os.path.join(case_dir, "forensic_money_trail_3d*.png"))
        if radar_imgs:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_PHOTO)
            await safe_send_photo(
                bot=bot,
                chat_id=chat_id,
                photo_path=radar_imgs[0],
                caption="📊 *फोरेंसिक मनी ट्रेल 3D विज़ुअल चार्ट (लेयर 1 से 5)*",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1)

        # 4. DELIVER INDIVIDUAL BANK NOTICE PDFS (With retries & non-fatal handling)
        pdf_dir = os.path.join(case_dir, "Notice_PDF_Files")
        if os.path.isdir(pdf_dir):
            pdfs = sorted([os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.endswith(".pdf")])
            for idx, p in enumerate(pdfs, 1):
                bname = os.path.basename(p)
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
                ok = await safe_send_document(
                    bot=bot,
                    chat_id=chat_id,
                    file_path=p,
                    caption=f"📑 [{idx}/{len(pdfs)}] {bname}"
                )
                if ok:
                    sent_pdf_count += 1
                await asyncio.sleep(1)

        # 5. DELIVER ATM CCTV NOTICES (DOCX)
        docx_dir = os.path.join(case_dir, "Notice_DOCX_Files")
        if os.path.isdir(docx_dir):
            atm_notices = sorted(glob.glob(os.path.join(docx_dir, "Notice_CCTV_ATM*.docx")))
            for idx, atm in enumerate(atm_notices, 1):
                bname = os.path.basename(atm)
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
                ok = await safe_send_document(
                    bot=bot,
                    chat_id=chat_id,
                    file_path=atm,
                    caption=f"🏧 [{idx}/{len(atm_notices)}] CCTV नोटिस: {bname}"
                )
                if ok:
                    sent_atm_count += 1
                await asyncio.sleep(1)

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
            f"• *ऑल-इन-वन बंडल*: {'✅ 1 ZIP प्रेषित' if zip_sent else '⚠️ ZIP तैयार'}\n"
            f"• *बैंक नोटिस (PDF)*: {sent_pdf_count} फाइल्स प्रेषित\n"
            f"• *ATM CCTV नोटिस*: {sent_atm_count} फाइल्स प्रेषित\n"
            f"• *कंबाइंड नोटिस*: 1 DOCX प्रेषित\n"
            f"• *ईमेल ऑटोमेशन*: {safe_email}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ *नया केस शुरू करने के लिए कभी भी नई NCRP शिकायत PDF भेजें या /start लिखें।*\n"
            f"*(यदि कभी कोई फाइल दोबारा चाहिए तो /resend लिखें)*"
        )
        keyboard = [
            [InlineKeyboardButton("📁 एक और केस शुरू करें (/start)", callback_data="act:reset")],
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

    request_config = HTTPXRequest(
        connection_pool_size=16,
        connect_timeout=60.0,
        read_timeout=180.0,
        write_timeout=180.0,
        media_write_timeout=180.0,
        pool_timeout=60.0
    )
    app = ApplicationBuilder().token(token).request(request_config).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("sample", sample_command))
    app.add_handler(CommandHandler("resend", resend_command))
    app.add_handler(CommandHandler("reset", reset_command))

    # Documents (PDFs)
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Interactive Inline Buttons
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # Text inputs (Replies for FIR no, Notice no, IO selection, Email, etc.)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Start Polling
    app.run_polling()


if __name__ == "__main__":
    main()
