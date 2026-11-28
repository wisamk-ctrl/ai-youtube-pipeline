# Voice-first pack · 2026-11-28-exp-uae-mira-ai-agent-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-28-exp-uae-mira-ai-agent-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 498 chars)

```
Mira is the UAE's new AI agent for government services. Arabian Business reports it will handle Emirates ID, residence and work permit renewals. Khaleej Times reports the first services arrive in March 2027. Zawya reports the UAE is moving half of government services to agentic AI. An Artefact white paper asks how agencies keep control of data, models and agents. For firms that file permits, the service counter may become a conversation. Would your company trust an AI agent with visa renewals?
```
