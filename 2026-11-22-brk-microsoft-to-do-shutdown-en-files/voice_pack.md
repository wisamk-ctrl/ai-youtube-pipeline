# Voice-first pack · 2026-11-22-brk-microsoft-to-do-shutdown-en

1 chunks · about 0.8 min of speech, 0 s of face · ≈ 2 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-22-brk-microsoft-to-do-shutdown-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 716 chars)

```
Microsoft is shutting down To Do, its task-manager app, after nearly 10 years. The company says the shutdown takes place on June 30, 2027, across Windows, Mac, Android, iOS and the web. Existing tasks and lists will not migrate to Microsoft Planner, the new home for work and school tasks. Planner is not available on personal accounts, including Microsoft 365 Personal and Family subscribers. They will need another app. Microsoft says it will offer an export option, but has not yet published the details. The underlying To Do service and APIs will be retired separately, at a date not yet disclosed. For Gulf companies running on Microsoft tools, watch how smoothly teams move their task data before the deadline.
```
