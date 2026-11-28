# Shorts, Reels and TikTok — on the platforms' own APIs

YouTube, TikTok and LinkedIn post on the platforms' own APIs. Instagram and the Facebook Page have no token
of their own (Meta's developer sign-up is blocked), so they go through Composio, or Buffer if that is set
(`social.relay`); this replaces "no third-party posting service" (founder, 2026-11-13). Code:
`pipeline/publish/social.py`, `scripts/social.py`, `scripts/connect.py`; workflows `social` (hourly) and `connect`.

## What goes where (checked against the code and the repository's secrets, 2026-11-23)
What is connected is worked out in one place, `pipeline/publish/release_status.py`, from the settings and the
secrets that are set. The reply to `publish`, the "ready to check" message and `social.posters` all read it.

| Platform | Full episode | Shorts (weekly and breaking) | State on 2026-11-23 |
|---|---|---|---|
| YouTube | Uploaded private, public at the Sunday slot | Automatic | Connected |
| LinkedIn | Video, once the episode is public | Automatic | Connected |
| Facebook Page | A link post through Composio. A video only with `FACEBOOK_PAGE_ID` and `FACEBOOK_PAGE_TOKEN` | Reel through Composio | No Page token. No Reel has posted yet |
| Instagram | Never | Reel through Composio | No token. One Reel has posted (W46-en #1) |
| TikTok | Never | Through Buffer, public, AI label on (`tiktok_via: buffer`, 2026-11-25); to the founder's drafts while TikTok is not connected in Buffer | Connect @aithisweek in Buffer |
| WhatsApp (your status) | By hand, from the "WhatsApp kit" issue | By hand, same issue | The AI This Week WhatsApp Channel is no longer promoted (founder 2026-11-28) |
| WhatsApp alerts to the founder | | | Off: `WHATSAPP_PHONE` and `CALLMEBOT_APIKEY` are not set |

A platform that is not connected is skipped, and now says so: a warning in the log, a `⏭️` line in the run
summary, and a note on the queue entry that the "posted" comment shows. The run still passes.

Shorts captions on YouTube, LinkedIn and Facebook end with "Follow us: Instagram · TikTok" (`social.follow`,
founder 2026-11-28; the WhatsApp Channel link was removed). Instagram and TikTok captions show no clickable links.

## How it runs each week
1. The edit makes three vertical clips (`output/<week>/shorts/`).
2. `social` with action **plan**, week `<week>`: the clips go to a public release `social-<week>`
   (Instagram fetches from that URL) and into `data/social_queue.json`, due Mon/Wed/Fri 15:00 UTC.
3. They wait for your OK: `social` action **approve**, week `<week>`.
4. Every hour `social` posts what is approved and due, on each connected platform, and records the
   result in the queue. A failed platform is retried next hour (3 tries), the others are not reposted.

TikTok: until TikTok audits our app it rejects direct posts, so each Short goes to your TikTok **drafts**
(`social.tiktok_mode: inbox`, founder 2026-11-20). Open it in the TikTok app, turn on the AI label, paste the
caption and post. Apply for the audit in the TikTok developer portal; then set `tiktok_mode: direct`.

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

## Facebook Page, Instagram and WhatsApp (founder 2026-11-18)

**What posts where, automatically**
- Shorts (weekly and breaking): YouTube Shorts, Instagram Reels, **Facebook Page Reels**, TikTok, LinkedIn.
- Episode: YouTube, then native video on LinkedIn (`phase_announce`). On the Facebook Page it is native video
  only with a Page token; without one it is a link post through Composio (the case today).
- WhatsApp: no official API posts to a personal status or a Channel. The hourly "WhatsApp kit" issue
  (`scripts/channel.py`) hands the founder the clip and caption; the last tap is his.

**One-time setup (founder, about 30 minutes)**
1. Instagram: Settings → Account type → switch to **Professional** (Creator or Business).
2. Facebook: create the Page "AI This Week", then in Instagram link the account to that Page.
3. developers.facebook.com → Create app → type **Business**. Add two products:
   - **Facebook Login for Business**: valid OAuth redirect URI `https://github.com/wisamk-ctrl/ai-youtube-pipeline`.
   - **Instagram** → "API setup with Instagram login": same redirect URI; add the Instagram account as a tester and accept the invite in Instagram.
   Keep the app in Development mode: as its admin you can post to your own Page and account without App Review.
4. GitHub → Settings → Secrets → Actions: `META_APP_ID`, `META_APP_SECRET` (App settings → Basic),
   `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET` (Instagram → API setup).
5. Run the `connect` workflow with `links`, open each link from the "Connect accounts" issue, then run
   `connect` with `facebook` / `instagram` and the address the browser landed on. `check` confirms both.
