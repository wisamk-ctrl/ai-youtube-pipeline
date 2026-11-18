"""WhatsApp alerts to the founder (founder 2026-11-18: "send me a WhatsApp message while you're compiling the script").

Sent through CallMeBot's free personal WhatsApp API: the founder activates it once from his phone, then the repo
secrets WHATSAPP_PHONE (international format, e.g. +9715…) and CALLMEBOT_APIKEY switch it on. Without them, or if
the service is down, nothing is sent and nothing fails: GitHub's issue comment stays the record."""
from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)
API = "https://api.callmebot.com/whatsapp.php"


def whatsapp(text: str, http=None) -> bool:
    phone, key = os.environ.get("WHATSAPP_PHONE", "").strip(), os.environ.get("CALLMEBOT_APIKEY", "").strip()
    if not phone or not key:
        return False
    try:
        import requests
        http = http or requests
        r = http.get(API, params={"phone": phone, "text": text[:900], "apikey": key}, timeout=30)
        ok = 200 <= r.status_code < 300
        if not ok:
            log.warning("WhatsApp alert not sent: HTTP %s", r.status_code)
        return ok
    except Exception as exc:  # noqa: BLE001 — an alert must never sink the run
        log.warning("WhatsApp alert not sent: %s", type(exc).__name__)
        return False


if __name__ == "__main__":
    import sys
    print("sent" if whatsapp(" ".join(sys.argv[1:]) or "Test from AI This Week") else "not sent")
