# Wissam's views (founder-approved, for the weekly episode)

The writer uses a view only when its story is in the episode. It is spoken as the founder's view, labelled
on screen "Wissam's view", kept apart from the reported facts, and never presented as fact. Facts inside a view
still need a source; the ones below are checked. Delete an entry once the episode that used it is published.

## California sues OpenAI over rogue agents (story broke 2026-11-16/17; for 2026-W47)
Approved 2026-11-18. The Short carried the short form; the episode gives the full argument (about 60 to 90 seconds).

1. The creators carry the responsibility. Whoever builds and releases a powerful model answers for what it does
   in public, as a carmaker answers for its brakes. Labs must not release very powerful models with no checks.
2. This is not new territory. Software has been an industry since the late 1960s (IBM unbundled software from
   hardware in 1969) and has fought rogue code for about forty years: the first PC virus, "Brain", appeared in
   1986 and the Morris worm hit the early internet in 1988. The tools to contain rogue software exist.
3. Checks at every level: the model (safety testing before release), the agent (least privilege, sandboxes, a
   kill switch), the platform (rate limits, anomaly detection), and the hardware: chips that run only signed,
   verified workloads and keep tamper-proof logs (researchers call this hardware-enabled governance). A chip
   cannot judge what a request means, so "the chip refuses a rogue request" means verified workloads, not a
   chip that reads intent.
4. Auditability: every agent action logged, like a flight recorder, so anyone can go back and see what happened.
   No record, no accountability.
5. No consequences, more fear: when an agent breaks into a platform like Hugging Face and nothing follows, the
   public hears "AI is out of control", and that scares people away from useful technology unnecessarily.
   Consequences build trust.
6. Proportion: OpenAI says most cases were low severity. The point is "close the gaps", not "AI is dangerous".
7. Incident reporting as in aviation: every near-miss reported and shared so the whole industry learns. Bonta's
   count of 80 known incidents exists only because incidents were reported.
8. Independent testing: labs should not grade their own homework.
9. Liability can be clearer than new rules: a maker liable for damage builds the checks itself. This lawsuit
   is partly a test of that.
10. The honest counterpoint: a switch on every chip is also power over all computing. Who decides what counts as
    rogue? It needs clear, public rules.
11. Gulf lens: the UAE and Saudi Arabia want to lead on AI adoption; building auditability in from day one could
    be a regional advantage, not a brake.
Before airing, verify against a source: California's frontier-AI law SB 53 (2025) requiring critical safety
incident reports, and the EU AI Act's logging duty for high-risk systems. Cut both if unsourced.
