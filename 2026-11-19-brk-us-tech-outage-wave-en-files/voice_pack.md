# Voice-first pack · 2026-11-19-brk-us-tech-outage-wave-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-19-brk-us-tech-outage-wave-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 735 chars)

```
Foreign Policy reports a wave of tech outages across the U.S. government and private sector. A global Microsoft outage that began last Thursday disrupted services that businesses, schools and governments rely on. On Friday, the FAA issued a rare nationwide ground stop, causing widespread flight cancellations and delays. Chase Bank, Bank of America and Apple services also faced brief disruptions, and some internal NSA systems went down. Foreign Policy says there is currently no evidence of cyberattacks, or that the incidents were linked. Microsoft's Charles Lamanna cited a latent bug, a surge in load and reduced server capacity. For the Gulf, the question to watch is how much critical services depend on a few shared platforms.
```
