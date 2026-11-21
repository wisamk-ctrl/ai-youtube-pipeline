# Voice-first pack · 2026-11-21-brk-nsa-network-outage-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-21-brk-nsa-network-outage-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 750 chars)

```
A computer fault has disrupted a US National Security Agency hub in Georgia, NewsCord's roundup reports. The site supports intelligence and cyber operations focused on the Middle East. The fault hit NSANet, the agency's internal network for classified information, leaving many staff unable to work normally. Officials say the most sensitive systems stayed up, with staff using backup channels. U.S. officials told CNN the outage was linked to security updates, and they ruled out a cyberattack. They tied the issues to systems using PHP, a widely used programming language. Senator Mark Warner told CNN the evidence points to legitimate efforts to secure systems. For the Gulf, watch how quickly critical networks recover when security patches fail.
```
