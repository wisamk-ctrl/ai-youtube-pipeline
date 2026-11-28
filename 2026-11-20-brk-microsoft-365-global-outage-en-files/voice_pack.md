# Voice-first pack · 2026-11-20-brk-microsoft-365-global-outage-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-20-brk-microsoft-365-global-outage-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 722 chars)

```
A Microsoft 365 outage took down Outlook, Teams and other services around the world. Downdetector logged more than 7.7 million reports in the 60 hours after it began, Broadband Breakfast reports. More than 90 countries and territories logged at least 1,000 reports. Japan's Digital Agency could not receive email. In the UK, almost all NHS Trusts lost email, and some operations were cancelled, Tech Policy Press reports. Microsoft's preliminary review blames a software defect, introduced in July, in its network gateway servers. At worst, more than 80% of those servers stopped responding. Microsoft found no sign of a cyberattack. For the Gulf, watch how much businesses and governments rely on a single cloud provider.
```
