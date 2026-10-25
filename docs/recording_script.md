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

## Reading passage (Jordanian colloquial, the way the show will sound)

Read it the way you would tell a friend, not the way a newsreader reads. The clone learns
your rhythm, your pauses and your Jordanian vowels from this.

> أهلاً فيكم بـ«أسبوع الذكاء الاصطناعي»، معكم وسام. كل أسبوع بنختارلكم أهم إشي صار بعالم
> الذكاء الاصطناعي، وبنسأل سؤال واحد: طيب، شو يعني هاد إلنا هون بالمنطقة؟

> شركة ناشئة بعمّان جمعت تلاتين مليون دولار بجولة تمويل جديدة. والشركة بتقول إنها رح تضاعف
> عدد موظفينها خلال سنة ونص، ورح تفتح مكتب بالرياض.

> هسّا خلّينا نروح عالشرائح. إنفيديا NVIDIA طلّعت جيل جديد، وبتقول إنه أسرع بأربع مرات من
> الجيل اللي قبله بتدريب الموديلات الكبيرة. بس لسّا ما حكت عن الأسعار.

> وبعالم الموديلات، ميسترال Mistral الفرنسية نزّلت موديل مفتوح، وأنثروبيك Anthropic حدّثت
> مساعدها، وجي فورتي تو G42 أعلنت شراكة جديدة بأوروبا.

> ليش هاد بيهمّ؟ لأنه الشركة اللي بتملك الموديل تبعها، بتملك بياناتها وبتتحكم بالتكلفة.
> بس السؤال الحقيقي: في عندها ناس بيعرفوا يشغّلوه؟

> وبسرعة: سبعة وتلاتين بالمية من الشركات اللي انسألت بلّشت تجرّب الوكلاء الأذكياء، وأربعة
> بالمية بس نقلتهم للشغل الحقيقي. والفرق بين الرقمين هاد هو قصة السنة الجاية.

> هاد كل إشي عنّا هالأسبوع. اشتركوا بالقناة واكتبولنا رأيكم، ويعطيكم العافية.

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
