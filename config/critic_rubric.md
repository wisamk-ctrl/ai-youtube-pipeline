# Critic rubric — fixed anchors, defect-counted

The critic does not "feel" a score. It lists defects against the rules below, each tagged
with an axis and a severity, and the score is computed from the count:

    penalty = 2 × (major defects) + 1 × (minor defects)
    score   = 10 − 2 × penalty ÷ (number of segments), rounded, floor 1

Density, not raw count, so an eight-segment episode is not punished for being long:
a 10 has no defects on that axis; an 8 has about one minor per segment (or a major every
other segment); a 6 has about one major per segment; a 4 has two majors per segment.
The same script must produce the same defect list; if a defect is not in this rubric it is
not a defect, it is taste, and taste is not scored.

**Major** = a listener would be confused, misled, or would stop listening.
**Minor** = a listener notices a wobble but keeps following.

Quote the exact words of every defect. A defect without a quote does not count.

## hook — the first 20 seconds (before the greeting)
- MAJOR: the first spoken sentence is a greeting, a date or a channel name, not a news fact.
- MAJOR: no number, name or decision in the first two sentences.
- MINOR: the first sentence exceeds 18 spoken words.
- MINOR: the question to the audience is missing or comes after the greeting.
- Not a defect: a pause placed before a number, even mid-sentence; that is the house style (§4).

## clarity — understood on first hearing
- MAJOR: a pronoun or «ذلك/هذا» whose referent could be two different things in the previous two sentences.
- MAJOR: a comparison with no stated reference point («أسرع بثلاثين في المئة» with no "than what").
- MAJOR: a sentence carrying three or more figures (numbers, dates, percentages).
- MINOR: a sentence over 25 spoken words.
- MINOR: a technical term not in the approved list (§5) and not explained in the same sentence.

## pacing — nothing drags or rushes
- MAJOR: a segment with no [Pause] across more than 60 spoken words.
- MAJOR: two important numbers inside one breath with no pause between them.
- MINOR: [Pause 2s] used inside a segment rather than between segments.
- MINOR: three consecutive sentences under 6 words, or three over 20.
- Not a defect: a pause between a verb and its subject or object when the pause precedes a number.

## flow — signposts and transitions
- MAJOR: a segment starts with no spoken transition (§4 list or equivalent).
- MAJOR: a story appears in two segments without a cross-reference.
- MINOR: the same transition phrase used more than twice in the episode.
- MINOR: the same "why it matters" question wording used more than three times.

## arabic — broadcast MSA, style guide §1–§3, §5–§6
- MAJOR: a calque listed in §1 («يقوم بإطلاق», «على مستوى», «بشكل», «من قِبل» without need).
- MAJOR: colloquial or archaic register («إنّ ممّا لا يخفى», dialect).
- MAJOR: a term rendered two different ways in one episode (§5 one-word rule).
- MINOR: a company or person on first mention without the §3 form (Arabic name + Latin name / full name + title).
- MINOR: a large number written in digits instead of words (§2), or «مائة» for «مئة».
- MINOR: an epithet («عملاق التقنية», «الشركة الرائدة»).

## value — why it matters here (style guide §4, §7)
- MAJOR: a segment with no sentence about enterprises, governments or buyers in the Gulf or Arab world.
- MAJOR: an imperative or recommendation («عليكم», «يجب», «اشترِ») outside a quotation.
- MAJOR: a forecast stated as fact with no attribution and no conditional («سيغيّر» rather than «قد يغيّر» / «يرى محللون»).
- MINOR: the regional implication is generic and could be pasted under any story (no named sector, buyer type or regulation).
- Not a defect: an implication in the conditional («قد», «ربما») or framed as a question to watch; §7 asks for attribution of *opinions*, and a hedged implication is not an opinion.

## worst_three
After listing defects, pick the three with the largest listener cost, one rewrite each,
quoting the words to replace and giving the replacement in full. Never suggest a rewrite
that would create a defect under this rubric.
