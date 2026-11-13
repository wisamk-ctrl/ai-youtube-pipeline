# Shorts, Reels and TikTok — on the platforms' own APIs

No third-party posting service (founder, 2026-11-13). Code: `pipeline/publish/social.py`,
`scripts/social.py`, `scripts/connect.py`; workflows `social` (hourly) and `connect`.

## How it runs each week
1. The edit makes three vertical clips (`output/<week>/shorts/`).
2. `social` with action **plan**, week `<week>`: the clips go to a public release `social-<week>`
   (Instagram fetches from that URL) and into `data/social_queue.json`, due Mon/Wed/Fri 15:00 UTC.
3. They wait for your OK: `social` action **approve**, week `<week>`.
4. Every hour `social` posts what is approved and due, on each connected platform, and records the
   result in the queue. A failed platform is retried next hour (3 tries), the others are not reposted.

TikTok: until TikTok audits our app, posts are **private** (`SELF_ONLY`). Open each in the TikTok
app → ··· → Privacy → Everyone. Apply for the audit in the TikTok developer portal to lift it.

## One-time setup (founder)

### 0. A key that lets the workflows store tokens — `SECRETS_PAT`
GitHub → Settings → Developer settings → Fine-grained tokens → Generate:
repository **ai-youtube-pipeline** only, permission **Secrets: Read and write**, expiry 1 year.
Save it as repository secret `SECRETS_PAT`. (Tokens are refreshed every run and written back with it.)

### 1. YouTube (Shorts) — reuses the Google app you already made
Google Cloud → Clients → your web client (`playground`) → Authorized redirect URIs → add `http://localhost`.

### 2. Instagram (Reels)
Instagram must be a **Professional** account (Business or Creator).
developers.facebook.com → My Apps → Create app → use case **Manage messaging & content on Instagram**
→ API setup with Instagram login → add your Instagram account as a tester and accept the invite
(instagram.com → Settings → App and websites → Tester invites) → Business login settings →
redirect URI `https://github.com/wisamk-ctrl/ai-youtube-pipeline` → copy the **Instagram app ID**
and **secret** into secrets `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`.
No app review is needed while the only account is your own (the app stays in development mode).

### 3. TikTok
developers.tiktok.com → Manage apps → Connect an app → add products **Login Kit** and
**Content Posting API** (turn on Direct Post) → scopes `user.info.basic`, `video.upload`,
`video.publish` → redirect URI `https://github.com/wisamk-ctrl/ai-youtube-pipeline` →
copy **Client key** and **Client secret** into `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`.
Submit the app for review when you can (it lifts the private-only limit).

### 4. Connect (each platform, about a minute)
Actions → **connect** → Run workflow → platform **links**. The sign-in links appear on the
**Connect accounts** issue. Click one, sign in as the show's account, allow; copy the whole address
the browser lands on (for YouTube a "can't connect" localhost page — expected), then
Actions → **connect** → platform `youtube|instagram|tiktok`, paste it as **code**. The run prints the
account it connected, so you can see it is the right one.
