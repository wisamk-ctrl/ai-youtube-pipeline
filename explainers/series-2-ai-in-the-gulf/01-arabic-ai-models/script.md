Arabic is the language of a whole region. Yet QCRI, Qatar's national computing research institute, says it makes up only about half a percent of web data. [Pause 2s] By the end, you'll know why that trips up AI, and who builds AI that speaks it.

[On-Screen Text: 400 million+ Arabic speakers | ~0.5% of web data (Fanar 2.0 paper, QCRI)]

[Section: Why Arabic breaks AI]

Let's start with why Arabic is so hard for AI in the first place. [Pause]

The first problem is data. Large language models, the systems behind chatbots, learn by reading enormous amounts of text. The model makers put Arabic speakers at more than [Pause] 400 million. Yet the web offers little Arabic text to learn from. [Pause] Preslav Nakov of MBZUAI, Abu Dhabi's AI university, says Arabic "has long been underserved in AI development due to limited high-quality data."

I'm Wissam, and this is AI This Week, AI Explained.

The second problem is that there is no single Arabic. Modern Standard Arabic, or MSA, is the formal language. TII, Abu Dhabi's Technology Innovation Institute, says it is used mainly in writing, education and news. [Pause] Everyday conversation happens in regional dialects. Those dialects are underrepresented in training data. TII puts it well. A model trained mainly on MSA "may understand every word of an Emirati sentence while still missing its intended meaning."

[On-Screen Text: MSA at the centre | Gulf · Levantine · Egyptian · North African]

Third, people mix languages. This is called code-switching. MBZUAI's Haonan Li says Arabic speakers slip "into English or French mid-sentence and back again." [Pause] Egyptian Arabic is also often typed in Latin letters. That is called Arabizi.

Fourth, and hardest, is tokenisation. A token is a small piece of text: a word, or part of a word. A tokeniser is the tool that chops text into those pieces before the model reads them. [Pause] The AraToken paper says general-purpose tokenisers are trained mostly on English and Latin-script languages. With Arabic, they produce "inflated token sequences."

Here's an illustration, not a measurement. Picture a cashier who only stocks big banknotes in one currency. Pay in English, and the bill is settled in a few big notes. [Pause] Pay in Arabic, and the cashier counts it out in small coins. More pieces, more time, more cost. [Pause] And less fits in the till. That till is the context window, meaning how much text a model can hold at once.

Spelling matters too. One study normalised Arabic spelling variation, such as the different forms of Alif. That cut tokens per word by [Pause] 18 percent.

[On-Screen Text: Normalising spelling: 1.35 → 1.199 tokens per word (AraToken)]

Diacritics add another twist. These are the small marks that show pronunciation or meaning. [Pause] A 2026 study found models cope with the light diacritics of everyday text. [Pause] But fully diacritised text "leads to substantially increased token fragmentation and degraded performance."

Last, measurement. A benchmark is a standard test for models. [Pause] The organisers of the Open Arabic LLM Leaderboard say many early Arabic benchmarks "were direct translations from English." So their second version removed machine-translated tasks.

[Section: The UAE's two tracks: Jais and Falcon]

Now to Abu Dhabi, where two teams took two different roads. [Pause]

Jais came first. On [Pause] 30 August 2023, Inception released it as open source. Inception is part of G42, an Abu Dhabi AI group. It worked with MBZUAI and with Cerebras, an American AI chipmaker. [Pause] Jais had 13 billion parameters. Parameters are the internal settings a model learns, roughly a measure of its size. It was trained on 116 billion Arabic tokens and 279 billion English tokens. [Pause] Jais is named after the UAE's highest peak. Early users named at launch included ADNOC, Etihad Airways and First Abu Dhabi Bank.

[On-Screen Text: Jais 13B, 30 August 2023, Inception (G42), MBZUAI, Cerebras]

A larger Jais followed in November 2023. Then, Middle East AI News reports, Inception released a family of 20 open Jais models in late 2024.

Jais 2 arrived in December 2025. It came in two sizes: [Pause] 8 billion and 70 billion parameters. It was trained from scratch, meaning built from zero rather than adapted from another company's model. [Pause] Its makers say it used "the richest Arabic-first dataset to date." It also has its own Arabic-centric vocabulary of [Pause] 150,272 tokens. That's our cashier, finally stocking the right denominations. [Pause] Its licence, Apache 2.0, permits commercial use.

On AraGen, an Arabic benchmark, the large Jais 2 scores about [Pause] 71 percent, its model card reports. Qwen, a rival open model of similar size, scores about 63. [Pause] Llama, another rival open model, scores about 61. The same card shows Jais 2 trailing those rivals on English instruction-following.

[On-Screen Text: AraGen (self-reported): Jais-2-70B 70.71% | Qwen2.5-72B 62.58% | Llama-3.3-70B 61.29%]

Jais 3 arrived in October 2026, as a fleet of six open models. The smallest has 900 million parameters. The largest has [Pause] 375 billion. [Pause] It is built on K2 Horizon, MBZUAI's fully open model fleet. Every Jais 3 model has a context window of 512,000 tokens. MBZUAI calls that the longest of any Arabic-native model. [Pause] There's also Jais Speech, which transcribes dialects spoken across 19 Arab countries.

Falcon took a different road. TII launched Falcon Arabic in May 2025, built on its Falcon 3 model with seven billion parameters. [Pause] It was trained on native Arabic data, not translations. TII says it matches models up to 10 times its size.

Falcon-H1 Arabic followed in January 2026, with up to 34 billion parameters. [Pause] It uses a hybrid architecture, combining two model designs called Mamba and Transformer. TII says its context of 256,000 tokens equals roughly 100,000 words. [Pause] On the Open Arabic LLM Leaderboard, TII says its largest model beats bigger rival open models, including Qwen and Llama.

[On-Screen Text: Falcon-H1 Arabic 34B: 75.36% OALL average (TII, January 2026)]

Then in October 2026 came Falcon-Emirati, a seven-billion-parameter model for the Emirati dialect. TII says it scored [Pause] 84.83 percent on Alyah, an Emirati benchmark. [Pause] Alongside it came Falcon-ASR for speech-to-text, and Falcon-OCR-Arabic for reading text in images and documents.

[On-Screen Text: Falcon-Emirati: 84.83% on Alyah (TII, October 2026)]

So, broadly, Jais has tended to go big, while Falcon has focused on smaller, efficient models. As of May 2025, TII said the Falcon ecosystem had over 55 million downloads.

[Section: Saudi Arabia: ALLaM and HUMAIN Chat]

Next, Riyadh, where the journey ran from a research lab to a consumer app. [Pause]

ALLaM is developed by the National Center for AI at SDAIA, the Saudi Data and AI Authority. Its paper appeared in July 2024. [Pause] The idea is to teach a model Arabic as a "second language." The team expands its vocabulary and trains on mixed Arabic and English. That way, the model doesn't forget its English.

ALLaM-7B was first trained on [Pause] 4 trillion English tokens. Then came 1.2 trillion mixed Arabic and English tokens.

[On-Screen Text: ALLaM-7B: 4T English + 1.2T Arabic/English tokens = 5.2T]

Distribution came through partners. According to the Saudi Press Agency, ALLaM went first to IBM's watsonx, then Microsoft Azure, then Qualcomm AI Cloud. [Pause] In March 2025, SDAIA listed the 7B model on Hugging Face, the public hub where AI models are shared.

Then, in August 2025, HUMAIN, a Public Investment Fund company, launched HUMAIN Chat. It runs on ALLaM 34B, which builds on SDAIA's earlier models. [Pause] HUMAIN says the model was refined with input from over 600 domain experts and 250 evaluators. HUMAIN Chat offers Arabic speech input across dialects, and switching between Arabic and English.

[Pause]

Crucially, HUMAIN says it is hosted end-to-end on its own infrastructure inside the Kingdom. It also complies with the PDPL, Saudi Arabia's personal data protection law. [Pause] One difference from the 7B: HUMAIN Chat is a service. Our research found no open release of the 34B model's weights, the trained files anyone can download and run.

[Section: Qatar's Fanar and the rest of the field]

Now to Doha, and then a few important players beyond the three hubs. [Pause]

Fanar is built by QCRI, Qatar's national computing research institute, at Hamad Bin Khalifa University. It is sponsored by Qatar's Ministry of Communications and IT. [Pause] The first version, described in January 2025, had two models. Fanar Star was trained from scratch. Fanar Prime was continually trained from Google's Gemma-2, meaning it started from an existing model and kept learning.

[Pause]

Fanar is a platform, not just a model. It includes an Islamic retrieval system for religious questions. Retrieval means the system looks things up in trusted sources before answering. [Pause] A second retrieval system, "Recency RAG", handles current events.

Fanar 2.0 came in March 2026. Fanar's core model builds on Google's open Gemma 3. [Pause] QCRI says it used eight times fewer pretraining tokens than Fanar 1.0. Yet on ArabicMMLU, a knowledge test, the model card reports a rise from [Pause] 67.35 to 74.67 percent. Quality over quantity. [Pause] The stack adds Fanar-Diwan for classical poetry, Fanar-Sadiq for Islamic content, and FanarGuard, a safety filter.

[On-Screen Text: Fanar-2-27B (from Gemma-3-27B): ArabicMMLU 67.35% → 74.67% | Apache 2.0]

Back in Abu Dhabi, MBZUAI and G42 built K2 Think, a reasoning model released in September 2025. It's not Arabic-specific. [Pause] Its makers say it matches or beats much larger models. Its successor, K2 Think V2, is described by MBZUAI as fully open, from pre-training through post-training.

[Pause]

Global companies compete too. In February 2025, Cohere released Command R7B Arabic, with about 8 billion parameters. Cohere says it can run on a MacBook, or even on ordinary processors. [Pause] But its licence, CC-BY-NC, does not allow commercial use.

And for Egypt, MBZUAI Paris built Nile-Chat, which reads and writes both Arabic script and Arabizi.

[Section: Who is best? Reading the leaderboards]

Finally, the question everyone asks: which model is best? [Pause]

Leaderboards rank models on shared tests. The Open Arabic LLM Leaderboard launched in May 2024. It came from 2A2I, an Arabic AI research initiative, together with TII and Hugging Face. [Pause] Within seven months, its organisers say, it received more than 700 models. In September 2024, SDAIA and the King Salman Global Academy for Arabic Language launched the BALSAM Index. [Pause] And in December 2024, Inception and MBZUAI launched AraGen, the first leaderboard for generative tasks in Arabic.

[On-Screen Text: OALL (May 2024) · BALSAM (Sep 2024) · AraGen (Dec 2024)]

Here's the catch. Almost everyone claims the top spot. In January 2026, TII said Falcon-H1 Arabic leads its leaderboard across sizes. [Pause] The Jais 2 report claims leading results among the models it evaluated. In October 2026, MBZUAI's large-model lab said Jais 3 leads open models on Arabic agentic tasks. Those are tasks where the AI carries out steps on its own. [Pause] Most of these scores are published by the makers themselves, against rivals they chose.

[On-Screen Text: Wissam's view]

This next part is my view, not a finding from the sources. [DRAFT VIEW: founder to confirm]

After twenty-five years selling enterprise software in this region, I've learned that headline rankings rarely decide anything. What decides is fit. [Pause] Does the model understand the dialect your customers actually speak? Does the licence allow what you plan to do? And where does your data live? [Pause] A model that tops a leaderboard but can't legally sit inside your country, or your contract, isn't the best model for you. I'd rather see a team run five candidates on its own documents than read five press releases. [Pause] And here's the question I'll be watching. When a Gulf government or bank chooses its AI, what will it pick? A home-grown Arabic model, or a global model that has simply got better at Arabic? I don't think the answer will be the same everywhere.

[Section: The bottom line]

Three things to remember.

First, Arabic is hard for AI. There's little data, many dialects, mixed languages, and tokenisers built for English. [Pause]

Second, the region's builders take different roads. Jais has gone big, with models trained from scratch and later built on open foundations. Falcon focuses on efficient models and dialects. ALLaM teaches Arabic as a second language, and powers HUMAIN Chat. Fanar adapts strong open models and wraps them in a platform. [Pause]

Third, read every "number one" claim carefully. Check who measured it, when, and against whom. And check the licence. [Pause]

[Pause 2s]

Next time in the series, we map the who's who of AI in the UAE. If this helped, please Hype the video, then subscribe and tell me in the comments which model you'd test first.
