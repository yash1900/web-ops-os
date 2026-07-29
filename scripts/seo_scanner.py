"""
Web-Ops OS Static SEO Scanner
Scans static HTML and React index.html files across managed sites for title tags, meta descriptions, OpenGraph tags, and ALT attributes.
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

def scan_html_file(file_path):
    if not os.path.exists(file_path):
        return {"error": f"File missing: {file_path}"}
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else None
    
    meta_desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
    if not meta_desc_match:
        meta_desc_match = re.search(r'<meta\s+content=["\'](.*?)["\']\s+name=["\']description["\']', content, re.IGNORECASE | re.DOTALL)
    meta_desc = meta_desc_match.group(1).strip() if meta_desc_match else None
    
    og_title = bool(re.search(r'property=["\']og:title["\']', content, re.IGNORECASE))
    og_desc = bool(re.search(r'property=["\']og:description["\']', content, re.IGNORECASE))
    og_image = bool(re.search(r'property=["\']og:image["\']', content, re.IGNORECASE))
    
    h1_count = len(re.findall(r'<h1[\s>]', content, re.IGNORECASE))
    img_without_alt = len(re.findall(r'<img(?![^>]*\balt=)[^>]*>', content, re.IGNORECASE))
    
    return {
        "title": title,
        "title_length": len(title) if title else 0,
        "meta_description": meta_desc,
        "desc_length": len(meta_desc) if meta_desc else 0,
        "og_title": og_title,
        "og_desc": og_desc,
        "og_image": og_image,
        "h1_count": h1_count,
        "missing_alt_count": img_without_alt
    }

def main():
    print("=" * 65)
    print(" [WEB-OPS] STATIC SEO & METADATA AUDITOR")
    print("=" * 65)
    
    websites = load_websites()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    for site in websites:
        site_id = site.get("site_id")
        local_rel = site.get("local_path")
        site_path = os.path.join(base_dir, local_rel)
        
        index_html = os.path.join(site_path, "index.html")
        if not os.path.exists(index_html):
            # check public/index.html
            index_html = os.path.join(site_path, "public", "index.html")
            
        print(f"\n[SITE] {site.get('name')} ({site_id})")
        if not os.path.exists(index_html):
            print(f"  [WARN] index.html not found at {site_path}")
            continue
            
        res = scan_html_file(index_html)
        
        # Output title checks
        if res["title"]:
            status = "[OK]" if 10 <= res["title_length"] <= 60 else "[WARN]"
            print(f" {status} Title ({res['title_length']} chars): \"{res['title']}\"")
        else:
            print(" [FAIL] Missing <title> tag!")
            
        # Output description checks
        if res["meta_description"]:
            status = "[OK]" if 50 <= res["desc_length"] <= 160 else "[WARN]"
            print(f" {status} Meta Description ({res['desc_length']} chars): \"{res['meta_description'][:70]}...\"")
        else:
            print(" [FAIL] Missing meta description tag!")
            
        # OpenGraph checks
        og_status = "[OK]" if (res["og_title"] and res["og_desc"]) else "[WARN]"
        print(f" {og_status} OpenGraph Tags — Title: {res['og_title']}, Desc: {res['og_desc']}, Image: {res['og_image']}")
        
        # Missing ALT images check
        if res["missing_alt_count"] > 0:
            print(f" [WARN] Images missing ALT tags: {res['missing_alt_count']}")
        else:
            print(" [OK] All images have ALT tags or none present.")
            
        print("-" * 65)

if __name__ == "__main__":
    main()
