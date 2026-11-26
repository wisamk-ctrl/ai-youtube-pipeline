# Source map

163 spoken sentences · 113 claims · 90 sourced · 10 partial · **13 unsourced claims**

## Partial support — check the wording

- (8) Yet the web offers little Arabic text to learn from.
- (11) Modern Standard Arabic, or MSA, is the formal language.
- (17) This is called code-switching.
- (41) Jais came first.
- (44) It worked with MBZUAI and with Cerebras, an American AI chipmaker.
- (57) Its licence, Apache 2.0, permits commercial use.
- (126) Leaderboards rank models on shared tests.
- (128) It came from 2A2I, an Arabic AI research initiative, together with TII and Hugging Face.
- (134) In January 2026, TII said Falcon-H1 Arabic leads its leaderboard across sizes.
- (153) There's little data, many dialects, mixed languages, and tokenisers built for English.

## ⚠️ Unsourced claims — fix before recording

- (1) Arabic is the language of a whole region.
- (6) Large language models, the systems behind chatbots, learn by reading enormous amounts of text.
- (21) A token is a small piece of text: a word, or part of a word.
- (22) A tokeniser is the tool that chops text into those pieces before the model reads them.
- (30) That till is the context window, meaning how much text a model can hold at once.
- (38) A benchmark is a standard test for models.
- (46) Parameters are the internal settings a model learns, roughly a measure of its size.
- (99) Our research found no open release of the 34B model's weights, the trained files anyone can download and run.
- (108) Retrieval means the system looks things up in trusted sources before answering.
- (116) Back in Abu Dhabi, MBZUAI and G42 built K2 Think, a reasoning model released in September 2025. — figure 42 not in the cited item(s)
- (136) In October 2026, MBZUAI's large-model lab said Jais 3 leads open models on Arabic agentic tasks.
- (137) Those are tasks where the AI carries out steps on its own.
- (140) After twenty-five years selling enterprise software in this region, I've learned that headline rankings rarely decide anything.

| # | sentence | kind | support | sources |
|---|---|---|---|---|
| 1 | Arabic is the language of a whole region. | claim | none |  |
| 2 | Yet QCRI, Qatar's national computing research institute, says it makes up only about half a percent of web data. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 3 | By the end, you'll know why that trips up AI, and who builds AI that speaks it. | transition | none |  |
| 4 | Let's start with why Arabic is so hard for AI in the first place. | transition | none |  |
| 5 | The first problem is data. | transition | none |  |
| 6 | Large language models, the systems behind chatbots, learn by reading enormous amounts of text. | claim | none |  |
| 7 | The model makers put Arabic speakers at more than 400 million. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception); [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004); [Institute of Foundation Models (ifm.ai)](https://ifm.ai/jais/); [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 8 | Yet the web offers little Arabic text to learn from. | claim | partial | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 9 | Preslav Nakov of MBZUAI, Abu Dhabi's AI university, says Arabic "has long been underserved in AI development due to limited high-quality data." I'm Wissam, and this is AI This Week, AI Explained. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/inception-cerebras-mbzuai-release-jais-2-the-next-generation-the-worlds-leading) |
| 10 | The second problem is that there is no single Arabic. | analysis | partial | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 11 | Modern Standard Arabic, or MSA, is the formal language. | claim | partial | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 12 | TII, Abu Dhabi's Technology Innovation Institute, says it is used mainly in writing, education and news. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 13 | Everyday conversation happens in regional dialects. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 14 | Those dialects are underrepresented in training data. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 15 | TII puts it well. | transition | none |  |
| 16 | A model trained mainly on MSA "may understand every word of an Emirati sentence while still missing its intended meaning." Third, people mix languages. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 17 | This is called code-switching. | claim | partial | [MBZUAI](https://mbzuai.ac.ae/news-events/news/inception-cerebras-mbzuai-release-jais-2-the-next-generation-the-worlds-leading); [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 18 | MBZUAI's Haonan Li says Arabic speakers slip "into English or French mid-sentence and back again." Egyptian Arabic is also often typed in Latin letters. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai); [arXiv (MBZUAI Paris)](https://arxiv.org/abs/2507.04569) |
| 19 | That is called Arabizi. | claim | direct | [arXiv (MBZUAI Paris)](https://arxiv.org/abs/2507.04569) |
| 20 | Fourth, and hardest, is tokenisation. | analysis | none | [arXiv](https://arxiv.org/abs/2512.18399) |
| 21 | A token is a small piece of text: a word, or part of a word. | claim | none |  |
| 22 | A tokeniser is the tool that chops text into those pieces before the model reads them. | claim | none |  |
| 23 | The AraToken paper says general-purpose tokenisers are trained mostly on English and Latin-script languages. | claim | direct | [arXiv](https://arxiv.org/abs/2512.18399) |
| 24 | With Arabic, they produce "inflated token sequences." Here's an illustration, not a measurement. | claim | direct | [arXiv](https://arxiv.org/abs/2512.18399) |
| 25 | Picture a cashier who only stocks big banknotes in one currency. | transition | none |  |
| 26 | Pay in English, and the bill is settled in a few big notes. | analysis | partial | [arXiv](https://arxiv.org/abs/2512.18399) |
| 27 | Pay in Arabic, and the cashier counts it out in small coins. | analysis | partial | [arXiv](https://arxiv.org/abs/2512.18399) |
| 28 | More pieces, more time, more cost. | analysis | partial | [arXiv](https://arxiv.org/abs/2512.18399) |
| 29 | And less fits in the till. | analysis | partial | [arXiv](https://arxiv.org/abs/2512.18399) |
| 30 | That till is the context window, meaning how much text a model can hold at once. | claim | none |  |
| 31 | Spelling matters too. | transition | none |  |
| 32 | One study normalised Arabic spelling variation, such as the different forms of Alif. | claim | direct | [arXiv](https://arxiv.org/abs/2512.18399) |
| 33 | That cut tokens per word by 18 percent. | claim | direct | [arXiv](https://arxiv.org/abs/2512.18399) |
| 34 | Diacritics add another twist. | transition | none |  |
| 35 | These are the small marks that show pronunciation or meaning. | claim | direct | [ACL Anthology (Findings of EACL 2026; Inoue, Alhafni, Habash, Baldwin)](https://aclanthology.org/2026.findings-eacl.22/) |
| 36 | A 2026 study found models cope with the light diacritics of everyday text. | claim | direct | [ACL Anthology (Findings of EACL 2026; Inoue, Alhafni, Habash, Baldwin)](https://aclanthology.org/2026.findings-eacl.22/) |
| 37 | But fully diacritised text "leads to substantially increased token fragmentation and degraded performance." Last, measurement. | claim | direct | [ACL Anthology (Findings of EACL 2026; Inoue, Alhafni, Habash, Baldwin)](https://aclanthology.org/2026.findings-eacl.22/) |
| 38 | A benchmark is a standard test for models. | claim | none |  |
| 39 | The organisers of the Open Arabic LLM Leaderboard say many early Arabic benchmarks "were direct translations from English." So their second version removed machine-translated tasks. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 40 | Now to Abu Dhabi, where two teams took two different roads. | transition | none |  |
| 41 | Jais came first. | claim | partial | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception); [Institute of Foundation Models (ifm.ai)](https://ifm.ai/jais/) |
| 42 | On 30 August 2023, Inception released it as open source. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 43 | Inception is part of G42, an Abu Dhabi AI group. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 44 | It worked with MBZUAI and with Cerebras, an American AI chipmaker. | claim | partial | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 45 | Jais had 13 billion parameters. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 46 | Parameters are the internal settings a model learns, roughly a measure of its size. | claim | none |  |
| 47 | It was trained on 116 billion Arabic tokens and 279 billion English tokens. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 48 | Jais is named after the UAE's highest peak. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 49 | Early users named at launch included ADNOC, Etihad Airways and First Abu Dhabi Bank. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 50 | A larger Jais followed in November 2023. | claim | direct | [Cerebras Systems (press release, PRNewswire/G42)](https://www.cerebras.ai/press-release/core42-sets-new-benchmark-for-arabic-large-language-models-with-the-release-of-jais-30b) |
| 51 | Then, Middle East AI News reports, Inception released a family of 20 open Jais models in late 2024. | claim | direct | [Middle East AI News](https://www.middleeastainews.com/p/inception-cerebras-and-mbzuai-release) |
| 52 | Jais 2 arrived in December 2025. | claim | direct | [Middle East AI News](https://www.middleeastainews.com/p/inception-cerebras-and-mbzuai-release); [Institute of Foundation Models (ifm.ai)](https://ifm.ai/jais/) |
| 53 | It came in two sizes: 8 billion and 70 billion parameters. | claim | direct | [Middle East AI News](https://www.middleeastainews.com/p/inception-cerebras-and-mbzuai-release); [MBZUAI](https://mbzuai.ac.ae/news-events/news/inception-cerebras-mbzuai-release-jais-2-the-next-generation-the-worlds-leading) |
| 54 | It was trained from scratch, meaning built from zero rather than adapted from another company's model. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat); [MBZUAI](https://mbzuai.ac.ae/news-events/news/inception-cerebras-mbzuai-release-jais-2-the-next-generation-the-worlds-leading) |
| 55 | Its makers say it used "the richest Arabic-first dataset to date." It also has its own Arabic-centric vocabulary of 150,272 tokens. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/inception-cerebras-mbzuai-release-jais-2-the-next-generation-the-worlds-leading); [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 56 | That's our cashier, finally stocking the right denominations. | analysis | partial | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 57 | Its licence, Apache 2.0, permits commercial use. | claim | partial | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat); [arXiv (MBZUAI, Cerebras, Inception)](https://arxiv.org/abs/2608.13580) |
| 58 | On AraGen, an Arabic benchmark, the large Jais 2 scores about 71 percent, its model card reports. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 59 | Qwen, a rival open model of similar size, scores about 63. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 60 | Llama, another rival open model, scores about 61. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 61 | The same card shows Jais 2 trailing those rivals on English instruction-following. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 62 | Jais 3 arrived in October 2026, as a fleet of six open models. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai); [Institute of Foundation Models (ifm.ai)](https://ifm.ai/jais/) |
| 63 | The smallest has 900 million parameters. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 64 | The largest has 375 billion. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 65 | It is built on K2 Horizon, MBZUAI's fully open model fleet. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 66 | Every Jais 3 model has a context window of 512,000 tokens. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 67 | MBZUAI calls that the longest of any Arabic-native model. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 68 | There's also Jais Speech, which transcribes dialects spoken across 19 Arab countries. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 69 | Falcon took a different road. | transition | none |  |
| 70 | TII launched Falcon Arabic in May 2025, built on its Falcon 3 model with seven billion parameters. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic) |
| 71 | It was trained on native Arabic data, not translations. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic) |
| 72 | TII says it matches models up to 10 times its size. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic) |
| 73 | Falcon-H1 Arabic followed in January 2026, with up to 34 billion parameters. | claim | direct | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model) |
| 74 | It uses a hybrid architecture, combining two model designs called Mamba and Transformer. | claim | direct | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model); [TII Falcon LLM site](https://falconllm.tii.ae/falcon-h1-arabic.html) |
| 75 | TII says its context of 256,000 tokens equals roughly 100,000 words. | claim | direct | [TII Falcon LLM site](https://falconllm.tii.ae/falcon-h1-arabic.html) |
| 76 | On the Open Arabic LLM Leaderboard, TII says its largest model beats bigger rival open models, including Qwen and Llama. | claim | direct | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model); [TII Falcon LLM site](https://falconllm.tii.ae/falcon-h1-arabic.html) |
| 77 | Then in October 2026 came Falcon-Emirati, a seven-billion-parameter model for the Emirati dialect. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 78 | TII says it scored 84.83 percent on Alyah, an Emirati benchmark. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 79 | Alongside it came Falcon-ASR for speech-to-text, and Falcon-OCR-Arabic for reading text in images and documents. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 80 | So, broadly, Jais has tended to go big, while Falcon has focused on smaller, efficient models. | analysis | partial | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai); [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic) |
| 81 | As of May 2025, TII said the Falcon ecosystem had over 55 million downloads. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic) |
| 82 | Next, Riyadh, where the journey ran from a research lab to a consumer app. | transition | none |  |
| 83 | ALLaM is developed by the National Center for AI at SDAIA, the Saudi Data and AI Authority. | claim | direct | [arXiv (SDAIA / NCAI)](https://arxiv.org/abs/2407.15390); [Hugging Face (SDAIA NCAI, hosted under humain-ai)](https://huggingface.co/humain-ai/ALLaM-7B-Instruct-preview) |
| 84 | Its paper appeared in July 2024. | claim | direct | [arXiv (SDAIA / NCAI)](https://arxiv.org/abs/2407.15390) |
| 85 | The idea is to teach a model Arabic as a "second language." The team expands its vocabulary and trains on mixed Arabic and English. | claim | direct | [arXiv (SDAIA / NCAI)](https://arxiv.org/abs/2407.15390) |
| 86 | That way, the model doesn't forget its English. | claim | direct | [arXiv (SDAIA / NCAI)](https://arxiv.org/abs/2407.15390) |
| 87 | ALLaM-7B was first trained on 4 trillion English tokens. | claim | direct | [Hugging Face (SDAIA NCAI, hosted under humain-ai)](https://huggingface.co/humain-ai/ALLaM-7B-Instruct-preview) |
| 88 | Then came 1.2 trillion mixed Arabic and English tokens. | claim | direct | [Hugging Face (SDAIA NCAI, hosted under humain-ai)](https://huggingface.co/humain-ai/ALLaM-7B-Instruct-preview) |
| 89 | Distribution came through partners. | analysis | partial | [Saudi Press Agency (SPA)](https://www.spa.gov.sa/en/N2276379) |
| 90 | According to the Saudi Press Agency, ALLaM went first to IBM's watsonx, then Microsoft Azure, then Qualcomm AI Cloud. | claim | direct | [Saudi Press Agency (SPA)](https://www.spa.gov.sa/en/N2276379) |
| 91 | In March 2025, SDAIA listed the 7B model on Hugging Face, the public hub where AI models are shared. | claim | direct | [Saudi Press Agency (SPA)](https://www.spa.gov.sa/en/N2276379) |
| 92 | Then, in August 2025, HUMAIN, a Public Investment Fund company, launched HUMAIN Chat. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 93 | It runs on ALLaM 34B, which builds on SDAIA's earlier models. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 94 | HUMAIN says the model was refined with input from over 600 domain experts and 250 evaluators. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 95 | HUMAIN Chat offers Arabic speech input across dialects, and switching between Arabic and English. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 96 | Crucially, HUMAIN says it is hosted end-to-end on its own infrastructure inside the Kingdom. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 97 | It also complies with the PDPL, Saudi Arabia's personal data protection law. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 98 | One difference from the 7B: HUMAIN Chat is a service. | analysis | partial | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 99 | Our research found no open release of the 34B model's weights, the trained files anyone can download and run. | claim | none |  |
| 100 | Now to Doha, and then a few important players beyond the three hubs. | transition | none |  |
| 101 | Fanar is built by QCRI, Qatar's national computing research institute, at Hamad Bin Khalifa University. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 102 | It is sponsored by Qatar's Ministry of Communications and IT. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 103 | The first version, described in January 2025, had two models. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 104 | Fanar Star was trained from scratch. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 105 | Fanar Prime was continually trained from Google's Gemma-2, meaning it started from an existing model and kept learning. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 106 | Fanar is a platform, not just a model. | analysis | partial | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 107 | It includes an Islamic retrieval system for religious questions. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 108 | Retrieval means the system looks things up in trusted sources before answering. | claim | none |  |
| 109 | A second retrieval system, "Recency RAG", handles current events. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 110 | Fanar 2.0 came in March 2026. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 111 | Fanar's core model builds on Google's open Gemma 3. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397); [Hugging Face (QCRI, HBKU)](https://huggingface.co/QCRI/Fanar-2-27B-Instruct) |
| 112 | QCRI says it used eight times fewer pretraining tokens than Fanar 1.0. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 113 | Yet on ArabicMMLU, a knowledge test, the model card reports a rise from 67.35 to 74.67 percent. | claim | direct | [Hugging Face (QCRI, HBKU)](https://huggingface.co/QCRI/Fanar-2-27B-Instruct) |
| 114 | Quality over quantity. | analysis | partial | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397); [Hugging Face (QCRI, HBKU)](https://huggingface.co/QCRI/Fanar-2-27B-Instruct) |
| 115 | The stack adds Fanar-Diwan for classical poetry, Fanar-Sadiq for Islamic content, and FanarGuard, a safety filter. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 116 | Back in Abu Dhabi, MBZUAI and G42 built K2 Think, a reasoning model released in September 2025. | claim | none · figure 42 not in the cited item(s) | [arXiv (MBZUAI)](https://arxiv.org/abs/2509.07604); [MBZUAI Institute of Foundation Models](https://mbzuai.ac.ae/news-events/news/k2-think-v2-fully-sovereign-reasoning-model) |
| 117 | It's not Arabic-specific. | claim | direct | [arXiv (MBZUAI)](https://arxiv.org/abs/2509.07604) |
| 118 | Its makers say it matches or beats much larger models. | claim | direct | [arXiv (MBZUAI)](https://arxiv.org/abs/2509.07604) |
| 119 | Its successor, K2 Think V2, is described by MBZUAI as fully open, from pre-training through post-training. | claim | direct | [MBZUAI Institute of Foundation Models](https://mbzuai.ac.ae/news-events/news/k2-think-v2-fully-sovereign-reasoning-model) |
| 120 | Global companies compete too. | transition | none |  |
| 121 | In February 2025, Cohere released Command R7B Arabic, with about 8 billion parameters. | claim | direct | [Cohere](https://cohere.com/blog/command-r7b-arabic); [Hugging Face (Cohere Labs)](https://huggingface.co/CohereLabs/c4ai-command-r7b-arabic-02-2025) |
| 122 | Cohere says it can run on a MacBook, or even on ordinary processors. | claim | direct | [Cohere](https://cohere.com/blog/command-r7b-arabic) |
| 123 | But its licence, CC-BY-NC, does not allow commercial use. | claim | direct | [Hugging Face (Cohere Labs)](https://huggingface.co/CohereLabs/c4ai-command-r7b-arabic-02-2025) |
| 124 | And for Egypt, MBZUAI Paris built Nile-Chat, which reads and writes both Arabic script and Arabizi. | claim | direct | [arXiv (MBZUAI Paris)](https://arxiv.org/abs/2507.04569) |
| 125 | Finally, the question everyone asks: which model is best? | transition | none |  |
| 126 | Leaderboards rank models on shared tests. | claim | partial | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 127 | The Open Arabic LLM Leaderboard launched in May 2024. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 128 | It came from 2A2I, an Arabic AI research initiative, together with TII and Hugging Face. | claim | partial | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 129 | Within seven months, its organisers say, it received more than 700 models. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 130 | In September 2024, SDAIA and the King Salman Global Academy for Arabic Language launched the BALSAM Index. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 131 | And in December 2024, Inception and MBZUAI launched AraGen, the first leaderboard for generative tasks in Arabic. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 132 | Here's the catch. | transition | none |  |
| 133 | Almost everyone claims the top spot. | analysis | partial | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model); [arXiv (MBZUAI, Cerebras, Inception)](https://arxiv.org/abs/2608.13580); [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 134 | In January 2026, TII said Falcon-H1 Arabic leads its leaderboard across sizes. | claim | partial | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model) |
| 135 | The Jais 2 report claims leading results among the models it evaluated. | claim | direct | [arXiv (MBZUAI, Cerebras, Inception)](https://arxiv.org/abs/2608.13580) |
| 136 | In October 2026, MBZUAI's large-model lab said Jais 3 leads open models on Arabic agentic tasks. | claim | none | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 137 | Those are tasks where the AI carries out steps on its own. | claim | none |  |
| 138 | Most of these scores are published by the makers themselves, against rivals they chose. | analysis | partial | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat); [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model); [Institute of Foundation Models (ifm.ai)](https://ifm.ai/jais/) |
| 139 | This next part is my view, not a finding from the sources. | transition | none |  |
| 140 | After twenty-five years selling enterprise software in this region, I've learned that headline rankings rarely decide anything. | claim | none |  |
| 141 | What decides is fit. | analysis | none |  |
| 142 | Does the model understand the dialect your customers actually speak? | transition | none |  |
| 143 | Does the licence allow what you plan to do? | transition | none |  |
| 144 | And where does your data live? | transition | none |  |
| 145 | A model that tops a leaderboard but can't legally sit inside your country, or your contract, isn't the best model for you. | analysis | none |  |
| 146 | I'd rather see a team run five candidates on its own documents than read five press releases. | analysis | none |  |
| 147 | And here's the question I'll be watching. | transition | none |  |
| 148 | When a Gulf government or bank chooses its AI, what will it pick? | transition | none |  |
| 149 | A home-grown Arabic model, or a global model that has simply got better at Arabic? | transition | none |  |
| 150 | I don't think the answer will be the same everywhere. | analysis | none |  |
| 151 | Three things to remember. | transition | none |  |
| 152 | First, Arabic is hard for AI. | analysis | partial | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397); [arXiv](https://arxiv.org/abs/2512.18399) |
| 153 | There's little data, many dialects, mixed languages, and tokenisers built for English. | claim | partial | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397); [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text); [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai); [arXiv](https://arxiv.org/abs/2512.18399) |
| 154 | Second, the region's builders take different roads. | analysis | none |  |
| 155 | Jais has gone big, with models trained from scratch and later built on open foundations. | analysis | partial | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat); [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 156 | Falcon focuses on efficient models and dialects. | analysis | partial | [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic); [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 157 | ALLaM teaches Arabic as a second language, and powers HUMAIN Chat. | claim | direct | [arXiv (SDAIA / NCAI)](https://arxiv.org/abs/2407.15390); [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 158 | Fanar adapts strong open models and wraps them in a platform. | analysis | partial | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944); [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 159 | Third, read every "number one" claim carefully. | transition | none |  |
| 160 | Check who measured it, when, and against whom. | transition | none |  |
| 161 | And check the licence. | transition | none |  |
| 162 | Next time in the series, we map the who's who of AI in the UAE. | transition | none |  |
| 163 | If this helped, please Hype the video, then subscribe and tell me in the comments which model you'd test first. | greeting | none |  |
