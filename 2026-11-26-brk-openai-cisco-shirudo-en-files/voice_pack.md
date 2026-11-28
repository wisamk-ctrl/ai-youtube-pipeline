# Voice-first pack · 2026-11-26-brk-openai-cisco-shirudo-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-26-brk-openai-cisco-shirudo-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 536 chars)

```
OpenAI and Cisco just launched Shirudo for AI cyber defense. The open-source project uses AI agents and eBPF kernel-level defenses. The goal is to shield vulnerable infrastructure before permanent patches are deployed. Gulf Business reports it targets AI-driven cyberattacks and blocks Java4shell exploits. Jeetu Patel says security teams need tools matching the speed of AI threats. He calls for self-defending infrastructure that shields itself until patches roll out. Would your security team let AI agents guard your infrastructure?
```
