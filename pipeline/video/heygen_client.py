"""
Phase 3 — Option A: HeyGen (voice + avatar in one API).

HeyGen renders your custom avatar speaking with your cloned voice from text.
A long script is sent as several *scenes* (`video_inputs`), each with the same
avatar and voice, which HeyGen stitches into one MP4. Splitting on sentence
boundaries keeps each scene under the per-scene text limit and avoids
mid-sentence cuts.

Endpoints used (HeyGen API v2):
    POST /v2/video/generate                 → {"data": {"video_id": ...}}
    GET  /v1/video_status.get?video_id=...  → {"data": {"status", "video_url", "error"}}

`video_url` is a short-lived signed URL, so we download immediately.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests

from pipeline.config import require_env
from pipeline.video.common import VideoGenerationError, download, http, http_once, poll_until

log = logging.getLogger(__name__)

BASE = "https://api.heygen.com"
MAX_SCENES = 50  # HeyGen's limit on video_inputs per request


class HeyGenClient:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.vcfg = cfg["video"]
        self.hcfg = dict(cfg["video"]["heygen"])
        if os.environ.get("HEYGEN_AVATAR_TYPE"):
            self.hcfg["avatar_type"] = os.environ["HEYGEN_AVATAR_TYPE"]
        self.avatar_id = require_env("HEYGEN_AVATAR_ID")
        self.voice_id = require_env("HEYGEN_VOICE_ID")
        self.session = requests.Session()
        self.session.headers.update({
            "X-Api-Key": require_env("HEYGEN_API_KEY"),
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _character(self) -> dict[str, Any]:
        """Your digital twin. Studio/Instant avatars use `avatar`; photo avatars use `talking_photo`."""
        if self.hcfg["avatar_type"] == "talking_photo":
            return {"type": "talking_photo", "talking_photo_id": self.avatar_id}
        return {"type": "avatar", "avatar_id": self.avatar_id, "avatar_style": self.hcfg["avatar_style"]}

    def build_payload(self, chunks: list[str], title: str) -> dict[str, Any]:
        """One scene per text chunk; identical avatar/voice/background keeps cuts invisible."""
        if len(chunks) > MAX_SCENES:
            raise VideoGenerationError(f"{len(chunks)} scenes exceeds HeyGen's {MAX_SCENES}; raise max_chars_per_chunk")
        return {
            "title": title,
            "caption": False,  # burn captions in post, where Arabic RTL typography can be controlled
            "dimension": {"width": self.hcfg["width"], "height": self.hcfg["height"]},
            **({"quality": self.hcfg["quality"]} if self.hcfg.get("quality") else {}),
            "video_inputs": [
                {
                    "character": self._character(),
                    "voice": {
                        "type": "text",
                        "input_text": chunk,
                        "voice_id": self.voice_id,
                        "speed": self.hcfg["voice_speed"],
                    },
                    "background": {"type": "color", "value": self.hcfg["background_color"]},
                }
                for chunk in chunks
            ],
        }

    def submit(self, chunks: list[str], title: str) -> str:
        resp = http_once(self.session, "POST", f"{BASE}/v2/video/generate", json=self.build_payload(chunks, title))
        body = resp.json()
        if body.get("error") or not body.get("data", {}).get("video_id"):
            raise VideoGenerationError(f"HeyGen rejected the job: {body}")
        video_id = body["data"]["video_id"]
        log.info("HeyGen job submitted: %s (%d scenes)", video_id, len(chunks))
        return video_id

    def wait(self, video_id: str) -> str:
        def check() -> tuple[str, dict[str, Any]]:
            data = http(self.session, "GET", f"{BASE}/v1/video_status.get",
                        params={"video_id": video_id}).json().get("data", {})
            return data.get("status", "unknown"), data

        data = poll_until(check, done={"completed"}, failed={"failed"},
                          interval=self.vcfg["poll_interval_s"], timeout=self.vcfg["poll_timeout_s"],
                          label=f"HeyGen {video_id}")
        return data["video_url"]

    def render(self, chunks: list[str], title: str, dest: Path) -> Path:
        video_id = self.submit(chunks, title)
        # Persist the job ID first: if this process dies mid-poll, the render
        # (which is already billed) can be recovered with `--resume-video-id`.
        dest.with_suffix(".job.txt").write_text(f"heygen:{video_id}\n", encoding="utf-8")
        return download(self.wait(video_id), dest)

    def resume(self, video_id: str, dest: Path) -> Path:
        return download(self.wait(video_id), dest)
