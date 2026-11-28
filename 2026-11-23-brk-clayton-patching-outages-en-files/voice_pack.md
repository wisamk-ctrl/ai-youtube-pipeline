# Voice-first pack · 2026-11-23-brk-clayton-patching-outages-en

1 chunks · about 0.7 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-23-brk-clayton-patching-outages-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 681 chars)

```
US Director of National Intelligence Jay Clayton says Americans should expect more tech outages. He told CNN that patching and replacing aging systems will bring glitches, gaps and interruptions in service. On ABC, he said the recent outages were not coordinated or state-sponsored. He declined to explain a suspected FBI hack and a USDA security incident. He linked an NSA outage to patching a PHP flaw. The NSA cited scheduled maintenance. Wiz says the PHP2Shell flaws affect software powering about 70% of websites, and were found with AI help. PHP issued security patches around October 21. In the Gulf, watch how operators tell patch-driven outages apart from real intrusions.
```
