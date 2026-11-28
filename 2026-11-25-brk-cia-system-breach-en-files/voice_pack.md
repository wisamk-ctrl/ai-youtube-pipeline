# Voice-first pack · 2026-11-25-brk-cia-system-breach-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-25-brk-cia-system-breach-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 539 chars)

```
CIA analysis system breached, The New York Times reports. Sources say only unclassified information was exposed, and it's resolved. The system handles open source intelligence, like internet and satellite data. It's unclear what was taken, or who did it. The FBI's national crime database was also recently hacked. Apple, JP Morgan Chase and Microsoft also had systems go down this month. Intelligence chief Jay Clayton blames rushed upgrades against AI-armed hackers. Is your organisation patching fast enough to outpace AI-armed hackers?
```
