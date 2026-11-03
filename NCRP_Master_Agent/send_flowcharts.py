# -*- coding: utf-8 -*-
import requests
import base64
import os
import time

instance = 'instance196018'
token = 'hc9tgxc274xe56s0'
target_phone = '919818036472'

cases = [
    {
        'fir': 'FIR No. 287/2026',
        'date': '21/08/2026',
        'ack': '30808260070812',
        'amount': 'Rs. 2,10,000.00',
        'file': r'NCRP_Master_Agent/output/FIR_287_2026/forensic_money_trail_3d_30808260070812.png',
        'already_sent': True
    },
    {
        'fir': 'FIR No. 0272/2026',
        'date': '23/09/2026',
        'ack': '30809260086615',
        'amount': 'Rs. 1,05,312.80',
        'file': r'NCRP_Master_Agent/output/FIR_0272_2026/forensic_money_trail_3d_30809260086615.png',
        'already_sent': False
    },
    {
        'fir': 'FIR No. 0281/2026',
        'date': '30/09/2026',
        'ack': '30809260089905',
        'amount': 'Rs. 1,98,000.00',
        'file': r'NCRP_Master_Agent/output/FIR_0281_2026/forensic_money_trail_3d_30809260089905.png',
        'already_sent': False
    },
    {
        'fir': 'FIR No. 294/2026',
        'date': '02/11/2026',
        'ack': '30810260093099',
        'amount': 'Rs. 1,00,000.00',
        'file': r'NCRP_Master_Agent/output/FIR_294_2026/forensic_money_trail_3d_30810260093099.png',
        'already_sent': False
    },
    {
        'fir': 'Complaint ACK No. 30810260096918',
        'date': '02/11/2026',
        'ack': '30810260096918',
        'amount': 'Rs. 1,35,506.00',
        'file': r'NCRP_Master_Agent/output/Case_30810260096918/forensic_money_trail_3d_30810260096918.png',
        'already_sent': False
    }
]

print("Sending Money Trail Flowcharts to WhatsApp +{}...".format(target_phone))
for c in cases:
    if c['already_sent']:
        print("  [OK] {} Flowchart already delivered (Message ID 18).".format(c['fir']))
        continue
    
    if not os.path.exists(c['file']):
        print("  [ERR] File not found: {}".format(c['file']))
        continue

    with open(c['file'], 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')

    caption = (
        "🏛️ *OFFICE OF THE STATION HOUSE OFFICER*\n"
        "*CYBER POLICE STATION, NORTH DISTRICT, DELHI*\n"
        "────────────────────────────\n"
        "📊 *3D FORENSIC MONEY TRAIL & ASSET RECOVERY MATRIX*\n\n"
        "• *Case / Reference:* {} Dated {}\n"
        "• *Sections:* 318(4) BNS\n"
        "• *NCRP Complaint ID:* {}\n"
        "• *Total Defrauded:* {}\n"
        "• *Visualizer:* Dynamic Multi-Layer Forensic Flowchart\n"
        "────────────────────────────\n"
        "👤 *Investigating Officer:* SUB INSPECTOR SI RENU (Mob: 9899959840)"
    ).format(c['fir'], c['date'], c['ack'], c['amount'])

    payload = {
        'token': token,
        'to': target_phone,
        'image': 'data:image/png;base64,' + b64,
        'caption': caption
    }

    try:
        r = requests.post("https://api.ultramsg.com/{}/messages/image".format(instance), data=payload, timeout=45)
        print("  [{}] Status: {} | Response: {}".format(c['fir'], r.status_code, r.text))
    except Exception as ex:
        print("  [{}] Exception: {}".format(c['fir'], ex))

    time.sleep(8)

print("Finished sending all flowcharts!")
