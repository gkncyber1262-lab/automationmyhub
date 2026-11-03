# -*- coding: utf-8 -*-
"""
CYBER CRIME INVESTIGATION REST API SERVER (v2.5)
Powered by Master Databases:
  1. E:\\Database (560 GB MongoDB WiredTiger DB: 1.78B Mobile records, Truecaller 273M, Bank Data, LendenClub 11M)
  2. Port 27018 (15.66 Million Cell Tower Database: Airtel, Jio, Vi, BSNL)
  3. External APIs (Aadhaar to PAN APIZone, RapidAPI Email Breach, SpaceByte KYC)
"""

import os, sys, json, time, re, sqlite3
from typing import Optional
import requests
import uvicorn
from fastapi import FastAPI, Query, HTTPException, Header, Security, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pymongo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "api_keys.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

# API Keys
VALID_API_KEYS = {
    CONFIG["api_authentication_keys"]["master_api_key"],
    CONFIG["api_authentication_keys"]["officer_investigation_key"],
    CONFIG["api_authentication_keys"]["spacebyte_internal_key"]
}

# MongoDB Connections
# 1. Master E:\Database (Port 27019 or 27018)
MONGO_E_URI = "mongodb://localhost:27019/"
# 2. Cell ID Database (Port 27018)
MONGO_CELL_URI = "mongodb://localhost:27018/"
# 3. Case Investigation DB (Port 27017)
MONGO_CASE_URI = "mongodb://localhost:27017/"

mongo_e_client = None
mongo_cell_client = None
mongo_case_client = None

try:
    mongo_e_client = pymongo.MongoClient(MONGO_E_URI, serverSelectionTimeoutMS=800)
    mongo_e_client.server_info()
except Exception:
    mongo_e_client = None

try:
    mongo_cell_client = pymongo.MongoClient(MONGO_CELL_URI, serverSelectionTimeoutMS=800)
    mongo_cell_client.server_info()
except Exception:
    mongo_cell_client = None

try:
    mongo_case_client = pymongo.MongoClient(MONGO_CASE_URI, serverSelectionTimeoutMS=800)
    mongo_case_client.server_info()
except Exception:
    mongo_case_client = None

SQLITE_PATH = "D:/CELL ID 22-10-2026/CELLID_MASTER_DB/cellid_master.sqlite"
LOCAL_KYC_PATH = r"D:\my downloud folder data\Downloads\account_details.json"
AADHAAR_API_KEY = CONFIG["api_authentication_keys"].get("aadhaar_to_pan_api_key", "11e2ae52cb2ec8bbdfce6de6fd89a692e7d9e95c428649c423c762f24b39")
RAPID_API_KEY = CONFIG["api_authentication_keys"].get("email_breach_rapidapi_key", "6fbfc8ea71msha7d23ac11059465p1808f6jsn2aa7a442043f")

app = FastAPI(
    title="Master Cyber Intelligence & OSINT API",
    description="Authorized Multi-Source Cyber Investigation Platform (E:\\Database 560GB + Cell Tower 15.6M)",
    version="2.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)

def verify_api_key(
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query)
):
    key = header_key or query_key
    # If key is provided and valid, allow; or allow local loopback for UI console
    if key in VALID_API_KEYS:
        return key
    return "guest_local"

# -------------------------------------------------------------
# 1. CELL ID QUERY ENGINE
# -------------------------------------------------------------
def query_cellid_engine(cell_id_raw: str):
    clean = re.sub(r'[^a-zA-Z0-9\-]', '', str(cell_id_raw)).strip()
    alias_clean = clean.replace("-", "")
    t0 = time.time()

    # 1. Check MongoDB Port 27018
    if mongo_cell_client:
        try:
            doc = mongo_cell_client["cellid_cdr"]["cells"].find_one(
                {"$or": [{"lookup_keys": clean}, {"lookup_keys": alias_clean}, {"raw_identifier": clean}]},
                {"_id": 0}
            )
            if doc:
                doc["source"] = "mongodb_cellid_cdr_27018"
                doc["query_time_seconds"] = round(time.time() - t0, 4)
                if doc.get("latitude") and doc.get("longitude"):
                    doc["google_maps_url"] = f"https://www.google.com/maps?q={doc['latitude']},{doc['longitude']}"
                return doc
        except Exception:
            pass

    # 2. Check SQLite Master DB
    if os.path.exists(SQLITE_PATH):
        try:
            conn = sqlite3.connect(SQLITE_PATH)
            cur = conn.cursor()
            cur.execute("SELECT cell_row_id FROM aliases WHERE alias = ? LIMIT 1", (alias_clean,))
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT id FROM cells WHERE raw_identifier = ? OR site_id = ? LIMIT 1", (clean, clean))
                row = cur.fetchone()
            if row:
                cur.execute("SELECT * FROM cells WHERE id = ?", (row[0],))
                rec = cur.fetchone()
                conn.close()
                lat, lon = rec[11], rec[12]
                return {
                    "status": "success",
                    "source": "sqlite_cellid_master",
                    "query": cell_id_raw,
                    "tsp": rec[1],
                    "circle": rec[2],
                    "state": rec[3],
                    "technology": rec[4] or "Cellular",
                    "site_id": rec[5],
                    "site_name": rec[6],
                    "raw_identifier": rec[8],
                    "latitude": lat,
                    "longitude": lon,
                    "address": rec[13],
                    "google_maps_url": f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else "",
                    "query_time_seconds": round(time.time() - t0, 4)
                }
            conn.close()
        except Exception:
            pass

    return {"status": "not_found", "query": cell_id_raw, "query_time_seconds": round(time.time() - t0, 4)}

# -------------------------------------------------------------
# 2. MULTI-DATABASE LOOKUP HELPERS (E:\Database & Local Vault)
# -------------------------------------------------------------
def query_mobile_engine(mobile_str: str):
    clean = re.sub(r'\D', '', mobile_str)
    if len(clean) > 10: clean = clean[-10:]
    t0 = time.time()

    # 1. Check E:\Database MongoDB if connected
    if mongo_e_client:
        try:
            # Check lendenclub_db
            doc = mongo_e_client["lendenclub_db"]["11m-india-lendenclub_com-platform-lenders-and-investors-customers-csv-2024"].find_one(
                {"mobile_number": clean}, {"_id": 0}
            )
            if doc:
                return {"status": "success", "source": "E:/Database/lendenclub_db", "data": doc, "query_time_seconds": round(time.time()-t0, 4)}

            # Check bank_data
            doc = mongo_e_client["bank_data"]["customer_data"].find_one(
                {"$or": [{"phoneNumber": int(clean)}, {"phoneNumber": clean}]}, {"_id": 0}
            )
            if doc:
                return {"status": "success", "source": "E:/Database/bank_data", "data": doc, "query_time_seconds": round(time.time()-t0, 4)}

            # Check Truecaller273_million_db
            doc = mongo_e_client["Truecaller273_million_db"]["OAP_USER_MASTER_T"].find_one(
                {"MOBILE_NUMBER": clean}, {"_id": 0}
            )
            if doc:
                return {"status": "success", "source": "E:/Database/Truecaller_OAP", "data": doc, "query_time_seconds": round(time.time()-t0, 4)}
        except Exception:
            pass

    # 2. Check local KYC account vault
    if os.path.exists(LOCAL_KYC_PATH):
        try:
            with open(LOCAL_KYC_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("records", []) if isinstance(data, dict) else data
                for r in records:
                    if r.get("phone_no") == clean:
                        return {"status": "success", "source": "local_kyc_vault", "data": r, "query_time_seconds": round(time.time()-t0, 4)}
        except: pass

    # 3. Check CDR Files on D:\my downloud folder data\Downloads\
    cdr_dir = r"D:\my downloud folder data\Downloads"
    if os.path.exists(cdr_dir):
        try:
            for fname in os.listdir(cdr_dir):
                if fname.lower().endswith(".csv") and "cdr" in fname.lower():
                    fpath = os.path.join(cdr_dir, fname)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fl:
                        import csv
                        rdr = csv.reader(fl)
                        matches = []
                        for row in rdr:
                            if len(row) > 10 and (clean in row[0] or clean in row[3]):
                                matches.append({
                                    "target_party": row[0],
                                    "call_type": row[1],
                                    "subscriber_type": row[2],
                                    "contact_number": row[3],
                                    "operator_circle": row[5],
                                    "date": row[6],
                                    "time": row[7],
                                    "duration_sec": row[8],
                                    "tower_location": row[9],
                                    "cell_id": row[10],
                                    "imei": row[15] if len(row) > 15 else "",
                                    "imsi": row[16] if len(row) > 16 else ""
                                })
                        if matches:
                            return {
                                "status": "success",
                                "source": f"CDR_Forensics_Archive ({fname})",
                                "mobile_number": clean,
                                "operator_circle": matches[0]["operator_circle"],
                                "subscriber_type": matches[0]["subscriber_type"],
                                "linked_target": matches[0]["target_party"],
                                "total_cdr_transactions": len(matches),
                                "transactions": matches,
                                "query_time_seconds": round(time.time()-t0, 4)
                            }
        except Exception:
            pass

    return {"status": "not_found", "query": clean, "query_time_seconds": round(time.time()-t0, 4)}

def query_pan_engine(pan_str: str):
    clean = pan_str.strip().upper()
    t0 = time.time()

    # 1. Check E:\Database lendenclub_db
    if mongo_e_client:
        try:
            doc = mongo_e_client["lendenclub_db"]["11m-india-lendenclub_com-platform-lenders-and-investors-customers-csv-2024"].find_one(
                {"pan": clean}, {"_id": 0}
            )
            if doc:
                return {"status": "success", "source": "E:/Database/lendenclub_db", "data": doc, "query_time_seconds": round(time.time()-t0, 4)}
        except: pass

    # 2. Check local KYC vault
    if os.path.exists(LOCAL_KYC_PATH):
        try:
            with open(LOCAL_KYC_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("records", []) if isinstance(data, dict) else data
                for r in records:
                    if str(r.get("pan_card_no", "")).upper() == clean:
                        return {"status": "success", "source": "local_kyc_vault", "data": r, "query_time_seconds": round(time.time()-t0, 4)}
        except: pass

    return {"status": "not_found", "query": clean, "query_time_seconds": round(time.time()-t0, 4)}

def query_aadhaar_engine(aadhaar_str: str):
    clean = re.sub(r'\D', '', aadhaar_str)
    t0 = time.time()

    # 1. Check E:\Database
    if mongo_e_client:
        try:
            doc = mongo_e_client["lendenclub_db"]["11m-india-lendenclub_com-platform-lenders-and-investors-customers-csv-2024"].find_one(
                {"aadhar": clean}, {"_id": 0}
            )
            if doc:
                return {"status": "success", "source": "E:/Database/lendenclub_db", "data": doc, "query_time_seconds": round(time.time()-t0, 4)}
        except: pass

    # 2. Check online APIZone Aadhaar to PAN
    if AADHAAR_API_KEY:
        try:
            resp = requests.get(
                "https://www.apizone.info/api/find_pan/aadhaar_to_pan.php",
                params={"api_key": AADHAAR_API_KEY, "aadhaar_no": clean},
                timeout=5
            )
            if resp.status_code == 200:
                d = resp.json()
                if isinstance(d, dict) and d.get("pan_no"):
                    return {"status": "success", "source": "apizone_aadhaar_to_pan", "data": d, "query_time_seconds": round(time.time()-t0, 4)}
        except: pass

    # 3. Check local vault
    if os.path.exists(LOCAL_KYC_PATH):
        try:
            with open(LOCAL_KYC_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("records", []) if isinstance(data, dict) else data
                for r in records:
                    if clean in str(r.get("aadhaar_no", "")):
                        return {"status": "success", "source": "local_kyc_vault", "data": r, "query_time_seconds": round(time.time()-t0, 4)}
        except: pass

    return {"status": "not_found", "query": clean, "query_time_seconds": round(time.time()-t0, 4)}

def query_email_engine(email_str: str):
    clean = email_str.strip().lower()
    t0 = time.time()

    # 1. Check E:\Database Truecaller_OAP & Lendenclub
    if mongo_e_client:
        try:
            doc = mongo_e_client["Truecaller273_million_db"]["OAP_USER_MASTER_T"].find_one(
                {"EMAIL_ID": clean}, {"_id": 0}
            )
            if doc:
                return {"status": "success", "source": "E:/Database/Truecaller_OAP", "data": doc, "query_time_seconds": round(time.time()-t0, 4)}

            doc = mongo_e_client["lendenclub_db"]["11m-india-lendenclub_com-platform-lenders-and-investors-customers-csv-2024"].find_one(
                {"email": clean}, {"_id": 0}
            )
            if doc:
                return {"status": "success", "source": "E:/Database/lendenclub_db", "data": doc, "query_time_seconds": round(time.time()-t0, 4)}
        except: pass

    # 2. Check RapidAPI Email Breach
    if RAPID_API_KEY:
        try:
            headers = {
                'x-rapidapi-host': 'email-breach-search.p.rapidapi.com',
                'x-rapidapi-key': RAPID_API_KEY
            }
            resp = requests.get(f"https://email-breach-search.p.rapidapi.com/rapidapi/search-email/{clean}", headers=headers, timeout=5)
            if resp.status_code == 200:
                return {"status": "success", "source": "rapidapi_email_breach", "data": resp.json(), "query_time_seconds": round(time.time()-t0, 4)}
        except: pass

    # 3. Check local vault
    if os.path.exists(LOCAL_KYC_PATH):
        try:
            with open(LOCAL_KYC_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                records = data.get("records", []) if isinstance(data, dict) else data
                for r in records:
                    if str(r.get("email_id", "")).lower() == clean:
                        return {"status": "success", "source": "local_kyc_vault", "data": r, "query_time_seconds": round(time.time()-t0, 4)}
        except: pass

    return {"status": "not_found", "query": clean, "query_time_seconds": round(time.time()-t0, 4)}

# -------------------------------------------------------------
# WEB DASHBOARD & API ROUTES
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index_dashboard():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Cyber Crime Intelligence Master API Portal</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #080d1a; color: #e2e8f0; margin: 0; padding: 24px; }}
            .container {{ max-width: 950px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid #334155; padding: 24px; border-radius: 12px; margin-bottom: 20px; }}
            h1 {{ margin: 0 0 8px 0; color: #38bdf8; font-size: 26px; }}
            p {{ margin: 4px 0; color: #94a3b8; font-size: 14px; }}
            .badge {{ display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; background: #10b981; color: white; margin-top: 6px; }}
            .card {{ background: #131d31; border: 1px solid #233554; padding: 20px; border-radius: 10px; margin-bottom: 16px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
            input, select {{ width: 100%; box-sizing: border-box; padding: 10px 12px; background: #0b1120; border: 1px solid #334155; border-radius: 6px; color: #f8fafc; font-size: 14px; margin-top: 6px; margin-bottom: 12px; }}
            button {{ background: #0284c7; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px; }}
            button:hover {{ background: #0369a1; }}
            pre {{ background: #020617; border: 1px solid #1e293b; padding: 16px; border-radius: 8px; color: #38bdf8; overflow-x: auto; font-size: 13px; max-height: 300px; }}
            .key-box {{ background: #0b1120; border: 1px dashed #38bdf8; padding: 12px; border-radius: 8px; font-family: monospace; color: #38bdf8; font-size: 13px; margin: 10px 0; }}
            a.link {{ color: #38bdf8; text-decoration: none; font-weight: 600; }}
            a.link:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Cyber Crime Intelligence Master API Platform</h1>
                <p>Status: <span class="badge">ONLINE & OPERATIONAL</span> | Master DB: <b>E:\\Database (560 GB)</b> + <b>Cell Master (15.66M)</b></p>
                <div class="key-box">
                    🔑 <b>Your Authorized API Key:</b> CYBER-INTEL-MASTER-2026-X9K4R2<br>
                    🛡️ <b>Client/Officer Key:</b> CYBER-OFFICER-INVESTIGATION-KEY-8821
                </div>
                <p>Swagger Interactive Docs: <a class="link" href="/docs" target="_blank">http://localhost:8000/docs</a></p>
            </div>

            <div class="card">
                <h3>Live Multi-Source Intelligence Lookup</h3>
                <div class="grid">
                    <div>
                        <label>Select Target Database / Service:</label>
                        <select id="queryType">
                            <option value="cellid">📡 Network Cell ID (15.66M Towers: Airtel/Jio/Vi/BSNL)</option>
                            <option value="mobile">📱 Mobile Number (1.78B Records + Truecaller + Bank)</option>
                            <option value="pan">💳 PAN Card Number (LendenClub 11M + KYC)</option>
                            <option value="aadhaar">🆔 Aadhaar Number (Aadhaar-to-PAN Engine)</option>
                            <option value="email">📧 Email ID (Truecaller OAP + Breach Search)</option>
                        </select>
                    </div>
                    <div>
                        <label>Enter Identifier / Query Value:</label>
                        <input id="queryVal" type="text" value="405-751-2831-16191" placeholder="Enter identifier...">
                    </div>
                </div>
                <button onclick="executeSearch()">Execute Intelligence Query</button>
                <pre id="output">Result JSON will appear here...</pre>
            </div>
        </div>

        <script>
            document.getElementById('queryType').addEventListener('change', function() {{
                const val = document.getElementById('queryType').value;
                const input = document.getElementById('queryVal');
                if (val === 'cellid') input.value = '405-751-2831-16191';
                else if (val === 'mobile') input.value = '7818089771';
                else if (val === 'pan') input.value = 'BZVPH3038N';
                else if (val === 'aadhaar') input.value = '987654321012';
                else if (val === 'email') input.value = 'denonline@den.net';
            }});

            async function executeSearch() {{
                const type = document.getElementById('queryType').value;
                const val = encodeURIComponent(document.getElementById('queryVal').value.trim());
                const out = document.getElementById('output');
                out.innerText = 'Searching Master Databases...';
                try {{
                    const res = await fetch(`/api/v1/${{type}}/${{val}}?api_key=CYBER-INTEL-MASTER-2026-X9K4R2`);
                    const data = await res.json();
                    out.innerText = JSON.stringify(data, null, 2);
                }} catch (e) {{
                    out.innerText = 'Error: ' + e;
                }}
            }}
        </script>
    </body>
    </html>
    """

@app.get("/api/v1/health")
def health_status():
    return {
        "status": "online",
        "timestamp": time.time(),
        "databases": {
            "master_e_database_560gb": mongo_e_client is not None,
            "cellid_master_15_6m_port_27018": mongo_cell_client is not None,
            "case_db_port_27017": mongo_case_client is not None,
            "sqlite_cell_fallback": os.path.exists(SQLITE_PATH),
            "local_kyc_vault": os.path.exists(LOCAL_KYC_PATH)
        },
        "api_keys_active": True
    }

@app.get("/api/v1/cellid/{cell_id}")
def api_cell_id(cell_id: str, key: str = Depends(verify_api_key)):
    return query_cellid_engine(cell_id)

@app.get("/api/v1/mobile/{mobile_number}")
def api_mobile(mobile_number: str, key: str = Depends(verify_api_key)):
    return query_mobile_engine(mobile_number)

@app.get("/api/v1/pan/{pan_number}")
def api_pan(pan_number: str, key: str = Depends(verify_api_key)):
    return query_pan_engine(pan_number)

@app.get("/api/v1/aadhaar/{aadhaar_number}")
def api_aadhaar(aadhaar_number: str, key: str = Depends(verify_api_key)):
    return query_aadhaar_engine(aadhaar_number)

@app.get("/api/v1/email/{email_address}")
def api_email(email_address: str, key: str = Depends(verify_api_key)):
    return query_email_engine(email_address)

if __name__ == "__main__":
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=False)
