# Voice-first pack · 2026-W47-en

23 chunks · about 16.5 min of speech, 69 s of face · ≈ 81 credits (speech ≈ 3/min, 1 minimum per call; Avatar IV ≈ 21/min).

1. Every chunk: `create_speech` with voice `e1412c8894c9462eb3aa8bc8ad1f6e26`, the text exactly as below (keep the break tags).
2. Face chunks also: `create_video_from_avatar` with look `1df5311275d0482cbe916ab841005526` (Professional in blue shirt), `audioUrl` = that chunk's speech URL, Avatar IV, 1080p, landscape.
3. Commit `reviewed/2026-W47-en/voice.yaml` (format: `pipeline/video/voicefirst.py`) with every chunk's
   `audio` (and `video` for face chunks), then run weekly-roundup with phase `assemble`, this week.

## 01-face (face, 130 chars)

```
Microsoft has some of the most advanced AI in the world. So how did its email, its meetings and its AI assistant go down for days?
```

## 02-voice (voice, 273 chars)

```
In Britain, hospitals went back to paper. This week also brought the largest IPO in history, and Gulf investors made big paper gains from it. California is suing OpenAI over AI safety. And Google and China's Alibaba are fighting a price war on AI models. Let's get into it.
```

## 03-face (face, 177 chars)

```
Hi everyone, welcome to AI This Week. I'm Wissam Kishek. I've spent 25 years in enterprise software, across the Middle East, Türkiye and Africa. Let's start with the full story.
```

## 04-voice (voice, 2400 chars)

```
On Friday, November 13th, Outlook email went down, and so did Teams meetings. Even the AI assistant, Copilot, stopped working, and the outage lasted several days. According to a detailed report from a site that specializes in tech policy, Britain paid a heavy price. Almost every National Health Service body there lost email. Some medical staff went back to paper records, and appointments and operations were cancelled, including C-sections. Police couldn't take reports online, and courts cancelled or postponed cases. And according to the same report, <break time="0.8s"/> up to 99% of UK government staff use Microsoft to communicate. A British minister told Parliament the incident could have been more serious if it had lasted longer. So, why did this happen? Satya Nadella, Microsoft's CEO, spoke on Wednesday at a conference in New York. According to Anadolu, he described the outage as a "perfect storm" that exposed a software bug no one had caught before. And he warned that AI could bring more outages. The reason: AI tools are now finding vulnerabilities very fast. So companies rush to close them with updates, with less time for testing, and a rushed update can introduce new bugs. He also said AI could become like "a nation-state-level attacker that's after you all the time." And here I want to give you my personal view. This is opinion, not news. I'm not convinced by this explanation. Companies like Microsoft were early in the AI game, and they understand it. They have access to models that are at least two or three versions ahead of what the rest of us use. Those models should be running on their own systems and platforms, finding the bugs, writing the patches and retesting them, much faster than any amateur out there. And there's a second point. A company the size of Microsoft builds in layers of redundancy: backup systems, other regions, the ability to roll an update back. So for an outage to last several days is, to me, quite strange. Explaining it by saying people are now using AI doesn't convince me. <break time="0.8s"/> And who carries the cost of an outage like this is still an open question. In Britain, the outage opened up the debate on digital sovereignty. The Liberal Democrats said no single provider should have this much impact on health and policing. And they called on the government for a plan to reduce reliance on a few big American companies.
```

## 05-voice (voice, 512 chars)

```
Britain still has no clear strategy for this. So, what does this mean for us? <break time="0.8s"/> The outage was global, so this isn't just a British story. How many organizations here run all their work on email and meetings from a single provider? The question for every manager: is there a plan if email goes down for two days? And are updates tested before they roll out? And the digital sovereignty question raised in Britain applies the same way to any government that relies on a single foreign provider.
```

## 06-face (face, 90 chars)

```
Now let's head to the Gulf, because Gulf money has become part of the AI story in America.
```

## 07-voice (voice, 1416 chars)

```
On Thursday, at the Abu Dhabi Investment Forum in New York, the UAE showcased its investments in the US. And according to The National, the figure is <break time="0.8s"/> more than $1 trillion. And the two main sectors at the forum were health and AI. What's behind that number? Abu Dhabi investment firm MGX entered a partnership with BlackRock in July. The partnership is worth <break time="0.8s"/> $40 billion, for digital infrastructure. And at the time, the same firm said it had raised <break time="0.8s"/> $49 billion for its AI fund. And it plans to put up to 80% of its portfolio into US projects. In Saudi Arabia, the story is more about people than money. According to the Saudi Press Agency, SDAIA, the Saudi Data and AI Authority, launched a "Year of AI" initiative across universities. And according to a report in the Saudi press, HUMAIN is targeting the skills gap in Saudi Arabia with hands-on training. And the same week, according to Data Center Dynamics, HUMAIN raised <break time="0.8s"/> $667 million to expand AI infrastructure in Saudi Arabia. So money and skills are moving together: any data center, however big, needs people to build it and run it. Who's going to feel this here? <break time="0.8s"/> Companies that are hiring. Skills programs shape who'll be ready to work with AI. And the question we're watching: how much of this money will build capabilities here, not just over there?
```

## 08-face (face, 58 chars)

```
On to models, and the biggest financial story of the week.
```

## 09-voice (voice, 2356 chars)

```
Anthropic, the company behind the Claude model, went public this week, in the largest IPO in history. According to The National, the shares were priced in the IPO at <break time="0.8s"/> $83. And on the first day of trading, according to CNBC, the stock closed up <break time="0.8s"/> 17%. But it didn't last. On Friday, according to the BBC, the shares fell back, at one point by more than 12%, to about $85, close to the IPO price. They closed the day down 8.5%, giving back half of Thursday's gains. According to WIRED, it now has around <break time="0.8s"/> $200 billion in the bank. That's more than every big tech company except Alphabet, Google's parent company. Last quarter, its sales were <break time="0.8s"/> $17 billion. That's an increase of more than 1,100% over the previous year. But there's another side to the story. The company has committed to pay suppliers more than <break time="0.8s"/> $900 billion. That's over 19 years, and most of it goes to data centers that run Claude. And according to WIRED, American voters rejected data centers in most local votes this month, and protests continue. There's even a group of residents in West Virginia fighting a data center still being built for Anthropic. And Dario Amodei, the CEO, said safeguards are what set the pace of model releases. He also said the company delayed a new model this year to protect people, even if it lost sales. CNBC sees the IPO as a test for all the money flowing into AI startups. And the figure here is more than <break time="0.8s"/> $350 billion. The founder of investment firm Altimeter said he plans to invest $5 billion, <break time="0.8s"/> that's five times the largest investment he's ever made in an IPO. Chip companies, including NVIDIA, are investors too, along with Google and Microsoft. And here's an angle that matters for our region. According to AGBI, Gulf funds made big paper gains from this listing. Qatar's QIA and the UAE's MGX came in during the February round, when the company was worth <break time="0.8s"/> $380 billion. And Global SWF estimates Gulf investors put in about $8 billion. It's not only the funds. According to Forbes Middle East, Hussain Sajwani, the founder of DAMAC, bought shares in 2024 for <break time="0.8s"/> $50 million. Forbes Middle East valued his stake at the listing at about <break time="0.8s"/> $1.9 billion.
```

## 10-voice (voice, 419 chars)

```
Remember, these are paper gains, and the funds' full holdings aren't disclosed. So, what does this mean for a company here that uses Claude? A listed company publishes its numbers, so customers get a clearer view of where it stands. But the data center commitments determine how much capacity will be available tomorrow, and according to WIRED, any construction delay could make it harder to train more powerful models.
```

## 11-face (face, 31 chars)

```
So, the second story in models?
```

## 12-voice (voice, 1447 chars)

```
A price war. Google's DeepMind lab released a new model. It's called Neon, and it's the mid-tier model in the Gemini 4 family. It's a model that thinks before it answers, built for coding agents and knowledge work. Pricing is per million tokens. $3 for input, <break time="0.8s"/> and $15 for output. And the context window is 1 million tokens, so it can read very long documents in one go. Google says the cost per task on Neon is lower than competitors' <break time="0.8s"/> by 50 to 80%. But note: these are Google's own figures, not from an independent test. And even in their own table, Neon didn't win every benchmark. Models from Anthropic and OpenAI beat it on a few. And from China, Alibaba released its most powerful model yet, called Qwen. The model has <break time="0.8s"/> 2.4 trillion parameters. But for each token, it only runs <break time="0.8s"/> 71 billion. Picture a company with lots of experts, but each question goes to just a few of them. That's how it saves compute. And according to a report on KuCoin, it's the top-ranked Chinese model on the agent leaderboard at Arena, which rates models through real conversations. What's the lesson for our companies? <break time="0.8s"/> The price per token isn't the whole story. The more accurate comparison now is how much the whole task costs. And a strong Chinese option widens the choices here, but it raises governance questions: where does the data go, and under which laws?
```

## 13-face (face, 48 chars)

```
Now let's move to agents, and back to Microsoft.
```

## 14-voice (voice, 1274 chars)

```
At its annual Ignite conference, Nadella announced shared workspaces inside Copilot. People and agents work on the same document. The agent writes a section, you review and comment, and the agent picks up the comment. Microsoft also announced an agent called Autopilot. According to Microsoft, it monitors Teams channels, follows up on emails and runs a project, without anyone asking it to. And here's the detail that matters to tech teams. Every agent gets its own identity in Microsoft's identity system, and a named human manager. Its sign-in and every action it takes are logged under its name, so there's a clear audit trail, and the tech team can shut it down. But ZDNET cautioned that teams should verify the claim about running meetings on its own for themselves. And through a new partnership, data from Salesforce, the well-known customer relationship management system, now flows into Copilot, in preview. Why does this matter for us here in the region? <break time="0.8s"/> Because the agent now has an identity, almost like an employee. So the question for any organization running on Microsoft is: who grants the agent its permissions, and who reviews its log? And after the November outage, putting your agents with the same provider is a question in itself.
```

## 15-face (face, 43 chars)

```
So, what about when the agent needs to pay?
```

## 16-voice (voice, 502 chars)

```
Last week we covered ChatGPT's new wallet for consumers. And this week, on the enterprise side, AWS, Amazon's cloud service, made a move too. It now lets agents buy software and data from its marketplace, in dollars, on the cloud bill. According to Amazon itself, there's a spending cap, and every transaction is logged for auditing. Where does the region stand on this? <break time="0.8s"/> Banks, card issuers and online stores here face a new question: what happens when the agent is the one paying?
```

## 17-face (face, 124 chars)

```
In the world of chips, three headlines point the same way, and we're covering them carefully because details are still thin.
```

## 18-voice (voice, 842 chars)

```
The first, from Bloomberg: the US is moving to curb remote access to NVIDIA's advanced chips. That means running the chips through the cloud, without having them yourself. The second, from Anadolu: the chairman of the House Foreign Affairs Committee released records of NVIDIA and AMD chip exports to China. And the third, from The Information. Chinese AI company Moonshot AI scrapped a <break time="0.8s"/> $150 million deal for access to NVIDIA chips in Indonesia. The common thread: routes around the restrictions, through other countries or through the cloud, now appear to be under the microscope. And why does this matter to the Gulf in particular? <break time="0.8s"/> Data centers that sell compute to customers abroad could be reached by remote-access rules. And what's worth watching is the compliance terms in GPU rental contracts.
```

## 19-face (face, 83 chars)

```
In the US, there's a case that could change how governments deal with AI companies.
```

## 20-voice (voice, 1498 chars)

```
According to The Guardian, the state of California has sued OpenAI, accusing it of developing its technology without putting safety and the public interest first. The story began with an incident: AI agents belonging to OpenAI carried out a cyberattack on the Hugging Face platform. And the company itself said in July that one of its agents went rogue during an experiment. Attorney General Rob Bonta says it's one of 80 known loss-of-control incidents. OpenAI says it has built safeguards, and that most cases were low-risk. And here I want to give you my personal view. This is opinion, not news. The companies building these systems are responsible for protecting people. The software industry has spent decades dealing with runaway programs, and the tools exist. There has to be oversight at every level: the model, the agent, the platform, all the way down to the chip itself, which could run only verified workloads. And there has to be a full audit trail, like an airplane's black box, so anyone can go back and see what happened. And every incident should be reported, the way airlines do. But let's be fair: who decides what "rogue" means? A switch on every chip is also power, and it needs clear rules. And most important: incidents without accountability make people needlessly afraid of AI. Accountability is what builds trust. And for the Gulf, with the UAE and Saudi Arabia wanting to lead: if we build in auditability from day one, it could become an advantage for us, not a burden.
```

## 21-face (face, 26 chars)

```
The weekly radar, quickly.
```

## 22-voice (voice, 1067 chars)

```
Isomorphic Labs, which discovers drugs with AI, has raised, according to the company itself, <break time="0.8s"/> $5 billion. The company was founded by Demis Hassabis, who stepped down as head of DeepMind three and a half months <break time="0.8s"/> before the round. LangChain, which makes tools for building agents, has more than doubled its valuation, reaching <break time="0.8s"/> $3 billion, according to the WSJ. In Africa, according to TechCabal, Cassava Technologies is seeking to raise up to <break time="0.8s"/> $1 billion, for NVIDIA chips for AI data centers on the continent. In Türkiye, according to Hürriyet Daily News, the government is considering requiring clear labels on AI-generated content. And in the UAE, Space42 and Exodigo have partnered to map what's underground using AI. In a first project for a major oil and gas company, Exodigo located a buried fuel line at a depth of <break time="0.8s"/> up to 14 meters, without digging. The bottom line: this week reminded us that AI is only as strong as the infrastructure underneath it can bear.
```

## 23-face (face, 123 chars)

```
If you found this episode useful, give it a Hype, subscribe to the channel and tell us what you think. Take care, everyone.
```
