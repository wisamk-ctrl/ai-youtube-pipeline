"""Compare what the presenter actually said (Whisper's transcript.srt) with the approved script.

Lists, with timestamps: words said but not in the script (repeats, insertions), script words
replaced by something else (likely mispronunciations), and script words that went missing.
Usage: python scripts/transcript_report.py output/<week>  →  prints Markdown
"""

import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.post.subtitles import norm_word  # noqa: E402
from pipeline.post.visuals import read_srt  # noqa: E402
from pipeline.script_format import spoken_text  # noqa: E402


def ts(x: float) -> str:
    return f"{int(x // 60)}:{int(x % 60):02d}"


def main(week_dir: str) -> str:
    d = Path(week_dir)
    heard = []
    for a, b, text in read_srt(d / "transcript.srt"):
        words = text.split()
        for k, w in enumerate(words):
            heard.append((a + (b - a) * k / max(1, len(words)), w))
    script = spoken_text((d / "script.md").read_text(encoding="utf-8")).split()
    sm = SequenceMatcher(None, [norm_word(w) for w in script], [norm_word(w) for _, w in heard], autojunk=False)
    inserted, replaced, missing = [], [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "insert":
            inserted.append((heard[j1][0], " ".join(w for _, w in heard[j1:j2])))
        elif op == "replace":
            replaced.append((heard[j1][0], " ".join(script[i1:i2]), " ".join(w for _, w in heard[j1:j2])))
        elif op == "delete":
            t = heard[min(j1, len(heard) - 1)][0] if heard else 0
            missing.append((t, " ".join(script[i1:i2])))
    # Repeats: the same 2–4 heard words twice in a row.
    repeats = []
    hw = [norm_word(w) for _, w in heard]
    for n in (4, 3, 2):
        for k in range(len(hw) - 2 * n + 1):
            if hw[k:k + n] == hw[k + n:k + 2 * n] and all(hw[k:k + n]):
                repeats.append((heard[k][0], " ".join(w for _, w in heard[k:k + n])))
    seen, uniq = set(), []
    for t, p in repeats:
        key = round(t)
        if key not in seen:
            seen.add(key)
            uniq.append((t, p))
    out = [f"## Transcript vs approved script · {d.name}", "",
           f"Script words {len(script)} · heard words {len(heard)} · match {sm.ratio():.0%}", "",
           f"### Repeated back to back ({len(uniq)})"] + [f"- {ts(t)} «{p}»" for t, p in sorted(uniq)]
    out += ["", f"### Said but not in the script ({len(inserted)})"] + [f"- {ts(t)} «{w}»" for t, w in inserted]
    out += ["", f"### Script word heard as something else ({len(replaced)}) — mispronunciation or transcription"]
    out += [f"- {ts(t)} script «{s}» → heard «{h}»" for t, s, h in replaced]
    out += ["", f"### In the script but not heard ({len(missing)})"] + [f"- {ts(t)} «{w}»" for t, w in missing]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    print(main(sys.argv[1]))
