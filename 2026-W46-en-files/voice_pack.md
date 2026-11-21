# Voice-first pack · 2026-W46-en

17 chunks · about 12.0 min of speech, 70 s of face · ≈ 67 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-W46-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-face (face, 111 chars)

```
In the latest US elections, local communities voted against proposals tied to data centers <break time="0.8s"/>
```

## 02-voice (voice, 167 chars)

```
in 40 cases <break time="0.8s"/> out of 41. So if people there don't want data centers next to their homes, who's going to host them? And who's going to pay the price?
```

## 03-face (face, 135 chars)

```
Hi everyone, welcome to AI This Week. I'm Wissam. I've spent 25 years in enterprise software across the Middle East, Turkey and Africa.
```

## 04-voice (voice, 218 chars)

```
Today: Jensen Huang leaves NVIDIA. Plus Anthropic's IPO under pressure, a Saudi platform that keeps data inside the Kingdom, and a wallet that lets an AI agent shop for you. We start with the biggest story of the week.
```

## 05-face (face, 122 chars)

```
On November 12, NVIDIA announced that Jensen Huang has resigned as president, CEO and board member, effective immediately.
```

## 06-voice (voice, 1073 chars)

```
The company's finance chief, Colette Kress, is now interim CEO. And the board says it will consider candidates from inside and outside the company. NVIDIA gave no reason. Press reports, including Al Jazeera and TechCrunch, tie his exit to his private life. Al Jazeera reports that he admitted being unfaithful to his wife. One of the reported relationships was with a woman alleged to have worked for Chinese intelligence. That part is an allegation: Al Jazeera notes there is no established evidence that company secrets were compromised. Why does this matter here in the region? Many AI programs in our region are built on NVIDIA's chips. And that roadmap now depends on a company without its founder. My view: the AI industry just lost its most important leader over matters that began in his private life. If the security allegations are proven, that's a different conversation. But until then, I think this is a loss the industry didn't need. And there's a lesson for us in the Gulf: don't build a national AI strategy around one man, or one vendor. Now to the models.
```

## 07-face (face, 160 chars)

```
Anthropic is the company behind the Claude family of models. And it's now getting ready to go public, most likely in mid-November, on the Nasdaq stock exchange.
```

## 08-voice (voice, 1724 chars)

```
According to CNBC, investors in the company are seeing a valuation that starts <break time="0.8s"/> at $1 trillion <break time="0.8s"/> and goes up to $1.5 trillion. A few months ago, the number people were talking about was <break time="0.8s"/> $2 trillion. So expectations have come down. Why? <break time="0.8s"/> Because the mood has gotten tougher, from the stock market to the street. The Nasdaq posted its sharpest drop <break time="0.8s"/> in 19 months. And the hardest hit were chip companies, and the newer companies that rent out computing power for AI. In the US midterms, voters sent a clear message. Candidates who called for tighter AI regulation won in states like Michigan and Texas. And according to an NBC News exit poll, a survey of people as they leave the voting booth, more than half of voters said data centers were a deciding or major factor in how they chose their congressional candidates. Maura Austin, a behavioral science researcher at the University of Virginia, told CNBC that people don't want a data center next to them if all it does is make a big tech company richer. She added that an Anthropic listing at such a high valuation brings it closer to the image of big tech and billionaires, and she doesn't expect people to like that. Anthropic could be the first company that does nothing but AI to go public, and in exactly this climate. So what does this mean for us? Anthropic sells most of its products to businesses, not individuals. So for a company here in the region that runs on Claude, its provider could soon be a listed company, under the market's eye. And when US politics gets tough on data centers, a question comes up: where will the next wave of computing power get built?
```

## 09-face (face, 71 chars)

```
From the US to Saudi Arabia, and this is our top story from the region.
```

## 10-voice (voice, 1676 chars)

```
Riyadh-based OmniOps has launched the Bunyan Inference Hub, according to a statement published by Wamda and Zawya. Inference just means running a trained model to get answers from it. The platform is for governments, companies, startups and developers. It has a library of open models, the kind anyone can download and run, or you can bring your own model. And the data and the running of the model all stay inside Saudi Arabia. Access to the models comes in ready-made token packages. A token is the unit of text a model reads and writes. And if you need more capacity or full isolation, there are dedicated GPUs, the chips that run AI models, just for you. According to the company, it has its own engine that adjusts how models run on existing hardware. The goal, in their words, is to raise GPU utilization and cut the cost per token. And the platform runs on different types of chips, so it isn't tied to a single vendor. You can also set usage limits and track how much each team is consuming. Mohammed Altassan, founder and CEO of OmniOps, said that managing model consumption securely and with cost controls has never mattered this much. And notice the irony: in the US, people are rejecting data centers near them, while here, local hosting is the selling point. Why does this matter here in the region? For organizations required to keep their data inside the country, the only option was sometimes to build their own infrastructure. Now, according to the company, they have another path. And the packages and per-team limits give the finance department control over costs. What should we watch? Who the first customers will be, and which models land in the library.
```

## 11-face (face, 72 chars)

```
Now let's move on to agents. On Friday, OpenAI announced ChatGPT Wallet.
```

## 12-voice (voice, 1530 chars)

```
It's a payment wallet that lets its AI agents, called "dots," make purchases for you. The company built it in partnership with American Express and Mastercard. Visa is a partner too. And users keep their card points and protections. So how does it work? You enter your card details once, and you ask the agent to find the item for you. And you approve every purchase yourself, with a security verification step. And most importantly, according to OpenAI, the agent never sees your card details. The payment network gives it a payment token just for that transaction. The token has a card number, a security code and an expiry date, all limited to that one purchase. And the company says it isn't taking a commission on purchases, at least at the start. Chaya Nayak, who leads payments and revenue products at OpenAI, told CNBC their goal is to build a safe, easy foundation with merchants and payment networks. The rollout is limited: only Pro subscribers in the US who are over <break time="0.8s"/> 18. And this isn't their first attempt at commerce. Last fall they launched a feature called Instant Checkout, and quickly dropped it. So the agent has gone from talking to paying. So where do our banks and retailers stand in all this? The service is still US-only. But the approach itself, partnering with card networks and using a payment token for each transaction, could be a model banks here look at. So the question for banks and retailers in the region is: how will they handle a purchase started by an agent, not a person?
```

## 13-face (face, 96 chars)

```
Before we go on, a story that hit offices across our region last week: the Microsoft 365 outage.
```

## 14-voice (voice, 1213 chars)

```
On November 12, Outlook email, calendars and Teams meetings stopped working for businesses around the world. Microsoft's preliminary incident report puts the outage at just under 24 hours, according to Ars Technica. In the UAE, Khaleej Times reported disruption for businesses and residents. So what went wrong? Microsoft says three things came together. A software defect that had been sitting in its network gateway since July. A shift that put Teams traffic onto the same system that carries email. And part of that system's server capacity already offline for a separate reason. Recovery was slow because servers coming back online were immediately overwhelmed again, a Microsoft executive, Charles Lamanna, told customers, as reported by ABC News. Microsoft says it was not a cyberattack and had nothing to do with AI agents. And it apologized. My view: this is not acceptable from a company of Microsoft's size. A defect that sat unnoticed for months should not be able to take email and meetings down across the world for a day. For large organizations in our region, the lesson is redundancy: more than one cloud, and a mix of international and local providers, so that one company's bad day is not yours.
```

## 15-face (face, 132 chars)

```
Staying with NVIDIA, and this time in Korea. This whole story comes from NVIDIA's own announcements, so let's hear it in that light.
```

## 16-voice (voice, 2039 chars)

```
NVIDIA and Korea's Ministry of Science and ICT have expanded their sovereign AI collaboration. According to NVIDIA, the collaboration opens the door for Korean chip companies to try joining NVLink Fusion, NVIDIA's technology for linking other companies' chips with its own. NVIDIA also announced work with SK Telecom, Korea's largest mobile operator, and with Rebellions, a Korean AI chip startup, on sovereign infrastructure for Korean models. And by their own numbers, they'll be working <break time="0.8s"/> with 3 consortiums <break time="0.8s"/> and with 4 Korean companies building foundation models, the large general models that other products are built on. That's using Dynamo, NVIDIA's software for serving models at scale. On the investment side, NVIDIA announced it has invested in a Korean startup called Point2. That company moves data between chips and racks using radio waves, instead of copper and optical fiber. And NVIDIA plans to invest in 3 more startups: a model lab in Seoul, a robotics company, and a company that makes language models and document tools. So what's the takeaway for the Gulf states? Korea shows us what a sovereign package between a government and a vendor looks like: local chips, local models, training, and startup funding. Sovereign programs in the Gulf can compare their own deals against it, keeping in mind this is NVIDIA's version of events. Before we wrap up, a quick roundup of developer tools. Claude Code, Anthropic's coding agent, shipped its latest release, and the first item in it is a fix for a security issue in how it unpacks compressed data. Codex, OpenAI's coding agent: the latest release lets you add a custom model provider from the command line. And it still blocks project settings in untrusted folders, a security point that matters to engineers. And CrewAI, a framework for building agents, has made gpt-6-luna the default model everywhere. The bottom line: in the US, the question is now who's willing to host AI, while in the Gulf, hosting has become the offer itself.
```

## 17-face (face, 153 chars)

```
Subscribe to the channel and tell us what you think: who do you think will host the next wave of AI? <break time="0.8s"/> Thanks for watching, take care.
```
