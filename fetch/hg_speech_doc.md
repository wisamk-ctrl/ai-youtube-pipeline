> ## Documentation Index
> Fetch the complete documentation index at: https://developers.heygen.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Text to Speech

> Try Turbo Free with a public voice, or generate speech from your clone with POST /v3/models/audio/tts and POST /v3/models/audio/tts/stream. Stream text in over a WebSocket.

![](https://mintcdn.com/heygen-1fa696a7/hfMXXwJzjE7vBSYZ/images/theme/research-2.webp?fit=max\&auto=format\&n=hfMXXwJzjE7vBSYZ\&q=85\&s=d6ee10585b27ddaf8137d6ed67791708)

The [HeyGen Voice](https://developers.heygen.com/docs/models/heygen-voice.md) model speaks two ways from the same request body:

* [`POST /v3/models/audio/tts`](https://developers.heygen.com/reference/generate-model-speech) waits for synthesis and returns one audio file URL. By default, the file is a 44.1 kHz WAV.
* [`POST /v3/models/audio/tts/stream`](https://developers.heygen.com/reference/stream-speech) returns ordered audio parts as Server-Sent Events (SSE).

To send `text` in pieces, such as LLM tokens, use [WebSocket input streaming](#websocket-input-streaming).

To get MP3, raw PCM, μ-law, or A-law audio, or a different sample rate, set [`output_format`](#output-format).

`voice_id` must be an `ACTIVE` HeyGen public voice or a clone in your workspace: an [instant voice](https://developers.heygen.com/docs/voices/heygen-voice-instant-clone.md) or a [professional clone](https://developers.heygen.com/docs/voices/professional-voice-clone.md).

> [!TIP]
>
> For the closest match to an instant clone's original speaker, create the clone with `similarity: "max"` and send `expressiveness_boost: 0.5`.

## Generate speech with an agent

Paste this into [Claude Code](https://claude.com/claude-code), [Codex](https://openai.com/codex/), or Cursor to try Turbo Free with a public voice. You do not need to create a clone or add credits.

```text Prompt for your agent wrap theme={null}
I want to try HeyGen Voice Turbo Free with the public voice Nadine. I am not a developer, so run the commands for me where you can, explain each step in one plain sentence, and when I have to do something myself tell me exactly what and wait for me.

Read these first and follow them exactly:
- https://developers.heygen.com/docs/voices/heygen-voice-speech.md
- https://developers.heygen.com/docs/for-ai-agents.md (rules for agents)

Then take me through this, checking each step before the next:
1. API key. Look for HEYGEN_API_KEY in my environment. If it is missing, send me to https://platform.heygen.com/api-keys to create one and have me export it in my terminal myself. Never ask me to paste the key into this chat. Confirm it works with GET /v3/users/me.
2. Voice. Use Nadine, voice_id 83548de556df48ba8c09c42a57c51d85. If it is not available, list public voices with GET /v3/models/audio/voices?type=public and let me pick an ACTIVE instant voice. Do not create a clone.
3. Text. Ask me what I want the voice to say, up to 10,000 characters of plain prose, and its language if I know it.
4. Speak. Call POST /v3/models/audio/tts with model heygen-voice-1-turbo-free, the voice_id and text. Send language only if I told you the language; otherwise leave it out so HeyGen detects it. Download the WAV and open it so I can listen. Show me how to change the text and run it again. On 429, wait and retry with backoff. Never switch to a paid model without asking me.

If a request fails, look the error code up in the Errors table on that page and tell me the fix. Never invent keys, IDs, or URLs; if something is missing, ask me for that one thing.
```

## Turbo Free

> [!NOTE]
>
> **HeyGen Voice Turbo Free is free until November 30, 2026.** We will notify you before this offer changes.
>
> [Try it in the playground](https://platform.heygen.com/models/heygen-voice) · [Get a free API key](https://platform.heygen.com/api-keys)

Set `"model": "heygen-voice-1-turbo-free"` on either speech endpoint, or `model=heygen-voice-1-turbo-free` on a [WebSocket](#socket-limits). These requests are free and do not require a credit balance.
Use a public voice or a HeyGen Voice 1 instant clone. Professional clones are not supported.
Requests to the default model or paid Turbo are still charged.

Use Turbo Free for tests, prototypes, and small amounts of speech.
Service availability, response time, and time to first audio are not guaranteed.

### Speech limits

Two limits apply:

* **Your request limit:** each endpoint allows 30 requests per minute per workspace member by default. Your account can have a different limit.
* **Shared capacity:** all Turbo Free users share a limited amount of capacity. You can receive HTTP `429` even if you are below your request limit.

If either limit blocks your request, the API returns `429 rate_limit_exceeded`.
If the response has a `Retry-After` header, wait that number of seconds before you retry.
Otherwise, increase the wait time after each failed attempt (exponential backoff).
A timeout or service failure can return HTTP `500` instead.
For streaming requests, these HTTP errors occur before audio starts.

A free request never switches to a paid model.
To use paid Turbo, send a new request with `"model": "heygen-voice-1-turbo"`. This request is charged.

## Request fields

The full field list is in [the API reference](https://developers.heygen.com/reference/generate-model-speech.md). `text` takes 1–10,000 characters of plain prose, and public and instant voices also perform [audio tags](#audio-tags), such as `[laughs]`, and take [IPA pronunciations](#pronunciation). `model` defaults to `heygen-voice-1`; `null` and unknown names return `400`. `expressiveness_boost` (instant voices, `0.0`–`1.0`, default `1.0`, or `0.5` when a [pronunciation](#pronunciation) applies) is not applied when `text` contains an audio tag other than `[pause]`. `seed`, `speed`, `pitch_shift` and `pitch_variance` shape professional voices only.

Unknown fields and invalid values return `400 invalid_parameter`, with `param` set to that field. Instant voices, including Turbo, accept and ignore valid `seed`, `speed`, `pitch_shift`, and `pitch_variance` values. Professional voices reject `expressiveness_boost`. Professional voices on `heygen-voice-1` take `<break time="0.5s"/>` pauses of up to 5 seconds each. On an instant voice, including every Turbo request, a `<break>` tag returns `400 invalid_parameter`. Other SSML is not supported. Instant voices made before HeyGen Voice 1 must be cloned again before they can speak here.

### Language

Send `language` as a lowercase ISO 639-1 code from [Supported languages](#supported-languages), such as `en` or `zh`. HeyGen Voice has no regional accents, so a regional tag such as `en-US`, `pt-BR`, or `zh-HK` returns `400 invalid_parameter` with `param` set to `language`; send the base code instead. Cantonese (`yue`) is not supported.

Send `language` when you know it. HeyGen speaks `text` in the stated `language` as given and does not check it against the text, so a wrong one, such as `en` for Russian text, gives speech with that language's accent. If you are not sure, leave it out. When you omit it, HeyGen reads the language from `text` and uses the first of these that applies:

1. A confident reading of `text`. If HeyGen Voice does not speak that language, the request returns `400 invalid_parameter`.
2. The language the voice was created in, if `text` is written in that language's script.
3. A less certain reading, if a second reading of `text` agrees with it.
4. The usual language of the script `text` is written in, such as English for Latin letters.

If none of these is a language HeyGen Voice speaks, the request returns `400 invalid_parameter` with `param` set to `language`. Send `language` and try again. Every successful response names the language it used in the `Content-Language` header, so you can check the result and send `language` next time if it is not what you meant.

### Supported languages

| Code | Language |
| - | - |
| `ar` | Arabic |
| `be` | Belarusian |
| `bg` | Bulgarian |
| `ca` | Catalan |
| `cs` | Czech |
| `da` | Danish |
| `de` | German |
| `el` | Greek |
| `en` | English |
| `es` | Spanish |
| `fa` | Persian |
| `fi` | Finnish |
| `fr` | French |
| `he` | Hebrew |
| `hi` | Hindi |
| `hr` | Croatian |
| `hu` | Hungarian |
| `id` | Indonesian |
| `it` | Italian |
| `ja` | Japanese |
| `ko` | Korean |
| `mk` | Macedonian |
| `ms` | Malay |
| `nl` | Dutch |
| `pl` | Polish |
| `pt` | Portuguese |
| `ro` | Romanian |
| `ru` | Russian |
| `sk` | Slovak |
| `sl` | Slovenian |
| `sr` | Serbian |
| `sv` | Swedish |
| `ta` | Tamil |
| `th` | Thai |
| `tl` | Filipino (Tagalog) |
| `tr` | Turkish |
| `uk` | Ukrainian |
| `vi` | Vietnamese |
| `zh` | Chinese (Mandarin) |

`fil` is also accepted for Filipino.

## Generate completed speech

Try Turbo Free with Nadine, a public voice. No clone or credit balance is required. The same voice and model work in the streaming example below.

```bash theme={null}
curl -X POST "https://api.heygen.com/v3/models/audio/tts" \
  -H "X-Api-Key: $HEYGEN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "heygen-voice-1-turbo-free",
    "voice_id": "83548de556df48ba8c09c42a57c51d85",
    "text": "Hello from Nadine. Try HeyGen Voice Turbo Free.",
    "language": "en",
    "expressiveness_boost": 0.8
  }'
```

The request stays open until the file is assembled, so no polling is needed. The response carries `audio_url`, one mono PCM16 WAV at 44.1 kHz without `output_format`, and `duration` in seconds.

Successful completed and streaming responses include `X-Request-Id` and `Content-Language`. Use `X-Request-Id` to match usage records and any billing settlement. `Content-Language` names the language the speech was generated in.

For a professional voice, swap the instant-only control for the prosody controls:

```json theme={null}
{
  "model": "heygen-voice-1",
  "voice_id": "0f4e5d8c9a1b4d62a914938d06c31234",
  "text": "Hello from my professional voice. <break time=\"0.5s\"/> Let us begin.",
  "language": "en",
  "seed": 7,
  "speed": 1.1,
  "pitch_shift": -1.0,
  "pitch_variance": 1.2
}
```

### Character timestamps

Set `"with_timestamps": true` to get the time of each character, for captions or word highlighting. The response then also carries `original_characters`: one entry for each character of `text`, in order, with `text`, `start_time`, and `end_time` in seconds from the start of the audio.

`original_characters` follows `text` as sent, so it also covers the characters of any [audio tags](https://developers.heygen.com/docs/voices/heygen-voice-audio-tags.md). Leave the bracketed tags out when you build captions.

Timestamps don't change the price.

## Stream speech

The stream is `text/event-stream`. Disable response buffering and handle each event as it arrives.

```bash theme={null}
curl -N --no-buffer -X POST "https://api.heygen.com/v3/models/audio/tts/stream" \
  -H "X-Api-Key: $HEYGEN_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "heygen-voice-1-turbo-free",
    "voice_id": "83548de556df48ba8c09c42a57c51d85",
    "text": "Hello from Nadine. Try HeyGen Voice Turbo Free.",
    "language": "en",
    "with_timestamps": true
  }'
```

**Audio events** carry base64-encoded standalone WAV parts, mono PCM16 at 44.1 kHz. Play them in ascending `part_index` order; each part is a complete WAV container, so decode them individually rather than concatenating the bytes.

```text theme={null}
data: {"type":"audio","part_index":0,"audio":"UklGR..."}

data: {"type":"audio","part_index":1,"audio":"UklGR..."}
```

**Character-alignment events** appear when `with_timestamps` is `true`. `original_characters` follows the submitted text, while `normalized_characters` follows the text spoken after normalization. Each character carries `text`, `start_time`, and `end_time` in seconds.

```text theme={null}
data: {"type":"character_alignment","original_characters":[{"text":"H","start_time":0.0,"end_time":0.08}],"normalized_characters":[{"text":"H","start_time":0.0,"end_time":0.08}]}
```

A clean stream ends with `data: [DONE]`. If synthesis fails mid-stream, the stream ends with an error event instead and no `[DONE]`:

```text theme={null}
data: {"type":"error","detail":"Voice inference failed mid-stream"}
```

Errors before the first event use the standard JSON [error envelope](https://developers.heygen.com/docs/error-codes.md).

## WebSocket input streaming

Use a WebSocket when your text arrives in pieces, such as tokens from an LLM. You send text as it is produced. Audio returns on the same connection.

| URL | Use |
| - | - |
| `wss://api.heygen.com/v3/models/audio/tts/stream-input?voice_id=<voice_id>` | One synthesis on the socket. |
| `wss://api.heygen.com/v3/models/audio/tts/multi-stream-input?voice_id=<voice_id>` | Up to five running contexts on one socket, each with its own `context_id`. |

Messages use the ElevenLabs `stream-input` and `multi-stream-input` formats. The URLs, authentication, and parameter names are HeyGen's, so ElevenLabs SDKs do not connect directly.

Use a public voice or an instant clone on any of the three models. A professional clone returns `400 invalid_parameter` at the handshake. Use [`POST /v3/models/audio/tts/stream`](https://developers.heygen.com/reference/stream-speech) for those voices.

### Send text and receive audio

This Python example uses [`websockets`](https://pypi.org/project/websockets/) and writes raw PCM16 at 24 kHz to `speech.pcm`.

```python theme={null}
import asyncio
import base64
import json
import os

import websockets

URL = (
    "wss://api.heygen.com/v3/models/audio/tts/stream-input"
    "?voice_id=83548de556df48ba8c09c42a57c51d85"
    "&model=heygen-voice-1-turbo-free"
    "&language=en"
    "&output_format=pcm_24000"
)


async def main():
    headers = {"X-Api-Key": os.environ["HEYGEN_API_KEY"]}
    async with websockets.connect(URL, additional_headers=headers) as socket:
        await socket.send(json.dumps({"text": " "}))
        await socket.send(json.dumps({"text": "Hello from Nadine. "}))
        await socket.send(json.dumps({"text": "This text arrived in pieces.", "flush": True}))
        await socket.send(json.dumps({"text": ""}))

        with open("speech.pcm", "wb") as audio:
            async for frame in socket:
                message = json.loads(frame)
                if message.get("audio"):
                    audio.write(base64.b64decode(message["audio"]))
                if message.get("isFinal"):
                    break


asyncio.run(main())
```

### Authenticate

Send the same `X-Api-Key` or `Authorization: Bearer` header as the other speech endpoints. An API key needs the `voices:write` scope.

A client that cannot set headers, such as a browser, uses a single-use token. Your backend calls [`POST /v3/models/audio/tts/stream-input/tokens`](https://developers.heygen.com/reference/create-speech-input-token) with its API key. The client then adds the returned `token` to the URL:

```javascript theme={null}
const socket = new WebSocket(
  `wss://api.heygen.com/v3/models/audio/tts/stream-input?voice_id=${voiceId}&token=${token}`
);
```

A token is valid for 15 minutes and for one connection. Do not send a token and a credential header together.

### Query parameters

`voice_id` is required. Unknown parameters return `400 invalid_parameter` at the handshake.

| Parameter | Default | Description |
| - | - | - |
| `model` | `heygen-voice-1` | `heygen-voice-1`, `heygen-voice-1-turbo`, or `heygen-voice-1-turbo-free`. |
| `output_format` | `pcm_44100` | A string, not the `output_format` object of the HTTP endpoints. One of `pcm_8000`, `pcm_16000`, `pcm_22050`, `pcm_24000`, `pcm_32000`, `pcm_44100`, `pcm_48000`, `mp3_22050_32`, `mp3_24000_48`, `mp3_44100_32`, `mp3_44100_64`, `mp3_44100_96`, `mp3_44100_128`, `mp3_44100_192`, `ulaw_8000`, or `alaw_8000`. Another value can pass the handshake, then closes the socket with code `1008` when a context opens. |
| `language` | Detected for each context | Lowercase ISO 639-1 code. See [Language](#language). |
| `with_timestamps` | Timings where available | `true` requires timings. `false` turns them off. |
| `expressiveness_boost` | `1.0` | `0.0`–`1.0`. |
| `end_user_id` | None | A stable, opaque ID of the end user in your application, for usage attribution. |
| `inactivity_timeout` | `20` | Seconds without a client message before the input ends, `1`–`180`. |
| `auto_mode` | `false` | `true` generates at sentence ends. |
| `apply_text_normalization` | `auto` | `auto`, `on`, or `off`. |
| `enable_ssml_parsing` | `false` | `true` makes `<break time="1s"/>` a pause. Without it, a break tag closes the socket with code `1008`. |
| `enable_logging` | `true` | `false` keeps no stored copy of the audio. |

### Messages you send

Send JSON text messages. An unknown field closes the socket with code `1008`.

| Field | Description |
| - | - |
| `text` | Text to speak, up to 10,000 characters in one message. Send `" "` to open. On `stream-input`, `""` ends the input. On `multi-stream-input`, `""` without `flush` keeps the context alive. |
| `flush` | `true` generates the buffered text now. |
| `generation_config` | First message of a context only. `chunk_length_schedule` sets how many characters start each generation. Default: `[120, 160, 250, 290]`. |
| `context_id` | `multi-stream-input` only. 1–128 characters. Default: `default`. |
| `close_context` | `multi-stream-input` only. Ends a context and returns its `isFinal` message. A flushed context finishes its audio first. Any other context stops now. |
| `close_socket` | `multi-stream-input` only. Closes every context, then the socket. |

On `multi-stream-input`, a context stays open after `flush`, so you can send it more text. Send `close_context` to end it. A context that you do not close ends after `inactivity_timeout`. It counts toward the five running contexts until then.

```json theme={null}
{"text": " ", "context_id": "turn-1"}
{"text": "Hello there.", "context_id": "turn-1", "flush": true}
{"context_id": "turn-1", "close_context": true}
```

### Messages you receive

Each audio message carries base64 audio in `output_format`. `alignment` follows the text as sent, and `normalizedAlignment` follows the text spoken. Both are `null` when timings are off or not available, and their lists can be empty on a message. Times are in milliseconds from the start of that message.

```json theme={null}
{"audio": "<base64 audio>", "isFinal": null, "alignment": {"chars": ["H", "i"], "charStartTimesMs": [0, 80], "charDurationsMs": [80, 90]}, "normalizedAlignment": {"chars": ["H", "i"], "charStartTimesMs": [0, 80], "charDurationsMs": [80, 90]}}
```

The last message of a context has `isFinal: true`. `synthesizedChars` is the number of characters spoken, so it is lower when a context stops early.

```json theme={null}
{"isFinal": true, "synthesizedChars": 57}
```

On `multi-stream-input`, every message also has `contextId`. A JSON message with `message` and the standard `error` envelope comes before every close except codes `1000` and `1012`.

### Socket limits

* **Request limit:** each handshake and each token request counts as one request toward the Stream Speech limit. On `multi-stream-input`, each new context counts as one more. Past the limit, a handshake returns `429 rate_limit_exceeded` with `Retry-After`, and a new context closes the socket with code `1008`.
* **Context size:** each context accepts up to 10,000 characters and is billed as one request.
* **Turbo Free:** a request is counted when each context opens. Text is counted as each piece is sent for synthesis. A socket over the free quota closes with code `1008`, which can come after earlier audio.
* **Open sockets:** a workspace can have a limit on open sockets. Past it, a handshake returns `429 rate_limit_exceeded` with `Retry-After`.

### Close codes

A refused handshake returns the standard [error envelope](https://developers.heygen.com/docs/error-codes.md). After the handshake, the socket reports problems with a close code:

| Code | Meaning | What to do |
| - | - | - |
| `1000` | Normal end, or no message within `inactivity_timeout`. | Open a new socket when you have more text. |
| `1008` | A message or its text was refused, or a limit was reached. | Read the error message. Fix the request, or wait if it is a limit. |
| `1011` | Voice inference failed. | Retry with exponential backoff. |
| `1012` | The service is restarting. | Reconnect. |
| `1013` | Capacity is full. | Retry with exponential backoff. |

## Output format

Without `output_format`, `/tts` returns a WAV file and `/tts/stream` returns SSE events with WAV parts. Both are mono PCM16 at 44.1 kHz.

Set `output_format` on either endpoint to choose the `encoding` (`pcm`, `mp3`, `ulaw` or `alaw`) and `sample_rate_hertz`. All output is mono. `pcm` is signed little-endian PCM16 with no header, and `ulaw` and `alaw` run at `8000` Hz only. `pcm` and `mp3` default to `44100` Hz; the allowed rates and `mp3` `bitrate_bps` values are in [the API reference](https://developers.heygen.com/reference/generate-model-speech.md). An unsupported combination, such as `ulaw` at `16000` Hz, returns `400 invalid_parameter`.

On `/tts`, `audio_url` is a file in the requested format. Its extension names the encoding: `.pcm`, `.mp3`, `.ulaw`, or `.alaw`. The `pcm`, `ulaw`, and `alaw` files contain only audio samples, with no WAV header. To get a WAV file, omit `output_format`.

```bash theme={null}
curl -X POST "https://api.heygen.com/v3/models/audio/tts" \
  -H "X-Api-Key: $HEYGEN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "heygen-voice-1-turbo-free",
    "voice_id": "83548de556df48ba8c09c42a57c51d85",
    "text": "Hello from Nadine.",
    "language": "en",
    "output_format": {"encoding": "mp3", "sample_rate_hertz": 44100, "bitrate_bps": 192000}
  }'
```

On `/tts/stream`, the response body is raw audio bytes in the requested format, not SSE. The stream has no events and no `[DONE]`. Write the bytes to a file or a player in the order they arrive.

* `Content-Type` is `audio/pcm`, `audio/mpeg`, `audio/basic` (μ-law), or `audio/alaw`.
* The `X-Audio-Sample-Rate` and `X-Audio-Channels` headers give the sample rate and the number of channels.
* `with_timestamps` must be `false`. If it is `true`, the request returns `400 invalid_parameter`.
* If synthesis fails after the audio starts, the connection closes. No error event is sent.

## Audio tags

Write an audio tag, such as `[excited]`, `[whispers]`, or `[laughs]`, in `text` to change how a public or instant voice speaks, or to add a sound at that spot. Both speech endpoints accept them on all three models. See [Audio Tags](https://developers.heygen.com/docs/voices/heygen-voice-audio-tags.md) for samples, the 201 supported tags, and how to write them.

## Pronunciation

Set how a public or instant voice says a name or term with an [IPA](https://en.wikipedia.org/wiki/International_Phonetic_Alphabet) transcription. Pronunciation works on `heygen-voice-1` and `heygen-voice-1-turbo`, on both speech endpoints.

For every occurrence of a term, send `pronunciation_dictionary`, an object of up to 100 terms, each mapped to its IPA:

```bash theme={null}
curl -X POST "https://api.heygen.com/v3/models/audio/tts" \
  -H "X-Api-Key: $HEYGEN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "heygen-voice-1-turbo",
    "voice_id": "83548de556df48ba8c09c42a57c51d85",
    "text": "Keytruda is now available. Ask your doctor whether Keytruda is right for you.",
    "language": "en",
    "pronunciation_dictionary": {
      "Keytruda": "/kiːˈtruː.də/",
      "Siobhan": "/ʃɪˈvɔːn/"
    }
  }'
```

For a single occurrence, wrap it in a `<pron>` tag in `text`:

```text theme={null}
Welcome, <pron ipa="/ʃɪˈvɔːn/">Siobhan</pron>. Today we cover Keytruda.
```

* Write each IPA value between slashes, as in `/ʃɪˈvɔːn/`, in up to 512 characters.
* A dictionary term matches whole words, without regard to case, so `Keytruda` also matches `KEYTRUDA`. A term can be up to 128 characters.
* A `<pron>` tag takes precedence over the dictionary for the text it wraps.
* A request can apply up to 100 pronunciations, counting every occurrence from the dictionary and from tags.
* When a pronunciation applies, `expressiveness_boost` defaults to `0.5`. Send it to choose another value from `0.0` to `1.0`.

Videos read pronunciations from a [brand glossary](https://developers.heygen.com/docs/brand-glossary/pronunciations.md) that you store once and pass as `brand_glossary_id`. Text to Speech takes them with each request in `pronunciation_dictionary`.

Pronunciation requests that cannot be served return `400 invalid_parameter`:

| `message` | Fix |
| - | - |
| `Invalid IPA pronunciation field` | Wrap the IPA in slashes, as in `/ʃɪˈvɔːn/`. |
| `Pronunciation supports instant voices on heygen-voice-1 and heygen-voice-1-turbo only` | Use a public or instant voice with `heygen-voice-1` or `heygen-voice-1-turbo`. |
| `text may contain at most 100 pronunciation occurrences` | Split `text` across requests. |

## Errors

| HTTP status | Error code | Meaning |
| - | - | - |
| `400` | `invalid_parameter` | Missing or unknown field, an invalid value, an unsupported `language` or `model`, either Turbo model sent for a professional voice (`param` is `model`), or, when `language` is omitted, a language that could not be detected from `text`. |
| `400` | `voice_expired` | The workspace is over its professional voice clone slot limit. [Add a slot](https://platform.heygen.com/usage) or delete another professional voice. |
| `402` | `insufficient_credit` | The API credit balance is empty. |
| `402` | `usage_limit_reached` | The member reached a workspace usage limit. Ask a workspace administrator to check the limit. |
| `403` | `forbidden` | The voice is a professional clone and the account is not enabled for professional voice cloning. Check the plan on the [Usage page](https://platform.heygen.com/usage). |
| `404` | `voice_not_found` | The voice is not in the caller's workspace. |
| `409` | `voice_not_ready` | The voice is still `PENDING`. Poll [`GET /v3/models/audio/voices/{voice_id}`](https://developers.heygen.com/reference/get-an-audio-voice) until `status` is `ACTIVE`, then send the request again. |
| `409` | `voice_training_failed` | The voice is `FAILED`. Read `failure_reason` on the voice. |
| `429` | `rate_limit_exceeded` | Your request limit was reached, or Turbo Free capacity is full. Wait for the seconds in `Retry-After`, if present. Otherwise, increase the wait time after each failed attempt. |
| `500` | | A Turbo Free request timed out or the service failed. Retry with exponential backoff. |
| `503` | `service_unavailable` | Inference is busy; the request is safe to retry. |


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.