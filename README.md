# Web-Ops OS — Websites Management & Optimization System

Web-Ops OS is an isolated, scalable, and agentic subsystem inside Yash's Automations OS (`Automations/web-ops-os`). It provides automated monitoring, UI/UX optimization, SEO management, security hardening, error redressal, and health tracking across all websites Yash manages.

- **Interactive Visual Dashboard:** [website_manager.html](file:///c:/Users/amar1/Downloads/Automations/web-ops-os/website_manager.html)

---

## Directory Breakdown

```
web-ops-os/
├── CLAUDE.md                # System governance, rules, commands & agent model matrix
├── ROUTING.md               # Task intent & website ID lookup router
├── README.md                # System documentation & sitemap
├── registry/                # Evolving knowledgebase per site
│   ├── websites.json        # Machine-readable website manifest
│   ├── personal-website.md  # Yash Malhotra Personal Site spec
│   ├── isaan-tea.md         # Isaan Tea Website spec
│   ├── fraterny.md          # Fraterny Platform spec
│   └── iconic-homes.md      # Iconic Homes Tulsi Tower spec
├── agents/                  # Specialized AI Agent specifications
│   ├── head-web-orchestrator.md   # System head & communication agent
│   ├── web-ui-ux-agent.md         # Design, animations & overflow agent
│   ├── web-seo-rank-agent.md      # SEO, schema & page rank agent
│   ├── web-security-error-agent.md# CSP, security & fallbacks agent
│   ├── web-health-crm-agent.md    # Latency, health & CRM webhook agent
│   └── web-verify-ship-agent.md   # Independent verify → commit → gated-deploy exit gate
├── skills/                  # Operational website management skill files
│   ├── web-audit.md         # Multi-dimensional site audit skill
│   ├── web-fix-ui.md        # UI overflow & visual fix skill
│   ├── web-seo-opt.md       # Metadata & JSON-LD optimization skill
│   ├── web-sec-harden.md    # Security header & CSP hardening skill
│   ├── web-health-monitor.md# Endpoint health ping & health summary skill
│   └── web-onboard-site.md  # Standardized new website onboarding skill
└── scripts/                 # Deterministic zero-cost Python scripts
    ├── health_check.py      # Async HTTP endpoint pings & latency scanner
    ├── seo_scanner.py       # Static HTML/JSX meta tag & ALT auditor
    ├── sec_audit.py         # Security header & CSP policy auditor
    └── sync_registry.py     # Registry resync & memory update script
```

---

## Quick Start Commands

```powershell
# 1. Run zero-cost health check across all sites
python scripts/health_check.py

# 2. Run static SEO audit
python scripts/seo_scanner.py

# 3. Run security audit
python scripts/sec_audit.py

# 4. Resync website registry with parent Automations OS
python scripts/sync_registry.py
```

---

## Architecture Principles

- **Zero-Cost First**: Deterministic Python scripts run routine audits instantly without API token overhead.
- **Dedicated Agent Models**: Each agent utilizes the most cost-efficient model tier (Gemini Flash Lite for structured checks, Flash for UI/UX CSS fixes, Pro for complex security/refactoring).
- **Self-Evolving**: New information or site updates are appended to `registry/<site_id>.md` and synced automatically.
