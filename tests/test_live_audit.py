"""live_audit + browser smoke catch real faults on a local fake site, and never read green
when they could not check."""
import json
import os
import shutil
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import live_audit  # noqa: E402
import cloud_runner  # noqa: E402

GOOD = """<!doctype html><html lang="en"><head><title>Good page</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="A perfectly ordinary test page used by the live audit tests here.">
<link rel="canonical" href="/good"></head>
<body><h1>Hello</h1><p>Plenty of visible text so the content check has something real to measure.</p>
<a href="/ok">ok</a> <a href="/missing">missing</a> <a href="mailto:x@y.z">mail</a> <a href="https://elsewhere.test/">ext</a>
</body></html>"""

BAD = """<!doctype html><html><head>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter">
</head><body><div style="width:900px">Too wide for a phone, which is the whole point of this test page.</div>
<img src="/missing.png" alt="x"><img src="/ok">
<script>throw new Error("boom from test page")</script></body></html>"""

WIDE = """<!doctype html><html lang="en"><head><title>Wide</title>
<meta name="viewport" content="width=device-width, initial-scale=1"><style>body{margin:0}</style></head>
<body><div id="hero" style="width:900px">A fixed 900px block on a responsive page overflows any phone.</div></body></html>"""

NUDGE = """<!doctype html><html lang="en"><head><title>Nudge</title>
<meta name="viewport" content="width=device-width, initial-scale=1"><style>body{margin:0}</style></head>
<body><div style="width:379px">Four pixels too wide on a 375px phone: a warning, not a failure.</div></body></html>"""

ROUTES = {
    "/good": (200, {}, GOOD),
    "/wide": (200, {}, WIDE),
    "/nudge": (200, {}, NUDGE),
    # script-src allows inline so the test exception really runs; style-src blocks Google Fonts.
    "/bad": (200, {"Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'"}, BAD),
    "/ok": (200, {}, "<p>ok</p>"),
    "/robots.txt": (200, {}, "User-agent: *\n"),
    "/sitemap.xml": (200, {}, ""),  # filled in setUpClass with the real port
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, headers, body = ROUTES.get(self.path.split("?")[0], (404, {}, "not found"))
        self.send_response(status)
        self.send_header("Content-Type", "application/xml" if self.path.endswith(".xml") else "text/html")
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


class FakeSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"
        ROUTES["/sitemap.xml"] = (200, {}, f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                                  f"<url><loc>{cls.base}/ok</loc></url><url><loc>{cls.base}/gone</loc></url></urlset>")
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def http(self, path):
        rows = live_audit.audit_site_http({"site_id": "t", "production_url": self.base + path}, days_fn=lambda h: 90)
        return {x["check"]: x for x in rows}


class HttpChecks(FakeSite):
    def test_broken_links_in_html_and_sitemap_fail(self):
        rows = self.http("/good")
        self.assertEqual(rows["links-served-html"]["level"], "FAIL")
        self.assertIn("/missing -> 404", rows["links-served-html"]["detail"])
        self.assertNotIn("elsewhere.test", rows["links-served-html"]["detail"])
        self.assertEqual(rows["links-sitemap"]["level"], "FAIL")
        self.assertIn("/gone -> 404", rows["links-sitemap"]["detail"])

    def test_good_page_seo_passes(self):
        rows = self.http("/good")
        for check in ("homepage", "title", "viewport", "description", "canonical", "lang", "robots.txt"):
            self.assertEqual(rows[check]["level"], "PASS", check)

    def test_plain_http_is_a_tls_fail(self):
        self.assertEqual(self.http("/good")["tls"]["level"], "FAIL")

    def test_missing_title_viewport_and_font_blocking_csp_fail(self):
        rows = self.http("/bad")
        self.assertEqual(rows["title"]["level"], "FAIL")
        self.assertEqual(rows["viewport"]["level"], "FAIL")
        self.assertEqual(rows["csp-fonts"]["level"], "FAIL")
        self.assertIn("fonts.googleapis.com", rows["csp-fonts"]["detail"])

    def test_dead_homepage_fails(self):
        rows = self.http("/nope")
        self.assertEqual(rows["homepage"]["level"], "FAIL")


class Units(unittest.TestCase):
    def test_tls_thresholds(self):
        level = lambda d: live_audit.audit_tls("t", "h", lambda h: d)[0]["level"]
        self.assertEqual([level(5), level(20), level(90)], ["FAIL", "WARN", "PASS"])

    def test_tls_handshake_error_fails(self):
        def bad(h):
            raise OSError("certificate verify failed")
        self.assertEqual(live_audit.audit_tls("t", "h", bad)[0]["level"], "FAIL")

    def test_csp_allows(self):
        csp = live_audit.parse_csp("default-src 'self'; font-src 'self' https: data:; style-src 'self' https://fonts.googleapis.com")
        self.assertTrue(live_audit.csp_allows(csp, "font-src", "fonts.gstatic.com"))
        self.assertTrue(live_audit.csp_allows(csp, "style-src", "fonts.googleapis.com"))
        self.assertFalse(live_audit.csp_allows(csp, "connect-src", "api.example.com"))  # falls back to default-src
        self.assertTrue(live_audit.csp_allows(live_audit.parse_csp("default-src *.gstatic.com"), "font-src", "fonts.gstatic.com"))

    def test_failures_groups_only_fails(self):
        rows = [live_audit.r("a", "x", "FAIL", "1"), live_audit.r("a", "y", "WARN", "2"), live_audit.r("b", "z", "PASS", "")]
        f = live_audit.failures(rows)
        self.assertEqual(len(f), 1)
        self.assertIn("x: 1", f[0]["error"])

    def test_offline_reads_unverified_not_fail(self):
        with mock.patch.object(live_audit.netcheck, "network_up", return_value=False):
            rows = live_audit.run(write=False)
        self.assertTrue(rows)
        self.assertTrue(all(x["level"] == "UNVERIFIED" for x in rows))


class BrowserCouldNotRun(unittest.TestCase):
    SITES = [{"site_id": "t", "production_url": "https://x.test"}]

    def fake(self, stdout, code=3):
        return lambda *a, **k: mock.Mock(stdout=stdout, stderr="", returncode=code)

    def test_skipped_locally_is_skipped_not_pass(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": ""}):
            rows = live_audit.run_browser(self.SITES, runner=self.fake('{"skipped": "no Chrome found"}'))
        self.assertEqual(rows[0]["level"], "SKIPPED")

    def test_skipped_in_github_actions_is_fail(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            rows = live_audit.run_browser(self.SITES, runner=self.fake('{"skipped": "no Chrome found"}'))
        self.assertEqual(rows[0]["level"], "FAIL")

    def test_garbage_output_and_missing_node_never_pass(self):
        def no_node(*a, **k):
            raise FileNotFoundError("node")
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": ""}):
            self.assertEqual(live_audit.run_browser(self.SITES, runner=self.fake("Segfault"))[0]["level"], "SKIPPED")
            self.assertEqual(live_audit.run_browser(self.SITES, runner=no_node)[0]["level"], "SKIPPED")


HAVE_BROWSER = shutil.which("node") and os.path.exists(
    os.path.join(os.path.dirname(live_audit.SMOKE_JS), "node_modules", "puppeteer-core"))


@unittest.skipUnless(HAVE_BROWSER, "puppeteer-core not installed (npm ci in browser/)")
class BrowserSmoke(FakeSite):
    def smoke(self, path):
        rows = live_audit.run_browser([{"site_id": "t", "production_url": self.base + path}])
        return {x["check"]: x for x in rows}

    def test_wide_block_overflows_phone_and_tablet_not_desktop(self):
        rows = self.smoke("/wide")
        self.assertNotIn("browser", rows, rows.get("browser"))
        self.assertEqual(rows["overflow@mobile"]["level"], "FAIL")
        self.assertIn("div#hero", rows["overflow@mobile"]["detail"])
        self.assertEqual(rows["overflow@tablet"]["level"], "FAIL")
        self.assertEqual(rows["overflow@desktop"]["level"], "PASS")

    def test_few_px_over_is_warn_not_fail(self):
        rows = self.smoke("/nudge")
        self.assertEqual(rows["overflow@mobile"]["level"], "WARN")
        self.assertEqual(rows["overflow@tablet"]["level"], "PASS")

    def test_bad_page_exception_csp_and_404_asset_fail(self):
        rows = self.smoke("/bad")
        self.assertNotIn("browser", rows, rows.get("browser"))
        self.assertEqual(rows["js-exceptions@mobile"]["level"], "FAIL")
        self.assertIn("boom", rows["js-exceptions@mobile"]["detail"])
        self.assertEqual(rows["csp-blocks@desktop"]["level"], "FAIL")
        self.assertEqual(rows["same-origin-requests@desktop"]["level"], "FAIL")
        self.assertIn("/missing.png", rows["same-origin-requests@desktop"]["detail"])
        self.assertEqual(rows["rendered-img-alt"]["level"], "WARN")
        self.assertEqual(rows["rendered-h1"]["level"], "WARN")

    def test_good_page_passes_but_rendered_broken_link_fails(self):
        rows = self.smoke("/good")
        for vp in ("mobile", "tablet", "desktop"):
            for check in ("overflow", "js-exceptions", "csp-blocks", "same-origin-requests", "content"):
                self.assertEqual(rows[f"{check}@{vp}"]["level"], "PASS", f"{check}@{vp}: {rows[f'{check}@{vp}']}")
        self.assertEqual(rows["links-rendered"]["level"], "FAIL")
        self.assertIn("/missing", rows["links-rendered"]["detail"])


class CloudRunnerGoesRed(unittest.TestCase):
    def run_cloud(self, probe_status, sent):
        probes = [{"status": probe_status, "id": "p", "name": "probe", "url": "u", "error": "e"}]
        with mock.patch.object(cloud_runner.health_check, "load_websites", return_value=[]), \
             mock.patch.object(cloud_runner.backend_deep_probe, "run_deep_probes", return_value=probes), \
             mock.patch.object(cloud_runner.live_audit, "run", return_value=[]), \
             mock.patch.object(cloud_runner, "send_alert_email", return_value=sent) as send:
            cloud_runner.main()
        return send

    def test_failure_with_unsent_alert_exits_1(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_cloud("UNHEALTHY", sent=False)
        self.assertEqual(cm.exception.code, 1)

    def test_failure_with_sent_alert_stays_green(self):
        self.assertTrue(self.run_cloud("UNHEALTHY", sent=True).called)

    def test_no_failures_sends_nothing(self):
        self.assertFalse(self.run_cloud("HEALTHY", sent=False).called)

    def test_missing_credentials_report_not_sent(self):
        with mock.patch.dict(os.environ, {"GMAIL_USER": "", "SMTP_USER": "", "GMAIL_APP_PASSWORD": "", "SMTP_PASS": ""}):
            self.assertFalse(cloud_runner.send_alert_email([{"site_id": "x"}], 1))


if __name__ == "__main__":
    unittest.main()
