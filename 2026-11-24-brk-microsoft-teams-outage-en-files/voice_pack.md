# Voice-first pack · 2026-11-24-brk-microsoft-teams-outage-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-24-brk-microsoft-teams-outage-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 475 chars)

```
Microsoft's Exchange Online and Teams went down for hours. More than 130,000 users reported problems, Computer Weekly reports. Computer Weekly calls it a major outage of Microsoft's online applications. Its data shows how deeply the UK public sector relies on these services. Computer Weekly says it is examining what went wrong. A Microsoft outage review found gaps in server testing, The Defiant reports. Could Gulf offices keep working if Teams and email failed for hours?
```
