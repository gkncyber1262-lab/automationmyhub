# -*- coding: utf-8 -*-
"""
========================================================================================
     DELHI POLICE CYBER CRIME INVESTIGATION - 5-CASE BATCH EXECUTION RUNNER
     (5 शिकायतों का स्वचालित बैच प्रोसेसिंग एवं ई-डिस्पैच निष्पादक)
========================================================================================
Case Specifications:
  1. AcknowledgementNo_30808260070812.pdf -> FIR No. 0387/2026 Dated 21/08/2026
  2. AcknowledgementNo_30809260086615.pdf -> FIR No. 0272/2026 Dated 23/09/2026
  3. AcknowledgementNo_30809260089905.pdf -> FIR No. 0281/2026 Dated 30/09/2026
  4. AcknowledgementNo_30810260093099.pdf -> FIR No. 294/2026 Dated 02/11/2026
  5. AcknowledgementNo_30810260096918.pdf -> FIR No. 287/2026 Dated 02/11/2026

Notice & Dispatch Policy:
  • Each FIR gets its OWN isolated, separate output folder (FIR_XXXX_2026).
  • Starting Notice No.: 5739 (Sequential Increment across all bank notices).
  • IO: SI RENU (SUB INSPECTOR | Mob: 9899959840 | shocyber.north@delhipolice.gov.in)
  • Signature: Unsigned / Blank space for physical signing & station seal.
  • Email: Forward only bank notices to rajendra.28082016@delhipolice.gov.in with 15s throttle.
========================================================================================
"""

import os
import sys
import re
import json
import time
import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from ncrp_master_agent import NCRPUnifiedAgent
from email_dispatch_agent import EmailDispatchAgent


def main():
    agent = NCRPUnifiedAgent()
    email_agent = EmailDispatchAgent()

    # Target settings
    target_nic_email = "rajendra.28082016@delhipolice.gov.in"
    email_agent.config.setdefault("forwarding_target", {})["nic_email"] = target_nic_email
    email_agent.config["notice_scope"] = "banks_only"

    io_details = {
        "name": "SI RENU",
        "rank": "SUB INSPECTOR",
        "mobile": "9899959840",
        "belt_no": "9899959840",
        "email": "shocyber.north@delhipolice.gov.in"
    }

    cases_manifest = [
        {
            "file": "AcknowledgementNo_30808260070812.pdf",
            "ack_no": "30808260070812",
            "is_fir": True,
            "fir_no": "287/2026",
            "fir_date": "21/08/2026",
            "fir_sections": "318(4) BNS"
        },
        {
            "file": "AcknowledgementNo_30809260086615.pdf",
            "ack_no": "30809260086615",
            "is_fir": True,
            "fir_no": "0272/2026",
            "fir_date": "23/09/2026",
            "fir_sections": "318(4) BNS"
        },
        {
            "file": "AcknowledgementNo_30809260089905.pdf",
            "ack_no": "30809260089905",
            "is_fir": True,
            "fir_no": "0281/2026",
            "fir_date": "30/09/2026",
            "fir_sections": "318(4) BNS"
        },
        {
            "file": "AcknowledgementNo_30810260093099.pdf",
            "ack_no": "30810260093099",
            "is_fir": True,
            "fir_no": "294/2026",
            "fir_date": "02/11/2026",
            "fir_sections": "318(4) BNS"
        },
        {
            "file": "AcknowledgementNo_30810260096918.pdf",
            "ack_no": "30810260096918",
            "is_fir": False,
            "fir_no": "",
            "fir_date": "02/11/2026",
            "fir_sections": "318(4) BNS"
        }
    ]

    print("\n" + "=" * 90)
    print("      DELHI POLICE CYBER CRIME INVESTIGATION - 5-CASE BATCH PROCESSING")
    print("=" * 90)
    print(f" • कुल केस (Total Cases)      : {len(cases_manifest)} केस")
    print(f" • स्टार्टिंग नोटिस नंबर        : Notice No. 5739 (Sequential increment)")
    print(f" • जांच अधिकारी (IO)          : {io_details['rank']} {io_details['name']} (Mob: {io_details['mobile']})")
    print(f" • टारगेट NIC ईमेल            : {target_nic_email}")
    print(f" • रेट लिमिटिंग समय अंतराल     : 15 सेकंड (Strict 15s Throttle Policy per Email)")
    print(f" • पृथक आउटपुट फोल्डर्स      : प्रत्येक e-FIR का 100% अलग आउटपुट फोल्डर (FIR_XXXX_2026)")
    print("=" * 90 + "\n")

    is_dry_run = "--dry-run" in sys.argv
    dispatch_only = "--dispatch-only" in sys.argv

    if is_dry_run:
        print("⚠️ [सूचना] DRY-RUN मोड सक्रिय: वास्तविक ईमेल नहीं भेजे जाएंगे, केवल सिमुलेशन होगा।\n")

    current_notice_no = 5739
    generated_case_dirs = []
    case_summary = []

    # ----------------------------------------------------------------------------------
    # PHASE 1: GENERATE ALL NOTICES & CASE DIARIES PER CASE
    # ----------------------------------------------------------------------------------
    if dispatch_only:
        print("\n⏩ [डिस्पैच-ओनली मोड] पूर्व-निर्मित 5 केसों के बैंक नोटिस सीधे लोड किए जा रहे हैं...")
        for c_info in cases_manifest:
            is_case_fir = c_info.get("is_fir", bool(c_info.get("fir_no")))
            if is_case_fir and c_info.get("fir_no"):
                clean_fir = re.sub(r'[^a-zA-Z0-9_-]', '_', str(c_info["fir_no"]))
                case_dir = os.path.join(agent.output_dir, f"FIR_{clean_fir}")
            else:
                case_dir = os.path.join(agent.output_dir, f"Case_{c_info['ack_no']}")
            pdf_dir = os.path.join(case_dir, "Notice_PDF_Files")
            bank_count = len([f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]) if os.path.exists(pdf_dir) else 0
            generated_case_dirs.append(case_dir)
            case_summary.append({
                "fir_no": c_info.get("fir_no") or f"ACK: {c_info['ack_no']}",
                "ack_no": c_info["ack_no"],
                "file": c_info["file"],
                "bank_notices": bank_count,
                "case_dir": os.path.basename(case_dir),
                "status": "SUCCESS"
            })
    else:
        for idx, c_info in enumerate(cases_manifest, start=1):
            fpath = os.path.join(agent.input_dir, c_info["file"])
            print("\n" + "#" * 90)
            print(f" 📂 [केस {idx}/{len(cases_manifest)}] प्रोसेसिंग प्रारंभ: {c_info['file']}")
            is_case_fir = c_info.get("is_fir", bool(c_info.get("fir_no")))
            fir_label = f"e-FIR No. : {c_info['fir_no']} | Date: {c_info['fir_date']}" if is_case_fir else "Mode: NCRP Acknowledgement Complaint"
            print(f"    {fir_label}")
            print(f"    ACK No.   : {c_info['ack_no']}")
            print(f"    Start No. : Notice No. {current_notice_no}")
            print("#" * 90)

            fir_d = {
                "is_fir": is_case_fir,
                "fir_no": c_info.get("fir_no", ""),
                "fir_date": c_info.get("fir_date", ""),
                "fir_sections": c_info.get("fir_sections", "318(4) BNS")
            }

            try:
                ctx = agent.run_case_pipeline(
                    case_file_or_target=fpath,
                    fir_details=fir_d,
                    io_override=io_details,
                    start_notice_no=current_notice_no,
                    notice_date_override="02/11/2026",
                    sign_mode="unsigned"
                )

                if is_case_fir and c_info.get("fir_no"):
                    clean_fir = re.sub(r'[^a-zA-Z0-9_-]', '_', str(c_info["fir_no"]))
                    case_dir = ctx.get("case_dir") or os.path.join(agent.output_dir, f"FIR_{clean_fir}")
                else:
                    case_dir = ctx.get("case_dir") or os.path.join(agent.output_dir, f"Case_{c_info['ack_no']}")
                generated_case_dirs.append(case_dir)

                # Count bank notices generated
                pdf_dir = os.path.join(case_dir, "Notice_PDF_Files")
                bank_count = len([f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]) if os.path.exists(pdf_dir) else 0

                # Update running notice counter
                current_notice_no += bank_count

                case_summary.append({
                    "fir_no": c_info.get("fir_no") or f"ACK: {c_info['ack_no']}",
                    "ack_no": c_info["ack_no"],
                    "file": c_info["file"],
                    "bank_notices": bank_count,
                    "case_dir": os.path.basename(case_dir),
                    "status": "SUCCESS"
                })
                print(f"\n✅ केस {c_info['fir_no']} सफल! {bank_count} बैंक नोटिस तैयार हुए फोल्डर: {os.path.basename(case_dir)}")

            except Exception as e:
                print(f"\n❌ [केस {c_info['fir_no']} त्रुटि]: {e}")
                case_summary.append({
                    "fir_no": c_info["fir_no"],
                    "ack_no": c_info["ack_no"],
                    "file": c_info["file"],
                    "bank_notices": 0,
                    "case_dir": "FAILED",
                    "status": f"FAILED: {e}"
                })

    # ----------------------------------------------------------------------------------
    # PHASE 2: AUTOMATED EMAIL DISPATCH TO NIC MAIL (15s DELAY)
    # ----------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print(" 🚀 PHASE 2: सभी 5 केसों के बैंक नोटिस ईमेल द्वारा NIC मेल पर भेजे जा रहे हैं...")
    print(f"    टारगेट: {target_nic_email} | प्रेषक: gkncyber1262@gmail.com")
    print(f"    रेट लिमिटिंग: प्रति ईमेल 15 सेकंड का सुरक्षित अंतराल")
    print("=" * 90 + "\n")

    total_dispatched = []
    for c_idx, c_dir in enumerate(generated_case_dirs, start=1):
        if not c_dir or not os.path.exists(c_dir):
            continue
        c_name = os.path.basename(c_dir)
        print("\n" + "-" * 70)
        print(f" 📨 [डिस्पैच {c_idx}/{len(generated_case_dirs)}] केस फोल्डर: {c_name} के बैंक नोटिस...")
        print("-" * 70)

        res = email_agent.dispatch_case_notices(c_dir, dry_run=is_dry_run)
        total_dispatched.extend(res)

    # ----------------------------------------------------------------------------------
    # FINAL CONSOLIDATED REPORT
    # ----------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("                   5-केस बैच प्रोसेसिंग संपूर्ण ऑडिट रिपोर्ट")
    print("=" * 90)
    for cs in case_summary:
        st_icon = "✅" if cs["status"] == "SUCCESS" else "❌"
        print(f" {st_icon} e-FIR: {cs['fir_no']:<12} | ACK: {cs['ack_no']:<16} | बैंक नोटिस: {cs['bank_notices']:2d} | फोल्डर: {cs['case_dir']}")

    success_emails = sum(1 for r in total_dispatched if "SUCCESS" in r.get("status", ""))
    print("-" * 90)
    print(f" 📬 कुल ईमेल प्रेषण संपन्न: {success_emails}/{len(total_dispatched)} बैंक नोटिस सफलतापूर्वक डिलीवर हुए!")
    print(f"    प्राप्तकर्ता इनबॉक्स : {target_nic_email}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
