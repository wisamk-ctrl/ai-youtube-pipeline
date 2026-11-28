# Voice-first pack · 2026-11-24-brk-amazon-buys-decart-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 1 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-24-brk-amazon-buys-decart-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 443 chars)

```
Amazon is buying key assets of AI startup Decart. The reported price is $7.5 billion. It gets Decart's tech for running AI models efficiently on different hardware. Founders and engineers join too, but not Decart's Lucy or Oasis models. Webrazzi says the goal is making Amazon's Trainium chips a rival to Nvidia. Amazon is now preparing to offer Trainium chips to customers. Would your company run its AI on Amazon's chips instead of Nvidia's?
```
