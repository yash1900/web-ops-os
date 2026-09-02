# CLAUDE.md — Web-Ops OS (Websites Management & Optimization System)

This directory is the **isolated Web-Ops OS** inside Yash's Automations OS. Its sole purpose is the holistic, scalable, structural, and agentic management of all websites Yash owns or has edit access to.

---

## Operational Scope & Principles

1. **Holistic Website Lifecycle Management**:
   - UI/UX & Visual Design (animations, responsive layouts, overflow/overlap fixes, glassmorphism, visual polish).
   - SEO & Page Rank Optimization (title/meta tags, Schema.org JSON-LD, sitemaps, OpenGraph, search indexing).
   - Security & Privacy Hardening (CSP, CORS, SSL/TLS, security headers, `.env` leak prevention, dependency audit).
   - Health, Analytics & CRM Tracking (HTTP pings, web vitals, form submission webhooks, Pipedrive/Supabase ingestion).
   - Error Redressal & Fallbacks (graceful degrade paths, error logs, automated fallback UI).

2. **Deterministic First, Agentic When Needed**:
   - Routine health checks, static SEO audits, and security header checks are performed by deterministic Python scripts (`scripts/`). Zero LLM cost.
   - AI Agents are dispatched only when anomalies are detected, complex refactoring is requested, or creative design/SEO overhauls are required.

3. **`/advise` Decision Principles**:
   - Every modification is evaluated against Risk vs. Impact.
   - Always preserve backwards compatibility and existing API contracts.

4. **Definition of "Complete" — the Verify-Ship Gate** *(added 2026-07-31)*:
   - **"Complete" = verified → committed → deployed → confirmed-live.** A passing build is step one of four, NOT completion. Files edited in the working tree are **not** "remediated" or "shipped" — they are unshipped drafts until committed, pushed, and confirmed live.
   - The component that **makes** a change may never **certify** it. Every changeset is routed through the independent [`web-verify-ship-agent`](agents/web-verify-ship-agent.md), which reality-checks the diff, rejects fabricated findings, isolates the intended edit from unrelated/sensitive working-tree changes, runs the build, commits, deploys, and confirms live.
   - **Autonomy = full-auto by default** (Yash's standing directive, 2026-07-31): when the gate is fully green it commits **and deploys** with no human step. It stops and pings Yash **only on a real problem** — build failure, fabrication, secret/PII in a public bundle, a site-breaking CSP, or unverifiable legal content. Partial ship (ship the clean wins, hold the problem file) is preferred over blocking everything.
   - **Never report "green" from disk state.** Report only the gate's verdict (`SHIPPED` / `ESCALATED` / `REJECTED`).
   - *Origin:* on 2026-07-30 an audit reported 4 sites "hardened/remediated (green)" while **nothing was committed**, escalated an already-resolved OpenAI-401 as a current CRITICAL (stale/freshness failure — verified 2026-07-31), left a hardcoded Supabase `service_role` key in the working tree, and nearly shipped a CSP that would have broken Google Fonts. This gate exists so that can't recur.

---

## Managed Website Registry

All sites are tracked in `registry/websites.json` and detailed in `registry/<site_id>.md`:

| Site ID | Name | Local Folder | Stack / Hosting | Domain / Target | Spec Doc |
|---------|------|--------------|-----------------|-----------------|----------|
| `personal-website` | Yash Malhotra Personal Site | `personal-website/` | Vite + React 18 + TS + Tailwind v3 + Three.js (Vercel) | `yashmalhotra.space` | [personal-website.md](file:///c:/Users/amar1/Downloads/Automations/web-ops-os/registry/personal-website.md) |
| `isaan-tea` | Isaan Tea Website | `Isaan_Tea_V1/` | React 19 + Vite 6 + Tailwind v4 (Vercel Serverless) | `isaantea.com` | [isaan-tea.md](file:///c:/Users/amar1/Downloads/Automations/web-ops-os/registry/isaan-tea.md) |
| `fraterny` | Fraterny Platform | `fraterny-automation/Fraterny_Nextjs` & `Quest` | Next.js 16 + Node/Quest API + Supabase (Vercel / GCP) | `fraterny.com` | [fraterny.md](file:///c:/Users/amar1/Downloads/Automations/web-ops-os/registry/fraterny.md) |
| `iconic-homes` | Iconic Homes Tulsi Tower | `Iconic-homes-Tulsi-tower/` | Static HTML5 / CSS3 / JS (Hostinger / Static) | `iconichomesinfracon.in` | [iconic-homes.md](file:///c:/Users/amar1/Downloads/Automations/web-ops-os/registry/iconic-homes.md) |

---

## Trigger Commands & Skills

Run commands using PowerShell in `web-ops-os/` (use `;` to chain, never `&&`):

| Task / Domain | Command / Skill | Purpose |
|---------------|-----------------|---------|
| **24/7 Cloud Sentinel Engine** | `python scripts/cloud_runner.py` | Runs health, SEO, security, auto-fixers, AI triggers & emails alerts on failure. |
| **Uptime & Health Ping** | `python scripts/health_check.py` | Fast zero-cost HTTP status ping across all site endpoints. |
| **SEO Static Audit** | `python scripts/seo_scanner.py` | Audits missing title, meta tags, alt tags, schema, and sitemap. |
| **Security Audit** | `python scripts/sec_audit.py` | Audits HTTP headers, CSP, CORS, and `.env` security. |
| **Auto-Fixer & Remediation** | `python scripts/auto_fixer.py` | Remediates missing ALT attributes, meta descriptions, CSP, and syncs log. |
| **Visual Layout Audit** | `python scripts/visual_audit.py` | Audits responsive viewports (375px, 768px, 1440px) & checks overflow. |
| **Autonomous AI Trigger Engine** | `python scripts/agent_autonomous_runner.py` | Evaluates diagnostic flags & dispatches departmental AI agent prompts. |
| **Sync Registry** | `python scripts/sync_registry.py` | Resyncs website statuses with `Dashboard/memory/automations.md`. |
| **System Verification** | `python scripts/verify_os.py` | Runs 44-point verification suite testing specs, agents, skills & scripts. |
| **Full Site Audit** | `/web-audit [site_id]` | Invokes multi-dimensional audit skill across UI, SEO, Sec, Health. |
| **Fix UI / Overflows** | `/web-fix-ui [site_id]` | Triggers UI/UX agent to diagnose and resolve layout bugs & overlaps. |
| **Optimize SEO** | `/web-seo-opt [site_id]` | Injects optimized metadata, JSON-LD schema, and updates sitemap. |
| **Harden Security** | `/web-sec-harden [site_id]` | Applies CSP rules, security headers, and fallback handlers. |
| **Onboard New Site** | `/web-onboard-site <name>` | Onboards a new website into `websites.json`, routing, and scripts. |


---

## Agent Orchestration & Model Triage Matrix

System agents are defined in `agents/` and governed by `head-web-orchestrator`:

| Agent Role | Model Tier | Trigger Criteria | Target Focus |
|------------|------------|------------------|--------------|
| **Head Web Orchestrator** | Gemini 3.6 Flash / Pro | All incoming user requests to `/web-ops` | Request routing, strategy, user communication, cost control. |
| **UI/UX & Design Agent** | Gemini 3.6 Flash | Layout bugs, animation glitches, visual overhauls | CSS flex/grid, micro-animations, glassmorphism, responsive UI. |
| **SEO & Page Rank Agent** | Gemini Flash Lite / Flash | Missing metadata, low page rank, sitemap updates | Meta tags, Schema.org, OpenGraph, dynamic sitemaps, SEO scores. |
| **Security & Error Agent** | Gemini Flash / Pro | Security header audits, fallback degrades, SSL/CSP | Security headers, CSP policy, error boundary fallbacks, API security. |
| **Health & CRM Agent** | Python + Flash Lite | Endpoint health failures, form webhook issues | Latency metrics, webhook verification, CRM form ingestion. |

---

## Conventions & Rules

1. **Powershell Hardening**: Always wrap file paths with spaces in double quotes. Never use `&&` in PowerShell 5.1.
2. **Never Break Production**: Test builds (`npm run build` or `python scripts/...`) before committing or pushing changes.
3. **Evolving Knowledge**: When a site's stack, route, or deployment URL changes, update `registry/<site_id>.md` and run `python scripts/sync_registry.py`.
