import os
import json
import re

def create_dynamic_html_visualizer(ctx: dict, output_html: str):
    c_meta = ctx.get("case_meta", {})
    comp = ctx.get("complainant", {})
    fin = ctx.get("financial_summary", {})
    
    ack = c_meta.get("acknowledgement_no", "N/A")
    fir_no = c_meta.get("fir_no", "")
    fir_date = c_meta.get("fir_date", "")
    is_fir = c_meta.get("case_type") == "fir" or bool(fir_no)
    
    case_ref = f"Case FIR No. {fir_no} Dated {fir_date}" if is_fir else f"NCRP ACK No. {ack}"
    comp_name = comp.get("name", "Complainant")
    v_bank = comp.get("victim_bank", "Victim Bank")
    v_acc = comp.get("victim_account", "Account")
    v_mob = comp.get("mobile", "")
    amt_str = fin.get("alleged_amount", "0.00")
    lien_str = fin.get("total_lien_amount", "0.00")
    atm_str = fin.get("total_atm_withdrawn", "0.00")
    rec_ratio = fin.get("recovery_ratio_pct", 0.0)

    # Build nodes & links
    nodes = []
    links = []
    
    # 0. Victim Node
    victim_id = "node_victim"
    nodes.append({
        "id": victim_id,
        "name": f"Victim: {comp_name}",
        "type": "victim",
        "layer": 0,
        "bank": v_bank,
        "account": v_acc,
        "amount": f"Rs. {amt_str}",
        "details": f"Complainant Bank: {v_bank} | A/c: {v_acc} | Mob: {v_mob}"
    })
    
    # 1. Transfers
    raw_txns = ctx.get("raw_transfers", [])
    seen_nodes = {victim_id: True}
    l1_nodes = []
    l2_nodes = []
    
    for idx, r in enumerate(raw_txns, start=1):
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
        
        node_id = f"node_L{l_num}_{clean_acc}"
        if node_id not in seen_nodes:
            seen_nodes[node_id] = True
            node_data = {
                "id": node_id,
                "name": f"{b_name[:24]}",
                "type": f"layer_{l_num}",
                "layer": l_num,
                "bank": b_name,
                "account": clean_acc,
                "ifsc": ifsc,
                "amount": f"Rs. {disp:,.2f}",
                "utr": utr,
                "details": f"Layer {l_num} Mule | Bank: {b_name} | A/c: {clean_acc} | IFSC: {ifsc}"
            }
            nodes.append(node_data)
            if l_num == 1: l1_nodes.append(node_id)
            elif l_num == 2: l2_nodes.append(node_id)
            
            # Add link
            if l_num == 1:
                links.append({"source": victim_id, "target": node_id, "amount": f"Rs. {disp:,.2f}", "utr": utr})
            elif l_num == 2 and l1_nodes:
                links.append({"source": l1_nodes[0], "target": node_id, "amount": f"Rs. {disp:,.2f}", "utr": utr})

    # Holds
    for hi, h in enumerate(ctx.get("raw_holds", []), start=1):
        if len(h) < 4: continue
        amt = str(h[3] or '0').replace(',', '').replace('\n', '').strip()
        h_acc = str(h[1] or '').replace('\n', '').strip()
        h_dt = str(h[2] or '').replace('\n', '').strip()
        h_id = f"node_hold_{hi}"
        nodes.append({
            "id": h_id,
            "name": f"🛡️ LIEN: Rs. {float(amt):,.2f}",
            "type": "lien",
            "layer": 3,
            "bank": "Bank Lien",
            "account": h_acc,
            "amount": f"Rs. {float(amt):,.2f}",
            "details": f"100% Debit Freeze | Date: {h_dt} | A/c: {h_acc}"
        })
        src = l1_nodes[0] if l1_nodes else victim_id
        links.append({"source": src, "target": h_id, "amount": f"Rs. {float(amt):,.2f}", "utr": "LIEN HOLD"})

    # ATMs
    raw_atms = ctx.get("atm_withdrawals", [])
    if raw_atms:
        atm_tot = 0.0
        atm_loc = "ATM"
        for a in raw_atms:
            for ci in [3, 4, 1]:
                v_s = str(a[ci] or '').replace(',', '').replace('\n', '').strip()
                if re.match(r'^\d+(\.\d+)?$', v_s):
                    atm_tot += float(v_s)
                    break
            if len(a) > 6 and str(a[6] or '').strip():
                atm_loc = str(a[6] or '').replace('\n', ' ').strip()
        atm_id = "node_atm_terminal"
        nodes.append({
            "id": atm_id,
            "name": f"🏧 ATM CASH: Rs. {atm_tot:,.2f}",
            "type": "atm",
            "layer": 3,
            "bank": "ATM Cash-Out",
            "amount": f"Rs. {atm_tot:,.2f}",
            "details": f"{len(raw_atms)} ATM Withdrawals | Location: {atm_loc}"
        })
        src = l1_nodes[-1] if l1_nodes else victim_id
        links.append({"source": src, "target": atm_id, "amount": f"Rs. {atm_tot:,.2f}", "utr": "CASH WITHDRAWAL"})

    # Generate HTML content
    nodes_json = json.dumps(nodes, ensure_ascii=False)
    links_json = json.dumps(links, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D FORENSIC MONEY TRAIL | {case_ref} | U/S 318(4) BNS</title>
    <style>
        :root {{
            --bg-base: #060b19;
            --bg-card: #0d162d;
            --cyan-glow: #00f0ff;
            --red-glow: #ef4444;
            --green-glow: #10b981;
            --amber-glow: #f59e0b;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }}
        body {{ background: var(--bg-base); color: #e2e8f0; overflow-x: hidden; }}
        header {{ text-align: center; padding: 25px 20px; border-bottom: 2px solid #1e293b; background: rgba(13,22,45,0.7); backdrop-filter: blur(8px); }}
        h1 {{ color: #ffd700; font-size: 24px; letter-spacing: 1px; }}
        h2 {{ color: var(--cyan-glow); font-size: 18px; margin-top: 6px; font-weight: 600; }}
        .meta-bar {{ margin-top: 8px; color: #94a3b8; font-size: 14px; }}
        .badge-sec {{ background: #dc2626; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; margin-left: 8px; }}
        
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; max-width: 1300px; margin: 20px auto; padding: 0 15px; }}
        .m-card {{ background: var(--bg-card); border-radius: 10px; padding: 15px 20px; border: 1px solid #1e293b; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
        .m-card h4 {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px; }}
        .m-card .val {{ font-size: 22px; font-weight: bold; }}
        
        .trail-container {{ max-width: 1300px; margin: 20px auto; padding: 20px 15px; display: flex; flex-direction: column; gap: 30px; }}
        .layer-row {{ background: rgba(13,22,45,0.5); border: 1px solid #1e293b; border-radius: 12px; padding: 20px; }}
        .layer-title {{ font-size: 15px; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }}
        .node-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }}
        .node-card {{ background: #0b1329; border: 2px solid; border-radius: 10px; padding: 15px; position: relative; transition: all 0.3s; }}
        .node-card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,240,255,0.25); }}
        .node-badge {{ display: inline-block; padding: 3px 8px; font-size: 11px; font-weight: bold; border-radius: 4px; margin-bottom: 8px; color: #fff; }}
        .node-name {{ font-size: 16px; font-weight: bold; color: #fff; margin-bottom: 6px; }}
        .node-row {{ font-size: 13px; color: #cbd5e1; margin-bottom: 4px; display: flex; justify-content: space-between; }}
        .node-amt {{ font-size: 18px; font-weight: bold; margin-top: 8px; }}
        
        .flow-arrow {{ text-align: center; color: var(--cyan-glow); font-size: 24px; margin: -10px 0; }}
        footer {{ text-align: center; padding: 25px; color: #64748b; font-size: 13px; border-top: 1px solid #1e293b; margin-top: 40px; }}
    </style>
</head>
<body>
    <header>
        <h1>OFFICE OF THE STATION HOUSE OFFICER, CYBER POLICE STATION</h1>
        <h2>3D FORENSIC MONEY TRAIL & ASSET RECOVERY MATRIX | {case_ref}</h2>
        <div class="meta-bar">
            NCRP ACK: <strong>{ack}</strong> | COMPLAINANT: <strong>{comp_name}</strong>
            <span class="badge-sec">PENAL SECTION: 318(4) BNS ONLY</span>
        </div>
    </header>

    <div class="metrics-grid">
        <div class="m-card" style="border-left: 4px solid var(--red-glow);">
            <h4>TOTAL REPORTED LOSS</h4>
            <div class="val" style="color: var(--red-glow);">Rs. {amt_str}</div>
        </div>
        <div class="m-card" style="border-left: 4px solid var(--green-glow);">
            <h4>TOTAL LIEN SECURED</h4>
            <div class="val" style="color: var(--green-glow);">Rs. {lien_str}</div>
        </div>
        <div class="m-card" style="border-left: 4px solid #ef4444;">
            <h4>ATM CASH DISPERSED</h4>
            <div class="val" style="color: #f87171;">Rs. {atm_str}</div>
        </div>
        <div class="m-card" style="border-left: 4px solid var(--cyan-glow);">
            <h4>ASSET RECOVERY RATIO</h4>
            <div class="val" style="color: var(--cyan-glow);">{rec_ratio:.1f}%</div>
        </div>
    </div>

    <div class="trail-container">
        <!-- Layer 0 -->
        <div class="layer-row" style="border-color: var(--red-glow);">
            <div class="layer-title" style="color: var(--red-glow);">
                <span>🚨 LAYER 0: VICTIM DEBIT DISBURSAL</span>
            </div>
            <div class="node-grid">
                <div class="node-card" style="border-color: var(--red-glow);">
                    <span class="node-badge" style="background: #dc2626;">COMPLAINANT / VICTIM</span>
                    <div class="node-name">{comp_name}</div>
                    <div class="node-row"><span>Victim Bank:</span><span>{v_bank}</span></div>
                    <div class="node-row"><span>Victim A/c:</span><span>{v_acc}</span></div>
                    <div class="node-amt" style="color: var(--red-glow);">Rs. {amt_str}</div>
                </div>
            </div>
        </div>

        <div class="flow-arrow">▼ Funds Disbursed to Entry Mules (Layer 1) ▼</div>

        <!-- Layer 1 -->
        <div class="layer-row" style="border-color: var(--amber-glow);" id="layer1_container">
            <div class="layer-title" style="color: var(--amber-glow);">
                <span>⚠️ LAYER 1: DIRECT ENTRY MULE ACCOUNTS (NOTICE U/S 94 BNSS)</span>
            </div>
            <div class="node-grid" id="l1_grid"></div>
        </div>

        <div class="flow-arrow">▼ Funds Layered across Banking Channels (Layer 2) ▼</div>

        <!-- Layer 2 -->
        <div class="layer-row" style="border-color: var(--cyan-glow);" id="layer2_container">
            <div class="layer-title" style="color: var(--cyan-glow);">
                <span>⚡ LAYER 2: INTERMEDIARY MULES & AGGREGATOR WALLETS</span>
            </div>
            <div class="node-grid" id="l2_grid"></div>
        </div>

        <div class="flow-arrow">▼ Terminal Lien Freezes & ATM Siphoning ▼</div>

        <!-- Terminal Endpoints -->
        <div class="layer-row" style="border-color: #a855f7;" id="term_container">
            <div class="layer-title" style="color: #a855f7;">
                <span>🎯 TERMINAL ENDPOINTS: LIENS & CASH-OUTS</span>
            </div>
            <div class="node-grid" id="term_grid"></div>
        </div>
    </div>

    <footer>
        DELHI POLICE CYBER CRIME INVESTIGATION SUITE • STATUTORY COMPLIANCE: SECTION 94 BNSS & SECTION 318(4) BNS<br>
        PS Cyber, North District, Maurice Nagar, Delhi-110007 • Email: shocyber.north@delhipolice.gov.in
    </footer>

    <script>
        const NODES = {nodes_json};
        const LINKS = {links_json};

        const l1Grid = document.getElementById('l1_grid');
        const l2Grid = document.getElementById('l2_grid');
        const termGrid = document.getElementById('term_grid');

        let hasL1 = false, hasL2 = false, hasTerm = false;

        NODES.forEach(n => {{
            if (n.type === 'layer_1') {{
                hasL1 = true;
                l1Grid.innerHTML += `
                    <div class="node-card" style="border-color: var(--amber-glow);">
                        <span class="node-badge" style="background: #d97706;">ENTRY MULE</span>
                        <div class="node-name">${{n.name}}</div>
                        <div class="node-row"><span>Account No:</span><span>${{n.account}}</span></div>
                        <div class="node-row"><span>IFSC Code:</span><span>${{n.ifsc || 'N/A'}}</span></div>
                        <div class="node-amt" style="color: var(--amber-glow);">${{n.amount}}</div>
                    </div>`;
            }} else if (n.type === 'layer_2') {{
                hasL2 = true;
                l2Grid.innerHTML += `
                    <div class="node-card" style="border-color: var(--cyan-glow);">
                        <span class="node-badge" style="background: #0284c7;">INTERMEDIARY MULE</span>
                        <div class="node-name">${{n.name}}</div>
                        <div class="node-row"><span>Account No:</span><span>${{n.account}}</span></div>
                        <div class="node-row"><span>IFSC Code:</span><span>${{n.ifsc || 'N/A'}}</span></div>
                        <div class="node-amt" style="color: var(--cyan-glow);">${{n.amount}}</div>
                    </div>`;
            }} else if (n.type === 'lien') {{
                hasTerm = true;
                termGrid.innerHTML += `
                    <div class="node-card" style="border-color: var(--green-glow);">
                        <span class="node-badge" style="background: #059669;">🛡️ LIEN SECURED</span>
                        <div class="node-name">${{n.name}}</div>
                        <div class="node-row"><span>Frozen Account:</span><span>${{n.account}}</span></div>
                        <div class="node-amt" style="color: var(--green-glow);">${{n.amount}}</div>
                    </div>`;
            }} else if (n.type === 'atm') {{
                hasTerm = true;
                termGrid.innerHTML += `
                    <div class="node-card" style="border-color: #ef4444;">
                        <span class="node-badge" style="background: #dc2626;">🏧 ATM CASH-OUT</span>
                        <div class="node-name">${{n.name}}</div>
                        <div class="node-row"><span>Details:</span><span>${{n.details}}</span></div>
                        <div class="node-amt" style="color: #f87171;">${{n.amount}}</div>
                    </div>`;
            }}
        }});

        if (!hasL1) document.getElementById('layer1_container').style.display = 'none';
        if (!hasL2) document.getElementById('layer2_container').style.display = 'none';
        if (!hasTerm) document.getElementById('term_container').style.display = 'none';
    </script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(os.path.abspath(output_html)), exist_ok=True)
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ Dynamic HTML Visualizer Generated: {output_html}")
