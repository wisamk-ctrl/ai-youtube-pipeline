# Voice-first pack · 2026-11-22-brk-tech-outages-truth-questions-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-22-brk-tech-outages-truth-questions-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 715 chars)

```
A Gulf Today column asks if the public is being told the truth about recent tech outages. It says the US grounded all departing flights, only the second time since the September 11 attacks. Microsoft was down for nearly 24 hours, weeks after announcing 60,000 job cuts, the column says. Several American banks went down, and Apple and the National Security Agency's internal network had brief outages. One cyber insider says the number of reports hasn't changed, only the newsworthiness threshold. The columnist writes that whatever company comms teams say, things are clearly not fine. For Gulf businesses and governments running more services in the cloud, how outages get explained to the public is one to watch.
```
