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
  ┌───────────────┼───────────────┬───────────────┐
  ▼               ▼               ▼               ▼
[health_check]  [seo_scanner]   [sec_audit]    [auto_fixer]
  │
  ├─► All 200 OK ──────────► Log & Standby
  └─► SSL Expiry / 500 ────► Send Instant Dark-Mode Email Alert 📧
```

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
| `ALERT_EMAIL_TO` | `yashmalhotra.space@gmail.com` | Destination inbox for instant downtime/SSL alerts. |

---

## 3. How 24/7 Alerts Work When Your Laptop Is Closed

1. **Every 3 Hours**: GitHub Actions wakes up in the cloud, checks `yashmalhotra.space`, `isaantea.com`, `fraterny.com`, and `iconichomesinfracon.in`.
2. **If an SSL cert expires or a server crashes**: `cloud_runner.py` formats a dark-mode HTML alert and emails it directly to your inbox within seconds.
3. **Zero Local Laptop Dependency**: Runs 24/7 365 days a year on GitHub's cloud servers.
