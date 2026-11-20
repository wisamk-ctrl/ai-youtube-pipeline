# Security — AI This Week

Written 2026-11-20 after the founder asked for a layer against account hijacking.

## The threat

YouTube channels are rarely taken by a guessed password. The common route is a fake sponsorship email with an
attachment that steals the browser's session cookies, then a rename and scam uploads within hours. 2FA alone
does not stop a stolen session. Shortening session life and limiting who can act does.

## Done in the repo (2026-11-20)

| Layer | What |
|---|---|
| Approval commands | `approve`, `publish`, breaking and inbox commands act only when the repo owner writes them; radar commands only for owner/member/collaborator. |
| `main` branch | Protected: no force-push, no deletion. |
| GitHub Actions | Every action pinned to a commit SHA, so a moved tag cannot run new code with our secrets (test: `tests/test_ci_workflows.py`). |
| Daily integrity check | `scripts/integrity.py`, 06:23 Gulf: channel renamed, handle or description changed, an upload the pipeline did not make, a video deleted or hidden → a "Security: channel changed" issue (and WhatsApp once CallMeBot is set). |
| Secrets | Only in GitHub Actions secrets and local gitignored files; never in the repo. |

## Founder checklist (about 30 minutes; only you can do these)

1. **Google account that owns the channel:** sign in with a **passkey**, and turn on **Advanced Protection**
   (g.co/advancedprotection). It blocks most cookie-theft and phishing takeovers.
2. **YouTube Studio → Settings → Permissions:** remove anyone who does not need access; nobody else as Owner.
3. **Google account → Security → Your devices:** sign out devices you do not recognise.
4. **GitHub:** a passkey or security key as 2FA; review Settings → Applications and personal access tokens;
   delete what you do not use.
5. **Meta, TikTok, LinkedIn, the partnerships Gmail:** 2FA by authenticator app or passkey, not SMS.
6. **Sponsorship emails:** never open attachments or "download our brief" links on the Mac that is signed in to
   YouTube. Read them on the phone or ask for the brief as text.
7. **WhatsApp alerts:** activate CallMeBot from your phone and add `WHATSAPP_PHONE` and `CALLMEBOT_APIKEY` as repo
   secrets, so the integrity alert reaches you within minutes rather than by email.

## If the alert fires

Sign in to YouTube Studio from a clean device. Remove unknown managers. Google account → Security → sign out of
all other sessions. Change the password. Then use YouTube's hacked-channel form (support.google.com/youtube,
"My channel was hacked"). Revoke and re-issue the pipeline's YouTube refresh token (`YOUTUBE_REFRESH_TOKEN`).

## Known gaps

- The YouTube API does not show managers or sign-ins; only the founder's own account protection covers those.
- The repo is public: workflows and code are visible. Secrets are not.
- Token scopes (YouTube, LinkedIn, TikTok) are as broad as the publishing needs; rotation dates are not tracked yet.
