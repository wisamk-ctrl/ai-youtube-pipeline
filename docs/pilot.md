# Five-episode pilot

The rubric, the sources and the voice prove themselves on live news, not on the fixture.
Run five consecutive Saturdays **unlisted** before making the channel public.

- `publish.privacy` is `unlisted` (settings.yaml). Each episode uploads unlisted; share the link
  with a handful of target viewers (CTOs, founders) and ask one question: "what would make you
  watch next week?"
- Track per episode, in `docs/pilot_log.md`: critic consensus scores, unsourced claims, the
  editor's note count, render cost (usage.json), watch-time from YouTube Studio.
- Pass criteria to go public: three consecutive episodes with every critic axis ≥ 8 on first
  score, zero unsourced claims, under five editor notes, and average view duration above 50%.
- Then set `publish.privacy: private` with the schedule (Saturday 06:00 UTC) or `public`.
