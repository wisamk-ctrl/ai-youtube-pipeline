#!/usr/bin/env python3
"""Is Ollama reachable, what is installed, and does the configured model answer in JSON?"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.config import load_settings  # noqa: E402

cfg = load_settings()["radar"]["extraction"]
url = os.environ.get("OLLAMA_HOST", cfg["ollama_url"]).rstrip("/")
url = url if url.startswith("http") else "http://" + url
model = cfg["ollama_model"]

try:
    tags = requests.get(f"{url}/api/tags", timeout=5).json().get("models", [])
except requests.RequestException as exc:
    sys.exit(f"Ollama not reachable at {url}: {exc}\nStart it with `ollama serve` (or open the Ollama app).")

print(f"Ollama at {url}: {len(tags)} models installed")
for m in tags:
    size = m.get("size", 0) / 1e9
    d = m.get("details", {})
    print(f"  {m['name']:28} {size:5.1f} GB  {d.get('parameter_size', ''):>6}  {d.get('family', '')}")

if not any(m["name"] == model or m["name"].split(":")[0] == model for m in tags):
    sys.exit(f"\nConfigured ollama_model '{model}' is not installed. Set radar.extraction.ollama_model to one of the names above, "
             f"or run: ollama pull {model}")

t0 = time.time()
r = requests.post(f"{url}/api/chat", json={
    "model": model, "stream": False, "options": {"temperature": 0},
    "format": {"type": "object", "properties": {"org": {"type": "string"}, "kind": {"type": "string"}}, "required": ["org", "kind"]},
    "messages": [{"role": "user", "content": "Which organisation released the Falcon models? Answer as JSON with org and kind."}],
}, timeout=120)
r.raise_for_status()
answer = r.json()["message"]["content"]
print(f"\n{model} answered in {time.time() - t0:.1f}s: {answer}")
try:
    json.loads(answer)
    print("JSON-schema mode works: ready for `make extract-test`")
except json.JSONDecodeError:
    sys.exit("The model did not return valid JSON; try a larger model (qwen2.5:7b or qwen3:8b).")
