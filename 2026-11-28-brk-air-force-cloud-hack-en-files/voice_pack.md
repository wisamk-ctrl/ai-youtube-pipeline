# Voice-first pack · 2026-11-28-brk-air-force-cloud-hack-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-28-brk-air-force-cloud-hack-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 493 chars)

```
Reuters reports hackers breached the US Air Force's cloud platform. The platform is called Cloud One. NBC News says the attack could have exposed sensitive military information. The Pentagon did not specifically deny the breach. An official said its systems are safe, secure, and managed 24-7. Federal News Network says contractors found the hack during maintenance. The CIA and FBI were also reportedly hacked in recent weeks. Would Gulf governments keep military data on cloud platforms now?
```
