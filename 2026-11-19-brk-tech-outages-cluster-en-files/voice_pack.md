# Voice-first pack · 2026-11-19-brk-tech-outages-cluster-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 3 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-19-brk-tech-outages-cluster-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 811 chars)

```
In one week, Microsoft, Apple, JPMorgan Chase, United Airlines and the NSA all suffered major tech failures, Scientific American reports. Microsoft's cloud software was unavailable for almost 24 hours. A malfunctioning telecom network halted U.S. air traffic. Some blamed cyberattacks or AI running amok. The magazine says the evidence supports neither. Microsoft says AI agents weren't the cause. Apple's outage followed an internal update, and the NSA cites scheduled maintenance. The Uptime Institute found data center outage rates per site fell in 2026 for a fifth year running. Reliability engineer Laura Nolan says outages can cluster in a few days without a shared cause. For Gulf businesses and governments, the thing to watch is how cloud providers test and manage updates to ever more complex systems.
```
