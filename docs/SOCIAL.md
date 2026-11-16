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
In the app's permissions, keep **instagram_business_manage_comments** on: the daily inbox reads and answers comments with it.
No app review is needed while the only account is your own (the app stays in development mode).

### 3. TikTok
developers.tiktok.com → Manage apps → Connect an app → add products **Login Kit** and
**Content Posting API** (turn on Direct Post) → scopes `user.info.basic`, `video.upload`,
`video.publish` → redirect URI `https://github.com/wisamk-ctrl/ai-youtube-pipeline` →
copy **Client key** and **Client secret** into `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`.
Submit the app for review when you can (it lifts the private-only limit).

### 3b. LinkedIn (posts on your own profile)
linkedin.com/developers/apps → Create app (it asks for a company page: pick or create one; posting still goes
to your own profile) → Products: add **Share on LinkedIn** and **Sign In with LinkedIn using OpenID Connect**
→ Auth → Authorized redirect URLs: `https://github.com/wisamk-ctrl/ai-youtube-pipeline` → copy **Client ID**
and **Primary Client Secret** into `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`.
LinkedIn gives a personal app no refresh token: the sign-in lasts 60 days. The Saturday check opens a
"Show at risk" note 10 days before it ends; reconnecting takes a minute.

### 4. Connect (each platform, about a minute)
Actions → **connect** → Run workflow → platform **links**. The sign-in links appear on the
**Connect accounts** issue. Click one, sign in as the show's account, allow; copy the whole address
the browser lands on (for YouTube a "can't connect" localhost page — expected), then
Actions → **connect** → platform `youtube|instagram|tiktok`, paste it as **code**. The run prints the
account it connected, so you can see it is the right one.

## The daily comment inbox
Every morning (09:13 Gulf) the `inbox` workflow reads new comments, sorts them and drafts replies, then opens an
**Inbox: <date>** issue (GitHub e-mails it to you). Nothing substantive is posted until you answer that issue:

    approve 3 5        post the drafts numbered 3 and 5
    approve all        post every draft still waiting
    edit 3: your text  post your own words under comment 3
    skip 4             leave comment 4 unanswered

You can answer from the GitHub app or by replying to the e-mail. Only the repository owner's comment counts.

| Platform | Read comments | Reply | Like a comment |
|---|---|---|---|
| YouTube | yes | yes, after your approval | not offered to apps: the issue lists links |
| Instagram | yes, once connected | yes, after your approval | not offered to apps: the issue lists links |
| LinkedIn (your profile) | no: LinkedIn has closed that permission | no | no: the issue links your recent posts |
| TikTok | no: there is no comment access for a posting app | no | no: the issue links your recent posts |

- Positive comments are listed with one-tap links to like. `inbox.auto_thanks: true` in `config/settings.yaml`
  also posts a short fixed thank-you under them on YouTube and Instagram (off by default).
- A piece of feedback about the show that three different viewers raise is written to `docs/LESSONS.md`.
- The repository is public, so the Inbox issues are public too. The comments in them are already public
  on the platforms; the drafts are not until you approve them.

## The quick way to connect LinkedIn and Instagram (no address to copy)
The sign-in link ends on a GitHub page, and GitHub can drop the code from the address bar (it did on
2026-11-16). Both platforms can hand you the token directly instead:

- **LinkedIn:** linkedin.com/developers/tools/oauth/token-generator → pick your app → tick `openid`,
  `profile`, `w_member_social` → Request access token → sign in and allow → copy the token into a repository
  secret named `LINKEDIN_TOKEN`. Add a second secret `LINKEDIN_TOKEN_UNTIL` with the date 60 days ahead
  (YYYY-MM-DD) so the Saturday check reminds you to renew it.
- **Instagram:** in your Meta app → Instagram → API setup with Instagram login → next to your account,
  Generate token → copy it into a repository secret named `INSTAGRAM_TOKEN`. The pipeline keeps it fresh.

Then Actions → **connect** → platform **check**: it replies on the Connect accounts issue with the
account each saved sign-in reaches.
