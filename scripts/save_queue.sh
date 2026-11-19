#!/usr/bin/env bash
# Commit and push data/social_queue.json without ever losing this run's posting results.
#   scripts/save_queue.sh "<commit message>"
# 2026-11-17: the save hit a git conflict (another job had changed the queue), the push gave up quietly, the
# "posted" record was lost and the next run posted the same Short again. On a conflict this takes the queue
# as it is on main and lays this run's results over it (scripts/social.py merge). If it still cannot push,
# the step fails, so the run is reported instead of silently forgetting what it posted.
set -u
msg="$1"
q=data/social_queue.json
ours="${RUNNER_TEMP:-/tmp}/social_queue.ours.json"
git config user.name "weekly-roundup[bot]" && git config user.email "bot@users.noreply.github.com"
[ -f "$q" ] || exit 0
cp "$q" "$ours"
git add "$q"
git diff --cached --quiet && exit 0
git commit -q -m "$msg"
for i in 1 2 3 4 5; do
  if git pull -q --rebase origin main; then
    git push -q origin HEAD:main && exit 0
  else
    echo "queue changed on main meanwhile: merging this run's results onto it"
    git rebase --abort 2>/dev/null
    git reset -q --hard origin/main
    python3 scripts/social.py merge "$ours" || exit 1
    git add "$q"
    git diff --cached --quiet || git commit -q -m "$msg (merged)"
  fi
  sleep $((i * 3))
done
echo "::error::Could not save $q: this run's posting results are in the job log only. Check before the next post."
exit 1
