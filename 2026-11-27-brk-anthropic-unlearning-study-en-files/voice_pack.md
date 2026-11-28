# Voice-first pack · 2026-11-27-brk-anthropic-unlearning-study-en

1 chunks · about 0.5 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-27-brk-anthropic-unlearning-study-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 505 chars)

```
Anthropic research says AI models keep cyberattack knowledge after unlearning. Researchers tested 23 model checkpoints that had been through unlearning. On standard tests, accuracy on cyber questions fell to near chance. But in 14 of 23 cases, models still ranked the correct answers highest. The researchers say unlearning created backdoor-like mechanisms inside the models. Activation on affected neurons rose by 22-100x on cyber text. Would your company trust an AI model that claims to have forgotten?
```
