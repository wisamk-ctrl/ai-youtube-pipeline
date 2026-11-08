"""
Voice lab: diagnose the episode's Arabic and test free voice tools, without HeyGen credits.

Run by .github/workflows/voice-lab.yml (GitHub's runners can reach the model hubs; the chat
sandbox cannot). Writes lab/report.md plus mp3 samples.

1. Diagnose: Whisper large-v3-turbo listens to the finished episode; every script word it heard
   differently, or heard with low confidence, is listed with its time — the candidates for
   "the Arabic is off" (founder, W45).
2. Candidates: the same test lines (the hard names, ADNOC in several spellings, plain Ammani
   sentences) are voiced by each free tool available:
     - edge  : Microsoft neural voices (ar-JO-TaimNeural, Jordanian male; ar-SA-HamedNeural)
     - xtts  : XTTS-v2 cloning the show's current voice from the original render
   plus the current HeyGen clone itself (cut from the episode) as the baseline.
3. Score: intelligibility (Whisper's character error rate against the text) and similarity to
   the show's voice (ECAPA speaker embedding, cosine). Licences are listed: a tool that cannot be
   used on a commercial channel is marked so.

Usage: python scripts/voice_lab.py <week dir> <out dir>
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
import traceback
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.post.subtitles import norm_word  # noqa: E402
from pipeline.script_format import spoken_text  # noqa: E402

LINES = [
    ("adnoc-1", "أدنوك وقّعت صفقة جديدة هالأسبوع."),
    ("adnoc-2", "آدنوك وقّعت صفقة جديدة هالأسبوع."),
    ("adnoc-3", "أد نوك وقّعت صفقة جديدة هالأسبوع."),
    ("adnoc-4", "شركة بترول أبوظبي الوطنية، أدنوك، وقّعت صفقة جديدة هالأسبوع."),
    ("names", "جي فورتي تو وهيوماين وسدايا وأنثروبيك، كلهم كانوا بالأخبار هالأسبوع."),
    ("claude", "أنثروبيك نزّلت تحديث جديد لكلود كود، وإنفيديا طلّعت معالج جديد."),
    ("ammani", "هسّا خلّينا نشوف شو صار هالأسبوع بعالم الذكاء الاصطناعي، وليش هاد بيهمّنا هون."),
    ("numbers", "الصفقة لخمس سنين، وفيها أكتر من مليارين وستمية مليون دولار."),
]

TOOLS = {
    "heygen-clone": "current show voice (HeyGen clone, from the render) — baseline; plan credits",
    "edge:ar-JO-TaimNeural": "Microsoft neural voice, Jordanian male. Free via the Edge read-aloud service "
                             "(terms unclear for commercial use); the same voice is licensed for commercial "
                             "use through Azure AI Speech (free tier 0.5M characters/month, then paid)",
    "edge:ar-SA-HamedNeural": "Microsoft neural voice, Saudi male (same terms as above)",
    "xtts": "XTTS-v2 (Coqui) cloning the show voice — Coqui Public Model License: NON-COMMERCIAL only",
    "knnvc:taim→show": "the Jordanian Microsoft reading (right pronunciation) converted into the show voice with "
                       "kNN-VC (MIT licence, open source), learning the voice from 5 min of the original render",
}


def sh(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def to_wav(src: Path, dest: Path, start: float | None = None, length: float | None = None) -> Path:
    cut = ["-ss", f"{start:.2f}", "-t", f"{length:.2f}"] if start is not None else []
    sh("ffmpeg", "-y", "-loglevel", "error", *cut, "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", str(dest))
    return dest


def whisper():
    from faster_whisper import WhisperModel
    return WhisperModel(os.environ.get("LAB_WHISPER", "large-v3-turbo"), device="cpu", compute_type="int8")


def words_of(model, wav: Path) -> list[tuple[float, float, str, float]]:
    segs, _ = model.transcribe(str(wav), language="ar", word_timestamps=True, vad_filter=True, beam_size=5)
    return [(w.start, w.end, w.word.strip(), w.probability) for s in segs for w in (s.words or [])]


def cer(ref: str, hyp: str) -> float:
    a = "".join(norm_word(w) for w in ref.split())
    b = "".join(norm_word(w) for w in hyp.split())
    if not a:
        return 0.0
    sm = SequenceMatcher(None, a, b, autojunk=False)
    return round(1 - sum(m.size for m in sm.get_matching_blocks()) / max(len(a), len(b)), 3)


# ── 1. Diagnose the episode ──────────────────────────────────────────────────

def diagnose(model, week: Path, out: Path) -> str:
    video = week / "final_subtitled.mp4"
    script = (week / "script.md").read_text(encoding="utf-8")
    wav = to_wav(video, out / "episode.wav")
    heard = words_of(model, wav)
    (out / "episode_words.json").write_text(json.dumps(heard, ensure_ascii=False), encoding="utf-8")
    sw = spoken_text(script).split()
    a, b = [norm_word(w) for w in sw], [norm_word(h[2]) for h in heard]
    sm = SequenceMatcher(None, a, b, autojunk=False)
    rows, low = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        t = heard[j1][0] if j1 < len(heard) else (heard[-1][1] if heard else 0)
        if tag == "replace":
            p = min((heard[j][3] for j in range(j1, j2)), default=0)
            rows.append((t, " ".join(sw[i1:i2]), " ".join(h[2] for h in heard[j1:j2]), p))
        elif tag == "equal":
            for k in range(i2 - i1):
                h = heard[j1 + k]
                if h[3] < 0.45:
                    low.append((h[0], sw[i1 + k], h[3]))

    def ts(x: float) -> str:
        return f"{int(x // 60)}:{int(x % 60):02d}"
    lines = [f"## 1. Where the episode's Arabic goes wrong\n",
             f"Whisper large-v3-turbo on the finished W45 episode: {len(heard)} words heard; "
             f"{len(rows)} script phrases heard as something else; {len(low)} words heard right but with low "
             f"confidence (unclear pronunciation). A quiet music bed sits under the voice, so treat single "
             f"low-confidence words with care; clusters and names are the signal.\n",
             "| time | script | heard | confidence |", "|---|---|---|---|"]
    lines += [f"| {ts(t)} | {s} | {h} | {p:.2f} |" for t, s, h, p in rows[:120]]
    if low:
        lines += ["", "<details><summary>Low-confidence words</summary>", "",
                  " · ".join(f"{ts(t)} «{w}» {p:.2f}" for t, w, p in low[:200]), "", "</details>"]
    return "\n".join(lines) + "\n"


# ── 2. Candidates ────────────────────────────────────────────────────────────

def reference(week: Path, out: Path) -> Path:
    """~25 s of the show voice from the original render (no music)."""
    return to_wav(week / "talking_head.mp4", out / "reference.wav", 20.0, 25.0)


def edge_voice(voice: str, text: str, dest: Path) -> Path:
    import edge_tts

    async def go():
        await edge_tts.Communicate(text, voice).save(str(dest.with_suffix(".mp3")))
    asyncio.run(go())
    return to_wav(dest.with_suffix(".mp3"), dest)


_XTTS = None


def xtts_voice(text: str, ref: Path, dest: Path) -> Path:
    global _XTTS
    if _XTTS is None:
        os.environ["COQUI_TOS_AGREED"] = "1"
        from TTS.api import TTS
        _XTTS = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    _XTTS.tts_to_file(text=text, speaker_wav=str(ref), language="ar", file_path=str(dest))
    return to_wav(dest, dest.with_name(dest.stem + "_16k.wav"))


_KNN = None
_MATCH = None


def knnvc_voice(src: Path, week: Path, out: Path, dest: Path) -> Path:
    """Voice conversion: keep the source's words and pronunciation, give it the show voice."""
    global _KNN, _MATCH
    import torch
    import torchaudio
    if _KNN is None:
        _KNN = torch.hub.load("bshall/knn-vc", "knn_vc", prematched=True, trust_repo=True, pretrained=True, device="cpu")
        refs = [to_wav(week / "talking_head.mp4", out / f"match_{i}.wav", 30.0 + i * 60, 60.0) for i in range(5)]
        _MATCH = _KNN.get_matching_set([str(r) for r in refs])
    wav = _KNN.match(_KNN.get_features(str(src)), _MATCH, topk=4)
    torchaudio.save(str(dest), wav[None], 16000)
    return dest


_ECAPA = None


def similarity(a: Path, b: Path) -> float | None:
    global _ECAPA
    try:
        import torch
        import torchaudio
        if _ECAPA is None:
            from speechbrain.inference.speaker import EncoderClassifier
            _ECAPA = EncoderClassifier.from_hparams("speechbrain/spkrec-ecapa-voxceleb", savedir="/tmp/ecapa")

        def emb(p: Path):
            sig, sr = torchaudio.load(str(p))
            return _ECAPA.encode_batch(sig).squeeze()
        return round(float(torch.nn.functional.cosine_similarity(emb(a), emb(b), dim=0)), 3)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        return None


def candidates(model, week: Path, out: Path) -> str:
    ref = reference(week, out)
    results: dict[str, dict[str, dict]] = {}
    makers = {
        "edge:ar-JO-TaimNeural": lambda t, d: edge_voice("ar-JO-TaimNeural", t, d),
        "edge:ar-SA-HamedNeural": lambda t, d: edge_voice("ar-SA-HamedNeural", t, d),
        "xtts": lambda t, d: xtts_voice(t, ref, d),
        "knnvc:taim→show": lambda t, d: knnvc_voice(edge_voice("ar-JO-TaimNeural", t, d.with_name(d.stem + "_src.wav")), week, out, d),
    }
    for tool, make in makers.items():
        slug = re.sub(r"[^a-z0-9]+", "-", tool.lower())
        for lid, text in LINES:
            dest = out / "samples" / f"{slug}__{lid}.wav"
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                wav = make(text, dest)
                heard = " ".join(w[2] for w in words_of(model, wav))
                results.setdefault(tool, {})[lid] = {"cer": cer(text, heard), "heard": heard,
                                                     "sim": similarity(wav, ref)}
                sh("ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-b:a", "96k", str(dest.with_suffix(".mp3")))
            except Exception as exc:  # noqa: BLE001
                traceback.print_exc()
                results.setdefault(tool, {})[lid] = {"error": f"{type(exc).__name__}: {exc}"[:200]}
    base_sim = similarity(to_wav(week / "talking_head.mp4", out / "ref2.wav", 120.0, 20.0), ref)
    (out / "candidates.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["## 2. Free voice tools on the hard lines\n",
             f"Similarity is to the show's current voice (ECAPA cosine; the current voice against itself on "
             f"another stretch scores {base_sim}). Intelligibility is Whisper's character error rate against "
             "the text (0 = every letter heard as written). Listen to the samples before trusting a number.\n",
             "| tool | mean error | mean similarity | licence / use |", "|---|---|---|---|"]
    for tool, per in results.items():
        ok = [v for v in per.values() if "cer" in v]
        if not ok:
            lines.append(f"| {tool} | failed: {next(iter(per.values())).get('error', '')} | | {TOOLS[tool]} |")
            continue
        sims = [v["sim"] for v in ok if v["sim"] is not None]
        lines.append(f"| {tool} | {sum(v['cer'] for v in ok) / len(ok):.2f} | "
                     f"{(sum(sims) / len(sims)) if sims else float('nan'):.2f} | {TOOLS[tool]} |")
    lines += ["", "### Line by line (what Whisper heard)", "", "| line | " + " | ".join(results) + " |",
              "|---|" + "---|" * len(results)]
    for lid, text in LINES:
        cells = []
        for tool in results:
            v = results[tool].get(lid, {})
            cells.append(f"{v['cer']:.2f} «{v['heard']}»" if "cer" in v else "—")
        lines.append(f"| **{lid}** «{text}» | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def repair_clips(model, week: Path, out: Path) -> str:
    """Re-voice the week's repair phrases with no credits: the Jordanian reading (right pronunciation)
    converted into the show voice. Writes lab/clips/NN.mp3 and lab/clips.yaml, whose `voice:` lines
    go into reviewed/<week>/repairs.yaml once the clips are copied to reviewed/<week>/clips/."""
    import yaml
    src = ROOT / "reviewed" / week.name / "repairs.yaml"
    raw = src.read_text(encoding="utf-8")
    keys = list((yaml.safe_load(raw) or {}).get("voice") or {})
    says = {m.group(1): m.group(2) for m in re.finditer(r'^\s*"([^"]+)":.*#\s*says «([^»]+)»', raw, re.M)}
    clips = out / "clips"
    clips.mkdir(parents=True, exist_ok=True)
    rows, mapping = [], {}
    for n, key in enumerate(keys, 1):
        text = says.get(key, key)
        dest = clips / f"{n:02d}.wav"
        try:
            wav = knnvc_voice(edge_voice("ar-JO-TaimNeural", text, dest.with_name(dest.stem + "_src.wav")), week, out, dest)
            heard = " ".join(w[2] for w in words_of(model, wav))
            sh("ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ar", "44100", "-b:a", "128k", str(dest.with_suffix(".mp3")))
            mapping[key] = f"file:reviewed/{week.name}/clips/{n:02d}.mp3"
            rows.append(f"| {n:02d} | {text} | {heard} | {cer(text, heard):.2f} |")
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            rows.append(f"| {n:02d} | {text} | failed: {type(exc).__name__} | |")
    (out / "clips.yaml").write_text(yaml.safe_dump({"voice": mapping}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return "\n".join(["## 3. Repair clips, no credits (Jordanian reading → show voice)\n",
                      "| # | says | Whisper heard | error |", "|---|---|---|---|", *rows]) + "\n"


def main() -> None:
    week, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    model = whisper()
    if "--clips" in sys.argv:
        report = f"# Voice lab · {week.name} · repair clips\n\n" + repair_clips(model, week, out)
        (out / "report.md").write_text(report, encoding="utf-8")
        print(report)
        return
    parts = [f"# Voice lab · {week.name}\n"]
    for step in (diagnose, candidates):
        try:
            parts.append(step(model, week, out))
        except Exception as exc:  # noqa: BLE001 — one failed step still reports the other
            traceback.print_exc()
            parts.append(f"## {step.__name__} failed\n\n`{type(exc).__name__}: {exc}`\n")
    (out / "report.md").write_text("\n".join(parts), encoding="utf-8")
    print("\n".join(parts))


if __name__ == "__main__":
    main()
