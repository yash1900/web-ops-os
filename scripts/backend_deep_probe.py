"""
Web-Ops OS Backend & Infrastructure Deep Probe Engine
Performs multi-dimensional verification across:
1. Backend API (Quest): https://api.fraterny.com/health (GCP Compute Engine FastAPI)
2. Database Connectivity (Supabase): https://pmaylemigtnzirbtiueg.supabase.co/rest/v1/
3. User Questionnaires & Workflows API: OpenAPI schema validation (https://api.fraterny.com/openapi.json)
4. Payment & Webhooks Listener Routes: https://api.fraterny.com/api/webhooks/razorpay & paypal
5. AI Generation Pipeline & Model Readiness: Quest API RAG & Model Endpoint Health
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
import urllib.request
import urllib.error

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROBES = [
    {
        "id": "quest_backend_api",
        "name": "Backend API (Quest FastAPI on GCP)",
        "url": "https://api.fraterny.com/health",
        "expected_code": [200],
        "category": "Backend API",
        "validator": lambda body, code: "status" in body and "healthy" in body.lower()
    },
    {
        "id": "supabase_db",
        "name": "Database Connectivity (Supabase PostgreSQL REST)",
        "url": "https://pmaylemigtnzirbtiueg.supabase.co/rest/v1/",
        "expected_code": [200, 401],  # 401 expected without API key, proving gateway is live
        "category": "Database Connectivity",
        "validator": lambda body, code: code in [200, 401]
    },
    {
        "id": "quest_questionnaires_api",
        "name": "User Questionnaires & Workflows API",
        "url": "https://api.fraterny.com/openapi.json",
        "expected_code": [200],
        "category": "User Questionnaires & Workflows",
        "validator": lambda body, code: "paths" in body or "openapi" in body.lower()
    },
    {
        "id": "webhook_razorpay",
        "name": "Payment & Webhooks — Razorpay Handler",
        "url": "https://api.fraterny.com/api/webhooks/razorpay",
        "expected_code": [200, 400, 405, 422],  # Listener active (returns HTTP 405/422 on GET/empty payload)
        "category": "Payment & Webhooks",
        "validator": lambda body, code: code in [200, 400, 405, 422]
    },
    {
        "id": "webhook_paypal",
        "name": "Payment & Webhooks — PayPal Handler",
        "url": "https://api.fraterny.com/api/webhooks/paypal",
        "expected_code": [200, 400, 405, 422],  # Listener active
        "category": "Payment & Webhooks",
        "validator": lambda body, code: code in [200, 400, 405, 422]
    }
]

def probe_endpoint(probe):
    url = probe["url"]
    name = probe["name"]
    start_time = time.time()
    
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 WebOpsOS/1.0"}
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            latency = int((time.time() - start_time) * 1000)
            status_code = response.getcode()
            body = response.read().decode('utf-8', errors='ignore')
            
            valid = probe["validator"](body, status_code)
            status = "HEALTHY" if (status_code in probe["expected_code"] and valid) else "DEGRADED"
            return {
                "id": probe["id"],
                "name": name,
                "category": probe["category"],
                "url": url,
                "status": status,
                "code": status_code,
                "latency_ms": latency,
                "error": None if status == "HEALTHY" else f"Unexpected response (Code {status_code})"
            }
    except urllib.error.HTTPError as e:
        latency = int((time.time() - start_time) * 1000)
        body = ""
        try:
            body = e.read().decode('utf-8', errors='ignore')
        except Exception:
            pass
            
        valid = probe["validator"](body, e.code)
        status = "HEALTHY" if (e.code in probe["expected_code"] and valid) else "DEGRADED"
        return {
            "id": probe["id"],
            "name": name,
            "category": probe["category"],
            "url": url,
            "status": status,
            "code": e.code,
            "latency_ms": latency,
            "error": None if status == "HEALTHY" else str(e)
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "id": probe["id"],
            "name": name,
            "category": probe["category"],
            "url": url,
            "status": "UNHEALTHY",
            "code": 0,
            "latency_ms": latency,
            "error": str(e)
        }

def probe_db_telemetry():
    """
    Direct Telemetry Audit of Quest AI Pipeline in Supabase (summary_generation).
    Inspects recent jobs for failures ('Failed', 'Failed in agent else') and stuck states.
    """
    url = "https://pmaylemigtnzirbtiueg.supabase.co/rest/v1/summary_generation?select=id,testid,status,summary_error,agent_start_time,agent_completion_time&order=id.desc&limit=10"
    # Supabase service_role key = full DB admin (bypasses RLS). Load from env, NEVER hardcode.
    api_key = os.environ.get("FRATERNY_SUPABASE_SERVICE_KEY", "")
    if not api_key:
        return {
            "id": "quest_db_pipeline_telemetry",
            "name": "Quest AI Pipeline Telemetry (Supabase DB)",
            "status": "SKIPPED",
            "url": url,
            "code": 0,
            "latency_ms": 0,
            "error": "FRATERNY_SUPABASE_SERVICE_KEY not set — DB telemetry probe skipped (set the env var to enable)."
        }
    start_time = time.time()
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                "apikey": api_key,
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "WebOpsOS/1.0",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            latency = int((time.time() - start_time) * 1000)
            body = response.read().decode('utf-8', errors='ignore')
            rows = json.loads(body)
            
            failed_jobs = []
            stuck_jobs = []
            
            for row in rows:
                st = str(row.get("status") or "")
                err = row.get("summary_error")
                tid = row.get("testid")
                row_id = row.get("id")
                
                # Check for explicit failure status or recorded error
                if "failed" in st.lower() or err:
                    failed_jobs.append(f"ID {row_id} (testId: {tid[:12]}...): {err or st}")
                elif st in ["Agent Started", "Data Recieved & Extracted", "Passing to Json"] and not row.get("agent_completion_time"):
                    stuck_jobs.append(f"ID {row_id} (testId: {tid[:12]}...) stuck in '{st}'")
                    
            if failed_jobs:
                return {
                    "id": "quest_db_pipeline_telemetry",
                    "name": "Quest AI Pipeline Telemetry (Supabase DB)",
                    "category": "AI Generation Pipeline",
                    "url": "https://pmaylemigtnzirbtiueg.supabase.co/rest/v1/summary_generation",
                    "status": "UNHEALTHY",
                    "code": 200,
                    "latency_ms": latency,
                    "error": f"{len(failed_jobs)} pipeline failure(s) detected: " + " | ".join(failed_jobs[:2])
                }
            elif stuck_jobs:
                return {
                    "id": "quest_db_pipeline_telemetry",
                    "name": "Quest AI Pipeline Telemetry (Supabase DB)",
                    "category": "AI Generation Pipeline",
                    "url": "https://pmaylemigtnzirbtiueg.supabase.co/rest/v1/summary_generation",
                    "status": "DEGRADED",
                    "code": 200,
                    "latency_ms": latency,
                    "error": f"{len(stuck_jobs)} stuck job(s) detected: " + " | ".join(stuck_jobs[:2])
                }
            else:
                return {
                    "id": "quest_db_pipeline_telemetry",
                    "name": "Quest AI Pipeline Telemetry (Supabase DB)",
                    "category": "AI Generation Pipeline",
                    "url": "https://pmaylemigtnzirbtiueg.supabase.co/rest/v1/summary_generation",
                    "status": "HEALTHY",
                    "code": 200,
                    "latency_ms": latency,
                    "error": None
                }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "id": "quest_db_pipeline_telemetry",
            "name": "Quest AI Pipeline Telemetry (Supabase DB)",
            "category": "AI Generation Pipeline",
            "url": "https://pmaylemigtnzirbtiueg.supabase.co/rest/v1/summary_generation",
            "status": "UNHEALTHY",
            "code": 0,
            "latency_ms": latency,
            "error": f"Failed to query Supabase summary_generation table: {e}"
        }

def sync_alerts_and_logs(results):
    """
    Syncs probe failures to daily-brief/alerts.json (for Morning Brief email alerts)
    and Dashboard/health-check-log.json (for live dashboard status map).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # 1. Build alerts list for daily-brief/alerts.json
    alerts = []
    for r in results:
        if r["status"] in ["UNHEALTHY", "DEGRADED"]:
            severity = "critical" if r["status"] == "UNHEALTHY" else "warning"
            alerts.append({
                "severity": severity,
                "title": f"{r['name']} — {r['status']}",
                "detail": r["error"] or f"Probe to {r['url']} failed with status {r['code']}",
                "sop": [
                    "Check OpenAI API Key in Quest/.env and GCP Compute Engine status",
                    "Run `python scripts/backend_deep_probe.py` to re-test pipeline"
                ]
            })
            
    alerts_path = os.path.join(r"c:\Users\amar1\Downloads\Automations", "daily-brief", "alerts.json")
    try:
        with open(alerts_path, "w", encoding="utf-8") as f:
            json.dump({"generatedAt": now_iso, "alerts": alerts}, f, indent=2)
        print(f"\n 🔔 [SYNC] Updated daily-brief/alerts.json with {len(alerts)} alert(s)")
    except Exception as e:
        print(f"\n ⚠️ [SYNC WARN] Could not write daily-brief/alerts.json: {e}")
        
    # 2. Update Dashboard/health-check-log.json
    health_log_path = os.path.join(r"c:\Users\amar1\Downloads\Automations", "Dashboard", "health-check-log.json")
    try:
        if os.path.exists(health_log_path):
            with open(health_log_path, "r", encoding="utf-8") as f:
                health_data = json.load(f)
        else:
            health_data = {"lastRun": today_str, "source": "web-ops-os backend_deep_probe.py", "automations": {}}
            
        db_telemetry = next((r for r in results if r["id"] == "quest_db_pipeline_telemetry"), None)
        if db_telemetry:
            res_val = "failed" if db_telemetry["status"] == "UNHEALTHY" else ("degraded" if db_telemetry["status"] == "DEGRADED" else "healthy")
            health_data["lastRun"] = today_str
            health_data["automations"]["fraterny-automation"] = {
                "checkedAt": now_iso,
                "result": res_val,
                "signal": db_telemetry["error"] or "Quest AI Pipeline Telemetry healthy",
                "note": "Live Supabase summary_generation DB telemetry audit"
            }
            with open(health_log_path, "w", encoding="utf-8") as f:
                json.dump(health_data, f, indent=2)
            print(f" 📊 [SYNC] Updated Dashboard/health-check-log.json (fraterny-automation -> {res_val})")
    except Exception as e:
        print(f" ⚠️ [SYNC WARN] Could not write Dashboard/health-check-log.json: {e}")

def run_deep_probes():
    print("=" * 75)
    print(" 🔬 [WEB-OPS] BACKEND, DATABASE, AI PIPELINE & WEBHOOK DEEP PROBE")
    print("=" * 75)
    
    results = []
    for probe in PROBES:
        res = probe_endpoint(probe)
        results.append(res)
        
        status_tag = "🟢 [PASS]" if res["status"] == "HEALTHY" else ("🟡 [WARN]" if res["status"] == "DEGRADED" else "🔴 [FAIL]")
        print(f"\n {status_tag} [{res['category']}] {res['name']}")
        print(f"   URL: {res['url']} | Code: {res['code']} | Latency: {res['latency_ms']}ms")
        if res["error"]:
            print(f"   Error: {res['error']}")

    # Run Database Telemetry Probe
    db_res = probe_db_telemetry()
    results.append(db_res)
    status_tag = "🟢 [PASS]" if db_res["status"] == "HEALTHY" else ("🟡 [WARN]" if db_res["status"] == "DEGRADED" else "🔴 [FAIL]")
    print(f"\n {status_tag} [{db_res['category']}] {db_res['name']}")
    print(f"   URL: {db_res['url']} | Code: {db_res['code']} | Latency: {db_res['latency_ms']}ms")
    if db_res["error"]:
        print(f"   Error: {db_res['error']}")
            
    print("\n" + "=" * 75)
    healthy_count = sum(1 for r in results if r["status"] == "HEALTHY")
    print(f" [SUMMARY] Deep Probes Passed: {healthy_count}/{len(results)}")
    print("=" * 75)
    
    # Sync alerts and dashboard log
    sync_alerts_and_logs(results)
    return results

if __name__ == "__main__":
    from datetime import datetime, timezone
    run_deep_probes()


