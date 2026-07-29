"""
Web-Ops OS Cloud Runner Engine
Executed 24/7 on GitHub Actions cloud infrastructure.
Runs health checks, static SEO, security audits, auto-fixers, autonomous agent triggers,
and dispatches dark-mode email alerts on website downtime or SSL certificate expiration.
"""

import json
import os
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

import health_check
import seo_scanner
import sec_audit
import auto_fixer
import agent_autonomous_runner

def send_alert_email(failed_sites, total_sites):
    smtp_user = os.environ.get("GMAIL_USER") or os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("GMAIL_APP_PASSWORD") or os.environ.get("SMTP_PASS")
    email_to = os.environ.get("ALERT_EMAIL_TO") or os.environ.get("EMAIL_TO") or "malhotrayash1900@gmail.com"


    if not smtp_user or not smtp_pass or not email_to:
        print("[INFO] Email alert credentials not configured in secrets. Skipping email dispatch.")
        return

    subject = f"🔴 [ALERT] Web-Ops OS: {len(failed_sites)} Website Issue(s) Detected"
    
    site_rows = ""
    for s in failed_sites:
        site_rows += f"""
        <tr>
          <td style="padding: 10px; border-bottom: 1px solid #334155; color: #f87171; font-weight: bold;">{s.get('site_id')}</td>
          <td style="padding: 10px; border-bottom: 1px solid #334155; color: #cbd5e1;">{s.get('url')}</td>
          <td style="padding: 10px; border-bottom: 1px solid #334155; color: #f87171;">{s.get('error') or 'Code ' + str(s.get('code'))}</td>
        </tr>
        """

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px; }}
        .card {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; max-width: 650px; margin: 0 auto; }}
        h2 {{ color: #ef4444; margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th {{ text-align: left; padding: 10px; border-bottom: 2px solid #334155; color: #94a3b8; }}
        .footer {{ margin-top: 20px; font-size: 12px; color: #64748b; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="card">
        <h2>⚠️ Web-Ops OS Cloud Alert</h2>
        <p>Your 24/7 Cloud Sentinel detected issues across <strong>{len(failed_sites)}</strong> of your managed websites:</p>
        <table>
          <thead>
            <tr>
              <th>Site ID</th>
              <th>Endpoint URL</th>
              <th>Error Details</th>
            </tr>
          </thead>
          <tbody>
            {site_rows}
          </tbody>
        </table>
        <p style="margin-top: 20px; font-size: 13px; color: #94a3b8;">
          Automated Health & Security Engine evaluated. Re-check active credentials or SSL certificates.
        </p>
        <div class="footer">
          Sent 24/7 by Web-Ops OS Cloud Sentinel (GitHub Actions)
        </div>
      </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Web-Ops Sentinel <{smtp_user}>"
        msg["To"] = email_to
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [email_to], msg.as_string())

        print(f"[OK] Alert email dispatched successfully to {email_to}")
    except Exception as e:
        print(f"[ERROR] Failed to send alert email: {e}")

def main():
    print("=" * 70)
    print(" ☁️  WEB-OPS OS — 24/7 CLOUD RUNNER ENGINE (GITHUB ACTIONS)")
    print("=" * 70)
    
    # 1. Load websites and check health
    websites = health_check.load_websites()
    results = []
    failed_sites = []
    
    for site in websites:
        res = health_check.check_website(site)
        results.append(res)
        if res["status"] != "HEALTHY":
            failed_sites.append(res)
            
    print(f"\n[CLOUD PING RESULT] Total: {len(results)} | Healthy: {len(results)-len(failed_sites)} | Issues: {len(failed_sites)}")
    
    # 2. Run static SEO audit
    print("\n--- Running SEO Audit ---")
    try:
        seo_scanner.main()
    except Exception as e:
        print(f"[WARN] SEO scan error: {e}")
        
    # 3. Run security audit
    print("\n--- Running Security Audit ---")
    try:
        sec_audit.main()
    except Exception as e:
        print(f"[WARN] Sec audit error: {e}")
        
    # 4. Run auto-fixer
    print("\n--- Running Auto-Fixer ---")
    try:
        auto_fixer.main()
    except Exception as e:
        print(f"[WARN] Auto-fixer error: {e}")

    # 5. Run autonomous agent trigger engine
    print("\n--- Running Autonomous AI Agent Engine ---")
    try:
        agent_autonomous_runner.main()
    except Exception as e:
        print(f"[WARN] Autonomous agent runner error: {e}")

    # 6. Dispatch email alert if any site is degraded/unhealthy
    if failed_sites:
        print(f"\n⚠️  {len(failed_sites)} site(s) failed health check. Triggering cloud email alert...")
        send_alert_email(failed_sites, len(results))
    else:
        print("\n🟢 All managed websites are 100% healthy. No alert email required.")

if __name__ == "__main__":
    main()
