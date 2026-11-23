"""Where a release goes, worked out from the settings and from which secrets are present.

Every message that tells the founder where an episode or a Short is going is built from here, and
`social.posters` reads the same table of secrets, so a message cannot name a platform the code will skip
(2026-11-23: the `publish` reply named only LinkedIn and Facebook, and the "ready" message named every
configured platform, connected or not).

Standard library only: the `approve` workflow runs this without installing the pipeline.
"""
from __future__ import annotations

import os
from typing import Any, Callable

PLATFORMS = ("youtube", "instagram", "facebook", "tiktok", "linkedin")
NAMES = {"youtube": "YouTube", "instagram": "Instagram", "facebook": "Facebook", "tiktok": "TikTok", "linkedin": "LinkedIn"}
NEEDS = {"youtube": ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"),
         "instagram": ("INSTAGRAM_TOKEN",),
         "facebook": ("FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_TOKEN"),
         "tiktok": ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN"),
         "linkedin": ("LINKEDIN_TOKEN",)}
RELAY = ("COMPOSIO_API_KEY", "BUFFER_API_KEY")       # either carries Instagram and the Facebook Page (social.relay)
RELAYED = ("instagram", "facebook")
ALERTS = ("WHATSAPP_PHONE", "CALLMEBOT_APIKEY")      # WhatsApp alerts to the founder (scripts/notify.py)

Have = Callable[[str], bool]


def in_env(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def shorts(cfg: dict[str, Any], have: Have = in_env) -> dict[str, str]:
    """Per configured platform, what happens to a Short: auto, relay (through Composio or Buffer), drafts (the
    founder's TikTok drafts: he posts it), or off (secrets missing). The rule `social.posters` applies."""
    s = cfg.get("social", {})
    relay = any(have(k) for k in RELAY)
    out = {}
    for p in s.get("platforms", PLATFORMS):
        if all(have(k) for k in NEEDS[p]):
            out[p] = "drafts" if p == "tiktok" and s.get("tiktok_mode", "inbox") == "inbox" else "auto"
        else:
            out[p] = "relay" if relay and p in RELAYED else "off"
    return out


def episode(cfg: dict[str, Any], have: Have = in_env) -> dict[str, str]:
    """What happens to the full episode: auto, link (a link post, not the video), off, or none (the code never
    sends the episode there). The rule `run_pipeline.phase_announce` applies."""
    relay = any(have(k) for k in RELAY)
    return {"youtube": "auto" if all(have(k) for k in NEEDS["youtube"]) else "off",
            "linkedin": "auto" if all(have(k) for k in NEEDS["linkedin"]) else "off",
            "facebook": "auto" if all(have(k) for k in NEEDS["facebook"]) else "link" if relay else "off",
            "instagram": "none", "tiktok": "none"}


def alerts_on(have: Have = in_env) -> bool:
    return all(have(k) for k in ALERTS)


def _join(names: list[str]) -> str:
    return ", ".join(names[:-1]) + (" and " if len(names) > 1 else "") + names[-1] if names else ""


def channels_line(cfg: dict[str, Any], have: Have = in_env) -> str:
    """Where a Short goes, for the messages that ask the founder to approve one: only the connected platforms,
    TikTok named as drafts while it is, and the ones that will be skipped named as skipped."""
    st = shorts(cfg, have)
    live = _join([NAMES[p] for p, v in st.items() if v in ("auto", "relay")])
    drafts = any(v == "drafts" for v in st.values())
    off = _join([NAMES[p] for p, v in st.items() if v == "off"])
    line = (live + (", and to your TikTok drafts" if live else "your TikTok drafts")) if drafts else live
    if not line:
        return "nowhere yet (no platform is connected: " + off + ")"
    return line + (f" (not connected, so skipped: {off})" if off else "")


def publish_reply(cfg: dict[str, Any], week: str, have: Have = in_env) -> str:
    """The reply to the founder's `publish` on the Review issue."""
    ep, st = episode(cfg, have), shorts(cfg, have)
    privacy = cfg.get("publish", {}).get("privacy", "private")
    say_ep = {"auto": "the episode as a video, automatically", "off": "**not connected**, so nothing is posted",
              "link": "a link post, not the video (the Page has no token of its own)"}
    say_short = {"auto": "automatically", "relay": "through Composio", "drafts": "to your drafts, for you to post",
                 "off": "**not connected**, skipped"}
    lines = [f"Publishing `{week}`: uploading to YouTube as {privacy} now, public at the Sunday 17:00 Gulf slot."
             if ep["youtube"] == "auto" else f"`{week}`: YouTube is **not connected**, so the episode cannot be uploaded.",
             "", "**The episode, once it is public**",
             f"- LinkedIn: {say_ep[ep['linkedin']]}", f"- Facebook: {say_ep[ep['facebook']]}",
             "- Instagram and TikTok: the full episode is never posted there, only Shorts",
             "- WhatsApp Channel: by hand. A \"WhatsApp kit\" issue brings you the text to paste",
             "", "**Breaking Shorts** (the weekly episode's own Shorts are not posted: founder 2026-11-18 and 2026-11-23)"]
    lines += [f"- {NAMES[p]}: {say_short[v]}" for p, v in st.items()]
    if not alerts_on(have):
        lines += ["", "WhatsApp alerts to your phone are off: the `WHATSAPP_PHONE` and `CALLMEBOT_APIKEY` secrets are not set."]
    return "\n".join(lines)
