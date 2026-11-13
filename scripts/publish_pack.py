"""A hand-upload pack for one week: everything YouTube Studio, Instagram and TikTok ask for, in one folder.

    python scripts/publish_pack.py output/<week> <dest>

<dest>/ holds: video (the 4K master, else the 1080p cut), thumbnail, captions.srt, youtube.txt (title,
description, tags, settings to tick), and shorts/ (each vertical clip with a caption.txt for Shorts /
Reels / TikTok). Nothing is uploaded: the founder drags the files in (soft launch, 2026-11-13).
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.config import load_settings  # noqa: E402
from pipeline.language import apply_language, week_language  # noqa: E402
from pipeline.publish import description as desc  # noqa: E402
from pipeline.publish.youtube_upload import caption_file, thumbnail_file  # noqa: E402


def main(out_dir: Path, dest: Path) -> None:
    cfg = apply_language(load_settings(), out_dir.name)
    lang = week_language(out_dir.name)
    en = lang == "en"
    p = cfg["publish"]
    dest.mkdir(parents=True, exist_ok=True)
    plan = json.loads((out_dir / "plan.json").read_text(encoding="utf-8"))
    items = json.loads((out_dir / "items.json").read_text(encoding="utf-8"))
    sources = desc.pick_sources(out_dir, plan, items)
    sections, duration = desc.load_sections(out_dir, cfg)
    script = (out_dir / "script.md").read_text(encoding="utf-8") if (out_dir / "script.md").exists() else None
    cred = out_dir / "credits.json"
    credits = json.loads(cred.read_text(encoding="utf-8")) if cred.exists() else []
    text = desc.build_description(plan, sources, cfg, sections=sections, duration=duration, script=script,
                                  credits=credits, lang=lang)
    title = desc.clean(plan.get("episode_title_en") if en else plan["episode_title_ar"])[: desc.TITLE_LIMIT]
    tags = p.get("tags_en" if en else "tags", [])

    masters = sorted(out_dir.glob("final_*p.mp4"), key=lambda f: int(f.stem.split("_")[1][:-1]), reverse=True)
    video = next((f for f in (*masters, out_dir / "final_subtitled.mp4") if f.exists()), None)
    if video is None:
        sys.exit(f"no finished video in {out_dir}")
    shutil.copy(video, dest / f"{out_dir.name}{'-4k' if masters else ''}.mp4")
    if (t := thumbnail_file(out_dir)):
        shutil.copy(t, dest / f"thumbnail{t.suffix}")
    if (c := caption_file(out_dir)):
        shutil.copy(c, dest / f"captions-{lang}.srt")

    (dest / "youtube.txt").write_text("\n".join([
        "YouTube Studio → Create → Upload videos → pick the .mp4",
        "", "TITLE", title, "", "DESCRIPTION (paste as is)", text, "", "TAGS (Show more → Tags)", ", ".join(tags), "",
        "SETTINGS",
        "- Thumbnail: upload thumbnail file (custom thumbnails need a phone-verified channel)",
        "- Audience: No, it's not made for kids",
        "- Show more → Altered or synthetic content: YES (the presenter is an AI digital twin)",
        f"- Show more → Language: {'English' if en else 'Arabic'} · Category: Science & Technology",
        f"- Subtitles → Upload file → With timing → captions-{lang}.srt",
        "- Visibility: Unlisted (soft launch: only people with the link)",
    ]) + "\n", encoding="utf-8")

    sj = out_dir / "shorts" / "shorts.json"
    if sj.exists():
        (dest / "shorts").mkdir(exist_ok=True)
        tags_line = " ".join(["#Shorts", *p.get("hashtags_en" if en else "hashtags", [])])
        for n, s in enumerate(json.loads(sj.read_text(encoding="utf-8")), 1):
            src = out_dir / "shorts" / Path(s.get("file") or s.get("path") or f"short_{n:02d}.mp4").name
            if not src.exists():
                continue
            shutil.copy(src, dest / "shorts" / f"short_{n:02d}.mp4")
            note = desc.DISCLOSURE_EN if en else desc.DISCLOSURE_AR
            (dest / "shorts" / f"short_{n:02d}.txt").write_text(
                f"{desc.clean(s.get('title', ''))}\n\n{'Full episode on YouTube: link in bio' if en else 'الحلقة الكاملة على يوتيوب: الرابط بالبايو'}"
                f"\n\n{note}\n\n{tags_line}\n", encoding="utf-8")
    print(f"pack → {dest}: " + ", ".join(sorted(f.name for f in dest.rglob('*') if f.is_file())))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
