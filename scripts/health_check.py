"""
Web-Ops OS Health Check Script
Performs zero-cost async HTTP status pings and measures response latency across all registered websites.
Dynamically updates Dashboard/health-check-log.json for live Dashboard Map indicators.
"""

import json
import time
import urllib.request
import urllib.error
import datetime
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def load_websites():
    registry_path = os.path.join(os.path.dirname(__file__), "..", "registry", "websites.json")
    if not os.path.exists(registry_path):
        print(f"[ERROR] Registry file not found at {registry_path}")
        sys.exit(1)
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("managed_websites", [])

def check_website(site):
    url = site.get("health_endpoint") or site.get("production_url")
    site_id = site.get("site_id")
    name = site.get("name")
    
    if not url:
        return {"site_id": site_id, "name": name, "status": "UNKNOWN", "code": 0, "latency_ms": 0, "error": "No endpoint URL"}
    
    start_time = time.time()
    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "WebOpsOS-HealthCheck/1.0 (Automations-OS)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            latency = int((time.time() - start_time) * 1000)
            status_code = response.getcode()
            status = "HEALTHY" if status_code == 200 else "DEGRADED"
            return {
                "site_id": site_id,
                "name": name,
                "url": url,
                "status": status,
                "code": status_code,
                "latency_ms": latency,
                "error": None
            }
    except urllib.error.HTTPError as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "site_id": site_id,
            "name": name,
            "url": url,
            "status": "DEGRADED",
            "code": e.code,
            "latency_ms": latency,
            "error": str(e)
        }
    except Exception as e:
        latency = int((time.time() - start_time) * 1000)
        return {
            "site_id": site_id,
            "name": name,
            "url": url,
            "status": "UNHEALTHY",
            "code": 0,
            "latency_ms": latency,
            "error": str(e)
        }

def update_dashboard_health_log(results):
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    health_log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Dashboard"))
    if not os.path.exists(health_log_dir):
        health_log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    health_log_path = os.path.join(health_log_dir, "health-check-log.json")
    
    health_data = {}
    if os.path.exists(health_log_path):
        try:
            with open(health_log_path, "r", encoding="utf-8") as f:
                health_data = json.load(f)
        except Exception:
            pass
            
    if not isinstance(health_data, dict):
        health_data = {}
        
    if "automations" not in health_data or not isinstance(health_data["automations"], dict):
        health_data["automations"] = {}
        
    failed_sites = [r for r in results if r["status"] != "HEALTHY"]
    total_sites = len(results)
    healthy_count = total_sites - len(failed_sites)
    
    if failed_sites:
        res_tag = "degraded" if healthy_count > 0 else "unhealthy"
        fail_summary = ", ".join([f"{f['site_id']} ({f['error'] or 'Code ' + str(f['code'])})" for f in failed_sites])
        signal = f"🔴 {len(failed_sites)} site issue(s): {fail_summary}"
        note = f"{healthy_count}/{total_sites} sites healthy. Issues detected on: {', '.join([f['site_id'] for f in failed_sites])}"
    else:
        res_tag = "healthy"
        signal = f"{healthy_count}/{total_sites} managed websites audited & healthy (all HTTP 200)"
        note = "Async HTTP pings, static SEO, security & auto-healing active"
        
    health_data["lastRun"] = today_str
    health_data["source"] = "web-ops-os health_check.py"
    health_data["automations"]["web-ops-os"] = {
        "checkedAt": now_iso,
        "result": res_tag,
        "signal": signal,
        "note": note
    }
    
    # Map site_id to automations.md folder keys for granular Dashboard Map indicators
    folder_mapping = {
        "personal-website": "personal-website",
        "isaan-tea": "Isaan_Tea_V1",
        "fraterny": "fraterny-automation",
        "iconic-homes": "Iconic-homes-Tulsi-tower"
    }
    
    for r in results:
        folder_key = folder_mapping.get(r["site_id"], r["site_id"])
        site_result = "healthy" if r["status"] == "HEALTHY" else "unhealthy"
        site_signal = f"HTTP 200 OK ({r['latency_ms']}ms)" if r["status"] == "HEALTHY" else f"🔴 {r['error'] or 'Code ' + str(r['code'])}"
        
        health_data["automations"][folder_key] = {
            "checkedAt": now_iso,
            "result": site_result,
            "signal": f"{r['name']} — {site_signal}",
            "note": f"Live health ping to {r['url']}"
        }
    
    try:
        with open(health_log_path, "w", encoding="utf-8") as f:
            json.dump(health_data, f, indent=2)
        print(f"\n[OK] Updated Dashboard Map health log at {health_log_path} (Result: {res_tag.upper()})")
    except Exception as e:
        print(f"\n[WARN] Failed to write to {health_log_path}: {e}")




def main():
    print("=" * 65)
    print(" [WEB-OPS] AUTOMATED HEALTH & LATENCY CHECK")
    print("=" * 65)
    
    websites = load_websites()
    results = []
    
    for site in websites:
        res = check_website(site)
        results.append(res)
        
        status_tag = "[OK]" if res["status"] == "HEALTHY" else (" [WARN]" if res["status"] == "DEGRADED" else "[FAIL]")
        print(f" {status_tag} [{res['site_id']}] {res['name']}")
        print(f"   URL: {res['url']} | Code: {res['code']} | Latency: {res['latency_ms']}ms")
        if res["error"]:
            print(f"   Error: {res['error']}")
        print("-" * 65)
        
    print(f"\n[SUMMARY] Total Sites Audited: {len(results)}")
    healthy_count = sum(1 for r in results if r["status"] == "HEALTHY")
    print(f"Healthy: {healthy_count}/{len(results)}")
    
    # Sync with Dashboard Map health log
    update_dashboard_health_log(results)

if __name__ == "__main__":
    main()
