#!/usr/bin/env bash
# Watchable preview of a week (video, text = the files and Shorts, all = both in one push, voice), pushed to the orphan branch `previews` (one commit, so old previews never
# bloat the repo history). Used by preview.yml (any week's artifact) and, since 2026-11-21, by the render
# job itself straight after the render (no second job re-downloading the 2.6 GB week artifact).
#
#   scripts/preview.sh <video|text|voice> <week> <week folder>
#   PREVIEW_PUSH=0   build into ./preview-out only (timing runs); GH_TOKEN + GITHUB_REPOSITORY to push
#   PREVIEW_FROM     label for the commit message (e.g. "run 123")
set -euo pipefail
what="$1"; week="$2"; d="$3"
out="${PREVIEW_OUT:-preview-out}"
mkdir -p "$out"
start=$(date +%s)

if [ "$what" = "text" ] || [ "$what" = "all" ]; then   # the session that drives the pipeline cannot download artifacts
  mkdir -p "$out/$week-files"
  for f in items.json script.md voice_pack.md voice_pack.json source_map.md plan.json critique.json shotlist.md cards.json subtitles.srt timeline.json credits.json stock_used.json timings.json thumbnail.png thumbnail_b.png; do
    [ -f "$d/$f" ] && cp "$d/$f" "$out/$week-files/" || true
  done
  [ -d "$d/cards" ] && cp -r "$d/cards" "$out/$week-files/cards" || true
  [ -f "$d/with_cards.mp4" ] && ffmpeg -hide_banner -loglevel error -y -ss 40 -t 12 -i "$d/with_cards.mp4" -vf scale=-2:540 -an "$out/$week-files/with_cards_40s.mp4" || true
  for v in "$d"/*.mp4; do   # where does the picture stop? frames per 30 s of every stage
    echo "== $(basename "$v")"; ffprobe -v error -select_streams v:0 -show_entries packet=pts_time -of csv=p=0 "$v" | awk '{n[int($1/30)]++} END{for(i=0;i<20;i++) printf "%d ", n[i]; print ""}'
  done > "$out/$week-files/frames.txt" 2>&1 || true
  for v in "$d"/shorts/short_*.mp4; do   # the week's Shorts, small enough to push
    [ -f "$v" ] && ffmpeg -hide_banner -loglevel error -y -i "$v" -vf scale=540:-2 -c:v libx264 -crf 27 -preset fast -c:a aac -b:a 96k "$out/$week-files/$(basename "$v")" || true
  done
  [ -f "$d/shorts/shorts.json" ] && cp "$d/shorts/shorts.json" "$out/$week-files/" || true
  ls -la "$out/$week-files"
fi
if [ "$what" = "voice" ]; then
  [ -f "$d/voice_check.mp3" ] || { echo "::error::no voice_check.mp3 in $d (run phase voicecheck first)"; exit 1; }
  cp "$d/voice_check.mp3" "$out/$week-voice.mp3"
  cp "$d/ownvoice.md" "$out/$week-voice.md"
  [ -f "$d/voice_words.json" ] && cp "$d/voice_words.json" "$out/$week-voice.words.json" || true
  cat "$d/ownvoice.md" | tee -a "${GITHUB_STEP_SUMMARY:-/dev/null}"
elif [ "$what" = "video" ] || [ "$what" = "all" ]; then
  src=""
  for f in final_subtitled.mp4 with_cards.mp4 talking_head.mp4; do [ -f "$d/$f" ] && src="$d/$f" && break; done
  [ -n "$src" ] || { echo "::error::no video in $d"; ls -R "$d" | head -50; exit 1; }
  echo "Source: $src"
  [ -f "$d/ownvoice.md" ] && { cat "$d/ownvoice.md"; cat "$d/ownvoice.md" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"; } || true
  # Word times of the own-voice recording, for `cut:` spans in voice.yaml (recording time).
  [ -f "$d/assemble/heard.json" ] && python3 -c "
import json, sys
for e in json.load(open(sys.argv[1]))['entries'].values():
    print('WORDS', ' '.join(f'{a // 60:.0f}:{a % 60:04.1f}-{b % 60:04.1f}={w.strip()}' for a, b, w in e['words']))
" "$d/assemble/heard.json" | fold -w 3000 || true
  # GitHub refuses files over 100 MB: size the bitrate to the length so any episode lands under ~90 MB,
  # and drop to 720p when that bitrate would be too thin for 1080p.
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$src")
  kbps=$(python3 -c "print(max(400, min(4000, int(90*8*1000/float('$dur')) - 160)))")
  height=$([ "$kbps" -ge 1500 ] && echo 1080 || echo 720)
  echo "Preview: ${dur}s at ${kbps} kbps, ${height}p"
  ffmpeg -hide_banner -loglevel error -y -i "$src" -vf "scale=-2:${height}" -c:v libx264 -preset medium \
    -b:v "${kbps}k" -maxrate "$((kbps * 3 / 2))k" -bufsize "$((kbps * 2))k" \
    -c:a aac -b:a 128k -movflags +faststart "$out/$week.mp4"
  ls -la "$out"
fi
echo "Preview build ($what): $(( $(date +%s) - start )) s"

[ "${PREVIEW_PUSH:-1}" = "1" ] || { echo "PREVIEW_PUSH=0: not pushed"; exit 0; }
# Keep the other weeks' previews, then put the new file on top (never the other way round). Two previews at
# once (preview.yml and a render job) would drop one week's file with a blind force-push, so the push is
# leased on the commit it was built on, and retried on top of the newer one.
remote="https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}"
here=$(pwd)
for attempt in 1 2 3 4 5; do
  rm -rf "$here/.preview-branch" && mkdir -p "$here/.preview-branch" && cd "$here/.preview-branch"
  git init -q -b previews
  git config user.name "weekly-roundup[bot]" && git config user.email "bot@users.noreply.github.com"
  base=""
  if git fetch -q "$remote" previews 2>/dev/null; then base=$(git rev-parse FETCH_HEAD); git checkout -q FETCH_HEAD -- . 2>/dev/null || true; fi
  cp -rf "$here/$out"/* .
  git add -A && git commit -q --allow-empty -m "preview: $week ($(date -u +%FT%H:%MZ)) from ${PREVIEW_FROM:-a render}"
  if git push -q --force-with-lease="previews:${base}" "$remote" HEAD:previews; then
    echo "Pushed the $what preview of $week (attempt $attempt)"; cd "$here"; rm -rf .preview-branch; exit 0
  fi
  echo "previews moved while building; retrying on top of it"; cd "$here"; sleep $((attempt * 5))
done
echo "::error::could not push the preview"; exit 1
