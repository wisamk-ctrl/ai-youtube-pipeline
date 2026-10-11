"""Shared plumbing for the avatar providers: retrying HTTP, job polling, streaming download."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Callable

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)


class VideoGenerationError(RuntimeError):
    pass


def _is_retryable(exc: BaseException) -> bool:
    """Retry network errors, 429 and 5xx. Never retry 4xx — a bad request stays bad (and may bill)."""
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return False


def http_once(session: requests.Session, method: str, url: str, **kwargs: Any) -> requests.Response:
    """Single attempt. Use for job *submissions*: retrying a POST whose response
    was lost could start (and bill) a second render of the same episode."""
    kwargs.setdefault("timeout", 60)
    resp = session.request(method, url, **kwargs)
    if resp.status_code >= 400:
        # Surface the provider's error body — it usually says exactly what's wrong
        # (unknown avatar_id, text too long, quota exhausted...).
        log.error("%s %s → %s: %s", method, url, resp.status_code, resp.text[:500])
    resp.raise_for_status()
    return resp


# Retrying variant for idempotent calls (status polls, uploads, TTS chunks).
http = retry(retry=retry_if_exception(_is_retryable), stop=stop_after_attempt(5),
             wait=wait_exponential(multiplier=2, max=60), reraise=True)(http_once)


def poll_until(check: Callable[[], tuple[str, dict[str, Any]]], done: set[str], failed: set[str],
               interval: int, timeout: int, label: str) -> dict[str, Any]:
    """Poll a render job until it reaches a terminal state.

    `check` returns (status, payload). Rendering 8 minutes of avatar video
    typically takes 10-30 min, so the default interval is deliberately slow.
    """
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        status, payload = check()
        if status != last:
            log.info("%s status: %s", label, status)
            last = status
        if status in done:
            return payload
        if status in failed:
            raise VideoGenerationError(f"{label} failed: {payload}")
        time.sleep(interval)
    raise VideoGenerationError(f"{label} did not finish within {timeout}s (last status: {last})")


def download(url: str, dest: Path) -> Path:
    """Stream a (potentially multi-GB) file to disk without loading it into memory."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
    tmp.replace(dest)  # atomic: a half-downloaded file never looks finished
    log.info("Saved %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
    return dest
