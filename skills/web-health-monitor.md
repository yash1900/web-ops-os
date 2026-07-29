# `/web-health-monitor` Skill — Website Health & Uptime Monitoring

Use this skill when checking live website availability, latency metrics, or form submission webhooks.

---

## Workflow Steps

1. **Execute Endpoint Ping**:
   - Run `python scripts/health_check.py`.

2. **Evaluate Results**:
   - HTTP 200-299: 🟢 Healthy
   - Latency > 2000ms: 🟡 Warning (Degraded performance)
   - HTTP 4xx / 5xx / Timeout: 🔴 Critical Failure

3. **Report & Sync**:
   - Run `python scripts/sync_registry.py` to resync status into `registry/websites.json` and `Dashboard/memory/automations.md`.
