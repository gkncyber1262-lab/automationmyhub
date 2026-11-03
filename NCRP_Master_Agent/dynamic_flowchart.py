import os
import sys
import json
import re
import math
from PIL import Image, ImageDraw, ImageFont

def create_dynamic_3d_flowchart(ctx: dict, output_png: str, output_jpg: str, base_dir: str):
    W, H = 3200, 2250
    img = Image.new("RGBA", (W, H), (5, 10, 24, 255))
    draw = ImageDraw.Draw(img)

    # Grid background
    for x in range(0, W, 80):
        draw.line([(x, 0), (x, H)], fill=(12, 24, 50, 160), width=1)
    for y in range(0, H, 80):
        draw.line([(0, y), (W, y)], fill=(12, 24, 50, 160), width=1)

    # Fonts
    try:
        f_title = ImageFont.truetype("arialbd.ttf", 40)
        f_sub = ImageFont.truetype("arialbd.ttf", 23)
        f_meta = ImageFont.truetype("arialbd.ttf", 18)
        f_col = ImageFont.truetype("arialbd.ttf", 20)
        f_h1 = ImageFont.truetype("arialbd.ttf", 22)
        f_h2 = ImageFont.truetype("arialbd.ttf", 18)
        f_amt = ImageFont.truetype("arialbd.ttf", 25)
        f_body = ImageFont.truetype("arial.ttf", 16)
        f_body_b = ImageFont.truetype("arialbd.ttf", 16)
        f_badge = ImageFont.truetype("arialbd.ttf", 14)
        f_tube = ImageFont.truetype("arialbd.ttf", 15)
    except Exception:
        f_title = ImageFont.load_default()
        f_sub = f_meta = f_col = f_h1 = f_h2 = f_amt = f_body = f_body_b = f_badge = f_tube = f_title

    def draw_3d_card(box, bg_top=(15, 25, 48), bg_bot=(8, 14, 28), border_color=(0, 240, 255), glow_alpha=35):
        x1, y1, x2, y2 = box
        w, h = x2 - x1, y2 - y1
        for s in range(12, 0, -2):
            alpha = int(glow_alpha - s * 2.2)
            draw.rounded_rectangle([x1 - s, y1 - s + 6, x2 + s, y2 + s + 10], radius=16, fill=(0, 0, 0, max(0, alpha)))
        card_surf = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        c_draw = ImageDraw.Draw(card_surf)
        for row in range(h):
            ratio = row / float(h)
            r = int(bg_top[0] * (1 - ratio) + bg_bot[0] * ratio)
            g = int(bg_top[1] * (1 - ratio) + bg_bot[1] * ratio)
            b = int(bg_top[2] * (1 - ratio) + bg_bot[2] * ratio)
            c_draw.line([(0, row), (w, row)], fill=(r, g, b, 248))
        for row in range(int(h * 0.35)):
            g_alpha = int(35 * (1 - row / (h * 0.35)))
            c_draw.line([(0, row), (w, row)], fill=(255, 255, 255, g_alpha))
        c_draw.rounded_rectangle([1, 1, w - 2, h - 2], radius=14, outline=border_color, width=3)
        img.alpha_composite(card_surf, (x1, y1))

    def draw_badge(x, y, text, bg=(220, 53, 69), fg=(255, 255, 255)):
        w = int(draw.textlength(text, f_badge)) + 20
        h = 26
        draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=bg, outline=(255, 255, 255, 180), width=1)
        draw.text((x + 10, y + 4), text, fill=fg, font=f_badge)

    def draw_tube(p1, p2, color=(0, 240, 255), width=4, label=""):
        draw.line([p1, p2], fill=(color[0]//3, color[1]//3, color[2]//3, 100), width=width + 4)
        draw.line([p1, p2], fill=color, width=width)
        x1, y1 = p1
        x2, y2 = p2
        angle = math.atan2(y2 - y1, x2 - x1)
        a_len = 14
        p_a1 = (x2 - a_len * math.cos(angle - math.pi / 6), y2 - a_len * math.sin(angle - math.pi / 6))
        p_a2 = (x2 - a_len * math.cos(angle + math.pi / 6), y2 - a_len * math.sin(angle + math.pi / 6))
        draw.polygon([p2, p_a1, p_a2], fill=color)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            lw = int(draw.textlength(label, f_tube)) + 16
            lh = 24
            draw.rounded_rectangle([mx - lw/2, my - lh/2, mx + lw/2, my + lh/2], radius=5, fill=(10, 18, 36, 230), outline=color, width=1)
            draw.text((mx - lw/2 + 8, my - lh/2 + 3), label, fill=(255, 255, 255), font=f_tube)

    # Paste crest
    crest_p = os.path.join(base_dir, "assets", "delhi_police_crest_only.png")
    if not os.path.exists(crest_p):
        crest_p = os.path.join(base_dir, "assets", "delhi_police_crest_hd.png")
    if os.path.exists(crest_p):
        try:
            c_img = Image.open(crest_p).convert("RGBA").resize((95, 95), Image.Resampling.LANCZOS)
            img.alpha_composite(c_img, (1552, 20))
        except Exception:
            pass

    # Extract meta
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

    # Top Header
    t_text = "CYBER POLICE STATION, NORTH DISTRICT, DELHI POLICE"
    draw.text(((W - draw.textlength(t_text, f_title)) // 2, 130), t_text, fill=(255, 215, 0), font=f_title)
    
    if is_fir:
        st_text = f"3D FORENSIC MONEY TRAIL & ASSET RECOVERY MATRIX | CASE FIR NO. {fir_no} DATED {fir_date}"
    else:
        st_text = f"3D FORENSIC MONEY TRAIL & ASSET RECOVERY MATRIX | NCRP ACK NO. {ack}"
    draw.text(((W - draw.textlength(st_text, f_sub)) // 2, 185), st_text, fill=(0, 240, 255), font=f_sub)

    meta_text = f"NCRP ACKNOWLEDGEMENT NO: {ack} | U/S 318(4) BNS | COMPLAINANT: {comp_name}"
    draw.text(((W - draw.textlength(meta_text, f_meta)) // 2, 225), meta_text, fill=(203, 213, 225), font=f_meta)

    # Column Headers
    cols = [
        (100, 560, "LAYER 0: VICTIM ACCOUNT", (239, 68, 68)),
        (680, 1220, "LAYER 1: ENTRY MULE ACCOUNTS", (245, 158, 11)),
        (1340, 1880, "LAYER 2: INTERMEDIARY MULES", (56, 189, 248)),
        (2000, 2540, "TERMINAL CASH-OUTS & LIENS", (168, 85, 247)),
        (2660, 3120, "INVESTIGATION ACTION DOSSIER", (16, 185, 129))
    ]
    for x1, x2, label, c in cols:
        draw.rounded_rectangle([x1, 270, x2, 310], radius=8, fill=(15, 23, 42, 220), outline=c, width=2)
        draw.text((x1 + 16, 278), label, fill=c, font=f_col)

    # 1. Victim Box
    v_box = [100, 650, 560, 1050]
    draw_3d_card(v_box, bg_top=(36, 14, 20), bg_bot=(18, 8, 12), border_color=(239, 68, 68))
    draw_badge(120, 670, "COMPLAINANT / VICTIM", bg=(220, 38, 38))
    draw.text((120, 715), f"{comp_name}", fill=(255, 255, 255), font=f_h1)
    draw.text((120, 755), f"Bank: {v_bank}", fill=(203, 213, 225), font=f_body_b)
    draw.text((120, 790), f"A/c No: {v_acc}", fill=(148, 163, 184), font=f_body)
    if v_mob:
        draw.text((120, 825), f"Mobile: +91-{v_mob}", fill=(148, 163, 184), font=f_body)
    draw.text((120, 865), f"Incident: {c_meta.get('incident_date', 'N/A')}", fill=(148, 163, 184), font=f_body)
    draw.text((120, 910), "Total Defrauded Amount:", fill=(255, 180, 180), font=f_body_b)
    draw.text((120, 945), f"Rs. {amt_str}", fill=(255, 75, 75), font=f_amt)
    draw.text((120, 1000), "Initial Fraudulent Disbursal U/S 318(4) BNS", fill=(251, 191, 36), font=f_body)

    # Group transfers by layer
    l1_items = []
    l2_items = []
    l3_items = []
    
    # Extract from raw_transfers
    raw_txns = ctx.get("raw_transfers", [])
    seen_keys = set()
    for r in raw_txns:
        if len(r) < 10: continue
        r_str = ' '.join(str(c or '').replace('\n', ' ') for c in r)
        if 'layer' not in r_str.lower(): continue
        
        b_name = str(r[1] or '').replace('\n', ' ').strip()
        acc_info = str(r[2] or '').replace('\n', ' ').strip()
        utr = str(r[3] or '').replace('\n', '').strip()
        disp_str = str(r[6] or '0').replace(',', '').replace('\n', '').replace(' ', '').strip()
        try: disp = float(disp_str)
        except: disp = 0.0
        
        m_lay = re.search(r'Layer\s*:?\s*(\d+)', acc_info, re.I)
        l_num = int(m_lay.group(1)) if m_lay else 1
        
        m_ifsc = re.search(r'[A-Za-z]{4}0[A-Za-z0-9]{6}', acc_info)
        ifsc = m_ifsc.group(0).upper() if m_ifsc else ''
        
        clean_acc = acc_info
        if m_lay: clean_acc = clean_acc.replace(m_lay.group(0), '')
        if m_ifsc: clean_acc = clean_acc.replace(m_ifsc.group(0), '')
        clean_acc = re.sub(r'[^a-zA-Z0-9@._-]', '', clean_acc).strip()
        
        key = (l_num, b_name, clean_acc)
        if key in seen_keys:
            # Add to amount
            for it in (l1_items if l_num == 1 else l2_items if l_num == 2 else l3_items):
                if it['key'] == key:
                    it['disp'] += disp
                    if utr and utr not in it['utrs']: it['utrs'].append(utr)
                    break
        else:
            seen_keys.add(key)
            item = {'key': key, 'bank': b_name, 'acc': clean_acc, 'ifsc': ifsc, 'disp': disp, 'utrs': [utr] if utr else []}
            if l_num == 1: l1_items.append(item)
            elif l_num == 2: l2_items.append(item)
            else: l3_items.append(item)

    # Draw Layer 1 Cards (Col 1)
    l1_boxes = []
    num_l1 = len(l1_items) or 1
    avail_h = 1600
    card_h = min(280, int((avail_h - (num_l1 - 1) * 40) / num_l1))
    start_y = 350 + int((avail_h - (num_l1 * card_h + (num_l1 - 1) * 40)) / 2)
    
    for idx, it in enumerate(l1_items):
        cy1 = start_y + idx * (card_h + 40)
        cy2 = cy1 + card_h
        box = [680, cy1, 1220, cy2]
        l1_boxes.append(box)
        draw_3d_card(box, bg_top=(32, 24, 12), bg_bot=(16, 12, 6), border_color=(245, 158, 11))
        draw_badge(700, cy1 + 15, "LAYER 1 - ENTRY MULE", bg=(217, 119, 6))
        draw.text((700, cy1 + 50), it['bank'][:26], fill=(255, 255, 255), font=f_h1)
        draw.text((700, cy1 + 85), f"A/c No: {it['acc']}", fill=(203, 213, 225), font=f_body_b)
        if it['ifsc']:
            draw.text((700, cy1 + 115), f"IFSC: {it['ifsc']}", fill=(148, 163, 184), font=f_body)
        if it['utrs']:
            draw.text((700, cy1 + 145), f"Txn/UTR: {it['utrs'][0][:24]}", fill=(148, 163, 184), font=f_body)
        draw.text((700, cy1 + 180), f"Credited: Rs. {it['disp']:,.2f}", fill=(251, 191, 36), font=f_amt)
        draw.text((700, cy1 + 225), "• Notice U/S 94 BNSS Dispatched", fill=(52, 211, 153), font=f_body)

        # Tube from Victim to L1
        draw_tube((560, (v_box[1] + v_box[3]) // 2), (680, (cy1 + cy2) // 2), color=(245, 158, 11), width=4, label=f"Rs. {it['disp']:,.0f}")

    # Draw Layer 2 Cards (Col 2)
    l2_boxes = []
    num_l2 = len(l2_items) or 1
    card_h2 = min(280, int((avail_h - (num_l2 - 1) * 35) / num_l2))
    start_y2 = 350 + int((avail_h - (num_l2 * card_h2 + (num_l2 - 1) * 35)) / 2)
    
    for idx, it in enumerate(l2_items):
        cy1 = start_y2 + idx * (card_h2 + 35)
        cy2 = cy1 + card_h2
        box = [1340, cy1, 1880, cy2]
        l2_boxes.append(box)
        draw_3d_card(box, bg_top=(14, 25, 42), bg_bot=(7, 14, 24), border_color=(56, 189, 248))
        draw_badge(1360, cy1 + 15, "LAYER 2 - INTERMEDIARY MULE", bg=(2, 132, 199))
        draw.text((1360, cy1 + 50), it['bank'][:26], fill=(255, 255, 255), font=f_h1)
        draw.text((1360, cy1 + 85), f"A/c No: {it['acc']}", fill=(203, 213, 225), font=f_body_b)
        if it['ifsc']:
            draw.text((1360, cy1 + 115), f"IFSC: {it['ifsc']}", fill=(148, 163, 184), font=f_body)
        if it['utrs']:
            draw.text((1360, cy1 + 145), f"Txn/UTR: {it['utrs'][0][:24]}", fill=(148, 163, 184), font=f_body)
        draw.text((1360, cy1 + 180), f"Transferred: Rs. {it['disp']:,.2f}", fill=(56, 189, 248), font=f_amt)
        draw.text((1360, cy1 + 225), "• Statutory Freezing Notice U/S 94/106 BNSS", fill=(165, 180, 252), font=f_body)

        # Tube from closest L1 to L2
        if l1_boxes:
            closest_l1 = min(l1_boxes, key=lambda b: abs((b[1]+b[3])/2 - (cy1+cy2)/2))
            draw_tube((1220, (closest_l1[1] + closest_l1[3]) // 2), (1340, (cy1 + cy2) // 2), color=(56, 189, 248), width=3, label=f"Rs. {it['disp']:,.0f}")

    # Draw Terminal Endpoints (Col 3): Holds & ATMs
    term_items = []
    # Holds
    raw_holds = ctx.get("raw_holds", [])
    for h in raw_holds:
        if len(h) < 4: continue
        amt = str(h[3] or '0').replace(',', '').replace('\n', '').strip()
        h_acc = str(h[1] or '').replace('\n', '').strip()
        h_dt = str(h[2] or '').replace('\n', '').strip()
        term_items.append({'type': 'HOLD', 'title': '🛡️ LIEN MARKED / SECURED', 'acc': h_acc, 'amt': amt, 'dt': h_dt, 'color': (16, 185, 129)})
    
    # ATMs
    raw_atms = ctx.get("atm_withdrawals", [])
    if raw_atms:
        # Sum total ATM
        atm_total = 0.0
        atm_loc = "ATM Cash Dispenser"
        atm_acc = ""
        for a in raw_atms:
            for ci in [3, 4, 1]:
                v_s = str(a[ci] or '').replace(',', '').replace('\n', '').strip()
                if re.match(r'^\d+(\.\d+)?$', v_s):
                    atm_total += float(v_s)
                    break
            if len(a) > 6 and str(a[6] or '').strip():
                atm_loc = str(a[6] or '').replace('\n', ' ').strip()
            if len(a) > 2 and re.search(r'\d{9,}', str(a[2] or '')):
                atm_acc = str(a[2] or '').replace('\n', '').strip()
        term_items.append({'type': 'ATM', 'title': '🏧 ATM CASH WITHDRAWAL (SIPHONED)', 'acc': atm_acc, 'amt': f"{atm_total:,.2f}", 'loc': atm_loc, 'cnt': len(raw_atms), 'color': (239, 68, 68)})

    # Layer 3 mules if any
    for it in l3_items:
        term_items.append({'type': 'L3', 'title': 'LAYER 3 - TERMINAL MULE', 'acc': it['acc'], 'amt': f"{it['disp']:,.2f}", 'bank': it['bank'], 'color': (168, 85, 247)})

    num_term = len(term_items) or 1
    card_ht = min(280, int((avail_h - (num_term - 1) * 35) / num_term))
    start_yt = 350 + int((avail_h - (num_term * card_ht + (num_term - 1) * 35)) / 2)

    for idx, it in enumerate(term_items):
        cy1 = start_yt + idx * (card_ht + 35)
        cy2 = cy1 + card_ht
        box = [2000, cy1, 2540, cy2]
        c = it['color']
        draw_3d_card(box, bg_top=(c[0]//8, c[1]//8, c[2]//8), bg_bot=(c[0]//16, c[1]//16, c[2]//16), border_color=c)
        draw_badge(2020, cy1 + 15, it['title'], bg=(c[0]//2, c[1]//2, c[2]//2))
        
        if it['type'] == 'HOLD':
            draw.text((2020, cy1 + 55), "FUNDS DEBIT FROZEN", fill=(255, 255, 255), font=f_h1)
            draw.text((2020, cy1 + 90), f"A/c: {it['acc']}", fill=(203, 213, 225), font=f_body_b)
            draw.text((2020, cy1 + 120), f"Hold Date: {it['dt']}", fill=(148, 163, 184), font=f_body)
            draw.text((2020, cy1 + 155), f"Lien Amount: Rs. {float(it['amt']):,.2f}", fill=(52, 211, 153), font=f_amt)
            draw.text((2020, cy1 + 200), "• Successfully Secured for Victim Restitution", fill=(52, 211, 153), font=f_body_b)
        elif it['type'] == 'ATM':
            draw.text((2020, cy1 + 55), f"PHYSICAL CASH-OUT ({it['cnt']} TXNS)", fill=(255, 255, 255), font=f_h1)
            if it['acc']:
                draw.text((2020, cy1 + 90), f"Mule A/c: {it['acc']}", fill=(203, 213, 225), font=f_body_b)
            draw.text((2020, cy1 + 120), f"Loc: {it['loc'][:28]}", fill=(255, 180, 180), font=f_body)
            draw.text((2020, cy1 + 155), f"Siphoned: Rs. {it['amt']}", fill=(255, 80, 80), font=f_amt)
            draw.text((2020, cy1 + 200), "• Requisition sent for ATM CCTV Footage", fill=(239, 68, 68), font=f_body_b)
        else: # L3
            draw.text((2020, cy1 + 55), it.get('bank', 'Merchant/Mule')[:26], fill=(255, 255, 255), font=f_h1)
            draw.text((2020, cy1 + 90), f"A/c: {it['acc']}", fill=(203, 213, 225), font=f_body_b)
            draw.text((2020, cy1 + 155), f"Settled: Rs. {it['amt']}", fill=(192, 132, 252), font=f_amt)
            draw.text((2020, cy1 + 200), "• Terminal Merchant / Mule Settlement", fill=(192, 132, 252), font=f_body_b)

        # Tube from closest L2 to Term
        src_boxes = l2_boxes or l1_boxes
        if src_boxes:
            closest_src = min(src_boxes, key=lambda b: abs((b[1]+b[3])/2 - (cy1+cy2)/2))
            draw_tube((closest_src[2], (closest_src[1] + closest_src[3]) // 2), (2000, (cy1 + cy2) // 2), color=c, width=3, label=it['type'])

    # Col 4: Action Dossier Metrics
    doss_box = [2660, 350, 3120, 1950]
    draw_3d_card(doss_box, bg_top=(16, 28, 20), bg_bot=(8, 16, 12), border_color=(16, 185, 129))
    draw_badge(2685, 375, "INVESTIGATION METRICS", bg=(5, 150, 105))
    
    draw.text((2685, 430), "FINANCIAL FORENSICS", fill=(255, 255, 255), font=f_h1)
    
    metrics = [
        ("TOTAL REPORTED LOSS", f"Rs. {amt_str}", (239, 68, 68)),
        ("TOTAL LIEN SECURED", f"Rs. {lien_str}", (52, 211, 153)),
        ("TOTAL ATM CASH-OUT", f"Rs. {atm_str}", (248, 113, 113)),
        ("ASSET RECOVERY RATIO", f"{rec_ratio:.1f}%", (0, 240, 255) if rec_ratio > 0 else (148, 163, 184))
    ]
    my = 490
    for label, val, color in metrics:
        draw.text((2685, my), label, fill=(148, 163, 184), font=f_body_b)
        draw.text((2685, my + 30), val, fill=color, font=f_amt)
        my += 100
        
    draw.line([(2685, my), (3095, my)], fill=(12, 48, 30), width=2)
    my += 25
    draw.text((2685, my), "STATUTORY COMPLIANCE", fill=(255, 215, 0), font=f_h2)
    my += 45
    draw.text((2685, my), "• Notice U/S 94 BNSS: Issued", fill=(203, 213, 225), font=f_body)
    my += 35
    draw.text((2685, my), "• Freeze U/S 106 BNSS: Dispatched", fill=(203, 213, 225), font=f_body)
    my += 35
    draw.text((2685, my), "• Case Diary: Zimni 1, 2, 3 Done", fill=(203, 213, 225), font=f_body)
    my += 35
    draw.text((2685, my), "• Penal Section: 318(4) BNS Only", fill=(52, 211, 153), font=f_body_b)
    
    my += 70
    draw.line([(2685, my), (3095, my)], fill=(12, 48, 30), width=2)
    my += 25
    draw.text((2685, my), "INVESTIGATING AGENCY", fill=(255, 255, 255), font=f_h2)
    my += 40
    draw.text((2685, my), "Cyber Police Station North District", fill=(203, 213, 225), font=f_body)
    my += 30
    draw.text((2685, my), "Delhi Police, Maurice Nagar", fill=(148, 163, 184), font=f_body)
    my += 30
    draw.text((2685, my), "Email: shocyber.north@delhipolice.gov.in", fill=(148, 163, 184), font=f_body)

    os.makedirs(os.path.dirname(os.path.abspath(output_png)), exist_ok=True)
    img.save(output_png, format="PNG")
    rgb_img = img.convert("RGB")
    rgb_img.save(output_jpg, format="JPEG", quality=95)
    print(f"  ✅ Dynamic 3D Flowchart Generated: {output_png} & {output_jpg}")
