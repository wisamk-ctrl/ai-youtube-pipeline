# Voice-first pack · 2026-11-23-brk-microsoft-outage-apology-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-23-brk-microsoft-outage-apology-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 654 chars)

```
Microsoft president Brad Smith has apologised again for a global outage that CBS said lasted 24 hours. Smith told CBS it was not linked to AI, and it was not a cyberattack. He blamed a perfect storm: software updated four months earlier, a new update and a shift in network traffic. Microsoft has published two reports in the last 10 days, showing minute by minute what happened. Smith says the company has taken nine steps already, with 13 more to come. He called the wider wave of outages partly AI ripple effects, as AI made flaws in code easier to find. For Gulf firms on global cloud platforms, watch how providers explain and fix outages like this.
```
