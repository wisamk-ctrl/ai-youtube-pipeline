# This Week in AI · W46 · English script for review

~1,420 words, about 9 minutes at the slower pace.

## Opening

In the latest US elections, local communities voted against proposals tied to data centers

in 40 cases

out of 41.

> on screen: 40 / 41

So if people there don't want data centers next to their homes, who's going to host them? And who's going to pay the price?

## Welcome

Hi everyone, welcome to This Week in AI. I'm Wissam.

Today we've got Anthropic's IPO under pressure, a Saudi platform that keeps data inside the Kingdom, and a wallet that lets an AI agent shop for you.

## Anthropic's IPO Under Pressure

Let's start with the models.

Anthropic is the company behind the Claude family of models.

And it's now getting ready to go public, most likely in mid-November, on the Nasdaq.

According to CNBC, investors in the company are seeing a valuation that starts

at $1 trillion

and goes up to $1.5 trillion.

A few months ago, the number people were talking about was

$2 trillion.

> on screen: Valuation: $2T → $1T–1.5T

So expectations have come down. Why?

Because the mood has gotten tougher, from the stock market to the street.

The Nasdaq posted its sharpest drop

in 19 months.

And the hardest hit were chip companies, and the newer companies that rent out computing power for AI.

In the US midterms, voters sent a clear message.

Candidates who called for tighter AI regulation won in states like Michigan and Texas.

And according to an NBC News exit poll, more than half of voters said data centers were a deciding or major factor in how they chose their congressional candidates.

Maura Austin, a behavioral science researcher at the University of Virginia, told CNBC that people don't want a data center next to them if all it does is make a big tech company richer.

She added that an Anthropic listing at such a high valuation brings it closer to the image of big tech and billionaires, and she doesn't expect people to like that.

Anthropic could be the first pure-play AI company to go public, and in exactly this climate.

So what does this mean for us?

Anthropic sells most of its products to businesses, not individuals.

So for a company here in the region that runs on Claude, its provider could soon be a listed company, under the market's eye.

And when US politics gets tough on data centers, a question comes up: where will the next wave of computing power get built?

## Saudi Arabia's Bunyan Platform

From the US to Saudi Arabia, and this is our top story from the region.

Riyadh-based OmniOps has launched the Bunyan Inference Hub, according to a statement published by Wamda and Zawya.

The platform is for governments, companies, startups and developers.

It has a library of open models, or you can bring your own model.

And the data and the running of the model all stay inside Saudi Arabia.

Access to the models comes in ready-made token packages. A token is the unit of text a model reads and writes.

And if you need more capacity or full isolation, there are dedicated GPUs just for you.

According to the company, it has its own engine that adjusts how models run on existing hardware.

The goal, in their words, is to raise GPU utilization and cut the cost per token.

And the platform runs on different types of chips, so it isn't tied to a single vendor.

You can also set usage limits and track how much each team is consuming.

Mohammed Altassan, founder and CEO of OmniOps, said that managing model consumption securely and with cost controls has never mattered this much.

And notice the irony: in the US, people are rejecting data centers near them, while here, local hosting is the selling point.

Why does this matter here in the region?

For organizations required to keep their data inside the country, the only option was sometimes to build their own infrastructure.

Now, according to the company, they have another path.

And the packages and per-team limits give the finance department control over costs.

What should we watch? Who the first customers will be, and which models land in the library.

## ADNOC and Industrial Sovereignty

We're staying in the Gulf, but this time in the UAE.

An analysis piece on the site debuglies talks about a partnership that brings together ADNOC, the Abu Dhabi National Oil Company, with OpenAI.

And the third party in the partnership is G42.

The article reads this partnership through the lens of AI agents and national security.

> on screen: The New Architecture of Industrial Sovereignty

And its headline calls it "The New Architecture of Industrial Sovereignty."

Who here is going to feel this difference?

The first to feel it could be energy and industrial companies in the Gulf.

Because the article frames the AI agent as a matter of sovereignty and national security, not just a purchase for the IT department.

And if that reading takes hold, it could affect who you pick as a partner, and where your data stays.

## The AI Agent Wallet

Now let's move on to agents.

On Friday, OpenAI announced ChatGPT Wallet.

It's a payment wallet that lets its AI agents, called "dots," make purchases for you.

The company built it in partnership with American Express and Mastercard.

Visa is a partner too. And users keep their card points and protections.

So how does it work?

You enter your card details once, and you ask the agent to find the item for you.

And you approve every purchase yourself, with a security verification step.

And most importantly, according to OpenAI, the agent never sees your card details.

The payment network gives it a payment token just for that transaction.

The token has a card number, a security code and an expiry date, all limited to that one purchase.

> on screen: No cut of transactions — for now

And the company says it isn't taking a commission on purchases, at least at the start.

Chaya Nayak, who leads payments and revenue products at OpenAI, told CNBC their goal is to build a safe, easy foundation with merchants and payment networks.

The rollout is limited: only Pro subscribers in the US who are over

18.

And this isn't their first attempt at commerce.

Last fall they launched a feature called Instant Checkout, and quickly dropped it.

So the agent has gone from talking to paying.

So where do our banks and retailers stand in all this?

The service is still US-only.

But the approach itself, partnering with card networks and using a payment token for each transaction, could be a model banks here look at.

So the question for banks and retailers in the region is: how will they handle a purchase started by an agent, not a person?

## NVIDIA and Korea

Now to chips, and this time to Korea.

> on screen: Source: NVIDIA announcement

This whole story comes from NVIDIA's own announcements, so let's hear it in that light.

NVIDIA and Korea's Ministry of Science and ICT have expanded their sovereign AI collaboration.

According to NVIDIA, the collaboration opens the door for Korean chip companies to try joining the NVLink Fusion ecosystem.

NVIDIA also announced work with SK Telecom and with Rebellions on sovereign infrastructure for Korean models.

And by their own numbers, they'll be working

with 3 consortiums

and with 4 Korean companies building foundation models.

That's using the Dynamo software for running models.

On the investment side, NVIDIA announced it has invested in a Korean startup called Point2.

That company moves data between chips and racks using radio waves, instead of copper and optical fiber.

And NVIDIA plans to invest in 3 more startups: a model lab in Seoul, a robotics company, and a company that makes language models and document tools.

> on screen: Motif Technologies · RLWRLD · Upstage

So what's the takeaway for the Gulf states?

Korea shows us what a sovereign package between a government and a vendor looks like: local chips, local models, training, and startup funding.

Sovereign programs in the Gulf can compare their own deals against it, keeping in mind this is NVIDIA's version of events.

## Quick Roundup

Before we wrap up, a quick roundup of developer tools.

Anthropic's Claude Code shipped its latest release, and the first item in it is a fix for a security issue in decompressing compressed responses.

> on screen: Claude Code v2.1.325

OpenAI's Codex: the latest release lets you add a custom model provider from the command line.

And it still blocks project settings in untrusted folders, a security point that matters to engineers.

> on screen: OpenAI Codex 0.169.0

And CrewAI, a framework for building agents, has made gpt-6-luna the default model everywhere.

> on screen: CrewAI 1.15.38

## Closing

The bottom line: in the US, the question is now who's willing to host AI, while in the Gulf, hosting has become the offer itself.

Subscribe to the channel and tell us what you think: who do you think will host the next wave of AI?

Thanks for watching, take care.
