"""Make the ElevenLabs sound effects listed in settings (post.audio.sfx) into post.audio.sfx_dir.
Run by .github/workflows/sfx.yml with ELEVENLABS_API_KEY; sounds already there are kept."""
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline.post.sfx import generate  # noqa: E402

a = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8"))["post"]["audio"]
for p in generate(a["sfx"], ROOT / a.get("sfx_dir", "assets/sfx"), os.environ["ELEVENLABS_API_KEY"]):
    print(p.relative_to(ROOT))
