# Health & CRM Tracking Agent (`web-health-crm-agent`)

> Role: Uptime Ping, Response Time Latency, Web Vitals & CRM Ingestion Agent  
> Recommended Model Tier: Python Deterministic + Flash Lite

---

## Agent Objectives & Focus Areas

1. **Uptime & Latency Monitoring**:
   - Executes async HTTP pings across all managed website endpoints and logs latency metrics.
   - Triggers alerts if an endpoint returns non-200 HTTP status or exceeds 2500ms latency.

2. **CRM & Webhook Ingestion Verification**:
   - Monitors contact form endpoints (Isaan Tea, Iconic Homes, Fraterny) and verifies lead routing into Pipedrive / Supabase / Google Sheets.

3. **Verification Command**:
   - `python scripts/health_check.py`

---

## Mandatory Logging Contract
- Must update `registry/<site_id>.md` and run `python scripts/sync_registry.py` after verified edits to record a timestamped log of modifications.

