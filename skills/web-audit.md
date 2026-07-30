# `/web-audit` Skill — Multi-Dimensional Website Audit

Use this skill when auditing a website (`/web-audit <site_id>`) or all managed websites.

---

## Audit Workflow Checklist

1. **Deterministic Scan Execution**:
   - Run `python scripts/health_check.py` to get uptime and latency status.
   - Run `python scripts/seo_scanner.py` to audit metadata and HTML structure.
   - Run `python scripts/sec_audit.py` to check security headers and `.env` files.

2. **UI/UX & Visual Review**:
   - Inspect layout responsiveness across breakpoints.
   - Check for `overflow-x` scrollbars, text overlaps, or unhandled image ratios.
   - Review animation loops and WebGL canvas performance.

3. **SEO & Page Rank Review**:
   - Verify single `<h1>` tag per page.
   - Check title tag length (< 60 chars) and meta description (120-160 chars).
   - Ensure OpenGraph tags and Schema.org JSON-LD are present.

4. **Synthesize Findings**:
   - Output clean executive summary of findings categorized by: Health (🟢/🔴), UI/UX, SEO, and Security.
   - **Every finding must be evidence-backed.** Do not report a fix as done because the file changed on disk — a working-tree edit is an unshipped draft, not a remediation. Do not cite a script/log/record you have not confirmed exists.

5. **Verify & Ship (mandatory — do NOT stop at step 4)**:
   - Route every change this audit produced through the independent [`web-verify-ship-agent`](../agents/web-verify-ship-agent.md).
   - It reality-checks each diff, rejects any fabricated finding, isolates the intended edit from unrelated/sensitive working-tree changes, runs the build (and validates CSP against what the site actually loads), commits, and gates the production push on Yash's approval.
   - Report the audit as complete **only** when the gate returns `SHIPPED` or `STAGED-AWAITING-APPROVAL` per change — never from disk state alone.
