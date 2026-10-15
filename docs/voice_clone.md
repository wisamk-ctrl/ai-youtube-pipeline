# Professional voice clone (ElevenLabs) — checklist

A stock voice is the first thing a Gulf executive notices. A professional clone of the
presenter's own voice is the biggest single lift in perceived quality. Steps:

1. **Record 30–60 minutes** of the presenter reading Arabic news copy (not the sample script —
   varied copy). Quiet room, one condenser or a good USB mic, 44.1 kHz / 24-bit, no music, no
   processing. Read at broadcast pace with the pauses the style guide asks for. Include numbers,
   names and passive verbs: the clone learns prosody from what it hears.
2. ElevenLabs → Voices → **Professional Voice Clone** (requires the Creator plan or above and an
   identity verification step). Upload the recordings; label the language Arabic.
3. Once trained, note the **voice id** and set `ELEVENLABS_VOICE_ID` (repo secret and `.env`).
   `video.elevenlabs.model_id` stays `eleven_multilingual_v2`; tune `stability` (0.45–0.6 for
   news) and `similarity_boost` (0.8–0.9) by ear on one segment before a full render.
4. Provider choice: `video.provider: elevenlabs_did` uses the clone for speech and D-ID for the
   face. With HeyGen, upload the same recordings as a HeyGen voice clone and set `HEYGEN_VOICE_ID`.
5. **Test the tashkeel pass** on one segment with and without `video.tashkeel: true`. Keep it on
   only if the clone reads the marked words more accurately; some engines ignore the marks.

Consent: the clone is the presenter's own voice; keep the signed consent with the recordings.
