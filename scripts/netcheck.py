"""Is this machine online? A probe that gets no HTTP answer while the laptop has no
network says nothing about the target, so it must read "unverified", never "unhealthy"
(same rule as automations/email-ops)."""

import socket

# Raw IPs on 443: no DNS needed, so a DNS outage cannot fake "online".
_CANARIES = (("1.1.1.1", 443), ("8.8.8.8", 443))


def network_up(timeout=3, connect=socket.create_connection):
    for host, port in _CANARIES:
        try:
            connect((host, port), timeout).close()
            return True
        except OSError:
            continue
    return False


def apply_offline(results, up=network_up):
    """Turn no-answer failures (status UNHEALTHY, code 0) into UNVERIFIED when the
    machine is offline. Real HTTP errors (code != 0) are never touched. The canary
    runs only if there is a no-answer failure to explain."""
    silent = [r for r in results if r.get("status") == "UNHEALTHY" and not r.get("code")]
    if not silent or up():
        return results
    for r in silent:
        r["status"] = "UNVERIFIED"
        r["error"] = f"machine offline, not checked ({r.get('error')})"[:200]
    return results
