"""Offline laptop => probes read 'unverified', never 'unhealthy'."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import netcheck  # noqa: E402


def res(status, code=0):
    return {"status": status, "code": code, "error": "getaddrinfo failed"}


class ApplyOffline(unittest.TestCase):
    def test_offline_turns_no_answer_failures_unverified(self):
        r = netcheck.apply_offline([res("UNHEALTHY")], up=lambda: False)
        self.assertEqual(r[0]["status"], "UNVERIFIED")
        self.assertIn("offline", r[0]["error"])

    def test_online_keeps_real_failure(self):
        r = netcheck.apply_offline([res("UNHEALTHY")], up=lambda: True)
        self.assertEqual(r[0]["status"], "UNHEALTHY")

    def test_http_errors_are_never_downgraded(self):
        r = netcheck.apply_offline([res("DEGRADED", 500), res("UNHEALTHY", 503)], up=lambda: False)
        self.assertEqual([x["status"] for x in r], ["DEGRADED", "UNHEALTHY"])

    def test_healthy_untouched_and_canary_not_called(self):
        def boom():
            raise AssertionError("canary must not run when nothing failed silently")
        r = netcheck.apply_offline([res("HEALTHY", 200), res("DEGRADED", 500)], up=boom)
        self.assertEqual([x["status"] for x in r], ["HEALTHY", "DEGRADED"])

    def test_network_up_false_when_every_connect_fails(self):
        def refuse(addr, timeout):
            raise OSError("unreachable")
        self.assertFalse(netcheck.network_up(connect=refuse))

    def test_network_up_true_when_one_canary_answers(self):
        calls = []

        class Sock:
            def close(self):
                pass

        def second_works(addr, timeout):
            calls.append(addr)
            if len(calls) == 1:
                raise OSError("first down")
            return Sock()
        self.assertTrue(netcheck.network_up(connect=second_works))


class HealthLogWriter(unittest.TestCase):
    def test_all_sites_unverified_writes_unverified(self):
        import tempfile, json, health_check
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "Dashboard"))
        fake = os.path.join(d, "web-ops-os", "scripts")
        os.makedirs(fake)
        real_file = health_check.__file__
        health_check.__file__ = os.path.join(fake, "health_check.py")
        try:
            sites = [{"site_id": "isaan-tea", "name": "Isaan", "url": "u", "status": "UNVERIFIED",
                      "code": 0, "latency_ms": 5, "error": "offline"}]
            health_check.update_dashboard_health_log(sites)
        finally:
            health_check.__file__ = real_file
        log = json.load(open(os.path.join(d, "Dashboard", "health-check-log.json"), encoding="utf-8"))
        self.assertEqual(log["automations"]["web-ops-os"]["result"], "unverified")
        self.assertEqual(log["automations"]["Isaan_Tea_V1"]["result"], "unverified")


if __name__ == "__main__":
    unittest.main()
