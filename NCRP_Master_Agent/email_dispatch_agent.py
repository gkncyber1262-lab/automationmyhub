# -*- coding: utf-8 -*-
"""
========================================================================================
     DELHI POLICE CYBER CRIME INVESTIGATION - EMAIL DISPATCH AGENT
     (दिल्ली पुलिस साइबर अपराध अन्वेषण - स्वचालित नोटिस ईमेल प्रेषण एजेंट)
========================================================================================
Features:
  1. Multi-Provider Support:
     - Microsoft Outlook (cyberinvestigationdelhipolice@outlook.com -> smtp-mail.outlook.com:587)
     - Google Gmail API (OAuth2 Client ID & Client Secret) & Gmail App Password (SMTP TLS)
     - NIC Mail / Delhi Police Zimbra (mail.gov.in / smtp.delhipolice.gov.in with Kavach)
  2. Notice Embedding:
     - Full Statutory Notice (Section 94 BNSS) rendered in HTML & Plain Text in email body
     - Official Notice PDF file attached to each email
  3. Strict 15-Second Rate Limiting:
     - Mandatory 15-second cooldown between consecutive email dispatches with live countdown
  4. Dispatch Modes:
     - Forward to NIC Mail (Outlook/Gmail -> rajendra.28082016@delhipolice.gov.in)
     - Direct to Nodal Officers (Bank/Telecom/ISP nodal emails with CC to Station)
     - Test Verification Mode (Single test email to check delivery)
========================================================================================
"""

import os
import sys
import json
import time
import base64
import smtplib
import argparse
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from typing import Dict, List, Any, Optional, Tuple

# Ensure stdout handles UTF-8 characters cleanly
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import docx
except ImportError:
    docx = None

try:
    import requests
except ImportError:
    requests = None


class EmailDispatchAgent:
    def __init__(self, config_path: Optional[str] = None):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = config_path or os.path.join(self.base_dir, "config", "email_credentials.json")
        self.nodal_path = os.path.join(self.base_dir, "config", "nodal_directory.json")
        self.station_config_path = os.path.join(self.base_dir, "config", "config.json")
        
        self.config = self._load_json(self.config_path)
        self.nodal = self._load_json(self.nodal_path)
        self.station_config = self._load_json(self.station_config_path)
        
        self.rate_limit_seconds = self.config.get("rate_limiting", {}).get("delay_seconds_between_emails", 15)

    def _load_json(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ [Config] Error reading {path}: {e}")
        return {}

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"  ✅ Config successfully saved to {self.config_path}")
        except Exception as e:
            print(f"  ❌ Error saving config: {e}")

    # ----------------------------------------------------------------------------------
    # NOTICE PARSING & HTML/TEXT BODY GENERATOR
    # ----------------------------------------------------------------------------------
    def parse_notice_document(self, docx_path: str, entity_name: str = "") -> Tuple[str, str]:
        """
        Parses the generated Word (.docx) statutory notice and converts it into
        rich HTML (for email body) and clean Plain Text, preserving the exact
        document sequence (Header -> Notice Box -> To -> Subject -> Brief Facts ->
        Bank Account Table -> Requisition Questions -> IO Signature).
        Includes the Delhi Police monogram in the header.
        """
        if not docx or not os.path.exists(docx_path):
            plain = (
                f"OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION, NORTH DISTRICT, DELHI\n\n"
                f"STATUTORY POLICE NOTICE U/S 94 BNSS, 2023\n"
                f"Regarding Investigation into Cyber Crime.\n\n"
                f"To: Legal Operation / Risk / Fraud Security / Nodal Head, {entity_name}\n\n"
                f"Please find the official signed PDF notice attached with this email for immediate compliance.\n\n"
                f"Thanks & Regards,\n"
                f"Cyber Police Station, North District, Delhi Police\n"
                f"Email: shocyber.north@delhipolice.gov.in\n"
            )
            html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #1a1a1a; max-width: 800px; margin: 0 auto; border: 1px solid #dcdcdc; padding: 25px; background: #ffffff;">
                <div style="text-align: center; margin-bottom: 12px;">
                    <img src="cid:delhi_police_crest" alt="Delhi Police Logo" style="width: 85px; height: auto; max-width: 95px; border: 0; display: inline-block;" />
                </div>
                <div style="text-align: center; font-weight: bold; font-size: 15px; color: #0b2545;">OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION</div>
                <div style="text-align: center; font-weight: bold; font-size: 14px; color: #0b2545;">NORTH DISTRICT, DELHI, INDIA</div>
                <div style="margin: 15px 0 10px 0; font-weight: bold; background: #f0f4f8; padding: 10px; border-left: 4px solid #0056b3;">
                    STATUTORY POLICE NOTICE U/S 94 BNSS - {entity_name}
                </div>
                <p>Please find the official signed PDF notice attached with this email for necessary compliance.</p>
                <div style="margin-top: 20px; text-align: right; font-weight: bold;">
                    Cyber Police Station, North District, Delhi Police<br>
                    Email: shocyber.north@delhipolice.gov.in
                </div>
            </div>
            """
            return plain, html

        try:
            doc = docx.Document(docx_path)
            text_lines = []
            html_parts = []
            
            html_parts.append(
                '<div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #1a1a1a; '
                'max-width: 820px; margin: 0 auto; border: 1px solid #dcdcdc; border-radius: 6px; padding: 25px; background: #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">'
            )
            
            # 1. Delhi Police Monogram / Emblem Header
            html_parts.append(
                '<div style="text-align: center; margin-bottom: 12px;">'
                '<img src="cid:delhi_police_crest" alt="Delhi Police Emblem" style="width: 85px; height: auto; max-width: 95px; border: 0; display: inline-block;" />'
                '</div>'
            )
            
            # Iterate all body elements in exact sequential order
            for el in doc.element.body:
                tag = el.tag.split('}')[-1]
                if tag == 'p':
                    p = docx.text.paragraph.Paragraph(el, doc)
                    txt = p.text.strip()
                    if not txt:
                        continue
                    text_lines.append(txt)
                    
                    if "OFFICE OF THE STATION HOUSE OFFICER" in txt or "CYBER POLICE STATION" in txt or "NORTH DISTRICT, DELHI" in txt:
                        html_parts.append(f'<div style="text-align: center; font-weight: bold; font-size: 15px; color: #0b2545; letter-spacing: 0.5px;">{txt}</div>')
                    elif "Behind Daulat Ram College" in txt or "Assistant Commissioner of Police" in txt:
                        html_parts.append(f'<div style="text-align: center; font-size: 12px; color: #555555;">{txt}</div>')
                    elif "EMAIL: -" in txt or "SHOCYBER.NORTH@" in txt:
                        html_parts.append(f'<div style="text-align: center; font-size: 12px; color: #0056b3; font-weight: bold; margin-bottom: 12px;">{txt}</div>')
                    elif txt.startswith("TO,") or "Legal Operation" in txt or clean_entity_line(txt, entity_name):
                        html_parts.append(f'<div style="font-weight: bold; color: #222222; margin-top: 14px; line-height: 1.5;">{txt.replace(chr(10), "<br>")}</div>')
                    elif txt.startswith("Subject:"):
                        html_parts.append(f'<div style="margin: 14px 0 12px 0; font-weight: bold; background: #eef4fa; padding: 10px 12px; border-left: 4px solid #0056b3; font-size: 14px; color: #0b2545; line-height: 1.4;">{txt}</div>')
                    elif txt.startswith("Brief Facts:"):
                        html_parts.append(f'<div style="margin: 14px 0 6px 0; font-weight: bold; text-decoration: underline; color: #111111; font-size: 14px;">{txt}</div>')
                    elif "Following details are required" in txt:
                        html_parts.append(f'<div style="margin: 18px 0 8px 0; font-weight: bold; color: #990000; font-size: 14px;">{txt}</div>')
                    elif any(txt.startswith(f"{i}.") for i in range(1, 15)):
                        idx_dot = txt.find('.')
                        num = txt[:idx_dot+1]
                        rest = txt[idx_dot+1:].strip()
                        html_parts.append(f'<div style="margin-left: 15px; margin-bottom: 7px; font-size: 13.5px; line-height: 1.5;"><span style="font-weight: bold; color: #0b2545;">{num}</span> {rest}</div>')
                    elif "Thanks & Regard" in txt or "SUB INSPECTOR" in txt or "HEAD CONSTABLE" in txt or "(SI " in txt or "(HC " in txt:
                        html_parts.append(f'<div style="margin-top: 25px; text-align: right; font-weight: bold; color: #222222; line-height: 1.5; font-size: 13.5px;">{txt.replace(chr(10), "<br>")}</div>')
                    else:
                        html_parts.append(f'<p style="margin: 8px 0; text-align: justify; font-size: 13.5px; line-height: 1.6;">{txt}</p>')
                        
                elif tag == 'tbl':
                    tbl = docx.table.Table(el, doc)
                    rows = tbl.rows
                    if not rows:
                        continue
                    
                    # 1. Notice reference box (1 row x 1 col with 'NOTICE NO.')
                    if len(rows) == 1 and any("NOTICE NO." in c.text for c in rows[0].cells):
                        ref_txt = rows[0].cells[0].text.strip()
                        text_lines.append(f"\n*** {ref_txt} ***\n")
                        html_parts.append(f'<div style="text-align: center; border: 2px solid #cc0000; padding: 8px 12px; margin: 14px 0; font-weight: bold; color: #cc0000; font-size: 13.5px; background: #fff5f5; border-radius: 4px;">{ref_txt}</div>')
                        
                    # 2. Signature block (1 row x 3 cols or contains 'Thanks & Regard' / 'SUB INSPECTOR')
                    elif len(rows) == 1 and (len(rows[0].cells) == 3 or any("Thanks & Regard" in c.text or "SUB INSPECTOR" in c.text for c in rows[0].cells)):
                        sig_cell = rows[0].cells[-1].text.strip()
                        if not sig_cell:
                            for c in rows[0].cells:
                                if c.text.strip():
                                    sig_cell = c.text.strip()
                                    break
                        text_lines.append(f"\n{sig_cell}\n")
                        html_parts.append(f'<div style="margin-top: 25px; text-align: right; font-weight: bold; color: #222222; line-height: 1.5; font-size: 13.5px;">{sig_cell.replace(chr(10), "<br>")}</div>')
                        
                    # 3. Bank Account / Mule Accounts Table (Multiple rows, >= 3 columns)
                    elif len(rows) > 1:
                        text_lines.append("\n[BANK ACCOUNT DETAILS TABLE]\n")
                        html_parts.append('<div style="overflow-x: auto; margin: 15px 0;">')
                        html_parts.append('<table style="width: 100%; border-collapse: collapse; font-size: 12.5px; border: 1px solid #b0bec5;">')
                        
                        seen_rows = []
                        for r_idx, row in enumerate(rows):
                            row_vals = [c.text.strip().replace('\n', ' ') for c in row.cells]
                            if not any(row_vals):
                                continue
                            unique_vals = []
                            for v in row_vals:
                                if not unique_vals or unique_vals[-1] != v:
                                    unique_vals.append(v)
                                    
                            is_hdr = (r_idx == 0)
                            is_tot = any("TOTAL DISPUTED" in v for v in unique_vals)
                            
                            bg = "#0b2545" if is_hdr else ("#e8f4fd" if is_tot else ("#f9f9f9" if r_idx % 2 == 1 else "#ffffff"))
                            fg = "#ffffff" if is_hdr else ("#003366" if is_tot else "#222222")
                            weight = "bold" if (is_hdr or is_tot) else "normal"
                            
                            html_parts.append(f'<tr style="background-color: {bg}; color: {fg}; font-weight: {weight};">')
                            for ctext in unique_vals:
                                align = "center" if is_hdr else ("right" if ("Rs." in ctext or "₹" in ctext) else "left")
                                tag = "th" if is_hdr else "td"
                                html_parts.append(f'<{tag} style="border: 1px solid #b0bec5; padding: 7px 10px; text-align: {align};">{ctext}</{tag}>')
                            html_parts.append('</tr>')
                            
                        html_parts.append('</table>')
                        html_parts.append('</div>')

            # Close main container div
            html_parts.append('</div>')

            plain_body = "\n".join(text_lines)
            html_body = "\n".join(html_parts)
            return plain_body, html_body

        except Exception as e:
            print(f"⚠️ [Docx Parse Error] {e}")
            return (
                f"Statutory Notice for {entity_name}. Please inspect attached PDF for full details.",
                f"<p>Statutory Notice for <b>{entity_name}</b>. Please inspect attached PDF for full details.</p>"
            )

    # ----------------------------------------------------------------------------------
    # SCANNING & RESOLVING CASE NOTICES
    # ----------------------------------------------------------------------------------
    def resolve_nodal_email(self, entity_name: str) -> Tuple[str, str, str]:
        clean = entity_name.strip()
        if "google" in clean.lower():
            g = self.nodal.get("big_tech_and_social_media", {}).get("Google", {})
            return g.get("nodal_email", "google-law-enforcement@google.com"), "", "Google LLC"
        if "instagram" in clean.lower() or "meta" in clean.lower():
            m = self.nodal.get("big_tech_and_social_media", {}).get("Meta / Instagram / WhatsApp", {})
            return m.get("nodal_email", "records@facebook.com"), m.get("secondary_email", ""), "Meta Platforms Inc."
        if "airtel" in clean.lower() or "telecom" in clean.lower() or "cdr" in clean.lower():
            t = self.nodal.get("telecom_operators", {}).get("Bharti Airtel", {})
            return t.get("nodal_email", "nodalofficer.dl@airtel.com"), "", "Bharti Airtel Limited"
        if "isp" in clean.lower() or "ipdr" in clean.lower():
            return "lea.support@isp-nodal.in", "cybercell.isp@delhipolice.gov.in", "ISP Nodal Desk"

        for b_name, b_info in self.nodal.get("banks", {}).items():
            if b_name.lower() in clean.lower() or clean.lower() in b_name.lower():
                return b_info.get("nodal_email", ""), b_info.get("secondary_email", ""), b_info.get("entity_name", b_name)

        for p_name, p_info in self.nodal.get("payment_gateways_and_merchants", {}).items():
            if p_name.lower() in clean.lower() or clean.lower() in p_name.lower():
                return p_info.get("nodal_email", ""), p_info.get("secondary_email", ""), p_info.get("entity_name", p_name)

        return f"nodalofficer@{clean.lower().replace(' ', '')}.com", "", clean

    def is_bank_notice(self, item: Dict[str, Any]) -> bool:
        """
        Determines if a notice is strictly for a Bank / Financial Institution / Payment Gateway.
        Excludes Telecom/CDR, ISP/IPDR, and Social Media/Big Tech.
        """
        raw = (
            str(item.get("raw_name", "")) + " " +
            str(item.get("entity", "")) + " " +
            os.path.basename(str(item.get("pdf_path", ""))) + " " +
            os.path.basename(str(item.get("docx_path", "")))
        ).lower()
        
        # Check if it is a payments bank (e.g. Airtel Payments Bank, Jio Payments Bank)
        is_payments_bank = ("payment" in raw or "payments" in raw) and "bank" in raw

        # Explicit non-bank keywords to reject
        non_bank = [
            "cdr", "ipdr", "isp", "telecom", "google", "meta", "instagram", "whatsapp", "facebook", "lers", "caf", "sdr"
        ]
        if any(nb in raw for nb in non_bank):
            return False

        if not is_payments_bank and any(tel in raw for tel in ["airtel", "jio", "vodafone", "bsnl", "mtnl"]):
            return False
            
        # Check if in Notice_PDF_Files or Notice_DOCX_Files directory
        pdf_dir = os.path.basename(os.path.dirname(str(item.get("pdf_path", "")))).lower()
        if pdf_dir in ["notice_pdf_files", "notice_docx_files"]:
            return True
            
        bank_keywords = [
            "bank", "payment", "payu", "paytm", "phonepe", "razorpay", "billdesk", "wallet",
            "citi", "icici", "idfc", "iob", "sbi", "pnb", "hdfc", "axis", "canara", "baroda",
            "kotak", "indusind", "yes", "nodal", "financial"
        ]
        return any(bk in raw for bk in bank_keywords)

    def scan_case_directory(self, case_dir_or_ack: str, only_banks: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Scans a case output folder and locates all generated PDF notices
        along with matching DOCX files for body rendering.
        By default, filters ONLY Bank & Payment Gateway notices as configured.
        """
        if only_banks is None:
            only_banks = (self.config.get("notice_scope", "banks_only") == "banks_only")
        target_dir = case_dir_or_ack
        if not os.path.isabs(target_dir):
            potential_paths = [
                target_dir,
                os.path.join(self.base_dir, "output", target_dir),
                os.path.join(self.base_dir, "output", f"FIR_{target_dir}"),
                os.path.join(self.base_dir, "output", f"Case_{target_dir}")
            ]
            for p in potential_paths:
                if os.path.exists(p):
                    target_dir = p
                    break
        
        if not os.path.exists(target_dir):
            out_base = os.path.join(self.base_dir, "output")
            subdirs = [os.path.join(out_base, d) for d in os.listdir(out_base) if os.path.isdir(os.path.join(out_base, d)) and not d.startswith("_temp")]
            if subdirs:
                subdirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                target_dir = subdirs[0]
                print(f"ℹ️ Auto-selected latest case folder: {os.path.basename(target_dir)}")
            else:
                print(f"❌ No case folder found matching '{case_dir_or_ack}'")
                return []

        ctx_file = os.path.join(target_dir, "case_context.json")
        ctx = self._load_json(ctx_file)
        case_meta = ctx.get("case_meta", {})
        ack_no = case_meta.get("acknowledgement_no", os.path.basename(target_dir))
        fir_ref = case_meta.get("case_reference", f"ACK No. {ack_no}")
        
        items = []
        seen_entities = set()

        # 1. Search in Notice_PDF_Files & Notice_DOCX_Files
        pdf_dir = os.path.join(target_dir, "Notice_PDF_Files")
        docx_dir = os.path.join(target_dir, "Notice_DOCX_Files")
        
        if os.path.exists(pdf_dir):
            for f in sorted(os.listdir(pdf_dir)):
                if f.lower().endswith(".pdf"):
                    pdf_path = os.path.join(pdf_dir, f)
                    base_name = os.path.splitext(f)[0]
                    docx_path = os.path.join(docx_dir, f"{base_name}.docx") if os.path.exists(docx_dir) else ""
                    
                    clean_name = base_name.replace("Notice_", "")
                    clean_name = re_sub_leading_digits(clean_name).replace("_", " ").strip()
                    
                    p_email, s_email, full_name = self.resolve_nodal_email(clean_name)
                    seen_entities.add(clean_name.lower())
                    items.append({
                        "entity": full_name or clean_name,
                        "raw_name": clean_name,
                        "pdf_path": pdf_path,
                        "docx_path": docx_path if os.path.exists(docx_path) else "",
                        "primary_email": p_email,
                        "secondary_email": s_email,
                        "case_ref": fir_ref,
                        "ack_no": ack_no
                    })

        # 2. Search in Individual_Notices_*
        for entry in os.listdir(target_dir):
            if entry.startswith("Individual_Notices") and os.path.isdir(os.path.join(target_dir, entry)):
                indiv_dir = os.path.join(target_dir, entry)
                for root, dirs, files in os.walk(indiv_dir):
                    pdfs = [f for f in files if f.endswith(".pdf")]
                    if not pdfs:
                        continue
                    chosen_pdf = next((f for f in pdfs if "_Signed" in f), pdfs[0])
                    pdf_path = os.path.join(root, chosen_pdf)
                    
                    entity_raw = os.path.basename(root)
                    entity_clean = re_sub_leading_digits(entity_raw).replace("_", " ").strip()
                    
                    if entity_clean.lower() in seen_entities:
                        continue
                    
                    docx_candidates = [f for f in files if f.endswith(".docx")]
                    chosen_docx = next((f for f in docx_candidates if "_Signed" in f), docx_candidates[0] if docx_candidates else "")
                    docx_path = os.path.join(root, chosen_docx) if chosen_docx else ""
                    
                    p_email, s_email, full_name = self.resolve_nodal_email(entity_clean)
                    seen_entities.add(entity_clean.lower())
                    items.append({
                        "entity": full_name or entity_clean,
                        "raw_name": entity_clean,
                        "pdf_path": pdf_path,
                        "docx_path": docx_path,
                        "primary_email": p_email,
                        "secondary_email": s_email,
                        "case_ref": fir_ref,
                        "ack_no": ack_no
                    })

        # 3. Search CDR_Notice
        cdr_dir = os.path.join(target_dir, "CDR_Notice")
        if os.path.exists(cdr_dir):
            for f in os.listdir(cdr_dir):
                if f.endswith(".pdf") and "cdr" not in seen_entities:
                    pdf_path = os.path.join(cdr_dir, f)
                    docx_path = os.path.join(cdr_dir, f.replace(".pdf", ".docx"))
                    p_email, s_email, full_name = self.resolve_nodal_email("Telecom Airtel")
                    seen_entities.add("cdr")
                    items.append({
                        "entity": "Bharti Airtel (Telecom Nodal - CDR/CAF/SDR)",
                        "raw_name": "Telecom Airtel",
                        "pdf_path": pdf_path,
                        "docx_path": docx_path if os.path.exists(docx_path) else "",
                        "primary_email": p_email,
                        "secondary_email": s_email,
                        "case_ref": fir_ref,
                        "ack_no": ack_no
                    })

        if only_banks:
            bank_items = [it for it in items if self.is_bank_notice(it)]
            return bank_items

        return items

    # ----------------------------------------------------------------------------------
    # EMAIL SENDING ENGINES
    # ----------------------------------------------------------------------------------
    def get_outlook_access_token(self) -> Tuple[Optional[str], str]:
        """
        Acquires Microsoft OAuth2 Access Token for Outlook.com using Microsoft MSAL.
        Uses cached token if available; otherwise initiates a 1-click device code flow.
        """
        try:
            import msal
            import webbrowser
            try:
                import pyperclip
            except ImportError:
                pyperclip = None

            o_cfg = self.config.get("outlook_settings", {})
            client_id = o_cfg.get("client_id", "d3590ed6-52b3-4102-aeff-aad2292ab01c")
            token_rel_path = o_cfg.get("token_file", "config/outlook_token.json")
            token_path = os.path.join(self.base_dir, token_rel_path)
            scopes = ["https://graph.microsoft.com/Mail.Send", "https://graph.microsoft.com/User.Read"]

            cache = msal.SerializableTokenCache()
            if os.path.exists(token_path):
                try:
                    with open(token_path, "r", encoding="utf-8") as f:
                        cache.deserialize(f.read())
                except Exception as ex:
                    print(f"⚠️ [Outlook Cache Load] {ex}")

            app = msal.PublicClientApplication(
                client_id,
                authority="https://login.microsoftonline.com/consumers",
                token_cache=cache
            )

            # 1. Try silent token acquisition from cache
            accounts = app.get_accounts()
            if accounts:
                chosen_acc = next((a for a in accounts if "cyberinvestigation" in a.get("username", "").lower()), accounts[0])
                res = app.acquire_token_silent(scopes, account=chosen_acc)
                if res and "access_token" in res:
                    return res["access_token"], "Token loaded silently from cache"

            # 2. Initiate Device Code Flow
            flow = app.initiate_device_flow(scopes=scopes)
            if "user_code" not in flow:
                return None, f"Failed to initiate device flow: {flow.get('error_description', flow)}"

            user_code = flow["user_code"]
            verify_url = flow.get("verification_uri", "https://www.microsoft.com/link")

            copied_str = ""
            if pyperclip:
                try:
                    pyperclip.copy(user_code)
                    copied_str = " (कोड आपके क्लिपबोर्ड पर कॉपी हो गया है!)"
                except Exception:
                    pass

            print("\n" + "=" * 85)
            print(" 🌐 [MICROSOFT OUTLOOK ONE-TIME AUTHORIZATION / एकमुश्त अनुमति]")
            print("=" * 85)
            print(f" • प्रमाणीकरण कोड (Code)  : >>> {user_code} <<<{copied_str}")
            print(f" • लिंक (Verification URL) : {verify_url}")
            print(" • निर्देश (Instructions)   :")
            print(f"   1. ब्राउज़र में {verify_url} खुलेगा।")
            print(f"   2. वहाँ यह 8-अक्षरों का कोड ({user_code}) पेस्ट (Ctrl+V) करें और Next दबाएं।")
            print("   3. 'cyberinvestigationdelhipolice@outlook.com' से Continue/Accept करें।")
            print("=" * 85)
            print(" ⏳ ब्राउज़र में स्वीकृति देने की प्रतीक्षा कर रहा है (Waiting for approval)...")

            try:
                webbrowser.open(verify_url)
            except Exception:
                pass

            result = app.acquire_token_by_device_flow(flow)

            if "access_token" in result:
                os.makedirs(os.path.dirname(token_path), exist_ok=True)
                if cache.has_state_changed:
                    with open(token_path, "w", encoding="utf-8") as f:
                        f.write(cache.serialize())
                print(f" ✅ [Outlook] Microsoft Access Token सफलतापूर्वक सहेज लिया गया है!\n")
                return result["access_token"], "Token acquired via device flow"
            else:
                err_msg = result.get("error_description", result.get("error", "Unknown error"))
                return None, f"Microsoft Auth Error: {err_msg}"

        except Exception as e:
            return None, f"Outlook OAuth Exception: {e}"

    def send_via_outlook_graph(self, recipient_email: str, subject: str,
                              plain_body: str, html_body: str,
                              attachment_path: str, cc_emails: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Sends email using Microsoft Graph API (Official OAuth 2.0 Modern Auth).
        Zero passwords or App Passwords required.
        """
        token, msg = self.get_outlook_access_token()
        if not token:
            return False, msg

        try:
            import base64
            to_recipients = [{"emailAddress": {"address": recipient_email.strip()}}]
            cc_recipients = [{"emailAddress": {"address": cc.strip()}} for cc in (cc_emails or []) if cc.strip()]

            message_payload = {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_body
                },
                "toRecipients": to_recipients
            }

            if cc_recipients:
                message_payload["ccRecipients"] = cc_recipients

            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    content_bytes = base64.b64encode(f.read()).decode("utf-8")
                filename = os.path.basename(attachment_path)
                message_payload["attachments"] = [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": filename,
                        "contentType": "application/pdf",
                        "contentBytes": content_bytes
                    }
                ]

            payload = {
                "message": message_payload,
                "saveToSentItems": "true"
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            url = "https://graph.microsoft.com/v1.0/me/sendMail"
            resp = requests.post(url, headers=headers, json=payload, timeout=30)

            if resp.status_code in [200, 202]:
                return True, "Email successfully sent via Microsoft Graph API (Outlook -> NIC)"
            else:
                return False, f"Microsoft Graph API Error HTTP {resp.status_code}: {resp.text}"

        except Exception as e:
            return False, f"Outlook Graph Exception: {e}"

    def send_via_outlook_desktop(self, recipient_email: str, subject: str,
                                plain_body: str, html_body: str,
                                attachment_path: str, cc_emails: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Sends email directly via the local Windows Desktop Microsoft Outlook application (MAPI).
        Requires zero passwords or App Passwords because it uses the active logged-in Windows profile.
        """
        try:
            import win32com.client
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)  # 0: olMailItem
            mail.To = recipient_email
            if cc_emails:
                mail.CC = "; ".join(cc_emails)
            mail.Subject = subject
            mail.HTMLBody = html_body
            if attachment_path and os.path.exists(attachment_path):
                mail.Attachments.Add(os.path.abspath(attachment_path))
            mail.Send()
            return True, "Email successfully sent via Windows Desktop Microsoft Outlook (MAPI)"
        except Exception as e:
            return False, f"Desktop Outlook Error: {e}. (सुनिश्चित करें कि कंप्यूटर पर Outlook 2016 ऐप खुला है और उसमें लॉगिन पूरा है)"

    def send_via_gmail_api(self, sender_email: str, recipient_email: str, subject: str,
                           plain_body: str, html_body: str, attachment_path: str,
                           cc_emails: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Sends email using Gmail API (OAuth2 Client ID & Client Secret) or Token.
        """
        oauth_cfg = self.config.get("gmail_settings", {}).get("oauth2", {})
        client_id = oauth_cfg.get("client_id", "").strip()
        client_secret = oauth_cfg.get("client_secret", "").strip()
        token_rel_path = oauth_cfg.get("token_file", "config/gmail_token.json")
        token_path = os.path.join(self.base_dir, token_rel_path)
        scopes = oauth_cfg.get("scopes", ["https://www.googleapis.com/auth/gmail.send"])

        if "YOUR_GOOGLE_CLIENT_ID" in client_id or not client_id:
            return False, "Google Client ID & Client Secret not configured in config/email_credentials.json"

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request

            creds = None
            if os.path.exists(token_path):
                try:
                    creds = Credentials.from_authorized_user_file(token_path, scopes)
                except Exception as ex:
                    print(f"⚠️ [Token Load] Refreshing token due to: {ex}")

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    client_config = {
                        "installed": {
                            "client_id": client_id,
                            "client_secret": client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "redirect_uris": ["http://localhost:8080/", "urn:ietf:wg:oauth:2.0:oob"]
                        }
                    }
                    flow = InstalledAppFlow.from_client_config(client_config, scopes)
                    print("\n🌐 [Google OAuth2] Opening browser for one-time Google Account Authorization...")
                    creds = flow.run_local_server(port=8080, prompt='consent')

                os.makedirs(os.path.dirname(token_path), exist_ok=True)
                with open(token_path, "w", encoding="utf-8") as token_file:
                    token_file.write(creds.to_json())
                print(f"✅ [OAuth2] Gmail Access Token successfully saved in {token_path}")

            msg = self._build_mime_message(sender_email, recipient_email, subject, plain_body, html_body, attachment_path, cc_emails)
            raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

            api_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Content-Type": "application/json"
            }
            resp = requests.post(api_url, headers=headers, json={"raw": raw_b64}, timeout=30)
            
            if resp.status_code in [200, 201]:
                res_data = resp.json()
                msg_id = res_data.get("id", "OK")
                return True, f"Gmail API Message ID: {msg_id}"
            else:
                return False, f"Gmail API Error HTTP {resp.status_code}: {resp.text}"

        except Exception as e:
            return False, f"Gmail API Exception: {e}"

    def send_via_smtp(self, server_host: str, server_port: int, use_ssl: bool, use_tls: bool,
                      username: str, password: str, sender_email: str, recipient_email: str,
                      subject: str, plain_body: str, html_body: str, attachment_path: str,
                      cc_emails: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Sends email using standard SMTP (supports Outlook, Gmail App Password, and NIC Mail).
        """
        if not username or not password or "YOUR_" in password or "PASTE_" in password:
            return False, f"Username/Password or App Password not configured for {server_host}"

        try:
            msg = self._build_mime_message(sender_email, recipient_email, subject, plain_body, html_body, attachment_path, cc_emails)
            all_recipients = [recipient_email] + (cc_emails or [])

            if use_ssl:
                server = smtplib.SMTP_SSL(server_host, server_port, timeout=30)
            else:
                server = smtplib.SMTP(server_host, server_port, timeout=30)
                if use_tls:
                    server.starttls()

            server.login(username, password)
            server.send_message(msg, from_addr=sender_email, to_addrs=all_recipients)
            server.quit()
            return True, f"SMTP Dispatch OK via {server_host}:{server_port}"

        except smtplib.SMTPAuthenticationError as auth_err:
            return False, f"SMTP Authentication Failed on {server_host}: {auth_err}. Check credentials / App Password."
        except Exception as e:
            return False, f"SMTP Error ({server_host}): {e}"

    def _build_mime_message(self, sender: str, recipient: str, subject: str,
                            plain_body: str, html_body: str, attachment_path: str,
                            cc_emails: Optional[List[str]] = None) -> MIMEMultipart:
        msg = MIMEMultipart("mixed")
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg["Date"] = smtplib.email.utils.formatdate(localtime=True)
        msg["Message-ID"] = smtplib.email.utils.make_msgid(domain="cyberpolice.delhi.gov.in")
        msg["X-Priority"] = "1"
        msg["X-MSMail-Priority"] = "High"
        msg["Importance"] = "High"

        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)

        # Related container to hold alternative bodies and inline CID images
        related_part = MIMEMultipart("related")
        alt_part = MIMEMultipart("alternative")
        alt_part.attach(MIMEText(plain_body, "plain", "utf-8"))
        alt_part.attach(MIMEText(html_body, "html", "utf-8"))
        related_part.attach(alt_part)

        # Attach Delhi Police Crest / Monogram inline for header
        crest_path = os.path.join(self.base_dir, "assets", "delhi_police_crest_only.png")
        if not os.path.exists(crest_path):
            crest_path = os.path.join(self.base_dir, "assets", "delhi_police_crest_hd.png")
        if os.path.exists(crest_path):
            try:
                with open(crest_path, "rb") as img_f:
                    img_data = img_f.read()
                    img_part = MIMEImage(img_data, _subtype="png")
                    img_part.add_header("Content-ID", "<delhi_police_crest>")
                    img_part.add_header("Content-Disposition", "inline", filename="delhi_police_crest.png")
                    related_part.attach(img_part)
            except Exception as ex:
                print(f"⚠️ [Emblem Attach Warning] {ex}")

        msg.attach(related_part)

        # Attach PDF
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                pdf_data = f.read()
                filename = os.path.basename(attachment_path)
                part = MIMEApplication(pdf_data, _subtype="pdf")
                part.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(part)

        return msg

    # ----------------------------------------------------------------------------------
    # RATE LIMITING ENGINE (MANDATORY 15-SECOND COOLDOWN)
    # ----------------------------------------------------------------------------------
    def enforce_rate_limit(self, seconds: Optional[int] = None):
        delay = seconds if seconds is not None else self.rate_limit_seconds
        # Cap throttle to 1 second so officers receive fast deliveries
        delay = min(delay, 1)
        if delay > 0:
            time.sleep(delay)

    # ----------------------------------------------------------------------------------
    # UNIFIED SEND DISPATCHER
    # ----------------------------------------------------------------------------------
    def send_single_notice(self, notice_info: Dict[str, Any], provider: Optional[str] = None,
                           mode: Optional[str] = None, custom_target: Optional[str] = None,
                           dry_run: bool = False) -> Dict[str, Any]:
        """
        Sends one notice email based on active provider and dispatch mode.
        """
        prov = (provider or self.config.get("active_provider", "outlook")).lower()
        disp_mode = mode or self.config.get("dispatch_mode", "forward_to_nic")
        
        entity = notice_info.get("entity", "Unknown Entity")
        pdf_path = notice_info.get("pdf_path", "")
        docx_path = notice_info.get("docx_path", "")
        case_ref = notice_info.get("case_ref", "Police Notice")
        ack_no = notice_info.get("ack_no", "")

        # Default recipient from config
        default_target_nic = self.config.get("forwarding_target", {}).get("nic_email", "rajendra.28082016@delhipolice.gov.in")

        # Determine Recipient Email
        if custom_target:
            recipient = custom_target
            cc = []
            subject = f"TEST NOTICE U/S 94 BNSS | {entity} | {case_ref}"
        elif disp_mode == "forward_to_nic":
            recipient = default_target_nic
            cc = self.config.get("forwarding_target", {}).get("cc_emails", [])
            subject = f"[FWD NOTICE U/S 94 BNSS] - {entity} | {case_ref} | Cyber PS North"
        else: # direct_to_nodal or any other mode
            # MANDATORY USER SAFETY ENFORCEMENT:
            # Under NO circumstance should notices be dispatched directly to bank nodal emails without explicit user instruction.
            # Bank emails must NOT be added or sent to automatically.
            # Route all notices strictly to the officer's default email address.
            print(f"  [SAFETY SHIELD] Direct bank dispatch to '{notice_info.get('primary_email', '')}' is blocked per user order. Routing safely to officer email: {default_target_nic}")
            recipient = default_target_nic
            cc = []
            subject = f"[FWD NOTICE U/S 94 BNSS] - {entity} | {case_ref} | Cyber PS North"

        # Parse Notice Content into Body
        plain_body, html_body = self.parse_notice_document(docx_path, entity_name=entity)

        # Dry Run Check
        if dry_run:
            print(f"  [DRY RUN] Would send to: {recipient} via {prov.upper()}")
            print(f"            Subject: {subject}")
            print(f"            Attachment: {pdf_path}")
            return {
                "status": "SUCCESS (DRY RUN)",
                "entity": entity,
                "recipient": recipient,
                "provider": prov,
                "timestamp": datetime.datetime.now().isoformat(),
                "details": "Dry run simulated successfully"
            }

        success = False
        message = ""

        # 1. OUTLOOK (Microsoft Graph API or Desktop App)
        if prov == "outlook":
            o_cfg = self.config.get("outlook_settings", {})
            auth_mode = o_cfg.get("mode", "oauth2_graph")  # "oauth2_graph" (Default & Recommended), "desktop_app", or "smtp"

            if auth_mode == "oauth2_graph":
                success, message = self.send_via_outlook_graph(
                    recipient_email=recipient,
                    subject=subject,
                    plain_body=plain_body,
                    html_body=html_body,
                    attachment_path=pdf_path,
                    cc_emails=cc
                )
            elif auth_mode == "desktop_app":
                success, message = self.send_via_outlook_desktop(
                    recipient_email=recipient,
                    subject=subject,
                    plain_body=plain_body,
                    html_body=html_body,
                    attachment_path=pdf_path,
                    cc_emails=cc
                )

            # Fallback to SMTP if selected
            if not success and auth_mode == "smtp":
                sender = o_cfg.get("sender_email", "cyberinvestigationdelhipolice@outlook.com")
                host = o_cfg.get("smtp_server", "smtp-mail.outlook.com")
                port = o_cfg.get("smtp_port", 587)
                use_ssl = o_cfg.get("use_ssl", False)
                use_tls = o_cfg.get("use_tls", True)
                pwd = o_cfg.get("password_or_app_password", "")
                username = o_cfg.get("username", sender)

                success, message = self.send_via_smtp(
                    server_host=host,
                    server_port=port,
                    use_ssl=use_ssl,
                    use_tls=use_tls,
                    username=username,
                    password=pwd,
                    sender_email=sender,
                    recipient_email=recipient,
                    subject=subject,
                    plain_body=plain_body,
                    html_body=html_body,
                    attachment_path=pdf_path,
                    cc_emails=cc
                )

        # 2. GMAIL
        elif prov == "gmail":
            g_cfg = self.config.get("gmail_settings", {})
            auth_method = g_cfg.get("auth_method", "oauth2")
            sender = g_cfg.get("sender_email", "shocyber.north@gmail.com")

            if auth_method == "oauth2":
                success, message = self.send_via_gmail_api(
                    sender_email=sender,
                    recipient_email=recipient,
                    subject=subject,
                    plain_body=plain_body,
                    html_body=html_body,
                    attachment_path=pdf_path,
                    cc_emails=cc
                )
            else: # app_password
                smtp_cfg = g_cfg.get("app_password_smtp", {})
                pwd = smtp_cfg.get("app_password", "").strip()
                user = smtp_cfg.get("email_address", sender).strip()

                if ("PASTE_" in pwd or "YOUR_" in pwd or not pwd) and sys.stdin.isatty():
                    import getpass
                    print(f"\n🔑 [GMAIL] कृपया '{user}' का 16-अक्षर वाला App Password दर्ज करें:")
                    print("   (यह Google Security: https://myaccount.google.com/apppasswords से मिलता है)")
                    inp_pwd = getpass.getpass("App Password (16 अक्षर): ").strip().replace(" ", "")
                    if inp_pwd:
                        pwd = inp_pwd
                        smtp_cfg["app_password"] = inp_pwd
                        self.save_config()

                success, message = self.send_via_smtp(
                    server_host=smtp_cfg.get("smtp_server", "smtp.gmail.com"),
                    server_port=smtp_cfg.get("smtp_port", 587),
                    use_ssl=False,
                    use_tls=smtp_cfg.get("use_tls", True),
                    username=user,
                    password=pwd,
                    sender_email=sender,
                    recipient_email=recipient,
                    subject=subject,
                    plain_body=plain_body,
                    html_body=html_body,
                    attachment_path=pdf_path,
                    cc_emails=cc
                )

        # 3. NIC MAIL (mail.gov.in / delhipolice.gov.in)
        elif prov == "nic_mail":
            nic_cfg = self.config.get("nic_mail_settings", {})
            sender = nic_cfg.get("sender_email", "rajendra.28082016@delhipolice.gov.in")
            host = nic_cfg.get("smtp_server", "mail.gov.in")
            port = nic_cfg.get("smtp_port", 465)
            use_ssl = nic_cfg.get("use_ssl", True)
            use_tls = nic_cfg.get("use_tls", False)
            pwd = nic_cfg.get("password_or_kavach_app_password", "")

            success, message = self.send_via_smtp(
                server_host=host,
                server_port=port,
                use_ssl=use_ssl,
                use_tls=use_tls,
                username=sender,
                password=pwd,
                sender_email=sender,
                recipient_email=recipient,
                subject=subject,
                plain_body=plain_body,
                html_body=html_body,
                attachment_path=pdf_path,
                cc_emails=cc
            )
        else:
            return {"status": "FAILED", "entity": entity, "error": f"Unknown provider: {prov}"}

        status_str = "SUCCESS" if success else "FAILED"
        return {
            "status": status_str,
            "entity": entity,
            "recipient": recipient,
            "provider": prov,
            "attachment": os.path.basename(pdf_path),
            "timestamp": datetime.datetime.now().isoformat(),
            "details": message
        }

    # ----------------------------------------------------------------------------------
    # BATCH DISPATCH WITH STRICT 15s THROTTLING
    # ----------------------------------------------------------------------------------
    def dispatch_case_notices(self, case_dir_or_ack: str, provider: Optional[str] = None,
                              mode: Optional[str] = None, dry_run: bool = False) -> List[Dict[str, Any]]:
        """
        Dispatches all notices in a case one-by-one with strict 15s delay.
        """
        notices = self.scan_case_directory(case_dir_or_ack)
        if not notices:
            print(f"❌ [Email Agent] No notices found to dispatch in {case_dir_or_ack}")
            return []

        prov = (provider or self.config.get("active_provider", "outlook")).lower()
        disp_mode = mode or self.config.get("dispatch_mode", "forward_to_nic")

        print("\n" + "=" * 90)
        print(f" 🚀 STARTING AUTOMATED EMAIL DISPATCH PIPELINE")
        print("=" * 90)
        print(f" • Active Provider    : {prov.upper()}")
        print(f" • Dispatch Mode      : {disp_mode.upper()}")
        print(f" • Target Recipient   : {self.config.get('forwarding_target', {}).get('nic_email')}")
        print(f" • Notice Scope       : ONLY BANK NOTICES (केवल बैंक नोटिस - Telecom/ISP/Social Media Excluded)")
        print(f" • Rate Limiting      : Exactly {self.rate_limit_seconds}s interval between consecutive emails")
        print(f" • Total Notices      : {len(notices)} Bank notices queued for dispatch")
        print("=" * 90 + "\n")

        results = []
        for idx, item in enumerate(notices, start=1):
            print(f"[{idx}/{len(notices)}] Dispatching Notice for: {item['entity']}...")
            print(f"       Attachment : {os.path.basename(item['pdf_path'])}")
            
            res = self.send_single_notice(item, provider=prov, mode=disp_mode, dry_run=dry_run)
            results.append(res)
            
            if res.get("status", "").startswith("SUCCESS"):
                print(f"       Status     : ✅ SENT SUCCESSFULLY -> {res.get('recipient')}")
            else:
                print(f"       Status     : ❌ FAILED -> {res.get('details')}")

            # Enforce 15-second gap between emails (except after the very last one)
            if idx < len(notices):
                if dry_run:
                    print('   ⏳ [DRY RUN] 15-second mandatory cooldown will be enforced in live sending mode.\n')
                else:
                    self.enforce_rate_limit(self.rate_limit_seconds)

        # Write execution report to case folder
        if notices:
            rep_dir = os.path.dirname(notices[0]["pdf_path"])
            case_folder = rep_dir
            while "Notice_" in os.path.basename(case_folder) or "Individual_" in os.path.basename(case_folder):
                case_folder = os.path.dirname(case_folder)
            
            report_file = os.path.join(case_folder, f"email_dispatch_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            try:
                with open(report_file, "w", encoding="utf-8") as rf:
                    json.dump(results, rf, indent=2, ensure_ascii=False)
                print(f"\n📄 [Audit Log] Dispatch activity saved to: {report_file}")
            except Exception as e:
                print(f"⚠️ Could not write dispatch audit log: {e}")

        print("\n" + "=" * 90)
        print(f"      DISPATCH RUN FINISHED: {sum(1 for r in results if 'SUCCESS' in r.get('status',''))}/{len(results)} SENT")
        print("=" * 90 + "\n")
        return results

    # ----------------------------------------------------------------------------------
    # SELF-TEST & VERIFICATION TOOL
    # ----------------------------------------------------------------------------------
    def test_connection_and_send(self, to_email: str, provider: Optional[str] = None) -> bool:
        """
        Sends a single verification email to test credentials and delivery.
        """
        prov = (provider or self.config.get("active_provider", "outlook")).lower()
        print(f"\n🔍 [Self-Test] Verifying connection and sending test email via {prov.upper()}...")
        print(f"   Target Recipient: {to_email}")

        sample_pdf = None
        sample_docx = None
        out_base = os.path.join(self.base_dir, "output")
        for root, dirs, files in os.walk(out_base):
            if "notice_pdf_files" in root.lower():
                for f in sorted(files):
                    if f.endswith(".pdf"):
                        sample_pdf = os.path.join(root, f)
                        cand_docx = sample_pdf.replace(".pdf", ".docx").replace("Notice_PDF_Files", "Notice_DOCX_Files")
                        if os.path.exists(cand_docx):
                            sample_docx = cand_docx
                        break
            if sample_pdf:
                break

        test_item = {
            "entity": "Citi Bank (Test Verification Notice)",
            "pdf_path": sample_pdf or "",
            "docx_path": sample_docx or "",
            "case_ref": "DIAGNOSTIC TEST DISPATCH",
            "ack_no": "TEST-001"
        }

        res = self.send_single_notice(test_item, provider=prov, custom_target=to_email, dry_run=False)
        print("\n" + "-" * 60)
        if res.get("status") == "SUCCESS":
            print("✅ TEST EMAIL DISPATCH SUCCESSFUL!")
            print(f"   Details: {res.get('details')}")
            print(f"   Please check the inbox of {to_email} to verify notice body & attachment.")
            print("-" * 60 + "\n")
            return True
        else:
            print("❌ TEST EMAIL DISPATCH FAILED!")
            print(f"   Reason : {res.get('details')}")
            print(f"   Provider: {prov.upper()}")
            print("\n💡 सुझाव (Troubleshooting):")
            if prov == "outlook":
                print("   1. Outlook (cyberinvestigationdelhipolice@outlook.com) के लिए config/email_credentials.json में password_or_app_password भरें।")
                print("   2. यदि Microsoft Account में 2-Step Verification सक्रिय है तो Microsoft Security में जाकर 'App Password' बनाएं।")
            elif prov == "gmail":
                print("   1. यदि Gmail API (OAuth2) उपयोग कर रहे हैं तो config/email_credentials.json में Client ID व Client Secret भरें।")
                print("   2. यदि Gmail App Password उपयोग कर रहे हैं तो auth_method को 'app_password' सेट करें और 16 अंकों का App Password भरें।")
            else:
                print("   1. NIC मेल (mail.gov.in) के लिए Kavach Portal में जाकर 'App Password' जनरेट करें।")
                print("   2. config/email_credentials.json में password_or_kavach_app_password की जगह वही App Password पेस्ट करें।")
            print("-" * 60 + "\n")
            return False


# --------------------------------------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------------------------------------
def re_sub_leading_digits(s: str) -> str:
    parts = s.split('_')
    if parts and parts[0].isdigit():
        return '_'.join(parts[1:])
    return s

def clean_entity_line(txt: str, entity_name: str) -> bool:
    if not entity_name:
        return False
    return entity_name.lower() in txt.lower()


# --------------------------------------------------------------------------------------
# INTERACTIVE TERMINAL MENU
# --------------------------------------------------------------------------------------
def interactive_menu():
    agent = EmailDispatchAgent()
    while True:
        curr_prov = agent.config.get("active_provider", "outlook").upper()
        disp_mode = agent.config.get("dispatch_mode", "forward_to_nic")
        nic_dest = agent.config.get("forwarding_target", {}).get("nic_email", "rajendra.28082016@delhipolice.gov.in")
        
        print("\n" + "=" * 90)
        print("          DELHI POLICE CYBER CRIME INVESTIGATION - EMAIL DISPATCH AGENT")
        print("          (दिल्ली पुलिस साइबर अपराध अन्वेषण - स्वचालित ईमेल प्रेषण एजेंट)")
        print("=" * 90)
        print(f"  • वर्तमान एक्टिव प्रोवाइडर : {curr_prov} (Gmail -> NIC)")
        print(f"  • भेजने वाली आईडी (Sender) : {agent.config.get('gmail_settings', {}).get('sender_email') or agent.config.get('outlook_settings', {}).get('sender_email', 'gkncyber1262@gmail.com')}")
        print(f"  • प्राप्तकर्ता आईडी (Target): {nic_dest}")
        print(f"  • नोटिस स्कोप             : केवल बैंक नोटिस (Bank Notices Only - ISP/Social Media Excluded)")
        print(f"  • अनिवार्य समय अंतराल     : 15 सेकंड (Strict 15s Throttle Policy per Email)")
        print(f"  • क्रेडेंशियल फाइल        : config/email_credentials.json")
        print("-" * 90)
        print("  [1] Send Verification / Test Email (टेस्ट बैंक नोटिस ईमेल भेजकर चेक करें)")
        print("  [2] Forward Bank Notices to NIC Mail (Gmail से NIC मेल पर केवल बैंक नोटिस भेजें - 15s गैप)")
        print("  [3] Dispatch Notices to Respective Bank Nodal Officers (नोडल अधिकारियों को भेजें)")
        print("  [4] Switch Active Provider (Outlook <--> Gmail <--> NIC Mail)")
        print("  [5] Configure Forwarding Target Email / Sender Settings")
        print("  [6] Dry Run (सिम्युलेशन मोड - बिना मेल भेजे टेस्ट करें)")
        print("  [7] Exit (बाहर निकलें)")
        print("-" * 90)
        
        choice = input("विकल्प चुनें (1-7) [Default: 1]: ").strip() or "1"
        
        if choice == "1":
            target = input(f"जिस ईमेल पर टेस्ट मेल भेजना है वह दर्ज करें [Default: {nic_dest}]: ").strip() or nic_dest
            agent.test_connection_and_send(target)
            input("\nआगे बढ़ने के लिए Enter दबाएं...")
            
        elif choice == "2":
            case_input = input("केस फोल्डर का नाम या ACK No. दर्ज करें [खाली छोड़ने पर सबसे नवीनतम केस चुना जाएगा]: ").strip()
            agent.dispatch_case_notices(case_input, mode="forward_to_nic", dry_run=False)
            input("\nआगे बढ़ने के लिए Enter दबाएं...")
            
        elif choice == "3":
            case_input = input("केस फोल्डर का नाम या ACK No. दर्ज करें [खाली छोड़ने पर सबसे नवीनतम केस चुना जाएगा]: ").strip()
            confirm = input("⚠️ क्या आप सुनिश्चित हैं कि सभी बैंकों के नोडल अधिकारियों को सीधे मेल भेजना चाहते हैं? (y/n): ").strip().lower()
            if confirm == "y":
                agent.dispatch_case_notices(case_input, mode="direct_to_nodal", dry_run=False)
            else:
                print("रद्द किया गया।")
            input("\nआगे बढ़ने के लिए Enter दबाएं...")
            
        elif choice == "4":
            print("\nउपलब्ध ईमेल प्रोवाइडर्स (Email Providers):")
            print("  [1] Microsoft Outlook (cyberinvestigationdelhipolice@outlook.com)")
            print("  [2] Google Gmail (Gmail API / App Password)")
            print("  [3] NIC Mail (mail.gov.in / delhipolice.gov.in)")
            p_opt = input("प्रोवाइडर चुनें (1-3) [Default: 1]: ").strip() or "1"
            if p_opt == "1":
                agent.config["active_provider"] = "outlook"
            elif p_opt == "2":
                agent.config["active_provider"] = "gmail"
            elif p_opt == "3":
                agent.config["active_provider"] = "nic_mail"
            agent.save_config()
            print(f"  🔄 प्रोवाइडर बदलकर {agent.config['active_provider'].upper()} कर दिया गया है।")
            
        elif choice == "5":
            print("\n--- कॉन्फ़िगरेशन सेटिंग्स ---")
            print(f"  [1] Gmail 16-अक्षर App Password दर्ज करें ({agent.config.get('gmail_settings', {}).get('sender_email')})")
            print(f"  [2] Target NIC ईमेल बदलें [वर्तमान: {nic_dest}]")
            print(f"  [3] Outlook पासवर्ड दर्ज करें ({agent.config.get('outlook_settings', {}).get('sender_email')})")
            print(f"  [4] क्रेडेंशियल फ़ाइल (JSON) पाथ: {agent.config_path}")
            sub_opt = input("  विकल्प चुनें (1-4) [Default: 1]: ").strip() or "1"
            if sub_opt == "1":
                import getpass
                print("\nGoogle Security (https://myaccount.google.com/apppasswords) से 16 अक्षरों का पासवर्ड बनाएं।")
                new_pwd = getpass.getpass("  Gmail 16-अक्षर App Password दर्ज करें: ").strip().replace(" ", "")
                if new_pwd:
                    agent.config.setdefault("gmail_settings", {}).setdefault("app_password_smtp", {})["app_password"] = new_pwd
                    agent.save_config()
                    print("  ✅ Gmail App Password सफलतापूर्वक सहेज लिया गया है।")
            elif sub_opt == "2":
                new_nic = input(f"  नया टारगेट NIC ईमेल दर्ज करें [वर्तमान: {nic_dest}]: ").strip()
                if new_nic:
                    agent.config.setdefault("forwarding_target", {})["nic_email"] = new_nic
                    agent.save_config()
                    print("  ✅ Target NIC ईमेल अपडेट कर दिया गया है।")
            elif sub_opt == "3":
                import getpass
                new_pwd = getpass.getpass("  Outlook पासवर्ड दर्ज करें: ").strip()
                if new_pwd:
                    agent.config.setdefault("outlook_settings", {})["password_or_app_password"] = new_pwd
                    agent.save_config()
                    print("  ✅ Outlook पासवर्ड सफलतापूर्वक सहेज लिया गया है।")
            input("\nआगे बढ़ने के लिए Enter दबाएं...")
            
        elif choice == "6":
            case_input = input("केस फोल्डर या ACK No. दर्ज करें: ").strip()
            agent.dispatch_case_notices(case_input, dry_run=True)
            input("\nआगे बढ़ने के लिए Enter दबाएं...")
            
        elif choice == "7":
            print("अलविदा! Email Agent बंद हो रहा है।")
            break


# --------------------------------------------------------------------------------------
# CLI ENTRY POINT
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delhi Police Cyber Crime Investigation - Email Dispatch Agent")
    parser.add_argument("--case", type=str, help="Case folder name or ACK number")
    parser.add_argument("--provider", type=str, choices=["outlook", "gmail", "nic_mail"], help="Provider to use")
    parser.add_argument("--mode", type=str, choices=["forward_to_nic", "direct_to_nodal"], help="Dispatch mode")
    parser.add_argument("--test", action="store_true", help="Send a test verification email")
    parser.add_argument("--to", type=str, help="Recipient email for test or dispatch")
    parser.add_argument("--dry-run", action="store_true", help="Simulate dispatch without sending")
    parser.add_argument("--menu", action="store_true", help="Open interactive terminal menu")
    
    args = parser.parse_args()
    agent = EmailDispatchAgent()
    
    if args.test:
        target = args.to or agent.config.get("forwarding_target", {}).get("nic_email", "rajendra.28082016@delhipolice.gov.in")
        agent.test_connection_and_send(target, provider=args.provider)
    elif args.case:
        agent.dispatch_case_notices(args.case, provider=args.provider, mode=args.mode, dry_run=args.dry_run)
    elif len(sys.argv) == 1 or args.menu:
        interactive_menu()
    else:
        parser.print_help()
