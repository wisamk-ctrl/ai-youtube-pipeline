# Voice-first pack · 2026-11-19-brk-microsoft-outage-class-actions-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-19-brk-microsoft-outage-class-actions-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 715 chars)

```
Microsoft faces a pair of class actions in Canada over last week's massive outage, Courthouse News reports. One suit, filed in Quebec Superior Court, says consumers were blocked from paid Microsoft services on November 12 and 13. It claims Microsoft should have anticipated the outage, given other major outages in 2025. Microsoft blames a latent defect from July and reduced server capacity. It says it was not a cyberattack. A second suit, by Metus Lykos Debt Law, seeks to represent all Canadians, including businesses. Attorney Darryl Singer says a 24-hour email blackout means lost customers and missed deadlines. For Gulf firms that run on cloud platforms, watch how outage liability shapes service contracts.
```
