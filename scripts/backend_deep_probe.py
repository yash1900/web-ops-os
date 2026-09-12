"""
Web-Ops OS Backend & Infrastructure Deep Probe Engine
Performs multi-dimensional verification across:
1. Backend API (Quest): https://api.fraterny.com/health (GCP Compute Engine FastAPI)
2. Database Connectivity (Supabase): https://pmaylemigtnzirbtiueg.supabase.co/rest/v1/
3. User Questionnaires & Workflows API: OpenAPI schema validation (https://api.fraterny.com/openapi.json)
4. Payment & Webhooks Listener Routes: https://api.fraterny.com/api/webhooks/razorpay & paypal
5. AI Generation Pipeline & Model Readiness: Quest API RAG & Model Endpoint Health
6. Checkout Pricing & Discount Integrity: dynamic_pricing vs the storefront, and
   discount codes still active past expiry

NOTE on what probes 1-5 can and cannot tell you: they assert that URLs respond
with an acceptable status code. The two "Payment & Webhooks" probes pass on a
405, i.e. they only prove the route exists. Nothing here calls
/api/payments/create-order, so no probe below #6 can see what a customer is
actually charged — a pricing defect will sit green indefinitely. Probe #6 exists
to close that specific blind spot; it still does not exercise order creation.
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
    # summary_generation has RLS disabled + a public SELECT policy, so the PUBLIC anon
    # key (already shipped in the Fraterny web frontend — safe to embed, NOT a secret)
    # can read it. This probe only ever does a read, so anon is sufficient and needs
    # zero config. If a service_role key is provided via env we prefer it, otherwise we
    # fall back to anon so the probe always runs instead of skipping.
    SUPABASE_ANON_KEY = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtYXlsZW1pZ3RuemlyYnRpdWVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIzMDAyMTAsImV4cCI6MjA1Nzg3NjIxMH0."
        "NrElgPeL_HOZnY3Ou5b5-I1X6ANI8SJh8Zcd_XmP5Xk"
    )
    api_key = os.environ.get("FRATERNY_SUPABASE_SERVICE_KEY", "").strip() or SUPABASE_ANON_KEY
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
            
            # Quest runs on demand (however often users trigger it), so volume is
            # irregular. The signal that matters is simply: DID THE LAST RUN SUCCEED?
            # Rows come ordered id desc, so rows[0] is the most recent job.
            base = {
                "id": "quest_db_pipeline_telemetry",
                "name": "Quest AI Pipeline Telemetry (Supabase DB)",
                "category": "AI Generation Pipeline",
                "url": "https://pmaylemigtnzirbtiueg.supabase.co/rest/v1/summary_generation",
                "code": 200,
                "latency_ms": latency,
            }

            if not rows:
                return {**base, "status": "DEGRADED",
                        "error": "No summary_generation rows returned — cannot confirm the last run."}

            latest = rows[0]
            st = str(latest.get("status") or "")
            err = latest.get("summary_error")
            tid = str(latest.get("testid") or "")[:12]
            row_id = latest.get("id")
            started = str(latest.get("agent_start_time") or "")
            completed = latest.get("agent_completion_time")
            when = started[:16] if started else "unknown time"

            # 1. Last run explicitly failed, or recorded an error without ever completing
            if "fail" in st.lower() or (err and not completed):
                return {**base, "status": "UNHEALTHY",
                        "error": f"LAST run FAILED — job #{row_id} (testId {tid}…, {when}), "
                                 f"status '{st}': {str(err or 'no error text')[:170]}"}

            # 2. Last run still mid-flight: fresh = normal (a user is running it now);
            #    old with no completion = genuinely stuck.
            mid_flight = not completed and "complete" not in st.lower()
            if mid_flight:
                stale = False
                try:
                    ts = started.replace(" ", "T")
                    if ts.endswith("+00"):
                        ts = ts[:-3] + "+00:00"
                    age_min = (datetime.now(timezone.utc) - datetime.fromisoformat(ts)).total_seconds() / 60
                    stale = age_min > 30
                except Exception:
                    stale = False
                if stale:
                    return {**base, "status": "DEGRADED",
                            "error": f"LAST run STUCK — job #{row_id} (testId {tid}…) still in "
                                     f"'{st}' since {when}, no completion after >30 min."}
                return {**base, "status": "HEALTHY", "error": None}

            # 3. Last run completed cleanly
            return {**base, "status": "HEALTHY", "error": None}
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

def probe_pricing_integrity():
    """
    Pricing & Discount Integrity audit for Quest checkout.

    The HTTP probes above only prove the server answers. They cannot see what a
    customer is actually charged, which is why a payment pricing defect can sit
    green for months. This probe checks the money path itself:

      1. An active `dynamic_pricing` row exists. Since 2026-09-12 the backend
         REFUSES to create an order when it can't read one, so a missing or
         deactivated row takes checkout down entirely.
      2. The storefront (/api/admin/pricing/display) serves the same numbers as
         that row. Drift means customers see a price the server won't honour.
      3. Prices clear Razorpay's 100 minor-unit floor (Rs.1 / $1).
      4. No discount code is active while past its expiry — the failure mode
         where a campaign link keeps working but silently stops discounting.

    Read-only, and the public anon key is enough (same rationale as the telemetry
    probe), so this needs zero configuration.
    """
    SUPABASE_ANON_KEY = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtYXlsZW1pZ3RuemlyYnRpdWVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIzMDAyMTAsImV4cCI6MjA1Nzg3NjIxMH0."
        "NrElgPeL_HOZnY3Ou5b5-I1X6ANI8SJh8Zcd_XmP5Xk"
    )
    api_key = os.environ.get("FRATERNY_SUPABASE_SERVICE_KEY", "").strip() or SUPABASE_ANON_KEY
    rest = "https://pmaylemigtnzirbtiueg.supabase.co/rest/v1/"
    storefront = "https://fraterny.com/api/admin/pricing/display"
    base = {
        "id": "quest_pricing_integrity",
        "name": "Checkout Pricing & Discount Integrity",
        "category": "Payment & Webhooks",
        "url": storefront,
        "code": 200,
    }
    start_time = time.time()

    def _get(url, headers):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))

    sb_headers = {"apikey": api_key, "Authorization": f"Bearer {api_key}",
                  "User-Agent": "WebOpsOS/1.0"}
    try:
        rows = _get(rest + "dynamic_pricing?is_active=eq.true&order=updated_at.desc&limit=1",
                    sb_headers)
        latency = int((time.time() - start_time) * 1000)
        if not rows:
            return {**base, "status": "UNHEALTHY", "code": 0, "latency_ms": latency,
                    "error": "NO ACTIVE `dynamic_pricing` ROW — checkout is DOWN. The "
                             "backend refuses to create any order when it cannot read a "
                             "price. Re-activate a pricing row immediately."}
        row = rows[0]

        fields = [
            ("razorpay_india_price_paise", ("razorpay", "india")),
            ("razorpay_international_price_cents", ("razorpay", "international")),
            ("paypal_india_price_cents", ("paypal", "india")),
            ("paypal_international_price_cents", ("paypal", "international")),
        ]

        # 3. floor check
        too_low = [c for c, _ in fields if int(row.get(c) or 0) < 100]
        if too_low:
            return {**base, "status": "UNHEALTHY", "code": 0, "latency_ms": latency,
                    "error": f"Price below the 100 minor-unit gateway floor: "
                             f"{', '.join(f'{c}={row.get(c)}' for c in too_low)}"}

        # 2. storefront must agree with the source of truth
        store = _get(storefront, {"User-Agent": "WebOpsOS/1.0"})
        drift = []
        if store.get("success") and store.get("data"):
            for col, (gw, region) in fields:
                served = store["data"].get(gw, {}).get(region, {}).get("price")
                if served is not None and int(served) != int(row[col]):
                    drift.append(f"{gw}.{region}: storefront {served} vs DB {row[col]}")
        else:
            drift.append("storefront returned no pricing data")
        if drift:
            return {**base, "status": "UNHEALTHY", "code": 0, "latency_ms": latency,
                    "error": "Storefront price disagrees with dynamic_pricing — customers "
                             "are quoted a price the server will not honour: " + "; ".join(drift)}

        # 4. active-but-expired discount codes
        codes = _get(rest + "discount_codes?select=code,discount_percentage,is_active,"
                            "expires_at&is_active=eq.true", sb_headers)
        now = datetime.now(timezone.utc)
        expired = []
        for c in codes or []:
            exp = c.get("expires_at")
            if not exp:
                continue
            try:
                when = datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                if when < now:
                    expired.append(f"{c['code']} ({c.get('discount_percentage')}%, "
                                   f"expired {when.date()})")
            except Exception:
                expired.append(f"{c['code']} (unparseable expires_at={exp!r})")

        active_summary = ", ".join(
            f"{c['code']}={c.get('discount_percentage')}%" for c in (codes or [])
        ) or "none"
        latency = int((time.time() - start_time) * 1000)

        if expired:
            return {**base, "status": "DEGRADED", "latency_ms": latency,
                    "error": f"Discount code(s) still flagged active past expiry: "
                             f"{'; '.join(expired)}. The code still validates but no longer "
                             f"discounts, so a live campaign link quietly charges full price. "
                             f"All active codes: {active_summary}"}

        india = int(row["razorpay_india_price_paise"])
        intl = int(row["razorpay_international_price_cents"])
        return {**base, "status": "HEALTHY", "latency_ms": latency, "error": None,
                "detail": f"India Rs.{india/100:.2f}, International ${intl/100:.2f}; "
                          f"storefront matches DB; active codes: {active_summary}"}

    except Exception as e:
        return {**base, "status": "UNHEALTHY", "code": 0,
                "latency_ms": int((time.time() - start_time) * 1000),
                "error": f"Pricing integrity audit failed: {e}"}


def sync_alerts_and_logs(results):
    """
    Syncs probe failures to daily-brief/alerts.json (for Morning Brief email alerts)
    and Dashboard/health-check-log.json (for live dashboard status map).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    # lastRun is a bare calendar date read by the Dashboard Map, so it must be
    # LOCAL: this probe runs last in push_tasks.ps1, and a UTC date stamped
    # during the 00:00-05:30 IST window overwrote health_check.py's correct
    # local date with yesterday's -- making every nightly run look stale.
    today_str = datetime.now().strftime("%Y-%m-%d")
    
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
            with open(health_log_path, "r", encoding="utf-8-sig") as f:
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
        
        status_tag = "🟢 [PASS]" if res["status"] == "HEALTHY" else ("🟡 [WARN]" if res["status"] == "DEGRADED" else ("⚪ [SKIP]" if res["status"] == "SKIPPED" else "🔴 [FAIL]"))
        print(f"\n {status_tag} [{res['category']}] {res['name']}")
        print(f"   URL: {res['url']} | Code: {res['code']} | Latency: {res['latency_ms']}ms")
        if res["error"]:
            print(f"   Error: {res['error']}")

    # Run Database Telemetry Probe
    db_res = probe_db_telemetry()
    results.append(db_res)
    status_tag = "🟢 [PASS]" if db_res["status"] == "HEALTHY" else ("🟡 [WARN]" if db_res["status"] == "DEGRADED" else ("⚪ [SKIP]" if db_res["status"] == "SKIPPED" else "🔴 [FAIL]"))
    print(f"\n {status_tag} [{db_res['category']}] {db_res['name']}")
    print(f"   URL: {db_res['url']} | Code: {db_res['code']} | Latency: {db_res['latency_ms']}ms")
    if db_res["error"]:
        print(f"   Error: {db_res['error']}")

    # Run Checkout Pricing & Discount Integrity audit
    price_res = probe_pricing_integrity()
    results.append(price_res)
    status_tag = "🟢 [PASS]" if price_res["status"] == "HEALTHY" else ("🟡 [WARN]" if price_res["status"] == "DEGRADED" else ("⚪ [SKIP]" if price_res["status"] == "SKIPPED" else "🔴 [FAIL]"))
    print(f"\n {status_tag} [{price_res['category']}] {price_res['name']}")
    print(f"   URL: {price_res['url']} | Code: {price_res['code']} | Latency: {price_res['latency_ms']}ms")
    if price_res.get("detail"):
        print(f"   {price_res['detail']}")
    if price_res["error"]:
        print(f"   Error: {price_res['error']}")

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


