# Voice-first pack · 2026-11-26-brk-google-orbital-ai-compute-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-26-brk-google-orbital-ai-compute-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 496 chars)

```
Google will test AI data center racks in orbit. It booked a Blue Origin New Glenn launch for the first quarter of 2029. Project Suncatcher uses solar-powered satellites carrying Google's Tensor Processing Units. The goal: test AI workloads at roughly single-rack scale. IDC's Dave McCarthy says no technician can swap a failed GPU at 500 kilometers. Data Center Knowledge reports heat rejection is the biggest engineering obstacle. Would Gulf data center operators ever look to space for compute?
```
