"""
Voice-first render route: the narration is made as speech with the presenter's voice clone, and
the avatar is rendered only for the two face stretches (the opening and the sign-off), driven by
that same audio. About 33 credits for a 9-minute episode instead of 63, with better lip sync
(docs/STATUS.md, "Voice-first render").

HeyGen API credits are empty, so CI never calls HeyGen. The route runs in three steps:

1. Voice pack (CI): `write_voice_pack()` turns the directed script into
   output/<week>/voice_pack.json + voice_pack.md, an ordered list of chunks
   `{id, role: face|voice, text}`. The text is the speakable form with <break time="Xs"/> pauses.
   Face chunks are the words under the first [Face] marker (opening) and under the last one
   (sign-off), each capped to visuals.face_keep_seconds at the script's words per minute and
   ending on a sentence boundary. Everything else is in voice chunks of at most
   video.voicefirst.max_chars characters, split on sentences.
2. Speech and face videos (chat session, HeyGen connector): one `create_speech` call per chunk
   with the voice clone; for a face chunk also `create_video_from_avatar` with `audioUrl` = that
   speech's URL (Avatar IV, the look in settings). The links go into reviewed/<week>/voice.yaml:

       01-face:
         audio: https://resource2.heygen.ai/.../speech.mp3
         duration: 7.9                      # optional, as the speech tool reported it
         video: https://files2.heygen.ai/.../face.mp4
       02-voice:
         audio: https://resource2.heygen.ai/.../speech.mp3
       02-voice: https://...                # a voice chunk may also be just its audio URL

   The ids must be exactly the pack's ids; any other file is rejected.
3. Assemble (CI, phase `assemble`): `assemble()` downloads every chunk, joins the audio in order
   with a short gap into narration.wav, and builds talking_head.mp4 of the narration's length: a
   dark backdrop with each face video at its chunk's position (its audio is the chunk audio, so
   the lips line up), narration as the sound. face_spans.json says where the faces are; the shot
   plan shows the face there and nowhere else. Post-production then runs as usual.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pipeline.script_format import (MARKER_RE, SENTENCE_END_RE, chunk_text, parse_shot, spoken_words,
                                    to_tts_text)
from pipeline.video.common import download

log = logging.getLogger(__name__)

_BREAK = re.compile(r'<break time="[\d.]+s"/>')


def _cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    return cfg.get("video", {}).get("voicefirst", {})


def _words(text: str) -> int:
    return len(spoken_words(_BREAK.sub(" ", text)))


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_END_RE.split(text.replace("\n", " ")) if _words(s)]


def pack(script: str, cfg: dict[str, Any]) -> list[dict[str, str]]:
    """The directed script as ordered speech chunks; [] when it has no shot markers."""
    marks = [(m, parse_shot(m.group("body"))) for m in MARKER_RE.finditer(script)]
    marks = [(m, p) for m, p in marks if p]
    if not marks:
        return []
    pause = float(cfg["video"].get("pause_seconds", 0.8))
    bounds = [m.start() for m, _ in marks[1:]] + [len(script)]
    parts = [("visual", script[:marks[0][0].start()])] + [(p[0], script[m.end():b]) for (m, p), b in zip(marks, bounds)]
    segs = [(mode, _sentences(to_tts_text(raw, "ssml", pause))) for mode, raw in parts]
    sents = [(n, s) for n, (_, ss) in enumerate(segs) for s in ss]      # (segment, sentence), in order
    faces = [n for n, (mode, ss) in enumerate(segs) if mode == "face" and ss]
    cap = float(cfg.get("visuals", {}).get("face_keep_seconds", 8)) * cfg["scripting"]["words_per_minute"] / 60

    def take(idx: list[int]) -> set[int]:
        """Sentences from the front of `idx` while they fit the cap (always at least one)."""
        got, words = set(), 0
        for i in idx:
            w = _words(sents[i][1])
            if got and words + w > cap:
                break
            got.add(i)
            words += w
        return got

    face: set[int] = set()
    if faces:
        face |= take([i for i, (n, _) in enumerate(sents) if n == faces[0]])
        if faces[-1] != faces[0]:
            face |= take([i for i, (n, _) in reversed(list(enumerate(sents))) if n == faces[-1]])
    groups: list[tuple[str, list[str]]] = []
    for i, (_, s) in enumerate(sents):
        role = "face" if i in face else "voice"
        if groups and groups[-1][0] == role:
            groups[-1][1].append(s)
        else:
            groups.append((role, [s]))
    limit = int(_cfg(cfg).get("max_chars", 4500))
    chunks: list[dict[str, str]] = []
    for role, ss in groups:
        for text in chunk_text(" ".join(ss), limit) if role == "voice" else [" ".join(ss)]:
            chunks.append({"id": f"{len(chunks) + 1:02d}-{role}", "role": role, "text": text})
    return chunks


def pack_md(chunks: list[dict[str, str]], cfg: dict[str, Any], week: str) -> str:
    h = cfg["video"]["heygen"]
    wpm = cfg["scripting"]["words_per_minute"]
    mins = {r: sum(_words(c["text"]) for c in chunks if c["role"] == r) / wpm for r in ("face", "voice")}
    credits = sum(max(1.0, _words(c["text"]) / wpm * 3) for c in chunks) + mins["face"] * 21
    lines = [
        f"# Voice-first pack · {week}",
        "",
        f"{len(chunks)} chunks · about {mins['face'] + mins['voice']:.1f} min of speech, {mins['face'] * 60:.0f} s of face"
        f" · ≈ {credits:.0f} credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).",
        "",
        f"1. Every chunk: `create_speech` with voice `{h.get('voice_id')}`, the text exactly as below (keep the break tags).",
        f"2. Face chunks also: `create_video_from_avatar` with look `{h.get('avatar_id')}` ({h.get('look_name', '')}),"
        " `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.",
        f"3. Commit `reviewed/{week}/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's",
        "   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.",
        "",
    ]
    for c in chunks:
        lines += [f"## {c['id']} ({c['role']}, {len(c['text'])} chars)", "", "```", c["text"], "```", ""]
    return "\n".join(lines)


def write_voice_pack(script: str, cfg: dict[str, Any], out_dir: Path) -> Path | None:
    chunks = pack(script, cfg)
    if not chunks:
        log.info("Voice pack: the script has no shot markers yet; written once it is directed")
        return None
    (out_dir / "voice_pack.json").write_text(json.dumps({"week": out_dir.name, "chunks": chunks}, ensure_ascii=False,
                                                        indent=2), encoding="utf-8")
    p = out_dir / "voice_pack.md"
    p.write_text(pack_md(chunks, cfg, out_dir.name), encoding="utf-8")
    log.info("Voice pack → %s (%d chunks)", p, len(chunks))
    return p


def load_voice(path: Path, chunks: list[dict[str, str]]) -> list[dict[str, Any]]:
    """reviewed/<week>/voice.yaml checked against the pack: one entry per chunk, in pack order."""
    import yaml
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a mapping of chunk id → audio/video links")
    data = {str(k): v for k, v in data.items()}
    ids = [c["id"] for c in chunks]
    missing, extra = [i for i in ids if i not in data], [i for i in data if i not in ids]
    if missing or extra:
        raise ValueError(f"{path.name} does not match the voice pack: missing {missing or 'none'}, "
                         f"not in the pack {extra or 'none'}")
    out = []
    for c in chunks:
        e = data[c["id"]]
        e = {"audio": e} if isinstance(e, str) else dict(e or {})
        for k in ("audio", "video") if c["role"] == "face" else ("audio",):
            if not str(e.get(k) or "").startswith(("http://", "https://")):
                raise ValueError(f"{path.name}: chunk {c['id']} needs an http(s) `{k}` link")
        out.append({**c, "audio": str(e["audio"]), "video": str(e.get("video") or ""),
                    "duration": float(e["duration"]) if e.get("duration") else None})
    return out


def _run(*args: str) -> None:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {r.stderr[-1500:]}")


def _duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def assemble(entries: list[dict[str, Any]], cfg: dict[str, Any], out_dir: Path) -> Path:
    """narration.wav + talking_head.mp4 (+ face_spans.json, talking_head.source.txt) from the chunks."""
    v, vf = cfg.get("visuals", {}), _cfg(cfg)
    w, h, fps = int(v.get("width", 1920)), int(v.get("height", 1080)), int(v.get("fps", 30))
    gap = float(vf.get("gap_seconds", 0.25))
    work = out_dir / "assemble"
    work.mkdir(parents=True, exist_ok=True)
    wavs, faces, t = [], [], 0.0
    for n, e in enumerate(entries):
        src = download(e["audio"], work / f"{e['id']}.audio")
        wav = work / f"{e['id']}.wav"
        _run("-i", str(src), "-vn", "-ar", "48000", "-ac", "2", str(wav))
        d = _duration(wav)
        if e.get("duration") and abs(d - e["duration"]) > 0.5:
            log.warning("Chunk %s is %.1fs, voice.yaml says %.1fs", e["id"], d, e["duration"])
        if e["role"] == "face":
            faces.append((e["id"], download(e["video"], work / f"{e['id']}.face.mp4"), round(t, 3), round(t + d, 3)))
        wavs.append(wav)
        t += d + (gap if n < len(entries) - 1 else 0.0)
    total = t
    narration = out_dir / "narration.wav"
    pads = "".join(f"[{n}:a]apad=pad_dur={gap if n < len(wavs) - 1 else 0}[a{n}];" for n in range(len(wavs)))
    _run(*[x for p in wavs for x in ("-i", str(p))], "-filter_complex",
         pads + "".join(f"[a{n}]" for n in range(len(wavs))) + f"concat=n={len(wavs)}:v=0:a=1[a]",
         "-map", "[a]", "-c:a", "pcm_s16le", str(narration))
    graph = f"color=c={vf.get('backdrop', '0x0B1220')}:s={w}x{h}:r={fps}:d={total:.3f}[v0];"
    for k, (_, _, a, b) in enumerate(faces, 1):
        graph += (f"[{k - 1}:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},setsar=1,"
                  f"tpad=stop_mode=clone:stop_duration={b - a:.3f},trim=duration={b - a:.3f},"
                  f"setpts=PTS-STARTPTS+{a:.3f}/TB[f{k}];"
                  f"[v{k - 1}][f{k}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[v{k}];")
    dest = out_dir / "talking_head.mp4"
    _run(*[x for f in faces for x in ("-i", str(f[1]))], "-i", str(narration), "-filter_complex",
         graph + f"[v{len(faces)}]format=yuv420p[v]", "-map", "[v]", "-map", f"{len(faces)}:a",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(fps), "-c:a", "aac", "-b:a", "192k",
         "-t", f"{total:.3f}", "-movflags", "+faststart", str(dest))
    spans = [{"id": i, "start": a, "end": b} for i, _, a, b in faces]
    (out_dir / "face_spans.json").write_text(json.dumps(spans, indent=2), encoding="utf-8")
    (out_dir / "talking_head.source.txt").write_text(
        "voice-first assemble\n" + "\n".join(f"{e['id']}: {e['audio']} {e['video']}".rstrip() for e in entries)
        + f"\n{json.dumps({'duration': round(total, 3), 'width': w, 'height': h, 'faces': len(faces)})}\n",
        encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    log.info("Assembled %s: %.0f s narration, %d chunks, %d face videos", dest, total, len(entries), len(faces))
    return dest


def face_spans(out_dir: Path) -> list[tuple[float, float]] | None:
    """The face spans of a voice-first talking_head.mp4; None for any other render."""
    src, spans = out_dir / "talking_head.source.txt", out_dir / "face_spans.json"
    if not (src.exists() and spans.exists()) or not src.read_text(encoding="utf-8").startswith("voice-first"):
        return None
    return [(float(s["start"]), float(s["end"])) for s in json.loads(spans.read_text(encoding="utf-8"))]
