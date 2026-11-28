# Voice-first pack · 2026-11-28-brk-air-force-cloud-breach-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-28-brk-air-force-cloud-breach-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 499 chars)

```
Reuters: hackers breached the US Air Force's Cloud One platform. It pools cloud from Microsoft, Amazon, Oracle and Alphabet. It holds personnel records, payroll, logistics and air defence radar data. It tracks munitions at more than 200 Air Force locations. Who did it, and whether data was stolen, is unclear. One source says hackers exploited a software vulnerability. Cyber Command was reportedly called in, and migrations are suspended. Would your government trust one shared cloud platform now?
```
