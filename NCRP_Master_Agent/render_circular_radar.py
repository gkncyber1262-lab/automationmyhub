# -*- coding: utf-8 -*-
"""
Generate Ultra-HD Circular Radar Money Trail Diagram for FIR No. 281/2026 (ACK: 30809260089905)
Resolution: 3200 x 2400 (Ultra High-Definition Forensic Print Quality)
"""

import os
import math
import shutil
from PIL import Image, ImageDraw, ImageFont

def render_circular_radar_chart():
    W, H = 3200, 2400
    img = Image.new("RGBA", (W, H), (4, 8, 20, 255))
    draw = ImageDraw.Draw(img)

    # Center of Radar
    cx, cy = 1600, 1300

    # Fonts
    try:
        f_title = ImageFont.truetype("arialbd.ttf", 46)
        f_sub = ImageFont.truetype("arialbd.ttf", 26)
        f_meta = ImageFont.truetype("arialbd.ttf", 20)
        f_orb = ImageFont.truetype("arialbd.ttf", 22)
        f_h1 = ImageFont.truetype("arialbd.ttf", 24)
        f_h2 = ImageFont.truetype("arialbd.ttf", 19)
        f_amt = ImageFont.truetype("arialbd.ttf", 28)
        f_body = ImageFont.truetype("arial.ttf", 17)
        f_body_b = ImageFont.truetype("arialbd.ttf", 17)
        f_pill = ImageFont.truetype("arialbd.ttf", 20)
    except:
        f_title = f_sub = f_meta = f_orb = f_h1 = f_h2 = f_amt = f_body = f_body_b = f_pill = ImageFont.load_default()

    # 1. Subtle Radial Background Grid
    for r in range(120, 1150, 60):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(15, 30, 60, 100), width=1)
    for deg in range(0, 360, 15):
        rad = math.radians(deg)
        x2 = cx + 1150 * math.cos(rad)
        y2 = cy + 1150 * math.sin(rad)
        draw.line([(cx, cy), (x2, y2)], fill=(15, 30, 60, 80), width=1)

    # 2. Institutional Forensic Header
    draw.rectangle([(0, 0), (W, 160)], fill=(8, 16, 36, 255))
    draw.line([(0, 160), (W, 160)], fill=(0, 240, 255, 180), width=3)
    
    # Title & Crest Text
    draw.text((60, 28), "CENTRAL FORENSIC INVESTIGATION RADAR — CIRCULAR MONEY TRAIL", fill=(255, 255, 255), font=f_title)
    draw.text((60, 88), "CYBER POLICE STATION NORTH DISTRICT • CASE FIR NO. 281/2026 • NCRP ACK: 30809260089905", fill=(0, 240, 255), font=f_sub)
    draw.text((60, 124), "STATUTORY COMPLIANCE: SECTION 94 & 106 BHARATIYA NAGARIK SURAKSHA SANHITA (BNSS, 2023)", fill=(160, 175, 200), font=f_meta)

    # Header Metric Chips (Right Aligned)
    chips = [
        ("TOTAL DEFRAUDED", "Rs. 1,98,000.00", (239, 68, 68)),
        ("LIEN MARKED (HOLD)", "Rs. 1,16,917.10 (59.05%)", (16, 185, 129)),
        ("ATM CASH LEAKAGE", "Rs. 77,082.90", (249, 115, 22)),
        ("MERCHANT CAPTURED", "Rs. 4,000.00", (168, 85, 247))
    ]
    chip_x = 1850
    for title, val, col in chips:
        draw.rounded_rectangle([(chip_x, 30), (chip_x + 310, 130)], radius=12, fill=(15, 25, 50, 220), outline=col, width=2)
        draw.text((chip_x + 18, 44), title, fill=(160, 175, 200), font=f_body_b)
        draw.text((chip_x + 18, 76), val, fill=col, font=f_h1)
        chip_x += 330

    # 3. Concentric Orbital Rings
    # Orbit 1: R=450 (Layer 1)
    draw.ellipse([cx - 460, cy - 460, cx + 460, cy + 460], outline=(0, 240, 255, 160), width=3)
    draw.text((cx, cy - 490), "⭕ ORBIT 1: LAYER 1 ENTRY MULE CLUSTER (RADIUS 460px)", fill=(0, 240, 255), font=f_orb, anchor="mm")

    # Orbit 2: R=760 (Layer 2)
    draw.ellipse([cx - 760, cy - 760, cx + 760, cy + 760], outline=(245, 158, 11, 160), width=3)
    draw.text((cx, cy - 790), "⭕ ORBIT 2: LAYER 2 INTERMEDIATE MULE & GATEWAY ROUTING (RADIUS 760px)", fill=(245, 158, 11), font=f_orb, anchor="mm")

    # Orbit 3: R=1050 (Terminal)
    draw.ellipse([cx - 1050, cy - 1050, cx + 1050, cy + 1050], outline=(168, 85, 247, 160), width=3)
    draw.text((cx, cy - 1080), "⭕ ORBIT 3: TERMINAL ENDPOINTS — ATM CASH LEAKAGES & SECURED LIEN (RADIUS 1050px)", fill=(168, 85, 247), font=f_orb, anchor="mm")

    # 4. Node Coordinates Definitions
    nodes = {
        "victim": {
            "x": cx, "y": cy, "w": 440, "h": 220, "color": (239, 68, 68),
            "tag": "LAYER 0 • VICTIM CORE", "name": "AMIT KUMAR (Complainant)",
            "bank": "Union Bank of India", "acc": "A/c: 125910100019333",
            "amt": "Rs. 1,98,000.00", "footer": "3 Fraudulent UPI Debits"
        },
        "iob": {
            "x": cx - 460, "y": cy, "w": 400, "h": 210, "color": (245, 158, 11),
            "tag": "LAYER 1 • ENTRY MULE", "name": "Indian Overseas Bank",
            "bank": "IFSC: IOBA0000499", "acc": "A/c: 049901000021812",
            "amt": "Rs. 99,000.00", "footer": "Txn: 627114473693"
        },
        "idfc": {
            "x": cx + 330, "y": cy + 325, "w": 400, "h": 210, "color": (16, 185, 129),
            "tag": "LAYER 1 • 100% LIEN MARKED", "name": "IDFC First Bank Mule",
            "bank": "IFSC: IDFB0000000", "acc": "A/c: 10304040490",
            "amt": "Rs. 95,000.00 (HOLD)", "footer": "100% Full Freeze (Secured)"
        },
        "icici": {
            "x": cx + 330, "y": cy - 325, "w": 400, "h": 210, "color": (245, 158, 11),
            "tag": "LAYER 1 • GATEWAY TRANSIT", "name": "ICICI Bank Gateway Hop",
            "bank": "IFSC: ICIC0DC0099", "acc": "A/c: 0103SL00IPAY",
            "amt": "Rs. 4,000.00", "footer": "Txn: 627216047641"
        },
        "sbi": {
            "x": cx - 560, "y": cy - 510, "w": 400, "h": 200, "color": (6, 182, 212),
            "tag": "LAYER 2 • SECONDARY MULE", "name": "State Bank of India",
            "bank": "IFSC: SBIN0001883", "acc": "A/c: 00000042581502450",
            "amt": "Rs. 500.00", "footer": "From IOB -> Direct ATM Out"
        },
        "payu": {
            "x": cx + 660, "y": cy - 370, "w": 400, "h": 200, "color": (6, 182, 212),
            "tag": "LAYER 2 • PG AGGREGATOR", "name": "PayU Payments Pvt Ltd",
            "bank": "VPA: facebookadsmanager.payu", "acc": "Aggregator Transit Node",
            "amt": "Rs. 4,000.00", "footer": "Settled to Citi Bank"
        },
        "iob_hold": {
            "x": cx - 580, "y": cy + 500, "w": 400, "h": 200, "color": (16, 185, 129),
            "tag": "PUT ON HOLD • SECURED", "name": "IOB Lien Marked Asset",
            "bank": "Indian Overseas Bank", "acc": "A/c: 049901000021812",
            "amt": "Rs. 21,917.10 (HOLD)", "footer": "Balance Zeroed (Sec 106)"
        },
        "iob_atm": {
            "x": cx - 1050, "y": cy, "w": 410, "h": 200, "color": (249, 115, 22),
            "tag": "ATM CASH-OUT LEAKAGE", "name": "IOB Mule ATM Cash-Out",
            "bank": "IOB Terminal Switch", "acc": "Source: 049901000021812",
            "amt": "Rs. 76,582.90", "footer": "ATM CCTV Requisitioned"
        },
        "sbi_atm": {
            "x": cx - 820, "y": cy - 660, "w": 410, "h": 200, "color": (249, 115, 22),
            "tag": "ATM CASH-OUT LEAKAGE", "name": "SBI Mule ATM Cash-Out",
            "bank": "SBI ATM Terminal", "acc": "Source: 00000042581502450",
            "amt": "Rs. 500.00", "footer": "Micro Cash Out Recorded"
        },
        "citi": {
            "x": cx + 1050, "y": cy - 100, "w": 410, "h": 200, "color": (168, 85, 247),
            "tag": "LAYER 3 • MERCHANT", "name": "Citi Bank / Meta Verified",
            "bank": "IFSC: CITI0000006", "acc": "A/c: 521752076",
            "amt": "Rs. 4,000.00", "footer": "Merchant Captured (Meta)"
        }
    }

    # 5. Cables & Moving Money Pills Along Curved Trajectories
    cables = [
        ("victim", "iob", (245, 158, 11), "Rs. 99,000.00"),
        ("victim", "idfc", (16, 185, 129), "Rs. 95,000.00"),
        ("victim", "icici", (245, 158, 11), "Rs. 4,000.00"),
        ("iob", "iob_hold", (16, 185, 129), "Rs. 21,917.10"),
        ("iob", "iob_atm", (249, 115, 22), "Rs. 76,582.90"),
        ("iob", "sbi", (6, 182, 212), "Rs. 500.00"),
        ("sbi", "sbi_atm", (249, 115, 22), "Rs. 500.00"),
        ("icici", "payu", (6, 182, 212), "Rs. 4,000.00"),
        ("payu", "citi", (168, 85, 247), "Rs. 4,000.00")
    ]

    for f_id, t_id, col, amt_txt in cables:
        n1 = nodes[f_id]
        n2 = nodes[t_id]
        x1, y1 = n1["x"], n1["y"]
        x2, y2 = n2["x"], n2["y"]

        # Draw smooth glowing cable line
        draw.line([(x1, y1), (x2, y2)], fill=(col[0], col[1], col[2], 80), width=8)
        draw.line([(x1, y1), (x2, y2)], fill=col, width=3)

        # Midpoint Money Capsule Pill
        mx = (x1 + x2) // 2
        my = (y1 + y2) // 2
        pw, ph = 210, 44
        draw.rounded_rectangle([(mx - pw//2, my - ph//2), (mx + pw//2, my + ph//2)], radius=22, fill=(10, 18, 38, 240), outline=col, width=2)
        draw.text((mx, my), f">> {amt_txt}", fill=(255, 255, 255), font=f_pill, anchor="mm")

    # 6. Draw Entity Cards
    for k, n in nodes.items():
        nx, ny, nw, nh = n["x"], n["y"], n["w"], n["h"]
        x0, y0 = nx - nw // 2, ny - nh // 2
        x1, y1 = nx + nw // 2, ny + nh // 2
        col = n["color"]

        # Outer Shadow & Card Body
        draw.rounded_rectangle([(x0 - 4, y0 - 4), (x1 + 4, y1 + 4)], radius=18, fill=(0, 0, 0, 140))
        draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=16, fill=(12, 20, 42, 245), outline=col, width=3)

        # Tag Banner
        draw.rounded_rectangle([(x0 + 16, y0 + 14), (x0 + 260, y0 + 44)], radius=6, fill=(col[0], col[1], col[2], 50), outline=col, width=1)
        draw.text((x0 + 26, y0 + 22), n["tag"], fill=col, font=f_meta)

        # Card Content
        draw.text((x0 + 18, y0 + 58), n["name"], fill=(255, 255, 255), font=f_h1)
        draw.text((x0 + 18, y0 + 90), n["bank"], fill=(160, 175, 200), font=f_body)
        draw.text((x0 + 18, y0 + 114), n["acc"], fill=(0, 240, 255), font=f_body_b)

        # Amount Panel
        draw.line([(x0 + 16, y0 + 145), (x1 - 16, y0 + 145)], fill=(40, 60, 95), width=1)
        draw.text((x0 + 18, y0 + 152), n["amt"], fill=col, font=f_amt)
        draw.text((x0 + 18, y0 + 184), n["footer"], fill=(200, 215, 235), font=f_body)

    # 7. Institutional Footer Notes
    draw.rectangle([(0, H - 90), (W, H)], fill=(8, 16, 36, 255))
    draw.line([(0, H - 90), (W, H - 90)], fill=(0, 240, 255, 180), width=2)
    footer_text = "FORENSIC SUMMARY: Out of disputed Rs. 1,98,000.00, Rs. 1,16,917.10 (59.05%) successfully frozen under lien. Siphoned cash Rs. 77,082.90 under Section 94 BNSS CCTV investigation. Section 106 BNSS invoked."
    draw.text((60, H - 56), footer_text, fill=(200, 220, 245), font=f_body_b)

    # Save to outputs
    out_dir = r"D:\agent\NCRP Compalint Againt\NCRP_Master_Agent\output\FIR_281_2026"
    os.makedirs(out_dir, exist_ok=True)
    out_png = os.path.join(out_dir, "circular_money_trail_radar_30809260089905.png")
    out_jpg = os.path.join(out_dir, "circular_money_trail_radar_30809260089905.jpg")
    
    img.save(out_png, format="PNG")
    img.convert("RGB").save(out_jpg, format="JPEG", quality=95)
    print(f"  [OK] Ultra-HD Circular Radar PNG saved: {out_png}")
    print(f"  [OK] Ultra-HD Circular Radar JPG saved: {out_jpg}")

    # Copy to brain artifact directory for instant viewing
    brain_dir = r"C:\Users\Hackthebox\.gemini\antigravity\brain\0a03e3cc-6ebc-4335-a186-beeec69269f8"
    brain_png = os.path.join(brain_dir, "circular_money_trail_radar_preview.png")
    shutil.copy2(out_png, brain_png)
    print(f"  [OK] Copied to Artifact: {brain_png}")

if __name__ == "__main__":
    render_circular_radar_chart()
