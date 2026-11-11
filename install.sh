#!/usr/bin/env bash
# Installs this setup into the Herdr desktop app (~/.config/herdr-app); safe to re-run.
#   Shepherdr (pinned, shepherdr.pin) + my mod keys-help + borrowed mods (sources.tsv) + Devin status hooks.
#   ./install.sh                 everything
#   ./install.sh --no-shepherdr  skip Shepherdr
# Replaced files are copied first to $APP/backup-<time>/. Needs jq, git, rsync, python3.
set -euo pipefail
readonly HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly APP="${HERDR_APP_HOME:-$HOME/.config/herdr-app}"
readonly BACKUP="$APP/backup-$(date +%Y%m%d-%H%M%S)"
readonly SRC="${SHEPHERDR_SRC:-$HOME/src/shepherdr}"
extra=" $* "

[[ -d "$APP" ]] || { echo "No $APP: open the Herdr app once, then run this again." >&2; exit 1; }
for c in jq git rsync python3; do command -v "$c" >/dev/null || { echo "$c is required." >&2; exit 1; }; done
backup() { [[ -e "$APP/$1" ]] || return 0; mkdir -p "$BACKUP/$(dirname "$1")"; cp -R "$APP/$1" "$BACKUP/$1"; }

# 1. Shepherdr, at its pinned commit, from a stable clone ($SRC; `shepherdr update` pulls there).
#    --no-build: no web app/service (needs bun + tailscale; rerun without it to add them).
if [[ $extra != *" --no-shepherdr "* ]]; then
  read -r srepo ssha < <(grep -v '^#' "$HERE/shepherdr.pin")
  [[ -d "$SRC/.git" ]] || git clone -q "https://github.com/$srepo" "$SRC"
  git -C "$SRC" fetch -q origin && git -C "$SRC" checkout -q "$ssha"
  "$SRC/install.sh" --no-build --yes --keys keep
fi

# 2. App files: programs.json (merged) and icons; keys.json is merged (this repo wins per key).
backup keys.json; backup programs.json
for f in keys programs; do
  if [[ -f "$APP/$f.json" ]]; then jq -s '.[0] * .[1]' "$APP/$f.json" "$HERE/$f.json" > "$APP/$f.json.tmp" && mv "$APP/$f.json.tmp" "$APP/$f.json"
  else cp "$HERE/$f.json" "$APP/$f.json"; fi
done
mkdir -p "$APP/my-icons" && cp "$HERE"/my-icons/* "$APP/my-icons/"

# 3. My mods.
for d in "$HERE"/mods/*/; do
  n=$(basename "$d"); backup "mods/$n"
  mkdir -p "$APP/mods/$n" && rsync -a --delete "$d" "$APP/mods/$n/"
done

# 4. Other people's mods, at the commit in sources.tsv.
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
while IFS=$'\t' read -r mod repo subpath sha license mode; do
  [[ -z $mod || $mod == \#* ]] && continue
  [[ $mode == default || $extra == *" $mod "* ]] || { echo "skip  $mod (optional: ./install.sh $mod)"; continue; }
  git clone -q --filter=blob:none --no-checkout "https://github.com/$repo" "$tmp/$mod"
  git -C "$tmp/$mod" checkout -q "$sha" -- "$subpath"
  backup "mods/$mod"
  mkdir -p "$APP/mods/$mod" && rsync -a --delete --exclude '*.d.ts' --exclude jsconfig.json "$tmp/$mod/$subpath/" "$APP/mods/$mod/"
  echo "mod   $mod  ($repo@${sha:0:7}, $license)"
done < "$HERE/sources.tsv"

# 4b. Layout "shepherdr-files": Shepherdr's layout with its Files panel swapped for the file-editor mod.
#     Generated from the live layouts/shepherdr.json each time, so Shepherdr updates carry over. Its keys
#     (layout:shepherdr) are copied to layout:shepherdr-files, then mine from keys.json win.
if [[ -f "$APP/layouts/shepherdr.json" && -d "$APP/mods/file-editor" ]]; then
  backup layouts/shepherdr-files.json; backup keys.json
  jq '(.. | objects | select(.id? == "files" and .type? == "block") | .content.mod) = "file-editor"' \
    "$APP/layouts/shepherdr.json" > "$APP/layouts/shepherdr-files.json.tmp" && mv "$APP/layouts/shepherdr-files.json.tmp" "$APP/layouts/shepherdr-files.json"
  jq --slurpfile mine "$HERE/keys.json" '."layout:shepherdr-files" = ((."layout:shepherdr" // {}) + ($mine[0]["layout:shepherdr"] // {}))' \
    "$APP/keys.json" > "$APP/keys.json.tmp" && mv "$APP/keys.json.tmp" "$APP/keys.json"
  echo "layout shepherdr-files  (Shepherdr + file-editor in place of Files; ctrl+shift+l to switch)"
fi

# 5. Agent integrations.
"$HERE/integrations/devin/install.sh"

echo "Installed into $APP. Previous files: $BACKUP"
echo "Check: herdr-app status · shepherdr doctor · then ctrl+shift+l picks the Shepherdr layout"
