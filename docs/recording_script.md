# Recording session — video digital twin and voice clone (v2, 2026-11-07)

One session gives you both: the camera footage trains a **video digital twin** (a real video avatar,
not the photo avatar used so far), and its audio (or a separate mic track) trains a better voice clone.
HeyGen's upload screens state the current minimum lengths and formats; follow them where they differ
from this sheet, and check on the upload screen whether creating the twin or clone costs credits on
the Creator plan before you start.

**Why a new session** (see `docs/LESSONS.md` §3): the photo avatar cannot make real Arabic mouth
shapes, so lip sync looked wrong in W45; and the first clone was trained on read-aloud text, so it
sounds read, and it never heard the tech names the show says every week (G42 came out «جي اتنان
وأربعون», Claude came out "cloud").

## Before you record
- **Room:** quiet, soft furnishings, no echo, no air-conditioning hum, phone on silent.
- **Light:** soft and even on the face, a window in front of you or two lights at 45°. No harsh
  shadows, no light behind you.
- **Camera:** landscape 16:9, 1080p or 4K, at eye level, locked off on a tripod. Frame from mid-chest
  up with a little headroom, **face in the centre of the frame**.
- **Background:** plain and calm (the edit puts you over our own visuals; a busy background fights them).
- **Mic:** a lavalier or USB condenser a hand's width from the mouth, recorded clean: no music, no noise
  reduction, no compression.
- **You:** the outfit you want on air every week (the blue shirt is the current brand look), solid
  colours, no fine stripes or logos; hair and glasses as they will look in every episode.

## Video twin footage
1. **Speak Jordanian Arabic, not English, for the footage.** The twin learns *your* mouth shapes for
   the sounds the show uses (ع، ح، ق، خ، ض and the Ammani vowels).
2. Look into the lens the whole time, as if talking to one viewer. Small, calm gestures; hands stay
   below the chin and never cover the face. No head turns, no leaning, no walking.
3. **Close your mouth and stay still for one to two seconds between paragraphs**: HeyGen learns your
   idle state from these moments.
4. Record at least the length HeyGen's screen asks for (plan on 2–3 minutes of usable talking), then
   record HeyGen's **consent statement** on camera exactly as its screen shows it.

## Voice clone audio
- 3–5 minutes of **clean, conversational** speech at broadcast pace — the way you'd explain the news
  to a friend, not the way a newsreader reads.
- Say the recurring names **once, the way you want them said every week** (list below). The clone
  copies what it hears.

## Reading passage (Jordanian colloquial)
Read it twice: once for the footage, once (or more, plus any other Arabic news copy) for the voice.

> أهلاً فيكم بـ«أسبوع الذكاء الاصطناعي»، معكم وسام. كل أسبوع بنختارلكم أهم إشي صار بعالم
> الذكاء الاصطناعي، وبنسأل سؤال واحد: طيب، شو يعني هاد إلنا هون بالمنطقة؟

> شركة ناشئة بعمّان جمعت تلاتين مليون دولار بجولة تمويل جديدة. والشركة بتقول إنها رح تضاعف
> عدد موظفينها خلال سنة ونص، ورح تفتح مكتب بالرياض.

> هسّا خلّينا نروح عالشرائح. إنفيديا طلّعت جيل جديد، وبتقول إنه أسرع بأربع مرات من الجيل اللي
> قبله بتدريب الموديلات الكبيرة. بس لسّا ما حكت عن الأسعار.

> وبعالم الموديلات، أوبن إيه آي نزّلت موديل جديد، وأنثروبيك حدّثت كلود، وجي فورتي تو أعلنت
> شراكة جديدة مع أدنوك. وبالسعودية، هيوماين وسدايا عم بيشتغلوا على موديلات عربية.

> ليش هاد بيهمّ؟ لأنه الشركة اللي بتملك الموديل تبعها، بتملك بياناتها وبتتحكم بالتكلفة.
> بس السؤال الحقيقي: في عندها ناس بيعرفوا يشغّلوه؟

> وبسرعة: سبعة وتلاتين بالمية من الشركات اللي انسألت بلّشت تجرّب الوكلاء الأذكياء، وأربعة
> بالمية بس نقلتهم للشغل الحقيقي. والفرق بين الرقمين هاد هو قصة السنة الجاية.

> هاد كل إشي عنّا هالأسبوع. اكتبولنا رأيكم بالتعليقات، ويعطيكم العافية.

The figures above are practice copy for pronunciation only. They are not facts and must never appear
in an episode.

**Names to say once, clearly, the way you want them** (add any you hear mispronounced later — they also
go in `config/pronunciation.yaml`): أوبن إيه آي · أنثروبيك · كلود · جوجل ديب مايند · جيميناي · إنفيديا ·
ميتا · مايكروسوفت · أمازون · جي فورتي تو · هيوماين · سدايا · أدنوك · أرامكو · تينسنت · ديب سيك ·
ميسترال · بيربلكسيتي · جي بي يو · سي بي يو · إيه آي.

## After the session
1. In HeyGen create the **digital twin** from the footage (with the consent clip) and the **voice
   clone** from the audio; wait for both to finish.
2. Tell the chat session (or run the **heygen-assets** workflow): the new avatar look ID and voice ID
   go into `config/settings.yaml` under `video.heygen`.
3. Test before spending on an episode: one 20-second clip through the voice-first route (speech with
   the new voice → the twin driven by that audio). The 2026-11-07 test with the photo look cost 1 credit
   of speech and 7 of Avatar IV.
4. If it looks and sounds right, the next episode uses them.
