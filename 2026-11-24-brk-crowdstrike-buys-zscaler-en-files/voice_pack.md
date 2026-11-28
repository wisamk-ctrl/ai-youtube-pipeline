# Voice-first pack · 2026-11-24-brk-crowdstrike-buys-zscaler-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-24-brk-crowdstrike-buys-zscaler-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 497 chars)

```
CrowdStrike is buying Zscaler for $43.9 billion, all in stock. The Register calls it the biggest cybersecurity acquisition on record. CrowdStrike protects devices. Zscaler secures the network with zero-trust technology. CrowdStrike says together they can watch what AI agents do and access. My view: as AI agents browse the internet, this is a seismic move for security. Watch the regulators, renewal prices, and whether outages get rarer. Would your company trust one vendor for all its security?
```
