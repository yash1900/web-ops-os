# SETUP_CLOUD.md — 24/7 Cloud Architecture for Web-Ops OS

This document explains how `web-ops-os` runs 24/7 in the cloud on **GitHub Actions** even when your laptop lid is closed.

---

## 1. Cloud Architecture Overview

```
 [GitHub Actions Cloud Cron (Every 3h)]
                  │
                  ▼
      [cloud_runner.py Engine]
                  │
  ┌───────────────┼──────────────────────┐
  ▼               ▼                      ▼
[health_check]  [backend_deep_probe]   [live_audit + browser/site_smoke.js]
                  │
  ├─► Nothing FAILed ──────────────► green run, no email
  ├─► Any FAIL ─────────────────────► alert email (green run)
  └─► Any FAIL + email not sent ───► run exits 1 (red) — GitHub's failure email is the fallback
```

The runner checks out only this repo, so it audits the live URLs. The local-folder scripts (`seo_scanner`, `sec_audit`, `auto_fixer`) do not run here. The workflow installs Node and runs `npm ci` in `browser/`; the headless check uses the runner's Google Chrome (`CHROME_PATH=/usr/bin/google-chrome`).

---

## 2. 1-Minute Cloud Setup Guide

### Step 1: Create or Push to GitHub Repository
Run in PowerShell inside `c:\Users\amar1\Downloads\Automations\web-ops-os`:

```powershell
git init
git add .
git commit -m "feat: initialize Web-Ops OS 24/7 cloud runner"
git remote add origin https://github.com/yash1900/web-ops-os.git
git push -u origin main
```

*(Or push the entire Automations OS tree if using a monorepo).*

### Step 2: Add GitHub Repository Secrets
Navigate to **GitHub Repo -> Settings -> Secrets and variables -> Actions -> New repository secret**:

| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `GEMINI_API_KEY` | Your Gemini API Key | Used by autonomous AI agent triggers. |
| `GMAIL_USER` | Your Gmail address | Sender email address for 24/7 downtime alerts. |
| `GMAIL_APP_PASSWORD` | Google App Password | SMTP authentication (16-char app password). |
| `ALERT_EMAIL_TO` | `malhotrayash1900@gmail.com` | Destination inbox for instant downtime/SSL alerts. |

Status (2026-11-01): `GMAIL_USER`, `GMAIL_APP_PASSWORD` and `ALERT_EMAIL_TO` are set (the Gmail pair from `%LOCALAPPDATA%\ai-os\secrets\gmail_smtp.json`); run 41241056945 delivered an alert. `GEMINI_API_KEY` is not set and nothing in the cloud run uses it.


---

## 3. How 24/7 Alerts Work When Your Laptop Is Closed

1. **Every 3 Hours**: GitHub Actions wakes up in the cloud, checks `yashmalhotra.space`, `isaantea.com`, `fraterny.com`, and `iconichomesinfracon.in`.
2. **If anything FAILs** (site down, cert under 14 days, broken link, page wider than a phone, JS crash, CSP block, deep-probe failure): `cloud_runner.py` emails a dark-mode HTML alert. If that email cannot be sent, the run goes red instead of green.
3. **Zero Local Laptop Dependency**: Runs 24/7 365 days a year on GitHub's cloud servers.
