"""One-click account connection for the publishing pipeline (no OAuth Playground, no local script).

    python scripts/connect.py links                 → the sign-in link for every platform whose app is set up
    python scripts/connect.py exchange <platform> <code or the whole address the sign-in ended on>

`exchange` turns the one-time code into the long-lived token and stores it as a repository secret
(needs SECRETS_PAT), then reads the account back so you can see it is the right one.
Platforms: youtube, instagram, tiktok. The code is single-use and expires within minutes, so it is
harmless once exchanged even though a workflow input shows it.
"""

import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlparse

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.publish.social import store_secret  # noqa: E402

GOOGLE_SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.force-ssl"
GOOGLE_REDIRECT = "http://localhost"   # the browser shows "can't connect"; the code is in its address bar
IG_SCOPES = "instagram_business_basic,instagram_business_content_publish"
TT_SCOPES = "user.info.basic,video.publish,video.upload"


def redirect() -> str:
    return os.environ.get("SOCIAL_REDIRECT_URI") or f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', '')}"


def links() -> str:
    out = ["## Connect the show's accounts", "",
           "Click a link, sign in as the show's account, allow. Your browser then lands on a page "
           "(for YouTube a \"can't connect\" page, that is expected). **Copy the whole address from the address bar**, "
           "then run the `connect` workflow with that platform and paste the address as `code`.", ""]
    e = os.environ
    if e.get("GOOGLE_CLIENT_ID"):
        out.append("- **YouTube** (pick the AI This Week channel): https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": e["GOOGLE_CLIENT_ID"], "redirect_uri": GOOGLE_REDIRECT, "response_type": "code",
            "scope": GOOGLE_SCOPES, "access_type": "offline", "prompt": "consent select_account"}, quote_via=quote))
    if e.get("INSTAGRAM_APP_ID"):
        out.append("- **Instagram**: https://www.instagram.com/oauth/authorize?" + urlencode({
            "client_id": e["INSTAGRAM_APP_ID"], "redirect_uri": redirect(), "response_type": "code",
            "scope": IG_SCOPES, "force_reauth": "true"}, quote_via=quote))
    if e.get("TIKTOK_CLIENT_KEY"):
        out.append("- **TikTok**: https://www.tiktok.com/v2/auth/authorize/?" + urlencode({
            "client_key": e["TIKTOK_CLIENT_KEY"], "redirect_uri": redirect(), "response_type": "code",
            "scope": TT_SCOPES, "state": "connect"}, quote_via=quote))
    missing = [p for p, k in (("YouTube", "GOOGLE_CLIENT_ID"), ("Instagram", "INSTAGRAM_APP_ID"),
                              ("TikTok", "TIKTOK_CLIENT_KEY")) if not e.get(k)]
    if missing:
        out += ["", f"Not set up yet (app keys missing): {', '.join(missing)}."]
    return "\n".join(out) + "\n"


def code_of(text: str) -> str:
    text = text.strip()
    if "code=" in text:
        text = parse_qs(urlparse(text).query).get("code", [text.split("code=", 1)[1].split("&")[0]])[0]
    return text.split("#")[0].strip()


def _json(r, who):
    try:
        data = r.json()
    except ValueError:
        data = {}
    if r.status_code >= 400 or "error" in data and not data.get("access_token"):
        sys.exit(f"{who}: HTTP {r.status_code}: {data or r.text[:300]}")
    return data


def exchange(platform: str, raw: str) -> None:
    code, e = code_of(raw), os.environ
    if platform == "youtube":
        d = _json(requests.post("https://oauth2.googleapis.com/token", timeout=60, data={
            "code": code, "client_id": e["GOOGLE_CLIENT_ID"], "client_secret": e["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": GOOGLE_REDIRECT, "grant_type": "authorization_code"}), "Google")
        if not d.get("refresh_token"):
            sys.exit("Google gave no refresh token: sign in again with the link (it asks for consent each time)")
        me = requests.get("https://www.googleapis.com/youtube/v3/channels", timeout=60,
                          params={"part": "snippet", "mine": "true"},
                          headers={"Authorization": f"Bearer {d['access_token']}"}).json().get("items", [])
        if not me:
            sys.exit("This Google identity has no YouTube channel: sign in again and pick the AI This Week channel")
        print(f"YouTube channel: {me[0]['snippet']['title']} ({me[0]['snippet'].get('customUrl', '')})")
        ok = store_secret("YOUTUBE_REFRESH_TOKEN", d["refresh_token"])
    elif platform == "instagram":
        short = _json(requests.post("https://api.instagram.com/oauth/access_token", timeout=60, data={
            "client_id": e["INSTAGRAM_APP_ID"], "client_secret": e["INSTAGRAM_APP_SECRET"],
            "grant_type": "authorization_code", "redirect_uri": redirect(), "code": code}), "Instagram")
        long = _json(requests.get("https://graph.instagram.com/access_token", timeout=60, params={
            "grant_type": "ig_exchange_token", "client_secret": e["INSTAGRAM_APP_SECRET"],
            "access_token": short["access_token"]}), "Instagram long-lived")
        me = requests.get("https://graph.instagram.com/me", timeout=60, params={
            "fields": "user_id,username,account_type", "access_token": long["access_token"]}).json()
        print(f"Instagram account: @{me.get('username')} ({me.get('account_type')})")
        ok = store_secret("INSTAGRAM_TOKEN", long["access_token"])
    elif platform == "tiktok":
        d = _json(requests.post("https://open.tiktokapis.com/v2/oauth/token/", timeout=60,
                                headers={"Content-Type": "application/x-www-form-urlencoded"}, data={
            "client_key": e["TIKTOK_CLIENT_KEY"], "client_secret": e["TIKTOK_CLIENT_SECRET"], "code": code,
            "grant_type": "authorization_code", "redirect_uri": redirect()}), "TikTok")
        me = requests.get("https://open.tiktokapis.com/v2/user/info/", timeout=60, params={"fields": "display_name"},
                          headers={"Authorization": f"Bearer {d['access_token']}"}).json()
        print(f"TikTok account: {me.get('data', {}).get('user', {}).get('display_name')}  scopes: {d.get('scope')}")
        ok = store_secret("TIKTOK_REFRESH_TOKEN", d["refresh_token"])
    else:
        sys.exit("platform: youtube | instagram | tiktok")
    if not ok:
        sys.exit("token obtained but not stored: add the SECRETS_PAT secret (see docs/SOCIAL.md)")
    print("Connected and stored.")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "links":
        print(links())
    elif len(sys.argv) == 4 and sys.argv[1] == "exchange":
        exchange(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
