"""Draft a breaking-news Short from what the news watch flagged (pipeline/breaking.py).

Prints the new folder name (reviewed/<name>/) on the last line, or nothing. Needs ANTHROPIC_API_KEY."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    import anthropic
    from pipeline import breaking
    from pipeline.config import load_settings
    from pipeline.ingestion import news_watch
    week = breaking.run(load_settings(), news_watch.load(), anthropic.Anthropic())
    print(f"BREAKING={week or ''}")
