# `/web-seo-opt` Skill — SEO & Metadata Optimization

Use this skill when enhancing title tags, meta descriptions, Schema.org JSON-LD, or sitemaps for any website.

---

## Workflow Steps

1. **Audit Current State**:
   - Run `python scripts/seo_scanner.py`.

2. **Metadata Injection**:
   - Add/update `<title>`: Actionable, brand-aligned title under 60 characters.
   - Add/update `<meta name="description">`: Compelling summary (120-160 characters).
   - Inject `<meta property="og:title">`, `og:description`, `og:image`, `twitter:card`.

3. **Schema.org Structured Data**:
   - Inject `<script type="application/ld+json">` for `Organization` or `WebSite` schemas.

4. **Verify**:
   - Re-run `python scripts/seo_scanner.py` to confirm zero missing tags.
