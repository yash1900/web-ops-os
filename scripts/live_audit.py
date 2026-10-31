"""
Web-Ops OS Live Production Auditor
Audits what visitors actually get from each production URL: HTTP status, security
headers, CSP sanity, TLS expiry, served SEO tags, robots/sitemap/llms.txt and broken
internal links. Optional headless-browser pass (browser/site_smoke.js) adds real
viewport overflow, runtime errors and failed assets at 375/768/1440px.

Needs no local site folders, so it runs the same on the laptop and in GitHub Actions.

  python scripts/live_audit.py                 # HTTP checks + browser smoke
  python scripts/live_audit.py --http-only
  python scripts/live_audit.py --browser-only --site isaan-tea

Exit 1 if any check FAILs. Levels: FAIL > WARN > PASS; UNVERIFIED = machine offline;
SKIPPED = could not run (in GitHub Actions a skipped browser pass counts as FAIL).
"""

import argparse
import json
import os
import socket
import ssl
import subprocess
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
import netcheck  # noqa: E402

OUTPUT_PATH = os.path.join(BASE_DIR, "output", "live_audit", "report.json")
SMOKE_JS = os.path.join(BASE_DIR, "browser", "site_smoke.js")
UA = "Mozilla/5.0 (Web-Ops OS live audit)"
TIMEOUT = 20
MAX_LINKS = 40
TLS_FAIL_DAYS = 14
TLS_WARN_DAYS = 30
RANK = {"FAIL": 4, "SKIPPED": 3, "WARN": 2, "UNVERIFIED": 1, "PASS": 0}


def load_websites():
    with open(os.path.join(BASE_DIR, "registry", "websites.json"), "r", encoding="utf-8") as f:
        return json.load(f).get("managed_websites", [])


# ---------- fetching ----------

def fetch(url, limit=2_000_000):
    """GET url. Returns (status, headers_dict_lowercase, body_text, final_url, error)."""
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urlopen(req, timeout=TIMEOUT) as r:
            # urlopen's timeout is per socket read, so a slow-drip server could stall a
            # single read(limit) for ever; read in chunks against a hard deadline.
            deadline, chunks, size = time.monotonic() + 2 * TIMEOUT, [], 0
            while size < limit and time.monotonic() < deadline:
                chunk = r.read(min(65536, limit - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
            body = b"".join(chunks).decode("utf-8", errors="ignore")
            return r.status, {k.lower(): v for k, v in r.headers.items()}, body, r.geturl(), None
    except HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, "", url, None
    except (URLError, socket.timeout, ConnectionError, ssl.SSLError, OSError) as e:
        return 0, {}, "", url, str(getattr(e, "reason", e))[:200]


def tls_days_left(host, port=443):
    """Days until the served certificate expires. Raises on handshake/validation failure."""
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=TIMEOUT) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as tls:
            not_after = tls.getpeercert()["notAfter"]
    expiry = datetime.fromtimestamp(ssl.cert_time_to_seconds(not_after), tz=timezone.utc)
    return (expiry - datetime.now(timezone.utc)).days


# ---------- parsing ----------

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self._in_title = "", False
        self.meta, self.links, self.hrefs, self.lang = {}, [], [], None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append(a)
        elif tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def parse_csp(value):
    out = {}
    for part in (value or "").split(";"):
        bits = part.strip().split()
        if bits:
            out[bits[0].lower()] = [b.lower() for b in bits[1:]]
    return out


def csp_allows(csp, directive, host):
    """Does the CSP let `directive` load from https://host? Falls back to default-src."""
    sources = csp.get(directive, csp.get("default-src"))
    if sources is None:
        return True
    for s in sources:
        s = s.strip("'")
        if s in ("*", "https:") or s.replace("https://", "") == host:
            return True
        if s.startswith("*.") and host.endswith(s[1:]):
            return True
        if s.startswith("https://*.") and host.endswith(s[len("https://*"):]):
            return True
    return False


# ---------- checks ----------

def r(site, check, level, detail=""):
    return {"site_id": site, "check": check, "level": level, "detail": detail}


def audit_headers(site, headers, html):
    out = []
    out.append(r(site, "hsts", "PASS" if "strict-transport-security" in headers else "WARN",
                 headers.get("strict-transport-security", "missing Strict-Transport-Security")))
    out.append(r(site, "nosniff", "PASS" if headers.get("x-content-type-options", "").lower() == "nosniff" else "WARN",
                 headers.get("x-content-type-options", "missing X-Content-Type-Options")))
    csp_raw = headers.get("content-security-policy", "")
    csp = parse_csp(csp_raw)
    framed = "x-frame-options" in headers or "frame-ancestors" in csp
    out.append(r(site, "clickjacking", "PASS" if framed else "WARN",
                 headers.get("x-frame-options", "frame-ancestors" if framed else "no X-Frame-Options or frame-ancestors")))
    if not csp_raw:
        out.append(r(site, "csp", "WARN", "no Content-Security-Policy served"))
        return out
    out.append(r(site, "csp", "PASS", f"{len(csp)} directives"))
    # The 2026-07-30 failure class: a CSP that blocks fonts the page really uses.
    uses_gfonts_css = "fonts.googleapis.com" in html
    uses_gfonts = uses_gfonts_css or "fonts.gstatic.com" in html
    if uses_gfonts:
        blocked = []
        if uses_gfonts_css and not csp_allows(csp, "style-src", "fonts.googleapis.com"):
            blocked.append("style-src blocks fonts.googleapis.com")
        if not csp_allows(csp, "font-src", "fonts.gstatic.com"):
            blocked.append("font-src blocks fonts.gstatic.com")
        out.append(r(site, "csp-fonts", "FAIL" if blocked else "PASS",
                     "; ".join(blocked) or "Google Fonts allowed"))
    return out


def audit_tls(site, host, days_fn=tls_days_left):
    try:
        days = days_fn(host)
    except Exception as e:
        return [r(site, "tls", "FAIL", f"TLS handshake/validation failed: {str(e)[:150]}")]
    level = "FAIL" if days < TLS_FAIL_DAYS else "WARN" if days < TLS_WARN_DAYS else "PASS"
    return [r(site, "tls", level, f"certificate expires in {days} days")]


def audit_seo(site, page):
    m = page.meta
    title = page.title.strip()
    out = [
        r(site, "title", "PASS" if title else "FAIL", title[:80] or "no <title> in served HTML"),
        r(site, "viewport", "PASS" if "viewport" in m else "FAIL", m.get("viewport", "no viewport meta")),
        r(site, "description", "PASS" if m.get("description") else "WARN",
          f"{len(m.get('description', ''))} chars" if m.get("description") else "no meta description"),
        r(site, "og-tags", "PASS" if m.get("og:title") and m.get("og:image") else "WARN",
          "og:title + og:image" if m.get("og:title") and m.get("og:image") else "missing og:title or og:image"),
        r(site, "lang", "PASS" if page.lang else "WARN", page.lang or "no <html lang>"),
    ]
    canon = [l.get("href") for l in page.links if "canonical" in l.get("rel", "").lower()]
    out.append(r(site, "canonical", "PASS" if canon else "WARN", canon[0] if canon else "no canonical link"))
    return out


def audit_text_files(site, base, fetch_fn):
    out, sitemap_urls = [], []
    st, _, body, _, _ = fetch_fn(urljoin(base, "/robots.txt"))
    out.append(r(site, "robots.txt", "PASS" if st == 200 else "WARN", f"HTTP {st}"))
    st, _, body, _, _ = fetch_fn(urljoin(base, "/sitemap.xml"))
    if st == 200:
        try:
            root = ET.fromstring(body.encode("utf-8"))
            sitemap_urls = [e.text.strip() for e in root.iter() if e.tag.endswith("loc") and e.text]
            out.append(r(site, "sitemap.xml", "PASS", f"{len(sitemap_urls)} URLs"))
        except ET.ParseError as e:
            out.append(r(site, "sitemap.xml", "WARN", f"served but not valid XML: {e}"))
    else:
        out.append(r(site, "sitemap.xml", "WARN", f"HTTP {st}"))
    st, _, _, _, _ = fetch_fn(urljoin(base, "/llms.txt"))
    out.append(r(site, "llms.txt", "PASS" if st == 200 else "WARN", f"HTTP {st}"))
    return out, sitemap_urls


def internal_links(base, hrefs):
    host = urlparse(base).hostname
    seen = []
    for h in hrefs:
        if h.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
            continue
        u = urljoin(base, h).split("#")[0]
        p = urlparse(u)
        if p.scheme in ("http", "https") and (p.hostname or "").removeprefix("www.") == host.removeprefix("www.") \
                and u not in seen:
            seen.append(u)
    return seen


def audit_links(site, urls, fetch_fn, label="links"):
    # Evenly spaced sample so a 400-URL sitemap is not judged by its first 40 entries.
    step = max(1, -(-len(urls) // MAX_LINKS))
    broken, checked = [], urls[::step][:MAX_LINKS]
    for u in checked:
        st, _, _, _, err = fetch_fn(u, limit=1)
        if st == 0 or st >= 400:
            broken.append(f"{u} -> {st or err}")
    detail = f"{len(checked)} checked" + (f" ({len(urls) - len(checked)} more not checked)" if len(urls) > len(checked) else "")
    if broken:
        return [r(site, label, "FAIL", f"{len(broken)} broken of {detail}: " + "; ".join(broken[:5]))]
    return [r(site, label, "PASS", detail)]


def audit_site_http(site, fetch_fn=fetch, days_fn=tls_days_left):
    sid, base = site["site_id"], site["production_url"]
    st, headers, html, final, err = fetch_fn(base)
    if st != 200:
        return [r(sid, "homepage", "FAIL", f"{base} -> HTTP {st or err}")]
    out = [r(sid, "homepage", "PASS", f"HTTP 200 ({final})")]
    if urlparse(final).scheme == "https":
        out += audit_tls(sid, urlparse(final).hostname, days_fn)
    else:
        out.append(r(sid, "tls", "FAIL", f"served over {urlparse(final).scheme}"))
    out += audit_headers(sid, headers, html)
    page = PageParser()
    page.feed(html)
    out += audit_seo(sid, page)
    og = page.meta.get("og:image")
    if og:
        ost, _, _, _, oerr = fetch_fn(urljoin(final, og), limit=1)
        out.append(r(sid, "og-image", "PASS" if ost == 200 else "FAIL", f"{og} -> HTTP {ost or oerr}"))
    files, sitemap_urls = audit_text_files(sid, final, fetch_fn)
    out += files
    out += audit_links(sid, internal_links(final, page.hrefs), fetch_fn, "links-served-html")
    if sitemap_urls:
        out += audit_links(sid, sitemap_urls, fetch_fn, "links-sitemap")
    return out


# ---------- browser pass ----------

def run_browser(sites, runner=subprocess.run):
    """Run browser/site_smoke.js; returns result rows. Exit 3 from the runner = could not start."""
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    skip_level = "FAIL" if in_ci else "SKIPPED"
    args = ["node", SMOKE_JS]
    for s in sites:
        args += ["--site", f"{s['site_id']}={s['production_url']}"]
    try:
        proc = runner(args, capture_output=True, text=True, encoding="utf-8", timeout=600, cwd=os.path.dirname(SMOKE_JS))
    except (OSError, subprocess.TimeoutExpired) as e:
        return [r(s["site_id"], "browser", skip_level, f"browser smoke not run: {e}") for s in sites]
    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        tail = (proc.stderr or proc.stdout or "")[-300:]
        return [r(s["site_id"], "browser", skip_level, f"browser smoke gave no result (exit {proc.returncode}): {tail}") for s in sites]
    if payload.get("skipped"):
        return [r(s["site_id"], "browser", skip_level, f"browser smoke not run: {payload['skipped']}") for s in sites]
    return payload.get("results", [])


# ---------- reporting ----------

def worst(rows):
    return max((x["level"] for x in rows), key=lambda l: RANK[l], default="PASS")


def print_report(rows, site_ids):
    icon = {"PASS": "[OK]  ", "WARN": "[WARN]", "FAIL": "[FAIL]", "SKIPPED": "[SKIP]", "UNVERIFIED": "[----]"}
    for sid in site_ids:
        mine = [x for x in rows if x["site_id"] == sid]
        print(f"\n[SITE] {sid} -> {worst(mine)}")
        for x in sorted(mine, key=lambda x: -RANK[x["level"]]):
            print(f"  {icon[x['level']]} {x['check']}: {x['detail']}")
    counts = {lvl: sum(1 for x in rows if x["level"] == lvl) for lvl in RANK}
    print("\n" + "=" * 65)
    print(" LIVE AUDIT: " + " | ".join(f"{k} {v}" for k, v in counts.items() if v))
    print("=" * 65)


def failures(rows):
    """Rows that should alert, as cloud_runner failed_sites entries."""
    sites = {}
    for x in rows:
        if x["level"] == "FAIL":
            sites.setdefault(x["site_id"], []).append(f"{x['check']}: {x['detail']}")
    return [{"site_id": f"{sid} (live audit)", "url": "", "error": " | ".join(errs)[:600]} for sid, errs in sites.items()]


def run(site_filter=None, http=True, browser=True, write=True):
    sites = [s for s in load_websites() if s.get("production_url") and (not site_filter or s["site_id"] == site_filter)]
    if not sites:
        print(f"[ERROR] no registered site matches {site_filter!r}")
        return [r(site_filter or "-", "registry", "FAIL", "no matching site")]
    if not netcheck.network_up():
        rows = [r(s["site_id"], "network", "UNVERIFIED", "machine offline, nothing checked") for s in sites]
    else:
        rows = []
        if http:
            for s in sites:
                rows += audit_site_http(s)
        if browser:
            rows += run_browser(sites)
    print_report(rows, [s["site_id"] for s in sites])
    if write:
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump({"checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "results": rows}, f, indent=2)
    return rows


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--site", help="one site_id from registry/websites.json")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--http-only", action="store_true")
    g.add_argument("--browser-only", action="store_true")
    a = p.parse_args(argv)
    print("=" * 65)
    print(" [WEB-OPS] LIVE PRODUCTION AUDIT")
    print("=" * 65)
    rows = run(a.site, http=not a.browser_only, browser=not a.http_only)
    return 1 if any(x["level"] == "FAIL" for x in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
