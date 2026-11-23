"""Print the reply to the founder's `publish`: where the episode and the Shorts will go, from the settings and the
secrets that are present (pipeline/publish/release_status.py).

Usage: python scripts/release_plan.py <week>
The `approve` workflow passes each secret as a flag ("1" when it is set), never its value."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    from pipeline.publish.release_status import publish_reply
    cfg = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8"))
    print(publish_reply(cfg, sys.argv[1]))
