# Native editor sign-off — how reviewer notes become rubric rules

Before the channel goes public, one Arabic broadcast editor reads two full episodes against
`config/style_guide.md` and marks every line that sounds translated, stiff or wrong for a Gulf
business audience. Their notes are the one input no model tuning replaces.

## What to give the editor
- `reviewed/<week>/script.md` for two weeks, printed or as a doc.
- The style guide, and the critic's defect list for each (the review issue has it).
- Ask for three columns per note: the quoted words, what a listener hears, the fix.

## What to do with the notes
1. Put the notes in `reviewed/<week>/notes.md` (same three columns).
2. For each note that is a **pattern** (would recur in other episodes), add one line to
   `config/critic_rubric.md` under the right axis, as MAJOR or MINOR, in the rubric's own
   wording: "- MINOR: <the pattern>, e.g. «<the editor's quote>»". The critic then catches it
   every week, and the score is explained by that line.
3. For a note that is a **term**, add the row to the style guide's §5 table; the writer, reviewer
   and critic all read it.
4. For a one-off, fix the script and move on.
5. Re-score the two episodes (`phase=score`). The editor's notes should now appear as defects.
   If they do not, the rubric line is too vague; rewrite it with the quote.

Two rounds of this (notes → rubric → re-score) is the sign-off. After that, the editor reviews
one episode a month, not every week.
