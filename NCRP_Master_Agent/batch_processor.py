# -*- coding: utf-8 -*-
"""
========================================================================================
     DELHI POLICE CYBER CRIME INVESTIGATION - MULTI-CASE BATCH PROCESSOR
     (दिल्ली पुलिस साइबर अपराध अन्वेषण - मल्टीपल केस स्वचालित बैच प्रोसेसर)
========================================================================================
Features:
  1. Multi-Complaint Auto Discovery:
     - Scans 'input/' directory for all complaint PDF and Excel exports.
  2. Guided Interactive Interview (Q&A):
     - Q1: Case Reference (e-FIR No. vs NCRP ACK No. - Single Clubbed FIR vs Individual FIRs)
     - Q2: Notice Numbering Policy (Sequential Notice-wise Increment vs Fixed Same Number) & Date
     - Q3: Investigating Officer (IO) Details (Name, Rank, Mobile, Email & Signature Handling)
     - Q4: Automated Email Dispatch to Delhi Police NIC Email with 15-second throttle delay & CC
  3. Batch Notice & Case Diary Generation:
     - Full automated execution of Layer 1 to Layer 5 suspect bank notices, PDFs, Zimni 1/2/3,
       and money trail visualizers across all complaints.
  4. Batch Email Dispatch:
     - Direct delivery of all Bank notices from Gmail to Delhi Police NIC email with 15s delay.
========================================================================================
"""

import os
import sys
import re
import json
import time
import datetime
from typing import Dict, List, Any, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure imports resolve from current directory
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

try:
    from ncrp_master_agent import NCRPUnifiedAgent
except ImportError as e:
    print(f"⚠️ [Import Error] Could not load NCRPUnifiedAgent: {e}")
    NCRPUnifiedAgent = None

try:
    from email_dispatch_agent import EmailDispatchAgent
except ImportError as e:
    print(f"⚠️ [Import Error] Could not load EmailDispatchAgent: {e}")
    EmailDispatchAgent = None

try:
    from whatsapp_dispatch_agent import WhatsAppDispatchAgent
except ImportError as e:
    print(f"⚠️ [Import Error] Could not load WhatsAppDispatchAgent: {e}")
    WhatsAppDispatchAgent = None


def run_batch_pipeline():
    if not NCRPUnifiedAgent:
        print("❌ Error: NCRP Master Agent module not available.")
        return

    agent = NCRPUnifiedAgent()

    print("\n" + "=" * 90)
    print("      DELHI POLICE - CYBER CRIME INVESTIGATION WING (NORTH DISTRICT)")
    print("      मल्टीपल केस स्वचालित बैच प्रोसेसिंग (MULTI-CASE BATCH PROCESSOR)")
    print("=" * 90)

    # ----------------------------------------------------------------------------------
    # STEP 1: Scan and list all complaint files in input/
    # ----------------------------------------------------------------------------------
    input_files = []
    if os.path.exists(agent.input_dir):
        for f in sorted(os.listdir(agent.input_dir)):
            if f.lower().endswith(('.pdf', '.xlsx', '.xls')) and not f.startswith('~') and not f.startswith('.'):
                input_files.append(os.path.join(agent.input_dir, f))

    if not input_files:
        print(f"\n⚠️ इनपुट फोल्डर ({agent.input_dir}) में कोई PDF या Excel शिकायत फाइल नहीं मिली।")
        print("   कृपया अपनी सभी NCRP शिकायत फाइलें (जैसे AcknowledgementNo_....pdf या .xlsx) 'input' फोल्डर में रखें।")
        custom_p = input("\n👉 या किसी अन्य फोल्डर का पूरा पाथ दर्ज करें: ").strip().strip('"').strip("'")
        if custom_p and os.path.exists(custom_p):
            if os.path.isdir(custom_p):
                for f in sorted(os.listdir(custom_p)):
                    if f.lower().endswith(('.pdf', '.xlsx', '.xls')) and not f.startswith('~'):
                        input_files.append(os.path.join(custom_p, f))
            elif os.path.isfile(custom_p):
                input_files.append(custom_p)

    if not input_files:
        print("❌ कोई वैध शिकायत फाइल नहीं मिली। बैच प्रोसेसिंग समाप्त की जा रही है।")
        return

    print(f"\n📂 इनपुट फोल्डर में कुल {len(input_files)} शिकायत फाइलें पाई गईं:")
    print("─" * 90)
    for idx, fpath in enumerate(input_files, start=1):
        sz_kb = os.path.getsize(fpath) / 1024
        print(f"   [{idx}] {os.path.basename(fpath):<55} ({sz_kb:6.1f} KB)")
    print("─" * 90)

    # ----------------------------------------------------------------------------------
    # Q1: Case Reference / Identification Type (EFIR No. vs ACK No.)
    # ----------------------------------------------------------------------------------
    print("\n" + "─" * 90)
    print("📌 [सवाल 1/4] केस संदर्भ प्रकार (Case Reference: e-FIR No. vs NCRP ACK No.):")
    print("   क्या इन शिकायतों में FIR / e-FIR दर्ज हो चुकी है, या केवल Acknowledgement No. पर नोटिस जारी करने हैं?")
    print("   [1] केवल Acknowledgement Number पर नोटिस बनाने हैं (Preliminary Enquiry / U/S 94 BNSS)")
    print("   [2] इन शिकायतों में FIR / e-FIR दर्ज हो चुकी है (FIR No., Date & Sections)")
    print("─" * 90)
    ans_case_type = input("👉 उत्तर यहाँ दर्ज करें (1/2) [Default: 2]: ").strip() or "2"

    file_fir_map = {}
    if ans_case_type == "2":
        print("\n   📋 दर्ज FIR / e-FIR का विवरण:")
        print("   [1] सभी फाइलों के लिए एक ही मुख्य FIR No. लागू है (Single Clubbed FIR)")
        print("   [2] प्रत्येक शिकायत का अलग-अलग FIR No. है (Individual FIR per Complaint)")
        ans_fir_scope = input("👉 उत्तर यहाँ दर्ज करें (1/2) [Default: 1]: ").strip() or "1"

        if ans_fir_scope == "1":
            print("\n   [सभी फाइलों के लिए मुख्य FIR विवरण]:")
            fir_no = input("👉 FIR / e-FIR नंबर दर्ज करें (उदा. 281/2026): ").strip() or "281/2026"
            fir_date = input(f"👉 FIR की तारीख दर्ज करें (DD/MM/YYYY) [Default: {datetime.datetime.now().strftime('%d/%m/%Y')}]: ").strip() or datetime.datetime.now().strftime("%d/%m/%Y")
            fir_sec = input("👉 FIR की धाराएं दर्ज करें [Default: 318(4)/316(2)/61(2) BNS & 66D IT Act]: ").strip() or "318(4)/316(2)/61(2) BNS & 66D IT Act"

            for fp in input_files:
                file_fir_map[fp] = {
                    "is_fir": True,
                    "fir_no": fir_no,
                    "fir_date": fir_date,
                    "fir_sections": fir_sec
                }
        else:
            print("\n   [प्रत्येक फाइल के लिए अलग-अलग FIR विवरण दर्ज करें]:")
            for fp in input_files:
                fn = os.path.basename(fp)
                print(f"\n   📄 शिकायत फाइल: {fn}")
                f_no = input("   👉 इस फाइल का FIR No. दर्ज करें (उदा. 281/2026): ").strip() or "281/2026"
                f_dt = input(f"   👉 FIR की तारीख [Default: {datetime.datetime.now().strftime('%d/%m/%Y')}]: ").strip() or datetime.datetime.now().strftime("%d/%m/%Y")
                f_sc = input("   👉 धाराएं (Sections) [Default: 318(4) BNS]: ").strip() or "318(4) BNS"
                file_fir_map[fp] = {"is_fir": True, "fir_no": f_no, "fir_date": f_dt, "fir_sections": f_sc}
    else:
        for fp in input_files:
            file_fir_map[fp] = {"is_fir": False}

    # ----------------------------------------------------------------------------------
    # Q2: Notice Numbering Policy & Notice Date
    # ----------------------------------------------------------------------------------
    print("\n" + "─" * 90)
    print("📌 [सवाल 2/4] नोटिस नंबरिंग नीति एवं नोटिस की तारीख (Notice Number & Date Policy):")
    today_str = datetime.datetime.now().strftime("%d/%m/%Y")
    print(f"   A) नोटिस पर कौन सी तारीख अंकित करनी है? (DD/MM/YYYY) [Default: {today_str}]")
    ans_date = input("👉 नोटिस की तारीख दर्ज करें: ").strip()
    notice_date = ans_date if ans_date else today_str

    print("\n   B) नोटिस नंबरिंग की नीति (Scheme):")
    print("      [1] हर नोटिस पर अलग-अलग नंबर क्रमवार बढ़ेगा (Notice-wise sequential increment - उदा. 5739, 5740, 5741...) [अनुशंसित]")
    print("      [2] सभी नोटिसों पर एक ही समान नोटिस नंबर रहेगा (Keep the same fixed notice number on all notices)")
    ans_num_mode = input("👉 नंबरिंग का विकल्प चुनें (1/2) [Default: 1]: ").strip() or "1"
    same_notice_number = (ans_num_mode == "2")

    print("\n   C) नोटिस नंबर कहाँ से शुरू करना है? (Starting Notice Number) [Default: 5739]")
    ans_start_no = input("👉 स्टार्टिंग नोटिस नंबर दर्ज करें: ").strip()
    start_notice_no = int(ans_start_no) if (ans_start_no.isdigit() and int(ans_start_no) > 0) else 5739

    # ----------------------------------------------------------------------------------
    # Q3: Investigating Officer (IO) Details & Signature Instructions
    # ----------------------------------------------------------------------------------
    print("\n" + "─" * 90)
    print("📌 [सवाल 3/4] जांच अधिकारी (IO) का विवरण एवं डिजिटल हस्ताक्षर (IO Name, Mobile, Email & Signature):")
    default_io = agent.config.get("default_investigating_officer", {})
    d_name = default_io.get("name", "SI RENU")
    d_rank = default_io.get("rank", "SUB INSPECTOR")
    d_mob = default_io.get("mobile", "9899959840")
    d_email = agent.config.get("station", {}).get("email", "shocyber.north@delhipolice.gov.in")

    print(f"   A) IO का नाम (Investigating Officer Name) [Default: {d_name}]")
    ans_io_name = input("👉 IO का नाम दर्ज करें: ").strip() or d_name

    print(f"\n   B) IO का पद / रैंक (HC / ASI / SI / Insp.) [Default: {d_rank}]")
    ans_io_rank = input("👉 IO की रैंक दर्ज करें: ").strip() or d_rank

    print(f"\n   C) IO का मोबाइल नंबर (Mobile Number) [Default: {d_mob}]")
    ans_io_mob = input("👉 IO का मोबाइल नंबर दर्ज करें: ").strip() or d_mob

    print(f"\n   D) IO की आधिकारिक ईमेल आईडी (Official Email) [Default: {d_email}]")
    ans_io_email = input("👉 IO की ईमेल आईडी दर्ज करें: ").strip() or d_email

    print("\n   ✍️ [हस्ताक्षर निर्देश / Signature Notice]:")
    print(f"   • यदि IO के डिजिटल हस्ताक्षर की PNG इमेज है, तो उसे 'assets/signatures' या 'assets' फोल्डर में")
    print(f"     IO के नाम से (उदा. assets/signatures/{ans_io_name.lower().replace(' ', '_')}_sign.png) रख सकते हैं।")
    print("   • यदि हस्ताक्षर इमेज नहीं मिलती है, तो नोटिस में हस्ताक्षर की जगह खाली (Unsigned) छोड़ दी जाएगी")
    print("     ताकि आप प्रिंट निकालकर भौतिक मुहर व हस्ताक्षर कर सकें।")

    io_override = {
        "name": ans_io_name,
        "rank": ans_io_rank,
        "belt_no": ans_io_mob,
        "mobile": ans_io_mob,
        "email": ans_io_email
    }

    # ----------------------------------------------------------------------------------
    # Q4: Automated Email Dispatch Settings
    # ----------------------------------------------------------------------------------
    print("\n" + "─" * 90)
    print("📌 [सवाल 4/4] स्वचालित ईमेल प्रेषण (Email Dispatch to Delhi Police NIC):")
    print("   क्या सभी केसों के बैंक नोटिस तैयार होने के तुरंत बाद उन्हें ईमेल द्वारा NIC मेल पर भेजना है?")
    print("   [1] हाँ, नोटिस बनते ही 15-15 सेकंड के सुरक्षित अंतराल पर NIC मेल पर फॉरवर्ड करें [Default]")
    print("   [2] नहीं, केवल नोटिस फाइल्स (Word & PDF) और केस डायरी बनाएं (ईमेल बाद में भेजेंगे)")
    print("─" * 90)
    ans_dispatch = input("👉 उत्तर यहाँ दर्ज करें (1/2) [Default: 1]: ").strip() or "1"

    do_email_dispatch = (ans_dispatch != "2")
    nic_email_target = "rajendra.28082016@delhipolice.gov.in"
    cc_list = []

    if do_email_dispatch:
        print(f"\n   A) किस NIC ईमेल आईडी पर नोटिस भेजने हैं? [Default: {nic_email_target}]")
        ans_nic = input("👉 टारगेट NIC ईमेल आईडी दर्ज करें: ").strip()
        if ans_nic:
            nic_email_target = ans_nic

        print("\n   B) क्या किसी अन्य ईमेल आईडी को CC (कार्बन कॉपी) में रखना है? (वैकल्पिक / खाली छोड़ें)")
        ans_cc = input("👉 CC ईमेल आईडी दर्ज करें: ").strip()
        if ans_cc:
            cc_list = [c.strip() for c in ans_cc.replace(";", ",").split(",") if c.strip()]

    # ----------------------------------------------------------------------------------
    # Q5: Automated WhatsApp Dispatch Settings
    # ----------------------------------------------------------------------------------
    print("\n" + "─" * 90)
    print("📌 [सवाल 5/5] स्वचालित व्हाट्सएप प्रेषण (WhatsApp Notice Dispatch via UltraMsg):")
    print("   क्या सभी बैंक नोटिस व्हाट्सएप पर भी PDF अटैचमेंट सहित भेजने हैं?")
    print("   [1] हाँ, UltraMsg द्वारा सीधे व्हाट्सएप पर भेजें (जैसे +91 9818036472 पर) [Default]")
    print("   [2] नहीं, अभी केवल ईमेल और फाइल्स बनाएं")
    print("─" * 90)
    ans_wa = input("👉 उत्तर यहाँ दर्ज करें (1/2) [Default: 1]: ").strip() or "1"

    do_wa_dispatch = (ans_wa != "2")
    wa_phone_target = "919818036472"
    if do_wa_dispatch:
        print(f"\n   A) किस मोबाइल नंबर पर व्हाट्सएप नोटिस भेजने हैं? [Default: {wa_phone_target}]")
        ans_waph = input("👉 व्हाट्सएप मोबाइल नंबर दर्ज करें: ").strip()
        if ans_waph:
            wa_phone_target = ans_waph

    # ----------------------------------------------------------------------------------
    # BATCH EXECUTION CONFIRMATION
    # ----------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("                 बैच प्रोसेसिंग पुष्टि (BATCH EXECUTION CONFIRMATION)")
    print("=" * 90)
    print(f" • कुल शिकायत फाइलें          : {len(input_files)} फाइलें")
    print(f" • संदर्भ प्रकार (Reference)   : {'FIR / e-FIR मोड' if ans_case_type == '2' else 'ACK No. मोड'}")
    print(f" • नोटिस नंबरिंग नीति         : {'हर नोटिस पर अलग नंबर (Sequential)' if not same_notice_number else 'सभी पर समान नंबर (Fixed)'}")
    print(f" • स्टार्टिंग नोटिस नंबर        : Notice No. {start_notice_no} | दिनांक: {notice_date}")
    print(f" • जांच अधिकारी (IO)          : {ans_io_rank} {ans_io_name} (Mob: {ans_io_mob})")
    print(f" • ईमेल प्रेषण (Email Send)   : {'सक्रिय -> ' + nic_email_target if do_email_dispatch else 'निष्क्रिय (Only Files)'}")
    if cc_list:
        print(f" • CC ईमेल                    : {', '.join(cc_list)}")
    print(f" • व्हाट्सएप प्रेषण (WhatsApp) : {'सक्रिय -> +' + wa_phone_target if do_wa_dispatch else 'निष्क्रिय'}")
    print("=" * 90)

    ans_confirm = input("\n👉 क्या बैच प्रोसेसिंग शुरू करें? (Y/N) [Default: Y]: ").strip().lower()
    if ans_confirm in ["n", "no"]:
        print("बैच प्रोसेसिंग रद्द कर दी गई।")
        return

    # ----------------------------------------------------------------------------------
    # BATCH EXECUTION ENGINE
    # ----------------------------------------------------------------------------------
    current_run_notice_no = start_notice_no
    total_case_dirs = []
    case_results = []

    for f_idx, fpath in enumerate(input_files, start=1):
        fname = os.path.basename(fpath)
        print("\n" + "#" * 90)
        print(f" 🚀 [केस {f_idx}/{len(input_files)}] प्रोसेसिंग प्रारंभ: {fname}")
        print("#" * 90)

        fir_info = file_fir_map.get(fpath, {"is_fir": False})

        try:
            ctx = agent.run_case_pipeline(
                case_file_or_target=fpath,
                fir_details=fir_info,
                io_override=io_override,
                start_notice_no=current_run_notice_no,
                notice_date_override=notice_date,
                sign_mode="unsigned"
            )

            case_dir = ctx.get("case_dir", "")
            if not case_dir:
                fir_no = fir_info.get("fir_no")
                if fir_no:
                    clean_fir = re.sub(r'[^a-zA-Z0-9_-]', '_', str(fir_no))
                    cand = os.path.join(agent.output_dir, f"FIR_{clean_fir}")
                    if os.path.exists(cand):
                        case_dir = cand
            total_case_dirs.append(case_dir)
            
            # Count bank notices generated
            pdf_dir = os.path.join(case_dir, "Notice_PDF_Files")
            count_notices = 0
            if os.path.exists(pdf_dir):
                count_notices = len([f for f in os.listdir(pdf_dir) if f.endswith(".pdf")])

            if not same_notice_number:
                current_run_notice_no += count_notices

            case_results.append({
                "file": fname,
                "status": "SUCCESS",
                "notices_count": count_notices,
                "case_dir": case_dir
            })
            print(f"✅ केस {f_idx} सफल! {count_notices} बैंक नोटिस तैयार हुए।")

        except Exception as ex:
            print(f"❌ [केस {f_idx} त्रुटि]: {ex}")
            case_results.append({
                "file": fname,
                "status": "FAILED",
                "notices_count": 0,
                "error": str(ex)
            })

    # ----------------------------------------------------------------------------------
    # BATCH EMAIL DISPATCH PIPELINE
    # ----------------------------------------------------------------------------------
    if do_email_dispatch and EmailDispatchAgent and total_case_dirs:
        print("\n" + "=" * 90)
        print(" 📨 सभी बैच केसों के बैंक नोटिस ईमेल द्वारा NIC मेल पर भेजे जा रहे हैं...")
        print("=" * 90)

        try:
            email_agent = EmailDispatchAgent()
            # Set target & CC
            email_agent.config.setdefault("forwarding_target", {})["nic_email"] = nic_email_target
            email_agent.config.setdefault("forwarding_target", {})["cc_emails"] = cc_list
            email_agent.config["notice_scope"] = "banks_only"

            all_dispatched = []
            for c_dir in total_case_dirs:
                if c_dir and os.path.exists(c_dir):
                    c_name = os.path.basename(c_dir)
                    print(f"\n>>> [Email Agent] केस के बैंक नोटिस भेजे जा रहे हैं: {c_name}...")
                    res = email_agent.dispatch_case_notices(c_dir)
                    all_dispatched.extend(res)

            print("\n" + "=" * 90)
            successful_sends = sum(1 for r in all_dispatched if "SUCCESS" in r.get("status", ""))
            print(f" 🏁 संपूर्ण बैच ईमेल डिस्पैच संपन्न: {successful_sends}/{len(all_dispatched)} बैंक नोटिस भेजे गए!")
            print("=" * 90)

        except Exception as em_err:
            print(f"⚠️ [Email Dispatch Error] {em_err}")

    # ----------------------------------------------------------------------------------
    # BATCH WHATSAPP DISPATCH PIPELINE
    # ----------------------------------------------------------------------------------
    if do_wa_dispatch and WhatsAppDispatchAgent and total_case_dirs:
        print("\n" + "=" * 90)
        print(" 📲 सभी बैच केसों के बैंक नोटिस व्हाट्सएप (UltraMsg) पर भेजे जा रहे हैं...")
        print(f"    टारगेट व्हाट्सएप नंबर: +{wa_phone_target}")
        print("=" * 90)

        try:
            wa_agent = WhatsAppDispatchAgent()
            all_wa_dispatched = []
            for c_idx, c_dir in enumerate(total_case_dirs):
                if c_dir and os.path.exists(c_dir):
                    c_name = os.path.basename(c_dir)
                    print(f"\n>>> [WhatsApp Agent] केस के बैंक नोटिस भेजे जा रहे हैं: {c_name}...")
                    res = wa_agent.dispatch_case_notices(c_dir, phone=wa_phone_target, io_override=io_override)
                    all_wa_dispatched.extend(res)
                    if res and c_idx < len(total_case_dirs) - 1:
                        time.sleep(wa_agent.rate_limit_seconds)

            print("\n" + "=" * 90)
            successful_wa = sum(1 for r in all_wa_dispatched if "SUCCESS" in r.get("status", ""))
            print(f" 🏁 संपूर्ण बैच व्हाट्सएप डिस्पैच संपन्न: {successful_wa}/{len(all_wa_dispatched)} बैंक नोटिस भेजे गए!")
            print("=" * 90)

        except Exception as wa_err:
            print(f"⚠️ [WhatsApp Dispatch Error] {wa_err}")

    # ----------------------------------------------------------------------------------
    # FINAL SUMMARY REPORT
    # ----------------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("                    बैच प्रोसेसिंग संपूर्ण रिपोर्ट (BATCH SUMMARY)")
    print("=" * 90)
    for idx, res in enumerate(case_results, start=1):
        st_icon = "✅" if res["status"] == "SUCCESS" else "❌"
        cnt = res.get("notices_count", 0)
        loc = os.path.basename(res.get("case_dir", "")) or res.get("error", "")
        print(f" {st_icon} [{idx}] {res['file']:<45} | बैंक नोटिस: {cnt:2d} | आउटपुट: {loc}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    run_batch_pipeline()
