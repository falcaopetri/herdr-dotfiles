#!/usr/bin/env bash
# Which pinned things (sources.tsv, shepherdr.pin) have newer commits upstream. Only reports.
set -euo pipefail
readonly D="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

read -r srepo ssha < <(grep -v '^#' "$D/shepherdr.pin")
head=$(gh api "repos/$srepo/commits/HEAD" -q .sha 2>/dev/null) || head=
if [[ -z $head ]]; then echo "?  shepherdr: $srepo unreachable"
elif [[ $head == "$ssha" ]]; then echo "=  shepherdr"
else echo "new  shepherdr: https://github.com/$srepo/compare/${ssha:0:7}...${head:0:7}"; fi

while IFS=$'\t' read -r mod repo subpath sha _license _mode; do
  [[ -z $mod || $mod == \#* ]] && continue
  head=$(gh api "repos/$repo/commits/HEAD" -q .sha 2>/dev/null) || { echo "?  $mod: $repo unreachable"; continue; }
  if [[ $head == "$sha" ]]; then echo "=  $mod"; continue; fi
  changed=$(gh api "repos/$repo/compare/$sha...$head" -q "[.files[].filename | select(startswith(\"$subpath/\"))] | length" 2>/dev/null || echo "?")
  if [[ $changed == 0 ]]; then echo "=  $mod (the repo moved, not this mod)"
  else echo "new  $mod: $changed file(s) changed, https://github.com/$repo/compare/${sha:0:7}...${head:0:7}"; fi
done < "$D/sources.tsv"
