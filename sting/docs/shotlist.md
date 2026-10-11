# أسبوع الذكاء الاصطناعي — intro sting: shot list
5 s · 128 bpm · 10.7 beats (period 0.469 s) · formats: 16x9 (primary)
Music: synth house, D minor, 128 bpm (`audio/music.wav`) · VO: none
Palette: navy #0B1220 (same as the HeyGen avatar background, so the cut into the presenter is seamless),
paper #F4F1EA, one accent gold #E9B44C, muted #5C6B86. Display: Noto Kufi Arabic · UI: Noto Naskh Arabic.
Arabic is drawn word-by-word (never per glyph: canvas shapes a whole word, per-glyph drawing would break
the letter joins), laid out right-to-left from the right edge of the safe area.

| # | beats | time | shot | on screen (asset) | motion | out (transition) | sound (hits) |
|---|-------|------|------|-------------------|--------|------------------|--------------|
| 1 | 0-1 | 0.00-0.47 | Hook: signal line | a 3 px gold line with a bright head races right→left across the frame at mid-height, already moving on frame 0; it leaves the title's underline behind it | linear sweep (mechanical, on purpose), head trails a short motion-blurred tail | the line stays as the underline the words land on | whoosh peaking @1 |
| 2 | 1-4 | 0.47-1.88 | Title lands, word by word | «أسبوع» drops from above onto the line @1 (squash on landing); «الذكاء» slides in from the right @1.75; «الاصطناعي» slides in from the right in gold @2.5 | bouncy springs, 4% squash-and-settle on word 1, overshoot on the slides | title lifts (see 3) | thud @1, pop A4 @1.75, pop D5 @2.5 |
| 3 | 4-6 | 1.88-2.82 | The week | on the downbeat the lockup lifts to the upper third and scales to 72%; seven vertical bars (the days) rise from the bottom one per quarter-beat, the seventh (today) taller and gold | gentle spring on the lift; each bar springs up with overlap | bars collapse (see 5) | impact @4, ticks @4.5…5.75, bell D6 @6 |
| 4 | 6.25-7.5 | 2.93-3.52 | Tagline | «نشرة أسبوعية لقادة الأعمال والتقنية» types on right-to-left under the bars in the UI face | typed on, 18 characters over 0.9 s | holds under the lockup | type @6.25 |
| 5 | 7.5-10.7 | 3.52-5.00 | End lockup | bars fold down into one gold underline; title returns to centre at 85%; «مع وسام» in muted under the line | spring collapse, title eases down; still from 8.5 to the end (1.0 s) + the 0.5 s settle ≈ 1.5 s readable hold | hard cut to the presenter (same navy) | sub @7.5, bell A5 @8 |

Deviation to defend: the end lockup lands a half-beat before the final downbeat (7.5) so the still hold reaches
~1.5 s inside a 5 s sting; the sub sits on 7.5 and the bell on the downbeat 8.

Longest gap without a new event: beats 8-10.7 (1.25 s) — the intentional end hold.
