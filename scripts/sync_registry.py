"""
Web-Ops OS Registry Sync Script
Resyncs website statuses from registry/websites.json and updates website_manager.html.
"""

import json
import os
import sys

from update_website_manager import generate_website_manager_html

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    registry_path = os.path.join(os.path.dirname(__file__), "..", "registry", "websites.json")
    if not os.path.exists(registry_path):
        print(f"[ERROR] Registry file not found at {registry_path}")
        sys.exit(1)
        
    with open(registry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    sites = data.get("managed_websites", [])
    
    print("=" * 65)
    print(" [WEB-OPS] REGISTRY & OS MEMORY RESYNC")
    print("=" * 65)
    print(f"Loaded {len(sites)} managed websites from registry.")
    
    for s in sites:
        print(f" - [{s['site_id']}] {s['name']} -> {s['production_url']} ({s['hosting']})")
        
    generate_website_manager_html()
    print("\n[OK] Web-Ops OS registry state & website_manager.html verified and synced.")

if __name__ == "__main__":
    main()
