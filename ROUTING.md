# ROUTING.md — Web-Ops OS Intent & Domain Routing Table

This table maps incoming user requests, website maintenance tasks, and automated triggers to the exact file, script, skill, and agent responsible within `web-ops-os`.

---

## 1. Domain & Task Intent Routing

| Task Type / Need | Key Terms / Trigger | Execute Script / Skill | Target Agent Role | Target Registry Spec |
|------------------|----------------------|-----------------------|-------------------|----------------------|
| **Uptime / Health Check** | "is site up", "health check", "ping sites", "500 error" | `python scripts/health_check.py` or `/web-health-monitor` | `web-health-crm-agent` | `registry/websites.json` |
| **UI Overflow / Layout Bug** | "overflow", "overlap", "broken UI", "mobile layout", "animation glitch" | `/web-fix-ui <site_id>` | `web-ui-ux-agent` | `registry/<site_id>.md` |
| **SEO & Page Rank** | "SEO audit", "meta tags", "sitemap", "schema markup", "page rank" | `python scripts/seo_scanner.py` or `/web-seo-opt` | `web-seo-rank-agent` | `registry/<site_id>.md` |
| **Security & Headers** | "CSP", "CORS", "SSL", "headers check", "secret exposure", "vulnerability" | `python scripts/sec_audit.py` or `/web-sec-harden` | `web-security-error-agent` | `registry/<site_id>.md` |
| **Full Site Audit** | "audit personal website", "check all sites", "web ops audit" | `/web-audit <site_id>` | `head-web-orchestrator` | `registry/<site_id>.md` |
| **Form & CRM Ingestion** | "contact form fail", "webhook issue", "Pipedrive lead", "inquiry form" | `/web-health-monitor` | `web-health-crm-agent` | `registry/isaan-tea.md` & `fraterny.md` |
| **Onboard New Site** | "add new site", "manage new domain", "onboard website" | `/web-onboard-site <site_id>` | `head-web-orchestrator` | `registry/websites.json` |

---

## 2. Website ID Mapping

| Site Alias | Canonical Site ID | Local Path | Production URL |
|------------|-------------------|------------|----------------|
| personal, yash site, yashmalhotra.space, quiet founder | `personal-website` | `personal-website/` | `https://yashmalhotra.space` |
| isaan, isaan tea, isaantea.com | `isaan-tea` | `Isaan_Tea_V1/` | `https://isaantea.com` |
| fraterny, quest, fraterny villa | `fraterny` | `fraterny-automation/Fraterny_Nextjs` | `https://fraterny.com` |
| iconic homes, tulsi tower, iconic | `iconic-homes` | `Iconic-homes-Tulsi-tower/` | `https://iconichomes.in` |

---

## 3. Fallback & Escalation Flow

```
[Incoming Request / Auto Trigger]
           │
           ▼
 [Deterministic Python Script Scan]
           │
   ┌───────┴────────┐
   │ Success        │ Anomaly / Deep Task
   ▼                ▼
[Log & Fast Return] [Head Web Orchestrator (Flash/Pro)]
                    │
                    ├─► UI/UX issue ──► web-ui-ux-agent (Flash)
                    ├─► SEO issue ───► web-seo-rank-agent (Flash Lite)
                    ├─► Security ────► web-security-error-agent (Flash/Pro)
                    └─► CRM/Health ──► web-health-crm-agent (Flash Lite)
```
