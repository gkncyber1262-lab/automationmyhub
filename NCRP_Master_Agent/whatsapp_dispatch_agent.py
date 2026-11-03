# -*- coding: utf-8 -*-
"""
========================================================================================
     DELHI POLICE CYBER CRIME INVESTIGATION - WHATSAPP DISPATCH AGENT
     (दिल्ली पुलिस साइबर अपराध अन्वेषण - स्वचालित व्हाट्सएप नोटिस प्रेषण एजेंट)
========================================================================================
Features:
  1. Multi-Gateway Support (Background REST APIs):
     - Green API (green-api.com: waInstance / sendFileByUpload)
     - UltraMsg (ultramsg.com: instance / messages/document)
  2. Notice Attachment:
     - Directly uploads and delivers official Section 94 BNSS Notice PDF files
     - Formats statutory message with FIR No., Section 318(4) BNS, Ack No., Notice No., IO details
  3. Safety & Throttling:
     - Configurable 10-15s cooldown per message to prevent WhatsApp rate-limiting/spam flags
     - Audit logging per case folder (whatsapp_dispatch_log_*.json)
  4. Modes:
     - Dry Run mode (--dry-run) for verification without API tokens
     - Single case or all 5 batch cases dispatch
========================================================================================
"""

import os
import sys
import json
import time
import re
import datetime
import argparse
from typing import Dict, List, Any, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import requests
except ImportError:
    requests = None


class WhatsAppDispatchAgent:
    def __init__(self, config_path: Optional[str] = None):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = config_path or os.path.join(self.base_dir, "config", "whatsapp_credentials.json")
        self.station_config_path = os.path.join(self.base_dir, "config", "config.json")
        
        self.config = self._load_json(self.config_path)
        self.station_config = self._load_json(self.station_config_path)
        
        self.rate_limit_seconds = self.config.get("rate_limiting", {}).get("delay_seconds_between_messages", 10)

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
    # NOTICE SCANNER & METADATA EXTRACTOR
    # ----------------------------------------------------------------------------------
    def scan_case_directory(self, case_dir_or_name: str) -> List[Dict[str, Any]]:
        """
        Scans a case output folder for generated notice PDF files and extracts metadata.
        """
        target_dir = case_dir_or_name
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
            print(f"❌ [WhatsApp Agent] Case directory not found: {case_dir_or_name}")
            return []

        pdf_dir = os.path.join(target_dir, "Notice_PDF_Files")
        if not os.path.exists(pdf_dir):
            # Try searching directly
            pdf_dir = target_dir

        # Load case context if available
        context_file = os.path.join(target_dir, "case_context.json")
        ctx = self._load_json(context_file) if os.path.exists(context_file) else {}

        items = []
        for fname in sorted(os.listdir(pdf_dir)):
            if fname.lower().endswith(".pdf") and fname.startswith("Notice_"):
                pdf_path = os.path.join(pdf_dir, fname)
                
                # Derive entity name from filename
                raw_entity = fname.replace("Notice_", "").replace(".pdf", "")
                parts = raw_entity.split("_")
                if parts and parts[0].isdigit():
                    parts = parts[1:]
                entity_name = " ".join(parts).strip()

                # Extract notice number if possible
                notice_no = ""
                try:
                    import pypdf
                    reader = pypdf.PdfReader(pdf_path)
                    if reader.pages:
                        txt = reader.pages[0].extract_text() or ""
                        m = re.search(r'NOTICE NO\.\s*(\d+)', txt)
                        if m:
                            notice_no = m.group(1)
                except Exception:
                    pass

                items.append({
                    "entity": entity_name,
                    "pdf_path": pdf_path,
                    "pdf_filename": fname,
                    "notice_no": notice_no,
                    "case_dir": target_dir,
                    "case_context": ctx
                })

        return items

    def format_whatsapp_message(self, notice_info: Dict[str, Any], custom_io: Optional[Dict[str, str]] = None) -> str:
        """
        Creates a legally compliant, clean WhatsApp text notice for police communication.
        """
        ctx = notice_info.get("case_context", {})
        meta = ctx.get("case_meta", {})
        comp = ctx.get("complainant", {})

        fir_no = meta.get("fir_no") or "—"
        fir_date = meta.get("fir_date") or ""
        ack_no = meta.get("ack_no") or comp.get("ack_no") or "N/A"
        sections = meta.get("fir_sections") or "318(4) BNS"
        entity_name = notice_info.get("entity") or "Nodal Officer"
        notice_no = notice_info.get("notice_no") or "—"

        io_name = custom_io.get("name") if custom_io else "SI RENU"
        io_rank = custom_io.get("rank") if custom_io else "SUB INSPECTOR"
        io_mobile = custom_io.get("mobile") if custom_io else "9899959840"

        case_header = f"Case FIR No. {fir_no} Dated {fir_date}" if fir_no and fir_no != "—" else f"NCRP ACK No. {ack_no}"

        msg = (
            f"🏛️ *OFFICE OF THE STATION HOUSE OFFICER*\n"
            f"*CYBER POLICE STATION, NORTH DISTRICT, DELHI*\n"
            f"Assistant Commissioner of Police Operations Office Complex,\n"
            f"Maurice Nagar, Delhi - 110007\n"
            f"────────────────────────────\n"
            f"📜 *STATUTORY POLICE NOTICE U/S 94 BNSS, 2023*\n\n"
            f"• *संदर्भ / Case:* {case_header}\n"
            f"• *धाराएं / Sections:* {sections}\n"
            f"• *NCRP Complaint ID:* {ack_no}\n"
            f"• *Notice Ref No.:* {notice_no}/Cyber PS North\n\n"
            f"🏦 *To: Legal Operations / Nodal Officer,*\n"
            f"*{entity_name}*\n\n"
            f"⚖️ *Action Mandated:* Immediate lien marking / debit freeze on suspect accounts "
            f"and submission of complete account opening forms, KYC documents, and transaction statements.\n"
            f"────────────────────────────\n"
            f"👤 *Investigating Officer (IO):*\n"
            f"{io_rank} {io_name} (Mob: {io_mobile})\n"
            f"Cyber Police Station, North District, Delhi\n"
            f"📧 Email: shocyber.north@delhipolice.gov.in\n"
            f"────────────────────────────\n"
            f"📎 *Attached Document:* {notice_info.get('pdf_filename')}\n"
            f"*(Official notice attached herewith for urgent compliance)*"
        )
        return msg

    # ----------------------------------------------------------------------------------
    # GATEWAY DISPATCH IMPLEMENTATIONS
    # ----------------------------------------------------------------------------------
    def send_via_green_api(self, phone: str, notice_info: Dict[str, Any], caption: str) -> Dict[str, Any]:
        """
        Sends PDF document via Green API (sendFileByUpload endpoint).
        Docs: https://green-api.com/en/docs/api/sending/SendFileByUpload/
        """
        if not requests:
            return {"status": "FAILED", "error": "Python requests module not installed"}

        green_cfg = self.config.get("gateways", {}).get("green_api", {})
        id_instance = green_cfg.get("id_instance", "").strip()
        api_token = green_cfg.get("api_token_instance", "").strip()
        api_url = green_cfg.get("api_url", "https://api.green-api.com").rstrip("/")

        if not id_instance or not api_token:
            return {
                "status": "NOT_CONFIGURED",
                "error": "Green API id_instance or api_token_instance is missing in config/whatsapp_credentials.json"
            }

        # Format recipient phone: remove +, spaces, dashes, append @c.us if not present
        clean_phone = re.sub(r'[^0-9]', '', str(phone))
        if not clean_phone.startswith("91") and len(clean_phone) == 10:
            clean_phone = "91" + clean_phone
        chat_id = f"{clean_phone}@c.us"

        url = f"{api_url}/waInstance{id_instance}/sendFileByUpload/{api_token}"
        pdf_path = notice_info["pdf_path"]
        pdf_name = notice_info["pdf_filename"]

        try:
            with open(pdf_path, "rb") as f:
                files = {
                    "file": (pdf_name, f, "application/pdf")
                }
                data = {
                    "chatId": chat_id,
                    "caption": caption,
                    "fileName": pdf_name
                }
                resp = requests.post(url, data=data, files=files, timeout=45)
                res_json = resp.json() if resp.status_code == 200 else {}

            if resp.status_code == 200 and res_json.get("idMessage"):
                return {
                    "status": "SUCCESS",
                    "gateway": "green_api",
                    "message_id": res_json.get("idMessage"),
                    "recipient": clean_phone
                }
            else:
                return {
                    "status": "FAILED",
                    "gateway": "green_api",
                    "http_code": resp.status_code,
                    "response": resp.text
                }
        except Exception as e:
            return {"status": "ERROR", "gateway": "green_api", "error": str(e)}

    def send_via_ultramsg(self, phone: str, notice_info: Dict[str, Any], caption: str) -> Dict[str, Any]:
        """
        Sends PDF document via UltraMsg API (/messages/document endpoint).
        Docs: https://docs.ultramsg.com/api/post/messages/document
        """
        if not requests:
            return {"status": "FAILED", "error": "Python requests module not installed"}

        ultra_cfg = self.config.get("gateways", {}).get("ultramsg", {})
        instance_id = ultra_cfg.get("instance_id", "").strip()
        token = ultra_cfg.get("token", "").strip()
        api_url = ultra_cfg.get("api_url", "https://api.ultramsg.com").rstrip("/")

        if not instance_id or not token:
            return {
                "status": "NOT_CONFIGURED",
                "error": "UltraMsg instance_id or token is missing in config/whatsapp_credentials.json"
            }

        clean_phone = re.sub(r'[^0-9]', '', str(phone))
        if not clean_phone.startswith("91") and len(clean_phone) == 10:
            clean_phone = "91" + clean_phone

        url = f"{api_url}/{instance_id}/messages/document"
        pdf_path = notice_info["pdf_path"]
        pdf_name = notice_info["pdf_filename"]

        try:
            # UltraMsg can accept document via multipart upload or base64
            with open(pdf_path, "rb") as f:
                import base64
                encoded_doc = base64.b64encode(f.read()).decode("utf-8")
                doc_payload = f"data:application/pdf;base64,{encoded_doc}"

            payload = {
                "token": token,
                "to": clean_phone,
                "filename": pdf_name,
                "document": doc_payload,
                "caption": caption
            }
            resp = requests.post(url, data=payload, timeout=45)
            res_json = resp.json() if resp.status_code == 200 else {}

            if resp.status_code == 200 and res_json.get("sent") == "true":
                return {
                    "status": "SUCCESS",
                    "gateway": "ultramsg",
                    "message_id": res_json.get("id"),
                    "recipient": clean_phone
                }
            else:
                return {
                    "status": "FAILED",
                    "gateway": "ultramsg",
                    "http_code": resp.status_code,
                    "response": resp.text
                }
        except Exception as e:
            return {"status": "ERROR", "gateway": "ultramsg", "error": str(e)}

    # ----------------------------------------------------------------------------------
    # BATCH DISPATCH EXECUTION
    # ----------------------------------------------------------------------------------
    def dispatch_case_notices(self, case_dir_or_ack: str, phone: Optional[str] = None,
                              gateway: Optional[str] = None, dry_run: bool = False,
                              io_override: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Dispatches all notices in a given case folder with throttling.
        """
        notices = self.scan_case_directory(case_dir_or_ack)
        if not notices:
            print(f"❌ [WhatsApp Agent] No notices found in {case_dir_or_ack}")
            return []

        active_gw = (gateway or self.config.get("active_gateway", "green_api")).lower()
        target_phone = phone or self.config.get("recipient_settings", {}).get("default_phone", "919899959840")
        target_phone = re.sub(r'[^0-9]', '', str(target_phone))
        if not target_phone.startswith("91") and len(target_phone) == 10:
            target_phone = "91" + target_phone

        print("\n" + "=" * 90)
        print(" 📲 STARTING AUTOMATED WHATSAPP DISPATCH PIPELINE")
        print("=" * 90)
        print(f" • Active Gateway    : {active_gw.upper()}")
        print(f" • Target Recipient  : +{target_phone} ({self.config.get('recipient_settings', {}).get('recipient_name', 'IO SI RENU')})")
        print(f" • Rate Limiting     : Exactly {self.rate_limit_seconds}s interval between consecutive notices")
        print(f" • Total Notices     : {len(notices)} statutory notices queued for WhatsApp delivery")
        print("=" * 90 + "\n")

        results = []
        for idx, item in enumerate(notices, start=1):
            print(f"[{idx}/{len(notices)}] Dispatching Notice for: {item['entity']}...")
            print(f"       Attachment : {item['pdf_filename']}")
            print(f"       Notice No. : {item['notice_no']}")

            caption = self.format_whatsapp_message(item, custom_io=io_override)

            if dry_run:
                print(f"  [DRY RUN] Would send to WhatsApp +{target_phone} via {active_gw.upper()}")
                print(f"            Attachment: {item['pdf_path']}")
                print("            Message Preview:\n" + "-" * 40)
                print(caption[:300] + "\n...[truncated for display]")
                print("-" * 40)
                res = {
                    "status": "SUCCESS",
                    "mode": "DRY_RUN",
                    "gateway": active_gw,
                    "entity": item["entity"],
                    "notice_no": item["notice_no"],
                    "recipient": target_phone,
                    "filename": item["pdf_filename"]
                }
            else:
                if active_gw == "ultramsg":
                    res = self.send_via_ultramsg(target_phone, item, caption)
                else:
                    res = self.send_via_green_api(target_phone, item, caption)

                res["entity"] = item["entity"]
                res["notice_no"] = item["notice_no"]
                res["filename"] = item["pdf_filename"]

            results.append(res)
            st_text = "✅ SENT SUCCESSFULLY" if res.get("status") == "SUCCESS" else f"❌ {res.get('status')}: {res.get('error', res.get('response'))}"
            print(f"       Status     : {st_text}")

            # Throttling
            if idx < len(notices):
                cooldown = self.rate_limit_seconds
                if dry_run:
                    print(f"   ⏳ [DRY RUN] {cooldown}-second cooldown will be enforced in live sending mode.\n")
                else:
                    print(f"\n⏳ [RATE LIMIT] Pausing for {cooldown} seconds before next WhatsApp dispatch...")
                    for s in range(cooldown, 0, -1):
                        bar = "█" * (cooldown - s + 1) + "░" * (s - 1)
                        print(f"\r   [{bar}] Cooling down: {s:02d}s remaining... (WhatsApp safety throttle)", end="", flush=True)
                        time.sleep(1)
                    print("\r" + " " * 90 + "\r✅ Cooldown complete. Ready for next message.\n", flush=True)

        # Save audit log
        log_dir = notices[0]["case_dir"]
        log_file = os.path.join(log_dir, f"whatsapp_dispatch_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n📄 [Audit Log] WhatsApp dispatch activity saved to: {log_file}")
        except Exception as e:
            print(f"⚠️ Could not write WhatsApp audit log: {e}")

        success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
        print("\n" + "=" * 90)
        print(f"      WHATSAPP DISPATCH RUN FINISHED: {success_count}/{len(notices)} SENT")
        print("=" * 90 + "\n")
        return results


def main():
    parser = argparse.ArgumentParser(description="Delhi Police Cyber Crime WhatsApp Dispatch Agent")
    parser.add_argument("--case", type=str, default="", help="Specific case folder or FIR (e.g. FIR_287_2026)")
    parser.add_argument("--all-cases", action="store_true", help="Dispatch notices for all 5 batch cases")
    parser.add_argument("--phone", type=str, default="", help="Recipient mobile number (e.g. 9899959840)")
    parser.add_argument("--gateway", type=str, choices=["green_api", "ultramsg"], default="", help="Active gateway")
    parser.add_argument("--dry-run", action="store_true", help="Simulate WhatsApp dispatch without sending network requests")

    args = parser.parse_args()

    agent = WhatsAppDispatchAgent()

    io_details = {
        "name": "SI RENU",
        "rank": "SUB INSPECTOR",
        "mobile": "9899959840"
    }

    if args.all_cases:
        out_base = os.path.join(agent.base_dir, "output")
        folders = [os.path.join(out_base, d) for d in os.listdir(out_base) if os.path.isdir(os.path.join(out_base, d)) and not d.startswith("_temp")]
        folders.sort()
        print(f"\n🚀 Batch WhatsApp Dispatch across {len(folders)} case folders...")
        all_results = []
        for idx, f in enumerate(folders):
            res = agent.dispatch_case_notices(f, phone=args.phone, gateway=args.gateway, dry_run=args.dry_run, io_override=io_details)
            all_results.extend(res)
            if res and idx < len(folders) - 1:
                cooldown = agent.rate_limit_seconds
                if not args.dry_run:
                    print(f"\n⏳ [RATE LIMIT] Inter-case pause for {cooldown}s before next case folder...")
                    time.sleep(cooldown)

        print("\n" + "=" * 90)
        print("                   WHATSAPP BATCH DISPATCH FINAL CONSOLIDATED REPORT")
        print("=" * 90)
        success_cnt = sum(1 for r in all_results if r.get("status") == "SUCCESS")
        print(f" 📲 Total Statutory Notices Processed: {len(all_results)}")
        print(f" ✅ Successfully Sent to WhatsApp   : {success_cnt}/{len(all_results)}")
        target_disp = args.phone or agent.config.get("recipient_settings", {}).get("default_phone", "919818036472")
        print(f" 📞 Target WhatsApp Number           : +{target_disp}")
        print("=" * 90 + "\n")
    elif args.case:
        agent.dispatch_case_notices(args.case, phone=args.phone, gateway=args.gateway, dry_run=args.dry_run, io_override=io_details)
    else:
        # Default to latest or FIR_287_2026
        target = os.path.join(agent.base_dir, "output", "FIR_287_2026")
        if not os.path.exists(target):
            target = "output"
        agent.dispatch_case_notices(target, phone=args.phone, gateway=args.gateway, dry_run=args.dry_run, io_override=io_details)


if __name__ == "__main__":
    main()
