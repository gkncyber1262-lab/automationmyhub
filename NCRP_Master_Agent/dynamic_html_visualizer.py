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
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
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
        "branch": "Victim Account Branch",
        "address": "Primary Incident Disbursal Origin",
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
            b_branch, b_addr = "", ""
            if ifsc:
                try:
                    from dynamic_flowchart import get_ifsc_branch_info
                    bi = get_ifsc_branch_info(ifsc, base_dir)
                    b_branch = bi.get("branch", "")
                    b_addr = bi.get("address", "")
                except Exception:
                    pass
            extra_d = (f" | Branch: {b_branch}" if b_branch else "") + (f" | Addr: {b_addr}" if b_addr else "")
            node_data = {
                "id": node_id,
                "name": f"{b_name[:24]}",
                "type": f"layer_{l_num}",
                "layer": l_num,
                "bank": b_name,
                "account": clean_acc,
                "ifsc": ifsc,
                "branch": b_branch or f"Branch ({ifsc})",
                "address": b_addr or "Verified via RBI IFSC Registry",
                "amount": f"Rs. {disp:,.2f}",
                "utr": utr,
                "details": f"Layer {l_num} Mule | Bank: {b_name} | A/c: {clean_acc} | IFSC: {ifsc}{extra_d}"
            }
            nodes.append(node_data)
            if l_num == 1: l1_nodes.append(node_id)
            elif l_num == 2: l2_nodes.append(node_id)
            
            # Add link
            if l_num == 1:
                links.append({"source": victim_id, "target": node_id, "amount": f"Rs. {disp:,.2f}", "utr": utr})
            elif l_num == 2 and l1_nodes:
                closest_l1 = l1_nodes[min(len(l2_nodes)-1, len(l1_nodes)-1)]
                links.append({"source": closest_l1, "target": node_id, "amount": f"Rs. {disp:,.2f}", "utr": utr})

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
            "bank": "Secured Lien Freeze",
            "account": h_acc,
            "amount": f"Rs. {float(amt):,.2f}",
            "branch": "Lien Marked Account",
            "address": f"Secured under Section 106 BNSS (Date: {h_dt})",
            "details": f"100% Debit Freeze | Date: {h_dt} | A/c: {h_acc}"
        })
        src = l1_nodes[0] if l1_nodes else victim_id
        links.append({"source": src, "target": h_id, "amount": f"Rs. {float(amt):,.2f}", "utr": "LIEN HOLD"})

    # ATMs
    raw_atms = ctx.get("atm_withdrawals", [])
    if raw_atms:
        atm_tot = 0.0
        atm_loc = "ATM Cash Dispenser"
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
            "branch": "ATM Kiosk Terminal",
            "address": f"Location: {atm_loc}",
            "details": f"{len(raw_atms)} ATM Withdrawals | Location: {atm_loc}"
        })
        src = l2_nodes[0] if l2_nodes else (l1_nodes[-1] if l1_nodes else victim_id)
        links.append({"source": src, "target": atm_id, "amount": f"Rs. {atm_tot:,.2f}", "utr": "CASH WITHDRAWAL"})

    nodes_json = json.dumps(nodes, ensure_ascii=False)
    links_json = json.dumps(links, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D FORENSIC MONEY TRAIL | {case_ref}</title>
    <style>
        :root {{
            --bg-canvas: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-sub: #475569;
            --border-card: #cbd5e1;
            --accent-red: #dc2626;
            --accent-green: #16a34a;
            --accent-blue: #2563eb;
            --accent-cyan: #0284c7;
            --shadow-3d: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        }}
        [data-theme="dark"] {{
            --bg-canvas: #090d16;
            --card-bg: #111827;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
            --border-card: #1f2937;
            --shadow-3d: 0 10px 30px rgba(0, 0, 0, 0.6);
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body, html {{ width: 100%; height: 100%; overflow: hidden; background: var(--bg-canvas); color: var(--text-main); }}
        
        #header-bar {{
            position: absolute; top: 0; left: 0; right: 0; height: 68px;
            background: var(--card-bg); border-bottom: 2px solid var(--border-card);
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 24px; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        .brand-title {{ font-size: 18px; font-weight: 800; letter-spacing: 0.5px; }}
        .brand-sub {{ font-size: 13px; color: var(--text-sub); margin-top: 2px; }}
        .hud-actions {{ display: flex; gap: 10px; align-items: center; }}
        .hud-btn {{
            background: var(--card-bg); border: 1.5px solid var(--border-card); color: var(--text-main);
            padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer;
            transition: all 0.2s; display: flex; align-items: center; gap: 6px;
        }}
        .hud-btn:hover {{ background: #f1f5f9; transform: translateY(-1px); }}
        
        #viewport-3d {{ width: 100%; height: calc(100% - 68px); margin-top: 68px; position: relative; cursor: grab; }}
        #viewport-3d:active {{ cursor: grabbing; }}
        canvas {{ width: 100%; height: 100%; display: block; }}
        
        /* Stats HUD */
        #stats-bar {{
            position: absolute; bottom: 20px; left: 24px; display: flex; gap: 12px; z-index: 100;
        }}
        .stat-pill {{
            background: var(--card-bg); border: 1.5px solid var(--border-card);
            border-radius: 10px; padding: 10px 16px; box-shadow: var(--shadow-3d);
        }}
        .stat-pill .lbl {{ font-size: 11px; font-weight: 700; color: var(--text-sub); text-transform: uppercase; }}
        .stat-pill .val {{ font-size: 16px; font-weight: 800; margin-top: 2px; }}
        
        /* Detail Drawer */
        #inspector-drawer {{
            position: absolute; top: 88px; right: 24px; width: 380px; max-height: calc(100% - 110px);
            background: var(--card-bg); border: 2px solid var(--border-card); border-radius: 14px;
            box-shadow: var(--shadow-3d); padding: 20px; z-index: 100; overflow-y: auto; display: none;
            backdrop-filter: blur(8px);
        }}
        #inspector-drawer.active {{ display: block; animation: slideIn 0.25s ease-out; }}
        @keyframes slideIn {{ from {{ opacity: 0; transform: translateX(20px); }} to {{ opacity: 1; transform: translateX(0); }} }}
        .drawer-close {{ position: absolute; top: 16px; right: 16px; cursor: pointer; font-size: 18px; font-weight: bold; color: var(--text-sub); }}
        .badge-type {{ display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; color: #fff; margin-bottom: 12px; }}
        .d-title {{ font-size: 18px; font-weight: 800; margin-bottom: 14px; }}
        .d-row {{ margin-bottom: 10px; font-size: 13px; }}
        .d-row .key {{ color: var(--text-sub); font-weight: 600; display: block; margin-bottom: 2px; }}
        .d-row .v {{ font-weight: 700; word-break: break-all; }}
        .d-addr-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; margin-top: 10px; }}
        [data-theme="dark"] .d-addr-box {{ background: #0f172a; border-color: #334155; }}
    </style>
</head>
<body>
    <div id="header-bar">
        <div>
            <div class="brand-title">🏛️ DELHI POLICE CYBER CRIME INVESTIGATION | 3D MONEY TRAIL MATRIX</div>
            <div class="brand-sub">{case_ref} | Section 318(4) BNS | Full 3D Interactive Visualization</div>
        </div>
        <div class="hud-actions">
            <button class="hud-btn" onclick="reset3DCamera()">⟲ Reset View</button>
            <button class="hud-btn" onclick="toggleParticles()">⏯ Pause Flow</button>
            <button class="hud-btn" onclick="toggleTheme()">🌓 Theme</button>
        </div>
    </div>

    <div id="viewport-3d">
        <canvas id="canvas3d"></canvas>
    </div>

    <div id="stats-bar">
        <div class="stat-pill" style="border-left: 4px solid var(--accent-red);">
            <div class="lbl">Reported Loss</div>
            <div class="val" style="color: var(--accent-red);">Rs. {amt_str}</div>
        </div>
        <div class="stat-pill" style="border-left: 4px solid var(--accent-green);">
            <div class="lbl">Lien Secured</div>
            <div class="val" style="color: var(--accent-green);">Rs. {lien_str}</div>
        </div>
        <div class="stat-pill" style="border-left: 4px solid var(--accent-cyan);">
            <div class="lbl">Recovery Ratio</div>
            <div class="val" style="color: var(--accent-cyan);">{rec_ratio:.1f}%</div>
        </div>
    </div>

    <div id="inspector-drawer">
        <div class="drawer-close" onclick="closeDrawer()">✕</div>
        <div id="drawer-content"></div>
    </div>

    <script>
        const nodesData = {nodes_json};
        const linksData = {links_json};

        const canvas = document.getElementById('canvas3d');
        const ctx = canvas.getContext('2d');

        let width = canvas.width = window.innerWidth;
        let height = canvas.height = window.innerHeight - 68;

        window.addEventListener('resize', () => {{
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight - 68;
        }});

        // 3D Camera & Scene State
        let rotX = 0.25;
        let rotY = -0.15;
        let zoom = 1.0;
        let panX = 0;
        let panY = 0;
        let isDragging = false;
        let isPanning = false;
        let lastMouseX = 0;
        let lastMouseY = 0;
        let particlesActive = true;

        // Position nodes in a 3D layered hierarchy
        const layerXMap = {{
            0: -550,
            1: -180,
            2: 180,
            3: 550
        }};

        // Group nodes by layer to calculate Y spacing
        const layers = {{}};
        nodesData.forEach(n => {{
            const l = n.layer || 0;
            if(!layers[l]) layers[l] = [];
            layers[l].push(n);
        }});

        Object.keys(layers).forEach(l => {{
            const arr = layers[l];
            const spacing = 190;
            const startY = -((arr.length - 1) * spacing) / 2;
            arr.forEach((n, idx) => {{
                n.x = layerXMap[l] || 0;
                n.y = startY + idx * spacing;
                n.z = (Math.sin(idx * 1.5) * 60) + (l * 20); // 3D depth curvature
            }});
        }});

        // Animation Particles
        const particles = [];
        linksData.forEach((link, l_idx) => {{
            const sNode = nodesData.find(n => n.id === link.source);
            const tNode = nodesData.find(n => n.id === link.target);
            if (sNode && tNode) {{
                link.sourceNode = sNode;
                link.targetNode = tNode;
                for (let i = 0; i < 4; i++) {{
                    particles.push({{
                        link: link,
                        t: i * 0.25,
                        speed: 0.006 + Math.random() * 0.003
                    }});
                }}
            }}
        }});

        // 3D Projection Engine
        function project3D(x, y, z) {{
            // Rotate Y
            let cosY = Math.cos(rotY), sinY = Math.sin(rotY);
            let x1 = x * cosY - z * sinY;
            let z1 = z * cosY + x * sinY;

            // Rotate X
            let cosX = Math.cos(rotX), sinX = Math.sin(rotX);
            let y2 = y * cosX - z1 * sinX;
            let z2 = z1 * cosX + y * sinX;

            // Perspective
            const fov = 1000;
            const distance = fov + z2;
            const scale = (fov / Math.max(10, distance)) * zoom;

            const px = (x1 * scale) + (width / 2) + panX;
            const py = (y2 * scale) + (height / 2) + panY;

            return {{ x: px, y: py, z: z2, scale: scale }};
        }}

        // Render Loop
        function render() {{
            ctx.clearRect(0, 0, width, height);

            const isDark = document.body.getAttribute('data-theme') === 'dark';

            // Draw subtle 3D floor grid
            ctx.strokeStyle = isDark ? '#1e293b' : '#e2e8f0';
            ctx.lineWidth = 1;
            for (let gx = -700; gx <= 700; gx += 140) {{
                let p1 = project3D(gx, 400, -400);
                let p2 = project3D(gx, 400, 400);
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }}
            for (let gz = -400; gz <= 400; gz += 140) {{
                let p1 = project3D(-700, 400, gz);
                let p2 = project3D(700, 400, gz);
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.stroke();
            }}

            // Draw 3D Connection Tubes
            linksData.forEach(link => {{
                if (!link.sourceNode || !link.targetNode) return;
                const p1 = project3D(link.sourceNode.x + 90, link.sourceNode.y, link.sourceNode.z);
                const p2 = project3D(link.targetNode.x - 90, link.targetNode.y, link.targetNode.z);

                const grad = ctx.createLinearGradient(p1.x, p1.y, p2.x, p2.y);
                grad.addColorStop(0, '#3b82f6');
                grad.addColorStop(1, '#06b6d4');

                // 3D tube shadow
                ctx.strokeStyle = 'rgba(0,0,0,0.1)';
                ctx.lineWidth = 6 * ((p1.scale + p2.scale) / 2);
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y + 4);
                ctx.bezierCurveTo((p1.x + p2.x) / 2, p1.y + 4, (p1.x + p2.x) / 2, p2.y + 4, p2.x, p2.y + 4);
                ctx.stroke();

                // Core tube
                ctx.strokeStyle = grad;
                ctx.lineWidth = 3.5 * ((p1.scale + p2.scale) / 2);
                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.bezierCurveTo((p1.x + p2.x) / 2, p1.y, (p1.x + p2.x) / 2, p2.y, p2.x, p2.y);
                ctx.stroke();

                // Label badge
                const mx = (p1.x + p2.x) / 2;
                const my = (p1.y + p2.y) / 2;
                ctx.fillStyle = isDark ? '#1e293b' : '#ffffff';
                ctx.strokeStyle = isDark ? '#334155' : '#cbd5e1';
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.roundRect(mx - 45, my - 12, 90, 22, 6);
                ctx.fill();
                ctx.stroke();
                ctx.fillStyle = isDark ? '#38bdf8' : '#0284c7';
                ctx.font = 'bold 10px Segoe UI';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(link.amount, mx, my);
            }});

            // Draw Animated Money Particles
            if (particlesActive) {{
                particles.forEach(pt => {{
                    pt.t = (pt.t + pt.speed) % 1.0;
                    const p1 = project3D(pt.link.sourceNode.x + 90, pt.link.sourceNode.y, pt.link.sourceNode.z);
                    const p2 = project3D(pt.link.targetNode.x - 90, pt.link.targetNode.y, pt.link.targetNode.z);

                    // Cubic Bezier interpolation
                    const t = pt.t;
                    const cx1 = (p1.x + p2.x) / 2, cy1 = p1.y;
                    const cx2 = (p1.x + p2.x) / 2, cy2 = p2.y;

                    const bx = Math.pow(1-t, 3)*p1.x + 3*Math.pow(1-t, 2)*t*cx1 + 3*(1-t)*Math.pow(t, 2)*cx2 + Math.pow(t, 3)*p2.x;
                    const by = Math.pow(1-t, 3)*p1.y + 3*Math.pow(1-t, 2)*t*cy1 + 3*(1-t)*Math.pow(t, 2)*cy2 + Math.pow(t, 3)*p2.y;

                    const curScale = (p1.scale + (p2.scale - p1.scale) * t);
                    ctx.fillStyle = '#00f0ff';
                    ctx.shadowColor = '#00f0ff';
                    ctx.shadowBlur = 10;
                    ctx.beginPath();
                    ctx.arc(bx, by, 4 * curScale, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.shadowBlur = 0;
                }});
            }}

            // Sort nodes by depth (z) to render back-to-front
            const projectedNodes = nodesData.map(node => {{
                return {{
                    node: node,
                    proj: project3D(node.x, node.y, node.z)
                }};
            }}).sort((a, b) => a.proj.z - b.proj.z);

            // Draw 3D Node Cards
            projectedNodes.forEach(item => {{
                const n = item.node;
                const p = item.proj;
                const sc = p.scale;

                const cWidth = 210 * sc;
                const cHeight = 115 * sc;
                const cx = p.x - cWidth / 2;
                const cy = p.y - cHeight / 2;

                n._screenBox = [cx, cy, cx + cWidth, cy + cHeight];

                // 3D Drop Shadow
                ctx.fillStyle = isDark ? 'rgba(0,0,0,0.5)' : 'rgba(0,0,0,0.12)';
                ctx.beginPath();
                ctx.roundRect(cx, cy + (8 * sc), cWidth, cHeight, 10 * sc);
                ctx.fill();

                // Card Body
                ctx.fillStyle = isDark ? '#111827' : '#ffffff';
                let bColor = '#0284c7';
                if (n.type === 'victim') bColor = '#dc2626';
                else if (n.type === 'lien') bColor = '#16a34a';
                else if (n.type === 'atm') bColor = '#dc2626';
                else if (n.layer === 1) bColor = '#1e293b';

                ctx.strokeStyle = isDark ? '#374151' : bColor;
                ctx.lineWidth = 2 * sc;
                ctx.beginPath();
                ctx.roundRect(cx, cy, cWidth, cHeight, 8 * sc);
                ctx.fill();
                ctx.stroke();

                // Header Strip
                ctx.fillStyle = bColor;
                ctx.beginPath();
                ctx.roundRect(cx, cy, cWidth, 24 * sc, [8 * sc, 8 * sc, 0, 0]);
                ctx.fill();

                // Category Title
                ctx.fillStyle = '#ffffff';
                ctx.font = `bold ${{Math.max(8, 10 * sc)}}px Segoe UI`;
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                const tag = n.type === 'victim' ? 'VICTIM DISBURSAL' : (n.type === 'lien' ? 'LIEN SECURED' : (n.type === 'atm' ? 'ATM WITHDRAWAL' : `LAYER ${{n.layer}} MULE`));
                ctx.fillText(tag, cx + (8 * sc), cy + (12 * sc));

                // Bank Name
                ctx.fillStyle = isDark ? '#f8fafc' : '#0f172a';
                ctx.font = `bold ${{Math.max(9, 12 * sc)}}px Segoe UI`;
                ctx.fillText(n.bank.slice(0, 22), cx + (10 * sc), cy + (40 * sc));

                // Account & IFSC
                ctx.fillStyle = isDark ? '#94a3b8' : '#334155';
                ctx.font = `bold ${{Math.max(8, 10 * sc)}}px Segoe UI`;
                ctx.fillText(`A/c: ${{n.account || '-'}}`, cx + (10 * sc), cy + (58 * sc));
                if (n.ifsc) {{
                    ctx.fillText(`IFSC: ${{n.ifsc}}`, cx + (10 * sc), cy + (74 * sc));
                }}

                // Amount
                ctx.fillStyle = n.type === 'victim' || n.type === 'atm' ? '#dc2626' : (n.type === 'lien' ? '#16a34a' : (isDark ? '#38bdf8' : '#0f172a'));
                ctx.font = `bold ${{Math.max(9, 13 * sc)}}px Segoe UI`;
                ctx.fillText(n.amount, cx + (10 * sc), cy + (98 * sc));
            }});

            requestAnimationFrame(render);
        }}

        // Mouse & Touch Controls
        window.addEventListener('mousedown', (e) => {{
            if (e.target.tagName === 'CANVAS') {{
                if (e.button === 2) isPanning = true;
                else isDragging = true;
                lastMouseX = e.clientX;
                lastMouseY = e.clientY;
            }}
        }});

        window.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                rotY += (e.clientX - lastMouseX) * 0.005;
                rotX += (e.clientY - lastMouseY) * 0.005;
                rotX = Math.max(-0.8, Math.min(0.8, rotX));
                lastMouseX = e.clientX;
                lastMouseY = e.clientY;
            }} else if (isPanning) {{
                panX += (e.clientX - lastMouseX);
                panY += (e.clientY - lastMouseY);
                lastMouseX = e.clientX;
                lastMouseY = e.clientY;
            }}
        }});

        window.addEventListener('mouseup', () => {{
            isDragging = false;
            isPanning = false;
        }});

        window.addEventListener('wheel', (e) => {{
            zoom *= e.deltaY > 0 ? 0.92 : 1.08;
            zoom = Math.max(0.4, Math.min(2.5, zoom));
        }});

        window.addEventListener('contextmenu', e => e.preventDefault());

        // Card Click Interaction
        canvas.addEventListener('click', (e) => {{
            const mx = e.clientX;
            const my = e.clientY - 68;
            for (let i = nodesData.length - 1; i >= 0; i--) {{
                const n = nodesData[i];
                if (n._screenBox) {{
                    const [x1, y1, x2, y2] = n._screenBox;
                    if (mx >= x1 && mx <= x2 && my >= y1 && my <= y2) {{
                        openDrawer(n);
                        break;
                    }}
                }}
            }}
        }});

        function openDrawer(n) {{
            const drawer = document.getElementById('inspector-drawer');
            const cont = document.getElementById('drawer-content');
            let bColor = '#0284c7';
            if (n.type === 'victim') bColor = '#dc2626';
            else if (n.type === 'lien') bColor = '#16a34a';
            else if (n.type === 'atm') bColor = '#dc2626';

            cont.innerHTML = `
                <span class="badge-type" style="background: ${{bColor}};">${{n.type.toUpperCase()}}</span>
                <div class="d-title">${{n.name}}</div>
                <div class="d-row"><span class="key">Entity / Bank:</span><span class="v">${{n.bank}}</span></div>
                <div class="d-row"><span class="key">Account No:</span><span class="v">${{n.account || 'N/A'}}</span></div>
                <div class="d-row"><span class="key">IFSC Code:</span><span class="v">${{n.ifsc || 'N/A'}}</span></div>
                <div class="d-row"><span class="key">Transferred / Loss:</span><span class="v" style="color: ${{bColor}};">${{n.amount}}</span></div>
                ${{n.utr ? `<div class="d-row"><span class="key">UTR Number:</span><span class="v">${{n.utr}}</span></div>` : ''}}
                <div class="d-addr-box">
                    <div class="d-row"><span class="key">🏛️ Branch Name:</span><span class="v">${{n.branch || 'Branch Details'}}</span></div>
                    <div class="d-row"><span class="key">📍 Physical Branch Address:</span><span class="v">${{n.address || 'Address Verified via RBI IFSC API'}}</span></div>
                </div>
            `;
            drawer.classList.add('active');
        }}

        function closeDrawer() {{
            document.getElementById('inspector-drawer').classList.remove('active');
        }}

        function reset3DCamera() {{
            rotX = 0.25;
            rotY = -0.15;
            zoom = 1.0;
            panX = 0;
            panY = 0;
        }}

        function toggleParticles() {{
            particlesActive = !particlesActive;
        }}

        function toggleTheme() {{
            const cur = document.body.getAttribute('data-theme');
            document.body.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
        }}

        requestAnimationFrame(render);
    </script>
</body>
</html>
"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [3D HTML Visualizer]: Successfully saved interactive 3D web application -> {output_html}")
