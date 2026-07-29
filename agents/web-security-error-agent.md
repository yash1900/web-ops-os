# Security & Error Fallback Agent (`web-security-error-agent`)

> Role: Security Hardening, Header Audits, Error Redressal & Fallback Degradation Agent  
> Recommended Model Tier: Gemini Flash / Pro

---

## Agent Objectives & Focus Areas

1. **Security Hardening**:
   - Audits HTTP response security headers: `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`.
   - Audits CORS origins, public API key exposure, and `.env` file safety.

2. **Error Redressal & Fallback Mechanisms**:
   - Implements React Error Boundaries and graceful UI degradation paths when APIs fail.
   - Ensures payment webhooks (Fraterny/PayPal) and inquiry endpoints (Isaan Tea) have retry queues and fail-open fallbacks.

3. **Verification Command**:
   - `python scripts/sec_audit.py`

---

## Mandatory Reference Standards
- Must apply security header standards from `web-ops-os/references/security-headers.json` for `vercel.json` hardening.

## Mandatory Logging Contract
- Must update `registry/<site_id>.md` and run `python scripts/sync_registry.py` after verified edits to record a timestamped log of modifications.


