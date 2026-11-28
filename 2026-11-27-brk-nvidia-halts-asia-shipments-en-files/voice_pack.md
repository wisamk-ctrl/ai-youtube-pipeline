# Voice-first pack · 2026-11-27-brk-nvidia-halts-asia-shipments-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-27-brk-nvidia-halts-asia-shipments-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 507 chars)

```
Nvidia halts AI server shipments to four South-East Asian countries. The FT reports Dell and Supermicro told customers Nvidia won't authorise their orders. Washington is tightening export controls to stop China accessing AI computing. New US rules target Chinese firms renting Nvidia-powered cloud computing. Nvidia booked $104 billion in revenue through its Singapore subsidiary in 2025. A cloud executive told the FT it's causing sheer chaos. Would Gulf data centre builders rely on one chip supplier now?
```
