# Voice-first pack · 2026-11-18-brk-week-of-outages-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-18-brk-week-of-outages-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 728 chars)

```
The BBC reports an unusual run of major outages in the past week. A massive Microsoft outage, all US flights grounded for hours, and NSA problems. No evidence links them, the BBC says. Many followed updates gone wrong. JP Morgan Chase blamed a software bug for US bank payment problems, saying it was not a cyber-security incident. AI also helped uncover flaws in Java, the third-most popular programming language. Hackers using malicious code in Optimizely stole about $7,000 in cryptocurrency before being kicked out. Anthropic and OpenAI now give select companies early access to top models, so defenders find flaws first. In the Gulf, watch how critical systems test their updates, and who gets early access to defensive AI.
```
