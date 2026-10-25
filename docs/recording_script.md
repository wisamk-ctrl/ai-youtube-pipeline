# Recording session — avatar footage and voice clone

One session gives you both: the camera footage trains the avatar, and its audio (or a
separate mic track) trains the voice. HeyGen's upload screens state the current minimum
lengths and formats; follow them where they differ from this sheet.

## Before you record

- **Room:** quiet, soft furnishings, no echo, no air-conditioning hum, phone on silent.
- **Light:** soft and even on the face, a window in front of you or two lights at 45°. No
  harsh shadows, no light behind you.
- **Camera:** 4K if available (the pipeline renders at 3840×2160), at eye level, landscape,
  locked off on a tripod. Frame from mid-chest up, a little headroom.
- **Mic:** a lavalier or USB condenser a hand's width from the mouth, recorded clean: no
  music, no noise reduction, no compression.
- **You:** the outfit you want on air every week (solid colours, no fine stripes or logos),
  hair and glasses as they will look in every episode.

## Avatar footage (what HeyGen asks for)

1. Look into the lens the whole time, as if talking to one viewer.
2. Speak naturally with small, calm gestures. Hands stay below the chest and never cover
   the face.
3. Close your mouth and pause for one to two seconds between paragraphs; HeyGen uses the
   still moments to learn your idle state.
4. Keep the head and shoulders inside the frame and do not walk or turn sideways.
5. Record HeyGen's **consent statement** on camera, exactly as its upload screen shows it.
   It is required and it is the proof the avatar is you.

Read the passage below for the footage. For the voice clone, read it again plus any other
Arabic news copy until you reach the length HeyGen asks for; more clean audio gives a
better clone.

## Reading passage (broadcast MSA, varied on purpose)

> أهلاً بكم في «أسبوع الذكاء الاصطناعي»، معكم وسام. في كل أسبوع نختار لكم أهم ما جرى في
> عالم الذكاء الاصطناعي، ونسأل سؤالاً واحداً: ماذا يعني ذلك لمؤسساتكم في الخليج والعالم العربي؟

> أعلنت شركة ناشئة في أبوظبي جمع مئتين وخمسين مليون دولار في جولة تمويل جديدة، بقيادة صندوق
> سيادي. وقالت الشركة إنها ستضاعف عدد موظفيها خلال ثمانية عشر شهراً، وستفتتح مكتباً في الرياض.

> في المقابل، تُدارُ اليوم أكثر من ثلث العمليات الحكومية في بعض الدول إلكترونياً، ويُتوقَّع أن
> ترتفع النسبة إلى النصف بحلول عام ألفين وثمانية وعشرين، بحسب تقديرات رسمية.

> ننتقل إلى الرقائق. كشفت إنفيديا NVIDIA عن جيل جديد من معالجاتها، وقالت إنه أسرع بأربع مرات من
> الجيل السابق في تدريب النماذج الكبيرة. ولم تُعلَن الأسعار بعد.

> أما في النماذج، فأطلقت ميسترال Mistral الفرنسية نموذجاً مفتوح الأوزان، وأطلقت أنثروبيك
> Anthropic تحديثاً لمساعدها، فيما أعلنت جي فورتي تو G42 شراكة جديدة في أوروبا.

> لماذا يهم هذا؟ لأن المؤسسة التي تملك نموذجها تملك بياناتها، وتتحكم في تكلفتها.
> لكن السؤال يبقى: هل تملك الكفاءات اللازمة لتشغيله؟

> وفي جولة سريعة: سبعة وثلاثون في المئة من الشركات المشمولة بالمسح بدأت تجربة الوكلاء،
> وأربعة في المئة فقط نقلتها إلى الإنتاج. والفارق بين الرقمين هو قصة العام المقبل.

> هذا كل ما لدينا هذا الأسبوع. شكراً لكم، ونلقاكم في الحلقة القادمة.

The figures above are practice copy for pronunciation only. They are not facts and must
never appear in an episode.

## After the session

1. In HeyGen create the **Instant Avatar** from the footage and the **voice clone** from the
   audio. Wait for both to finish processing.
2. Run the **heygen-assets** workflow: your avatar and voice appear at the top of the issue
   with their IDs.
3. Run **weekly-roundup** with phase `video`, week `voicetest`, and your two IDs in
   `avatar_id` / `voice_id`. It renders the 45-second test clip in
   `reviewed/voicetest/script.md`: numbers, foreign names, passive verbs, pauses.
4. If the clip sounds right, save the IDs as the `HEYGEN_AVATAR_ID` and `HEYGEN_VOICE_ID`
   secrets. Every episode uses them from then on.
