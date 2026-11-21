# Voice-first pack · 2026-11-18-brk-us-tech-outages-wave-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-18-brk-us-tech-outages-wave-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 765 chars)

```
Vice President JD Vance canceled a summit appearance on Wednesday to attend meetings on a wave of tech outages, CNBC reports. Incidents include a nationwide ground stop, a Microsoft Outlook outage and a reported blackout of an NSA classified network. CNBC also lists issues at JPMorgan Chase, United Airlines and Apple. A senior administration official says they are not a cyberattack, but upgrades, patches and other disparate events. Intelligence director Jay Clayton says there is no sign they are coordinated. Asked about AI's role, the official called it challenging to answer. Senator Mark Warner told CNBC he wants better coordination on AI safety. For Gulf businesses and governments, watch whether this brings new scrutiny of system upgrades and AI safety.
```
