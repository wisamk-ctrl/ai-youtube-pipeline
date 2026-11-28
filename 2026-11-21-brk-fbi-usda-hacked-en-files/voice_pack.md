# Voice-first pack · 2026-11-21-brk-fbi-usda-hacked-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-21-brk-fbi-usda-hacked-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 705 chars)

```
US media report that hackers have breached the US Agriculture Department and the FBI. NBC reports the USDA told staff a system for payments to farmers was targeted. Two former officials told NBC the hackers may use it as a backdoor to more sensitive material. CNN reports the FBI was hacked for the second time since September. The FBI is probing an apparent intrusion of the National Crime Information Center, used for warrant checks. It remains unclear if the breaches are linked, or who is behind them. They follow weeks of major US outages that officials say were not criminal. Gulf governments and businesses will be watching how attacks on payment and records systems shape their own cyber defences.
```
