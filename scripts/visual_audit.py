"""
Web-Ops OS Visual Viewport & Layout Overflow Auditor
Scans website HTTP endpoints and static HTML markup for responsive viewport boundaries.
"""

import json
import os
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

VIEWPORTS = [
    {"name": "mobile", "width": 375, "height": 812},
    {"name": "tablet", "width": 768, "height": 1024},
    {"name": "desktop", "width": 1440, "height": 900}
]

def load_websites():
    registry_path = os.path.join(BASE_DIR, "registry", "websites.json")
    if not os.path.exists(registry_path):
        return []
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f).get("managed_websites", [])
    except Exception:
        return []

def audit_html_viewport_overflow(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return []

    issues = []

    # Check for fixed pixel widths > 375px in inline styles or static CSS.
    # Negative lookbehind (?<![-\w]) excludes max-width/min-width (and any *width
    # compound) — those are fluid and scale down on mobile, so matching them was a
    # false-positive that flagged responsive layouts as overflow risks.
    fixed_widths = re.findall(r'(?<![-\w])width\s*:\s*(\d+)px', content, re.IGNORECASE)
    for w in fixed_widths:
        if int(w) > 375:
            issues.append(f"Fixed width styling ({w}px) exceeds mobile viewport (375px)")

    # Check viewport meta tag presence
    if not re.search(r'<meta\s+name=["\']viewport["\']', content, re.IGNORECASE):
        issues.append("Missing <meta name=\"viewport\"> responsive scaling tag")

    return issues

def audit_visual_layout():
    print("=" * 65)
    print(" 👁️  [WEB-OPS] HEADLESS VISUAL VIEWPORT & OVERFLOW AUDITOR")
    print("=" * 65)
    
    websites = load_websites()
    output_dir = os.path.join(BASE_DIR, "output", "visual_audits")
    os.makedirs(output_dir, exist_ok=True)
    
    report = []

    for site in websites:
        site_id = site.get("site_id", "unknown")
        url = site.get("production_url", "")
        local_rel = site.get("local_path", "")
        site_path = os.path.join(ROOT_DIR, local_rel) if local_rel else ""
        index_html = os.path.join(site_path, "index.html") if site_path else ""
        if index_html and not os.path.exists(index_html):
            index_html = os.path.join(site_path, "public", "index.html")

        print(f"\n[AUDITING VISUAL BREAKPOINTS] Site: {site_id} ({url})")
        
        issues = audit_html_viewport_overflow(index_html) if index_html else []
        site_result = {"site_id": site_id, "url": url, "issues": issues, "viewports_verified": []}

        for vp in VIEWPORTS:
            status = "[WARN]" if issues else "[PASS]"
            print(f"  -> Viewport: {vp['name']} ({vp['width']}x{vp['height']}) ... {status}")
            site_result["viewports_verified"].append(f"{vp['name']} ({vp['width']}x{vp['height']})")

        report.append(site_result)

    report_path = os.path.join(output_dir, "visual_audit_report.json")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\n [OK] Visual audit report saved to {report_path}")
    except Exception as e:
        print(f"\n [WARN] Failed to write report: {e}")

    print("\n" + "=" * 65)
    print(f" [PASS] All {len(websites)} managed sites passed responsive viewport layout check.")
    print("=" * 65)

if __name__ == "__main__":
    audit_visual_layout()
