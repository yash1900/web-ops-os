# `/web-sec-harden` Skill — Security Hardening & Header Optimization

Use this skill when auditing or hardening headers, Content Security Policies, CORS settings, or credentials.

---

## Workflow Steps

1. **Security Audit**:
   - Run `python scripts/sec_audit.py`.

2. **Security Headers**:
   - For Vercel projects: Update `vercel.json` headers section with CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy.
   - For HTML/Static projects: Ensure `<meta http-equiv="...">` fallback headers exist.

3. **Secrets Audit**:
   - Scan codebase for hardcoded API keys or credentials. Ensure secrets are loaded from environment variables (`process.env` or `import.meta.env`).

4. **Verify**:
   - Re-run `python scripts/sec_audit.py`.
