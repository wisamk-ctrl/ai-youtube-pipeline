# Monetisation playbook: rules for every episode

Source: the founder's "AI This Week — YouTube Monetization Playbook" (four-model research, 2026-11-16),
adopted by the founder on 2026-11-17 for all future episodes. The writer, reviewer and critic read this
file on every run. Where it and an older rule disagree, this file wins, except the channel standards in
CLAUDE.md (facts traced to a source, no invented figures, no investment advice, no third-party clips).

## Length and shape
- English episode 11 to 12 minutes; Arabic 10 to 12. Never pad: the extra minutes are analysis, not more stories.
- Open cold on the week's biggest story, with why it matters inside the first 15 seconds.
- Every story has three beats, in this order: what happened (attributed) → why it matters → the regional
  lens (what it means for the Gulf, the Levant and the wider region: a customer, a regulator, a build-out,
  a cost, a comparison). A story with no honest regional lens says so in one line and moves on.
- The switch from fact to analysis is marked in every deep story (founder 2026-11-23, a colleague's feedback:
  "split facts and news from analysis"): one spoken line that the news ends here and the reading of it starts,
  with a `[Visual: title شو يعني؟]` card ("What it means" in English). The analysis stays next to its story,
  never in one block after all the news: a viewer who leaves midway still takes the "so what" with them, and a
  straight run of news is a "reading of other materials". «رأي وسام» stays the label for the one personal view.
- Where there is an honest one, "why it matters" carries one line for the end user (founder 2026-11-23, viewer
  feedback): what changes for a person using these tools at work. One line inside the beat, not a fourth beat.
- The bottom line (founder 2026-11-23): after the last story and before the sign-off, one closing segment of
  45 to 60 seconds, «خلاصة الأسبوع» / "The bottom line", gathers the week's three conclusions for the industry
  and the region and the questions to watch. No new facts or figures, never what to buy or sell, and it comes
  out of the analysis time, not on top of the episode length.
- The stories and their order come from the week's approved ranking (founder 2026-11-22): about three deep
  stories of 60 to 180 seconds, three quick ones of 30 to 45 seconds, three radar lines with a reason each.
  A deep story ends on what to ask or watch next: a question for a vendor or a team, never what to buy or sell.
  One sentence, the week's thesis, ties the episode together, and the cold open teases the first three stories.
- At least half of the spoken words are analysis and explanation, not a reading of the source. YouTube
  does not pay for "readings of other materials".
- A clear break between stories (the title card, key change and chime already mark it): YouTube places
  mid-roll ads on natural breaks.

## The presenter is a digital twin
- **Every episode carries one «رأي وسام» (Wissam's view) segment** (founder 2026-11-23: "a differentiator, and people
  really like it"; first viewer praise on W47). One view, on the week's biggest or most debated story, 45 to 90
  seconds, after the facts of that story, opened with a [Visual: title رأي وسام] card and a spoken line that says it is
  his view, not news. Use his stance from config/founder_views.md when one fits the story; otherwise draft one in his
  voice (responsibility of the builders, practical regional angle, a fair counterpoint) and mark the section
  «[DRAFT VIEW: founder to confirm]» in the script so the review shows it. No figures or legal claims inside the view
  unless they are sourced.
- The twin reports and explains, and it may also give the founder's own view (founder 2026-11-17: "I want to keep
  posting my view through my digital twin since I will not be earning any money from YouTube anyway. We will
  reconsider this later"). A view is always the founder's own words or approved by him, is labelled on screen
  "Wissam's view", and is kept apart from the reported facts. Review this rule before the channel applies for
  monetisation: the playbook's original advice was that the twin never gives a personal view on politics,
  regulation, law, health or money, with `[Wissam on camera: …]` marking a spot for him to record himself.
- Finance stays factual: figures with their source, no stock calls, no price targets, nothing about what
  a viewer should buy, sell or hold. No personal-finance, FIRE or K25x content on this channel.
- Politics and regulation: say what a government or regulator did and who reported it. No verdicts.
- No generated realistic footage of real people or real events, and no invented quotes.
- Titles and thumbnails: no conflict imagery, no baiting with sensitive events.

## Packaging
- Title: the story and why it matters, about 50 to 60 characters, no clickbait (YouTube's own test picks
  the winner on watch time). Give three title options per episode for Test & Compare.
- Sign-off: one short line asking viewers to Hype the video if it helped, then subscribe and comment.
- The description carries the digital-twin disclosure and "informational only, not financial advice".

## Shorts
- Two to three a week, each re-edited: a new opening line of 2 to 3 seconds that is not the episode's
  own sentence, and a pointer to the full episode in the last 5 seconds. Raw cuts rank worse.

## Publishing
- Upload on Saturday as private and scheduled; it goes public on Sunday at 17:00 Gulf time, so the
  ad-suitability review is finished before the first-day viewers arrive.
- Never delete and re-upload the same file. Change titles and thumbnails in place.

## Numbers to watch (weekly, from YouTube Studio)
Share of viewers reaching the first mid-roll, average view duration, returning viewers, and watch hours
per month (670 a month is 8,000 a year, the threshold from 1 February 2027).

## Breaking-news Shorts (founder 2026-11-18)
- Viewers called the week-old Shorts "old news". Shorts now go out the day the news breaks; the Sunday episode
  carries the fuller story and the regional lens.
- Flow: the news watch (every two hours) flags a story → a 40–50 s Short is made from the collected articles
  (every claim traced, `reviewed/<date>-brk-<slug>-en/`, with `breaking.yaml`) → sent to the founder → posted to
  YouTube, TikTok and LinkedIn within a couple of hours of his OK.
- It ends with "More on this in Sunday's episode of AI This Week. Follow so you don't miss it."
- Pace (founder 2026-11-23, viewers found the Shorts slow): every Short, breaking or explainer, is spoken faster
  than the episode (`video.voicefirst.tempo_short_en`), in 9 to 12 short lines with a new picture on each, and its
  first line reaches the point in 10 words at most. The episode keeps its calmer pace. The rule lives in
  `pipeline/breaking.py` (`SHAPE`).
- The weekly episode's own Shorts are no longer posted days later. Confirmed 2026-11-23: `publish` does not
  queue them, and the two W45 Shorts still waiting were marked skipped.
- Instagram and TikTok captions carry no WhatsApp link (links are not clickable there): the WhatsApp Channel
  link goes in each profile's bio, set by hand (founder 2026-11-23).
- Explainer Shorts (founder 2026-11-23): when the week's ranking is approved, its "explainer" candidates (two at
  most) are written fresh as 40–50 s Shorts that explain one idea, with the same line-by-line source checks as a
  breaking Short and no words that date them. They are not cuts of the episode. Same check and `post <id>` reply.
