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
