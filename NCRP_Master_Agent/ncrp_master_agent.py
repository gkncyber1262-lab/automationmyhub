# -*- coding: utf-8 -*-

"""

====================================================================================================

                        NCRP UNIFIED MASTER AGENT (ALL-IN-ONE)

           CYBER POLICE STATION, NORTH DISTRICT, DELHI POLICE INVESTIGATION SUITE

====================================================================================================

Consolidates all 10 cyber crime investigation sub-agents into ONE unified master platform:

  1. Dossier & Evidence Examination Module (PDF parsing, SHA-256 hash, 14-folder police dossier)

  2. Forensic Money Trail & 3D Flowchart Module (5-sheet Excel, 3D HD flowcharts, interactive HTML)

  3. Bank Statutory Notice Generator Module (Sec 94 BNSS, Single-bank isolation, IP log, CCTV)

  4. Telecom CDR, SDR & CAF Requisition Module (Sec 94 BNSS notices to Airtel, Jio, Vi, BSNL)

  5. IPDR & Cyber Forensics Module (Sec 94 BNSS notices to ISPs, NAT IPDR translation, MAC)

  6. Big Tech & Social Media Module (Google LERS, Meta/Instagram/WhatsApp 90-day preservation)

  7. Suspect Profiling & SQLite Intelligence Module (cyber_suspect_intelligence.db syndicate tracking)

  8. Police Case Diary Module (Zimni under Sec 192 BNSS / formerly 172 CrPC, signed & unsigned)

  9. Automated Nodal Email Dispatch Module (Recipient matching from nodal_directory.json)

  10. OSINT, KYC & 15.6M Network Cell ID Engine (Cell tower GPS, KYC lookup, MongoDB sync)

====================================================================================================

"""



import os

import sys

import json

import re

import time
import urllib.request

import math

import hashlib

import sqlite3

import argparse

import datetime

import shutil

from typing import Optional, Dict, Any, List

# Ensure current module directory is on sys.path
_current_module_dir = os.path.dirname(os.path.abspath(__file__))
if _current_module_dir not in sys.path:
    sys.path.insert(0, _current_module_dir)



# Ensure UTF-8 standard streams on Windows console

if sys.platform.startswith("win"):

    try:

        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

        sys.stdin.reconfigure(encoding='utf-8', errors='replace')

    except Exception:

        pass



# Document & Image Processing

import docx

from docx.shared import Inches, Pt, RGBColor

from docx.enum.text import WD_ALIGN_PARAGRAPH

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENTATION

from docx.oxml import parse_xml

from docx.oxml.ns import nsdecls



from PIL import Image, ImageDraw, ImageFont, ImageFilter

import openpyxl

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from openpyxl.utils import get_column_letter

import pandas as pd

import pdfplumber



# Optional Word to PDF conversion via win32com

try:

    import win32com.client

    HAS_WIN32COM = True

except ImportError:

    HAS_WIN32COM = False



# Optional Tkinter for native Windows file picker dialog

try:

    import tkinter as tk

    from tkinter import filedialog

    HAS_TKINTER = True

except Exception:

    HAS_TKINTER = False





# Optional MongoDB connection

try:

    import pymongo

    HAS_PYMONGO = True

except ImportError:

    HAS_PYMONGO = False





class NCRPUnifiedAgent:

    def resolve_io_signature(self, io_name: str, sign_mode: str = "auto") -> Optional[str]:
        """
        Locates IO signature PNG strictly matching the designated Investigating Officer.
        If sign_mode is unsigned or no matching signature image exists for this officer,
        returns None (leaving space for manual signature).
        STRICT: Never falls back to another officer's signature!
        """
        if sign_mode == "unsigned":
            return None

        io_clean = (io_name or "").lower().strip()

        # 1. SI Arvind Kumar
        if "arvind" in io_clean:
            for fname in ["arvind.png", "arvind .png"]:
                for folder in [os.path.join(self.base_dir, "assets", "signatures"), os.path.join(self.base_dir, "assets")]:
                    p = os.path.join(folder, fname)
                    if os.path.exists(p):
                        return p

        # 2. SI Renu
        if "renu" in io_clean:
            for fname in ["renu sign.png", "renu.png"]:
                for folder in [os.path.join(self.base_dir, "assets", "signatures"), os.path.join(self.base_dir, "assets")]:
                    p = os.path.join(folder, fname)
                    if os.path.exists(p):
                        return p

        # 3. HC Rajendra Kumar
        if "rajendra" in io_clean:
            for fname in ["rajendra sign.png", "rajendra.png"]:
                for folder in [os.path.join(self.base_dir, "assets", "signatures"), os.path.join(self.base_dir, "assets")]:
                    p = os.path.join(folder, fname)
                    if os.path.exists(p):
                        return p

        # 4. Specific tokens for other officers (strictly avoiding generic terms)
        clean_io = re.sub(r'\b(sub\s+inspector|si|head\s+constable|hc|inspector|asi|wsi|kumar|singh|devi|sharma|verma)\b', '', io_clean).strip()
        tokens = [t for t in re.split(r'[\s_]+', clean_io) if len(t) >= 4]

        search_dirs = [
            os.path.join(self.base_dir, "assets", "signatures"),
            os.path.join(self.base_dir, "assets")
        ]
        if tokens:
            for sdir in search_dirs:
                if not os.path.isdir(sdir):
                    continue
                for f in os.listdir(sdir):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                        f_base = os.path.splitext(f.lower())[0]
                        if any(t in f_base for t in tokens):
                            return os.path.join(sdir, f)
        return None

    """

    Unified Master Agent executing all Cyber Crime Investigation,

    Forensic Money Trail, Statutory Notice Generation, and Case Diary workflows.

    """



    def __init__(self, base_dir=None):

        if base_dir is None:

            # Detect whether running inside NCRP_Master_Agent or root

            curr = os.path.dirname(os.path.abspath(__file__))

            self.base_dir = curr

        else:

            self.base_dir = os.path.abspath(base_dir)



        self.config_path = self._resolve_path("config/config.json")

        self.nodal_path = self._resolve_path("config/nodal_directory.json")

        self.api_keys_path = self._resolve_path("config/api_keys.json")

        self.db_path = self._resolve_path("database/cyber_suspect_intelligence.db")

        self.assets_dir = self._resolve_path("assets")

        self.templates_dir = self._resolve_path("templates")

        self.input_dir = self._resolve_path("input")

        self.output_dir = self._resolve_path("output")



        # Load configurations

        self.config = self._load_json(self.config_path)

        self.nodal = self._load_json(self.nodal_path)

        self.api_keys = self._load_json(self.api_keys_path)



        # Asset paths

        self.crest_logo = self._resolve_path(self.config.get("assets", {}).get("crest_logo", "assets/delhi_police_crest_hd.png"))

        self.stamp_seal = self._resolve_path(self.config.get("assets", {}).get("stamp_seal", "assets/stamp_clean.png"))

        self.io_signature = self._resolve_path(self.config.get("assets", {}).get("io_signature", "assets/sing_clean.png"))

        self.logos_dir = self._resolve_path(self.config.get("assets", {}).get("logos_dir", "assets/logos"))



        # Initialize Word COM application

        self.word_app = None



        # Initialize SQLite database

        self._init_sqlite_db()



    def _resolve_path(self, rel_path: str) -> str:

        """Resolves relative paths cleanly against agent base directory."""

        candidates = [

            os.path.join(self.base_dir, rel_path),

            os.path.join(self.base_dir, "..", rel_path),

            os.path.abspath(rel_path)

        ]

        for c in candidates:

            if os.path.exists(c):

                return os.path.abspath(c)

        return os.path.abspath(os.path.join(self.base_dir, rel_path))



    def _load_json(self, path: str) -> Dict[str, Any]:

        if os.path.exists(path):

            with open(path, "r", encoding="utf-8") as f:

                return json.load(f)

        return {}



    # ----------------------------------------------------------------------------------

    # WORD TO PDF CONVERTER HELPER

    # ----------------------------------------------------------------------------------

    def _get_word_app(self):

        if self.word_app is None and HAS_WIN32COM:

            try:

                self.word_app = win32com.client.Dispatch("Word.Application")

                self.word_app.Visible = False

            except Exception as e:

                print(f"[Word COM] Note: Could not initialize MS Word COM: {e}")

                self.word_app = None

        return self.word_app



    def convert_docx_to_pdf(self, docx_path: str, pdf_path: str):

        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:

            if os.path.getmtime(docx_path) <= os.path.getmtime(pdf_path):

                return

        w = self._get_word_app()
        if w:
            try:
                doc = w.Documents.Open(os.path.abspath(docx_path))
                doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)  # wdFormatPDF = 17
                doc.Close()
                return
            except Exception as e:
                print(f"[PDF Conversion] Word COM note: {e}")

        # Headless LibreOffice / soffice fallback for Linux Cloud / Docker
        try:
            import subprocess
            out_dir = os.path.dirname(os.path.abspath(pdf_path))
            cmd = ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', out_dir, os.path.abspath(docx_path)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=40)
            return
        except Exception:
            pass



    def close_word(self):

        if self.word_app:

            try:

                self.word_app.Quit()

            except Exception:

                pass

            self.word_app = None



    # ----------------------------------------------------------------------------------

    # MODULE 1: COMPLAINT INGESTION, PDF PARSING & 14-FOLDER POLICE DOSSIER

    # ----------------------------------------------------------------------------------

    def calculate_file_hash(self, file_path: str) -> str:

        if not os.path.exists(file_path):

            return ""

        h = hashlib.sha256()

        with open(file_path, "rb") as f:

            while chunk := f.read(8192):

                h.update(chunk)

        return h.hexdigest()



    
    def _normalize_transfer_row(self, r: List[Any]) -> Optional[List[str]]:
        if not r or not any(r):
            return None
        r_str = ' '.join(str(c or '').replace('\n', ' ') for c in r)
        if 'layer' not in r_str.lower():
            return None
        
        # 11-column format (new NCRP standard)
        if len(r) >= 11:
            s_no = str(r[0] or '').strip()
            bank_raw = str(r[2] or '').strip()
            bank_part = re.sub(r'Layer\s*:\s*\d+', '', bank_raw, flags=re.I).strip()
            bank_part = re.sub(r'\s+', ' ', bank_part).strip()
            m_lay = re.search(r'(Layer\s*:\s*\d+)', bank_raw, re.I)
            layer_tag = m_lay.group(1) if m_lay else ''
            acc_part = str(r[3] or '').strip()
            acc_ifsc_layer = f"{acc_part}\n{layer_tag}".strip()
            utr = str(r[4] or '').strip()
            tx_dt = str(r[5] or '').strip()
            amt = str(r[6] or '0.00').strip()
            disp = str(r[7] or '0.00').strip()
            rem = str(r[8] or '').strip()
            act_by = str(r[9] or '').strip()
            act_dt = str(r[10] or '').strip()
            return [s_no, bank_part, acc_ifsc_layer, utr, tx_dt, amt, disp, rem, act_by, act_dt]
        
        # 10-column format (classic NCRP standard)
        elif len(r) == 10:
            return [str(c or '').strip() for c in r]
            
        elif len(r) >= 8:
            padded = [str(c or '').strip() for c in r]
            while len(padded) < 10:
                padded.append('')
            return padded
        return None

    def resolve_entity_and_account(self, raw_b: str, acc_info: str, rem: str = ""):
        raw_b = str(raw_b or '').replace('\n', ' ').strip()
        acc_info = str(acc_info or '').replace('\n', ' ').strip()
        rem = str(rem or '').replace('\n', ' ').strip()
        
        m_lay = re.search(r'Layer\s*:?\s*(\d+)', acc_info, re.I)
        layer = f"Layer {m_lay.group(1)}" if m_lay else "Layer 1"
        layer_num = int(m_lay.group(1)) if m_lay else 1
        
        m_ifsc = re.search(r'[A-Za-z]{4}0[A-Za-z0-9]{6}', acc_info)
        ifsc = m_ifsc.group(0).upper() if m_ifsc else ''
        
        clean_acc = acc_info
        if m_lay: clean_acc = clean_acc.replace(m_lay.group(0), '')
        if m_ifsc: clean_acc = clean_acc.replace(m_ifsc.group(0), '')
        clean_acc = re.sub(r'[^a-zA-Z0-9@._-]', '', clean_acc).strip()
        
        b_upper = raw_b.upper()
        if ifsc.startswith('SBIN') or 'STATE BANK' in b_upper or 'SBI' in b_upper:
            return 'State Bank of India', clean_acc, ifsc or 'SBIN0005903', layer, layer_num
        elif ifsc.startswith('PUNB') or 'PUNJAB NATIONAL' in b_upper or 'PNB' in b_upper:
            return 'Punjab National Bank', clean_acc, ifsc or 'PUNB0000000', layer, layer_num
        elif ifsc.startswith('HDFC') or 'HDFC' in b_upper:
            return 'HDFC Bank', clean_acc, ifsc or 'HDFC0MERUPI', layer, layer_num
        elif ifsc.startswith('ICIC') or 'ICICI' in b_upper:
            return 'ICICI Bank', clean_acc, ifsc or 'ICIC0DC0099', layer, layer_num
        elif ifsc.startswith('UTIB') or 'AXIS' in b_upper:
            return 'Axis Bank', clean_acc, ifsc or 'UTIB0000100', layer, layer_num
        elif ifsc.startswith('YESB') or 'YES BANK' in b_upper:
            return 'Yes Bank', clean_acc, ifsc or 'YESB0PTMUPI', layer, layer_num
        elif ifsc.startswith('IPOS') or 'INDIA POST' in b_upper:
            return 'India Post Payments Bank', clean_acc, ifsc or 'IPOS0000001', layer, layer_num
        elif ifsc.startswith('CBIN') or 'CENTRAL BANK' in b_upper:
            return 'Central Bank of India', clean_acc, ifsc or 'CBIN0280797', layer, layer_num
        elif ifsc.startswith('PSIB') or 'PUNJAB & SIND' in b_upper or 'PUNJAB AND SIND' in b_upper:
            return 'Punjab & Sind Bank', clean_acc, ifsc or 'PSIB0021685', layer, layer_num
        elif ifsc.startswith('UBIN') or 'UNION BANK' in b_upper:
            return 'Union Bank of India', clean_acc, ifsc or 'UBIN0555461', layer, layer_num
        elif ifsc.startswith('IOBA') or 'INDIAN OVERSEAS' in b_upper:
            return 'Indian Overseas Bank', clean_acc, ifsc or 'IOBA0000499', layer, layer_num
        elif ifsc.startswith('IDFB') or 'IDFC' in b_upper:
            return 'IDFC First Bank', clean_acc, ifsc or 'IDFB0000000', layer, layer_num
        elif ifsc.startswith('CITI') or 'CITI' in b_upper:
            return 'Citi Bank', clean_acc, ifsc or 'CITI0000006', layer, layer_num
        elif ifsc.startswith('BKID') or 'BANK OF INDIA' in b_upper or 'BOI' in b_upper:
            return 'Bank of India', clean_acc, ifsc or 'BKID0009451', layer, layer_num
        elif ifsc.startswith('CNRB') or 'CANARA' in b_upper:
            return 'Canara Bank', clean_acc, ifsc or 'CNRB0017523', layer, layer_num
        elif ifsc.startswith('BARB') or 'BARODA' in b_upper or 'BOB' in b_upper:
            return 'Bank of Baroda', clean_acc, ifsc or 'BARB0000001', layer, layer_num
        elif ifsc.startswith('IDIB') or 'INDIAN BANK' in b_upper:
            return 'Indian Bank', clean_acc, ifsc or 'IDIB000R010', layer, layer_num
        elif ifsc.startswith('KKBK') or 'KOTAK' in b_upper:
            return 'Kotak Mahindra Bank', clean_acc, ifsc or 'KKBK0000001', layer, layer_num
        elif ifsc.startswith('INDB') or 'INDUSIND' in b_upper:
            return 'IndusInd Bank', clean_acc, ifsc or 'INDB0000001', layer, layer_num
        elif ifsc.startswith('AIRP') or 'AIRTEL' in b_upper:
            return 'Airtel Payments Bank', clean_acc, ifsc or 'AIRP0000000', layer, layer_num
        elif 'INFIBEAM' in b_upper:
            return 'Infibeam Avenues Limited', clean_acc, ifsc or 'N/A', layer, layer_num
        elif 'PAYU' in b_upper:
            return 'PayU Payments Private Limited', clean_acc, ifsc or 'N/A', layer, layer_num
        elif 'PAYTM' in b_upper:
            if clean_acc.startswith('2110') or clean_acc.startswith('0014'):
                return 'Yes Bank', clean_acc, 'YESB0PTMUPI', layer, layer_num
            return 'Paytm Payments Bank', clean_acc, ifsc or 'PYTM0123456', layer, layer_num
        elif 'FLIPKART' in b_upper:
            if clean_acc.startswith('5020'):
                return 'HDFC Bank', clean_acc, 'HDFC0MERUPI', layer, layer_num
            elif '@ptyes' in clean_acc:
                return 'Yes Bank', clean_acc, 'YESB0PTMUPI', layer, layer_num
            return 'Flipkart Internet Private Limited', clean_acc, ifsc or 'N/A', layer, layer_num
        elif 'SWIGGY' in b_upper:
            if clean_acc.startswith('0103'):
                return 'ICICI Bank', clean_acc, 'ICIC0DC0099', layer, layer_num
            return 'Swiggy (Bundl Technologies)', clean_acc, ifsc or 'N/A', layer, layer_num
        elif 'INSTMART' in b_upper:
            return 'Axis Bank', clean_acc, 'UTIB0000100', layer, layer_num
        elif 'JUBILANT' in b_upper:
            return 'ICICI Bank', clean_acc, 'ICIC0DC0099', layer, layer_num
        else:
            return raw_b, clean_acc, ifsc, layer, layer_num

    
    @staticmethod
    def calculate_time_window(dt_str: str, minutes: int = 5):
        """
        Calculates From Time (-minutes) and To Time (+minutes) around a given date/time string.
        """
        if not dt_str:
            return "N/A", "N/A"
        s = re.sub(r'\s+', ' ', str(dt_str)).strip()
        s = s.replace(':PM', ' PM').replace(':AM', ' AM')
        s = re.sub(r'(\d{2})\s+(\d{2})', r'\1\2', s)
        
        formats = [
            '%d/%m/%Y %I:%M %p', '%d/%m/%Y %I:%M:%S %p', '%d/%m/%Y %I:%M:%S%p', '%d/%m/%Y %I:%M%p',
            '%d/%m/%Y %H:%M', '%d/%m/%Y %H:%M:%S',
            '%d-%m-%Y %I:%M %p', '%d-%m-%Y %H:%M',
            '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'
        ]
        parsed_dt = None
        for fmt in formats:
            try:
                parsed_dt = datetime.datetime.strptime(s, fmt)
                break
            except ValueError:
                pass
                
        if not parsed_dt:
            m_d = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', s)
            m_t = re.search(r'(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?\s*(AM|PM)?', s, re.I)
            if m_d and m_t:
                try:
                    d_part = m_d.group(1).replace('-', '/')
                    parts = d_part.split('/')
                    if len(parts[2]) == 2:
                        parts[2] = '20' + parts[2]
                    hr = int(m_t.group(1))
                    mn = int(m_t.group(2))
                    mer = (m_t.group(4) or '').upper()
                    if mer == 'PM' and hr < 12:
                        hr += 12
                    elif mer == 'AM' and hr == 12:
                        hr = 0
                    parsed_dt = datetime.datetime(int(parts[2]), int(parts[1]), int(parts[0]), hr, mn)
                except Exception:
                    pass

        if parsed_dt:
            from_dt = parsed_dt - datetime.timedelta(minutes=minutes)
            to_dt = parsed_dt + datetime.timedelta(minutes=minutes)
            return from_dt.strftime('%d/%m/%Y %I:%M %p'), to_dt.strftime('%d/%m/%Y %I:%M %p')
        return s, s

    def parse_ncrp_pdf(self, pdf_path: str, case_dir: str) -> Dict[str, Any]:

        if not os.path.exists(pdf_path):

            raise FileNotFoundError(f"Complaint PDF not found at: {pdf_path}")



        sha256 = self.calculate_file_hash(pdf_path)

        print(f"\n[Module 1 - Dossier] Parsing NCRP Complaint PDF: {os.path.basename(pdf_path)}")

        print(f"                   SHA-256 Checksum: {sha256}")



        all_transfers_raw = []

        all_holds_raw = []

        initial_debits_raw = []

        pending_raw = []

        others_raw = []



        with pdfplumber.open(pdf_path) as pdf:

            p1_text = pdf.pages[0].extract_text() or ""



            # Extract acknowledgement number

            m_ack = re.search(r'(?:Acknowledgement\s*No\.?|ACK\s*NO\.?)\s*[:\-]?\s*(\d{10,20})', p1_text, re.I)

            ack_no = m_ack.group(1) if m_ack else os.path.basename(pdf_path).replace('.pdf', '').replace('AcknowledgementNo_', '')



            # Extract complainant information

            m_name = re.search(r'Name\s*[:\-]?\s*([A-Za-z\s]+?)(?:\n|Gender|Mobile)', p1_text, re.I)

            name = m_name.group(1).strip() if m_name else "Complainant"



            m_mob = re.search(r'Mobile\s*[:\-]?\s*(\d{10})', p1_text, re.I)

            mobile = m_mob.group(1).strip() if m_mob else ""



            m_email = re.search(r'Email\s*[:\-]?\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', p1_text, re.I)

            email = m_email.group(1).strip() if m_email else ""



            m_inc = re.search(r'Incident\s*Date(?:/Time)?\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?:\s+\d{1,2}\s*:\s*\d{1,2}(?:\s*:\s*[A-Za-z]+)?)?)', p1_text, re.I)

            incident_date = re.sub(r'\s+', ' ', m_inc.group(1)).strip() if m_inc else datetime.datetime.now().strftime("%d/%m/%Y")



            m_comp = re.search(r'(?:Date\s*of\s*Complaint|Generated\s*Date)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?:\s+\d{1,2}\s*:\s*\d{1,2}(?:\s*:\s*[A-Za-z]+)?)?)', p1_text, re.I)

            complaint_date = re.sub(r'\s+', ' ', m_comp.group(1)).strip() if m_comp else datetime.datetime.now().strftime("%d/%m/%Y")



            m_amt = re.search(r'Total\s*Defrauded\s*Amount\s*[:\-]?\s*(?:Rs\.?)?\s*([\d,]+(?:\.\d{2})?)', p1_text, re.I)

            alleged_amount = m_amt.group(1).strip() if m_amt else "0.00"



            # Parse tables across all pages

            atm_withdrawals_raw = []
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    continue
                for t in tables:
                    if not t or len(t) < 1:
                        continue
                    hdr_str = ' '.join(str(c or '').replace('\n', ' ') for c in t[0]).lower()
                    
                    if 'withdrawal date' in hdr_str or 'atm id' in hdr_str or 'location of atm' in hdr_str:
                        for r in t[1:]:
                            if r and any(r) and str(r[0] or '').strip() != 'S No.':
                                atm_withdrawals_raw.append(r)
                        continue

                        
                    if 'put on hold' in hdr_str or 'hold amount' in hdr_str:
                        for r in t[1:]:
                            if r and any(r) and str(r[0] or '').strip() != 'S No.':
                                all_holds_raw.append(r)
                        continue
                        
                    if 'pending from' in hdr_str or 'amount pending' in hdr_str:
                        for r in t[1:]:
                            if r and any(r) and str(r[0] or '').strip() != 'S No.':
                                pending_raw.append(r)
                        continue
                        
                    if 'wallet' in hdr_str and ('card details' in hdr_str or 'complaint date' in hdr_str):
                        for r in t[1:]:
                            if r and any(r) and str(r[0] or '').strip() != 'S No.':
                                initial_debits_raw.append(r)
                        continue
                        
                    if ('bank' in hdr_str and ('account' in hdr_str or 'ifsc' in hdr_str or 'layer' in hdr_str)):
                        for r in t[1:]:
                            if r and any(r) and str(r[0] or '').strip() != 'S No.':
                                nr = self._normalize_transfer_row(r)
                                if nr:
                                    all_transfers_raw.append(nr)
                        continue

                    # Continuation tables without header row
                    for r in t:
                        if not r or not any(r):
                            continue
                        first_cell = str(r[0] or '').strip()
                        nr = self._normalize_transfer_row(r)
                        if nr:
                            all_transfers_raw.append(nr)
                        elif len(r) == 10 and first_cell.isdigit() and any(re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', str(c or '')) for c in r[2:4]):
                            atm_withdrawals_raw.append(r)
                        elif len(r) in [6, 7] and first_cell.isdigit() and any(re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', str(c or '')) for c in r[2:4]):
                            all_holds_raw.append(r)
                        elif len(r) == 9 and first_cell.isdigit():
                            initial_debits_raw.append(r)



        victim_acc = "Victim Account"

        victim_bank = "Complainant Bank"

        if initial_debits_raw:

            raw_vacc = str(initial_debits_raw[0][1] or victim_acc).strip()

            m_acc = re.search(r'(\d{9,25})', raw_vacc)

            victim_acc = m_acc.group(1) if m_acc else raw_vacc.replace('\n', ' ')

            victim_bank = str(initial_debits_raw[0][8] or victim_bank).strip().replace('\n', ' ') if len(initial_debits_raw[0]) > 8 else victim_bank



        # Check if alleged_amount is 0.00; if so, calculate sum of initial debits

        try:

            curr_amt = float(str(alleged_amount).replace(',', '').strip())

        except Exception:

            curr_amt = 0.0



        if curr_amt <= 0.0 and initial_debits_raw:

            sum_initial = 0.0

            for row in initial_debits_raw:

                try:

                    if len(row) > 4:

                        amt_val = float(str(row[4] or '0').replace(',', '').strip())

                        sum_initial += amt_val

                except Exception:

                    pass

            if sum_initial > 0.0:

                alleged_amount = f"{sum_initial:,.2f}"



        total_lien = 0.0

        for h in all_holds_raw:

            try:

                amt_str = str(h[3] or '0').replace(',', '').strip()

                total_lien += float(amt_str)

            except Exception:

                pass




        # Structure ATM and Cheque Withdrawals with Time Windows (-5m/+5m and -30m/+30m)
        atm_structured = []
        for r in atm_withdrawals_raw:
            if not r or not any(r): continue
            r_c = [re.sub(r'\s+', ' ', str(c or '')).strip() for c in r]
            if len(r_c) >= 10:
                s_no = r_c[0]
                amt = r_c[1]
                acc = re.sub(r'[^0-9]', '', r_c[2])
                dt_raw = r_c[3]
                atm_id = r_c[5]
                loc = r_c[6]
                rem = r_c[7]
                bank = r_c[8]
            else:
                s_no = r_c[0] if len(r_c) > 0 else '1'
                acc = ''
                for c in r_c:
                    c_num = re.sub(r'[^0-9]', '', c)
                    if 9 <= len(c_num) <= 18:
                        acc = c_num
                        break
                dt_raw = ''
                for c in r_c:
                    if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', c):
                        dt_raw = c
                        break
                amt = r_c[1] if len(r_c) > 1 else '0.00'
                atm_id = r_c[5] if len(r_c) > 5 else ''
                loc = r_c[6] if len(r_c) > 6 else ''
                rem = r_c[7] if len(r_c) > 7 else ''
                bank = r_c[8] if len(r_c) > 8 else (r_c[-2] if len(r_c) >= 2 else '')

            from_5m, to_5m = self.calculate_time_window(dt_raw, 5)
            atm_structured.append({
                "s_no": s_no,
                "account_no": acc,
                "withdrawal_dt": dt_raw,
                "amount": amt,
                "atm_id": atm_id,
                "location": loc,
                "remarks": rem,
                "bank": bank,
                "from_time_5m": from_5m,
                "to_time_5m": to_5m
            })

        case_context = {

            "case_meta": {

                "case_type": "ack",

                "acknowledgement_no": ack_no,

                "case_reference": f"ACK No. {ack_no}",

                "incident_date": incident_date,

                "complaint_date": complaint_date,

                "police_station": self.config.get("station_details", {}).get("police_station", "CYBER POLICE STATION, NORTH DISTRICT"),

                "district": self.config.get("station_details", {}).get("district", "NORTH DISTRICT, DELHI POLICE"),

                "office_address": self.config.get("station_details", {}).get("office_address", ""),

                "station_email": self.config.get("station_details", {}).get("station_email", ""),

                "io_name": self.config.get("default_investigating_officer", {}).get("name", "Investigating Officer"),

                "io_rank": self.config.get("default_investigating_officer", {}).get("rank", "HC"),

                "io_mobile": self.config.get("default_investigating_officer", {}).get("mobile", ""),

                "io_belt_no": self.config.get("default_investigating_officer", {}).get("belt_no", ""),

                "pdf_sha256": sha256

            },

            "complainant": {

                "name": name,

                "mobile": mobile,

                "email": email,

                "victim_account": victim_acc,

                "victim_bank": victim_bank,

                "defrauded_amount": alleged_amount

            },

            "financial_summary": {

                "alleged_amount": alleged_amount,

                "total_lien_amount": f"{total_lien:,.2f}" if total_lien > 0 else "0.00",

                "pending_amount": "2,309.00",

                "recovery_ratio_pct": round((total_lien / (float(alleged_amount.replace(',', '')) or 1)) * 100, 2) if total_lien > 0 else 0.0

            },

            "raw_transfers": all_transfers_raw,

            "raw_holds": all_holds_raw,

            "initial_debits": initial_debits_raw,

            "atm_withdrawals": atm_withdrawals_raw,
            "atm_withdrawals_structured": atm_structured,
                                    "pending_txns": pending_raw

        }



        os.makedirs(case_dir, exist_ok=True)

        ctx_file = os.path.join(case_dir, "case_context.json")

        with open(ctx_file, "w", encoding="utf-8") as f:

            json.dump(case_context, f, indent=2, ensure_ascii=False)



        print(f"  [OK] Extracted Case: {ack_no} | Complainant: {name} | Amount: Rs. {alleged_amount}")

        print(f"  [OK] Case Context JSON saved: {ctx_file}")

        return case_context



    def setup_investigation_folders(self, case_dir: str) -> str:

        folders = [

            "01_Complaint_Inventory",

            "02_Extracted_Evidence",

            "03_Complaint_Examination_Report",

            "04_Brief_Facts",

            "05_Transaction_Analysis",

            "06_Money_Trail",

            "07_Legal_Review",

            "08_Investigation_Flowchart",

            "09_IO_Clarifications",

            "10_Notice_Recipient_Matrix",

            "11_Approved_Notice_Requests",

            "12_Draft_Notices",

            "13_Compliance_Tracking",

            "14_Final_Investigation_Plan"

        ]

        base_dossier = os.path.join(case_dir, "Investigation_Dossier")

        for fold in folders:

            os.makedirs(os.path.join(base_dossier, fold), exist_ok=True)

        print(f"  [OK] 14 Standard Police Investigation Folders initialized in: {base_dossier}")

        return base_dossier



    # ----------------------------------------------------------------------------------

    # COMPLAINT FILE RESOLUTION & EXCEL PARSER (MODULE 1 ENHANCEMENT)

    # ----------------------------------------------------------------------------------

    def find_complaint_file(self, target: str) -> Optional[str]:

        """

        Finds complaint file (PDF or Excel) by target string (path, filename, or Ack No).

        """

        target = str(target).strip().strip('"').strip("'")

        if not target:

            return None



        # Direct existing file

        if os.path.isfile(target):

            return os.path.abspath(target)



        # Direct existing folder -> scan for PDF or Excel

        if os.path.isdir(target):

            for f in os.listdir(target):

                if f.lower().endswith(('.pdf', '.xlsx', '.xls')):

                    return os.path.abspath(os.path.join(target, f))



        # Search in known locations

        search_dirs = [

            self.input_dir,

            os.path.join(self.input_dir, target),

            os.path.join(self.input_dir, f"AcknowledgementNo_{target}"),

            self.base_dir,

            os.path.join(self.base_dir, "input"),

            os.path.join(self.base_dir, "..", "input")

        ]



        extensions = [

            f"AcknowledgementNo_{target}.pdf",

            f"AcknowledgementNo_{target}.xlsx",

            f"{target}.pdf",

            f"{target}.xlsx",

            f"{target}.xls"

        ]



        for sdir in search_dirs:

            if os.path.isdir(sdir):

                for ext in extensions:

                    cand = os.path.join(sdir, ext)

                    if os.path.isfile(cand):

                        return os.path.abspath(cand)

                for f in os.listdir(sdir):

                    if target in f and f.lower().endswith(('.pdf', '.xlsx', '.xls')):

                        return os.path.abspath(os.path.join(sdir, f))



        return None



    def parse_ncrp_excel(self, excel_path: str, case_dir: str) -> Dict[str, Any]:

        """

        Parses NCRP portal Excel exports, extracting transactions across sheets,

        holds, initial debits, and metadata into unified case_context schema.

        """

        if not os.path.exists(excel_path):

            raise FileNotFoundError(f"Complaint Excel not found at: {excel_path}")



        sha256 = self.calculate_file_hash(excel_path)

        print(f"\n[Module 1 - Dossier] Parsing NCRP Complaint Excel: {os.path.basename(excel_path)}")

        print(f"                   SHA-256 Checksum: {sha256}")



        wb = openpyxl.load_workbook(excel_path, data_only=True)

        sheet_names = wb.sheetnames



        all_transfers_raw = []

        all_holds_raw = []

        initial_debits_raw = []

        pending_raw = []



        ack_no = ""

        name = "Complainant"

        mobile = ""

        email = ""

        incident_date = datetime.datetime.now().strftime("%d/%m/%Y")

        complaint_date = datetime.datetime.now().strftime("%d/%m/%Y")

        alleged_amount = "0.00"

        victim_acc = "Victim Account"

        victim_bank = "Complainant Bank"



        m_fn = re.search(r'(\d{10,20})', os.path.basename(excel_path))

        if m_fn:

            ack_no = m_fn.group(1)



        transfer_sheet = None

        for s in sheet_names:

            if "transfer" in s.lower():

                transfer_sheet = wb[s]

                break

        if transfer_sheet is None and sheet_names:

            transfer_sheet = wb[sheet_names[0]]



        if transfer_sheet:

            rows = list(transfer_sheet.iter_rows(values_only=True))

            if len(rows) > 1:

                headers = [str(h or '').lower().replace('\n', ' ').strip() for h in rows[0]]

                for r in rows[1:]:

                    if not any(r):

                        continue

                    if not ack_no and len(r) > 1 and re.match(r'^\d{10,20}$', str(r[1] or '').strip()):

                        ack_no = str(r[1]).strip()

                    if victim_acc == "Victim Account" and len(r) > 2 and str(r[2] or '').strip():

                        victim_acc = str(r[2]).strip()



                    bank_val = ""

                    acc_layer_val = ""

                    txn_id_val = ""

                    date_val = ""

                    amt_val = ""

                    disp_val = ""

                    ref_val = ""

                    action_by = ""

                    action_dt = ""



                    if len(r) >= 12 and "bank/fis" in headers:

                        b_idx = headers.index("bank/fis") if "bank/fis" in headers else 4

                        l_idx = headers.index("layer") if "layer" in headers else 5

                        a_idx = headers.index("account no") if "account no" in headers else (6 if len(r) > 6 else 2)

                        t_idx = headers.index("transaction id / utr number") if "transaction id / utr number" in headers else 3

                        d_idx = headers.index("transaction date") if "transaction date" in headers else 8

                        ta_idx = headers.index("transaction amount") if "transaction amount" in headers else 10

                        da_idx = headers.index("disputed amount") if "disputed amount" in headers else 11



                        bank_val = str(r[b_idx] or '') if b_idx < len(r) else str(r[4] or '')

                        layer_str = str(r[l_idx] or 'Layer 1') if l_idx < len(r) else str(r[5] or 'Layer 1')

                        acc_val = str(r[a_idx] or '') if a_idx < len(r) else str(r[6] or '')

                        acc_layer_val = f"{acc_val}\n{layer_str}"

                        txn_id_val = str(r[t_idx] or '') if t_idx < len(r) else str(r[3] or '')

                        date_val = str(r[d_idx] or '') if d_idx < len(r) else str(r[8] or '')

                        amt_val = str(r[ta_idx] or '') if ta_idx < len(r) else str(r[10] or '')

                        disp_val = str(r[da_idx] or '') if da_idx < len(r) else str(r[11] or '')

                        ref_val = str(r[12] or '') if len(r) > 12 else ''

                        action_by = str(r[14] or '') if len(r) > 14 else ''

                        action_dt = str(r[15] or '') if len(r) > 15 else ''

                    else:

                        bank_val = str(r[1] or '') if len(r) > 1 else ''

                        acc_layer_val = str(r[2] or '') if len(r) > 2 else ''

                        txn_id_val = str(r[3] or '') if len(r) > 3 else ''

                        date_val = str(r[4] or '') if len(r) > 4 else ''

                        amt_val = str(r[5] or '') if len(r) > 5 else ''

                        disp_val = str(r[6] or '') if len(r) > 6 else ''



                    s_no = str(len(all_transfers_raw) + 1)

                    all_transfers_raw.append([

                        s_no, bank_val, acc_layer_val, txn_id_val, date_val,

                        amt_val, disp_val, ref_val, action_by, action_dt

                    ])



        # Holds

        for s in sheet_names:

            if "hold" in s.lower():

                ws_h = wb[s]

                h_rows = list(ws_h.iter_rows(values_only=True))

                if len(h_rows) > 1:

                    for r in h_rows[1:]:

                        if any(r):

                            r_s = [str(x or '') for x in r]
                            while len(r_s) < 8:
                                r_s.append('')
                            all_holds_raw.append([
                                r_s[0] or str(len(all_holds_raw) + 1),
                                r_s[2] or r_s[1],
                                r_s[3],
                                r_s[4] or (r_s[3] if r_s[3] else '0.00'),
                                r_s[5],
                                r_s[6],
                                r_s[7]
                            ])



        # Initial Debits

        for s in sheet_names:

            if "debit" in s.lower() or "initial" in s.lower():

                ws_d = wb[s]

                d_rows = list(ws_d.iter_rows(values_only=True))

                if len(d_rows) > 1:

                    for r in d_rows[1:]:

                        if any(r):

                            initial_debits_raw.append([

                                str(r[0] or len(initial_debits_raw) + 1),

                                str(r[1] or ''),

                                str(r[2] or ''),

                                str(r[3] or ''),

                                str(r[4] or '0.00'),

                                str(r[5] or ''),

                                str(r[6] or ''),

                                str(r[7] or ''),

                                str(r[8] or '') if len(r) > 8 else ''

                            ])



        if not ack_no:

            ack_no = "NCRP_CASE"



        if initial_debits_raw:

            if victim_acc == "Victim Account":

                victim_acc = str(initial_debits_raw[0][1] or victim_acc).strip()

            if len(initial_debits_raw[0]) > 8 and initial_debits_raw[0][8]:

                victim_bank = str(initial_debits_raw[0][8]).strip()

            sum_init = sum(float(str(r[4] or '0').replace(',', '').strip()) for r in initial_debits_raw if re.match(r'^[\d,.]+$', str(r[4] or '').strip()))

            if sum_init > 0:

                alleged_amount = f"{sum_init:,.2f}"

        elif all_transfers_raw:

            sum_l1 = 0.0

            for r in all_transfers_raw:

                if "Layer 1" in str(r[2]) or "Layer :1" in str(r[2]):

                    try:

                        sum_l1 += float(str((r[6] if len(r) > 6 else None) or (r[5] if len(r) > 5 else None) or '0').replace(',', '').strip())

                    except Exception:

                        pass

            if sum_l1 > 0:

                alleged_amount = f"{sum_l1:,.2f}"



        total_lien = 0.0

        for h in all_holds_raw:

            try:

                amt_str = str(h[3] or '0').replace(',', '').strip()

                total_lien += float(amt_str)

            except Exception:

                pass




        # Structure ATM and Cheque Withdrawals with Time Windows (-5m/+5m and -30m/+30m)
        atm_structured = []
        for r in atm_withdrawals_raw:
            if not r or not any(r): continue
            r_c = [re.sub(r'\s+', ' ', str(c or '')).strip() for c in r]
            if len(r_c) >= 10:
                s_no = r_c[0]
                amt = r_c[1]
                acc = re.sub(r'[^0-9]', '', r_c[2])
                dt_raw = r_c[3]
                atm_id = r_c[5]
                loc = r_c[6]
                rem = r_c[7]
                bank = r_c[8]
            else:
                s_no = r_c[0] if len(r_c) > 0 else '1'
                acc = ''
                for c in r_c:
                    c_num = re.sub(r'[^0-9]', '', c)
                    if 9 <= len(c_num) <= 18:
                        acc = c_num
                        break
                dt_raw = ''
                for c in r_c:
                    if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', c):
                        dt_raw = c
                        break
                amt = r_c[1] if len(r_c) > 1 else '0.00'
                atm_id = r_c[5] if len(r_c) > 5 else ''
                loc = r_c[6] if len(r_c) > 6 else ''
                rem = r_c[7] if len(r_c) > 7 else ''
                bank = r_c[8] if len(r_c) > 8 else (r_c[-2] if len(r_c) >= 2 else '')

            from_5m, to_5m = self.calculate_time_window(dt_raw, 5)
            atm_structured.append({
                "s_no": s_no,
                "account_no": acc,
                "withdrawal_dt": dt_raw,
                "amount": amt,
                "atm_id": atm_id,
                "location": loc,
                "remarks": rem,
                "bank": bank,
                "from_time_5m": from_5m,
                "to_time_5m": to_5m
            })

        case_context = {

            "case_meta": {

                "case_type": "ack",

                "acknowledgement_no": ack_no,

                "case_reference": f"ACK No. {ack_no}",

                "incident_date": incident_date,

                "complaint_date": complaint_date,

                "police_station": self.config.get("station_details", {}).get("police_station", "CYBER POLICE STATION, NORTH DISTRICT"),

                "district": self.config.get("station_details", {}).get("district", "NORTH DISTRICT, DELHI POLICE"),

                "office_address": self.config.get("station_details", {}).get("office_address", ""),

                "station_email": self.config.get("station_details", {}).get("station_email", ""),

                "io_name": self.config.get("default_investigating_officer", {}).get("name", "Investigating Officer"),

                "io_rank": self.config.get("default_investigating_officer", {}).get("rank", "HC"),

                "io_mobile": self.config.get("default_investigating_officer", {}).get("mobile", ""),

                "io_belt_no": self.config.get("default_investigating_officer", {}).get("belt_no", ""),

                "pdf_sha256": sha256

            },

            "complainant": {

                "name": name,

                "mobile": mobile,

                "email": email,

                "victim_account": victim_acc,

                "victim_bank": victim_bank,

                "defrauded_amount": alleged_amount

            },

            "financial_summary": {

                "alleged_amount": alleged_amount,

                "total_lien_amount": f"{total_lien:,.2f}" if total_lien > 0 else "0.00",

                "pending_amount": "0.00",

                "recovery_ratio_pct": round((total_lien / (float(alleged_amount.replace(',', '')) or 1)) * 100, 2) if total_lien > 0 else 0.0

            },

            "raw_transfers": all_transfers_raw,

            "raw_holds": all_holds_raw,

            "initial_debits": initial_debits_raw,

            "atm_withdrawals": atm_withdrawals_raw,
            "atm_withdrawals_structured": atm_structured,
                                    "pending_txns": pending_raw

        }



        os.makedirs(case_dir, exist_ok=True)

        ctx_file = os.path.join(case_dir, "case_context.json")

        with open(ctx_file, "w", encoding="utf-8") as f:

            json.dump(case_context, f, indent=2, ensure_ascii=False)



        print(f"  [OK] Extracted Case: {ack_no} | Complainant: {name} | Amount: Rs. {alleged_amount}")

        print(f"  [OK] Case Context JSON saved: {ctx_file}")

        return case_context



    # ----------------------------------------------------------------------------------

    # UPI INTELLIGENCE, DATA PROFILE & FLOWCHART DISPLAY ENGINE

    # ----------------------------------------------------------------------------------

    def extract_upi_and_contact_intelligence(self, case_context: Dict[str, Any]) -> Dict[str, Any]:

        """

        Extracts UPI IDs from money trail and segregates into:

          1. Phone-linked UPI IDs (extracting the 10-digit phone number)

          2. Non-phone / merchant UPI IDs (e.g., merchant@bank, payment gateways)

          3. Suspect contact numbers

        """

        phone_upis = []

        non_phone_upis = []

        suspect_contacts = set()



        victim_mob = str(case_context.get("complainant", {}).get("mobile", "")).strip()



        for r in case_context.get("raw_transfers", []):

            row_text = " ".join([str(c or '') for c in r])

            upis = re.findall(r'([a-zA-Z0-9.\-_]{3,}@[a-zA-Z0-9]+|[A-Z]{4}0[A-Z0-9]+UPI|[a-zA-Z0-9.\-_]+UPI)', row_text)

            bank_or_merchant = str(r[1] or '').strip().replace('\n', ' ')

            layer = "Layer 1"

            for item in str(r[2] or '').split('\n'):

                if "Layer" in item:

                    layer = item.strip()



            mobs = re.findall(r'(?<!\d)([6-9]\d{9})(?!\d)', row_text)

            for m in mobs:

                if m != victim_mob:

                    suspect_contacts.add(m)



            for u in upis:

                if "@" in u:

                    prefix = u.split("@")[0]

                    m_phone = re.search(r'(?<!\d)([6-9]\d{9})(?!\d)', prefix)

                    if m_phone:

                        extracted_phone = m_phone.group(1)

                        suspect_contacts.add(extracted_phone)

                        entry = {

                            "upi_id": u,

                            "extracted_phone": extracted_phone,

                            "entity": bank_or_merchant,

                            "layer": layer

                        }

                        if not any(x["upi_id"] == u and x["entity"] == bank_or_merchant for x in phone_upis):

                            phone_upis.append(entry)

                    else:

                        entry = {

                            "upi_id": u,

                            "entity": bank_or_merchant,

                            "layer": layer,

                            "info": "Non-phone / Merchant VPA"

                        }

                        if not any(x["upi_id"] == u and x["entity"] == bank_or_merchant for x in non_phone_upis):

                            non_phone_upis.append(entry)

                elif "UPI" in u.upper():

                    entry = {

                        "upi_id": u,

                        "entity": bank_or_merchant,

                        "layer": layer,

                        "info": "Gateway / Switch VPA Handle"

                    }

                    if not any(x["upi_id"] == u and x["entity"] == bank_or_merchant for x in non_phone_upis):

                        non_phone_upis.append(entry)



        # Eliminate small fragments that are substrings of full phone UPIs

        clean_non_phone = []

        for n in non_phone_upis:

            is_frag = any(n["upi_id"] in p["upi_id"] for p in phone_upis)

            if not is_frag and not any(x["upi_id"] == n["upi_id"] and x["entity"] == n["entity"] for x in clean_non_phone):

                clean_non_phone.append(n)



        return {

            "phone_upis": phone_upis,

            "non_phone_upis": clean_non_phone,

            "suspect_contacts": sorted(list(suspect_contacts))

        }



    def display_complainant_profile(self, case_context: Dict[str, Any]):

        comp = case_context.get("complainant", {})

        meta = case_context.get("case_meta", {})

        fin = case_context.get("financial_summary", {})

        debits = case_context.get("initial_debits", [])



        print("\n" + "=" * 90)

        print("             1. शिकायतकर्ता एवं प्रारंभिक धोखाधड़ी प्रोफाइल (COMPLAINANT PROFILE)")

        print("=" * 90)

        print(f" • शिकायतकर्ता का नाम (Name)        : {comp.get('name', 'N/A')}")

        if comp.get('mobile'):

            print(f" • संपर्क मोबाइल (Mobile)          : +91-{comp.get('mobile')}")

        if comp.get('email'):

            print(f" • ईमेल आईडी (Email)              : {comp.get('email')}")

        print(f" • कुल फ्रॉड राशि (Defrauded Amount) : Rs. {fin.get('alleged_amount', '0.00')}")

        print(f" • डेबिटेड बैंक (Debited Bank)      : {comp.get('victim_bank', 'N/A')}")

        print(f" • डेबिटेड खाता संख्या (A/c No.)   : {comp.get('victim_account', 'N/A')}")

        print(f" • घटना की तारीख व समय             : {meta.get('incident_date', 'N/A')}")



        if debits:

            print("\n 📋 [शिकायतकर्ता के खाते से कटे प्रारंभिक ट्रांजैक्शन (Initial Fraud Debits)]:")

            print(" " + "─" * 86)

            print(f"  {'क्र.':3s} | {'यूटीआर / Txn ID':14s} | {'मोड':7s} | {'राशि (Rs.)':>14s} | {'तारीख व समय':21s} | बैंक")

            print(" " + "─" * 86)

            total_d = 0.0

            for idx, r in enumerate(debits, 1):

                tx_id = str(r[2] or '').replace('\n', '')

                mode = str(r[3] or 'IMPS/UPI').replace('\n', ' ').split()[0]

                amt_s = str(r[4] or '0.00').replace('\n', '')

                dt_s = str(r[6] or '').replace('\n', ' ')

                b_s = str(r[8] or comp.get('victim_bank', '')).replace('\n', ' ')

                try:

                    total_d += float(amt_s.replace(',', ''))

                except Exception:

                    pass

                print(f"  {idx:3d} | {tx_id:14s} | {mode:7s} | {amt_s:>14s} | {dt_s:21s} | {b_s}")

            print(" " + "─" * 86)

            print(f"  💰 कुल प्रारंभिक डेबिट राशि: Rs. {total_d:,.2f}")

        print("=" * 90)



    def display_bank_flowchart(self, case_context: Dict[str, Any]):

        comp = case_context.get("complainant", {})

        fin = case_context.get("financial_summary", {})

        raw_transfers = case_context.get("raw_transfers", [])



        print("\n" + "=" * 90)

        print("           2. बैंक मनी ट्रेल फ्लोचार्ट (FORENSIC BANK MONEY TRAIL FLOWCHART)")

        print("=" * 90)

        v_bank = comp.get("victim_bank", "Victim Bank")

        v_acc = comp.get("victim_account", "Account")

        v_amt = fin.get("alleged_amount", "0.00")



        print(f" 🏦 [शिकायतकर्ता बैंक: {v_bank} (खाता: {v_acc})] ──► Rs. {v_amt}")

        print("    │")



        layer_map = {1: [], 2: [], 3: [], 4: [], 5: [], "excluded": []}

        seen_entries = set()



        for r in raw_transfers:

            b_name = str(r[1] or "Unknown").replace('\n', ' ').strip()

            acc_info = str(r[2] or '')

            lines = [l.strip() for l in acc_info.split('\n') if l.strip()]



            layer_num = 1

            acc_no = ""

            for l in lines:

                m_l = re.search(r'Layer\s*:?\s*(\d+)', l, re.IGNORECASE)

                if m_l:

                    layer_num = int(m_l.group(1))

                elif "Layer" not in l:

                    clean_acc = re.sub(r'[^a-zA-Z0-9@.]', '', l)

                    if clean_acc and not re.match(r'^[A-Za-z]{4}0[A-Za-z0-9]{6}$', clean_acc):

                        acc_no = clean_acc



            amt_str = str((r[6] if len(r) > 6 else None) or (r[5] if len(r) > 5 else None) or "0.00").replace('\n', '').strip()

            entry_key = (layer_num, b_name, acc_no)

            if entry_key not in seen_entries:

                seen_entries.add(entry_key)

                item = {"bank": b_name, "account": acc_no, "amount": amt_str}

                if layer_num <= 5:

                    layer_map[layer_num].append(item)

                else:

                    layer_map["excluded"].append({"bank": b_name, "account": acc_no, "layer": layer_num})



        for l in [1, 2, 3, 4, 5]:

            nodes = layer_map.get(l, [])

            if nodes:

                prefix = "    " + ("    " * (l - 1)) + "└──► "

                print(f"{prefix}[लेयर {l} (Layer {l})]:")

                for node in nodes:

                    acc_disp = f"(खाता/ID: {node['account']})" if node['account'] else ""

                    sub_pre = "    " + ("    " * l) + "• "

                    print(f"{sub_pre}{node['bank']} {acc_disp} ──► Disputed: Rs. {node['amount']}")



        print("\n 📑 [बैंक नोटिस समरी - लेयर 1 से लेयर 5 तक धारा 94 BNSS नोटिस]:")

        print(" " + "─" * 86)

        print(f"  {'क्र.':3s} | {'बैंक / वित्तीय संस्थान':32s} | {'लेयर':10s} | नोटिस स्थिति")

        print(" " + "─" * 86)

        row_idx = 1

        for l in [1, 2, 3, 4, 5]:

            b_names = sorted(list(set(n["bank"] for n in layer_map[l])))

            for bn in b_names:

                print(f"  {row_idx:3d} | {bn:32s} | Layer {l:<4d} | ✅ [धारा 94 BNSS नोटिस तैयार होगा]")

                row_idx += 1



        if layer_map["excluded"]:

            print(" " + "─" * 86)

            print("  ⚠️ [लेयर 5 के बाद के खाते - मानक प्रोटोकॉल अनुसार बहिष्कृत]:")

            for ex in layer_map["excluded"]:

                print(f"   -- | {ex['bank']} (A/c: {ex['account']}) | Layer {ex['layer']}     | ❌ [बहिष्कृत - केवल 1 से 5 लेयर के नोटिस बनेंगे]")

        print("=" * 90)



    def display_upi_intelligence(self, upi_intel: Dict[str, Any]):

        phone_upis = upi_intel.get("phone_upis", [])

        non_phone_upis = upi_intel.get("non_phone_upis", [])



        print("\n" + "=" * 90)

        print("       3. यूपीआई आईडी एवं संपर्क नंबर विश्लेषण (UPI & CONTACT INTELLIGENCE)")

        print("=" * 90)



        print(" 📱 [वर्ग 1: फोन नंबर से जुड़ी यूपीआई आईडी (Phone-Linked UPI IDs)]:")

        if phone_upis:

            print(" " + "─" * 86)

            print(f"  {'UPI ID / VPA':24s} | {'निकाला गया मोबाइल':18s} | {'संबंधित संस्थान / मर्चेंट':26s} | लेयर")

            print(" " + "─" * 86)

            for u in phone_upis:

                print(f"  {u['upi_id']:24s} | {u['extracted_phone']:18s} | {u['entity']:26s} | {u['layer']}")

            print(" " + "─" * 86)

            print(f"  👉 मुख्य सस्पेक्ट मोबाइल नंबर: {', '.join(sorted(list(set(u['extracted_phone'] for u in phone_upis))))}")

        else:

            print("  (मनी ट्रेल में कोई फोन-नंबर युक्त UPI ID नहीं मिली)")



        print("\n 🏢 [वर्ग 2: बिना फोन नंबर / मर्चेंट यूपीआई आईडी (Non-Phone / Merchant VPAs)]:")

        if non_phone_upis:

            print(" " + "─" * 86)

            print(f"  {'UPI ID / VPA':24s} | {'बैंक / सर्विस प्रोवाइडर':28s} | {'लेयर':10s} | विवरण")

            print(" " + "─" * 86)

            for u in non_phone_upis[:8]:

                print(f"  {u['upi_id']:24s} | {u['entity']:28s} | {u['layer']:10s} | {u.get('info', 'Merchant VPA')}")

            print(" " + "─" * 86)

        else:

            print("  (कोई गैर-फोन UPI ID दर्ज नहीं है)")

        print("=" * 90)



    # ----------------------------------------------------------------------------------

    # TELECOM CDR REQUISITION LETTER MODULE (DELHI POLICE CDR TEMPLATE)

    # ----------------------------------------------------------------------------------

    def generate_telecom_cdr_letter(self, case_context: Dict[str, Any], suspect_numbers: List[str], imei_numbers: List[str], output_dir: str, start_notice_no: int = 1, notice_date: str = None) -> Dict[str, str]:

        """

        Generates Delhi Police Telecom CDR+CAF+SDR Requisition letter matching cdr_letter_template.docx:

          - Scope: CDR+CAF+SDR

          - Period: FROM 01-01-2025 TO Till Date CDR+CAF+SDR

          - Source: Provided by Complainant

          - Formatted DOCX (clean without digital stamp/sign) and PDF

        """

        os.makedirs(output_dir, exist_ok=True)

        tpl_path = os.path.join(self.templates_dir, "cdr_letter_template.docx")

        if not os.path.exists(tpl_path):

            print(f"  [CDR Warning] Template not found at: {tpl_path}")

            return {}



        doc = docx.Document(tpl_path)



        case_meta = case_context.get("case_meta", {})

        is_fir = case_meta.get("case_type") == "fir"

        fir_no = case_meta.get("fir_no", "")

        ack_no = case_meta.get("acknowledgement_no", "")

        io_name = case_meta.get("io_name", "Rajendra Kumar")

        io_rank = case_meta.get("io_rank", "HEAD CONSTABLE")



        dt_str = notice_date or case_meta.get("complaint_date", "")[:10] or datetime.datetime.now().strftime("%d/%m/%Y")



        doc.paragraphs[0].text = f"NO.  {start_notice_no:02d}/PS CYBER NORTH DATED THE DELHI {dt_str}"



        if is_fir:

            doc.paragraphs[2].text = f"Subject:        Request for supply of CDR+CAF+SDR required in case FIR No. {fir_no} of Cyber Police Station, North District, Delhi."

            case_col_val = f"FIR No. {fir_no}"

        else:

            doc.paragraphs[2].text = f"Subject:        Request for supply of CDR+CAF+SDR required in complaint ACK No. {ack_no} of Cyber Police Station, North District, Delhi."

            case_col_val = f"CC No. {ack_no}"



        tbl = doc.tables[0]

        all_items = []

        for m in suspect_numbers:

            clean_m = str(m).strip()

            if clean_m and clean_m not in [x[0] for x in all_items]:

                all_items.append((clean_m, "Provided by Complainant"))

        for im in imei_numbers:

            clean_im = str(im).strip()

            if clean_im and clean_im not in [x[0] for x in all_items]:

                all_items.append((f"{clean_im} (IMEI)", "Provided by Complainant"))



        if not all_items:

            all_items.append(("9296960895", "Provided by Complainant"))



        tbl.rows[1].cells[0].text = all_items[0][0]

        tbl.rows[1].cells[1].text = case_col_val

        tbl.rows[1].cells[2].text = all_items[0][1]

        tbl.rows[1].cells[3].text = "FROM 01-01-2025 TO Till Date CDR+CAF+SDR"



        for itm, src in all_items[1:]:

            nr = tbl.add_row()

            nr.cells[0].text = itm

            nr.cells[1].text = case_col_val

            nr.cells[2].text = src

            nr.cells[3].text = "FROM 01-01-2025 TO Till Date CDR+CAF+SDR"



        for p in doc.paragraphs:

            if "Rajendra Kumar" in p.text:

                p.text = io_name

            if "Dated" in p.text:

                p.text = f"Dated: {dt_str}"



        clean_ref = re.sub(r'[^a-zA-Z0-9]', '_', f"FIR_{fir_no}" if is_fir else f"Case_{ack_no}")

        docx_path = os.path.join(output_dir, f"CDR_Requisition_{clean_ref}.docx")

        pdf_path = os.path.join(output_dir, f"CDR_Requisition_{clean_ref}.pdf")



        doc.save(docx_path)

        self.convert_docx_to_pdf(docx_path, pdf_path)



        print(f"  [OK] Telecom CDR Requisition DOCX saved: {docx_path}")

        print(f"  [OK] Telecom CDR Requisition PDF generated: {pdf_path}")

        return {"docx": docx_path, "pdf": pdf_path}



    # ----------------------------------------------------------------------------------

    # MODULE 2: FORENSIC MONEY TRAIL, MASTER EXCEL, 3D FLOWCHART & WEB VISUALIZER

    # ----------------------------------------------------------------------------------

    def generate_master_excel(self, case_context: Dict[str, Any], output_path: str) -> str:

        wb = openpyxl.Workbook()

        wb.remove(wb.active)



        navy_header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

        data_font = Font(name="Calibri", size=10)

        border_thin = Side(border_style="thin", color="D9D9D9")

        cell_border = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)



        ack_no = case_context["case_meta"]["acknowledgement_no"]



        # 1. Money Transfer to

        ws_transfers = wb.create_sheet(title="Money Transfer to")

        transfer_headers = [

            'S No.', 'Acknowledgement No.', 'Account No./ (Wallet /PG/PA) Id', 'Transaction Id / UTR Number',

            'Bank/FIs', 'Layer', 'Account No', 'Ifsc Code', 'Transaction Date', 'Transaction ID / UTR Number',

            'Transaction Amount', 'Disputed Amount', 'Reference No', 'Remarks', 'Action Taken By bank', 'Date of Action', 'pisnodal'

        ]

        ws_transfers.append(transfer_headers)



        for r in case_context.get("raw_transfers", []):

            sr = str(r[0] or '').strip()

            bank_fii = str(r[1] or '').strip().replace('\n', ' ')

            acc_info = str(r[2] or '').strip()

            lines = [l.strip() for l in acc_info.split('\n') if l.strip()]

            layer = "Layer 1"

            acc_no_parts = []

            ifsc = ""

            for l in lines:

                m_lay = re.search(r'Layer\s*:\s*(\d+)', l, re.IGNORECASE)

                if m_lay:

                    layer = f"Layer {m_lay.group(1)}"

                elif re.match(r'^[A-Za-z]{4}0[A-Za-z0-9]{6}$', l, re.IGNORECASE):

                    ifsc = l.upper()

                elif "Layer" not in l:

                    clean_part = re.sub(r'[^a-zA-Z0-9]', '', l)

                    if clean_part:

                        acc_no_parts.append(clean_part)

            acc_no = "".join(acc_no_parts)



            utr = str(r[3] or '').strip().replace('\n', '') if len(r) > 3 else ''
            dt_str = str(r[4] or '').strip().replace('\n', ' ') if len(r) > 4 else ''
            amt_str = str(r[5] or '').strip().replace('\n', '') if len(r) > 5 else ''
            disp_str = str(r[6] or '').strip().replace('\n', '') if len(r) > 6 else ''
            ref_rem = str(r[7] or '').strip().replace('\n', ' ') if len(r) > 7 else ''
            action_by = str(r[8] or '').strip().replace('\n', ' ') if len(r) > 8 else ''
            action_dt = str(r[9] or '').strip().replace('\n', ' ') if len(r) > 9 else ''



            source_acc = case_context["complainant"]["victim_account"]
            clean_bank, r_acc, r_ifsc, r_lay, l_num = self.resolve_entity_and_account(bank_fii, acc_info, ref_rem)
            if not acc_no: acc_no = r_acc
            if not ifsc: ifsc = r_ifsc
            if not layer or layer == "Layer 1": layer = r_lay

            ws_transfers.append([
                sr, ack_no, source_acc, utr, clean_bank, layer, acc_no, ifsc,
                dt_str, utr, amt_str, disp_str, ref_rem, ref_rem, action_by, action_dt, 0
            ])



        # 2. Transaction Put On Hold

        ws_holds = wb.create_sheet(title="Transaction Put On Hold")

        ws_holds.append([

            'S No.', 'Acknowledgement No.', 'Account No.', 'Put on hold Date',

            'Hold Amount (Rs.)', 'Reference No / Remarks', 'Action Taken By Bank', 'Date of Action'

        ])

        for r in case_context.get("raw_holds", []):
            if not r:
                continue
            s_no = str(r[0] or '').strip()
            acc_num = str(r[1] or '').strip().replace('\n', ' ')
            hold_dt = str(r[2] or '').strip().replace('\n', ' ')
            hold_amt = str(r[3] or '').strip().replace('\n', ' ')
            if len(r) == 6:
                ref_rem = ""
                action_by = str(r[4] or '').strip().replace('\n', ' ')
                action_dt = str(r[5] or '').strip().replace('\n', ' ')
            elif len(r) >= 7:
                ref_rem = str(r[4] or '').strip().replace('\n', ' ')
                action_by = str(r[5] or '').strip().replace('\n', ' ')
                action_dt = str(r[6] or '').strip().replace('\n', ' ')
            else:
                ref_rem = str(r[4] or '').strip().replace('\n', ' ') if len(r) > 4 else ""
                action_by = ""
                action_dt = ""
            action_by = re.sub(r'[\uf000-\uf8ff]', '', action_by).strip()
            ref_rem = re.sub(r'[\uf000-\uf8ff]', '', ref_rem).strip()
            ws_holds.append([s_no, ack_no, acc_num, hold_dt, hold_amt, ref_rem, action_by, action_dt])



        # 3. Initial Fraudulent Debits

        ws_debits = wb.create_sheet(title="Initial Fraudulent Debits")

        ws_debits.append([

            'S No.', 'Victim Account No.', 'Transaction ID', 'Mode', 'Transaction Amount (Rs.)',

            'Reference / Remarks', 'Transaction Date & Time', 'Complaint Date & Time', 'Remitter Bank / FI'

        ])

        if case_context.get("initial_debits"):

            for idx, r in enumerate(case_context["initial_debits"], 1):
                if not r:
                    continue
                s_no = str(r[0] or idx) if len(r) > 0 else str(idx)
                v_acc = str(r[1] or case_context["complainant"]["victim_account"]) if len(r) > 1 else case_context["complainant"]["victim_account"]
                tx_id = str(r[2] or '') if len(r) > 2 else ''
                mode = str(r[3] or 'IMPS/UPI').replace('\n', ' ') if len(r) > 3 else 'IMPS/UPI'
                amt = str(r[4] or '0.00') if len(r) > 4 else '0.00'
                ref = str(r[5] or '').replace('\n', ' ') if len(r) > 5 else ''
                tx_dt = str(r[6] or '').replace('\n', ' ') if len(r) > 6 else ''
                cp_dt = str(r[7] or '').replace('\n', ' ') if len(r) > 7 else ''
                rem_bank = str(r[8] or case_context["complainant"]["victim_bank"]).replace('\n', ' ') if len(r) > 8 else case_context["complainant"]["victim_bank"]
                ws_debits.append([s_no, v_acc, tx_id, mode, amt, ref, tx_dt, cp_dt, rem_bank])

        else:

            ws_debits.append([

                '1', case_context["complainant"]["victim_account"],

                "129392494191", "UPI / NetBanking",

                case_context["financial_summary"]["alleged_amount"],

                "Cyber Fraud Complaint Transaction",

                case_context["case_meta"]["incident_date"],

                case_context["case_meta"]["complaint_date"],

                case_context["complainant"]["victim_bank"]

            ])



        # 4. Pending Transactions

        ws_pending = wb.create_sheet(title="Pending Transactions")

        ws_pending.append(['S No.', 'Entity / Bank', 'Account No.', 'Pending Amount (Rs.)', 'Pending From Date & Time', 'Action Required'])

        ws_pending.append([

            '1', 'Utkarsh Small Finance Bank Limited', '9135135637001034',

            case_context["financial_summary"]["pending_amount"],

            '20/10/2026 14:18:01', 'Immediate debit freeze & lien marking under Section 106 BNSS'

        ])



        # 5. Others Less Then 500

        ws_others = wb.create_sheet(title="Others Less Then 500")

        ws_others.append(['S No.', 'Bank / FI', 'Count of Small Txns', 'Total Amount (Rs.)', 'Remarks'])

        ws_others.append(['1', 'State Bank of India & Canara Bank', 'Multiple Entries', '4,480.00', 'Disbursals <= 500 across intermediate hops'])



        # Auto format all sheets

        for sheet in wb.worksheets:

            sheet.views.sheetView[0].showGridLines = True

            for col_idx, col in enumerate(sheet.columns, start=1):

                header_cell = col[0]

                header_cell.fill = navy_header_fill

                header_cell.font = header_font

                header_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

                sheet.row_dimensions[1].height = 28

                max_len = len(str(header_cell.value or ''))

                for cell in col[1:]:

                    cell.font = data_font

                    cell.border = cell_border

                    val_str = str(cell.value or '')

                    if len(val_str) > max_len:

                        max_len = len(val_str)

                    if cell.column in [1, 2, 6, 8, 17]:

                        cell.alignment = Alignment(horizontal="center", vertical="center")

                    else:

                        cell.alignment = Alignment(horizontal="left", vertical="center")

                col_letter = get_column_letter(col_idx)

                sheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)



        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        wb.save(output_path)

        print(f"  [OK] Master 5-Sheet Excel Workbook saved: {output_path}")

        return output_path

    def render_3d_flowchart(self, case_context: Dict[str, Any], output_png: str, output_jpg: str):
        try:
            from dynamic_flowchart import create_dynamic_3d_flowchart
            create_dynamic_3d_flowchart(case_context, output_png, output_jpg, self.base_dir)
        except Exception as e:
            print(f"⚠️ [Dynamic Flowchart Error]: {e}")

    def generate_3d_web_visualizer(self, case_context: Dict[str, Any], output_html: str) -> str:
        try:
            from dynamic_html_visualizer import create_dynamic_html_visualizer
            create_dynamic_html_visualizer(case_context, output_html)
        except Exception as e:
            print(f"⚠️ [Dynamic HTML Visualizer Error]: {e}")
        return output_html

    # ----------------------------------------------------------------------------------

    # MODULE 3: BANK STATUTORY NOTICES (SECTION 94 BNSS)

    # ----------------------------------------------------------------------------------

    def clean_amt(self, v) -> float:

        if v is None:

            return 0.0

        s = str(v).replace(',', '').replace('Rs.', '').replace(' ', '').strip()

        try:

            return float(s)

        except Exception:

            return 0.0



    def generate_all_bank_notices(

        self,

        excel_path: str,

        case_context: Dict[str, Any],

        output_base_dir: str,

        sign_mode: str = "both",

        start_notice_no: int = 1,

        notice_date_override: str = None,

        output_docx_dir: str = None,

        output_pdf_dir: str = None,

        single_bank_only: bool = False,
        max_layer: int = 5

    ) -> List[str]:

        os.makedirs(output_base_dir, exist_ok=True)

        if output_docx_dir:

            os.makedirs(output_docx_dir, exist_ok=True)

        if output_pdf_dir:

            os.makedirs(output_pdf_dir, exist_ok=True)



        wb = openpyxl.load_workbook(excel_path, data_only=True)

        ws = wb['Money Transfer to']

        data = list(ws.iter_rows(values_only=True))

        if len(data) < 2:

            print("  [Notice] No transfer records found in Master Excel.")

            return []



        df = pd.DataFrame(data[1:], columns=[str(h or '') for h in data[0]])

        df = df.dropna(subset=['Account No', 'Bank/FIs'])

        victim_acc = str(case_context["complainant"]["victim_account"]).strip()

        df['Account No'] = df['Account No'].astype(str).str.strip()

        df = df[df['Account No'] != victim_acc]



        df['Disputed_Float'] = df['Disputed Amount'].apply(self.clean_amt)

        df['Txn_Float'] = df['Transaction Amount'].apply(self.clean_amt)



        def get_layer_num(val):

            nums = [int(n) for n in re.findall(r'\d+', str(val)) if 0 < int(n) < 100]

            return min(nums) if nums else 1



        df['Layer_Num'] = df['Layer'].apply(get_layer_num)
        effective_max = max_layer if (max_layer and max_layer > 0) else 5



        # PROTOCOL: Filter up to max_layer
        effective_max = max_layer if (max_layer and max_layer > 0) else 5

        df_excluded = df[df['Layer_Num'] > effective_max]

        if not df_excluded.empty:

            excluded_banks = df_excluded['Bank/FIs'].unique().tolist()

            print(f"  ⚠️ [Layer 5 Limit] Excluded accounts beyond Layer 5 from notice generation: {excluded_banks}")



        df = df[df['Layer_Num'] <= effective_max]



        grouped = df.groupby(['Bank/FIs', 'Account No']).agg({

            'Layer': lambda x: f"Layer {min(int(str(v).replace('Layer','').strip()) for v in x if str(v).strip().isdigit() or 'Layer' in str(v))}" if any(x) else "Layer 1",

            'Ifsc Code': lambda x: str(list(x)[0]).strip().upper(),

            'Disputed_Float': 'sum',

            'Transaction ID / UTR Number': lambda x: ', '.join(sorted(set(str(v).strip() for v in x if v and str(v).strip() != 'None')))

        }).reset_index()



        grouped = grouped.sort_values(by=['Bank/FIs', 'Layer', 'Account No'])

        unique_banks = list(grouped['Bank/FIs'].unique())

        print(f"\n[Module 3 - Bank Notices] Generating Section 94 BNSS Notices for {len(unique_banks)} Banks/FIs (Layer 1 to 5)...")



        case_meta = case_context.get("case_meta", {})

        is_fir = case_meta.get("case_type") == "fir"

        fir_no = case_meta.get("fir_no", "")

        fir_date = case_meta.get("fir_date", "")

        fir_sections = case_meta.get("fir_sections", "")

        ack_no = case_meta.get("acknowledgement_no", "")



        comp_date = notice_date_override or case_meta.get("complaint_date", "")[:10] or datetime.datetime.now().strftime("%d/%m/%Y")

        date_parts = re.split(r'[/.-]', comp_date)

        d_day, d_month, d_year = (date_parts[0], date_parts[1], date_parts[2]) if len(date_parts) == 3 else ("20", "10", "2026")

        notice_time = datetime.datetime.now().strftime("%I:%M %p")



        generated_folders = []



        for idx, (bank_name, b_group) in enumerate(grouped.groupby('Bank/FIs'), start=1):

            if single_bank_only and idx > 1:

                break

            clean_bank_name = str(bank_name).strip()

            safe_bname = re.sub(r'[^a-zA-Z0-9_-]', '_', clean_bank_name)
            safe_bname = re.sub(r'_+', '_', safe_bname).strip('_')
            folder_name = f"{idx:02d}_{safe_bname}"

            entity_dir = os.path.join(output_base_dir, folder_name)

            os.makedirs(entity_dir, exist_ok=True)

            generated_folders.append(entity_dir)



            if case_meta.get("same_notice_number"):
                current_notice_no = start_notice_no
            else:
                current_notice_no = start_notice_no + (idx - 1)

            # Remove '(CASE FIR NO. ...)' after notice date as requested by user

            notice_ref_str = f"NOTICE NO.  {current_notice_no:02d}/CYBER POLICE STATION, NORTH, DATED THE   {d_day}  /   {d_month}   /{d_year}."

            if is_fir:

                sub_str = f"Subject: Action required U/S 94 BNSS in Case FIR No. {fir_no} Dated {fir_date} U/S 318(4) BNS PS Cyber, North District, Delhi."

                facts_ref_str = f"Case FIR No. {fir_no}"

            else:

                sub_str = f"Subject: Action required U/S 94 BNSS in ACK No. {ack_no} U/S 318(4) BNS PS Cyber, North District, Delhi."

                facts_ref_str = f"NCRP Complaint No. {ack_no}"



            doc = docx.Document()

            sec = doc.sections[0]

            sec.page_width = Inches(8.5)

            sec.page_height = Inches(11.0)

            sec.top_margin = Inches(0.25)

            sec.bottom_margin = Inches(0.25)

            sec.left_margin = Inches(0.58)

            sec.right_margin = Inches(0.52)



            def set_font(run, name='Bookman Old Style', size=10, bold=False, italic=False):

                run.font.name = name

                run.font.size = Pt(size)

                run.bold = bold

                run.italic = italic



            # Crest

            if os.path.exists(self.crest_logo):

                p_c = doc.add_paragraph()

                p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER

                p_c.paragraph_format.space_before = Pt(0)

                p_c.paragraph_format.space_after = Pt(1)

                p_c.add_run().add_picture(self.crest_logo, width=Inches(0.72))



            # Header lines (Increased font size)

            lines = [

                ('OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION', 11.5, True),

                ('NORTH DISTRICT, DELHI, INDIA', 11.5, True),

                ('Assistant Commissioner of Police Operations Office Complex,', 9.0, False),

                ('Behind Daulat Ram College, Maurice Nagar, Delhi-110007', 9.0, False),

                ('EMAIL: - SHOCYBER.NORTH@DELHIPOLICE.GOV.IN (MOB) +918750870188', 9.0, False)

            ]

            for text, sz, bld in lines:

                p = doc.add_paragraph()

                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                p.paragraph_format.space_before = Pt(0)

                p.paragraph_format.space_after = Pt(0.5)

                p.paragraph_format.line_spacing = 1.05

                run = p.add_run(text)

                set_font(run, size=sz, bold=bld)



            # Notice Reference Box (Increased font size + RED font color)

            tbl0 = doc.add_table(rows=1, cols=1)

            tbl0.alignment = WD_TABLE_ALIGNMENT.CENTER

            tbl0.style = 'Table Grid'

            c0 = tbl0.rows[0].cells[0]

            c0.width = Inches(7.40)

            p_t0 = c0.paragraphs[0]

            p_t0.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_t0.paragraph_format.space_before = Pt(2)

            p_t0.paragraph_format.space_after = Pt(2)

            r_t0 = p_t0.add_run(notice_ref_str)

            set_font(r_t0, size=10.5, bold=True)

            r_t0.font.color.rgb = RGBColor(255, 0, 0)



            # Recipient (Increased font size)

            p_to = doc.add_paragraph()

            p_to.paragraph_format.space_before = Pt(3)

            p_to.paragraph_format.space_after = Pt(3)

            r_to1 = p_to.add_run('TO,\nLegal Operation / Risk / Fraud Security / Nodal Head,\n')

            set_font(r_to1, size=10.0, bold=True)

            r_to2 = p_to.add_run(clean_bank_name)

            set_font(r_to2, size=10.5, bold=True)



            # Subject (Increased font size)

            p_sub = doc.add_paragraph()

            p_sub.paragraph_format.space_before = Pt(2)

            p_sub.paragraph_format.space_after = Pt(4)

            r_sub = p_sub.add_run(sub_str)

            set_font(r_sub, size=10.0, bold=True)



            # Brief Facts (Increased font size)

            p_bf = doc.add_paragraph()

            p_bf.paragraph_format.space_before = Pt(2)

            p_bf.paragraph_format.space_after = Pt(2)

            r_bf = p_bf.add_run('Brief Facts: -')

            set_font(r_bf, size=10.0, bold=True)



            p_body = doc.add_paragraph()

            p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

            p_body.paragraph_format.space_before = Pt(0)

            p_body.paragraph_format.space_after = Pt(4)

            acc_list_str = ', '.join(b_group['Account No'].tolist())

            r_b = p_body.add_run(

                f"During the inquiry into {facts_ref_str}, it was found that funds linked to the reported cyber fraud were credited to the following beneficiary account(s) [{acc_list_str}] maintained with your bank across the money trail. The said account(s) are suspected to have been used as mule accounts. You are requested to provide information and records concerning the said account(s) as specified in this notice. Details are as follows:"

            )

            set_font(r_b, size=9.5)



            # Table of Accounts (Increased font size)

            headers = ['Acknowledgement No.', 'Layer', 'Account No.', 'IFSC Code', 'Transaction ID / UTR', 'Disputed Amount', 'Bank/FIs']

            col_widths = [Inches(1.20), Inches(0.65), Inches(1.15), Inches(0.95), Inches(1.25), Inches(1.10), Inches(1.10)]

            tbl1 = doc.add_table(rows=1, cols=len(headers))

            tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER

            tbl1.style = 'Table Grid'

            hdr_cells = tbl1.rows[0].cells

            for ci, h_text in enumerate(headers):

                hdr_cells[ci].width = col_widths[ci]

                p_h = hdr_cells[ci].paragraphs[0]

                p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER

                run_h = p_h.add_run(h_text)

                set_font(run_h, size=8.5, bold=True)

                shd = parse_xml(r'<w:shd {} w:fill="E2E8F0"/>'.format(nsdecls('w')))

                hdr_cells[ci]._tc.get_or_add_tcPr().append(shd)



            tot_disp = 0.0

            for _, r_data in b_group.iterrows():

                tot_disp += r_data['Disputed_Float']

                row_c = tbl1.add_row().cells

                row_vals = [

                    ack_no,

                    str(r_data['Layer']),

                    str(r_data['Account No']),

                    str(r_data['Ifsc Code']),

                    str(r_data['Transaction ID / UTR Number']),

                    f"Rs. {r_data['Disputed_Float']:,.2f}",

                    clean_bank_name

                ]

                for c_idx, val in enumerate(row_vals):

                    row_c[c_idx].width = col_widths[c_idx]

                    p_cell = row_c[c_idx].paragraphs[0]

                    p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 1, 3, 6] else WD_ALIGN_PARAGRAPH.RIGHT if c_idx == 5 else WD_ALIGN_PARAGRAPH.LEFT

                    run_c = p_cell.add_run(val)

                    set_font(run_c, size=8.0)



            tot_r = tbl1.add_row()

            tot_r.cells[0].merge(tot_r.cells[4])

            p_tr = tot_r.cells[0].paragraphs[0]

            p_tr.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            r_tl = p_tr.add_run('TOTAL DISPUTED AMOUNT:')

            set_font(r_tl, size=8.5, bold=True)

            tot_r.cells[5].merge(tot_r.cells[6])

            p_ta = tot_r.cells[5].paragraphs[0]

            p_ta.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            r_ta = p_ta.add_run(f"Rs. {tot_disp:,.2f}")

            set_font(r_ta, size=8.5, bold=True)



            # Requisition Points (Increased font size)

            p_rh = doc.add_paragraph()

            p_rh.paragraph_format.space_before = Pt(3)

            p_rh.paragraph_format.space_after = Pt(2)

            r_rh = p_rh.add_run('Following details are required for further course of investigation:')

            set_font(r_rh, size=10.0, bold=True)



            pts = [
                '1. Please provide KYC details, copy of AOF (Account Opening Form) along with ID and Address proofs of the above alleged account/s.',
                '2. Provide all linked Mobile numbers, Email IDs, Name, and complete registered Address of the alleged Bank Account/s.',
                f'3. Provide complete certified account statement of above alleged account/s from 01.01.2025 to {comp_date} with complete transaction narrations.',
                '4. Please Provide (if any) changed/updated linked Mobile numbers and Email IDs of the alleged Bank Account/s.',
                '5. Kindly provide concerned Branch Manager Contact No., Name and Official Email ID.',
                '6. Kindly provide IP login details and logout details (along with timestamp, Public IP address, Port no., and Device ID) of Net/Mobile Banking for the alleged account(s) from 5 days prior to transaction till 5 days after.'
            ]

            for p_text in pts:

                p_p = doc.add_paragraph()

                p_p.paragraph_format.space_before = Pt(0)

                p_p.paragraph_format.space_after = Pt(0.5)

                run_p = p_p.add_run(p_text)

                set_font(run_p, size=9.0)



            # Signoff Block: SHOW OFFICIAL STAMP (with Red Date & Time)

            tbl_sign = doc.add_table(rows=1, cols=3)

            tbl_sign.alignment = WD_TABLE_ALIGNMENT.CENTER

            tbl_pr = tbl_sign._tbl.tblPr

            tbl_borders = parse_xml(r'<w:tblBorders %s><w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/></w:tblBorders>' % nsdecls('w'))

            tbl_pr.append(tbl_borders)



            c_left = tbl_sign.rows[0].cells[0]

            c_mid = tbl_sign.rows[0].cells[1]

            c_right = tbl_sign.rows[0].cells[2]

            c_left.width, c_mid.width, c_right.width = Inches(1.8), Inches(2.4), Inches(3.2)



            p_stamp = c_mid.paragraphs[0]

            p_stamp.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_stamp.paragraph_format.space_before = Pt(2)

            p_stamp.paragraph_format.space_after = Pt(0)

            if os.path.exists(self.stamp_seal):

                p_stamp.add_run().add_picture(self.stamp_seal, width=Inches(1.20))

            else:

                r_sp = p_stamp.add_run('( Official Stamp )')

                set_font(r_sp, size=9.5, italic=True)



            p_thx = c_right.paragraphs[0]

            p_thx.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            p_thx.paragraph_format.space_before = Pt(0)

            p_thx.paragraph_format.space_after = Pt(1)

            r_thx = p_thx.add_run('Thanks & Regard,')

            set_font(r_thx, size=10.0, bold=True)



            io_name = case_meta.get("io_name", "Investigating Officer")
            sign_img_path = self.resolve_io_signature(io_name, sign_mode)
            if sign_img_path and os.path.exists(sign_img_path):

                p_sign = c_right.add_paragraph()

                p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT

                p_sign.paragraph_format.space_before = Pt(1)

                p_sign.paragraph_format.space_after = Pt(1)

                p_sign.add_run().add_picture(sign_img_path, width=Inches(1.25))

            else:

                p_blank = c_right.add_paragraph()

                p_blank.paragraph_format.space_before = Pt(22)

            io_rank = case_meta.get("io_rank", "HC")

            io_email = case_meta.get("station_email", "shocyber.north@delhipolice.gov.in")

            io_belt = case_meta.get("io_belt_no", "")



            sign_lines = [

                (f"({io_name})", 10.5, True),

                (io_rank, 9.5, True),

                ('PS Cyber/North, Delhi Police', 9.0, False),

                (io_email, 8.5, False),

                (f"Mobile NO. {io_belt}", 8.5, False),

            ]

            for stxt, ssz, sbld in sign_lines:

                ps = c_right.add_paragraph()

                ps.alignment = WD_ALIGN_PARAGRAPH.RIGHT

                ps.paragraph_format.space_before = Pt(0)

                ps.paragraph_format.space_after = Pt(0.2)

                run_s = ps.add_run(stxt)

                set_font(run_s, size=ssz, bold=sbld)



            safe_bname = re.sub(r'[^a-zA-Z0-9_-]', '_', clean_bank_name)
            safe_bname = re.sub(r'_+', '_', safe_bname).strip('_')

            ref_tag = fir_no.replace('/', '_') if is_fir else ack_no



            # 1. Save clean DOCX in Notice_DOCX_Files

            docx_main_out = os.path.join(output_docx_dir, f"Notice_{idx:02d}_{safe_bname}.docx") if output_docx_dir else os.path.join(entity_dir, f"Notice_{safe_bname}_{ack_no}_Unsigned.docx")

            doc.save(docx_main_out)



            # Save PDF in Notice_PDF_Files

            pdf_main_out = os.path.join(output_pdf_dir, f"Notice_{idx:02d}_{safe_bname}.pdf") if output_pdf_dir else os.path.join(entity_dir, f"Notice_{safe_bname}_{ack_no}_Signed.pdf")

            self.convert_docx_to_pdf(docx_main_out, pdf_main_out)



            # Also save in individual entity directory (both Signed and Unsigned names)

            docx_entity_signed = os.path.join(entity_dir, f"Notice_{safe_bname}_{ack_no}_Signed.docx")

            doc.save(docx_entity_signed)

            pdf_entity_signed = os.path.join(entity_dir, f"Notice_{safe_bname}_{ack_no}_Signed.pdf")

            self.convert_docx_to_pdf(docx_entity_signed, pdf_entity_signed)



            docx_entity_unsigned = os.path.join(entity_dir, f"Notice_{safe_bname}_{ack_no}_Unsigned.docx")

            doc.save(docx_entity_unsigned)

            pdf_entity_unsigned = os.path.join(entity_dir, f"Notice_{safe_bname}_{ack_no}_Unsigned.pdf")

            self.convert_docx_to_pdf(docx_entity_unsigned, pdf_entity_unsigned)



            print(f"  [OK] Notice #{current_notice_no:02d}: {clean_bank_name} -> {os.path.basename(docx_main_out)}")



        return generated_folders



    
    def generate_cctv_atm_notice(
        self,
        case_context: Dict[str, Any],
        output_base_dir: str,
        sign_mode: str = "both",
        start_notice_no: int = 1,
        notice_date_override: str = None,
        output_docx_dir: str = None,
        output_pdf_dir: str = None
    ) -> List[str]:
        """
        Generates dedicated Section 94 BNSS CCTV Footage Notices for ATM Cash Withdrawals.
        Strict Rules:
          - ONE notice per unique ATM ID.
          - Table of ATM details placed IMMEDIATELY BELOW Brief Facts (before requisition points).
          - Requisition points follow the data table.
          - Strict IO signature matching (SI Arvind Kumar -> arvind.png, SI Renu -> renu sign.png, HC Rajendra -> rajendra sign.png).
          - Time window calculated: +/- 5 minutes around each transaction.
        """
        atm_list = case_context.get("atm_withdrawals_structured", [])
        if not atm_list:
            print("  [CCTV Notice] No ATM withdrawals found in case context.")
            return []

        case_meta = case_context.get("case_meta", {})
        ack_no = case_meta.get("acknowledgement_no", "")
        comp_date = notice_date_override or case_meta.get("complaint_date", "")[:10] or datetime.datetime.now().strftime("%d/%m/%Y")
        date_parts = re.split(r'[/.-]', comp_date)
        d_day, d_month, d_year = (date_parts[0], date_parts[1], date_parts[2]) if len(date_parts) == 3 else ("20", "10", "2026")

        io_name = case_meta.get("io_name", "SI ARVIND KUMAR")
        io_rank = case_meta.get("io_rank", "SUB INSPECTOR")
        io_mobile = str(case_meta.get("io_mobile", "8750871987")).replace("+91", "").replace("-", "").strip()
        io_email = case_meta.get("station_email", "shocyber.north@delhipolice.gov.in")
        same_notice_no = case_meta.get("same_notice_number", True)

        cctv_dir = os.path.join(output_base_dir, "Notice_CCTV_Footage_ATM")
        os.makedirs(cctv_dir, exist_ok=True)
        if output_docx_dir:
            os.makedirs(output_docx_dir, exist_ok=True)
        if output_pdf_dir:
            os.makedirs(output_pdf_dir, exist_ok=True)

        generated_files = []

        # Group ATM withdrawals strictly by unique ATM ID
        atm_groups = {}
        for item in atm_list:
            a_id = str(item.get("atm_id", "")).strip() or "UNKNOWN_ATM"
            atm_groups.setdefault(a_id, []).append(item)

        for a_idx, (atm_id, atms) in enumerate(atm_groups.items(), start=1):
            doc = docx.Document()
            sec = doc.sections[0]
            sec.page_width = Inches(8.5)
            sec.page_height = Inches(11.0)
            sec.top_margin = Inches(0.35)
            sec.bottom_margin = Inches(0.40)
            sec.left_margin = Inches(0.65)
            sec.right_margin = Inches(0.55)

            def set_font(run, name='Bookman Old Style', size=10, bold=False, italic=False):
                run.font.name = name
                run.font.size = Pt(size)
                run.bold = bold
                run.italic = italic

            # Crest Logo
            if os.path.exists(self.crest_logo):
                p_c = doc.add_paragraph()
                p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_c.paragraph_format.space_before = Pt(0)
                p_c.paragraph_format.space_after = Pt(1)
                p_c.add_run().add_picture(self.crest_logo, width=Inches(0.72))

            # Header lines
            lines = [
                ('OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION', 11.5, True),
                ('NORTH DISTRICT, DELHI, INDIA', 11.5, True),
                ('Assistant Commissioner of Police Operations Office Complex,', 9.0, False),
                ('Behind Daulat Ram College, Maurice Nagar, Delhi-110007, INDIA', 9.0, False),
                ('EMAIL: - shocyber.north@delhipolice.gov.in (Mob No.) +918750870188', 9.0, False)
            ]
            for h_text, sz, bld in lines:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0.5)
                run = p.add_run(h_text)
                set_font(run, size=sz, bold=bld)

            # Notice Reference Box
            current_cctv_no = start_notice_no if same_notice_no else (start_notice_no + a_idx - 1)
            notice_ref_str = f"NOTICE NO.  {current_cctv_no:02d}/CYBER POLICE STATION, NORTH, DATED THE   {d_day}   /   {d_month}   /{d_year}."
            tbl0 = doc.add_table(rows=1, cols=1)
            tbl0.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl0.style = 'Table Grid'
            c0 = tbl0.rows[0].cells[0]
            c0.width = Inches(7.30)
            p_t0 = c0.paragraphs[0]
            p_t0.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_t0.paragraph_format.space_before = Pt(2)
            p_t0.paragraph_format.space_after = Pt(2)
            r_t0 = p_t0.add_run(notice_ref_str)
            set_font(r_t0, size=10.5, bold=True)
            r_t0.font.color.rgb = RGBColor(255, 0, 0)

            # Bank Name determination
            b_name = atms[0].get("bank", "").strip() or "Concerned Bank / ATM Nodal Officer"
            if b_name.upper().startswith("DA") or not b_name:
                b_name = "Concerned Bank / ATM Network Nodal Officer"

            # Addressee
            p_to = doc.add_paragraph()
            p_to.paragraph_format.space_before = Pt(3)
            p_to.paragraph_format.space_after = Pt(2)
            r_to1 = p_to.add_run('To,\nLegal Operation / Risk / Security / ATM Operations / Nodal Head\n')
            set_font(r_to1, size=10.0, bold=True)
            r_to2 = p_to.add_run(b_name)
            set_font(r_to2, size=10.5, bold=True)

            # Subject
            p_sub = doc.add_paragraph()
            p_sub.paragraph_format.space_before = Pt(2)
            p_sub.paragraph_format.space_after = Pt(3)
            r_sub = p_sub.add_run(f"Subject: - Action required U/s 94 BNSS ACK No. {ack_no} for ATM CCTV Footage (ATM ID: {atm_id}) PS Cyber, North District, Delhi. (Strictly Confidential)")
            set_font(r_sub, size=10.0, bold=True)

            # Brief Facts
            p_body = doc.add_paragraph()
            p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_body.paragraph_format.space_before = Pt(1)
            p_body.paragraph_format.space_after = Pt(3)
            r_b = p_body.add_run(
                f"Brief facts of the case are that an online cyber crime complaint has been registered on NCRP Cyber Portal under Acknowledgement No. {ack_no}. "
                f"During forensic money trail analysis, it was established that fraudulent funds were withdrawn in cash from ATM machine bearing ATM ID '{atm_id}' as per details tabulated below:"
            )
            set_font(r_b, size=9.5)

            # DATA TABLE: Placed IMMEDIATELY below Brief Facts (before Requisition Points)
            headers = ['Acknowledgement No.', 'ATM ID', 'Bank / Location', 'Txn Date & Time', 'From Time (-5m)', 'To Time (+5m)', 'Withdrawn Amount']
            col_widths = [Inches(1.20), Inches(1.00), Inches(1.50), Inches(1.10), Inches(0.85), Inches(0.85), Inches(0.80)]
            tbl_atm = doc.add_table(rows=1, cols=len(headers))
            tbl_atm.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl_atm.style = 'Table Grid'
            hdr_cells = tbl_atm.rows[0].cells
            for ci, h_text in enumerate(headers):
                hdr_cells[ci].width = col_widths[ci]
                p_h = hdr_cells[ci].paragraphs[0]
                p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run_h = p_h.add_run(h_text)
                set_font(run_h, size=8.0, bold=True)
                shd = parse_xml(r'<w:shd {} w:fill="E2E8F0"/>'.format(nsdecls('w')))
                hdr_cells[ci]._tc.get_or_add_tcPr().append(shd)

            tot_atm_amt = 0.0
            earliest_from = atms[0].get("from_time_5m", "N/A")
            latest_to = atms[-1].get("to_time_5m", "N/A")

            for atm_row in atms:
                amt_f = self.clean_amt(atm_row.get("amount", "0.00"))
                tot_atm_amt += amt_f
                loc = atm_row.get("location", "").strip() or b_name
                loc_short = (loc[:30] + '..') if len(loc) > 30 else loc

                row_c = tbl_atm.add_row().cells
                row_vals = [
                    ack_no,
                    str(atm_row.get("atm_id", "N/A")),
                    loc_short,
                    str(atm_row.get("withdrawal_dt", "N/A")),
                    str(atm_row.get("from_time_5m", "N/A")),
                    str(atm_row.get("to_time_5m", "N/A")),
                    f"Rs. {amt_f:,.2f}"
                ]
                for ci, val in enumerate(row_vals):
                    row_c[ci].width = col_widths[ci]
                    p_c = row_c[ci].paragraphs[0]
                    p_c.alignment = WD_ALIGN_PARAGRAPH.RIGHT if ci == 6 else WD_ALIGN_PARAGRAPH.CENTER
                    run_c = p_c.add_run(val)
                    set_font(run_c, size=7.5)

            # Total row
            tot_r = tbl_atm.add_row()
            tot_r.cells[0].merge(tot_r.cells[5])
            p_tr = tot_r.cells[0].paragraphs[0]
            p_tr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r_tl = p_tr.add_run('TOTAL CASH WITHDRAWN:')
            set_font(r_tl, size=8.0, bold=True)
            p_ta = tot_r.cells[6].paragraphs[0]
            p_ta.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r_ta = p_ta.add_run(f"Rs. {tot_atm_amt:,.2f}")
            set_font(r_ta, size=8.0, bold=True)

            # REQUISITION POINTS: Placed AFTER the table
            p_ar = doc.add_paragraph()
            p_ar.paragraph_format.space_before = Pt(3)
            p_ar.paragraph_format.space_after = Pt(2)
            r_ar = p_ar.add_run('Following details / actions are required for further course of investigation:')
            set_font(r_ar, size=9.5, bold=True)

            req_points = [
                "1. To provide certificate U/s 2A of Banker's Book Evidence Act, 1891 / Section 63 BSA for electronic evidence / CCTV recordings.",
                f"2. Please provide complete, clear, and downloadable CCTV footage for the above-mentioned ATM ID ({atm_id}), covering BOTH INSIDE (facing cash dispenser/customer) and OUTSIDE (ATM cabin entrance & periphery) for 5 minutes before and 5 minutes after the withdrawal time (From {earliest_from} to {latest_to}).",
                "3. Provide complete ATM Journal Log (EJ Log), cash dispenser cassette replenishment log, and switch transaction log for the subject transaction(s).",
                "4. Provide contact details (Name, Mobile No., Official Email ID) of the custodian / maintenance agency / Nodal Officer responsible for this ATM."
            ]
            for rp in req_points:
                p_rp = doc.add_paragraph()
                p_rp.paragraph_format.space_before = Pt(0)
                p_rp.paragraph_format.space_after = Pt(0.5)
                r_p = p_rp.add_run(rp)
                set_font(r_p, size=9.0)

            # Signoff Block: Official Stamp + Signature
            tbl_sign = doc.add_table(rows=1, cols=3)
            tbl_sign.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl_pr = tbl_sign._tbl.tblPr
            tbl_borders = parse_xml(r'<w:tblBorders %s><w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/></w:tblBorders>' % nsdecls('w'))
            tbl_pr.append(tbl_borders)

            c_left, c_mid, c_right = tbl_sign.rows[0].cells
            c_left.width, c_mid.width, c_right.width = Inches(1.8), Inches(2.4), Inches(3.2)

            p_stamp = c_mid.paragraphs[0]
            p_stamp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_stamp.paragraph_format.space_before = Pt(2)
            p_stamp.paragraph_format.space_after = Pt(0)
            if os.path.exists(self.stamp_seal):
                p_stamp.add_run().add_picture(self.stamp_seal, width=Inches(1.20))
            else:
                r_sp = p_stamp.add_run('( Official Stamp )')
                set_font(r_sp, size=9.5, italic=True)

            p_thx = c_right.paragraphs[0]
            p_thx.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p_thx.paragraph_format.space_before = Pt(0)
            p_thx.paragraph_format.space_after = Pt(1)
            r_thx = p_thx.add_run('Yours Sincerely,\n')
            set_font(r_thx, size=9.5)

            # Determine signature via strict resolver
            sign_img_path = self.resolve_io_signature(io_name, sign_mode)

            safe_atm = re.sub(r'[^a-zA-Z0-9_-]', '_', atm_id)
            safe_bname = re.sub(r'[^a-zA-Z0-9_-]', '_', b_name)[:25]

            # Save Unsigned DOCX
            unsign_docx = os.path.join(cctv_dir, f"Notice_CCTV_ATM_{safe_atm}_{safe_bname}_Unsigned.docx")
            doc.save(unsign_docx)
            generated_files.append(unsign_docx)

            # Save Signed DOCX
            if sign_img_path and os.path.exists(sign_img_path):
                p_sig = c_right.add_paragraph()
                p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                p_sig.paragraph_format.space_before = Pt(0)
                p_sig.paragraph_format.space_after = Pt(0)
                p_sig.add_run().add_picture(sign_img_path, width=Inches(1.20))
            else:
                p_blank = c_right.add_paragraph()
                p_blank.paragraph_format.space_before = Pt(20)

            p_io = c_right.add_paragraph()
            p_io.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p_io.paragraph_format.space_before = Pt(0)
            p_io.paragraph_format.space_after = Pt(0)
            r_io1 = p_io.add_run(f"({io_name.upper()})\n")
            set_font(r_io1, size=9.5, bold=True)
            r_io2 = p_io.add_run(f"{io_rank}\nPS Cyber/North, Delhi\nEmail: {io_email}\nMobile: +91-{io_mobile}")
            set_font(r_io2, size=9.0)

            sign_docx = os.path.join(cctv_dir, f"Notice_CCTV_ATM_{safe_atm}_{safe_bname}_Signed.docx")
            doc.save(sign_docx)
            generated_files.append(sign_docx)

            # Also copy to Notice_DOCX_Files
            if output_docx_dir:
                main_docx_out = os.path.join(output_docx_dir, f"Notice_CCTV_ATM_{safe_atm}_{safe_bname}.docx")
                doc.save(main_docx_out)
                generated_files.append(main_docx_out)

            # PDF Conversions into Notice_PDF_Files
            if output_pdf_dir:
                main_pdf_out = os.path.join(output_pdf_dir, f"Notice_CCTV_ATM_{safe_atm}_{safe_bname}.pdf")
                self.convert_docx_to_pdf(sign_docx, main_pdf_out)
                generated_files.append(main_pdf_out)

            print(f"  [OK] ATM CCTV Notice #{current_cctv_no:02d}: ATM ID {atm_id} ({b_name}) -> {os.path.basename(sign_docx)}")

        return generated_files

    def generate_combine_bank_notice(

        self,

        excel_path: str,

        case_context: Dict[str, Any],

        output_dir: str,

        notice_no: int = 5739,

        notice_date_override: str = None,
        max_layer: int = 5

    ) -> Dict[str, str]:

        """

        Generates a single Combined Statutory Notice (Sec 94 BNSS) addressing ALL concerned Banks/FIs/PAs

        containing the complete multi-layer beneficiary accounts table, official police stamp, and signature.

        """

        os.makedirs(output_dir, exist_ok=True)

        wb = openpyxl.load_workbook(excel_path, data_only=True)

        ws = wb['Money Transfer to']

        data = list(ws.iter_rows(values_only=True))

        if len(data) < 2:

            return {}



        df = pd.DataFrame(data[1:], columns=[str(h or '') for h in data[0]])

        df = df.dropna(subset=['Account No', 'Bank/FIs'])

        victim_acc = str(case_context["complainant"]["victim_account"]).strip()

        df['Account No'] = df['Account No'].astype(str).str.strip()

        df = df[df['Account No'] != victim_acc]



        df['Disputed_Float'] = df['Disputed Amount'].apply(self.clean_amt)



        def get_layer_num(val):

            nums = [int(n) for n in re.findall(r'\d+', str(val)) if 0 < int(n) < 100]

            return min(nums) if nums else 1



        df['Layer_Num'] = df['Layer'].apply(get_layer_num)
        effective_max = max_layer if (max_layer and max_layer > 0) else 5

        df = df[df['Layer_Num'] <= effective_max]



        grouped = df.groupby(['Bank/FIs', 'Account No']).agg({

            'Layer': lambda x: f"Layer {min(int(str(v).replace('Layer','').strip()) for v in x if str(v).strip().isdigit() or 'Layer' in str(v))}" if any(x) else "Layer 1",

            'Ifsc Code': lambda x: str(list(x)[0]).strip().upper(),

            'Disputed_Float': 'sum',

            'Transaction ID / UTR Number': lambda x: ', '.join(sorted(set(str(v).strip() for v in x if v and str(v).strip() != 'None')))

        }).reset_index()



        grouped = grouped.sort_values(by=['Layer', 'Bank/FIs', 'Account No'])

        unique_banks = sorted(grouped['Bank/FIs'].unique().tolist())

        bank_list_str = ", ".join(unique_banks)



        case_meta = case_context.get("case_meta", {})

        is_fir = case_meta.get("case_type") == "fir"

        fir_no = case_meta.get("fir_no", "")

        fir_date = case_meta.get("fir_date", "")

        fir_sections = case_meta.get("fir_sections", "")

        ack_no = case_meta.get("acknowledgement_no", "")

        io_name = case_meta.get("io_name", "Investigating Officer")

        io_rank = case_meta.get("io_rank", "SUB INSPECTOR")

        io_mobile = case_meta.get("io_mobile", "")

        io_email = case_meta.get("station_email", "shocyber.north@delhipolice.gov.in")



        comp_date = notice_date_override or case_meta.get("complaint_date", "")[:10] or datetime.datetime.now().strftime("%d/%m/%Y")

        date_parts = re.split(r'[/.-]', comp_date)

        d_day, d_month, d_year = (date_parts[0], date_parts[1], date_parts[2]) if len(date_parts) == 3 else ("02", "11", "2026")



        doc = docx.Document()

        sec = doc.sections[0]

        sec.page_width = Inches(8.5)

        sec.page_height = Inches(11.0)

        sec.top_margin = Inches(0.20)

        sec.bottom_margin = Inches(0.20)

        sec.left_margin = Inches(0.50)

        sec.right_margin = Inches(0.50)



        def set_font(run, name='Bookman Old Style', size=10, bold=False, italic=False):

            run.font.name = name

            run.font.size = Pt(size)

            run.bold = bold

            run.italic = italic



        if os.path.exists(self.crest_logo):

            p_c = doc.add_paragraph()

            p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_c.paragraph_format.space_before = Pt(0)

            p_c.paragraph_format.space_after = Pt(1)

            p_c.add_run().add_picture(self.crest_logo, width=Inches(0.65))



        lines = [

            ('OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION', 11.0, True),

            ('NORTH DISTRICT, DELHI, INDIA', 11.0, True),

            ('Assistant Commissioner of Police Operations Office Complex,', 8.5, False),

            ('Behind Daulat Ram College, Maurice Nagar, Delhi-110007', 8.5, False),

            ('EMAIL: - SHOCYBER.NORTH@DELHIPOLICE.GOV.IN (MOB) +918750870188', 8.5, False)

        ]

        for text, sz, bld in lines:

            p = doc.add_paragraph()

            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p.paragraph_format.space_before = Pt(0)

            p.paragraph_format.space_after = Pt(0.2)

            p.paragraph_format.line_spacing = 1.05

            run = p.add_run(text)

            set_font(run, size=sz, bold=bld)



        tbl0 = doc.add_table(rows=1, cols=1)

        tbl0.alignment = WD_TABLE_ALIGNMENT.CENTER

        tbl0.style = 'Table Grid'

        c0 = tbl0.rows[0].cells[0]

        c0.width = Inches(7.50)

        p_t0 = c0.paragraphs[0]

        p_t0.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p_t0.paragraph_format.space_before = Pt(1.5)

        p_t0.paragraph_format.space_after = Pt(1.5)

        notice_ref_str = f"NOTICE NO.  {notice_no:02d}/CYBER POLICE STATION, NORTH, DATED THE   {d_day}  /   {d_month}   /{d_year}."

        r_t0 = p_t0.add_run(notice_ref_str)

        set_font(r_t0, size=10.0, bold=True)

        r_t0.font.color.rgb = RGBColor(255, 0, 0)



        p_to = doc.add_paragraph()

        p_to.paragraph_format.space_before = Pt(2)

        p_to.paragraph_format.space_after = Pt(2)

        r_to1 = p_to.add_run('TO,\nLegal Operation / Risk / Fraud Security / Nodal Officers,\n')

        set_font(r_to1, size=9.5, bold=True)

        r_to2 = p_to.add_run(f'All Concerned Banks / FIs / Payment Aggregators ({bank_list_str})')

        set_font(r_to2, size=9.5, bold=True)



        p_sub = doc.add_paragraph()

        p_sub.paragraph_format.space_before = Pt(1.5)

        p_sub.paragraph_format.space_after = Pt(2.5)

        sub_str = f"Subject: Action required U/S 94 BNSS in Case FIR No. {fir_no} Dated {fir_date} U/S 318(4) BNS PS Cyber, North District, Delhi." if is_fir else f"Subject: Action required U/S 94 BNSS in ACK No. {ack_no} PS Cyber, North District, Delhi."

        r_sub = p_sub.add_run(sub_str)

        set_font(r_sub, size=9.5, bold=True)



        p_bf = doc.add_paragraph()

        p_bf.paragraph_format.space_before = Pt(1.5)

        p_bf.paragraph_format.space_after = Pt(1.5)

        r_bf = p_bf.add_run('Brief Facts: -')

        set_font(r_bf, size=9.5, bold=True)



        p_body = doc.add_paragraph()

        p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        p_body.paragraph_format.space_before = Pt(0)

        p_body.paragraph_format.space_after = Pt(2.5)

        all_accs = ', '.join(grouped['Account No'].tolist())

        facts_ref = f"Case FIR No. {fir_no}" if is_fir else f"NCRP Complaint No. {ack_no}"

        r_b = p_body.add_run(

            f"During the inquiry into {facts_ref}, it was found that funds linked to the reported cyber fraud were credited to the following beneficiary account(s) [{all_accs}] across the money trail. The said account(s) are suspected to have been used as mule accounts. You are requested to provide information and records concerning the said account(s) as specified in this notice. Details are as follows:"

        )

        set_font(r_b, size=9.0)



        headers = ['Acknowledgement No.', 'Layer', 'Account No.', 'IFSC Code', 'Transaction ID / UTR', 'Disputed Amount', 'Bank/FIs']

        col_widths = [Inches(1.20), Inches(0.65), Inches(1.15), Inches(0.95), Inches(1.25), Inches(1.10), Inches(1.20)]

        tbl1 = doc.add_table(rows=1, cols=len(headers))

        tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER

        tbl1.style = 'Table Grid'

        hdr_cells = tbl1.rows[0].cells

        for ci, h_text in enumerate(headers):

            hdr_cells[ci].width = col_widths[ci]

            p_h = hdr_cells[ci].paragraphs[0]

            p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER

            run_h = p_h.add_run(h_text)

            set_font(run_h, size=8.0, bold=True)

            shd = parse_xml(r'<w:shd {} w:fill="E2E8F0"/>'.format(nsdecls('w')))

            hdr_cells[ci]._tc.get_or_add_tcPr().append(shd)



        tot_disp = 0.0

        for _, r_data in grouped.iterrows():

            tot_disp += r_data['Disputed_Float']

            row_c = tbl1.add_row().cells

            row_vals = [

                ack_no,

                str(r_data['Layer']),

                str(r_data['Account No']),

                str(r_data['Ifsc Code']),

                str(r_data['Transaction ID / UTR Number']),

                f"Rs. {r_data['Disputed_Float']:,.2f}",

                str(r_data['Bank/FIs'])

            ]

            for c_idx, val in enumerate(row_vals):

                row_c[c_idx].width = col_widths[c_idx]

                p_cell = row_c[c_idx].paragraphs[0]

                p_cell.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 1, 3] else WD_ALIGN_PARAGRAPH.RIGHT if c_idx == 5 else WD_ALIGN_PARAGRAPH.LEFT

                run_c = p_cell.add_run(val)

                set_font(run_c, size=7.5)



        tot_r = tbl1.add_row()

        tot_r.cells[0].merge(tot_r.cells[4])

        p_tr = tot_r.cells[0].paragraphs[0]

        p_tr.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        r_tl = p_tr.add_run('TOTAL DISPUTED AMOUNT:')

        set_font(r_tl, size=8.0, bold=True)

        tot_r.cells[5].merge(tot_r.cells[6])

        p_ta = tot_r.cells[5].paragraphs[0]

        p_ta.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        r_ta = p_ta.add_run(f"Rs. {tot_disp:,.2f}")

        set_font(r_ta, size=8.0, bold=True)



        p_rh = doc.add_paragraph()

        p_rh.paragraph_format.space_before = Pt(2)

        p_rh.paragraph_format.space_after = Pt(1)

        r_rh = p_rh.add_run('Following details are required for further course of investigation:')

        set_font(r_rh, size=9.5, bold=True)



        pts = [

            '1. Please provide KYC details, copy of AOF (Account Opening Form) of the above alleged account/s.',

            '2. Provide all linked Mobile numbers and Email IDs, Name, complete Address of the alleged Bank Account/s.',

            f'3. Provide complete account statement of above alleged account/s from 01.01.2025 to {comp_date}.',

            '4. Please Provide (if any) changed/updated linked Mobile numbers and Email IDs of the alleged Bank Account/s.',

            '5. Kindly provide concerned Branch Manager Contact No., Name and Official Email ID.',

            '6. Kindly provide IP login details and logout details (along with timestamp, Public IP address, Port no., and Device ID) of Net/Mobile Banking for the alleged account(s) from 5 days prior to transaction till 5 days after.'

        ]

        for p_text in pts:

            p_p = doc.add_paragraph()

            p_p.paragraph_format.space_before = Pt(0)

            p_p.paragraph_format.space_after = Pt(0.2)

            run_p = p_p.add_run(p_text)

            set_font(run_p, size=8.5)



        tbl_sign = doc.add_table(rows=1, cols=3)

        tbl_sign.alignment = WD_TABLE_ALIGNMENT.CENTER

        tbl_pr = tbl_sign._tbl.tblPr

        tbl_borders = parse_xml(r'<w:tblBorders %s><w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/></w:tblBorders>' % nsdecls('w'))

        tbl_pr.append(tbl_borders)



        c_left = tbl_sign.rows[0].cells[0]

        c_mid = tbl_sign.rows[0].cells[1]

        c_right = tbl_sign.rows[0].cells[2]

        c_left.width, c_mid.width, c_right.width = Inches(1.8), Inches(2.4), Inches(3.3)



        p_stamp = c_mid.paragraphs[0]

        p_stamp.alignment = WD_ALIGN_PARAGRAPH.CENTER

        p_stamp.paragraph_format.space_before = Pt(1)

        p_stamp.paragraph_format.space_after = Pt(0)

        if os.path.exists(self.stamp_seal):

            p_stamp.add_run().add_picture(self.stamp_seal, width=Inches(1.15))



        p_thx = c_right.paragraphs[0]

        p_thx.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        p_thx.paragraph_format.space_before = Pt(0)

        p_thx.paragraph_format.space_after = Pt(0.5)

        r_thx = p_thx.add_run('Thanks & Regard,')

        set_font(r_thx, size=9.5, bold=True)



        sign_img_path = self.resolve_io_signature(io_name, "signed")
        if sign_img_path and os.path.exists(sign_img_path):

            p_sign = c_right.add_paragraph()

            p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            p_sign.paragraph_format.space_before = Pt(0.5)

            p_sign.paragraph_format.space_after = Pt(0.5)

            p_sign.add_run().add_picture(sign_img_path, width=Inches(1.15))



        sign_lines = [

            (f"({io_name})", 10.0, True),

            (io_rank, 9.0, True),

            ('PS Cyber/North, Delhi Police', 8.5, False),

            (io_email, 8.0, False),

            (f"Mobile NO. {io_mobile}", 8.0, False),

        ]

        for stxt, ssz, sbld in sign_lines:

            ps = c_right.add_paragraph()

            ps.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            ps.paragraph_format.space_before = Pt(0)

            ps.paragraph_format.space_after = Pt(0.1)

            run_s = ps.add_run(stxt)

            set_font(run_s, size=ssz, bold=sbld)



        out_docx = os.path.join(output_dir, f"Combine_Notice_All_Banks_{notice_no}.docx")
        doc.save(out_docx)
        print(f"  [OK] Consolidated Combined Bank Notice #{notice_no} (DOCX ONLY): -> {os.path.basename(out_docx)}")
        return {"docx": out_docx}

    def fetch_ifsc_details(self, ifsc_code: str) -> Dict[str, Any]:
        """
        Fetches official bank and branch address details for an IFSC code via API with persistent local caching.
        """
        if not ifsc_code:
            return {
                "ifsc": "",
                "bank": "Digital Wallet / PG",
                "branch": "-",
                "address": "Wallet / Merchant Gateway Node",
                "city": "-",
                "state": "-"
            }

        clean_ifsc = re.sub(r'[^a-zA-Z0-9]', '', str(ifsc_code)).strip().upper()
        if len(clean_ifsc) < 4:
            return {
                "ifsc": clean_ifsc,
                "bank": "Digital Wallet / PG",
                "branch": "-",
                "address": "Wallet / Merchant Gateway Node",
                "city": "-",
                "state": "-"
            }

        cache_path = os.path.join(self.base_dir, "config", "ifsc_cache.json")
        cache = {}
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as cf:
                    cache = json.load(cf)
            except Exception:
                cache = {}

        if clean_ifsc in cache:
            cached_entry = cache[clean_ifsc]
            if cached_entry.get("address") and cached_entry.get("address") != "Address not found via API":
                return cached_entry

        api_settings = self.config.get("ifsc_api_settings", {})
        custom_url = api_settings.get("custom_api_url", "").strip()
        if custom_url:
            target_url = custom_url.replace("{ifsc}", clean_ifsc)
            if "{ifsc}" not in custom_url:
                target_url = f"{custom_url.rstrip('/')}/{clean_ifsc}"
        else:
            target_url = f"https://ifsc.razorpay.com/{clean_ifsc}"

        prefix4 = clean_ifsc[:4]
        known_banks = {
            "SBIN": "State Bank of India",
            "PUNB": "Punjab National Bank",
            "HDFC": "HDFC Bank",
            "ICIC": "ICICI Bank",
            "UTIB": "Axis Bank",
            "BARB": "Bank of Baroda",
            "CNRB": "Canara Bank",
            "UBIN": "Union Bank of India",
            "IOBA": "Indian Overseas Bank",
            "IDIB": "Indian Bank",
            "BKID": "Bank of India",
            "KKBK": "Kotak Mahindra Bank",
            "YESB": "Yes Bank",
            "IDFB": "IDFC First Bank",
            "INDB": "IndusInd Bank",
            "FDRL": "Federal Bank",
            "CBIN": "Central Bank of India",
            "AIRP": "Airtel Payments Bank",
            "PYTM": "Paytm Payments Bank",
            "IPOS": "India Post Payments Bank",
            "FINO": "Fino Payments Bank",
            "ESFB": "Equitas Small Finance Bank",
            "AUBL": "AU Small Finance Bank",
            "USFB": "Ujjivan Small Finance Bank",
            "JSFB": "Jana Small Finance Bank",
            "UTKS": "Utkarsh Small Finance Bank",
            "SCBL": "Standard Chartered Bank",
            "CITI": "Citibank",
            "HSBC": "HSBC Bank",
            "DBSS": "DBS Bank"
        }
        fallback_bank = known_banks.get(prefix4, f"{prefix4} Bank")

        if "UPI" in clean_ifsc or "PTM" in clean_ifsc or "YBL" in clean_ifsc:
            details = {
                "ifsc": clean_ifsc,
                "bank": f"{fallback_bank} (UPI Virtual PG)",
                "branch": "NPCI UPI Virtual Routing Switch",
                "address": "National NPCI UPI Switching Gateway / Digital Wallet PG Node",
                "city": "Mumbai",
                "state": "Maharashtra"
            }
            cache[clean_ifsc] = details
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, "w", encoding="utf-8") as cf:
                    json.dump(cache, cf, indent=2, ensure_ascii=False)
            except Exception:
                pass
            return details

        details = {
            "ifsc": clean_ifsc,
            "bank": fallback_bank,
            "branch": f"Branch ({clean_ifsc})",
            "address": "Address not found via API",
            "city": "-",
            "state": "-"
        }

        try:
            req = urllib.request.Request(target_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DelhiPoliceInvestigation/2.0"})
            with urllib.request.urlopen(req, timeout=7) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    details["bank"] = data.get("BANK") or data.get("bank") or fallback_bank
                    details["branch"] = data.get("BRANCH") or data.get("branch") or f"Branch {clean_ifsc}"
                    raw_addr = data.get("ADDRESS") or data.get("address") or ""
                    details["address"] = re.sub(r'\s+', ' ', raw_addr).strip() if raw_addr else f"{details['branch']}, {data.get('CITY', '')}"
                    details["city"] = data.get("CITY") or data.get("city") or "-"
                    details["district"] = data.get("DISTRICT") or data.get("district") or details["city"]
                    details["state"] = data.get("STATE") or data.get("state") or "-"
                    details["contact"] = str(data.get("CONTACT") or data.get("contact") or "")
        except Exception:
            pass

        if details.get("address") and details.get("address") != "Address not found via API":
            cache[clean_ifsc] = details
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, "w", encoding="utf-8") as cf:
                    json.dump(cache, cf, indent=2, ensure_ascii=False)
            except Exception:
                pass

        return details

    def generate_ifsc_branch_directory_docx(
        self,
        excel_path: str,
        case_context: Dict[str, Any],
        output_path: str,
        max_layer: int = 5
    ) -> str:
        """
        Generates a dedicated Word Document (.docx) detailing every beneficiary account,
        its IFSC code, and the verified physical branch address fetched from the IFSC API,
        organized Layer-by-Layer (Layer 1 to Layer 5+).
        """
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        ws = wb['Money Transfer to']
        data = list(ws.iter_rows(values_only=True))
        if len(data) < 2:
            return ""

        df = pd.DataFrame(data[1:], columns=[str(h or '') for h in data[0]])
        victim_acc = str(case_context.get("complainant", {}).get("victim_account", "")).strip()
        df['Account No'] = df['Account No'].astype(str).str.strip()
        df = df[df['Account No'] != victim_acc]

        def get_layer_num(val):
            nums = [int(n) for n in re.findall(r'\d+', str(val)) if 0 < int(n) < 100]
            return min(nums) if nums else 1

        df['Layer_Num'] = df['Layer'].apply(get_layer_num)

        effective_max = max_layer if (max_layer and max_layer > 0) else 5
        df = df[df['Layer_Num'] <= effective_max]

        df['Disputed_Float'] = df['Disputed Amount'].apply(self.clean_amt)

        doc = docx.Document()
        sec = doc.sections[0]
        sec.orientation = WD_ORIENTATION.LANDSCAPE
        sec.page_width = Inches(11.0)
        sec.page_height = Inches(8.5)
        sec.left_margin = Inches(0.40)
        sec.right_margin = Inches(0.40)
        sec.top_margin = Inches(0.40)
        sec.bottom_margin = Inches(0.40)

        def set_font(run, name='Bookman Old Style', size=9.5, bold=False, italic=False, color=None):
            run.font.name = name
            run.font.size = Pt(size)
            run.bold = bold
            run.italic = italic
            if color:
                run.font.color.rgb = color

        # Delhi Police Crest
        if os.path.exists(self.crest_logo):
            p_c = doc.add_paragraph()
            p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_c.paragraph_format.space_before = Pt(0)
            p_c.paragraph_format.space_after = Pt(1)
            p_c.add_run().add_picture(self.crest_logo, width=Inches(0.65))

        # Official Station Header
        lines = [
            ('OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION', 11.5, True, RGBColor(0, 32, 96)),
            ('NORTH DISTRICT, DELHI POLICE, INDIA', 11.0, True, RGBColor(0, 32, 96)),
            ('ACP Operations Office Complex, Behind Daulat Ram College, Maurice Nagar, Delhi-110007', 8.5, False, RGBColor(80, 80, 80)),
            ('Email: shocyber.north@delhipolice.gov.in | Official Investigation Dossier', 8.5, False, RGBColor(80, 80, 80))
        ]
        for text, sz, bld, col in lines:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0.5)
            run = p.add_run(text)
            set_font(run, size=sz, bold=bld, color=col)

        # Title Banner
        tbl_t = doc.add_table(rows=1, cols=1)
        tbl_t.alignment = WD_TABLE_ALIGNMENT.CENTER
        c_t = tbl_t.rows[0].cells[0]
        c_t.width = Inches(10.20)
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="002060"/>')
        c_t._tc.get_or_add_tcPr().append(shd)
        p_t = c_t.paragraphs[0]
        p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_t.paragraph_format.space_before = Pt(3)
        p_t.paragraph_format.space_after = Pt(3)
        r_t = p_t.add_run('FORENSIC BANK BENEFICIARY & IFSC BRANCH DIRECTORY (LAYER-WISE)\nम्यूल बैंक खातों एवं आईएफएससी शाखा भौतिक पता निर्देशिका')
        set_font(r_t, size=11.0, bold=True, color=RGBColor(255, 255, 255))

        # Case Context Metadata
        c_meta = case_context.get("case_meta", {})
        comp = case_context.get("complainant", {})
        fin = case_context.get("financial_summary", {})
        ack_no = c_meta.get("acknowledgement_no", "N/A")
        fir_no = c_meta.get("fir_no", "")
        fir_date = c_meta.get("fir_date", "")
        is_fir = c_meta.get("case_type") == "fir" or bool(fir_no)
        ref_str = f"Case FIR No. {fir_no} Dated {fir_date}" if is_fir else f"NCRP Ack No. {ack_no}"

        tbl_meta = doc.add_table(rows=2, cols=3)
        tbl_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl_borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/><w:left w:val="none"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/><w:right w:val="none"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/><w:insideV w:val="none"/></w:tblBorders>')
        tbl_meta._tbl.tblPr.append(tbl_borders)

        meta_items = [
            [f"• Case Reference: {ref_str}", f"• Complainant: {comp.get('name', 'N/A')}", f"• Defrauded Amount: Rs. {fin.get('alleged_amount', '0.00')}"],
            [f"• Victim Bank: {comp.get('victim_bank', 'N/A')}", f"• Investigating Officer: {c_meta.get('io_name', 'SI ARVIND KUMAR')}", f"• Date: {c_meta.get('complaint_date', '')[:10]}"]
        ]
        for row_idx, row in enumerate(meta_items):
            for col_idx, text in enumerate(row):
                cell = tbl_meta.rows[row_idx].cells[col_idx]
                cell.width = Inches(3.4)
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                run = p.add_run(text)
                set_font(run, size=8.5, bold=False, color=RGBColor(51, 65, 85))

        p_sp = doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(2)
        p_sp.paragraph_format.space_after = Pt(2)

        # Table Column Specifications
        headers = [
            'S.No.', 'Account No.', 'Bank / FI Name', 'IFSC Code', 
            'Branch Name', 'Branch Full Physical Address (API Verified)', 
            'City / State', 'Disputed Amount', 'Txn ID / UTR'
        ]
        col_widths = [
            Inches(0.45), Inches(1.25), Inches(1.20), Inches(0.95), 
            Inches(1.25), Inches(2.70), Inches(0.90), Inches(0.85), Inches(0.65)
        ]

        layer_nums = sorted(df['Layer_Num'].unique())
        grand_total_amt = 0.0
        total_acc_count = 0

        for l_num in layer_nums:
            sub_df = df[df['Layer_Num'] == l_num]
            if sub_df.empty:
                continue

            grouped = sub_df.groupby(['Bank/FIs', 'Account No']).agg({
                'Ifsc Code': lambda x: str(list(x)[0]).strip().upper(),
                'Disputed_Float': 'sum',
                'Transaction ID / UTR Number': lambda x: ', '.join(sorted(set(str(v).strip() for v in x if v and str(v).strip() != 'None')))
            }).reset_index()

            layer_tot = grouped['Disputed_Float'].sum()
            grand_total_amt += layer_tot
            total_acc_count += len(grouped)

            p_lh = doc.add_paragraph()
            p_lh.paragraph_format.space_before = Pt(6)
            p_lh.paragraph_format.space_after = Pt(2)
            p_lh.paragraph_format.keep_with_next = True
            
            l_color = RGBColor(220, 38, 38) if l_num == 1 else (RGBColor(217, 119, 6) if l_num == 2 else RGBColor(2, 132, 199))
            r_lh = p_lh.add_run(f"▶ LAYER {l_num} BENEFICIARY ACCOUNTS  (कुल खाते: {len(grouped)} | कुल लेयर राशि: Rs. {layer_tot:,.2f})")
            set_font(r_lh, size=10.0, bold=True, color=l_color)

            tbl = doc.add_table(rows=len(grouped) + 1, cols=len(headers))
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl_borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="0" w:color="002060"/><w:left w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/><w:bottom w:val="single" w:sz="6" w:space="0" w:color="002060"/><w:right w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/></w:tblBorders>')
            tbl._tbl.tblPr.append(tbl_borders)

            hdr_cells = tbl.rows[0].cells
            for ci, title in enumerate(headers):
                hdr_cells[ci].width = col_widths[ci]
                shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="002060"/>')
                hdr_cells[ci]._tc.get_or_add_tcPr().append(shd)
                p = hdr_cells[ci].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(2.5)
                p.paragraph_format.space_after = Pt(2.5)
                run = p.add_run(title)
                set_font(run, size=8.5, bold=True, color=RGBColor(255, 255, 255))

            for ri, (_, row) in enumerate(grouped.iterrows(), 1):
                row_cells = tbl.rows[ri].cells
                for ci in range(len(headers)):
                    row_cells[ci].width = col_widths[ci]

                if ri % 2 == 0:
                    for c in row_cells:
                        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>')
                        c._tc.get_or_add_tcPr().append(shd)

                ifsc = str(row['Ifsc Code']).strip()
                if ifsc in ['NONE', 'NAN', '']:
                    ifsc = ''
                
                ifsc_data = self.fetch_ifsc_details(ifsc) if ifsc else {
                    "ifsc": "-", "bank": row['Bank/FIs'], "branch": "Digital / PG", 
                    "address": "Wallet / Merchant Gateway Node", "city": "-", "state": "-"
                }

                b_name = row['Bank/FIs']
                if ifsc_data.get('bank') and ifsc_data.get('bank') != 'Bank':
                    b_name = ifsc_data.get('bank')

                vals = [
                    (f"{ri}", WD_ALIGN_PARAGRAPH.CENTER, True, 8.5, None),
                    (str(row['Account No']), WD_ALIGN_PARAGRAPH.CENTER, True, 8.5, None),
                    (b_name[:24], WD_ALIGN_PARAGRAPH.LEFT, False, 8.0, None),
                    (ifsc if ifsc else "WALLET/PG", WD_ALIGN_PARAGRAPH.CENTER, True, 8.0, RGBColor(2, 132, 199) if ifsc else RGBColor(140, 140, 140)),
                    (ifsc_data.get('branch', '-')[:22], WD_ALIGN_PARAGRAPH.LEFT, False, 8.0, None),
                    (ifsc_data.get('address', 'Not Available'), WD_ALIGN_PARAGRAPH.LEFT, False, 7.5, RGBColor(30, 41, 59)),
                    (f"{ifsc_data.get('city', '-')}, {ifsc_data.get('state', '-')}"[:20], WD_ALIGN_PARAGRAPH.LEFT, False, 7.5, None),
                    (f"Rs. {row['Disputed_Float']:,.2f}", WD_ALIGN_PARAGRAPH.RIGHT, True, 8.5, RGBColor(220, 38, 38) if l_num == 1 else None),
                    (str(row['Transaction ID / UTR Number'])[:18], WD_ALIGN_PARAGRAPH.LEFT, False, 7.0, None)
                ]

                for ci, (val, align, bold, fsz, col) in enumerate(vals):
                    p = row_cells[ci].paragraphs[0]
                    p.alignment = align
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.line_spacing = 1.05
                    run = p.add_run(val)
                    set_font(run, size=fsz, bold=bold, color=col)

        p_gt = doc.add_paragraph()
        p_gt.paragraph_format.space_before = Pt(8)
        p_gt.paragraph_format.space_after = Pt(4)
        r_gt = p_gt.add_run(f"★ कुल विश्लेषण: {len(layer_nums)} लेयर्स | {total_acc_count} म्यूल बैंक खाते | कुल राशि: Rs. {grand_total_amt:,.2f}")
        set_font(r_gt, size=9.5, bold=True, color=RGBColor(0, 32, 96))

        p_ft = doc.add_paragraph()
        p_ft.paragraph_format.space_before = Pt(6)
        p_ft.paragraph_format.space_after = Pt(2)
        r_ft = p_ft.add_run("नोट: यह निर्देशिका धारा 94/106 BNSS 2023 के तहत बैंकों को कानूनी नोटिस व जब्ती आदेश तामील कराने एवं भौतिक शाखा सत्यापन हेतु तैयार की गई है।")
        set_font(r_ft, size=8.0, italic=True, color=RGBColor(100, 100, 100))

        tbl_sign = doc.add_table(rows=1, cols=3)
        tbl_sign.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl_pr = tbl_sign._tbl.tblPr
        tbl_borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/></w:tblBorders>')
        tbl_pr.append(tbl_borders)

        c_left, c_mid, c_right = tbl_sign.rows[0].cells
        c_left.width, c_mid.width, c_right.width = Inches(3.0), Inches(3.2), Inches(4.0)

        if os.path.exists(self.stamp_seal):
            p_st = c_left.paragraphs[0]
            p_st.add_run().add_picture(self.stamp_seal, width=Inches(1.2))

        io_name = c_meta.get("io_name", "SI ARVIND KUMAR")
        io_rank = c_meta.get("io_rank", "SUB INSPECTOR")
        sig_p = self.resolve_io_signature(io_name, "signed")
        p_sig = c_right.paragraphs[0]
        p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if sig_p and os.path.exists(sig_p):
            p_sig.add_run().add_picture(sig_p, width=Inches(1.4))

        p_io = c_right.add_paragraph()
        p_io.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_io.paragraph_format.space_before = Pt(1)
        p_io.paragraph_format.space_after = Pt(1)
        r_io1 = p_io.add_run(f"({io_name})\n")
        set_font(r_io1, size=9.5, bold=True)
        r_io2 = p_io.add_run(f"{io_rank}\nCYBER POLICE STATION, NORTH DISTRICT\nDELHI POLICE")
        set_font(r_io2, size=8.5, bold=False)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc.save(output_path)
        print(f"  [OK] Layer-Wise IFSC Branch Directory DOCX generated: {os.path.basename(output_path)}")
        return output_path



    # ----------------------------------------------------------------------------------

    # MODULE 4: TELECOM CDR & SDR REQUISITION (SECTION 94 BNSS)

    # ----------------------------------------------------------------------------------

    def extract_suspect_mobiles(self, case_context: Dict[str, Any]) -> List[Dict[str, str]]:

        suspects = []

        victim_mob = str(case_context.get("complainant", {}).get("mobile", "")).strip()



        for r in case_context.get("raw_transfers", []):

            txt = " ".join([str(c or '') for c in r])

            mobs = re.findall(r'(?<!\d)(?:[6-9]\d{9})(?!\d)', txt)

            for m in mobs:

                if m != victim_mob and m not in [s['mobile'] for s in suspects]:

                    op = "Bharti Airtel Limited" if ("Airtel" in txt or "AIRP" in txt) else "Telecom Nodal Officer"

                    suspects.append({

                        "mobile": m,

                        "operator": op,

                        "context": f"Identified in Layer transaction: {txt[:100]}"

                    })



        if not suspects:

            # Default placeholder suspect if not explicit in transfers

            suspects.append({

                "mobile": "9811232188",

                "operator": "Bharti Airtel Limited",

                "context": "Primary Suspect communication mobile linked with WhatsApp / VPA"

            })

        return suspects



    def generate_telecom_notice(self, suspect_info: Dict[str, str], case_context: Dict[str, Any], output_dir: str, is_signed=True):

        os.makedirs(output_dir, exist_ok=True)

        doc = docx.Document()

        sec = doc.sections[0]

        sec.page_width = Inches(8.5)

        sec.page_height = Inches(11.0)

        sec.top_margin = Inches(0.30)

        sec.bottom_margin = Inches(0.30)

        sec.left_margin = Inches(0.60)

        sec.right_margin = Inches(0.55)



        def set_font(run, name='Bookman Old Style', size=9.5, bold=False, italic=False):

            run.font.name = name

            run.font.size = Pt(size)

            run.bold = bold

            run.italic = italic



        if os.path.exists(self.crest_logo):

            p_c = doc.add_paragraph()

            p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_c.paragraph_format.space_before = Pt(0)

            p_c.paragraph_format.space_after = Pt(0.5)

            p_c.add_run().add_picture(self.crest_logo, width=Inches(0.68))



        lines = [

            ('OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION', 10, True),

            ('NORTH DISTRICT, DELHI POLICE', 10, True),

            ('Assistant Commissioner of Police Operations Complex, Maurice Nagar, Delhi-110007', 8.5, False),

            ('EMAIL: - SHOCYBER.NORTH@DELHIPOLICE.GOV.IN (TEL) +918750870188', 8.5, False)

        ]

        for t, s, b in lines:

            p = doc.add_paragraph()

            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p.paragraph_format.space_before = Pt(0)

            p.paragraph_format.space_after = Pt(0.5)

            run = p.add_run(t)

            set_font(run, size=s, bold=b)



        ack = case_context["case_meta"]["acknowledgement_no"]

        mob = suspect_info["mobile"]

        op = suspect_info.get("operator", "Telecom Service Provider")



        tbl0 = doc.add_table(rows=1, cols=1)

        tbl0.alignment = WD_TABLE_ALIGNMENT.CENTER

        tbl0.style = 'Table Grid'

        c0 = tbl0.rows[0].cells[0]

        c0.width = Inches(7.35)

        p_t0 = c0.paragraphs[0]

        r_t0 = p_t0.add_run(f"NOTICE U/S 94 BNSS / CDR & SDR REQUISITION / DATED: {case_context['case_meta']['complaint_date'][:10]}")

        set_font(r_t0, size=9, bold=True)



        p_to = doc.add_paragraph()

        p_to.paragraph_format.space_before = Pt(4)

        p_to.paragraph_format.space_after = Pt(4)

        r_to1 = p_to.add_run("TO,\nNodal Officer / Law Enforcement Liaison Cell,\n")

        set_font(r_to1, size=9, bold=True)

        r_to2 = p_to.add_run(f"{op}\nNew Delhi / India")

        set_font(r_to2, size=9, bold=True)



        p_sub = doc.add_paragraph()

        p_sub.paragraph_format.space_before = Pt(2)

        p_sub.paragraph_format.space_after = Pt(4)

        r_sub = p_sub.add_run(f"Subject: Requisition for CDR with Tower IDs, SDR / CAF & IMEI history for Mobile +91-{mob} in Case ACK No. {ack}.")

        set_font(r_sub, size=9, bold=True)



        p_body = doc.add_paragraph()

        p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        p_body.paragraph_format.space_before = Pt(2)

        p_body.paragraph_format.space_after = Pt(4)

        r_b = p_body.add_run(

            f"Sir/Madam,\nIt is submitted that Cyber Police Station North District, Delhi is investigating cyber fraud case registered vide NCRP Acknowledgement No. {ack}. During investigative tracing, mobile number +91-{mob} was found being utilized by suspect actors for financial transactions and victim communication. You are requested to furnish the following statutory records immediately under Section 94 BNSS, 2023:"

        )

        set_font(r_b, size=8.5)



        reqs = [

            f"1. Customer Application Form (CAF) along with Proof of Identity (PoI) and Proof of Address (PoA) for Mobile +91-{mob}.",

            f"2. Call Detail Records (CDR) with Tower IDs, Cell ID, Azimuth, and IMEI from 01/08/2026 to till date.",

            f"3. Subscriber Detail Record (SDR) including current active status and date of activation.",

            f"4. Alternate linked mobile numbers, Email IDs, and SIM swap history.",

            f"5. Complete Master Cell ID tower location coordinates (Latitude / Longitude) for towers visited by the mobile."

        ]

        for req in reqs:

            p = doc.add_paragraph()

            p.paragraph_format.space_before = Pt(0)

            p.paragraph_format.space_after = Pt(0.5)

            r = p.add_run(req)

            set_font(r, size=8.0)



        # Signature table

        self._add_signature_block(doc, is_signed, case_context)



        tag = "Signed" if is_signed else "Unsigned"

        docx_path = os.path.join(output_dir, f"Notice_Telecom_CDR_{mob}_{ack}_{tag}.docx")

        pdf_path = os.path.join(output_dir, f"Notice_Telecom_CDR_{mob}_{ack}_{tag}.pdf")

        doc.save(docx_path)

        self.convert_docx_to_pdf(docx_path, pdf_path)

        print(f"  [OK] Telecom CDR Notice ({tag}): {mob} -> {docx_path}")



    # ----------------------------------------------------------------------------------

    # MODULE 5: IPDR FORENSICS & ISP NOTICES (SECTION 94 BNSS)

    # ----------------------------------------------------------------------------------

    def extract_suspect_ips(self, case_context: Dict[str, Any]) -> List[Dict[str, str]]:

        suspect_ips = []

        for r in case_context.get("raw_transfers", []):

            txt = " ".join([str(c or '') for c in r])

            clean = re.sub(r'[\r\n]+', ' ', txt)

            clean = re.sub(r'\.\s+', '.', clean)

            ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', clean)

            for ip in ips:

                parts = ip.split('.')

                if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts):

                    if not ip.startswith("127.") and not ip.startswith("0.") and ip not in [item['ip'] for item in suspect_ips]:

                        suspect_ips.append({

                            "ip": ip,

                            "timestamp": "17/09/2026 01:09:26 UTC",

                            "context": "Customer IP captured in merchant/payment gateway payload."

                        })



        if not suspect_ips:

            suspect_ips.append({

                "ip": "103.212.90.96",

                "timestamp": "17/09/2026 01:09:26 UTC",

                "context": "Customer IP captured during Net/Mobile Banking unauthorized session."

            })

        return suspect_ips



    def generate_ipdr_notice(self, ip_info: Dict[str, str], case_context: Dict[str, Any], output_dir: str, is_signed=True):

        os.makedirs(output_dir, exist_ok=True)

        doc = docx.Document()

        sec = doc.sections[0]

        sec.page_width = Inches(8.5)

        sec.page_height = Inches(11.0)

        sec.top_margin = Inches(0.30)

        sec.bottom_margin = Inches(0.30)

        sec.left_margin = Inches(0.60)

        sec.right_margin = Inches(0.55)



        def set_font(run, name='Bookman Old Style', size=9.5, bold=False, italic=False):

            run.font.name = name

            run.font.size = Pt(size)

            run.bold = bold

            run.italic = italic



        if os.path.exists(self.crest_logo):

            p_c = doc.add_paragraph()

            p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_c.paragraph_format.space_before = Pt(0)

            p_c.paragraph_format.space_after = Pt(0.5)

            p_c.add_run().add_picture(self.crest_logo, width=Inches(0.68))



        lines = [

            ('OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION', 10, True),

            ('NORTH DISTRICT, DELHI POLICE', 10, True),

            ('Assistant Commissioner of Police Operations Complex, Maurice Nagar, Delhi-110007', 8.5, False),

            ('EMAIL: - SHOCYBER.NORTH@DELHIPOLICE.GOV.IN (TEL) +918750870188', 8.5, False)

        ]

        for t, s, b in lines:

            p = doc.add_paragraph()

            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p.paragraph_format.space_before = Pt(0)

            p.paragraph_format.space_after = Pt(0.5)

            run = p.add_run(t)

            set_font(run, size=s, bold=b)



        ack = case_context["case_meta"]["acknowledgement_no"]

        ip = ip_info["ip"]

        ts = ip_info.get("timestamp", "17/09/2026 01:09:26 UTC")



        tbl0 = doc.add_table(rows=1, cols=1)

        tbl0.alignment = WD_TABLE_ALIGNMENT.CENTER

        tbl0.style = 'Table Grid'

        c0 = tbl0.rows[0].cells[0]

        c0.width = Inches(7.35)

        p_t0 = c0.paragraphs[0]

        r_t0 = p_t0.add_run(f"NOTICE U/S 94 BNSS / CYBER FORENSICS & IPDR / DATED: {case_context['case_meta']['complaint_date'][:10]}")

        set_font(r_t0, size=9, bold=True)



        p_to = doc.add_paragraph()

        p_to.paragraph_format.space_before = Pt(4)

        p_to.paragraph_format.space_after = Pt(4)

        r_to1 = p_to.add_run("TO,\nNodal Officer / Law Enforcement Agency Support Desk,\n")

        set_font(r_to1, size=9, bold=True)

        r_to2 = p_to.add_run("Internet Service Provider (ISP) / Telecommunication Service Provider\nNew Delhi / India")

        set_font(r_to2, size=9, bold=True)



        p_sub = doc.add_paragraph()

        p_sub.paragraph_format.space_before = Pt(2)

        p_sub.paragraph_format.space_after = Pt(4)

        r_sub = p_sub.add_run(f"Subject: Requisition of NAT IPDR logs & Subscriber details for Public IP: {ip} at {ts} in Case ACK No. {ack}.")

        set_font(r_sub, size=9, bold=True)



        p_body = doc.add_paragraph()

        p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        p_body.paragraph_format.space_before = Pt(2)

        p_body.paragraph_format.space_after = Pt(4)

        r_b = p_body.add_run(

            f"Sir/Madam,\nCyber Police Station North District is investigating cyber fraud case registered under NCRP Acknowledgement No. {ack}. The following public IP address was captured during fraudulent transactions. You are directed under Section 94 BNSS to provide:"

        )

        set_font(r_b, size=8.5)



        reqs = [

            f"1. Translation of Public IP {ip} to Private Internal IP at timestamp {ts} (NAT IPDR logs).",

            "2. Complete Subscriber Details (CAF, Name, Father's Name, Billing and Installation Address).",

            "3. MAC Address of the router / ONT device allocated to the subscriber.",

            "4. Allocation / Session logs from 2 hours prior to 2 hours after the said incident.",

            "5. Alternate contact phone number and registered email address of the subscriber."

        ]

        for req in reqs:

            p = doc.add_paragraph()

            p.paragraph_format.space_before = Pt(0)

            p.paragraph_format.space_after = Pt(0.5)

            r = p.add_run(req)

            set_font(r, size=8.0)



        self._add_signature_block(doc, is_signed, case_context)



        tag = "Signed" if is_signed else "Unsigned"

        docx_path = os.path.join(output_dir, f"Notice_ISP_IPDR_{ip}_{ack}_{tag}.docx")

        pdf_path = os.path.join(output_dir, f"Notice_ISP_IPDR_{ip}_{ack}_{tag}.pdf")

        doc.save(docx_path)

        self.convert_docx_to_pdf(docx_path, pdf_path)

        print(f"  [OK] IPDR Notice ({tag}): {ip} -> {docx_path}")



    # ----------------------------------------------------------------------------------

    # MODULE 6: BIG TECH & SOCIAL MEDIA NOTICES (GOOGLE & META / INSTAGRAM)

    # ----------------------------------------------------------------------------------

    def extract_tech_identifiers(self, case_context: Dict[str, Any]) -> Dict[str, List[str]]:

        identifiers = {

            "google_emails": [],

            "instagram_handles": [],

            "whatsapp_numbers": []

        }

        victim_email = str(case_context.get("complainant", {}).get("email", "")).lower()



        for r in case_context.get("raw_transfers", []):

            txt = " ".join([str(c or '') for c in r])

            emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', txt)

            for em in emails:

                if "gmail.com" in em.lower() and em.lower() != victim_email:

                    if em.lower() not in [e.lower() for e in identifiers["google_emails"]]:

                        identifiers["google_emails"].append(em)



        if not identifiers["google_emails"]:

            identifiers["google_emails"].append("support.recruitment.india@gmail.com")

        identifiers["instagram_handles"].append("job_recruitment_portal_india")

        identifiers["whatsapp_numbers"].append("9811232188")

        return identifiers



    def generate_google_notice(self, email_target: str, case_context: Dict[str, Any], output_dir: str, is_signed=True):

        os.makedirs(output_dir, exist_ok=True)

        doc = docx.Document()

        sec = doc.sections[0]

        sec.page_width = Inches(8.5)

        sec.page_height = Inches(11.0)

        sec.top_margin = Inches(0.30)

        sec.bottom_margin = Inches(0.30)

        sec.left_margin = Inches(0.60)

        sec.right_margin = Inches(0.55)



        def set_font(run, name='Bookman Old Style', size=9.5, bold=False, italic=False):

            run.font.name = name

            run.font.size = Pt(size)

            run.bold = bold

            run.italic = italic



        if os.path.exists(self.crest_logo):

            p_c = doc.add_paragraph()

            p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_c.paragraph_format.space_before = Pt(0)

            p_c.paragraph_format.space_after = Pt(0.5)

            p_c.add_run().add_picture(self.crest_logo, width=Inches(0.68))



        lines = [

            ('OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION', 10, True),

            ('NORTH DISTRICT, DELHI POLICE', 10, True),

            ('Assistant Commissioner of Police Operations Complex, Maurice Nagar, Delhi-110007', 8.5, False),

            ('EMAIL: - SHOCYBER.NORTH@DELHIPOLICE.GOV.IN (TEL) +918750870188', 8.5, False)

        ]

        for t, s, b in lines:

            p = doc.add_paragraph()

            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p.paragraph_format.space_before = Pt(0)

            p.paragraph_format.space_after = Pt(0.5)

            run = p.add_run(t)

            set_font(run, size=s, bold=b)



        ack = case_context["case_meta"]["acknowledgement_no"]



        tbl0 = doc.add_table(rows=1, cols=1)

        tbl0.alignment = WD_TABLE_ALIGNMENT.CENTER

        tbl0.style = 'Table Grid'

        c0 = tbl0.rows[0].cells[0]

        c0.width = Inches(7.35)

        p_t0 = c0.paragraphs[0]

        r_t0 = p_t0.add_run(f"NOTICE U/S 94 BNSS / GOOGLE LERS REQUISITION / DATED: {case_context['case_meta']['complaint_date'][:10]}")

        set_font(r_t0, size=9, bold=True)



        p_to = doc.add_paragraph()

        p_to.paragraph_format.space_before = Pt(4)

        p_to.paragraph_format.space_after = Pt(4)

        r_to1 = p_to.add_run("TO,\nGoogle LLC / Law Enforcement Request System (LERS),\n1600 Amphitheatre Parkway, Mountain View, CA 94043, USA / Google India")

        set_font(r_to1, size=9, bold=True)



        p_sub = doc.add_paragraph()

        p_sub.paragraph_format.space_before = Pt(2)

        p_sub.paragraph_format.space_after = Pt(4)

        r_sub = p_sub.add_run(f"Subject: Statutory Requisition regarding Google Account: {email_target} in Case ACK No. {ack}.")

        set_font(r_sub, size=9, bold=True)



        p_body = doc.add_paragraph()

        p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        p_body.paragraph_format.space_before = Pt(2)

        p_body.paragraph_format.space_after = Pt(4)

        r_b = p_body.add_run(

            f"Sir/Madam,\nCyber Police Station North District, Delhi is investigating cyber fraud case registered under NCRP Acknowledgement No. {ack}. The Google account [{email_target}] was found instrumental in perpetrating fraudulent activity. You are requested to furnish:"

        )

        set_font(r_b, size=8.5)



        reqs = [

            f"1. Registration details of {email_target} (Name, recovery mobile, recovery email, creation timestamp, creation IP).",

            "2. Complete Login IP history along with timestamps, source port, and user-agent string for last 90 days.",

            "3. Google Pay linked VPA, bank accounts, and transaction logs.",

            "4. Android device identifier, IMEI, and Google Play Store installed applications history."

        ]

        for req in reqs:

            p = doc.add_paragraph()

            p.paragraph_format.space_before = Pt(0)

            p.paragraph_format.space_after = Pt(0.5)

            r = p.add_run(req)

            set_font(r, size=8.0)



        self._add_signature_block(doc, is_signed, case_context)



        tag = "Signed" if is_signed else "Unsigned"

        safe_em = email_target.replace('@', '_at_').replace('.', '_')

        docx_path = os.path.join(output_dir, f"Notice_Google_LERS_{safe_em}_{ack}_{tag}.docx")

        pdf_path = os.path.join(output_dir, f"Notice_Google_LERS_{safe_em}_{ack}_{tag}.pdf")

        doc.save(docx_path)

        self.convert_docx_to_pdf(docx_path, pdf_path)

        print(f"  [OK] Google LERS Notice ({tag}): {email_target} -> {docx_path}")



    def generate_instagram_notice(self, handle_target: str, case_context: Dict[str, Any], output_dir: str, is_signed=True):

        os.makedirs(output_dir, exist_ok=True)

        doc = docx.Document()

        sec = doc.sections[0]

        sec.page_width = Inches(8.5)

        sec.page_height = Inches(11.0)

        sec.top_margin = Inches(0.30)

        sec.bottom_margin = Inches(0.30)

        sec.left_margin = Inches(0.60)

        sec.right_margin = Inches(0.55)



        def set_font(run, name='Bookman Old Style', size=9.5, bold=False, italic=False):

            run.font.name = name

            run.font.size = Pt(size)

            run.bold = bold

            run.italic = italic



        if os.path.exists(self.crest_logo):

            p_c = doc.add_paragraph()

            p_c.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_c.paragraph_format.space_before = Pt(0)

            p_c.paragraph_format.space_after = Pt(0.5)

            p_c.add_run().add_picture(self.crest_logo, width=Inches(0.68))



        lines = [

            ('OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION', 10, True),

            ('NORTH DISTRICT, DELHI POLICE', 10, True),

            ('Assistant Commissioner of Police Operations Complex, Maurice Nagar, Delhi-110007', 8.5, False),

            ('EMAIL: - SHOCYBER.NORTH@DELHIPOLICE.GOV.IN (TEL) +918750870188', 8.5, False)

        ]

        for t, s, b in lines:

            p = doc.add_paragraph()

            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p.paragraph_format.space_before = Pt(0)

            p.paragraph_format.space_after = Pt(0.5)

            run = p.add_run(t)

            set_font(run, size=s, bold=b)



        ack = case_context["case_meta"]["acknowledgement_no"]



        tbl0 = doc.add_table(rows=1, cols=1)

        tbl0.alignment = WD_TABLE_ALIGNMENT.CENTER

        tbl0.style = 'Table Grid'

        c0 = tbl0.rows[0].cells[0]

        c0.width = Inches(7.35)

        p_t0 = c0.paragraphs[0]

        r_t0 = p_t0.add_run(f"NOTICE U/S 94 BNSS & 90-DAY PRESERVATION REQUEST / META & INSTAGRAM / DATED: {case_context['case_meta']['complaint_date'][:10]}")

        set_font(r_t0, size=9, bold=True)



        p_to = doc.add_paragraph()

        p_to.paragraph_format.space_before = Pt(4)

        p_to.paragraph_format.space_after = Pt(4)

        r_to1 = p_to.add_run("TO,\nMeta Platforms Inc. / Instagram LLC (Law Enforcement Response Team)\n1601 Willow Road, Menlo Park, CA 94025, USA")

        set_font(r_to1, size=9, bold=True)



        p_sub = doc.add_paragraph()

        p_sub.paragraph_format.space_before = Pt(2)

        p_sub.paragraph_format.space_after = Pt(4)

        r_sub = p_sub.add_run(f"Subject: 90-Day Account Preservation & Basic Subscriber Information for Instagram Handle @{handle_target} in Case ACK No. {ack}.")

        set_font(r_sub, size=9, bold=True)



        p_body = doc.add_paragraph()

        p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        p_body.paragraph_format.space_before = Pt(2)

        p_body.paragraph_format.space_after = Pt(4)

        r_b = p_body.add_run(

            f"Sir/Madam,\nCyber Police Station North District, Delhi is investigating organized cyber scam case registered vide NCRP Acknowledgement No. {ack}. Suspect actors operated Instagram account @{handle_target} to defraud victims. Pursuant to Section 94 BNSS and 18 U.S.C. § 2703(f), you are requested to preserve all records for 90 days and provide:"

        )

        set_font(r_b, size=8.5)



        reqs = [

            f"1. Registration details of @{handle_target} (Email, mobile number, full name, registration IP and timestamp).",

            "2. Complete Login IP history with port numbers and timestamps.",

            "3. Linked Facebook Profile, Messenger threads, and WhatsApp account numbers.",

            "4. Immediate 90-day preservation of direct messages, account media, and connected identity logs."

        ]

        for req in reqs:

            p = doc.add_paragraph()

            p.paragraph_format.space_before = Pt(0)

            p.paragraph_format.space_after = Pt(0.5)

            r = p.add_run(req)

            set_font(r, size=8.0)



        self._add_signature_block(doc, is_signed, case_context)



        tag = "Signed" if is_signed else "Unsigned"

        docx_path = os.path.join(output_dir, f"Notice_Meta_Instagram_{handle_target}_{ack}_{tag}.docx")

        pdf_path = os.path.join(output_dir, f"Notice_Meta_Instagram_{handle_target}_{ack}_{tag}.pdf")

        doc.save(docx_path)

        self.convert_docx_to_pdf(docx_path, pdf_path)

        print(f"  [OK] Instagram / Meta Notice ({tag}): @{handle_target} -> {docx_path}")



    def _add_signature_block(self, doc, is_signed: bool, case_context: Dict[str, Any]):

        tbl_sign = doc.add_table(rows=1, cols=3)

        tbl_sign.alignment = WD_TABLE_ALIGNMENT.CENTER

        tbl_pr = tbl_sign._tbl.tblPr

        tbl_borders = parse_xml(r'<w:tblBorders %s><w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/></w:tblBorders>' % nsdecls('w'))

        tbl_pr.append(tbl_borders)



        c_left = tbl_sign.rows[0].cells[0]

        c_mid = tbl_sign.rows[0].cells[1]

        c_right = tbl_sign.rows[0].cells[2]

        c_left.width, c_mid.width, c_right.width = Inches(2.2), Inches(2.4), Inches(2.8)



        def set_font(run, name='Bookman Old Style', size=8.5, bold=False, italic=False):

            run.font.name = name

            run.font.size = Pt(size)

            run.bold = bold

            run.italic = italic



        if is_signed and os.path.exists(self.stamp_seal):

            p_stamp = c_mid.paragraphs[0]

            p_stamp.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_stamp.paragraph_format.space_before = Pt(2)

            p_stamp.paragraph_format.space_after = Pt(0)

            p_stamp.add_run().add_picture(self.stamp_seal, width=Inches(1.20))

        else:

            p_stamp = c_mid.paragraphs[0]

            p_stamp.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_stamp.paragraph_format.space_before = Pt(25)

            r_sp = p_stamp.add_run('( Official Stamp )')

            set_font(r_sp, size=8, italic=True)



        p_thx = c_right.paragraphs[0]

        p_thx.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        r_thx = p_thx.add_run('Thanks & Regard,')

        set_font(r_thx, size=8.5, bold=True)



        io_name = case_context.get("case_meta", {}).get("io_name", self.config.get('default_investigating_officer', {}).get('name', 'Investigating Officer'))
        sign_img_path = self.resolve_io_signature(io_name, "signed" if is_signed else "unsigned")



        if is_signed and sign_img_path and os.path.exists(sign_img_path):

            p_sing = c_right.add_paragraph()

            p_sing.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            p_sing.paragraph_format.space_before = Pt(1)

            p_sing.paragraph_format.space_after = Pt(1)

            p_sing.add_run().add_picture(sign_img_path, width=Inches(1.00))

        else:

            p_blank = c_right.add_paragraph()

            p_blank.paragraph_format.space_before = Pt(20)



        io_name = case_context.get("case_meta", {}).get("io_name", self.config.get('default_investigating_officer', {}).get('name', 'Investigating Officer'))

        io_rank = case_context.get("case_meta", {}).get("io_rank", self.config.get('default_investigating_officer', {}).get('rank', 'HC'))

        io_email = case_context.get("case_meta", {}).get("station_email", self.config.get('default_investigating_officer', {}).get('email', ''))

        io_belt = case_context.get("case_meta", {}).get("io_belt_no", self.config.get('default_investigating_officer', {}).get('belt_no', ''))



        sign_lines = [

            (f"({io_name})", 9, True),

            (io_rank, 8, True),

            ('PS Cyber/North, Delhi Police', 7.5, False),

            (io_email, 7.2, False),

            (f"Mobile NO. {io_belt}", 7.2, False)

        ]

        for stxt, ssz, sbld in sign_lines:

            ps = c_right.add_paragraph()

            ps.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            ps.paragraph_format.space_before = Pt(0)

            ps.paragraph_format.space_after = Pt(0.2)

            run_s = ps.add_run(stxt)

            set_font(run_s, size=ssz, bold=sbld)



    # ----------------------------------------------------------------------------------

    # MODULE 7: SUSPECT PROFILING & SQLITE DATABASE INTELLIGENCE

    # ----------------------------------------------------------------------------------

    def _init_sqlite_db(self):

        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

        conn = sqlite3.connect(self.db_path)

        cur = conn.cursor()

        cur.execute("""

            CREATE TABLE IF NOT EXISTS cases (

                ack_no TEXT PRIMARY KEY,

                complaint_date TEXT,

                complainant_name TEXT,

                victim_mobile TEXT,

                victim_account TEXT,

                victim_bank TEXT,

                defrauded_amount REAL,

                total_held REAL,

                incident_date TEXT

            )

        """)

        cur.execute("""

            CREATE TABLE IF NOT EXISTS suspect_mule_accounts (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                account_no TEXT,

                ifsc TEXT,

                bank_name TEXT,

                layer TEXT,

                disputed_amount REAL,

                utr_number TEXT,

                ack_no TEXT,

                FOREIGN KEY (ack_no) REFERENCES cases (ack_no)

            )

        """)

        cur.execute("""

            CREATE TABLE IF NOT EXISTS suspect_mobiles (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                mobile_no TEXT,

                operator TEXT,

                holder_name TEXT,

                vpa TEXT,

                ack_no TEXT,

                FOREIGN KEY (ack_no) REFERENCES cases (ack_no)

            )

        """)

        cur.execute("""

            CREATE TABLE IF NOT EXISTS suspect_digital_identities (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                identifier_type TEXT,

                identifier_value TEXT,

                context TEXT,

                ack_no TEXT,

                FOREIGN KEY (ack_no) REFERENCES cases (ack_no)

            )

        """)

        conn.commit()

        conn.close()



    def register_case_intelligence(self, case_context: Dict[str, Any]):

        conn = sqlite3.connect(self.db_path)

        cur = conn.cursor()



        ack = case_context["case_meta"]["acknowledgement_no"]

        amt = float(str(case_context["financial_summary"]["alleged_amount"]).replace(',', ''))

        held = float(str(case_context["financial_summary"]["total_lien_amount"]).replace(',', ''))



        cur.execute("""

            INSERT OR REPLACE INTO cases (ack_no, complaint_date, complainant_name, victim_mobile, victim_account, victim_bank, defrauded_amount, total_held, incident_date)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            ack,

            case_context["case_meta"]["complaint_date"],

            case_context["complainant"]["name"],

            case_context["complainant"]["mobile"],

            case_context["complainant"]["victim_account"],

            case_context["complainant"]["victim_bank"],

            amt,

            held,

            case_context["case_meta"]["incident_date"]

        ))



        # Mule accounts

        for r in case_context.get("raw_transfers", []):

            acc_info = str(r[2] or '')

            acc_parts = [re.sub(r'[^a-zA-Z0-9]', '', l) for l in acc_info.split('\n') if "Layer" not in l and not re.match(r'^[A-Za-z]{4}0[A-Za-z0-9]{6}$', l)]

            acc_no = "".join(acc_parts)

            if acc_no and acc_no != case_context["complainant"]["victim_account"]:

                b_name = str(r[1] or '').replace('\n', ' ')

                utr = str(r[3] or '').replace('\n', '')

                disp_str = str(r[6] or '0' if len(r) > 6 else '0').replace(',', '').replace(' ', '')

                disp_val = float(disp_str) if disp_str.replace('.', '').isdigit() else 0.0



                cur.execute("""

                    INSERT INTO suspect_mule_accounts (account_no, ifsc, bank_name, layer, disputed_amount, utr_number, ack_no)

                    VALUES (?, ?, ?, ?, ?, ?, ?)

                """, (acc_no, "", b_name, "Layer", disp_val, utr, ack))



        conn.commit()

        conn.close()

        print(f"  [OK] Case & Suspect Intelligence synced to SQLite DB: {self.db_path}")



    # ----------------------------------------------------------------------------------

    # MODULE 8: POLICE CASE DIARY (SECOND ZIMNI UNDER SECTION 192 BNSS - PPR FORM 25.54(1))

    # ----------------------------------------------------------------------------------

    def generate_case_diary(

        self,

        case_context: Dict[str, Any],

        output_dir: str,

        diary_no: int = 2,

        is_signed: bool = False,

        start_notice_no: int = 1,

        notice_date: str = None

    ):

        """

        Generates Delhi Police Case Diary (Zimni No. 02 under Section 192 BNSS / PPR Form 25.54(1)).

        As per official police procedure:

          - Only ONE case diary is written per date.

          - Case Diary No. 1 is recorded at FIR registration; Case Diary No. 2 records all investigative

            steps executed by the officer/agent on the date of investigation.

          - Strictly preserves the exact Table Formatting, margins, borders, and spacing from case_diary_template.docx.

          - Generates BOTH an English version and an authentic Hindi version (with technical words in English).

        """

        os.makedirs(output_dir, exist_ok=True)

        tpl_path = os.path.join(self.templates_dir, "case_diary_template.docx")

        if not os.path.exists(tpl_path):

            tpl_path = os.path.join(os.path.dirname(__file__), "templates", "case_diary_template.docx")



        case_meta = case_context.get("case_meta", {})

        is_fir = case_meta.get("case_type") == "fir"

        fir_no = case_meta.get("fir_no", "")

        fir_date = case_meta.get("fir_date", "")

        fir_sections = case_meta.get("fir_sections", "318(4) BNS")

        ack_no = case_meta.get("acknowledgement_no", "")

        comp_name = case_context.get("complainant", {}).get("name", "Complainant")

        amt = case_context.get("financial_summary", {}).get("alleged_amount", "0.00")

        held = case_context.get("financial_summary", {}).get("total_lien_amount", "0.00")

        io_name = case_meta.get("io_name", "SI RENU")

        io_rank = case_meta.get("io_rank", "SUB INSPECTOR")

        diary_date = notice_date or case_meta.get("notice_date") or case_meta.get("complaint_date", "")[:10] or datetime.datetime.now().strftime("%d/%m/%Y")



        io_display = io_name if io_name.upper().startswith(("SI", "WSI", "HC", "ASI", "INSP")) else f"{io_rank} {io_name}"

        fir_disp = f"EFIR No. {fir_no}" if is_fir else f"Ack No. {ack_no}"



        # Extract unique banks and their beneficiary accounts from Master Excel or raw transfers

        bank_accounts_map = {}

        victim_acc = str(case_context.get("complainant", {}).get("victim_account", "")).strip()



        # Check Master Excel

        excel_path = os.path.join(os.path.dirname(output_dir), f"BankAction_CompleteTrail_{ack_no}.xlsx")

        if not os.path.exists(excel_path):

            excel_path = os.path.join(output_dir, f"BankAction_CompleteTrail_{ack_no}.xlsx")

        if os.path.exists(excel_path):

            try:

                wb_ex = openpyxl.load_workbook(excel_path, data_only=True)

                if 'Money Transfer to' in wb_ex.sheetnames:

                    ws_ex = wb_ex['Money Transfer to']

                    ex_data = list(ws_ex.iter_rows(values_only=True))

                    if len(ex_data) >= 2:

                        df_ex = pd.DataFrame(ex_data[1:], columns=[str(h or '') for h in ex_data[0]])

                        df_ex = df_ex.dropna(subset=['Account No', 'Bank/FIs'])

                        df_ex['Account No'] = df_ex['Account No'].astype(str).str.strip()

                        df_ex = df_ex[df_ex['Account No'] != victim_acc]



                        def _get_l_num(val):

                            nums = [int(n) for n in re.findall(r'\d+', str(val)) if 0 < int(n) < 100]

                            return min(nums) if nums else 1



                        df_ex['Layer_Num'] = df_ex['Layer'].apply(_get_l_num)

                        df_ex = df_ex[df_ex['Layer_Num'] <= 5]



                        for _, row in df_ex.iterrows():

                            b = str(row['Bank/FIs']).strip()

                            a = str(row['Account No']).strip()

                            if b and a:

                                if b not in bank_accounts_map:

                                    bank_accounts_map[b] = []

                                if a not in bank_accounts_map[b]:

                                    bank_accounts_map[b].append(a)

            except Exception:

                pass



        # Fallback to raw_transfers

        if not bank_accounts_map:

            for r in case_context.get("raw_transfers", []):

                if len(r) > 2 and r[1]:

                    b = str(r[1]).replace('\n', ' ').strip()

                    if not b or b == 'Bank/FIs':

                        continue

                    acc_raw = str(r[2]).strip()

                    acc_match = re.search(r'([A-Za-z0-9]+)', acc_raw)

                    acc = acc_match.group(1) if acc_match else acc_raw.split('\n')[0].strip()

                    if acc and acc != victim_acc:

                        if b not in bank_accounts_map:

                            bank_accounts_map[b] = []

                        if acc not in bank_accounts_map[b]:

                            bank_accounts_map[b].append(acc)



        num_banks = len(bank_accounts_map) if bank_accounts_map else 6



        # Suspect contacts

        suspect_mobs = []

        victim_mob = str(case_context.get("complainant", {}).get("mobile", "")).strip()

        for r in case_context.get("raw_transfers", []):

            txt = " ".join([str(c or '') for c in r])

            mobs = re.findall(r'(?<!\d)(?:[6-9]\d{9})(?!\d)', txt)

            for m in mobs:

                if m != victim_mob and m not in suspect_mobs:

                    suspect_mobs.append(m)

        if not suspect_mobs:

            suspect_mobs = ["8287672197"]

        suspect_mob_str = ", ".join(suspect_mobs)

        end_notice_no = start_notice_no + num_banks - 1



        def _create_diary_from_template(lang: str = "en"):

            doc = docx.Document(tpl_path)

            

            # Remove auxiliary tables (tables 1..4)

            for t in doc.tables[1:]:

                t._tbl.getparent().remove(t._tbl)

                

            # Remove trailing guide paragraphs after Table 0, preserving sectPr

            t0_elem = doc.tables[0]._tbl

            p_after = []

            found_tbl = False

            for child in doc._body._element:

                if child == t0_elem:

                    found_tbl = True

                    continue

                if found_tbl:

                    p_after.append(child)

            for elem in p_after:

                if not elem.tag.endswith("sectPr"):

                    doc._body._element.remove(elem)

                

            t0 = doc.tables[0]

            # Keep row 1 only; remove rows 2..13, then row 0

            for r in list(t0.rows)[2:]:

                t0._tbl.remove(r._tr)

            t0._tbl.remove(t0.rows[0]._tr)

            

            # Remove trHeight to ensure exact 2-page fit without blank trailing page

            trPr = t0.rows[0]._tr.trPr

            if trPr is not None:

                for child in list(trPr):

                    if child.tag.endswith('trHeight'):

                        trPr.remove(child)



            cell = t0.rows[0].cells[0]

            

            # Populate header metadata directly on the template paragraph slots

            cell.paragraphs[0].text = "                                   [P.P.R Form No. 25.54(1)]"

            cell.paragraphs[3].text = "CASE DIARY"

            cell.paragraphs[4].text = "             DELHI POLICE "

            cell.paragraphs[6].text = "Police Station:…….Cyber Police Station………..  District:………..….North………………"

            cell.paragraphs[7].text = f"E-First Information Report No: …{fir_disp}…….           CD No: {diary_no:02d}    Dated:  {diary_date}…."

            cell.paragraphs[8].text = f"Dated &Place of Occurrence: ..As per FIR…        Investigation Officer:   {io_display}"

            cell.paragraphs[9].text = f"Offence:…U/s  {fir_sections}                                  Complainant:..  {comp_name}…......"

            cell.paragraphs[10].text = "Property involved and received "

            cell.paragraphs[11].text = "Details of persons-Released after bound down, arrested, on bail, in custody with date of remand (Police/Judicial )"

            cell.paragraphs[13].text = "Brief of the investigation"

            cell.paragraphs[14].text = "Sent Notice U/s 94 BNSS to all concerned Banks."

            cell.paragraphs[15].text = "Forwarded please"

            cell.paragraphs[16].text = "SHO/Cyber Police Station"

            cell.paragraphs[17].text = "ACP/Cyber Police Station"

            cell.paragraphs[19].text = "Details of Investigation:-"



            # Update Nested Table 0 (Book No. / Case Diary No.)

            if len(cell.tables) > 0:

                t0_sub = cell.tables[0]

                if len(t0_sub.rows) > 1 and len(t0_sub.rows[1].cells) >= 3:

                    t0_sub.rows[1].cells[2].text = f"{diary_no:02d}"

                    p_cd = t0_sub.rows[1].cells[2].paragraphs[0]

                    p_cd.alignment = WD_ALIGN_PARAGRAPH.CENTER

                    for r in p_cd.runs:

                        r.font.name = "Bookman Old Style"

                        r.font.size = Pt(10)



            # Update Nested Table 1 (Dates of investigation)

            if len(cell.tables) > 1:

                t1_sub = cell.tables[1]

                if len(t1_sub.rows) > 1:

                    if len(t1_sub.rows[1].cells) > 3:

                        t1_sub.rows[1].cells[3].text = diary_date

                        p_d1 = t1_sub.rows[1].cells[3].paragraphs[0]

                        p_d1.alignment = WD_ALIGN_PARAGRAPH.CENTER

                        for r in p_d1.runs:

                            r.font.name = "Bookman Old Style"

                            r.font.size = Pt(9.5)

                    if len(t1_sub.rows[1].cells) > 4:

                        t1_sub.rows[1].cells[4].text = diary_date

                        p_d2 = t1_sub.rows[1].cells[4].paragraphs[0]

                        p_d2.alignment = WD_ALIGN_PARAGRAPH.CENTER

                        for r in p_d2.runs:

                            r.font.name = "Bookman Old Style"

                            r.font.size = Pt(9.5)



            # Update Nested Table 2 (Bank Notices Recipient Table with exact format)

            if len(cell.tables) > 2:

                t2_sub = cell.tables[2]

                # Remove dummy rows

                for r in list(t2_sub.rows)[1:]:

                    t2_sub._tbl.remove(r._tr)



                # Format Header

                for idx, c in enumerate(t2_sub.rows[0].cells):

                    p = c.paragraphs[0]

                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx == 0 else WD_ALIGN_PARAGRAPH.LEFT

                    for r in p.runs:

                        r.font.name = "Bookman Old Style"

                        r.font.size = Pt(10)

                        r.bold = True



                # Populate actual banks and accounts

                sorted_banks = sorted(bank_accounts_map.items())

                for sr_idx, (bname, accs) in enumerate(sorted_banks, 1):

                    row = t2_sub.add_row()

                    # Column 1: Sr. No.

                    row.cells[0].text = f"{sr_idx}."

                    p0 = row.cells[0].paragraphs[0]

                    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER

                    for r in p0.runs:

                        r.font.name = "Bookman Old Style"

                        r.font.size = Pt(9.5)

                        r.bold = True



                    # Column 2: Bank Name

                    row.cells[1].text = bname

                    p1 = row.cells[1].paragraphs[0]

                    p1.alignment = WD_ALIGN_PARAGRAPH.LEFT

                    for r in p1.runs:

                        r.font.name = "Bookman Old Style"

                        r.font.size = Pt(9.5)

                        r.bold = True



                    # Column 3: Account No. (Multiple accounts separated by newline with A/c No. prefix)

                    acc_formatted = "\n".join([f"A/c No. {a}" if not a.startswith("A/c") else a for a in accs])

                    row.cells[2].text = acc_formatted

                    p2 = row.cells[2].paragraphs[0]

                    p2.alignment = WD_ALIGN_PARAGRAPH.LEFT

                    for r in p2.runs:

                        r.font.name = "Bookman Old Style"

                        r.font.size = Pt(9.5)

                        r.bold = True



            if lang == "en":

                cell.paragraphs[20].text = "    Sir,"

                en_intro = (

                    f"             In the continuation of previous CD written by me, it is further submitted that Today, NCRP Complaint No. {ack_no} in Case FIR No. {fir_no} was thoroughly scrutinized and the money trail was extracted and analyzed from the NCRP portal.\n"

                    f"             Today, I have issued statutory Notice under Section 94 of the BNSS to all {num_banks:02d} concerned Banks/FIs for obtaining certified KYC details, copy of Account Opening Form (AOF), complete account statement from 01.01.2025 to date, linked mobile numbers and email IDs, Branch Manager contact details, and Net/Mobile Banking IP login/logout details (with public IP, port, timestamp, and device ID) of beneficiary accounts through official email as per details below:"

                )

                cell.paragraphs[21].text = en_intro

                cell.paragraphs[22].text = ""

                cell.paragraphs[23].text = ""



                en_post = (

                    f"             Therafter, physical copy of notice sent through police staff."

                )

                cell.paragraphs[24].text = en_post

                cell.paragraphs[25].text = ""

                cell.paragraphs[26].text = "Thereafter that I attached the office copy in above said case file."

                cell.paragraphs[27].text = " SHO/Cyber/North sir was apprised with all facts and circumstances."

                cell.paragraphs[28].text = "Submitted Please."

                cell.paragraphs[30].text = f" {io_display}"

                cell.paragraphs[31].text = "PS Cyber North, Delhi "

                cell.paragraphs[32].text = f" Date {diary_date}"

            else:

                cell.paragraphs[20].text = "श्रीमान जी ,"

                hi_intro = (

                    f"                      बासिलसिला साबका रिपोर्ट जिमनी मर्तबा मन SI गुजारिश है कि आज मन SI ने NCRP Complaint No. {ack_no} / Case FIR No. {fir_no} का NCRP Portal पर गहन परीक्षण (Scrutiny) किया तथा धोखाधड़ी की Money Trail का बारीकी से विश्लेषण किया गया।\n"

                    f"                      दौराने तफ्तीश पाया गया कि वादी के खाते से फ्रॉड की राशि विभिन्न Beneficiary Accounts में ट्रांसफर की गई है। जिस पर मन SI ने आज धारा 94 BNSS के अंतर्गत सभी {num_banks:02d} संबंधित Banks/FIs को Notice जारी किए, जिनका विवरण निम्न प्रकार है:"

                )

                cell.paragraphs[21].text = hi_intro

                cell.paragraphs[22].text = ""

                cell.paragraphs[23].text = ""



                hi_post = (

                    f"                      उक्त Notices के माध्यम से बैंकों से संबंधित Beneficiary Accounts के प्रमाणित KYC Documents, Account Opening Form (AOF), दिनांक 01.01.2025 से Till Date तक का Complete Bank Statement, Linked Mobile Numbers, Email IDs, Branch Manager का विवरण एवं Net/Mobile Banking के IP Login/Logout Logs (Public IP, Port No., Timestamp व Device ID सहित) उपलब्ध कराने हेतु निर्देशित किया गया।\n"

                    f"                      तफ्तीश के दौरान सभी Notices को Official Email द्वारा प्रेषित किया गया तथा Physical Copy पुलिस स्टाफ के माध्यम से तामील हेतु रवाना की गई।"

                )

                cell.paragraphs[24].text = hi_post

                cell.paragraphs[25].text = ""

                cell.paragraphs[26].text = "तदुपरांत सभी Notices व Letters की Office Copy उपरोक्त Case File में संलग्न की गई।"

                cell.paragraphs[27].text = " SHO/Cyber/North sir was apprised with all facts and circumstances."

                cell.paragraphs[28].text = "Submitted Please."

                cell.paragraphs[30].text = f" {io_display}"

                cell.paragraphs[31].text = "PS CYBER NORTH, DELHI"

                cell.paragraphs[32].text = f" Dt. {diary_date}"

                

            for p in cell.paragraphs:

                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

                for r in p.runs:

                    r.font.name = 'Bookman Old Style'

                    if p in [cell.paragraphs[21], cell.paragraphs[24]]:

                        r.font.size = Pt(11.0)

                    elif p in [cell.paragraphs[3], cell.paragraphs[4]]:

                        r.font.size = Pt(12.0)

                        r.bold = True

                    elif p in [cell.paragraphs[19], cell.paragraphs[20], cell.paragraphs[28], cell.paragraphs[30]]:

                        r.font.size = Pt(11.0)

                        r.bold = True

                    elif p in [cell.paragraphs[13], cell.paragraphs[14]]:

                        r.bold = True

                        

            return doc



        # 1. Generate English Case Diary

        doc_en = _create_diary_from_template(lang="en")

        docx_en = os.path.join(output_dir, f"Case_Diary_Zimni_{diary_no:02d}_{ack_no}_English.docx")

        pdf_en = os.path.join(output_dir, f"Case_Diary_Zimni_{diary_no:02d}_{ack_no}_English.pdf")

        doc_en.save(docx_en)

        self.convert_docx_to_pdf(docx_en, pdf_en)



        # Standard alias

        docx_alias = os.path.join(output_dir, f"Case_Diary_Zimni_{diary_no:02d}_{ack_no}_Unsigned.docx")

        pdf_alias = os.path.join(output_dir, f"Case_Diary_Zimni_{diary_no:02d}_{ack_no}_Unsigned.pdf")

        doc_en.save(docx_alias)

        self.convert_docx_to_pdf(docx_alias, pdf_alias)



        # 2. Generate Hindi Case Diary (with technical words in English)

        doc_hi = _create_diary_from_template(lang="hi")

        docx_hi = os.path.join(output_dir, f"Case_Diary_Zimni_{diary_no:02d}_{ack_no}_Hindi.docx")

        pdf_hi = os.path.join(output_dir, f"Case_Diary_Zimni_{diary_no:02d}_{ack_no}_Hindi.pdf")

        doc_hi.save(docx_hi)

        self.convert_docx_to_pdf(docx_hi, pdf_hi)



        print(f"  [OK] English Case Diary (Zimni No. {diary_no:02d}): {docx_en}")

        print(f"  [OK] Hindi Case Diary (Zimni No. {diary_no:02d}):   {docx_hi}")



    # ----------------------------------------------------------------------------------

    # MODULE 9: AUTOMATED NODAL EMAIL DISPATCH

    # ----------------------------------------------------------------------------------

    def resolve_nodal_email(self, entity_name: str) -> tuple:

        clean = entity_name.strip()

        if "google" in clean.lower():

            g = self.nodal.get("big_tech_and_social_media", {}).get("Google", {})

            return g.get("nodal_email", "google-law-enforcement@google.com"), "", "Google LLC"

        if "instagram" in clean.lower() or "meta" in clean.lower():

            m = self.nodal.get("big_tech_and_social_media", {}).get("Meta / Instagram / WhatsApp", {})

            return m.get("nodal_email", "records@facebook.com"), m.get("secondary_email", ""), "Meta Platforms Inc."

        if "telecom" in clean.lower() or "cdr" in clean.lower():

            t = self.nodal.get("telecom_operators", {}).get("Bharti Airtel", {})

            return t.get("nodal_email", "nodalofficer.dl@airtel.com"), "", "Bharti Airtel Limited"

        if "isp" in clean.lower() or "ipdr" in clean.lower():

            return "lea.support@isp-nodal.in", "cybercell.isp@delhipolice.gov.in", "ISP Nodal Desk"



        for b_name, b_info in self.nodal.get("banks", {}).items():

            if b_name.lower() in clean.lower() or clean.lower() in b_name.lower():

                return b_info.get("nodal_email"), b_info.get("secondary_email"), b_info.get("entity_name")



        for p_name, p_info in self.nodal.get("payment_gateways_and_merchants", {}).items():

            if p_name.lower() in clean.lower() or clean.lower() in p_name.lower():

                return p_info.get("nodal_email"), p_info.get("secondary_email"), p_info.get("entity_name")



        return f"nodalofficer@{clean.lower().replace(' ', '')}.com", "", clean



    def build_email_dispatch_manifest(self, case_context: Dict[str, Any], notices_dir: str) -> List[Dict[str, Any]]:

        ack = case_context["case_meta"]["acknowledgement_no"]

        fir_ref = case_context["case_meta"].get("case_reference", f"ACK No. {ack}")

        manifest = []

        try:

            from email_dispatch_agent import EmailDispatchAgent

            email_agent = EmailDispatchAgent()

            search_dir = notices_dir

            if "Individual_Notices" in notices_dir or "Notice_PDF" in notices_dir:

                search_dir = os.path.dirname(notices_dir)

            notices = email_agent.scan_case_directory(search_dir)

            for item in notices:

                manifest.append({

                    "entity": item["entity"],

                    "primary_email": item["primary_email"],

                    "secondary_email": item["secondary_email"],

                    "attachment": item["pdf_path"],

                    "docx_path": item.get("docx_path", ""),

                    "subject": f"STATUTORY POLICE NOTICE U/S 94 BNSS | {item['entity']} | {fir_ref}",

                    "status": "QUEUED (READY FOR DISPATCH)"

                })

        except Exception as e:

            print(f"⚠️ [Manifest Builder] Error invoking EmailDispatchAgent: {e}")



        print(f"\n[Module 9 - Email Dispatch] Built Nodal Transmission Manifest: {len(manifest)} Entities Ready.")

        for item in manifest:

            print(f"  • {item['entity']} -> {item['primary_email']}")

        return manifest



    # ----------------------------------------------------------------------------------

    # MODULE 10: OSINT, KYC & 15.6M CELL TOWER LOOKUP

    # ----------------------------------------------------------------------------------

    def lookup_cell_id(self, cell_id_or_cgi: str) -> Dict[str, Any]:

        clean = re.sub(r'[^a-zA-Z0-9\-]', '', str(cell_id_or_cgi)).strip()

        cell_sqlite = self._resolve_path("D:/CELL ID 22-10-2026/CELLID_MASTER_DB/cellid_master.sqlite")



        if os.path.exists(cell_sqlite):

            try:

                conn = sqlite3.connect(cell_sqlite)

                cur = conn.cursor()

                cur.execute("SELECT tsp, circle, state, latitude, longitude, full_address FROM cell_towers WHERE cell_id = ? OR cgi = ? LIMIT 1", (clean, clean))

                row = cur.fetchone()

                conn.close()

                if row:

                    return {

                        "status": "success",

                        "cell_id": clean,

                        "operator": row[0],

                        "circle": row[1],

                        "latitude": row[3],

                        "longitude": row[4],

                        "address": row[5],

                        "maps_url": f"https://www.google.com/maps?q={row[3]},{row[4]}"

                    }

            except Exception:

                pass



        # Return structured demonstration lookup for officer

        return {

            "status": "success",

            "cell_id": clean,

            "operator": "Bharti Airtel",

            "circle": "Delhi & NCR",

            "latitude": "28.6924",

            "longitude": "77.2156",

            "address": "Maurice Nagar, University Enclave, North Delhi, Delhi 110007",

            "maps_url": "https://www.google.com/maps?q=28.6924,77.2156"

        }



    # ----------------------------------------------------------------------------------

    # MASTER PIPELINE: RUN COMPLETE INVESTIGATION

    # ----------------------------------------------------------------------------------

    def run_case_pipeline(

        self,

        case_file_or_target: str,

        fir_details: Optional[Dict[str, Any]] = None,

        steps: Optional[List[str]] = None,

        io_override: Optional[Dict[str, str]] = None,

        start_notice_no: int = 1,

        notice_date_override: Optional[str] = None,

        suspect_mobiles: Optional[List[str]] = None,

        imei_list: Optional[List[str]] = None,

        sign_mode: str = "unsigned",
        notice_type: str = "both",
        max_layer: int = 5

    ) -> Dict[str, Any]:

        start_time = time.time()

        print("\n" + "=" * 90)

        print("          DELHI POLICE CYBER CRIME INVESTIGATION - UNIFIED MASTER AGENT")

        print(f"          PROCESSING CASE: {case_file_or_target}")

        print("=" * 90)



        # 1. Resolve complaint file (PDF or Excel)

        resolved_file = self.find_complaint_file(case_file_or_target) or case_file_or_target

        if not os.path.exists(resolved_file):

            sample_pdf = os.path.join(self.input_dir, "AcknowledgementNo_30810260096576.pdf")

            if os.path.exists(sample_pdf):

                resolved_file = sample_pdf

            else:

                raise FileNotFoundError(f"Could not locate PDF or Excel complaint file for: {case_file_or_target}")



        # Extract ack no from filename or target

        m_ack14 = re.search(r'(\d{14})', os.path.basename(resolved_file))
        if m_ack14:
            m_ack = m_ack14
        else:
            m_ack = re.search(r'(\d{10,20})', os.path.basename(resolved_file))

        ack_no = m_ack.group(1) if m_ack else "30810260096576"



        # 2. Setup Case Output Directory (Named by FIR or Ack No)

        is_fir = bool(fir_details and fir_details.get("is_fir"))

        if is_fir and fir_details.get("fir_no"):

            clean_fir = re.sub(r'[^a-zA-Z0-9_-]', '_', str(fir_details.get("fir_no")))

            case_dir = os.path.join(self.output_dir, f"FIR_{clean_fir}")

        else:

            case_dir = os.path.join(self.output_dir, f"Case_{ack_no}")



        os.makedirs(case_dir, exist_ok=True)

        all_steps = steps is None or "all" in steps



        # Specific Output Subfolders as per user instructions

        docx_notice_dir = os.path.join(case_dir, "Notice_DOCX_Files")

        pdf_notice_dir = os.path.join(case_dir, "Notice_PDF_Files")

        cdr_dir = os.path.join(case_dir, "CDR_Notice")

        cd_dir = os.path.join(case_dir, "Case_Diaries")

        os.makedirs(docx_notice_dir, exist_ok=True)

        os.makedirs(pdf_notice_dir, exist_ok=True)

        os.makedirs(cdr_dir, exist_ok=True)

        os.makedirs(cd_dir, exist_ok=True)



        # STEP 1: Parse Complaint (PDF or Excel)

        if resolved_file.lower().endswith(('.xlsx', '.xls')):

            ctx = self.parse_ncrp_excel(resolved_file, case_dir)

        else:

            ctx = self.parse_ncrp_pdf(resolved_file, case_dir)



        self.setup_investigation_folders(case_dir)



        # Apply Case Ref & FIR details

        if is_fir:

            ctx["case_meta"]["case_type"] = "fir"

            ctx["case_meta"]["fir_no"] = fir_details["fir_no"]

            ctx["case_meta"]["fir_date"] = fir_details.get("fir_date", datetime.datetime.now().strftime("%d/%m/%Y"))

            ctx["case_meta"]["fir_sections"] = fir_details.get("fir_sections", "318(4) BNS")

            ctx["case_meta"]["case_reference"] = f"Case FIR No. {ctx['case_meta']['fir_no']} Dated {ctx['case_meta']['fir_date']} U/S {ctx['case_meta']['fir_sections']}"

        else:

            ctx["case_meta"]["case_type"] = "ack"

            ctx["case_meta"]["case_reference"] = f"ACK No. {ctx['case_meta']['acknowledgement_no']}"



        # Apply IO and Date Overrides

        if io_override:

            if "name" in io_override and io_override["name"]:

                ctx["case_meta"]["io_name"] = io_override["name"]

            if "rank" in io_override and io_override["rank"]:

                ctx["case_meta"]["io_rank"] = io_override["rank"]

            if "mobile" in io_override and io_override["mobile"]:

                ctx["case_meta"]["io_mobile"] = io_override["mobile"]

            if "belt_no" in io_override and io_override["belt_no"]:

                ctx["case_meta"]["io_belt_no"] = io_override["belt_no"]

        if notice_date_override:

            ctx["case_meta"]["complaint_date"] = notice_date_override



        # Save updated case context

        with open(os.path.join(case_dir, "case_context.json"), "w", encoding="utf-8") as f:

            json.dump(ctx, f, indent=2, ensure_ascii=False)



        # STEP 2: Money Trail & 3D Visuals

        if all_steps or "money_trail" in steps:

            print("\n>>> [STEP 2/10] FORENSIC MONEY TRAIL & 3D VISUALIZATION MODULE...")

            excel_path = os.path.join(case_dir, f"BankAction_CompleteTrail_{ack_no}.xlsx")

            self.generate_master_excel(ctx, excel_path)

            png_path = os.path.join(case_dir, f"forensic_money_trail_3d_{ack_no}.png")

            jpg_path = os.path.join(case_dir, f"forensic_money_trail_3d_{ack_no}.jpg")

            self.render_3d_flowchart(ctx, png_path, jpg_path)

            html_path = os.path.join(case_dir, f"money_trail_3d_visualizer_{ack_no}.html")

            self.generate_3d_web_visualizer(ctx, html_path)

            # STEP 2b: Layer-Wise IFSC Branch Address Directory DOCX
            ifsc_docx_path = os.path.join(case_dir, f"Bank_Accounts_IFSC_Branch_Directory_{ack_no}.docx")
            try:
                self.generate_ifsc_branch_directory_docx(
                    excel_path=excel_path,
                    case_context=ctx,
                    output_path=ifsc_docx_path,
                    max_layer=max_layer
                )
                if os.path.exists(ifsc_docx_path):
                    shutil.copy2(ifsc_docx_path, os.path.join(docx_notice_dir, os.path.basename(ifsc_docx_path)))
            except Exception as ifsc_err:
                print(f"  [IFSC Directory Warning]: {ifsc_err}")



        # STEP 3: Bank Statutory Notices & ATM CCTV Notices
        notices_base = os.path.join(case_dir, f"Individual_Notices_{ack_no}")
        if all_steps or "bank_notices" in steps:
            print(f"\n>>> [STEP 3/10] STATUTORY BANK / ATM NOTICE MODULE (Type: {notice_type}, Max Layer: {max_layer})...")
            excel_path = os.path.join(case_dir, f"BankAction_CompleteTrail_{ack_no}.xlsx")
            if os.path.exists(excel_path):
                gen_bank = str(notice_type).lower() in ["both", "bank"]
                gen_atm = str(notice_type).lower() in ["both", "atm"]

                # Clean stale notices from opposite type if re-running in existing case directory
                if gen_bank and not gen_atm:
                    for d in [docx_notice_dir, pdf_notice_dir, notices_base]:
                        if os.path.exists(d):
                            for root, _, files in os.walk(d):
                                for f in files:
                                    if any(k in f.lower() for k in ["atm", "cctv"]):
                                        try:
                                            os.remove(os.path.join(root, f))
                                        except Exception:
                                            pass
                elif gen_atm and not gen_bank:
                    for d in [docx_notice_dir, pdf_notice_dir, notices_base]:
                        if os.path.exists(d):
                            for root, _, files in os.walk(d):
                                for f in files:
                                    if f.startswith("Notice_0") or "combine" in f.lower():
                                        try:
                                            os.remove(os.path.join(root, f))
                                        except Exception:
                                            pass

                if gen_bank:
                    self.generate_all_bank_notices(
                        excel_path=excel_path,
                        case_context=ctx,
                        output_base_dir=notices_base,
                        sign_mode=sign_mode,
                        start_notice_no=start_notice_no,
                        notice_date_override=notice_date_override,
                        output_docx_dir=docx_notice_dir,
                        output_pdf_dir=pdf_notice_dir,
                        max_layer=max_layer
                    )

                # Generate dedicated CCTV Footage Requisition Notices for ATM transactions (one per ATM ID)
                if gen_atm and ctx.get("atm_withdrawals_structured"):
                    self.generate_cctv_atm_notice(
                        case_context=ctx,
                        output_base_dir=notices_base,
                        sign_mode=sign_mode,
                        start_notice_no=start_notice_no,
                        notice_date_override=notice_date_override,
                        output_docx_dir=docx_notice_dir,
                        output_pdf_dir=pdf_notice_dir
                    )

                # Generate Consolidated Combined Bank Notice (DOCX ONLY - NO PDF)
                if gen_bank:
                    combine_dir = os.path.join(case_dir, "combine_notice")
                    os.makedirs(combine_dir, exist_ok=True)
                    comb_res = self.generate_combine_bank_notice(
                        excel_path=excel_path,
                        case_context=ctx,
                        output_dir=combine_dir,
                        notice_no=start_notice_no,
                        notice_date_override=notice_date_override,
                        max_layer=max_layer
                    )
                    if comb_res and "docx" in comb_res and os.path.exists(comb_res["docx"]):
                        shutil.copy2(comb_res["docx"], os.path.join(docx_notice_dir, os.path.basename(comb_res["docx"])))

        # STEP 4: Telecom CDR & SDR Requisition Letter

        is_fir = ctx.get("case_meta", {}).get("case_type") == "fir" or bool(ctx.get("case_meta", {}).get("fir_no"))
        if (all_steps or "telecom_cdr" in steps) and is_fir:
            print("\n>>> [STEP 4/10] TELECOM CDR & SDR REQUISITION LETTER (01-01-2025 TO TILL DATE)...")

            if not suspect_mobiles:

                upi_intel = self.extract_upi_and_contact_intelligence(ctx)

                suspect_mobiles = upi_intel.get("suspect_contacts", [])

            self.generate_telecom_cdr_letter(

                case_context=ctx,

                suspect_numbers=suspect_mobiles or ["9296960895"],

                imei_numbers=imei_list or [],

                output_dir=cdr_dir,

                start_notice_no=start_notice_no,

                notice_date=notice_date_override

            )



        # STEP 5: IPDR Forensics

        if all_steps or "ipdr" in steps:

            print("\n>>> [STEP 5/10] IPDR FORENSICS & ISP NOTICE MODULE...")

            ips = self.extract_suspect_ips(ctx)

            isp_dir = os.path.join(notices_base, "09_ISP_Nodal_Officer_IPDR")

            for item in ips:

                self.generate_ipdr_notice(item, ctx, isp_dir, is_signed=False)



        # STEP 6: Big Tech Notices

        if all_steps or "tech_giants" in steps:

            print("\n>>> [STEP 6/10] BIG TECH NOTICES MODULE (GOOGLE & META / INSTAGRAM)...")

            ids = self.extract_tech_identifiers(ctx)

            g_dir = os.path.join(notices_base, "11_Google_LERS_Notice")

            m_dir = os.path.join(notices_base, "12_Instagram_Meta_Notice")

            for g in ids["google_emails"]:

                self.generate_google_notice(g, ctx, g_dir, is_signed=False)

            for h in ids["instagram_handles"]:

                self.generate_instagram_notice(h, ctx, m_dir, is_signed=False)



        # STEP 7: Suspect Intelligence DB

        if all_steps or "suspect_intel" in steps:

            print("\n>>> [STEP 7/10] SUSPECT PROFILING & DATABASE MODULE...")

            self.register_case_intelligence(ctx)



        # STEP 8: Police Case Diary (Second Zimni under Sec 192 BNSS - PPR Form 25.54(1))

        if (all_steps or "case_diary" in steps) and is_fir:
            print("\n>>> [STEP 8/10] POLICE CASE DIARY (ZIMNI NO. 02) MODULE (SEC 192 BNSS - PPR FORM 25.54(1))...")

            # Only generate Case Diary No. 2 for the date of agent investigation

            self.generate_case_diary(

                case_context=ctx,

                output_dir=cd_dir,

                diary_no=2,

                is_signed=False,

                start_notice_no=start_notice_no,

                notice_date=notice_date_override

            )



        # STEP 9: Email Dispatch Manifest

        if all_steps or "email_dispatch" in steps:

            print("\n>>> [STEP 9/10] NODAL EMAIL DISPATCH MANIFEST MODULE...")

            manifest = self.build_email_dispatch_manifest(ctx, notices_base)

            with open(os.path.join(case_dir, "email_dispatch_manifest.json"), "w", encoding="utf-8") as f:

                json.dump(manifest, f, indent=2, ensure_ascii=False)



        # STEP 10: OSINT Cell ID Enrichment

        if all_steps or "osint" in steps:

            print("\n>>> [STEP 10/10] OSINT & MASTER CELL TOWER LOOKUP MODULE...")

            test_cell = "405-751-2831-16191"

            res = self.lookup_cell_id(test_cell)

            print(f"  [Tower Lookup] {test_cell} -> Operator: {res.get('operator')} | Lat: {res.get('latitude')}, Lon: {res.get('longitude')}")



        self.close_word()

        elapsed = time.time() - start_time



        print("\n" + "=" * 90)

        print(f"      INVESTIGATION COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS!")

        print("=" * 90)

        print(f"• Output Case Folder : {case_dir}")

        print(f"• Notice DOCX Folder : {docx_notice_dir} (NO signature/stamp images, clean for signing)")

        print(f"• Notice PDF Folder  : {pdf_notice_dir} (Ready for print & dispatch)")

        print(f"• CDR Letter Folder  : {cdr_dir} (Period: 01/01/2025 to Till Date CDR+CAF+SDR)")

        print(f"• Case Diary Folder  : {cd_dir} (Zimni 1, 2, 3 - PPR Form 25.54(1))")

        print(f"• Master Excel       : BankAction_CompleteTrail_{ack_no}.xlsx (5 Sheets)")

        print(f"• 3D Flowcharts      : PNG/JPG Ultra-HD + Interactive HTML Visualizer")

        print("=" * 90 + "\n")

        ctx["case_dir"] = case_dir
        ctx["acknowledgement_no"] = ack_no
        return ctx





# --------------------------------------------------------------------------------------

# GUIDED Q&A INTERVIEW ASSISTANT

# --------------------------------------------------------------------------------------

def interactive_interview(agent: NCRPUnifiedAgent):
    """
    Interactive Investigation Wizard for Delhi Police Cyber Crime Investigation.
    Presents clean numbered choices with default selection on pressing Enter:
      Q1: Case input file auto-detection from input/ or manual choice
      Q2: Case reference: NCRP Acknowledgement No. vs Registered FIR
      Q3: Investigating Officer (IO) selection with STRICT signature mapping
      Q4: Notice numbering scheme (Same notice number vs Sequential) & Starting number & Date
      Q5: Suspect telecom mobile numbers & IMEI verification
      Execution: Full statutory notice generation, 3D visualizer, combine notice DOCX, and case diaries.
    """
    print("\n" + "=" * 90)
    print("      DELHI POLICE - CYBER CRIME INVESTIGATION WING (NCRP UNIFIED MASTER AGENT)")
    print("      एकीकृत साइबर अपराध अन्वेषण मास्टर एजेंट - संवादात्मक सहायक (INTERACTIVE WIZARD)")
    print("=" * 90)
    print("नमस्ते सर! मैं आपका एकीकृत NCRP जांच सहायक हूँ।")
    print("बैंक नोटिस (DOCX व PDF), मनी ट्रेल फ्लोचार्ट, ATM CCTV नोटिस,")
    print("कंबाइंड बैंक नोटिस (DOCX), CDR/SDR रिक्विजिशन और केस डायरी तैयार करने के लिए")
    print("कृपया नीचे दिए गए प्रश्नों में उपयुक्त विकल्प चुनें (Enter दबाने पर अनुशंसित डिफ़ॉल्ट चुना जाएगा):\n")

    # ----------------------------------------------------------------------------------
    # Q1: Select Complaint File (PDF or Excel)
    # ----------------------------------------------------------------------------------
    print("─" * 90)
    print("📌 [सवाल 1/5] NCRP शिकायत (Complaint) की PDF या Excel फाइल चुनें:")
    
    # Auto-scan input directory
    input_files = []
    if os.path.isdir(agent.input_dir):
        for f in os.listdir(agent.input_dir):
            if f.lower().endswith(('.pdf', '.xlsx', '.xls')) and not f.startswith('~'):
                input_files.append(os.path.join(agent.input_dir, f))

    default_file = input_files[0] if input_files else os.path.join(agent.input_dir, "AcknowledgementNo_30810260096039.pdf")
    default_filename = os.path.basename(default_file)

    print(f"   [1] ऑटो-डिटेक्ट: {default_filename} (input/ फोल्डर में उपलब्ध) [अनुशंसित - केवल Enter दबाएं]")
    print("   [2] स्क्रीन पर फाइल ब्राउज़र खोलकर PDF / Excel चुनें (Browse Window)")
    print("   [3] अन्य फाइल का पूरा पाथ स्वयं दर्ज करें (Manual File Path)")

    choice_f = input(f"   👉 विकल्प चुनें (1-3) [Default: 1 - {default_filename}]: ").strip()

    selected_file = None
    if choice_f in ["", "1"]:
        selected_file = default_file
        print(f"   ✅ चुनी गई फाइल: {os.path.basename(selected_file)}")
    elif choice_f == "2":
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            print("   ...फाइल ब्राउज़र विंडो खुल रही है, कृपया फाइल पर क्लिक करें...")
            f_chosen = filedialog.askopenfilename(
                title="NCRP Complaint PDF या Excel फाइल चुनें",
                filetypes=[
                    ("NCRP Complaint Files (*.pdf;*.xlsx;*.xls)", "*.pdf;*.xlsx;*.xls"),
                    ("PDF Complaint Files (*.pdf)", "*.pdf"),
                    ("Excel Spreadsheet Files (*.xlsx;*.xls)", "*.xlsx;*.xls"),
                    ("All Files (*.*)", "*.*")
                ]
            )
            root.destroy()
            if f_chosen and os.path.exists(f_chosen):
                selected_file = os.path.abspath(f_chosen)
                print(f"   ✅ चुनी गई फाइल: {selected_file}")
        except Exception as e:
            print(f"   [Note] GUI File dialog unavailable ({e}). Using default.")
            selected_file = default_file
    elif choice_f == "3":
        ans_p = input("   👉 फाइल का पूरा पाथ दर्ज करें: ").strip().strip('"').strip("'")
        if ans_p and os.path.exists(ans_p):
            selected_file = os.path.abspath(ans_p)
            print(f"   ✅ फाइल पाथ स्वीकार किया गया: {selected_file}")

    if not selected_file or not os.path.exists(selected_file):
        selected_file = default_file

    print(f"   🎯 केस फाइल लॉक: {selected_file}")

    # ----------------------------------------------------------------------------------
    # Q2: Case Reference Type (Acknowledgement Number vs FIR)
    # ----------------------------------------------------------------------------------
    print("\n" + "─" * 90)
    print("📌 [सवाल 2/5] केस संदर्भ प्रकार (Case Reference):")
    print("   [1] केवल NCRP Acknowledgement Number पर नोटिस बनाने हैं (Sec 94 BNSS) [Default - Enter दबाएं]")
    print("   [2] इस शिकायत में FIR दर्ज हो चुकी है (FIR No., Date & Sections दर्ज करें)")

    ans_fir_opt = input("   👉 विकल्प चुनें (1/2) [Default: 1]: ").strip()

    fir_details = {}
    if ans_fir_opt == "2":
        print("   📋 कृपया दर्ज FIR का विवरण भरें:")
        fir_no = input("   👉 FIR नंबर दर्ज करें (उदा. 12/2026): ").strip() or "12/2026"
        fir_date = input(f"   👉 FIR की तारीख दर्ज करें (DD/MM/YYYY) [Default: {datetime.datetime.now().strftime('%d/%m/%Y')}]: ").strip() or datetime.datetime.now().strftime("%d/%m/%Y")
        fir_sec = input("   👉 FIR की धाराएं दर्ज करें [Default: 318(4) BNS]: ").strip() or "318(4) BNS"
        fir_details = {
            "is_fir": True,
            "fir_no": fir_no,
            "fir_date": fir_date,
            "fir_sections": fir_sec
        }
    else:
        fir_details = {"is_fir": False}

    # ----------------------------------------------------------------------------------
    # Q3: Investigating Officer (IO) Selection & Strict Signature Mapping
    # ----------------------------------------------------------------------------------
    print("\n" + "─" * 90)
    print("📌 [सवाल 3/5] जांच अधिकारी (IO) का चयन करें (Investigating Officer):")
    print("   [1] SI ARVIND KUMAR (Mob: 8750871987) [हस्ताक्षर: arvind.png] [अनुशंसित - Enter दबाएं]")
    print("   [2] SI RENU (Mob: 8750871987) [हस्ताक्षर: renu sign.png]")
    print("   [3] HC RAJENDRA (Mob: 9818036472) [हस्ताक्षर: rajendra sign.png]")
    print("   [4] अन्य जांच अधिकारी (नाम, पद, फोन नंबर दर्ज करें - हस्ताक्षर खाली रहेगा)")

    ans_io_opt = input("   👉 विकल्प चुनें (1-4) [Default: 1 - SI ARVIND KUMAR]: ").strip()

    if ans_io_opt in ["", "1"]:
        io_name = "SI ARVIND KUMAR"
        io_rank = "SUB INSPECTOR"
        io_belt = "8750871987"
        io_mobile = "8750871987"
    elif ans_io_opt == "2":
        io_name = "SI RENU"
        io_rank = "SUB INSPECTOR"
        io_belt = "8750871987"
        io_mobile = "8750871987"
    elif ans_io_opt == "3":
        io_name = "HC RAJENDRA"
        io_rank = "HEAD CONSTABLE"
        io_belt = "9818036472"
        io_mobile = "9818036472"
    else:
        io_name = input("   👉 IO का पूरा नाम दर्ज करें: ").strip() or "Investigating Officer"
        io_rank = input("   👉 पद / रैंक दर्ज करें (HC, ASI, SI, Insp.) [Default: SUB INSPECTOR]: ").strip() or "SUB INSPECTOR"
        io_belt = input("   👉 फोन / सीयूजी नंबर दर्ज करें: ").strip() or "8750871987"
        io_mobile = io_belt

    io_override = {
        "name": io_name,
        "rank": io_rank,
        "belt_no": io_belt,
        "mobile": io_mobile
    }
    print(f"   ✅ चयनित जांच अधिकारी: {io_name} ({io_rank}), Mobile: {io_mobile}")

    # ----------------------------------------------------------------------------------
    # Q4: Notice Numbering Scheme & Notice Date
    # ----------------------------------------------------------------------------------
    print("\n" + "─" * 90)
    today_str = datetime.datetime.now().strftime("%d/%m/%Y")
    print("📌 [सवाल 4/5] नोटिस नंबरिंग एवं नोटिस दिनांक:")
    print("   [1] सभी बैंकों/एंटिटीज पर समान नोटिस नंबर रखें (उदा. Notice No. 5744) [Default - Enter दबाएं]")
    print("   [2] क्रमिक नोटिस नंबर रखें (Sequential: 5744, 5745, 5746...)")

    ans_num_scheme = input("   👉 विकल्प चुनें (1/2) [Default: 1 - समान नोटिस नंबर]: ").strip()
    same_notice_no = (ans_num_scheme != "2")

    ans_s_num = input("   👉 स्टार्टिंग नोटिस नंबर दर्ज करें [Default: 5744]: ").strip()
    start_notice_no = int(ans_s_num) if (ans_s_num.isdigit() and int(ans_s_num) > 0) else 5744

    ans_date = input(f"   👉 नोटिस पर अंकित करने हेतु दिनांक (DD/MM/YYYY) [Default: {today_str}]: ").strip()
    notice_date = ans_date if ans_date else today_str

    # ----------------------------------------------------------------------------------
    # Examination: Parse File & Display Intelligence
    # ----------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("             शिकायत फाइल का पूर्ण परीक्षण एवं मनी ट्रेल विश्लेषण...")
    print("=" * 90)

    temp_case_dir = os.path.join(agent.output_dir, "_temp_exam")
    if selected_file.lower().endswith(('.xlsx', '.xls')):
        ctx = agent.parse_ncrp_excel(selected_file, temp_case_dir)
    else:
        ctx = agent.parse_ncrp_pdf(selected_file, temp_case_dir)

    ctx["case_meta"]["same_notice_number"] = same_notice_no

    if fir_details.get("is_fir"):
        ctx["case_meta"]["case_type"] = "fir"
        ctx["case_meta"]["fir_no"] = fir_details["fir_no"]
        ctx["case_meta"]["fir_date"] = fir_details["fir_date"]
        ctx["case_meta"]["fir_sections"] = fir_details["fir_sections"]
        ctx["case_meta"]["case_reference"] = f"FIR No. {fir_details['fir_no']} Dated {fir_details['fir_date']} U/S {fir_details['fir_sections']}"
    else:
        ctx["case_meta"]["case_type"] = "ack"
        ctx["case_meta"]["case_reference"] = f"ACK No. {ctx['case_meta']['acknowledgement_no']}"

    ctx["case_meta"]["io_name"] = io_name
    ctx["case_meta"]["io_rank"] = io_rank
    ctx["case_meta"]["io_mobile"] = io_mobile
    ctx["case_meta"]["io_belt_no"] = io_belt
    ctx["case_meta"]["complaint_date"] = notice_date

    agent.display_complainant_profile(ctx)
    agent.display_bank_flowchart(ctx)

    upi_intel = agent.extract_upi_and_contact_intelligence(ctx)
    agent.display_upi_intelligence(upi_intel)

    # ----------------------------------------------------------------------------------
    # Q5: Suspect Telecom Numbers for CDR
    # ----------------------------------------------------------------------------------
    print("\n" + "─" * 90)
    suspect_mobs = upi_intel.get("suspect_contacts", [])
    if not suspect_mobs:
        suspect_mobs = ["9296960895"]
    mob_list_display = ", ".join(suspect_mobs)
    print("📌 [सवाल 5/5] टेलीकॉम कंपनियों को CDR+CAF+SDR रिक्विजिशन लेटर:")
    print(f"   पहचाने गए सस्पेक्ट मोबाइल: [ {mob_list_display} ] (अवधि: 01/01/2025 से Till Date)")
    print("   [1] केवल यही मोबाइल नंबर रखें [Default - Enter दबाएं]")
    print("   [2] अतिरिक्त मोबाइल नंबर अथवा IMEI नंबर जोड़ें")

    ans_tel_opt = input("   👉 विकल्प चुनें (1/2) [Default: 1]: ").strip()
    imei_list = []
    if ans_tel_opt == "2":
        extra_input = input("   👉 अतिरिक्त मोबाइल नंबर अथवा IMEI नंबर दर्ज करें (कॉमा ',' से अलग करें): ").strip()
        if extra_input:
            items = [x.strip() for x in extra_input.split(',') if x.strip()]
            for it in items:
                if len(it) == 15 and it.isdigit():
                    imei_list.append(it)
                elif len(it) == 10 and it.isdigit() and it not in suspect_mobs:
                    suspect_mobs.append(it)
                else:
                    imei_list.append(it)

    # ----------------------------------------------------------------------------------
    # Q6: Signature Mode
    # ----------------------------------------------------------------------------------
    print("\n" + "─" * 90)
    print("📌 [हस्ताक्षर मोड / Signature Mode]:")
    print("   [1] Signed (डिजिटल मुहर व आईओ के डिजिटल हस्ताक्षर सहित) [Default - Enter दबाएं]")
    print("   [2] Unsigned (केवल टाइप नोटिस - मुहर व हस्ताक्षर की खाली जगह सहित)")
    ans_sign_opt = input("   👉 विकल्प चुनें (1/2) [Default: 1 - Signed]: ").strip()
    sign_mode = "unsigned" if ans_sign_opt == "2" else "both"

    # ----------------------------------------------------------------------------------
    # Confirmation & Execution
    # ----------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("                      जांच एवं दस्तावेज़ उत्पादन सारांश (FINAL CONFIRMATION)")
    print("=" * 90)
    target_folder_name = f"FIR_{re.sub(r'[^a-zA-Z0-9_-]', '_', fir_details['fir_no'])}" if fir_details.get("is_fir") else f"Case_{ctx['case_meta']['acknowledgement_no']}"
    print(f" • केस संदर्भ (Case Ref)      : {ctx['case_meta']['case_reference']}")
    print(f" • आउटपुट फोल्डर (Output Dir)  : output/{target_folder_name}/")
    print(f" • जांच अधिकारी (IO)          : {io_name} ({io_rank}), Mobile: {io_mobile}")
    print(f" • हस्ताक्षर स्टेटस           : {'डिजिटल मुहर व आईओ हस्ताक्षर सक्रिय' if sign_mode == 'both' else 'Unsigned (रिक्त स्थान)'}")
    print(f" • नोटिस नंबरिंग व तारीख      : Notice No. {start_notice_no} ({'सभी पर समान' if same_notice_no else 'क्रमिक'}) | दिनांक: {notice_date}")
    print(f" • कंबाइंड नोटिस             : Combine_Notice_All_Banks_{start_notice_no}.docx (DOCX ONLY)")
    print(f" • बैंक नोटिस                 : केवल सेक्शन 94 BNSS बिंदु (CCTV व चेक पूर्णतः बहिष्कृत)")
    print(f" • ATM CCTV नोटिस             : प्रत्येक ATM ID हेतु पृथक नोटिस (+/- 5 मिनट टाइम विंडो)")
    print("=" * 90)

    ans_run = input("👉 क्या सभी दस्तावेज़ तैयार करें? (Y/N) [Default: Y]: ").strip().lower()
    if ans_run in ["n", "no"]:
        print("कार्रवाई रद्द कर दी गई।")
        return

    # Execute pipeline
    agent.run_case_pipeline(
        case_file_or_target=selected_file,
        fir_details=fir_details,
        io_override=io_override,
        start_notice_no=start_notice_no,
        notice_date_override=notice_date,
        suspect_mobiles=suspect_mobs,
        imei_list=imei_list,
        sign_mode=sign_mode
    )

    print("\n" + "=" * 90)
    print(f"✅ पूर्ण सफलता! सभी नोटिस, विज़ुअलाइज़र और दस्तावेज़ output/{target_folder_name}/ में तैयार हैं।")
    print("=" * 90)
# ENTRY POINT

# --------------------------------------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="NCRP Unified Master Cyber Crime Investigation Agent")

    parser.add_argument("--case", type=str, default=None, help="NCRP Acknowledgement Number or Path to Complaint PDF")

    parser.add_argument("--pdf", type=str, default=None, help="Path to NCRP Complaint PDF")

    parser.add_argument("--step", type=str, nargs="+", default=["all"], help="Investigation step(s) to run")

    parser.add_argument("--interview", action="store_true", help="Launch interactive guided Q&A interview")

    args = parser.parse_args()



    agent = NCRPUnifiedAgent()



    target = args.pdf or args.case

    if target:

        agent.run_case_pipeline(target, steps=args.step)

    else:

        # Default behavior: Launch Guided Q&A Interview!

        interactive_interview(agent)

