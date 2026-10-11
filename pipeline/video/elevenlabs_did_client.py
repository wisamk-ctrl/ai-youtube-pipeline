"""
Phase 3 — Option B: ElevenLabs (cloned voice) + D-ID (talking-head video).

Use this path when you want finer control of the voice (ElevenLabs' cloning
and Arabic prosody are excellent) or already own a D-ID presenter.

    1. ElevenLabs TTS, chunk by chunk, with `previous_text` / `next_text` so
       each chunk's intonation flows into the next     → one MP3
    2. Upload the MP3 to D-ID                          → s3:// audio URL
    3. D-ID Clips API with your presenter_id + that audio → MP4

Endpoints:
    POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}   (header xi-api-key)
    POST https://api.d-id.com/audios                               (multipart "audio")
    POST https://api.d-id.com/clips                                → {"id"}
    GET  https://api.d-id.com/clips/{id}                           → {"status", "result_url"}

D-ID auth is `Authorization: Basic <API key as shown in the D-ID studio>`.
Check your D-ID plan's maximum clip duration; if an 8-minute clip exceeds it,
render one clip per chunk and concatenate (see README).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

from pipeline.config import require_env
from pipeline.video.common import VideoGenerationError, download, http, http_once, poll_until

log = logging.getLogger(__name__)

ELEVEN = "https://api.elevenlabs.io/v1"
DID = "https://api.d-id.com"


class ElevenLabsVoice:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.ecfg = cfg["video"]["elevenlabs"]
        self.voice_id = require_env("ELEVENLABS_VOICE_ID")
        self.session = requests.Session()
        self.session.headers.update({"xi-api-key": require_env("ELEVENLABS_API_KEY"), "Accept": "audio/mpeg"})

    def synthesize(self, chunks: list[str], dest: Path) -> Path:
        """Render each chunk and append the MP3 frames into one file.

        MP3 is a frame-based format, so byte-concatenating same-encoder output
        plays back seamlessly; no ffmpeg needed. `previous_text`/`next_text`
        give the model the neighbouring context, so sentence-final intonation
        doesn't reset at every chunk boundary.
        """
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as out:
            for idx, chunk in enumerate(chunks):
                payload = {
                    "text": chunk,
                    "model_id": self.ecfg["model_id"],
                    "language_code": "ar",
                    "voice_settings": {
                        "stability": self.ecfg["stability"],
                        "similarity_boost": self.ecfg["similarity_boost"],
                        "style": self.ecfg["style"],
                        "use_speaker_boost": self.ecfg["use_speaker_boost"],
                    },
                    "previous_text": chunks[idx - 1] if idx > 0 else None,
                    "next_text": chunks[idx + 1] if idx + 1 < len(chunks) else None,
                }
                resp = http(self.session, "POST", f"{ELEVEN}/text-to-speech/{self.voice_id}",
                            params={"output_format": "mp3_44100_128"},
                            json={k: v for k, v in payload.items() if v is not None}, timeout=180)
                out.write(resp.content)
                log.info("ElevenLabs chunk %d/%d: %d bytes", idx + 1, len(chunks), len(resp.content))
        return dest


class DIDVideo:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.vcfg = cfg["video"]
        self.presenter_id = require_env("DID_PRESENTER_ID")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Basic {require_env('DID_API_KEY')}",
                                     "Accept": "application/json"})

    def upload_audio(self, audio: Path) -> str:
        # Pass bytes, not a file handle: a retried request would re-send an
        # exhausted handle as an empty upload.
        data = audio.read_bytes()
        resp = http(self.session, "POST", f"{DID}/audios",
                    files={"audio": (audio.name, data, "audio/mpeg")}, timeout=300)
        return resp.json()["url"]

    def submit(self, audio_url: str) -> str:
        payload = {
            "presenter_id": self.presenter_id,
            "script": {"type": "audio", "audio_url": audio_url},
            "config": {"result_format": "mp4"},
        }
        body = http_once(self.session, "POST", f"{DID}/clips", json=payload).json()
        if "id" not in body:
            raise VideoGenerationError(f"D-ID rejected the job: {body}")
        log.info("D-ID clip submitted: %s", body["id"])
        return body["id"]

    def wait(self, clip_id: str) -> str:
        def check() -> tuple[str, dict[str, Any]]:
            data = http(self.session, "GET", f"{DID}/clips/{clip_id}").json()
            return data.get("status", "unknown"), data

        data = poll_until(check, done={"done"}, failed={"error", "rejected"},
                          interval=self.vcfg["poll_interval_s"], timeout=self.vcfg["poll_timeout_s"],
                          label=f"D-ID {clip_id}")
        return data["result_url"]


class ElevenLabsDIDPipeline:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.voice = ElevenLabsVoice(cfg)
        self.video = DIDVideo(cfg)

    def render(self, chunks: list[str], title: str, dest: Path) -> Path:  # noqa: ARG002 — title unused by D-ID
        audio = self.voice.synthesize(chunks, dest.with_suffix(".mp3"))
        clip_id = self.video.submit(self.video.upload_audio(audio))
        dest.with_suffix(".job.txt").write_text(f"did:{clip_id}\n", encoding="utf-8")
        return download(self.video.wait(clip_id), dest)

    def resume(self, clip_id: str, dest: Path) -> Path:
        return download(self.video.wait(clip_id), dest)
