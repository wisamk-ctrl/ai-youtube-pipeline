# News ranking for the episode and the Shorts (founder 2026-11-22)

Asked after PR #61 added 17 regional outlets (~80 extra AI items a week). Claude's plan was cross-checked with
ChatGPT and Gemini through the founder's Chrome (same prompt, channel described generically).

## Where all three agree
- Group articles into stories first; rank stories, never articles. Outlet count is a signal, not five votes.
- Weight "does it change a decision" highest, then the regional angle; then evidence and tension.
- "New since last episode" is a pass/fail gate, not a score (Gemini; ChatGPT: a new article is not a new development).
- Balance by slots, not pure rank: about half global shifts told through the regional lens, half regional.
- Shorts are picked on their own merits (one idea each): 1 breaking within hours + 1–2 explainers/insights; never a 3-headline summary.
- Substance = a fixed arc per deep story: the fact → what it means for the region → what to ask or watch next.
- Fewer radar one-liners (3 with a reason each, or one "number of the week").
- Don't tune weights from retention yet: too few views. First 8–10 episodes: watch hook drop-off, CTR, returning viewers.

## Where they differ
- Host approval: Gemini says before scoring (scan 20 headlines); ChatGPT says after, with a recorded reason. Plan: one approval of the scored list, host override logged with a reason.
- Deep-story count: ChatGPT says flex 2–4 by the week; Gemini fixes quotas (1 global + 2 regional deep). Plan: default 3, flex 2–4.
- ChatGPT adds: a verified/unverified flag (an unverified story never outranks a verified one) and a one-sentence weekly thesis.
- Gemini adds: a "Monday action" beat. Kept as "what to ask your vendor or team" — information, never investment advice.

## Decided plan (pending the founder's OK)
1. Cluster ~500 items → 15–20 stories.
2. Gate: new development since last episode? verified by a tier A/B source? (else out or radar)
3. Score 0–3 by the model, summed in code: decision impact ×3, regional angle ×2, evidence ×1, tension ×1.
4. Slots: 3 deep (≥1 global shift with regional impact, ≥1 regional), 3 quick, 3 radar. Flex deep 2–4.
5. Weekly thesis line; the hook teases the top three.
6. Shorts: breaking Short the day news breaks (news watch flags it); 1–2 explainer/insight Shorts from the ranked list's "one sharp idea" candidates.
7. Founder approves the ranked list in the review issue before the script is written.

## Second round (same prompt): Perplexity and DeepSeek. Kimi needs a login (not asked).
New points beyond round one:
- **"Regional consequence", not "regional angle"** (both): a token mention must not score. Test: a named regional actor, rule, customer, market or supplier, or a decision that changes. DeepSeek: prefer stories that matter in at least two of Gulf/Levant/Türkiye/Africa, or one major market with spillover.
- **A depth gate** (Perplexity): "can we say something useful in 60–180 s?" If it is only "a company announced something", it is radar.
- **A kill list** (both): vague "AI is transforming X", funding rounds with no customer or market consequence, demos without deployments, ministerial meetings with no decision, global headlines every channel has with no regional consequence.
- **Novelty is a tiebreaker** (Perplexity): an older story whose implications became clear can still lead.
- **Global/regional mix:** Perplexity 60% global-with-regional-consequence / 30% regional-first / 10% radar; DeepSeek two queues blended ~50–60% regional consequence. Consistent with slots: no global story without the regional test, no regional story without decision impact.
- **Shorts** (Perplexity): three jobs — breaking context (24–48 h), evergreen explainer, best moment from the episode; ~70% evergreen/clips, 30% timely; batch the evergreen ones. DeepSeek: one fact + one implication + one question, understandable without the episode.
- **Generic explainers leave the weekly show** and go to Shorts (Perplexity).
- **Recurring decision frames** per story (Perplexity): buy/build/partner, cost, risk, talent, regulation, data.
- **Quick stories 30–45 s**, radar 3 (Perplexity). Tune from retention only after 6–8 episodes, one variable at a time.

Changes to the decided plan: step 2 gains the depth gate and the kill list; step 3 scores "regional consequence" with the named-actor test; Shorts get the three-jobs rule and the one fact + one implication + one question shape; quick stories 30–45 s.
