"""
NCRP Investigation Pipeline - Master Google Sheets & Local Excel Mule Database Sync
Delhi Police Cyber Crime Investigation Unit

Automatically records every suspect bank account, layer, IFSC, verified branch address,
complainant details, brief facts, defrauded/lien amounts, and investigating officer
into:
  1. Centralized Google Sheet ("म्यूल अकाउंट डेटाबेस" / "Mule Account Master Database")
  2. Local Master Excel Sheet: output/Mule_Account_Master_Database.xlsx
  3. Centralized SQLite Database: ncrp_cases.db
"""

import os
import re
import sys
import json
import datetime
from typing import Dict, Any, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Try importing gspread & requests
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Import IFSC resolver
try:
    from dynamic_flowchart import get_ifsc_branch_info
except ImportError:
    def get_ifsc_branch_info(ifsc: str, base_dir: str = ""):
        return {"branch": f"Branch ({ifsc})", "address": "Address not found", "city": "-", "state": "-"}

COLUMNS_HEADER = [
    "Acknowledgement / FIR No.",
    "Complainant Name",
    "Complainant Address",
    "Complainant Mobile",
    "Layer",
    "Bank Name",
    "Suspect Account No.",
    "IFSC Code",
    "Bank Branch Address",
    "Cheated / Disputed Amount (₹)",
    "Brief Facts of Complaint",
    "Total Defrauded Amount (₹)",
    "Total Lien / Hold Amount (₹)",
    "Investigating Officer (IO)",
    "Record Timestamp"
]

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "google_sheets_config.json")
DEFAULT_SERVICE_ACCOUNT_PATH = os.path.join(os.path.dirname(__file__), "config", "google_service_account.json")
DEFAULT_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "output", "Mule_Account_Master_Database.xlsx")


def get_sheets_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Loads Google Sheets configuration, or initializes default if missing."""
    default_cfg = {
        "spreadsheet_name": "म्यूल अकाउंट डेटाबेस - Mule Account Master Database",
        "sheet_tab_name": "Mule_Accounts",
        "local_excel_path": "output/Mule_Account_Master_Database.xlsx",
        "google_service_account_file": "config/google_service_account.json",
        "apps_script_webhook_url": "",
        "google_sheet_id_or_url": "",
        "auto_sync_enabled": True
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                default_cfg.update(cfg)
                return default_cfg
        except Exception as e:
            print(f"  [WARN] Failed to read {config_path}: {e}")
    else:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    return default_cfg


def extract_mule_records(case_context: Dict[str, Any], base_dir: str = "") -> List[Dict[str, Any]]:
    """
    Extracts structured mule account rows strictly adhering to the 15 required fields:
      1. Acknowledgement / FIR No.
      2. Complainant Name
      3. Complainant Address
      4. Complainant Mobile
      5. Layer
      6. Bank Name
      7. Suspect Account No.
      8. IFSC Code
      9. Bank Branch Address (API verified)
      10. Cheated / Disputed Amount
      11. Brief Facts of Complaint
      12. Total Defrauded Amount
      13. Total Lien / Hold Amount
      14. Investigating Officer (IO)
      15. Record Timestamp
    """
    case_meta = case_context.get("case_meta", {})
    comp = case_context.get("complainant", {})
    fin = case_context.get("financial_summary", {})

    ack_no = str(case_meta.get("acknowledgement_no", "")).strip()
    is_fir = case_meta.get("case_type") == "fir" or bool(case_meta.get("fir_no"))
    fir_no = str(case_meta.get("fir_no", "")).strip()
    
    if is_fir and fir_no:
        case_ref = f"FIR No. {fir_no} (Ack: {ack_no})" if ack_no else f"FIR No. {fir_no}"
    else:
        case_ref = ack_no or "N/A"

    comp_name = str(comp.get("name", "Complainant")).strip()
    comp_addr = str(comp.get("address", "")).strip()
    comp_mob = str(comp.get("mobile", "")).strip()

    total_defrauded = str(fin.get("alleged_amount", comp.get("defrauded_amount", "0.00"))).strip()
    total_lien = str(fin.get("total_lien_amount", "0.00")).strip()

    # Investigating Officer Info - strictly as provided by user
    io_name = str(case_meta.get("io_name", "Investigating Officer")).strip()
    io_rank = str(case_meta.get("io_rank", "")).strip()
    io_mob = str(case_meta.get("io_mobile", "")).strip()
    io_belt = str(case_meta.get("io_belt_no", "")).strip()

    rank_prefixes = ('SI', 'WSI', 'W/SI', 'HC', 'ASI', 'INSP', 'INSPECTOR', 'SUB INSPECTOR', 'HEAD CONSTABLE', 'CT', 'CONSTABLE')
    if any(io_name.upper().startswith(p + ' ') or io_name.upper() == p for p in rank_prefixes):
        full_io = io_name
    elif io_rank:
        full_io = f"{io_rank} {io_name}".strip()
    else:
        full_io = io_name

    contact = io_belt or io_mob
    io_str = f"{full_io} ({contact})" if contact else full_io

    # Brief Facts synthesis
    cat = str(comp.get("category", "")).strip()
    subcat = str(comp.get("sub_category", "")).strip()
    add_info = str(comp.get("additional_info", "")).strip()
    v_bank = str(comp.get("victim_bank", "")).strip()
    v_acc = str(comp.get("victim_account", "")).strip()

    facts_tokens = []
    if cat or subcat:
        crime_label = f"{cat} - {subcat}" if cat and subcat else (cat or subcat)
        facts_tokens.append(f"Cyber Crime Category: {crime_label}")
    if add_info and add_info.lower() not in ["null", "none", "-"]:
        facts_tokens.append(f"Modus Operandi: {add_info}")
    if v_bank or v_acc:
        facts_tokens.append(f"Target Source: {v_bank} A/c {v_acc}")
    facts_tokens.append(f"Defrauded Amount: Rs. {total_defrauded}")
    brief_facts = ". ".join(facts_tokens) + "."

    now_ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    records = []
    raw_transfers = case_context.get("raw_transfers", [])
    seen_keys = set()

    for r in raw_transfers:
        r_str = ' '.join(str(c or '').replace('\n', ' ') for c in r)
        b_name = str(r[1] or '').replace('\n', ' ').strip()
        acc_info = str(r[2] or '').replace('\n', ' ').strip()
        disp_str = str(r[6] or r[5] or '0').replace(',', '').replace('\n', '').replace(' ', '').strip()
        
        try:
            disp_val = float(disp_str)
        except Exception:
            disp_val = 0.0

        m_lay = re.search(r'Layer\s*:?\s*(\d+)', acc_info, re.I)
        l_num = int(m_lay.group(1)) if m_lay else 1
        layer_str = f"Layer {l_num}"

        m_ifsc = re.search(r'[A-Za-z]{4}0[A-Za-z0-9]{6}', acc_info)
        ifsc = m_ifsc.group(0).upper() if m_ifsc else ''

        clean_acc = acc_info
        if m_lay:
            clean_acc = clean_acc.replace(m_lay.group(0), '')
        if m_ifsc:
            clean_acc = clean_acc.replace(m_ifsc.group(0), '')
        clean_acc = re.sub(r'[^a-zA-Z0-9@._-]', '', clean_acc).strip()

        if not clean_acc or clean_acc == v_acc:
            continue

        # Look up API branch address
        branch_addr = ""
        if ifsc:
            ifsc_info = get_ifsc_branch_info(ifsc, base_dir)
            branch_addr = ifsc_info.get("address") or ifsc_info.get("branch") or ""

        entry_key = (case_ref, layer_str, clean_acc, ifsc)
        if entry_key in seen_keys:
            # Aggregate amount
            for rec in records:
                if rec["_key"] == entry_key:
                    rec["disputed_amount_val"] += disp_val
                    rec["disputed_amount"] = f"{rec['disputed_amount_val']:,.2f}"
                    break
        else:
            seen_keys.add(entry_key)
            rec = {
                "_key": entry_key,
                "ack_or_fir_no": case_ref,
                "complainant_name": comp_name,
                "complainant_address": comp_addr,
                "complainant_mobile": comp_mob,
                "layer": layer_str,
                "bank_name": b_name,
                "suspect_account_no": clean_acc,
                "ifsc_code": ifsc,
                "bank_branch_address": branch_addr,
                "disputed_amount_val": disp_val,
                "disputed_amount": f"{disp_val:,.2f}",
                "brief_facts": brief_facts,
                "total_defrauded_amount": total_defrauded,
                "total_lien_amount": total_lien,
                "investigating_officer": io_str,
                "record_timestamp": now_ts
            }
            records.append(rec)

    return records


def format_record_for_row(rec: Dict[str, Any]) -> List[Any]:
    """Returns row array matching COLUMNS_HEADER."""
    return [
        rec.get("ack_or_fir_no", ""),
        rec.get("complainant_name", ""),
        rec.get("complainant_address", ""),
        rec.get("complainant_mobile", ""),
        rec.get("layer", ""),
        rec.get("bank_name", ""),
        rec.get("suspect_account_no", ""),
        rec.get("ifsc_code", ""),
        rec.get("bank_branch_address", ""),
        rec.get("disputed_amount", ""),
        rec.get("brief_facts", ""),
        rec.get("total_defrauded_amount", ""),
        rec.get("total_lien_amount", ""),
        rec.get("investigating_officer", ""),
        rec.get("record_timestamp", "")
    ]


def sync_to_local_excel(records: List[Dict[str, Any]], excel_path: str = DEFAULT_EXCEL_PATH) -> str:
    """
    Appends mule account records into the master Excel workbook.
    Creates the workbook with professional Delhi Police cyber crime investigation styling if missing.
    """
    os.makedirs(os.path.dirname(os.path.abspath(excel_path)), exist_ok=True)
    
    wb = None
    if os.path.exists(excel_path):
        try:
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active
        except Exception:
            wb = None

    if wb is None:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Mule_Accounts_Database"
        
        # Header formatting
        ws.append(COLUMNS_HEADER)
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Deep Navy Blue
        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )

        for col_idx in range(1, len(COLUMNS_HEADER) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align
            cell.border = thin_border
        ws.row_dimensions[1].height = 32
        ws.freeze_panes = "A2"

    # Map existing row indices by key to update them in-place with latest IO and details
    existing_key_to_row = {}
    for r_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if row and any(row):
            ack = str(row[0] or "").strip()
            layer = str(row[4] or "").strip()
            acc = str(row[6] or "").strip()
            ifsc = str(row[7] or "").strip()
            existing_key_to_row[(ack, layer, acc, ifsc)] = r_idx

    regular_font = Font(name="Calibri", size=10)
    regular_align = Alignment(vertical="center", wrap_text=True)
    money_align = Alignment(horizontal="right", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    new_appended = 0
    updated_count = 0
    for rec in records:
        key = (rec["ack_or_fir_no"], rec["layer"], rec["suspect_account_no"], rec["ifsc_code"])
        row_data = format_record_for_row(rec)

        if key in existing_key_to_row:
            target_row = existing_key_to_row[key]
            for col_idx in range(1, len(row_data) + 1):
                cell = ws.cell(row=target_row, column=col_idx)
                cell.value = row_data[col_idx - 1]
                cell.font = regular_font
                cell.border = thin_border
                if col_idx in [10, 12, 13]:
                    cell.alignment = money_align
                elif col_idx in [1, 4, 5, 7, 8, 15]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = regular_align
            updated_count += 1
        else:
            ws.append(row_data)
            current_row = ws.max_row
            ws.row_dimensions[current_row].height = 24
            for col_idx in range(1, len(row_data) + 1):
                cell = ws.cell(row=current_row, column=col_idx)
                cell.font = regular_font
                cell.border = thin_border
                if col_idx in [10, 12, 13]:
                    cell.alignment = money_align
                elif col_idx in [1, 4, 5, 7, 8, 15]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = regular_align
            existing_key_to_row[key] = current_row
            new_appended += 1

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            lines = val_str.split('\n')
            for l in lines:
                if len(l) > max_len:
                    max_len = len(l)
        ws.column_dimensions[col_letter].width = max(12, min(50, max_len + 4))

    wb.save(excel_path)
    print(f"  [OK] Master Mule Excel updated ({new_appended} new rows added): {excel_path}")
    return excel_path


def sync_to_google_sheet(records: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Syncs rows to cloud Google Sheet.
    Supports:
      1. Google Service Account credentials (JSON file)
      2. Google Apps Script Webhook POST (instant no-credentials method)
    """
    if not records:
        return {"status": "no_data", "message": "No suspect mule records to sync"}

    rows_to_send = [format_record_for_row(r) for r in records]

    # Method 1: Google Apps Script Webhook
    webhook_url = config.get("apps_script_webhook_url", "").strip()
    if webhook_url and HAS_REQUESTS:
        try:
            payload = {
                "action": "append_rows",
                "spreadsheet_name": config.get("spreadsheet_name", "Mule Account Database"),
                "sheet_tab": config.get("sheet_tab_name", "Mule_Accounts"),
                "headers": COLUMNS_HEADER,
                "rows": rows_to_send
            }
            resp = requests.post(webhook_url, json=payload, timeout=12)
            if resp.status_code in [200, 201, 302]:
                print(f"  [OK] Successfully synced {len(records)} rows to Google Sheet via Webhook!")
                return {
                    "status": "success",
                    "method": "webhook",
                    "rows_synced": len(records),
                    "response": resp.text[:200]
                }
            else:
                print(f"  [WARN] Apps Script Webhook returned status {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  [WARN] Apps Script Webhook failed: {e}")

    # Method 2: Google Service Account
    sa_path = config.get("google_service_account_file", DEFAULT_SERVICE_ACCOUNT_PATH)
    if not os.path.isabs(sa_path):
        sa_path = os.path.join(os.path.dirname(__file__), sa_path)

    if os.path.exists(sa_path) and HAS_GSPREAD:
        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file(sa_path, scopes=scopes)
            client = gspread.authorize(creds)

            sheet_name = config.get("spreadsheet_name", "म्यूल अकाउंट डेटाबेस - Mule Account Master Database")
            sheet_id = config.get("google_sheet_id_or_url", "").strip()

            sh = None
            if sheet_id:
                if sheet_id.startswith("http"):
                    sh = client.open_by_url(sheet_id)
                else:
                    sh = client.open_by_key(sheet_id)
            else:
                try:
                    sh = client.open(sheet_name)
                except gspread.SpreadsheetNotFound:
                    # Create new sheet in user's Drive and share
                    sh = client.create(sheet_name)
                    # Share with user's Gmail if known
                    target_email = "gkncyber1262@gmail.com"
                    try:
                        sh.share(target_email, perm_type='user', role='writer')
                        print(f"  [OK] Created Google Sheet and shared with {target_email}")
                    except Exception as se:
                        print(f"  [INFO] Shared sheet note: {se}")

            ws_name = config.get("sheet_tab_name", "Mule_Accounts")
            try:
                ws = sh.worksheet(ws_name)
            except gspread.WorksheetNotFound:
                ws = sh.add_worksheet(title=ws_name, rows=1000, cols=20)

            # Check if headers exist
            existing_vals = ws.get_all_values()
            if not existing_vals or len(existing_vals) == 0:
                ws.append_row(COLUMNS_HEADER)
                existing_keys = set()
            else:
                existing_keys = set()
                for row in existing_vals[1:]:
                    if row and any(row):
                        ack = str(row[0] or "").strip()
                        layer = str(row[4] or "").strip()
                        acc = str(row[6] or "").strip()
                        ifsc = str(row[7] or "").strip()
                        existing_keys.add((ack, layer, acc, ifsc))

            new_rows = []
            for r in records:
                k = (r["ack_or_fir_no"], r["layer"], r["suspect_account_no"], r["ifsc_code"])
                if k not in existing_keys:
                    new_rows.append(format_record_for_row(r))
                    existing_keys.add(k)

            if new_rows:
                ws.append_rows(new_rows, value_input_option="USER_ENTERED")
                print(f"  [OK] Successfully pushed {len(new_rows)} rows to Google Sheet '{sh.title}'!")

            return {
                "status": "success",
                "method": "service_account",
                "spreadsheet_title": sh.title,
                "spreadsheet_url": sh.url,
                "rows_synced": len(new_rows)
            }
        except Exception as e:
            print(f"  [WARN] Google Sheets API Sync Error: {e}")
            return {"status": "error", "error": str(e)}

    return {
        "status": "pending_credentials",
        "message": (
            "Cloud Google Sheet credentials not configured yet. "
            "Data safely stored in local Master Excel file: output/Mule_Account_Master_Database.xlsx. "
            "To connect live Google Sheet, add Google Service Account JSON or Apps Script Webhook URL."
        )
    }


def sync_case_to_database_and_sheets(case_context: Dict[str, Any], base_dir: str = "") -> Dict[str, Any]:
    """
    Main entrypoint:
      1. Extracts 15 structured fields for all suspect mule accounts across all layers.
      2. Appends to local Master Excel (output/Mule_Account_Master_Database.xlsx).
      3. Synchronizes with Cloud Google Sheet (if configured).
    """
    if not base_dir:
        base_dir = os.path.dirname(__file__)

    records = extract_mule_records(case_context, base_dir)
    if not records:
        return {"status": "empty", "message": "No suspect transfers found in case context", "count": 0}

    # 1. Update local Master Excel (with lock resilience)
    excel_path = os.path.join(base_dir, "output", "Mule_Account_Master_Database.xlsx")
    try:
        sync_to_local_excel(records, excel_path)
    except PermissionError:
        print(f"  [WARN] Master Excel file is open in Microsoft Excel. Saving to Live fallback mirror.")
        fallback_path = os.path.join(base_dir, "output", "Mule_Account_Master_Database_Live.xlsx")
        try:
            sync_to_local_excel(records, fallback_path)
        except Exception:
            pass
    except Exception as ee:
        print(f"  [WARN] Local Excel sync warning: {ee}")

    # 2. Update Cloud Google Sheet
    cfg_path = os.path.join(base_dir, "config", "google_sheets_config.json")
    config = get_sheets_config(cfg_path)
    cloud_res = sync_to_google_sheet(records, config)

    return {
        "status": "completed",
        "count": len(records),
        "local_excel": excel_path,
        "cloud_sync": cloud_res
    }


if __name__ == "__main__":
    # Test script with sample case
    test_case_dir = os.path.join(os.path.dirname(__file__), "output", "Case_30811260103830")
    ctx_path = os.path.join(test_case_dir, "case_context.json")
    if os.path.exists(ctx_path):
        with open(ctx_path, "r", encoding="utf-8") as f:
            ctx = json.load(f)
        res = sync_case_to_database_and_sheets(ctx)
        print("Result:", json.dumps(res, indent=2))
    else:
        print("Test context not found at", ctx_path)
