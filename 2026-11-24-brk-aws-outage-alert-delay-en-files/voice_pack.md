# Voice-first pack · 2026-11-24-brk-aws-outage-alert-delay-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-24-brk-aws-outage-alert-delay-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 713 chars)

```
AWS took 93 minutes to tell customers about an outage. The outage hit its US East region early on November 15. It began at 3:05 a.m. and lasted until 6:53 a.m. THE ELEC says more than 10 major AWS services were affected. Users hit sign-up errors, authentication failures and connectivity issues. The main casualty was IAM Identity Center, an enterprise login system. AWS engineers responded within minutes, the report says. But the first status page post came only after 93 minutes. The Register reports AWS questioned Downdetector's reliability instead of explaining the failure. The outage drew little attention, coming early on a Sunday. For Gulf firms on global clouds, outage communication is worth watching.
```
