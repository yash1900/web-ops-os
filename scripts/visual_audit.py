"""
Web-Ops OS Visual Viewport & Layout Overflow Auditor
Loads each live production URL in headless Chrome at 375 / 768 / 1440 px and reports
real horizontal overflow, runtime errors, CSP blocks and failed assets.
Thin wrapper over `live_audit.py --browser-only` (engine: browser/site_smoke.js).

  python scripts/visual_audit.py [--site SITE_ID]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import live_audit  # noqa: E402

if __name__ == "__main__":
    sys.exit(live_audit.main(["--browser-only"] + sys.argv[1:]))
