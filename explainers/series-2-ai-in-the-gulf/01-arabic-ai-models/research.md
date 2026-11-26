# Episode 01: The Arabic AI models (research)

Research date: 2026-11-26. Source ids refer to `items.json` (prefix `01-arabic-ai-models-`). Every fact below comes from a page fetched during this research.

## Facts

### Why Arabic is hard
1. Arabic makes up only about 0.5% of web data despite 400 million native speakers, according to the Fanar 2.0 paper from Qatar's QCRI [01-arabic-ai-models-18].
2. MBZUAI's Preslav Nakov says Arabic "has long been underserved in AI development due to limited high-quality data for training large language models" [01-arabic-ai-models-03].
3. TII explains that Modern Standard Arabic (MSA) is used mainly in formal writing, education and news, while everyday conversation happens in distinct regional dialects that are underrepresented in AI training data [01-arabic-ai-models-12].
4. TII says a model trained mainly on MSA "may understand every word of an Emirati sentence while still missing its intended meaning" [01-arabic-ai-models-12].
5. General-purpose tokenisers, trained mostly on English and Latin-script languages, perform poorly on morphologically rich languages such as Arabic, producing "inflated token sequences and reduced compression efficiency", according to the AraToken paper [01-arabic-ai-models-26].
6. Arabic spelling variation (Alif variants, diacritics, Arabic-Indic numerals) affects tokenisation. Normalising it cut fertility by 18%, from 1.35 to 1.199 tokens per word, in one study [01-arabic-ai-models-26].
7. A 2026 EACL study found LLMs cope with the light diacritics in everyday text, but fully diacritised text "leads to substantially increased token fragmentation and degraded performance" [01-arabic-ai-models-27].
8. The organisers of the Open Arabic LLM Leaderboard say many early Arabic benchmarks "were direct translations from English", which missed Arabic's morphology and real-world use, so version 2 removed machine-translated tasks [01-arabic-ai-models-22].
9. People mix languages mid-sentence. MBZUAI's Haonan Li says Arabic speakers slip "into English or French mid-sentence and back again", and Jais 3 was built for that [01-arabic-ai-models-07].
10. Egyptian Arabic is often typed in Latin letters ("Arabizi"). MBZUAI Paris built Nile-Chat (4B, 3x4B-A6B and 12B) to handle both scripts. Its 12B model shows a 14.4% gain over Qwen2.5-14B-Instruct on Latin-script benchmarks [01-arabic-ai-models-25].

### Jais (UAE: Inception/G42, MBZUAI, Cerebras)
11. Jais was released open-source on 30 August 2023 by Inception (G42) with MBZUAI and Cerebras: 13 billion parameters, trained on 116 billion Arabic tokens and 279 billion English tokens [01-arabic-ai-models-01].
12. Jais is named after the UAE's highest peak and was trained on Condor Galaxy 1, a supercomputer built by G42 and Cerebras [01-arabic-ai-models-01].
13. Early users named at launch included the UAE Ministry of Foreign Affairs, ADNOC, Etihad Airways, First Abu Dhabi Bank and e& [01-arabic-ai-models-01].
14. Jais 30B followed on 9 November 2023 and was trained on 126 billion Arabic, 251 billion English and 50 billion code tokens. The Jais 13B production training run took 21 days [01-arabic-ai-models-02].
15. In the second half of 2024 Inception released a family of 20 open Jais models, from 590 million to 70 billion parameters, trained on up to 1.6 trillion tokens, Middle East AI News reports [01-arabic-ai-models-04].
16. Jais 2 was released on 9 December 2025 in 8B and 70B chat versions, trained from scratch on what the makers call "the richest Arabic-first dataset to date" [01-arabic-ai-models-03] [01-arabic-ai-models-04] [01-arabic-ai-models-08].
17. Jais 2 70B uses a custom Arabic-centric vocabulary of 150,272 tokens, has an 8,192-token context, and is licensed Apache 2.0 [01-arabic-ai-models-05].
18. The Jais 2 report calls the 70B model, to the authors' knowledge, the largest open Arabic-centric LLM trained from scratch. It runs in the Jais chat app at up to 2,000 tokens per second on Cerebras hardware [01-arabic-ai-models-06].
19. On the AraGen (3C3H) benchmark, the Jais 2 model card reports 70.71% for Jais-2-70B, versus 62.58% for Qwen2.5-72B and 61.29% for Llama-3.3-70B. On English instruction-following it trails both [01-arabic-ai-models-05].
20. Jais 3 (October 2026) is six open models from 900 million to 375 billion parameters, plus Jais Speech, built on MBZUAI's fully open K2 Horizon fleet (released September 2026) [01-arabic-ai-models-07] [01-arabic-ai-models-08].
21. Every Jais 3 model has a 512,000-token context window, which MBZUAI calls the longest of any Arabic-native model [01-arabic-ai-models-07].
22. Adapting K2 Horizon to Arabic lifted the 7B model's average Arabic score from 56.4 to 79.6 on IFM's and Inception42's own evaluation of 24 benchmarks [01-arabic-ai-models-07].
23. Jais Speech transcribes MSA and dialects spoken across 19 Arab countries, and can identify which dialect is being spoken [01-arabic-ai-models-07].

### Falcon (UAE: Technology Innovation Institute, Abu Dhabi)
24. Falcon Arabic, launched on 21 May 2025, was the first Arabic model in TII's Falcon series. It is built on Falcon 3-7B and trained on native, non-translated Arabic data covering MSA and dialects [01-arabic-ai-models-09].
25. TII says Falcon Arabic matches models up to 10 times its size on the Open Arabic LLM Leaderboard [01-arabic-ai-models-09].
26. TII says the Falcon ecosystem has been downloaded over 55 million times. Falcon models use the TII Falcon License, which is based on Apache 2.0 [01-arabic-ai-models-09].
27. Falcon-H1 Arabic was announced on 5 January 2026 in 3B, 7B and 34B sizes on a hybrid Mamba-Transformer architecture, with up to 256K tokens of context [01-arabic-ai-models-10].
28. TII says 256K tokens is roughly 100,000 words. Falcon-H1-Arabic covers Gulf, Levantine, North African and Egyptian dialects and supports 18 languages [01-arabic-ai-models-11].
29. TII's reported OALL averages: Falcon-H1 Arabic 3B 61.87%, 7B 71.47%, 34B 75.36%. TII says the 34B beats Qwen2.5 72B and Llama-3.3 70B, and the 7B beats Fanar-1-9B and ALLaM 7B [01-arabic-ai-models-10].
30. On 6 October 2026 TII launched Falcon-Emirati, a 7B model for the Emirati dialect built on Falcon-H1-Arabic. It scored 84.83% on the Emirati benchmark Alyah [01-arabic-ai-models-12].
31. TII launched Falcon-Emirati alongside Falcon-ASR, a 1.6B speech-to-text model, and Falcon-OCR-Arabic, which reads Arabic text from images and documents [01-arabic-ai-models-12].

### ALLaM and HUMAIN Chat (Saudi Arabia: SDAIA, then HUMAIN)
32. ALLaM is developed by the National Center for AI (NCAI) at the Saudi Data and AI Authority (SDAIA). Its paper was posted in July 2024 [01-arabic-ai-models-13] [01-arabic-ai-models-14].
33. ALLaM's approach teaches Arabic as a "second language" to the model: it expands the vocabulary and trains on mixed Arabic and English, so the model does not forget its English [01-arabic-ai-models-13].
34. ALLaM-7B was trained from scratch on 4 trillion English tokens, then 1.2 trillion mixed Arabic/English tokens (5.2 trillion in total), with a 4,096-token context [01-arabic-ai-models-14].
35. ALLaM was offered on IBM watsonx, then Microsoft Azure, then Qualcomm AI Cloud, before SDAIA listed the 7B model on Hugging Face on 6 March 2025 [01-arabic-ai-models-15].
36. HUMAIN, a Public Investment Fund company, launched HUMAIN Chat on 25 August 2025. It is powered by ALLaM 34B, which builds on SDAIA's earlier ALLaM models [01-arabic-ai-models-16].
37. HUMAIN says ALLaM 34B was refined with input from over 600 domain experts and 250 evaluators, by a team of over 120 AI specialists including 35 PhDs [01-arabic-ai-models-16].
38. HUMAIN Chat offers Arabic speech input across dialects and Arabic-English switching, and is hosted end-to-end on HUMAIN infrastructure in Saudi Arabia under the Saudi data-protection law (PDPL) [01-arabic-ai-models-16].

### Fanar (Qatar: QCRI, Hamad Bin Khalifa University)
39. Fanar 1 (paper January 2025) had two models. Fanar Star (7B) was trained from scratch on nearly 1 trillion tokens. Fanar Prime (9B) was continually trained from Google's Gemma-2 9B [01-arabic-ai-models-17].
40. Fanar includes an Islamic retrieval system for religious questions and a "Recency RAG" for current events. It is sponsored by Qatar's Ministry of Communications and IT [01-arabic-ai-models-17].
41. Fanar 2.0 (March 2026) centres on Fanar-27B, continually pretrained from Gemma-3-27B. QCRI did the work on 256 NVIDIA H100 GPUs, using 8x fewer pretraining tokens than Fanar 1.0 [01-arabic-ai-models-18].
42. Fanar-2-27B-Instruct is licensed Apache 2.0 with a 32,768-token context. Its ArabicMMLU score rose from 67.35% (Fanar 1, 9B) to 74.67% [01-arabic-ai-models-19].
43. The Fanar 2.0 stack adds Fanar-Diwan for classical poetry, Fanar-Sadiq for Islamic content and FanarGuard, a 4B safety filter [01-arabic-ai-models-18].

### K2 Think (UAE: MBZUAI and G42; reasoning, not Arabic-specific)
44. K2 Think, a 32B reasoning model built on Qwen2.5, was released in September 2025. Its makers say it matches or beats much larger models such as GPT-OSS 120B and DeepSeek v3.1 [01-arabic-ai-models-20].
45. K2 Think V2 is 70 billion parameters, built on K2 V2 Instruct. MBZUAI says it is fully open "from pre-training through post-training, using only IFM-curated data" [01-arabic-ai-models-21].

### Others and benchmarks
46. Cohere released Command R7B Arabic on 27 February 2025: about 8 billion parameters and a 128K context, able to run on a MacBook or even CPUs [01-arabic-ai-models-23] [01-arabic-ai-models-24].
47. Command R7B Arabic's weights are licensed CC-BY-NC, which does not allow commercial use [01-arabic-ai-models-24].
48. The Open Arabic LLM Leaderboard launched in May 2024 (2A2I, TII, Hugging Face) and received more than 700 models from over 180 organisations in under 7 months [01-arabic-ai-models-22].
49. In September 2024 SDAIA and the King Salman Global Academy for Arabic Language launched the BALSAM Index: about 1,400 datasets, 50,000 questions and 67 tasks [01-arabic-ai-models-22].
50. Inception and MBZUAI launched AraGen on 5 December 2024, the first leaderboard for generative tasks in Arabic [01-arabic-ai-models-22].

## Conflicts and dates
- **Jais 2 size label:** the official release says 70 billion parameters [03]; Hugging Face's automatic metadata labels the file "72B parameters" [05]. Use "70 billion" on air.
- **Jais 2 paper date:** the arXiv record says submitted 7 July 2026, but its number (2608.13580) would normally mean August 2026 [06]. The model itself launched on 9 December 2025 [04, 08].
- **Jais 3 date:** the MBZUAI release page carries no date. The IFM roadmap says "Oct 2026" [08], and a search snippet (not fetched) said 15 October 2026. Say "October 2026".
- **Fanar 2.0 training tokens:** the paper says 120 billion tokens [18]; the model card says about 166 billion [19]. The card's own recipe breakdown (50B + 70B + 30B = 150B, plus 8B of annealing after each recipe) matches neither figure exactly. Neither source explains the gap. Prefer "over 100 billion" or quote one figure with its source.
- **Arabic speaker count:** most sources say "400 million" or "more than 400 million" [01, 07, 16, 18]. Arab News's write-up of the same HUMAIN launch said 350 million (not used as a source). Use "more than 400 million, as the model makers put it".
- **Falcon Arabic timing:** ATRC's release of 5 January 2026 calls Falcon Arabic "released earlier this year", but Falcon Arabic launched on 21 May 2025 [09, 10]. The release was likely drafted in late 2025.
- **"Number one" claims change often:** TII says Falcon-H1 Arabic leads OALL across sizes (January 2026) [10]; Jais 2 claims leading OALL2/AraGen results among the models it evaluated [06]; IFM says Jais 3 leads open models on Arabic agentic tasks (October 2026) [07]; SILMA's own card says it was top-ranked "until February 2025" (fetched; not used as a source). Each maker uses its own selection of rivals and benchmarks. On air, attribute every "best" claim and date it.
- **Benchmarks are self-reported:** the OALL scores for Falcon-H1 Arabic, the AraGen scores for Jais 2, the Jais 3 table and Cohere's Arabic average are all published by the model makers themselves.
- **Licences differ:** Jais 2 is Apache 2.0 [05]; Falcon uses the TII Falcon License, based on Apache 2.0 [09]; Fanar 2 is Apache 2.0 [19]; Command R7B Arabic is CC-BY-NC [24]; ALLaM 7B's licence was not retrieved [14]; ALLaM 34B and HUMAIN Chat are not open weights. The ALLaM 34B evaluation paper calls HUMAIN Chat "a closed conversational web service" (fetched, not used as a source).
- **Changes often:** leaderboard positions, model versions (Jais, Falcon and Fanar each released at least two generations in 2025-2026), HUMAIN Chat country availability, and download counts.

## Unverified
- ALLaM 7B licence terms (the model card points to a LICENSE file that returned 404).
- Whether ALLaM 34B weights were ever released openly; whether HUMAIN Chat has rolled out beyond Saudi Arabia.
- Any HUMAIN model announced after ALLaM 34B, such as a successor or new HUMAIN LLM in 2026. Not searched in depth.
- Fanar 1's public launch date as a consumer product (a Qatar MCIT page from May 2024 was found in search but not fetched).
- K2 Think V2 release date (the page gives no date; it came after K2-V2 in December 2025).
- AceGPT: the arXiv paper (fetched; Sep 2023, NAACL) says it was localised to Arabic with RLAIF tuned to local culture, but the builders' institutions were not confirmed, so it is excluded from the facts.
- SILMA 9B (built on Google Gemma, open weights under the Gemma licence, per its own card): the company's location and background were not sourced.
- Noon (an Arabic model of about 2023): not searched; omitted.
- Current live OALL v2 rankings (the leaderboard Space was not fetched). Do not state a current number one on air.
- Size or tokenisation figures comparing Arabic with English for GPT-style tokenisers: the "tokenization premium" paper fetched had no Arabic figure in its abstract.

## Proposed outline
**Working title:** Arabic AI Models Explained: Jais, Falcon, ALLaM, Fanar (54 characters)

**First 15 seconds promise:** "More than 400 million people speak Arabic, but Arabic is only about half a percent of the web. In twelve minutes, here is who is building AI that actually speaks Arabic, and how they are doing it."

**Chapter 1: Why Arabic breaks AI (about 2.5 minutes)**
Data scarcity (0.5% of web data), MSA versus dialects, code-switching, Arabizi, tokenisation and diacritics, and translated benchmarks. Facts 1-10.

**Chapter 2: The UAE's two tracks, Jais and Falcon (about 3.5 minutes)**
Jais from 13B (2023) through 30B, the 20-model family, Jais 2 70B, and the Jais 3 fleet up to 375B. Falcon Arabic (May 2025), then Falcon-H1 Arabic's hybrid architecture and 256K context, then Falcon-Emirati. Note the different philosophies: Jais builds big from scratch; Falcon builds small and efficient. Facts 11-31.

**Chapter 3: Saudi Arabia's ALLaM and HUMAIN Chat (about 2 minutes)**
From the SDAIA research model to a cloud-partner rollout (IBM, Microsoft, Qualcomm), the Hugging Face listing, then ALLaM 34B powering HUMAIN Chat, hosted in the Kingdom. Facts 32-38.

**Chapter 4: Qatar's Fanar and the rest of the field (about 2 minutes)**
Fanar's platform approach: Islamic retrieval, poetry, safety filter, building on Gemma, "quality over quantity". Then K2 Think (reasoning, not Arabic-specific), Cohere's Command R7B Arabic, and Nile-Chat for Egyptian Arabic. Facts 39-47, 10.

**Chapter 5: Who is "best"? How to read the leaderboards (about 1.5 minutes)**
OALL, BALSAM and AraGen; why everyone claims number one; open versus closed and the licence table. Facts 48-50, 19, 29, plus the Conflicts section.

**Analogy for the hardest idea (tokenisation):** A tokeniser is like a cashier who only stocks big banknotes in one currency. Pay in English and the bill gets done in a few big notes. Pay in Arabic and the cashier has to count it out in small coins: more pieces, more time, more cost, and less fits in the till (the context window). An Arabic-centric vocabulary, like Jais 2's 150,272-token vocabulary, stocks the right denominations. Present this as an illustration, not a measured claim.

**On-screen visuals:**
- Map of the Gulf with three pins: Abu Dhabi (Jais, Falcon, K2), Riyadh (ALLaM/HUMAIN), Doha (Fanar), with a small annotation for Cairo/Egyptian (Nile-Chat).
- Timeline strip from 2023 to 2026: Jais 13B (Aug 2023), Jais 30B (Nov 2023), OALL (May 2024), ALLaM paper (Jul 2024), BALSAM (Sep 2024), Fanar paper (Jan 2025), Command R7B Arabic (Feb 2025), ALLaM on Hugging Face (Mar 2025), Falcon Arabic (May 2025), HUMAIN Chat (Aug 2025), K2 Think (Sep 2025), Jais 2 (Dec 2025), Falcon-H1 Arabic (Jan 2026), Fanar 2.0 (Mar 2026), Falcon-Emirati (Oct 2026), Jais 3 (Oct 2026).
- Comparison table with columns builder / country / latest size / built from scratch or adapted / open weights and licence / context window.
- "Half a percent" graphic: a pie chart of web data with an Arabic sliver of about 0.5% next to a 400-million-speaker figure.
- Tokenisation animation: one Arabic word splitting into many sub-word pieces, with diacritics making it split further.
- Dialect map with MSA in the centre and Gulf, Levantine, Egyptian and North African dialects around it, plus an Arabizi example typed in Latin letters.

**Closing "what to watch next":** "When a Gulf government or bank picks its AI, will it choose a home-grown Arabic model, or a global model that has simply got better at Arabic?"

## Shorts
1. **"Half a percent."** Fact: Arabic is about 0.5% of web data despite 400 million native speakers [18]. Takeaway: that is why the Gulf is building its own models instead of waiting for Silicon Valley to catch up.
2. **"The model that speaks Emirati."** Fact: TII's Falcon-Emirati is a 7B model built for the Emirati dialect, and it scored 84.83% on the Emirati benchmark Alyah [12]. TII says an MSA-trained model "may understand every word of an Emirati sentence while still missing its intended meaning". Takeaway: the next frontier is dialects, not just "Arabic".
3. **"Why Arabic costs more to process."** Fact: English-centric tokenisers chop Arabic into more pieces, and normalising Arabic spelling alone cut tokens per word by 18% in one study [26]. Takeaway: more tokens means more cost and less room in the context window, which is why Jais 2 built its own Arabic vocabulary [05].
