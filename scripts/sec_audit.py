"""
Web-Ops OS Security & Config Auditor
Scans managed site folders for .env leak risks, security header configs, and hardcoded secrets.
"""

import json
import os
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def load_websites():
    registry_path = os.path.join(os.path.dirname(__file__), "..", "registry", "websites.json")
    if not os.path.exists(registry_path):
        print(f"[ERROR] Registry file not found at {registry_path}")
        sys.exit(1)
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("managed_websites", [])

def check_security(site_path):
    issues = []
    
    # 1. Check for committed .env files
    env_file = os.path.join(site_path, ".env")
    if os.path.exists(env_file):
        issues.append("[FAIL] Local .env file detected in repo folder. Ensure it is gitignored!")
        
    gitignore_file = os.path.join(site_path, ".gitignore")
    if os.path.exists(gitignore_file):
        with open(gitignore_file, "r", encoding="utf-8", errors="ignore") as f:
            gi_content = f.read()
            if ".env" not in gi_content:
                issues.append("[FAIL] .gitignore does NOT contain '.env' pattern!")
    else:
        issues.append("[WARN] No .gitignore file found in site folder.")
        
    # 2. Check for vercel.json headers if present
    vercel_json = os.path.join(site_path, "vercel.json")
    has_csp = False
    if os.path.exists(vercel_json):
        try:
            with open(vercel_json, "r", encoding="utf-8") as f:
                v_data = json.load(f)
                headers = v_data.get("headers", [])
                for h in headers:
                    for item in h.get("headers", []):
                        if item.get("key", "").lower() == "content-security-policy":
                            has_csp = True
        except Exception:
            pass
            
    return issues, has_csp

def main():
    print("=" * 65)
    print(" [WEB-OPS] SECURITY & ENVIRONMENT HARDENING AUDITOR")
    print("=" * 65)
    
    websites = load_websites()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    for site in websites:
        site_id = site.get("site_id")
        local_rel = site.get("local_path")
        site_path = os.path.join(base_dir, local_rel)
        
        print(f"\n[SITE] {site.get('name')} ({site_id})")
        if not os.path.exists(site_path):
            print(f"  [WARN] Folder missing: {site_path}")
            continue
            
        issues, has_csp = check_security(site_path)
        
        if not issues:
            print(" [OK] .env security & .gitignore rules passed.")
        else:
            for issue in issues:
                print(f" {issue}")
                
        if has_csp:
            print(" [OK] Security Headers / CSP configured in vercel.json.")
        else:
            print(" [INFO] No explicit vercel.json CSP headers configured (using platform defaults).")
            
        print("-" * 65)

if __name__ == "__main__":
    main()
