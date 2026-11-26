# Source map

142 spoken sentences · 112 claims · 86 sourced · 12 partial · **14 unsourced claims**

## Partial support — check the wording

- (19) Many Egyptians also type Arabic in Latin letters, a style known as Arabizi.
- (41) It worked with MBZUAI and Cerebras, which co-built the supercomputer Jais trained on.
- (58) That makes it open weights: anyone can download the model, and commercial use is allowed.
- (81) Alongside it came speech-to-text and a tool that reads Arabic text from images.
- (87) Its research paper appeared in July 2024.
- (93) The Saudi Press Agency says it went first to IBM's watsonx, then Microsoft Azure, then Qualcomm's AI Cloud.
- (106) Public sources show the 34-billion model offered as a service, not as open weights.
- (109) The first version, described in January 2025, had two models.
- (113) Fanar also uses retrieval, often called RAG.
- (116) Fanar 2.0 was published in March 2026.
- (139) It was the first leaderboard for generative Arabic tasks, where the model writes its own answers.
- (142) TII claimed the lead for Falcon-H1 Arabic in January

## ⚠️ Unsourced claims — fix before recording

- (5) A large language model, or LLM, is the kind of AI behind chatbots.
- (6) It learns language by reading enormous amounts of text.
- (18) MBZUAI's Haonan Li says Arabic speakers slip "into English or French mid-sentence and back again." That habit is called code-switching.
- (21) Models do not read words.
- (22) They read tokens, which are small chunks of text.
- (23) A tokeniser is the tool that cuts text into those chunks.
- (30) In AI, that till is the context window: how much text a model can hold at once.
- (37) A benchmark is a standard exam for AI models.
- (43) Parameters are the internal settings a model adjusts while learning.
- (44) More parameters usually means a bigger, more capable model.
- (67) Jais Speech covers dialects from 19 Arab countries, and can tell which one is being spoken.
- (95) That is a public website where AI models are shared for download.
- (112) Continual training means taking an existing model and teaching it more.
- (114) The system looks things up in trusted sources before answering.

| # | sentence | kind | support | sources |
|---|---|---|---|---|
| 1 | Arabic is spoken by hundreds of millions of people, yet it makes up only about half a percent of web data. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 2 | By the end, you will know who builds AI that truly speaks Arabic, how they do it, and how to judge their claims. | transition | none |  |
| 3 | First, why Arabic is so hard for AI. | transition | none |  |
| 4 | Start with the raw material. | transition | none |  |
| 5 | A large language model, or LLM, is the kind of AI behind chatbots. | claim | none |  |
| 6 | It learns language by reading enormous amounts of text. | claim | none |  |
| 7 | The Fanar 2.0 paper from QCRI, Qatar's computing research institute, is the source for that half-percent figure. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 8 | And it is the root of everything else in this story. | analysis | partial | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 9 | I'm Wissam, and this is AI This Week, AI Explained. | greeting | none |  |
| 10 | MBZUAI's Preslav Nakov puts it plainly. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/inception-cerebras-mbzuai-release-jais-2-the-next-generation-the-worlds-leading) |
| 11 | He says Arabic "has long been underserved" because of limited high-quality training data. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/inception-cerebras-mbzuai-release-jais-2-the-next-generation-the-worlds-leading) |
| 12 | The Fanar paper sets that sliver of data against 400 million native speakers. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 13 | The second problem is that Arabic is really many Arabics. | analysis | partial | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 14 | Modern Standard Arabic, or MSA, is the formal language of writing, education and news. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 15 | Daily conversation happens in regional dialects, and those dialects are thin in AI training data. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 16 | Abu Dhabi's Technology Innovation Institute, TII, gives a sharp example. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text); [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic) |
| 17 | A model trained mainly on MSA "may understand every word of an Emirati sentence while still missing its intended meaning."  Third, people mix languages. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 18 | MBZUAI's Haonan Li says Arabic speakers slip "into English or French mid-sentence and back again." That habit is called code-switching. | claim | none |  |
| 19 | Many Egyptians also type Arabic in Latin letters, a style known as Arabizi. | claim | partial | [arXiv (MBZUAI Paris)](https://arxiv.org/abs/2507.04569) |
| 20 | Fourth, and hardest to picture, is tokenisation. | transition | none |  |
| 21 | Models do not read words. | claim | none |  |
| 22 | They read tokens, which are small chunks of text. | claim | none |  |
| 23 | A tokeniser is the tool that cuts text into those chunks. | claim | none |  |
| 24 | Here is an illustration, not a measurement. | transition | none |  |
| 25 | Picture a cashier who only stocks big banknotes in one currency. | analysis | none |  |
| 26 | Pay in English, and the bill is settled in a few big notes. | analysis | none |  |
| 27 | Pay in Arabic, and the cashier counts it out in small coins. | analysis | none |  |
| 28 | That means more pieces, more time and more cost. | analysis | partial | [arXiv](https://arxiv.org/abs/2512.18399) |
| 29 | Less also fits in the till. | analysis | none |  |
| 30 | In AI, that till is the context window: how much text a model can hold at once. | claim | none |  |
| 31 | The research matches the picture. | analysis | partial | [arXiv](https://arxiv.org/abs/2512.18399) |
| 32 | The AraToken paper says general-purpose tokenisers, trained mostly on English, produce "inflated token sequences" for Arabic. | claim | direct | [arXiv](https://arxiv.org/abs/2512.18399) |
| 33 | Arabic spelling varies too, with different forms of Alif, optional vowel marks called diacritics, and Arabic-Indic numerals. | claim | direct | [arXiv](https://arxiv.org/abs/2512.18399) |
| 34 | In one study, tidying up that variation cut tokens per word by 18%. | claim | direct | [arXiv](https://arxiv.org/abs/2512.18399) |
| 35 | A study at EACL 2026, a language research conference, found models cope with the light diacritics of everyday text. | claim | direct | [ACL Anthology (Findings of EACL 2026; Inoue, Alhafni, Habash, Baldwin)](https://aclanthology.org/2026.findings-eacl.22/) |
| 36 | Fully diacritised text, though, "leads to substantially increased token fragmentation and degraded performance."  Finally, the tests themselves were weak. | claim | direct | [ACL Anthology (Findings of EACL 2026; Inoue, Alhafni, Habash, Baldwin)](https://aclanthology.org/2026.findings-eacl.22/) |
| 37 | A benchmark is a standard exam for AI models. | claim | none |  |
| 38 | The team behind the Open Arabic LLM Leaderboard says many early Arabic benchmarks "were direct translations from English."  Now to Abu Dhabi, where two teams have taken different roads. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 39 | The first road is Jais, named after the UAE's highest peak. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 40 | Inception, a G42 company, released it open-source on 30 August 2023. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 41 | It worked with MBZUAI and Cerebras, which co-built the supercomputer Jais trained on. | claim | partial | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 42 | It had 13 billion parameters. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 43 | Parameters are the internal settings a model adjusts while learning. | claim | none |  |
| 44 | More parameters usually means a bigger, more capable model. | claim | none |  |
| 45 | It trained on 116 billion Arabic tokens and 279 billion English tokens. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 46 | Early users named at launch included the UAE Ministry of Foreign Affairs, ADNOC, Etihad Airways, First Abu Dhabi Bank and e&. | claim | direct | [Cerebras Systems (press release)](https://www.cerebras.ai/press-release/meet-jais-the-worlds-most-advanced-arabic-large-language-model-open-sourced-by-g42s-inception) |
| 47 | Jais 30B followed in November 2023. | claim | direct | [Cerebras Systems (press release, PRNewswire/G42)](https://www.cerebras.ai/press-release/core42-sets-new-benchmark-for-arabic-large-language-models-with-the-release-of-jais-30b) |
| 48 | In the second half of 2024, Middle East AI News reports, Inception released 20 open Jais models. | claim | direct | [Middle East AI News](https://www.middleeastainews.com/p/inception-cerebras-and-mbzuai-release) |
| 49 | The smallest had 590 million parameters, the largest 70 billion. | claim | direct | [Middle East AI News](https://www.middleeastainews.com/p/inception-cerebras-and-mbzuai-release) |
| 50 | Jais 2 arrived in December 2025. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/inception-cerebras-mbzuai-release-jais-2-the-next-generation-the-worlds-leading); [Middle East AI News](https://www.middleeastainews.com/p/inception-cerebras-and-mbzuai-release) |
| 51 | The largest version has 70 billion parameters. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/inception-cerebras-mbzuai-release-jais-2-the-next-generation-the-worlds-leading); [arXiv (MBZUAI, Cerebras, Inception)](https://arxiv.org/abs/2608.13580) |
| 52 | A smaller 8-billion version came alongside. | claim | direct | [arXiv (MBZUAI, Cerebras, Inception)](https://arxiv.org/abs/2608.13580); [Middle East AI News](https://www.middleeastainews.com/p/inception-cerebras-and-mbzuai-release) |
| 53 | It was trained from scratch, meaning it did not start from someone else's model. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat); [arXiv (MBZUAI, Cerebras, Inception)](https://arxiv.org/abs/2608.13580) |
| 54 | Remember the cashier? | transition | none |  |
| 55 | Jais 2 stocks the right notes. | analysis | partial | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 56 | Its vocabulary of 150,272 tokens was built around Arabic. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 57 | It carries an Apache 2.0 licence. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 58 | That makes it open weights: anyone can download the model, and commercial use is allowed. | claim | partial | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat); [arXiv (MBZUAI, Cerebras, Inception)](https://arxiv.org/abs/2608.13580) |
| 59 | On the AraGen benchmark, the makers report 70.71% for their largest model. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 60 | A 72-billion Qwen model scored 62.58%. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 61 | A 70-billion Llama model scored 61.29%. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 62 | The same model card shows Jais 2 trailing both on English instruction-following. | claim | direct | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat) |
| 63 | Then, in October 2026, came Jais 3. | claim | direct | [Institute of Foundation Models (ifm.ai)](https://ifm.ai/jais/) |
| 64 | It is a fleet of six open models, plus Jais Speech. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 65 | The largest has 375 billion parameters. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 66 | Every model holds 512,000 tokens of context, which MBZUAI calls the longest of any Arabic-native model. | claim | direct | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 67 | Jais Speech covers dialects from 19 Arab countries, and can tell which one is being spoken. | claim | none | [MBZUAI](https://mbzuai.ac.ae/news-events/news/mbzuais-institute-foundation-models-inception42-launch-jais-3-arabic-native-ai) |
| 68 | The second road is Falcon, from TII. | transition | none |  |
| 69 | Falcon Arabic launched on 21 May 2025. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic) |
| 70 | It was built on Falcon 3, a 7-billion model, and trained on native Arabic data, not translations. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic) |
| 71 | TII says it matches models up to ten times its size. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic) |
| 72 | Falcon-H1 Arabic followed in January 2026. | claim | direct | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model) |
| 73 | It comes in three sizes, the largest at 34 billion parameters. | claim | direct | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model) |
| 74 | It uses a hybrid design that combines two ways of processing text, called Mamba and Transformer. | claim | direct | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model); [TII Falcon LLM site](https://falconllm.tii.ae/falcon-h1-arabic.html) |
| 75 | Its context reaches 256,000 tokens, which TII says is roughly 100,000 words. | claim | direct | [TII Falcon LLM site](https://falconllm.tii.ae/falcon-h1-arabic.html); [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model) |
| 76 | That is enough, TII says, for long legal documents or medical records in one go. | claim | direct | [TII Falcon LLM site](https://falconllm.tii.ae/falcon-h1-arabic.html) |
| 77 | As of January 2026, TII reported a leaderboard average for its largest model of 75.36%. | claim | direct | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model) |
| 78 | TII says that beat Qwen and Llama models of 70 billion parameters and more. | claim | direct | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model); [TII Falcon LLM site](https://falconllm.tii.ae/falcon-h1-arabic.html) |
| 79 | On 6 October 2026, TII launched Falcon-Emirati, a 7-billion model for the Emirati dialect. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 80 | It scored 84.83% on Alyah, an Emirati benchmark. | claim | direct | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 81 | Alongside it came speech-to-text and a tool that reads Arabic text from images. | claim | partial | [Technology Innovation Institute (TII)](https://www.tii.ae/news/tii-launches-falcon-emirati-alongside-new-arabic-ai-models-speech-and-visual-text) |
| 82 | So the contrast is clear. | analysis | none |  |
| 83 | Jais goes big and builds from scratch. | analysis | partial | [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat); [arXiv (MBZUAI, Cerebras, Inception)](https://arxiv.org/abs/2608.13580) |
| 84 | Falcon goes compact and efficient. | analysis | partial | [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic) |
| 85 | Next, Riyadh, and a model that moved from the lab to a national chatbot. | transition | none |  |
| 86 | ALLaM comes from the National Center for AI at the Saudi Data and AI Authority, SDAIA. | claim | direct | [arXiv (SDAIA / NCAI)](https://arxiv.org/abs/2407.15390); [Hugging Face (SDAIA NCAI, hosted under humain-ai)](https://huggingface.co/humain-ai/ALLaM-7B-Instruct-preview) |
| 87 | Its research paper appeared in July 2024. | claim | partial | [arXiv (SDAIA / NCAI)](https://arxiv.org/abs/2407.15390) |
| 88 | Its idea is to teach Arabic as a "second language." The team expands the model's vocabulary and trains on mixed Arabic and English. | claim | direct | [arXiv (SDAIA / NCAI)](https://arxiv.org/abs/2407.15390) |
| 89 | The goal is to steer the model towards Arabic without it forgetting English. | claim | direct | [arXiv (SDAIA / NCAI)](https://arxiv.org/abs/2407.15390) |
| 90 | The 7-billion model learned from 4 trillion English tokens first. | claim | direct | [Hugging Face (SDAIA NCAI, hosted under humain-ai)](https://huggingface.co/humain-ai/ALLaM-7B-Instruct-preview) |
| 91 | Then it learned from 1.2 trillion mixed Arabic and English tokens. | claim | direct | [Hugging Face (SDAIA NCAI, hosted under humain-ai)](https://huggingface.co/humain-ai/ALLaM-7B-Instruct-preview) |
| 92 | ALLaM reached people through partners. | analysis | partial | [Saudi Press Agency (SPA)](https://www.spa.gov.sa/en/N2276379) |
| 93 | The Saudi Press Agency says it went first to IBM's watsonx, then Microsoft Azure, then Qualcomm's AI Cloud. | claim | partial | [Saudi Press Agency (SPA)](https://www.spa.gov.sa/en/N2276379) |
| 94 | On 6 March 2025, SDAIA listed the 7-billion model on Hugging Face. | claim | direct | [Saudi Press Agency (SPA)](https://www.spa.gov.sa/en/N2276379) |
| 95 | That is a public website where AI models are shared for download. | claim | none |  |
| 96 | Then came the bigger step. | transition | none |  |
| 97 | On 25 August 2025, HUMAIN, a Public Investment Fund company, launched HUMAIN Chat. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 98 | It runs on ALLaM 34B. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 99 | HUMAIN says experts shaped that model: more than 600 domain experts and 250 evaluators. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 100 | A team of over 120 AI specialists, including 35 PhD holders, built it. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 101 | HUMAIN Chat accepts Arabic speech across dialects and handles Arabic-English switching. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 102 | It is hosted end-to-end on HUMAIN infrastructure inside Saudi Arabia. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 103 | It operates under the PDPL, the Kingdom's personal data protection law. | claim | direct | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 104 | One difference matters. | transition | none |  |
| 105 | The 7-billion ALLaM can be downloaded. | claim | direct | [Saudi Press Agency (SPA)](https://www.spa.gov.sa/en/N2276379); [Hugging Face (SDAIA NCAI, hosted under humain-ai)](https://huggingface.co/humain-ai/ALLaM-7B-Instruct-preview) |
| 106 | Public sources show the 34-billion model offered as a service, not as open weights. | claim | partial | [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 107 | Now Doha, and a different idea: a whole platform, not a single model. | transition | none |  |
| 108 | Fanar comes from QCRI at Hamad Bin Khalifa University, sponsored by Qatar's Ministry of Communications and IT. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 109 | The first version, described in January 2025, had two models. | claim | partial | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 110 | Fanar Star was trained from scratch. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 111 | Fanar Prime was continually trained from Google's Gemma-2. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 112 | Continual training means taking an existing model and teaching it more. | claim | none |  |
| 113 | Fanar also uses retrieval, often called RAG. | claim | partial | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 114 | The system looks things up in trusted sources before answering. | claim | none |  |
| 115 | Fanar has an Islamic retrieval system for religious questions, and a "Recency RAG" for current events. | claim | direct | [arXiv (QCRI, Hamad Bin Khalifa University)](https://arxiv.org/abs/2501.13944) |
| 116 | Fanar 2.0 was published in March 2026. | claim | partial | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 117 | Its core is a 27-billion model, built from Google's Gemma 3. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 118 | QCRI trained it on 256 NVIDIA H100 chips. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 119 | It used eight times fewer pretraining tokens than Fanar 1. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 120 | Fewer tokens still brought better scores. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 121 | The model card reports ArabicMMLU, a test built from school exam questions, rising from 67.35% to 74.67%. | claim | direct | [Hugging Face (QCRI, HBKU)](https://huggingface.co/QCRI/Fanar-2-27B-Instruct); [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 122 | The stack adds Fanar-Diwan for classical poetry, Fanar-Sadiq for Islamic content, and FanarGuard, a safety filter. | claim | direct | [Hugging Face Papers / arXiv (QCRI, HBKU)](https://huggingface.co/papers/2603.16397) |
| 123 | Beyond the big three, a few names round out the field. | transition | none |  |
| 124 | MBZUAI's K2 Think, released in September 2025, is a reasoning model, strongest in maths. | claim | direct | [MBZUAI Institute of Foundation Models](https://mbzuai.ac.ae/news-events/news/k2-think-v2-fully-sovereign-reasoning-model); [arXiv (MBZUAI)](https://arxiv.org/abs/2509.07604) |
| 125 | It is not Arabic-specific. | claim | direct | [arXiv (MBZUAI)](https://arxiv.org/abs/2509.07604) |
| 126 | Its second version has 70 billion parameters. | claim | direct | [MBZUAI Institute of Foundation Models](https://mbzuai.ac.ae/news-events/news/k2-think-v2-fully-sovereign-reasoning-model) |
| 127 | MBZUAI says it is fully open "from pre-training through post-training."  Cohere released Command R7B Arabic on 27 February 2025. | claim | direct | [MBZUAI Institute of Foundation Models](https://mbzuai.ac.ae/news-events/news/k2-think-v2-fully-sovereign-reasoning-model); [Cohere](https://cohere.com/blog/command-r7b-arabic) |
| 128 | It is small enough to run on a MacBook, or even on ordinary processors. | claim | direct | [Cohere](https://cohere.com/blog/command-r7b-arabic) |
| 129 | Its licence, CC-BY-NC, does not allow commercial use. | claim | direct | [Hugging Face (Cohere Labs)](https://huggingface.co/CohereLabs/c4ai-command-r7b-arabic-02-2025) |
| 130 | And for Egypt, MBZUAI Paris built Nile-Chat, which reads and writes both Arabic script and Arabizi. | claim | direct | [arXiv (MBZUAI Paris)](https://arxiv.org/abs/2507.04569) |
| 131 | On Latin-script tests, its makers report a 14.4% gain for the largest model over a similar-sized Qwen model. | claim | direct | [arXiv (MBZUAI Paris)](https://arxiv.org/abs/2507.04569) |
| 132 | Finally, the question everyone asks: which one is best? | transition | none |  |
| 133 | Arabic now has its own scoreboards. | analysis | partial | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 134 | The Open Arabic LLM Leaderboard launched in May 2024. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 135 | In under seven months, it received more than 700 models. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 136 | They came from over 180 organisations. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 137 | SDAIA and the King Salman Global Academy for Arabic Language launched the BALSAM Index in September 2024. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 138 | Inception and MBZUAI launched AraGen that December. | claim | direct | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 139 | It was the first leaderboard for generative Arabic tasks, where the model writes its own answers. | claim | partial | [Hugging Face blog (OALL team: 2A2I, TII, Hugging Face)](https://huggingface.co/blog/leaderboard-arabic-v2) |
| 140 | Here is the catch. | transition | none |  |
| 141 | Almost every maker claims the top spot. | analysis | partial | [Technology Innovation Institute (TII)](https://www.tii.ae/news/middle-easts-leading-ai-powerhouse-tii-launches-two-new-ai-models-falcon-arabic-first-arabic); [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model); [Hugging Face (Inception / MBZUAI / Cerebras)](https://huggingface.co/inception42/Jais-2-70B-Chat); [Saudi Press Agency (SPA), HUMAIN press release](https://www.spa.gov.sa/en/N2385004) |
| 142 | TII claimed the lead for Falcon-H1 Arabic in January | claim | partial | [Advanced Technology Research Council (ATRC)](https://atrc.gov.ae/news/abu-dhabis-tii-launches-falcon-h1-arabic-establishing-the-worlds-leading-arabic-ai-model) |
