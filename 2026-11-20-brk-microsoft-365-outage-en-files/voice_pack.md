# Voice-first pack · 2026-11-20-brk-microsoft-365-outage-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-20-brk-microsoft-365-outage-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 771 chars)

```
BankInfoSecurity reports a global Microsoft 365 outage disrupted email, calendars and cloud tools across many sectors this week. InformationWeek reports it lasted over 20 hours, with more than 7 million reports on Downdetector. That makes it the largest outage reported there in the last 12 months. Microsoft says the disruption was not caused by malicious actors. But Microsoft Threat Intelligence says it saw a coordinated, high-volume phishing campaign targeting enterprises globally. Experts say U.S. hospitals largely kept patient care running, using manual workarounds. For many, services returned by early Friday. For Gulf businesses and governments relying on a single cloud provider, the question to watch is whether continuity plans can cover outages like this.
```
