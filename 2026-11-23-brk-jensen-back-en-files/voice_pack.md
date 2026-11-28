# Voice-first pack · 2026-11-23-brk-jensen-back-en

1 chunks · about 1.1 min of speech, 0 s of face · ≈ 3 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-23-brk-jensen-back-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 940 chars)

```
NVIDIA's board has reinstated Jensen Huang as CEO, CNN reports. He had stepped down on November 12. The board says it is satisfied with his candor and his ability to lead the company. NVIDIA says senior levels of the US government assured it that his return poses no national security risk. President Trump backed the move hours before the announcement. And the market answered: NVIDIA shares rose more than 30 percent on Monday. Huang says he is honored to return. And the board's investigation is continuing. Now my view. When Jensen resigned, I said on this channel that the industry had lost its most important leader over a private matter, a loss we didn't need. Today, common sense prevailed. He built the world's largest company from scratch, and we need him leading NVIDIA through this AI era. I hope he's learned from the scandal and comes back stronger. Judging by how NVIDIA's shares jumped on the news, the markets think so too.
```
