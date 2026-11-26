[On-Screen Text: about 0.5% of web data | 400 million+ speakers]

Arabic is spoken by hundreds of millions of people, yet it makes up only about [Pause] half a percent of web data. [Pause] By the end, you will know who builds AI that truly speaks Arabic, how they do it, and how to judge their claims.

[Section: Why Arabic breaks AI]

First, why Arabic is so hard for AI. [Pause]

Start with the raw material. A large language model, or LLM, is the kind of AI behind chatbots. It learns language by reading enormous amounts of text.

The Fanar 2.0 paper from QCRI, Qatar's computing research institute, is the source for that half-percent figure. And it is the root of everything else in this story.

[On-Screen Text: Arabic ≈ 0.5% of web data (Fanar 2.0 paper, QCRI)]

[Pause]

I'm Wissam, and this is AI This Week, AI Explained.

[Pause]

MBZUAI's Preslav Nakov puts it plainly. He says Arabic "has long been underserved" because of limited high-quality training data. The Fanar paper sets that sliver of data against [Pause] 400 million native speakers.

The second problem is that Arabic is really many Arabics. Modern Standard Arabic, or MSA, is the formal language of writing, education and news. [Pause] Daily conversation happens in regional dialects, and those dialects are thin in AI training data.

Abu Dhabi's Technology Innovation Institute, TII, gives a sharp example. A model trained mainly on MSA "may understand every word of an Emirati sentence while still missing its intended meaning." [Pause]

[On-Screen Text: MSA at the centre | Gulf · Levantine · Egyptian · North African]

Third, people mix languages. MBZUAI's Haonan Li says Arabic speakers slip "into English or French mid-sentence and back again." That habit is called code-switching. Many Egyptians also type Arabic in Latin letters, a style known as Arabizi. [Pause]

Fourth, and hardest to picture, is tokenisation. Models do not read words. They read tokens, which are small chunks of text. A tokeniser is the tool that cuts text into those chunks. [Pause]

Here is an illustration, not a measurement. Picture a cashier who only stocks big banknotes in one currency. Pay in English, and the bill is settled in a few big notes. Pay in Arabic, and the cashier counts it out in small coins. [Pause]

That means more pieces, more time and more cost. Less also fits in the till. In AI, that till is the context window: how much text a model can hold at once. [Pause]

The research matches the picture. The AraToken paper says general-purpose tokenisers, trained mostly on English, produce "inflated token sequences" for Arabic.

Arabic spelling varies too, with different forms of Alif, optional vowel marks called diacritics, and Arabic-Indic numerals. In one study, tidying up that variation cut tokens per word by [Pause] 18%.

[On-Screen Text: 1.35 → 1.199 tokens per word (−18%), AraToken study]

A study at EACL 2026, a language research conference, found models cope with the light diacritics of everyday text. [Pause] Fully diacritised text, though, "leads to substantially increased token fragmentation and degraded performance." [Pause]

Finally, the tests themselves were weak. A benchmark is a standard exam for AI models. The team behind the Open Arabic LLM Leaderboard says many early Arabic benchmarks "were direct translations from English." [Pause]

[Section: The UAE's two tracks: Jais and Falcon]

Now to Abu Dhabi, where two teams have taken different roads. [Pause]

The first road is Jais, named after the UAE's highest peak. Inception, a G42 company, released it open-source on 30 August 2023. It worked with MBZUAI and Cerebras, which co-built the supercomputer Jais trained on.

It had [Pause] 13 billion parameters. Parameters are the internal settings a model adjusts while learning. More parameters usually means a bigger, more capable model.

[On-Screen Text: Jais (Aug 2023): 13B parameters | 116B Arabic + 279B English tokens]

It trained on 116 billion Arabic tokens and 279 billion English tokens. [Pause] Early users named at launch included the UAE Ministry of Foreign Affairs, ADNOC, Etihad Airways, First Abu Dhabi Bank and e&.

Jais 30B followed in November 2023. [Pause] In the second half of 2024, Middle East AI News reports, Inception released 20 open Jais models. The smallest had 590 million parameters, the largest 70 billion.

[Pause]

Jais 2 arrived in December 2025. The largest version has 70 billion parameters. A smaller 8-billion version came alongside. [Pause] It was trained from scratch, meaning it did not start from someone else's model. Remember the cashier? Jais 2 stocks the right notes. Its vocabulary of [Pause] 150,272 tokens was built around Arabic.

[On-Screen Text: Jais 2 (Dec 2025): 8B and 70B | 150,272-token Arabic-centric vocabulary | Apache 2.0]

It carries an Apache 2.0 licence. That makes it open weights: anyone can download the model, and commercial use is allowed. [Pause]

On the AraGen benchmark, the makers report [Pause] 70.71% for their largest model. A 72-billion Qwen model scored 62.58%. A 70-billion Llama model scored 61.29%. [Pause] The same model card shows Jais 2 trailing both on English instruction-following.

[On-Screen Text: AraGen (makers' figures): Jais-2-70B 70.71% | Qwen2.5-72B 62.58% | Llama-3.3-70B 61.29%]

[Pause]

Then, in October 2026, came Jais 3. It is a fleet of six open models, plus Jais Speech. The largest has [Pause] 375 billion parameters.

[On-Screen Text: Jais 3 (Oct 2026): six models, 900M to 375B | 512K-token context | Jais Speech]

Every model holds 512,000 tokens of context, which MBZUAI calls the longest of any Arabic-native model. [Pause] Jais Speech covers dialects from 19 Arab countries, and can tell which one is being spoken. [Pause]

The second road is Falcon, from TII. Falcon Arabic launched on 21 May 2025. It was built on Falcon 3, a 7-billion model, and trained on native Arabic data, not translations. TII says it matches models up to [Pause] ten times its size.

[Pause]

Falcon-H1 Arabic followed in January 2026. It comes in three sizes, the largest at 34 billion parameters. It uses a hybrid design that combines two ways of processing text, called Mamba and Transformer. [Pause]

Its context reaches 256,000 tokens, which TII says is roughly 100,000 words. That is enough, TII says, for long legal documents or medical records in one go. [Pause]

[On-Screen Text: Falcon-H1 Arabic (Jan 2026): 3B · 7B · 34B | up to 256K tokens ≈ 100,000 words]

As of January 2026, TII reported a leaderboard average for its largest model of [Pause] 75.36%. TII says that beat Qwen and Llama models of 70 billion parameters and more.

[On-Screen Text: OALL average (TII, Jan 2026): Falcon-H1 Arabic 34B 75.36% | vs Qwen2.5 72B, Llama-3.3 70B]

[Pause]

On 6 October 2026, TII launched Falcon-Emirati, a 7-billion model for the Emirati dialect. It scored [Pause] 84.83% on Alyah, an Emirati benchmark. Alongside it came speech-to-text and a tool that reads Arabic text from images. [Pause]

So the contrast is clear. Jais goes big and builds from scratch. Falcon goes compact and efficient.

[Section: Saudi Arabia: ALLaM and HUMAIN Chat]

Next, Riyadh, and a model that moved from the lab to a national chatbot. [Pause]

ALLaM comes from the National Center for AI at the Saudi Data and AI Authority, SDAIA. Its research paper appeared in July 2024. [Pause]

Its idea is to teach Arabic as a "second language." The team expands the model's vocabulary and trains on mixed Arabic and English. The goal is to steer the model towards Arabic without it forgetting English.

The 7-billion model learned from [Pause] 4 trillion English tokens first. Then it learned from 1.2 trillion mixed Arabic and English tokens.

[On-Screen Text: ALLaM-7B: 4T English + 1.2T Arabic/English tokens = 5.2T]

[Pause]

ALLaM reached people through partners. The Saudi Press Agency says it went first to IBM's watsonx, then Microsoft Azure, then Qualcomm's AI Cloud. [Pause] On 6 March 2025, SDAIA listed the 7-billion model on Hugging Face. That is a public website where AI models are shared for download.

[Pause]

Then came the bigger step. On 25 August 2025, HUMAIN, a Public Investment Fund company, launched HUMAIN Chat. It runs on ALLaM 34B. [Pause]

HUMAIN says experts shaped that model: more than 600 domain experts and 250 evaluators. A team of over 120 AI specialists, including 35 PhD holders, built it.

[On-Screen Text: HUMAIN Chat (Aug 2025), powered by ALLaM 34B]

[Pause]

HUMAIN Chat accepts Arabic speech across dialects and handles Arabic-English switching. It is hosted end-to-end on HUMAIN infrastructure inside Saudi Arabia. It operates under the PDPL, the Kingdom's personal data protection law. [Pause]

One difference matters. The 7-billion ALLaM can be downloaded. Public sources show the 34-billion model offered as a service, not as open weights.

[Section: Qatar's Fanar and the rest of the field]

Now Doha, and a different idea: a whole platform, not a single model. [Pause]

Fanar comes from QCRI at Hamad Bin Khalifa University, sponsored by Qatar's Ministry of Communications and IT. The first version, described in January 2025, had two models. [Pause] Fanar Star was trained from scratch. Fanar Prime was continually trained from Google's Gemma-2. Continual training means taking an existing model and teaching it more. [Pause]

Fanar also uses retrieval, often called RAG. The system looks things up in trusted sources before answering. Fanar has an Islamic retrieval system for religious questions, and a "Recency RAG" for current events. [Pause]

Fanar 2.0 was published in March 2026. Its core is a 27-billion model, built from Google's Gemma 3. QCRI trained it on 256 NVIDIA H100 chips. It used [Pause] eight times fewer pretraining tokens than Fanar 1.

[On-Screen Text: Fanar 2.0 (Mar 2026): 27B | 8× fewer pretraining tokens | Apache 2.0]

Fewer tokens still brought better scores. The model card reports ArabicMMLU, a test built from school exam questions, rising from 67.35% to 74.67%. [Pause] The stack adds Fanar-Diwan for classical poetry, Fanar-Sadiq for Islamic content, and FanarGuard, a safety filter. [Pause]

Beyond the big three, a few names round out the field. MBZUAI's K2 Think, released in September 2025, is a reasoning model, strongest in maths. It is not Arabic-specific. Its second version has 70 billion parameters. MBZUAI says it is fully open "from pre-training through post-training." [Pause]

Cohere released Command R7B Arabic on 27 February 2025. It is small enough to run on a MacBook, or even on ordinary processors. Its licence, CC-BY-NC, does not allow commercial use. [Pause]

And for Egypt, MBZUAI Paris built Nile-Chat, which reads and writes both Arabic script and Arabizi. On Latin-script tests, its makers report a [Pause] 14.4% gain for the largest model over a similar-sized Qwen model.

[On-Screen Text: Nile-Chat 12B: +14.4% vs Qwen2.5-14B-Instruct on Latin-script benchmarks (makers' figures)]

[Section: Who is best? Reading the leaderboards]

Finally, the question everyone asks: which one is best? [Pause]

Arabic now has its own scoreboards. The Open Arabic LLM Leaderboard launched in May 2024. In under seven months, it received more than [Pause] 700 models. They came from over 180 organisations. [Pause]

SDAIA and the King Salman Global Academy for Arabic Language launched the BALSAM Index in September 2024. Inception and MBZUAI launched AraGen that December. It was the first leaderboard for generative Arabic tasks, where the model writes its own answers. [Pause]

[On-Screen Text: OALL (May 2024) · BALSAM (Sep 2024) · AraGen (Dec 2024)]

Here is the catch. Almost every maker claims the top spot. TII claimed the lead for Falcon-H1 Arabic in January
