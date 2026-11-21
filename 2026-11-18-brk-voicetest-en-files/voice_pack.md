# Voice-first pack · 2026-11-18-brk-voicetest-en

1 chunks · about 0.7 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-18-brk-voicetest-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 668 chars)

```
Politico counts six major outages in six days across the United States. Microsoft 365 went down on November 12. The next day, the FAA halted flight departures nationwide for about four hours. Then JPMorgan Chase payments were delayed, United Airlines had a systemwide outage, and CNN reported that the NSA's classified network went down. So was it an attack? Secretary of State Marco Rubio says there is zero evidence of a malign actor. The Director of National Intelligence says security upgrades are taking longer than planned and hitting unexpected problems. For businesses in our region, last week's lesson holds: plan for the day a system you depend on goes down.
```
