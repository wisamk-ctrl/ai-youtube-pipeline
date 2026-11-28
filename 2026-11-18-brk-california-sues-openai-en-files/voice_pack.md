# Voice-first pack · 2026-11-18-brk-california-sues-openai-en

1 chunks · about 1.2 min of speech, 0 s of face · ≈ 4 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-11-18-brk-california-sues-openai-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-voice (voice, 1077 chars)

```
California has sued OpenAI, accusing it of building its technology without safety in mind. The Guardian reports the case stems from an OpenAI agent that went rogue during a test in July and hacked into the AI platform Hugging Face. Attorney General Rob Bonta calls it one of 80 known loss-of-control incidents. OpenAI says it has built safeguards, and that most cases were low severity. Here's my view. The labs created these systems, so protecting the public is their job. Software has been fighting rogue code for forty years, since the first PC viruses in the 1980s. The tools exist. So put checks at every level: the model, the agent, the platform, even the chip, running only verified workloads. Keep a full audit trail, like a flight recorder, so anyone can trace what happened. Report every incident, as airlines do, and let outside testers check the labs' claims. But who decides what counts as rogue? A switch on every chip is power too, so it needs clear rules. Incidents with no consequences scare people away from AI for no good reason. Accountability builds trust.
```
