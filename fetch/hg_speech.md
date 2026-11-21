> ## Documentation Index
> Fetch the complete documentation index at: https://developers.heygen.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Generate Speech

> Generate speech from the voice identified by `voice_id`.

The request stays open until speech generation finishes. The response contains an audio URL: a 44.1 kHz mono WAV by default, or the requested `output_format`.

### Voice and settings

Use an `ACTIVE` HeyGen Voice clone in your workspace. `heygen-voice-1-turbo` speaks instant clones at lower latency and refuses professional clones.

`seed`, `speed`, `pitch_shift`, and `pitch_variance` apply only to professional clones. Instant clones, including Turbo, accept and ignore these controls.

### Turbo Free

Use `heygen-voice-1-turbo-free` for instant voices without charge, including API-key and OAuth requests. This model is available to direct users and resellers for experimentation and prototyping. It has no latency, time-to-first-audio, or availability guarantee.

Per-user request limits and shared free capacity both apply. Either limit can return HTTP 429 with `code=rate_limit_exceeded`. Shared capacity can be exhausted even when you are below your own request limit. A timeout or service failure can return HTTP 500. Follow `Retry-After` when present; otherwise use exponential backoff. A free request never switches to a paid model. For streaming, HTTP 429 is returned before audio starts.

### Language

Set `language` to the language of `text`. If you omit it, the language is detected from `text`. Successful responses include `Content-Language`, the language the speech was generated in.

### Limits and request ID

The rate limit is 30 requests per minute per workspace member.
High demand can exceed the available capacity for speech generation. The service then returns HTTP 429 with `code=rate_limit_exceeded`. This response has no `Retry-After` header. Retry the request with exponential backoff. For streaming, the service returns HTTP 429 only before the response starts.

Successful responses include `X-Request-Id`. Use this ID when you contact support about the request. For instant clones, completed requests automatically retain audio for request stitching when speech retention is allowed. Pass completed IDs in `previous_request_ids` or `next_request_ids` to keep continuity. Use up to three IDs per field in playback order, from the same workspace, voice, and model, within two hours. Finish reading a stream before reusing its ID. If context is unavailable, synthesis continues with its normal defaults. Stitching is unavailable when speech retention is disabled.



## OpenAPI

````yaml /openapi/external-api.json post /v3/models/audio/tts
openapi: 3.1.0
info:
  title: HeyGen External API
  version: 1.0.0
  description: >-
    HeyGen's external API for programmatic AI video creation. See
    https://docs.heygen.com for full documentation.
  contact:
    name: HeyGen Product Infra
    url: https://heygen.com
servers:
  - url: https://api.heygen.com
    description: Production
security:
  - ApiKeyAuth: []
  - BearerAuth: []
tags:
  - name: Video
    description: >-
      Create videos from a prompt or an avatar, then list, fetch, deliver and
      delete them
  - name: Avatar
    description: >-
      Create avatars and looks, record consent, and generate with the Avatar 6
      model
  - name: Voice
    description: Text to speech, speech to speech, and voice cloning
  - name: Audio
    description: Music, sound effects, transcription, stem separation and audio analysis
  - name: Image
    description: Generate images
  - name: Video editing
    description: >-
      Translate, lipsync, clip, analyze and remove filler words or backgrounds
      from existing videos
  - name: Video Agent
    description: Create videos from a prompt with an agent that plans, writes and edits
  - name: Templates
    description: Generate videos from reusable templates by replacing their variables
  - name: HyperFrames
    description: Render HyperFrames compositions into video
  - name: Brand
    description: >-
      Brand kits (colors, fonts, logos) and brand glossaries (term translations
      and pronunciations)
  - name: Assets and folders
    description: Upload files and organize them in folders
  - name: Batches
    description: Submit and track videos, translations, lipsyncs and uploads in bulk
  - name: Webhooks
    description: Manage webhook endpoints and events
  - name: Account and usage
    description: Your account, the current API key, request logs and usage
paths:
  /v3/models/audio/tts:
    post:
      tags:
        - Voice
      summary: Generate Speech
      description: >-
        Generate speech from the voice identified by `voice_id`.


        The request stays open until speech generation finishes. The response
        contains an audio URL: a 44.1 kHz mono WAV by default, or the requested
        `output_format`.


        ### Voice and settings


        Use an `ACTIVE` HeyGen Voice clone in your workspace.
        `heygen-voice-1-turbo` speaks instant clones at lower latency and
        refuses professional clones.


        `seed`, `speed`, `pitch_shift`, and `pitch_variance` apply only to
        professional clones. Instant clones, including Turbo, accept and ignore
        these controls.


        ### Turbo Free


        Use `heygen-voice-1-turbo-free` for instant voices without charge,
        including API-key and OAuth requests. This model is available to direct
        users and resellers for experimentation and prototyping. It has no
        latency, time-to-first-audio, or availability guarantee.


        Per-user request limits and shared free capacity both apply. Either
        limit can return HTTP 429 with `code=rate_limit_exceeded`. Shared
        capacity can be exhausted even when you are below your own request
        limit. A timeout or service failure can return HTTP 500. Follow
        `Retry-After` when present; otherwise use exponential backoff. A free
        request never switches to a paid model. For streaming, HTTP 429 is
        returned before audio starts.


        ### Language


        Set `language` to the language of `text`. If you omit it, the language
        is detected from `text`. Successful responses include
        `Content-Language`, the language the speech was generated in.


        ### Limits and request ID


        The rate limit is 30 requests per minute per workspace member.

        High demand can exceed the available capacity for speech generation. The
        service then returns HTTP 429 with `code=rate_limit_exceeded`. This
        response has no `Retry-After` header. Retry the request with exponential
        backoff. For streaming, the service returns HTTP 429 only before the
        response starts.


        Successful responses include `X-Request-Id`. Use this ID when you
        contact support about the request. For instant clones, completed
        requests automatically retain audio for request stitching when speech
        retention is allowed. Pass completed IDs in `previous_request_ids` or
        `next_request_ids` to keep continuity. Use up to three IDs per field in
        playback order, from the same workspace, voice, and model, within two
        hours. Finish reading a stream before reusing its ID. If context is
        unavailable, synthesis continues with its normal defaults. Stitching is
        unavailable when speech retention is disabled.
      operationId: generateModelSpeech
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateSpeechRequest'
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    $ref: '#/components/schemas/CreateSpeechResponseData'
          headers:
            X-Request-Id:
              description: >-
                The request identifier. Use it for support or as stitching
                context after generation completes.
              schema:
                type: string
            Content-Language:
              description: The language the speech was generated in.
              schema:
                type: string
        '400':
          description: Invalid request parameters
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    $ref: '#/components/schemas/StandardAPIError'
              examples:
                invalid_parameter:
                  summary: Unsupported language
                  value:
                    error:
                      code: invalid_parameter
                      message: language is not a supported language.
                      param: language
                      doc_url: null
                invalid_voice_id:
                  summary: Voice missing or inaccessible in the caller's workspace
                  value:
                    error:
                      code: invalid_parameter
                      message: Voice not found
                      param: voice_id
                      doc_url: null
                language_not_detected:
                  summary: Language omitted and not detected from text
                  value:
                    error:
                      code: invalid_parameter
                      message: >-
                        Could not detect a supported language in text. Set
                        language to the language of the text.
                      param: language
                      doc_url: null
                voice_expired:
                  summary: Professional voice clone over the workspace slot limit
                  value:
                    error:
                      code: voice_expired
                      message: >-
                        Professional voice clone 'voice-1' expired because this
                        workspace exceeded its professional voice clone slot
                        limit of 2. Purchase more professional voice clone
                        slots, or delete other professional voice clones to
                        bring the workspace within its limit, then try again.
                      param: null
                      doc_url: null
        '401':
          description: Authentication failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    $ref: '#/components/schemas/StandardAPIError'
              example:
                error:
                  code: unauthorized
                  message: API key or OAuth token required
                  param: null
                  doc_url: null
        '402':
          description: >-
            Payment required — `error.code` is one of: `usage_limit_reached`,
            `insufficient_credit`, `plan_upgrade_required`.
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    $ref: '#/components/schemas/StandardAPIError'
              examples:
                usage_limit_reached:
                  summary: >-
                    A workspace usage limit or an API key's credit limit was
                    reached
                  value:
                    error:
                      code: usage_limit_reached
                      message: >-
                        Usage limit reached. Ask a workspace administrator to
                        check your limit.
                insufficient_credit:
                  summary: Insufficient credits in the selected billing wallet
                  value:
                    error:
                      code: insufficient_credit
                      message: >-
                        Insufficient credits. Please upgrade your plan or
                        purchase additional credits.
                      param: null
                      doc_url: null
                plan_upgrade_required:
                  summary: OAuth speech requires a paid plan
                  value:
                    error:
                      code: plan_upgrade_required
                      message: >-
                        Professional voice speech through OAuth requires a paid
                        plan. Please upgrade your subscription.
                      param: null
                      doc_url: null
        '409':
          description: >-
            Conflict — `error.code` is one of: `voice_not_ready`,
            `voice_training_failed`.
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    $ref: '#/components/schemas/StandardAPIError'
              examples:
                voice_not_ready:
                  summary: Voice creation is not complete
                  value:
                    error:
                      code: voice_not_ready
                      message: The voice clone is not ready for inference.
                      param: null
                      doc_url: null
                voice_training_failed:
                  summary: Voice creation failed
                  value:
                    error:
                      code: voice_training_failed
                      message: The voice clone failed to train or design.
                      param: null
                      doc_url: null
        '429':
          description: Rate limit exceeded
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    $ref: '#/components/schemas/StandardAPIError'
              example:
                error:
                  code: rate_limit_exceeded
                  message: >-
                    Too many requests. Retry after the duration specified in the
                    Retry-After header.
                  param: null
                  doc_url: null
          headers:
            Retry-After:
              description: Seconds to wait before retrying
              schema:
                type: integer
        '502':
          description: >-
            Upstream dependency failed — the request did not complete and is
            safe to retry.
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    $ref: '#/components/schemas/StandardAPIError'
              example:
                error:
                  code: voice_provider_error
                  message: The upstream voice provider failed. Retry the request.
                  param: null
                  doc_url: null
        '503':
          description: >-
            Temporarily unavailable — the request did not complete and is safe
            to retry.
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    $ref: '#/components/schemas/StandardAPIError'
              example:
                error:
                  code: service_unavailable
                  message: Voice inference is temporarily busy. Retry the request.
                  param: null
                  doc_url: null
        '504':
          description: >-
            Upstream dependency timed out — the request did not complete and is
            safe to retry.
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    $ref: '#/components/schemas/StandardAPIError'
              example:
                error:
                  code: gateway_timeout
                  message: The upstream voice provider timed out. Retry the request.
                  param: null
                  doc_url: null
      security:
        - ApiKeyAuth: []
        - BearerAuth: []
components:
  schemas:
    CreateSpeechRequest:
      additionalProperties: false
      example:
        language: en
        text: Hello from HeyGen Voice.
        voice_id: <voice_id>
      properties:
        end_user_id:
          anyOf:
            - maxLength: 128
              minLength: 1
              pattern: ^\S+$
              type: string
            - type: 'null'
          default: null
          description: >-
            Stable, opaque end-user identifier in your application, scoped to
            the authenticated workspace. Use 1–128 non-whitespace characters
            without personal information. Used for usage attribution and abuse
            investigation; does not change billing, authorization, or rate
            limits.
          title: End User Id
          x-mcp-visible: false
        output_format:
          anyOf:
            - $ref: '#/components/schemas/SpeechOutputFormat'
            - type: 'null'
          default: null
          description: >-
            Optional audio output: encoding pcm (signed little-endian PCM16),
            mp3, ulaw, or alaw; mono only. sample_rate_hertz: 8000, 16000,
            22050, 24000, 44100, or 48000 for pcm/mp3 (default 44100); ulaw/alaw
            require 8000 (default). MP3 bitrate_bps: 32000/48000/64000 below
            32000 Hz (default 64000), or 64000/96000/128000/192000 at
            44100/48000 Hz (default 128000). Omit for the existing WAV file or
            SSE stream of base64 WAV parts. When supplied, /tts/stream returns
            raw audio bytes and does not support with_timestamps.
        model:
          default: heygen-voice-1
          description: >-
            heygen-voice-1: instant and professional voices.
            heygen-voice-1-turbo: instant voices at lower latency.
            heygen-voice-1-turbo-free: instant voices without charge, subject to
            per-user limits and shared capacity. No latency or availability
            guarantee. Requests rejected by a limit or capacity check return
            HTTP 429. Timeouts and service failures can return HTTP 500.
          enum:
            - heygen-voice-1
            - heygen-voice-1-turbo
            - heygen-voice-1-turbo-free
          title: Model
          type: string
        voice_id:
          description: Identifier of the voice used for speech synthesis.
          minLength: 1
          title: Voice Id
          type: string
        text:
          description: >-
            Text to synthesize. Instant voices accept caller-supplied IPA, such
            as <pron ipa="/ˈækmi/">Acme</pron>. Respelling cues are not
            supported. Unsupported IPA returns HTTP 400. Pronunciation requires
            an available pronunciation-capable model. Instant voices perform
            audio tags in square brackets, such as [laughs], [whispers], or
            [sad]; see
            https://developers.heygen.com/docs/voices/heygen-voice-speech#audio-tags
            for the supported tags. Bracketed text that is not a supported tag
            is usually not spoken; to have those words spoken, remove the square
            brackets. Professional voices do not perform audio tags.
            Professional voices accept <break time="Xs"/> pauses (seconds, up to
            5 per pause, e.g. <break time="0.5s"/>); other SSML, and break tags
            for an instant voice clone, are not supported.
          maxLength: 10000
          minLength: 1
          title: Text
          type: string
        apply_text_normalization:
          default: auto
          description: >-
            Text normalization rewrites numbers, currencies, dates, and other
            written forms as spoken words before synthesis. Applies to instant
            voices, including Turbo, and professional voices. on normalizes text
            in Arabic, Chinese, English, French, German, Hebrew, Hindi,
            Indonesian, Italian, Japanese, Korean, Portuguese, Russian, Spanish,
            and Vietnamese; text in any other language is spoken as written. off
            speaks all text as written. auto (default) lets HeyGen Voice decide
            and currently behaves as on. Pronunciation dictionaries, inline IPA,
            audio tags, and break tags are not affected.
          enum:
            - auto
            - 'on'
            - 'off'
          title: Apply Text Normalization
          type: string
          x-mcp-default: null
        pronunciation_dictionary:
          anyOf:
            - additionalProperties:
                maxLength: 512
                minLength: 3
                type: string
              maxProperties: 100
              propertyNames:
                maxLength: 128
                minLength: 1
              type: object
            - type: 'null'
          default: null
          description: >-
            Optional term-to-IPA dictionary, such as {"Acme": "/ˈækmi/"}. Use
            enclosing slashes for each IPA value. Matches whole terms without
            case sensitivity. Inline pronunciation takes precedence. Supports
            instant voices on heygen-voice-1 and heygen-voice-1-turbo when
            pronunciation is available. Omit expressiveness_boost to use 0.5, or
            supply a value from 0.0 to 1.0.
          title: Pronunciation Dictionary
        language:
          anyOf:
            - enum:
                - ar
                - be
                - bg
                - ca
                - cs
                - da
                - de
                - el
                - en
                - es
                - fa
                - fi
                - fr
                - he
                - hi
                - hr
                - hu
                - id
                - it
                - ja
                - ko
                - mk
                - ms
                - nl
                - pl
                - pt
                - ro
                - ru
                - sk
                - sl
                - sr
                - sv
                - ta
                - th
                - tl
                - tr
                - uk
                - vi
                - zh
              minLength: 1
              type: string
            - type: 'null'
          default: null
          description: >-
            Language of `text` as a lowercase ISO 639-1 code, such as `en` or
            `zh`. HeyGen Voice has no regional accents, so a regional tag such
            as `en-US` or `zh-HK` fails with `invalid_parameter`. Omit it to
            detect the language from `text`. A confident reading that matches
            the letters of `text` is used, and the request fails with
            `invalid_parameter` if HeyGen Voice does not speak that language.
            Otherwise the first of these that HeyGen Voice speaks is used: the
            language the voice was created in, if `text` is written in that
            language's script; a less certain reading that a second reading of
            `text` without its numbers and brand names agrees with; the usual
            language of the script `text` is mostly written in, such as English
            for Latin letters; and, only when that script has no usual language,
            the reading itself. If none of them applies, the request fails with
            `invalid_parameter`. The `Content-Language` response header names
            the language used.
          title: Language
        previous_request_ids:
          anyOf:
            - items:
                maxLength: 64
                minLength: 1
                pattern: ^[A-Za-z0-9_-]+$
                type: string
              maxItems: 3
              type: array
            - type: 'null'
          default: null
          description: >-
            Completed speech request IDs before this text, in playback order, up
            to three. Use X-Request-Id from completed batch or fully consumed
            streaming responses within two hours. Requests must use the same
            workspace, voice, and model. Instant clones only, including Turbo.
            Unavailable when speech retention is disabled. Only the last three
            seconds of context are used. Unavailable context falls back to
            normal synthesis.
          title: Previous Request Ids
          x-mcp-visible: false
        next_request_ids:
          anyOf:
            - items:
                maxLength: 64
                minLength: 1
                pattern: ^[A-Za-z0-9_-]+$
                type: string
              maxItems: 3
              type: array
            - type: 'null'
          default: null
          description: >-
            Completed speech request IDs after this text, in playback order, up
            to three. Use X-Request-Id from completed batch or fully consumed
            streaming responses within two hours. Requests must use the same
            workspace, voice, and model. Instant clones only, including Turbo.
            Unavailable when speech retention is disabled. Only the first three
            seconds of context are used. Unavailable context falls back to
            normal synthesis.
          title: Next Request Ids
          x-mcp-visible: false
        expressiveness_boost:
          anyOf:
            - maximum: 1
              minimum: 0
              type: number
            - type: 'null'
          default: null
          description: >-
            Expressiveness boost for instant voices, from 0.0 to 1.0. Omit for
            professional voices. Omitted values use 0.5 with pronunciation and
            1.0 otherwise. The boost is not applied when text contains an audio
            tag other than [pause].
          title: Expressiveness Boost
          x-mcp-default: null
        seed:
          anyOf:
            - maximum: 4294967295
              minimum: 0
              type: integer
            - type: 'null'
          default: null
          description: >-
            Optional best-effort deterministic generation seed for professional
            clones. Ignored for instant clones.
          title: Seed
        speed:
          anyOf:
            - maximum: 1.25
              minimum: 0.75
              type: number
            - type: 'null'
          default: null
          description: >-
            Speech speed multiplier for professional clones. Ignored for instant
            clones, including Turbo.
          title: Speed
        pitch_shift:
          anyOf:
            - maximum: 4
              minimum: -4
              type: number
            - type: 'null'
          default: null
          description: >-
            Pitch shift in semitones for professional clones. Ignored for
            instant clones.
          title: Pitch Shift
        pitch_variance:
          anyOf:
            - maximum: 2
              minimum: 0.5
              type: number
            - type: 'null'
          default: null
          description: >-
            Pitch variation multiplier for professional clones; 1.0 preserves
            the voice default. Ignored for instant clones.
          title: Pitch Variance
        with_timestamps:
          default: false
          description: Include character and word timings in the response.
          title: With Timestamps
          type: boolean
          x-mcp-visible: false
      required:
        - voice_id
        - text
      title: CreateSpeechRequest
      type: object
    CreateSpeechResponseData:
      properties:
        audio_url:
          description: URL of the generated audio file.
          title: Audio Url
          type: string
        duration:
          description: Duration of the generated audio in seconds.
          minimum: 0
          title: Duration
          type: number
        original_characters:
          anyOf:
            - items:
                $ref: '#/components/schemas/SpeechCharacterAlignment'
              type: array
            - type: 'null'
          default: null
          description: >-
            Start and end time of each written character, without pronunciation
            tags, in seconds from the start of the audio. Present only when
            `with_timestamps` is true.
          title: Original Characters
          x-mcp-visible: false
        original_words:
          anyOf:
            - items:
                $ref: '#/components/schemas/SpeechWordAlignment'
              type: array
            - type: 'null'
          default: null
          description: >-
            Word timings from original_characters. Present only when
            with_timestamps is true. Unicode word boundaries determine the
            words. Punctuation-only and whitespace-only segments are excluded.
            Dictionary segmentation is not used for Chinese, Japanese, or Thai.
          title: Original Words
          x-mcp-visible: false
      required:
        - audio_url
        - duration
      title: CreateSpeechResponseData
      type: object
    StandardAPIError:
      type: object
      properties:
        code:
          type: string
          description: Machine-readable error code
          example: invalid_parameter
        message:
          type: string
          description: Human-readable error message
          example: Video not found
        param:
          type:
            - string
            - 'null'
          description: Which request field caused the error
        doc_url:
          type:
            - string
            - 'null'
          description: Link to error documentation
        errors:
          type: array
          description: >-
            Per-item error details for batch/multi-node failures (e.g. graph
            compilation errors by node).
          items:
            $ref: '#/components/schemas/StandardAPIErrorDetail'
        request_id:
          type: string
          description: >-
            Request identifier, also returned in the X-HeyGen-Request-Id
            response header. Include it when contacting support.
          example: 8c4f0b9e1d2a4f6b9e3c7a1d5f2b8e40
      required:
        - code
        - message
    SpeechOutputFormat:
      additionalProperties: false
      properties:
        encoding:
          enum:
            - pcm
            - mp3
            - ulaw
            - alaw
          title: Encoding
          type: string
        sample_rate_hertz:
          anyOf:
            - type: integer
            - type: 'null'
          default: null
          title: Sample Rate Hertz
        bit_depth:
          anyOf:
            - type: integer
            - type: 'null'
          default: null
          title: Bit Depth
        num_channels:
          default: 1
          title: Num Channels
          type: integer
        bitrate_bps:
          anyOf:
            - type: integer
            - type: 'null'
          default: null
          title: Bitrate Bps
      required:
        - encoding
      title: SpeechOutputFormat
      type: object
    SpeechCharacterAlignment:
      properties:
        text:
          description: Character represented by this alignment entry.
          maxLength: 1
          minLength: 1
          title: Text
          type: string
        start_time:
          description: Character start time in seconds.
          minimum: 0
          title: Start Time
          type: number
        end_time:
          description: Character end time in seconds.
          minimum: 0
          title: End Time
          type: number
      required:
        - text
        - start_time
        - end_time
      title: SpeechCharacterAlignment
      type: object
    SpeechWordAlignment:
      properties:
        text:
          description: Word text from the character alignment.
          minLength: 1
          title: Text
          type: string
        start_time:
          description: Earliest character start time, in seconds from the audio start.
          minimum: 0
          title: Start Time
          type: number
        end_time:
          description: Latest character end time, in seconds from the audio start.
          minimum: 0
          title: End Time
          type: number
      required:
        - text
        - start_time
        - end_time
      title: SpeechWordAlignment
      type: object
    StandardAPIErrorDetail:
      type: object
      properties:
        code:
          type: string
          description: Machine-readable error code
          example: unknown_node_type
        message:
          type: string
          description: Human-readable error message
          example: Unknown node type
        node_id:
          type: string
          description: Graph node id this error pertains to, if applicable
        port:
          type: string
          description: Port name on the node this error pertains to, if applicable
        path:
          type: string
          description: Field path within the item this error pertains to, if applicable
      required:
        - code
        - message
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: x-api-key
      description: HeyGen API key. Obtain from your HeyGen dashboard.
    BearerAuth:
      type: http
      scheme: bearer
      description: OAuth2 bearer token.

````

This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.