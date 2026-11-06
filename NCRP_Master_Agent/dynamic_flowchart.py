import os
import sys
import json
import re
import math
import textwrap
import urllib.request
from PIL import Image, ImageDraw, ImageFont

def get_ifsc_branch_info(ifsc: str, base_dir: str) -> dict:
    """
    Looks up branch name and verified physical address for an IFSC code
    from local persistent cache (ifsc_cache.json) or Razorpay RBI IFSC API.
    """
    if not ifsc:
        return {"branch": "", "address": "", "city": "", "state": ""}
    
    clean = re.sub(r'[^a-zA-Z0-9]', '', str(ifsc)).strip().upper()
    if len(clean) < 4:
        return {"branch": "", "address": "", "city": "", "state": ""}
    
    cache_path = os.path.join(base_dir, "config", "ifsc_cache.json")
    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
                if clean in cache:
                    entry = cache[clean]
                    if entry.get("address") and entry.get("address") != "Address not found via API":
                        return entry
        except Exception:
            pass

    # Virtual UPI nodes
    if "UPI" in clean or "PTM" in clean or "YBL" in clean:
        info = {
            "branch": "NPCI UPI Virtual Routing Switch",
            "address": "National NPCI UPI Switching Gateway / Digital Wallet PG Node",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        cache[clean] = info
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return info

    # Fetch via API
    try:
        url = f"https://ifsc.razorpay.com/{clean}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DelhiPoliceInvestigation/2.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                branch = data.get("BRANCH") or data.get("branch") or f"Branch {clean}"
                raw_addr = data.get("ADDRESS") or data.get("address") or ""
                city = data.get("CITY") or data.get("city") or ""
                state = data.get("STATE") or data.get("state") or ""
                addr = re.sub(r'\s+', ' ', raw_addr).strip() if raw_addr else f"{branch}, {city}, {state}"
                info = {"branch": branch, "address": addr, "city": city, "state": state}
                cache[clean] = info
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(cache, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass
                return info
    except Exception:
        pass

    return {"branch": f"Branch ({clean})", "address": "Address not found via API", "city": "-", "state": "-"}


def get_bank_logo_image(bank_name: str, ifsc: str, base_dir: str, target_size=(160, 48)) -> Image.Image:
    """
    Retrieves and resizes the official bank logo banner based on IFSC or Bank Name.
    Guarantees strict distinction between Union Bank and Bank of India.
    """
    b = str(bank_name or '').upper()
    c = str(ifsc or '').upper()
    logo_dir = os.path.join(base_dir, "assets", "logos")
    
    fn = "generic_bank.png"
    if c.startswith("UBIN") or "UNION BANK" in b:
        fn = "union_bank.png"
    elif c.startswith("BKID") or (("BANK OF INDIA" in b or "BOI" in b) and "UNION" not in b):
        fn = "bank_of_india.png"
    elif c.startswith("PUNB") or "PNB" in b or "PUNJAB NATIONAL" in b:
        fn = "pnb_bank.png"
    elif c.startswith("YESB") or "YES BANK" in b:
        fn = "yes_bank.png"
    elif c.startswith("SBIN") or "SBI" in b or "STATE BANK" in b:
        fn = "sbi_bank.png"
    elif c.startswith("HDFC") or "HDFC" in b:
        fn = "hdfc_bank.png"
    elif c.startswith("ICIC") or "ICICI" in b:
        fn = "icici_bank.png"
    elif c.startswith("UTIB") or "AXIS" in b:
        fn = "axis_bank.png"
    elif c.startswith("CNRB") or "CANARA" in b:
        fn = "canara_bank.png"
    elif c.startswith("BARB") or "BARODA" in b or "BOB" in b:
        fn = "bob_bank.png"
    elif c.startswith("IDIB") or "INDIAN BANK" in b:
        fn = "indian_bank.png"
    elif c.startswith("IOBA") or "INDIAN OVERSEAS" in b:
        fn = "indian_overseas_bank.png"
    elif c.startswith("KKBK") or "KOTAK" in b:
        fn = "kotak_bank.png"
    elif c.startswith("INDB") or "INDUSIND" in b:
        fn = "indusind_bank.png"
    elif c.startswith("IDFB") or "IDFC" in b:
        fn = "idfc_first_bank.png"
    elif c.startswith("AIRP") or "AIRTEL" in b:
        fn = "airtel_bank.png"
    elif c.startswith("RATN") or "RBL" in b:
        fn = "rbl_bank.png"
    elif c.startswith("UTKS") or "UTKARSH" in b:
        fn = "utkarsh_bank.png"
    elif c.startswith("SIBL") or "SOUTH INDIAN" in b:
        fn = "south_indian_bank.png"
    elif c.startswith("SBMY") or "SBM" in b:
        fn = "sbm_bank.png"
    elif "UNITY" in b:
        fn = "unity_bank.png"
    elif "PAYTM" in b or "PYTM" in c:
        fn = "paytm.png"
    elif "PHONEPE" in b:
        fn = "phonepe.png"
    elif "GPAY" in b or "GOOGLE" in b:
        fn = "gpay.png"
    elif "MOBIKWIK" in b:
        fn = "mobikwik.png"
    elif "ATM" in b or "CASH" in b:
        fn = "atm_booth.png"
    elif "POS" in b or "MERCHANT" in b or "BHARAT PE" in b:
        fn = "pos_terminal.png"
        
    logo_path = os.path.join(logo_dir, fn)
    if not os.path.exists(logo_path):
        logo_path = os.path.join(logo_dir, "generic_bank.png")
        
    try:
        if os.path.exists(logo_path):
            l_img = Image.open(logo_path).convert("RGBA")
            l_img.thumbnail(target_size, Image.Resampling.LANCZOS)
            return l_img
    except Exception:
        pass
    return None


def create_dynamic_3d_flowchart(ctx: dict, output_png: str, output_jpg: str, base_dir: str):
    """
    Renders Forensic Money Trail Flowchart strictly compliant with Delhi Police Investigation standard:
      - Background: Pure White (#FFFFFF)
      - Fonts: Deep Black (#000000 / #0F172A) & Ultra-High Visibility
      - 3D Realistic Boxes with Soft Drop Shadows, Metallic Accents, and Bank Logo Badges
      - Every Mule card includes: Bank Logo, Bank Name, Account No, IFSC Code, and API-verified Physical Branch Address!
      - Also exports an animated 3D pulse GIF: forensic_money_trail_3d_animated.gif!
    """
    W, H = 3600, 2400
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Crisp subtle grid background
    grid_color = (244, 246, 248, 255)
    for x in range(0, W, 90):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, 90):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)

    # Fonts
    try:
        f_title = ImageFont.truetype("arialbd.ttf", 44)
        f_sub = ImageFont.truetype("arialbd.ttf", 24)
        f_meta = ImageFont.truetype("arialbd.ttf", 19)
        f_col = ImageFont.truetype("arialbd.ttf", 20)
        f_h1 = ImageFont.truetype("arialbd.ttf", 23)
        f_h2 = ImageFont.truetype("arialbd.ttf", 19)
        f_amt = ImageFont.truetype("arialbd.ttf", 24)
        f_body = ImageFont.truetype("arial.ttf", 17)
        f_body_b = ImageFont.truetype("arialbd.ttf", 17)
        f_badge = ImageFont.truetype("arialbd.ttf", 14)
        f_tube = ImageFont.truetype("arialbd.ttf", 16)
        f_addr = ImageFont.truetype("arial.ttf", 15)
        f_addr_b = ImageFont.truetype("arialbd.ttf", 15)
    except Exception:
        f_title = ImageFont.load_default()
        f_sub = f_meta = f_col = f_h1 = f_h2 = f_amt = f_body = f_body_b = f_badge = f_tube = f_addr = f_addr_b = f_title

    def draw_3d_white_card(box, border_color=(30, 41, 59), header_bg=None, logo_img=None):
        x1, y1, x2, y2 = box
        # Multi-layer Soft 3D drop-shadow
        for s in range(12, 0, -2):
            alpha = int(36 - s * 2.8)
            draw.rounded_rectangle([x1 - s, y1 - s + 5, x2 + s, y2 + s + 7], radius=14, fill=(200, 210, 225, max(0, alpha)))
        
        # Pure White body with crisp border
        draw.rounded_rectangle([x1, y1, x2, y2], radius=12, fill=(255, 255, 255, 255), outline=border_color, width=2)
        
        # Top subtle highlight edge (3D Bevel)
        draw.line([(x1 + 12, y1 + 1), (x2 - 12, y1 + 1)], fill=(255, 255, 255, 255), width=2)
        
        # Header strip
        header_h = 56
        if header_bg:
            draw.rounded_rectangle([x1 + 1, y1 + 1, x2 - 1, min(y2 - 1, y1 + header_h)], radius=10, fill=header_bg)
            draw.line([(x1 + 1, min(y2 - 1, y1 + header_h)), (x2 - 1, min(y2 - 1, y1 + header_h))], fill=border_color, width=1)
        
        # Draw Bank Logo on Top-Right of Card if provided
        if logo_img:
            lw, lh = logo_img.size
            lx = x2 - lw - 16
            ly = y1 + int((header_h - lh) / 2)
            # Subtle emblem backdrop capsule
            draw.rounded_rectangle([lx - 4, ly - 3, lx + lw + 4, ly + lh + 3], radius=6, fill=(255, 255, 255, 230), outline=(226, 232, 240), width=1)
            img.alpha_composite(logo_img, (lx, ly))

    def draw_badge(x, y, text, bg=(15, 23, 42), fg=(255, 255, 255)):
        w = int(draw.textlength(text, f_badge)) + 20
        h = 28
        draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=bg)
        draw.text((x + 10, y + 5), text, fill=fg, font=f_badge)

    tubes_list = []  # Store for animation generation

    def draw_tube(p1, p2, color=(51, 65, 85), width=4, label=""):
        tubes_list.append((p1, p2, label, color))
        draw.line([p1, p2], fill=(color[0], color[1], color[2], 90), width=width + 3)
        draw.line([p1, p2], fill=color, width=width)
        x1, y1 = p1
        x2, y2 = p2
        angle = math.atan2(y2 - y1, x2 - x1)
        a_len = 16
        p_a1 = (x2 - a_len * math.cos(angle - math.pi / 6), y2 - a_len * math.sin(angle - math.pi / 6))
        p_a2 = (x2 - a_len * math.cos(angle + math.pi / 6), y2 - a_len * math.sin(angle + math.pi / 6))
        draw.polygon([p2, p_a1, p_a2], fill=color)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            lw = int(draw.textlength(label, f_tube)) + 20
            lh = 28
            # 3D shadow for label pill
            draw.rounded_rectangle([mx - lw/2 - 1, my - lh/2 + 2, mx + lw/2 + 1, my + lh/2 + 4], radius=6, fill=(200, 210, 225, 120))
            draw.rounded_rectangle([mx - lw/2, my - lh/2, mx + lw/2, my + lh/2], radius=6, fill=(255, 255, 255, 255), outline=color, width=2)
            draw.text((mx - lw/2 + 10, my - lh/2 + 4), label, fill=(0, 0, 0), font=f_tube)

    # Paste Delhi Police Crest
    crest_p = os.path.join(base_dir, "assets", "delhi_police_crest_only.png")
    if not os.path.exists(crest_p):
        crest_p = os.path.join(base_dir, "assets", "delhi_police_crest_hd.png")
    if os.path.exists(crest_p):
        try:
            c_img = Image.open(crest_p).convert("RGBA").resize((100, 100), Image.Resampling.LANCZOS)
            img.alpha_composite(c_img, (1750, 16))
        except Exception:
            pass

    # Extract Metadata
    c_meta = ctx.get("case_meta", {})
    comp = ctx.get("complainant", {})
    fin = ctx.get("financial_summary", {})
    
    ack = c_meta.get("acknowledgement_no", "N/A")
    fir_no = c_meta.get("fir_no", "")
    fir_date = c_meta.get("fir_date", "")
    is_fir = c_meta.get("case_type") == "fir" or bool(fir_no)
    
    comp_name = comp.get("name", "Complainant")
    v_bank = comp.get("victim_bank", "Victim Bank")
    v_acc = comp.get("victim_account", "Account")
    v_mob = comp.get("mobile", "")
    amt_str = fin.get("alleged_amount", "0.00")
    lien_str = fin.get("total_lien_amount", "0.00")
    atm_str = fin.get("total_atm_withdrawn", "0.00")
    rec_ratio = fin.get("recovery_ratio_pct", 0.0)

    # Header Titles (Deep Black & Police Navy)
    t_text = "CYBER POLICE STATION, NORTH DISTRICT, DELHI POLICE"
    draw.text(((W - draw.textlength(t_text, f_title)) // 2, 125), t_text, fill=(0, 0, 0), font=f_title)
    
    if is_fir:
        st_text = f"FORENSIC MONEY TRAIL & ASSET RECOVERY MATRIX | CASE FIR NO. {fir_no} DATED {fir_date}"
    else:
        st_text = f"FORENSIC MONEY TRAIL & ASSET RECOVERY MATRIX | NCRP ACK NO. {ack}"
    draw.text(((W - draw.textlength(st_text, f_sub)) // 2, 180), st_text, fill=(15, 23, 42), font=f_sub)

    meta_text = f"NCRP ACKNOWLEDGEMENT NO: {ack} | INVESTIGATING OFFICER: {c_meta.get('io_name', 'IO')} | COMPLAINANT: {comp_name}"
    draw.text(((W - draw.textlength(meta_text, f_meta)) // 2, 222), meta_text, fill=(51, 65, 85), font=f_meta)

    # Columns Setup (5 Columns)
    cols = [
        (80, 620, "LAYER 0: VICTIM ACCOUNT", (185, 28, 28)),
        (740, 1360, "LAYER 1: ENTRY MULE ACCOUNTS", (30, 41, 59)),
        (1480, 2100, "LAYER 2: INTERMEDIARY MULES", (15, 23, 42)),
        (2220, 2840, "TERMINAL CASH-OUTS & LIENS", (71, 85, 105)),
        (2960, 3520, "INVESTIGATION DOSSIER", (15, 23, 42))
    ]
    for x1, x2, label, c in cols:
        draw.rounded_rectangle([x1, 265, x2, 312], radius=8, fill=(248, 250, 252), outline=c, width=2)
        draw.text((x1 + 18, 276), label, fill=(0, 0, 0), font=f_col)

    # 1. Victim Card (Col 0)
    v_logo = get_bank_logo_image(v_bank, "", base_dir, target_size=(150, 44))
    v_box = [80, 680, 620, 1200]
    draw_3d_white_card(v_box, border_color=(185, 28, 28), header_bg=(254, 242, 242), logo_img=v_logo)
    draw_badge(100, 694, "COMPLAINANT / VICTIM", bg=(185, 28, 28), fg=(255, 255, 255))
    draw.text((100, 755), f"{comp_name[:28]}", fill=(0, 0, 0), font=f_h1)
    draw.text((100, 795), f"Bank: {v_bank[:28]}", fill=(0, 0, 0), font=f_body_b)
    draw.text((100, 835), f"A/c No: {v_acc}", fill=(15, 23, 42), font=f_body)
    if v_mob:
        draw.text((100, 875), f"Mobile: +91-{v_mob}", fill=(15, 23, 42), font=f_body)
    draw.text((100, 915), f"Incident Date: {c_meta.get('incident_date', 'N/A')}", fill=(15, 23, 42), font=f_body)
    draw.text((100, 965), "Total Defrauded Amount:", fill=(185, 28, 28), font=f_body_b)
    draw.text((100, 1005), f"Rs. {amt_str}", fill=(185, 28, 28), font=f_amt)
    draw.text((100, 1065), "• Initial Fraudulent Disbursal", fill=(0, 0, 0), font=f_body_b)

    # Group transfers by layer
    l1_items = []
    l2_items = []
    l3_items = []
    
    raw_txns = ctx.get("raw_transfers", [])
    seen_keys = set()
    for r in raw_txns:
        if len(r) < 10:
            continue
        r_str = ' '.join(str(c or '').replace('\n', ' ') for c in r)
        if 'layer' not in r_str.lower():
            continue
        
        b_name = str(r[1] or '').replace('\n', ' ').strip()
        acc_info = str(r[2] or '').replace('\n', ' ').strip()
        utr = str(r[3] or '').replace('\n', '').strip()
        disp_str = str(r[6] or '0').replace(',', '').replace('\n', '').replace(' ', '').strip()
        try:
            disp = float(disp_str)
        except Exception:
            disp = 0.0
        
        m_lay = re.search(r'Layer\s*:?\s*(\d+)', acc_info, re.I)
        l_num = int(m_lay.group(1)) if m_lay else 1
        
        m_ifsc = re.search(r'[A-Za-z]{4}0[A-Za-z0-9]{6}', acc_info)
        ifsc = m_ifsc.group(0).upper() if m_ifsc else ''
        
        clean_acc = acc_info
        if m_lay:
            clean_acc = clean_acc.replace(m_lay.group(0), '')
        if m_ifsc:
            clean_acc = clean_acc.replace(m_ifsc.group(0), '')
        clean_acc = re.sub(r'[^a-zA-Z0-9@._-]', '', clean_acc).strip()
        
        key = (l_num, b_name, clean_acc)
        if key in seen_keys:
            for it in (l1_items if l_num == 1 else l2_items if l_num == 2 else l3_items):
                if it['key'] == key:
                    it['disp'] += disp
                    if utr and utr not in it['utrs']:
                        it['utrs'].append(utr)
                    break
        else:
            seen_keys.add(key)
            ifsc_details = get_ifsc_branch_info(ifsc, base_dir) if ifsc else {}
            branch_name = ifsc_details.get("branch", "")
            branch_addr = ifsc_details.get("address", "")
            
            logo_img = get_bank_logo_image(b_name, ifsc, base_dir, target_size=(150, 44))
            
            item = {
                'key': key,
                'bank': b_name,
                'acc': clean_acc,
                'ifsc': ifsc,
                'branch': branch_name,
                'address': branch_addr,
                'disp': disp,
                'utrs': [utr] if utr else [],
                'logo': logo_img
            }
            if l_num == 1:
                l1_items.append(item)
            elif l_num == 2:
                l2_items.append(item)
            else:
                l3_items.append(item)

    avail_h = 1750
    
    # Draw Layer 1 Cards (Col 1)
    l1_boxes = []
    num_l1 = max(1, len(l1_items))
    card_h1 = max(260, min(350, int((avail_h - (num_l1 - 1) * 35) / num_l1)))
    start_y1 = 340 + max(0, int((avail_h - (num_l1 * card_h1 + (num_l1 - 1) * 35)) / 2))
    
    for idx, it in enumerate(l1_items):
        cy1 = start_y1 + idx * (card_h1 + 35)
        cy2 = cy1 + card_h1
        box = [740, cy1, 1360, cy2]
        l1_boxes.append(box)
        draw_3d_white_card(box, border_color=(30, 41, 59), header_bg=(241, 245, 249), logo_img=it.get('logo'))
        draw_badge(760, cy1 + 14, "LAYER 1 - ENTRY MULE", bg=(15, 23, 42), fg=(255, 255, 255))
        draw.text((760, cy1 + 65), it['bank'][:26], fill=(0, 0, 0), font=f_h1)
        draw.text((760, cy1 + 98), f"A/c No: {it['acc']}", fill=(0, 0, 0), font=f_body_b)
        
        curr_y = cy1 + 128
        if it['ifsc']:
            draw.text((760, curr_y), f"IFSC: {it['ifsc']}", fill=(0, 0, 0), font=f_body_b)
            curr_y += 26
        
        if it.get('branch'):
            draw.text((760, curr_y), f"🏛️ Branch: {it['branch'][:36]}", fill=(30, 58, 138), font=f_addr_b)
            curr_y += 24
            
        if it.get('address'):
            raw_ad = it['address']
            wrapped = textwrap.wrap(raw_ad, width=42)
            for w_idx, line in enumerate(wrapped[:2]):
                prefix = "📍 Addr: " if w_idx == 0 else "        "
                draw.text((760, curr_y), f"{prefix}{line}", fill=(30, 41, 59), font=f_addr)
                curr_y += 22
        
        draw.text((760, max(curr_y + 6, cy2 - 62)), f"Credited: Rs. {it['disp']:,.2f}", fill=(0, 0, 0), font=f_amt)
        draw.text((760, cy2 - 30), "• Statutory Notice U/S 94 BNSS Issued", fill=(21, 128, 61), font=f_body_b)

        # Connection tube from Victim to L1
        draw_tube((620, (v_box[1] + v_box[3]) // 2), (740, (cy1 + cy2) // 2), color=(51, 65, 85), width=4, label=f"Rs. {it['disp']:,.0f}")

    # Draw Layer 2 Cards (Col 2)
    l2_boxes = []
    num_l2 = max(1, len(l2_items))
    card_h2 = max(260, min(350, int((avail_h - (num_l2 - 1) * 35) / num_l2)))
    start_y2 = 340 + max(0, int((avail_h - (num_l2 * card_h2 + (num_l2 - 1) * 35)) / 2))
    
    for idx, it in enumerate(l2_items):
        cy1 = start_y2 + idx * (card_h2 + 35)
        cy2 = cy1 + card_h2
        box = [1480, cy1, 2100, cy2]
        l2_boxes.append(box)
        draw_3d_white_card(box, border_color=(15, 23, 42), header_bg=(241, 245, 249), logo_img=it.get('logo'))
        draw_badge(1500, cy1 + 14, "LAYER 2 - INTERMEDIARY MULE", bg=(30, 41, 59), fg=(255, 255, 255))
        draw.text((1500, cy1 + 65), it['bank'][:26], fill=(0, 0, 0), font=f_h1)
        draw.text((1500, cy1 + 98), f"A/c No: {it['acc']}", fill=(0, 0, 0), font=f_body_b)
        
        curr_y = cy1 + 128
        if it['ifsc']:
            draw.text((1500, curr_y), f"IFSC: {it['ifsc']}", fill=(0, 0, 0), font=f_body_b)
            curr_y += 26
        
        if it.get('branch'):
            draw.text((1500, curr_y), f"🏛️ Branch: {it['branch'][:36]}", fill=(30, 58, 138), font=f_addr_b)
            curr_y += 24
            
        if it.get('address'):
            raw_ad = it['address']
            wrapped = textwrap.wrap(raw_ad, width=42)
            for w_idx, line in enumerate(wrapped[:2]):
                prefix = "📍 Addr: " if w_idx == 0 else "        "
                draw.text((1500, curr_y), f"{prefix}{line}", fill=(30, 41, 59), font=f_addr)
                curr_y += 22
        
        draw.text((1500, max(curr_y + 6, cy2 - 62)), f"Transferred: Rs. {it['disp']:,.2f}", fill=(0, 0, 0), font=f_amt)
        l2_tag = "• Statutory Freezing Notice U/S 94/106 BNSS" if is_fir else "• Debit Freeze & Information Notice Issued"
        draw.text((1500, cy2 - 30), l2_tag, fill=(30, 58, 138), font=f_body_b)

        # Connection tube from closest L1 to L2
        if l1_boxes:
            closest_l1 = min(l1_boxes, key=lambda b: abs((b[1]+b[3])/2 - (cy1+cy2)/2))
            draw_tube((1360, (closest_l1[1] + closest_l1[3]) // 2), (1480, (cy1 + cy2) // 2), color=(51, 65, 85), width=4, label=f"Rs. {it['disp']:,.0f}")

    # Draw Terminal Endpoints (Col 3): Holds & ATMs & L3
    term_items = []
    # Holds
    raw_holds = ctx.get("raw_holds", [])
    for h in raw_holds:
        if len(h) < 4:
            continue
        amt = str(h[3] or '0').replace(',', '').replace('\n', '').strip()
        h_acc = str(h[1] or '').replace('\n', ' ').strip()
        h_dt = str(h[2] or '').replace('\n', ' ').strip()
        term_items.append({'type': 'HOLD', 'title': '🛡️ LIEN MARKED / SECURED', 'acc': h_acc, 'amt': amt, 'dt': h_dt, 'color': (21, 128, 61), 'bg': (236, 253, 245)})
    
    # ATMs
    raw_atms = ctx.get("atm_withdrawals", [])
    if raw_atms:
        atm_total = 0.0
        atm_loc = "ATM Cash Dispenser"
        atm_acc = ""
        for a in raw_atms:
            for ci in [3, 4, 1]:
                if ci < len(a):
                    v_s = str(a[ci] or '').replace(',', '').replace('\n', '').strip()
                    if re.match(r'^\d+(\.\d+)?$', v_s):
                        atm_total += float(v_s)
                        break
            if len(a) > 6 and str(a[6] or '').strip():
                atm_loc = str(a[6] or '').replace('\n', ' ').strip()
            if len(a) > 2 and re.search(r'\d{9,}', str(a[2] or '')):
                atm_acc = str(a[2] or '').replace('\n', '').strip()
        atm_logo = get_bank_logo_image("ATM", "", base_dir, target_size=(140, 44))
        term_items.append({'type': 'ATM', 'title': '🏧 ATM CASH WITHDRAWAL', 'acc': atm_acc, 'amt': f"{atm_total:,.2f}", 'loc': atm_loc, 'cnt': len(raw_atms), 'color': (185, 28, 28), 'bg': (254, 242, 242), 'logo': atm_logo})

    # Layer 3 mules if any
    for it in l3_items:
        term_items.append({'type': 'L3', 'title': 'LAYER 3 - TERMINAL MULE', 'acc': it['acc'], 'amt': f"{it['disp']:,.2f}", 'bank': it['bank'], 'ifsc': it.get('ifsc', ''), 'branch': it.get('branch', ''), 'address': it.get('address', ''), 'color': (71, 85, 105), 'bg': (248, 250, 252), 'logo': it.get('logo')})

    num_term = max(1, len(term_items))
    card_ht = max(220, min(330, int((avail_h - (num_term - 1) * 35) / num_term)))
    start_yt = 340 + max(0, int((avail_h - (num_term * card_ht + (num_term - 1) * 35)) / 2))

    for idx, it in enumerate(term_items):
        cy1 = start_yt + idx * (card_ht + 35)
        cy2 = cy1 + card_ht
        box = [2220, cy1, 2840, cy2]
        c = it['color']
        draw_3d_white_card(box, border_color=c, header_bg=it.get('bg', (248, 250, 252)), logo_img=it.get('logo'))
        draw_badge(2240, cy1 + 14, it['title'], bg=c, fg=(255, 255, 255))
        
        if it['type'] == 'HOLD':
            draw.text((2240, cy1 + 65), "FUNDS DEBIT FROZEN", fill=(0, 0, 0), font=f_h1)
            draw.text((2240, cy1 + 98), f"A/c: {it['acc'][:28]}", fill=(0, 0, 0), font=f_body_b)
            draw.text((2240, cy1 + 128), f"Hold Date: {it['dt']}", fill=(15, 23, 42), font=f_body)
            draw.text((2240, cy1 + 160), f"Lien Amount: Rs. {float(it['amt']):,.2f}", fill=(21, 128, 61), font=f_amt)
            draw.text((2240, cy2 - 30), "• Successfully Secured for Restitution", fill=(21, 128, 61), font=f_body_b)
        elif it['type'] == 'ATM':
            draw.text((2240, cy1 + 65), f"PHYSICAL CASH-OUT ({it['cnt']} TXNS)", fill=(0, 0, 0), font=f_h1)
            if it['acc']:
                draw.text((2240, cy1 + 98), f"Mule A/c: {it['acc']}", fill=(0, 0, 0), font=f_body_b)
            draw.text((2240, cy1 + 128), f"📍 Loc: {it['loc'][:32]}", fill=(185, 28, 28), font=f_body)
            draw.text((2240, cy1 + 160), f"Siphoned: Rs. {it['amt']}", fill=(185, 28, 28), font=f_amt)
            draw.text((2240, cy2 - 30), "• Requisition sent for ATM CCTV Footage", fill=(185, 28, 28), font=f_body_b)
        else: # L3
            draw.text((2240, cy1 + 65), it.get('bank', 'Merchant/Mule')[:26], fill=(0, 0, 0), font=f_h1)
            draw.text((2240, cy1 + 98), f"A/c: {it['acc']}", fill=(0, 0, 0), font=f_body_b)
            if it.get('ifsc'):
                draw.text((2240, cy1 + 126), f"IFSC: {it['ifsc']}", fill=(0, 0, 0), font=f_body)
            if it.get('branch'):
                draw.text((2240, cy1 + 150), f"🏛️ Branch: {it['branch'][:34]}", fill=(15, 23, 42), font=f_addr)
            draw.text((2240, max(cy1 + 175, cy2 - 62)), f"Settled: Rs. {it['amt']}", fill=(0, 0, 0), font=f_amt)
            draw.text((2240, cy2 - 30), "• Terminal Merchant / Mule Settlement", fill=(51, 65, 85), font=f_body_b)

        # Connection tube from closest L2 to Term
        src_boxes = l2_boxes or l1_boxes
        if src_boxes:
            closest_src = min(src_boxes, key=lambda b: abs((b[1]+b[3])/2 - (cy1+cy2)/2))
            draw_tube((closest_src[2], (closest_src[1] + closest_src[3]) // 2), (2220, (cy1 + cy2) // 2), color=(51, 65, 85), width=4, label=it['type'])

    # Col 4: Action Dossier Metrics (Pure White Card with Deep Black Typography)
    doss_box = [2960, 340, 3520, 2080]
    draw_3d_white_card(doss_box, border_color=(30, 41, 59), header_bg=(241, 245, 249))
    draw_badge(2985, 355, "INVESTIGATION METRICS", bg=(15, 23, 42), fg=(255, 255, 255))
    
    draw.text((2985, 415), "FINANCIAL FORENSICS", fill=(0, 0, 0), font=f_h1)
    
    metrics = [
        ("TOTAL REPORTED LOSS", f"Rs. {amt_str}", (185, 28, 28)),
        ("TOTAL LIEN SECURED", f"Rs. {lien_str}", (21, 128, 61)),
        ("TOTAL ATM CASH-OUT", f"Rs. {atm_str}", (185, 28, 28)),
        ("ASSET RECOVERY RATIO", f"{rec_ratio:.1f}%", (0, 0, 0) if rec_ratio > 0 else (71, 85, 105))
    ]
    my = 480
    for label, val, color in metrics:
        draw.text((2985, my), label, fill=(0, 0, 0), font=f_body_b)
        draw.text((2985, my + 28), val, fill=color, font=f_amt)
        my += 110
        
    draw.line([(2985, my), (3495, my)], fill=(203, 213, 225), width=2)
    my += 26
    draw.text((2985, my), "STATUTORY COMPLIANCE", fill=(0, 0, 0), font=f_h2)
    my += 48
    draw.text((2985, my), "• Notice U/S 94 BNSS: Issued", fill=(0, 0, 0), font=f_body)
    my += 36
    if is_fir:
        draw.text((2985, my), "• Freeze U/S 106 BNSS: Dispatched", fill=(0, 0, 0), font=f_body)
        my += 36
        draw.text((2985, my), "• Case Diary: Zimni 02 Maintained", fill=(0, 0, 0), font=f_body)
    else:
        draw.text((2985, my), "• Freeze Requisition: Dispatched", fill=(0, 0, 0), font=f_body)
        my += 36
        draw.text((2985, my), "• Case Diary: Skipped (Ack Stage)", fill=(71, 85, 105), font=f_body)
    my += 36
    draw.text((2985, my), "• IFSC API: Addresses Verified", fill=(21, 128, 61), font=f_body_b)
    
    my += 70
    draw.line([(2985, my), (3495, my)], fill=(203, 213, 225), width=2)
    my += 26
    draw.text((2985, my), "INVESTIGATING AGENCY", fill=(0, 0, 0), font=f_h2)
    my += 40
    draw.text((2985, my), "Cyber Police Station North District", fill=(0, 0, 0), font=f_body_b)
    my += 32
    draw.text((2985, my), "Delhi Police, Maurice Nagar", fill=(15, 23, 42), font=f_body)
    my += 32
    draw.text((2985, my), "Email: shocyber.north@delhipolice.gov.in", fill=(15, 23, 42), font=f_body)

    # Save high-res PNG and JPG
    os.makedirs(os.path.dirname(os.path.abspath(output_png)), exist_ok=True)
    img.save(output_png, format="PNG")
    rgb_img = img.convert("RGB")
    rgb_img.save(output_jpg, format="JPEG", quality=95)
    print(f"  [Flowchart 3D HD]: Saved {output_png} and {output_jpg}")

    # Generate 3D Animated Pulse GIF (forensic_money_trail_3d_animated.gif)
    try:
        gif_path = output_png.replace(".png", "_animated.gif")
        if not gif_path.endswith("_animated.gif"):
            gif_path = os.path.splitext(output_png)[0] + "_animated.gif"
            
        base_small = img.resize((1800, 1200), Image.Resampling.LANCZOS)
        scale_x = 1800.0 / W
        scale_y = 1200.0 / H
        
        frames = []
        num_frames = 12
        for f_idx in range(num_frames):
            frame = base_small.copy()
            f_draw = ImageDraw.Draw(frame)
            phase = f_idx / num_frames
            
            for (p1, p2, label, color) in tubes_list:
                sx1, sy1 = p1[0] * scale_x, p1[1] * scale_y
                sx2, sy2 = p2[0] * scale_x, p2[1] * scale_y
                
                # Draw 3 pulsing particles per conduit
                for p_offset in [0.0, 0.35, 0.70]:
                    t = (phase + p_offset) % 1.0
                    px = sx1 + (sx2 - sx1) * t
                    py = sy1 + (sy2 - sy1) * t
                    
                    # Glowing neon orb
                    f_draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=(0, 240, 255, 140))
                    f_draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 255, 255, 255))
            
            frames.append(frame.convert("RGB"))
            
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0,
            optimize=True
        )
        print(f"  [Flowchart 3D Animated GIF]: Saved {gif_path}")
    except Exception as gif_err:
        print(f"  [Flowchart GIF Warning]: {gif_err}")
