#!/usr/bin/env bash
# Installs this setup into the Herdr desktop app (~/.config/herdr-app); safe to re-run.
#   Shepherdr (pinned, shepherdr.pin) + my mod keys-help + borrowed mods (sources.tsv) + Devin status hooks
#   + a patch that lets Shepherdr's chat follow Devin.
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
#     (layout:shepherdr) are copied to layout:shepherdr-files, then mine from keys.json (layout:shepherdr, layout:shepherdr-files) win.
if [[ -f "$APP/layouts/shepherdr.json" && -d "$APP/mods/file-editor" ]]; then
  backup layouts/shepherdr-files.json; backup keys.json
  # Also docks desktop-notifications and space-jump (0px blocks) and adds the Asks panel to the right-hand stack: the top node is wrapped in a column and its root-only keys move up to it.
  jq '(.. | objects | select(.id? == "files" and .type? == "block") | .content.mod) = "file-editor"
      | ["titlebar","traffic_lights","terminal_padding","background","preview","terminal_menu","toast","theme","colors","font","font_size","ui_font","terminal_opacity"] as $rk
      | with_entries(select(.key as $k | $rk | index($k))) + {id: "frame", type: "column", children: [
          with_entries(select(.key as $k | ($rk | index($k)) | not)),
          {id: "notifications", type: "block", content: {mod: "desktop-notifications"}, size: {px: 0}},
          {id: "space-jump", type: "block", content: {mod: "space-jump"}, size: {px: 0}}]}
      | (.. | objects | select(.id? == "panel-body") | .children) += [{id: "asks", type: "block", content: {mod: "asks"}}]' \
    "$APP/layouts/shepherdr.json" > "$APP/layouts/shepherdr-files.json.tmp" && mv "$APP/layouts/shepherdr-files.json.tmp" "$APP/layouts/shepherdr-files.json"
  jq --slurpfile mine "$HERE/keys.json" '."layout:shepherdr-files" = ((."layout:shepherdr" // {}) + ($mine[0]["layout:shepherdr"] // {}) + ($mine[0]["layout:shepherdr-files"] // {}))' \
    "$APP/keys.json" > "$APP/keys.json.tmp" && mv "$APP/keys.json.tmp" "$APP/keys.json"
  echo "layout shepherdr-files  (Shepherdr + file-editor in place of Files; ctrl+shift+l to switch)"
fi

# 4c. Devin in Shepherdr's chat: a small, anchored patch to its `chat` and `pane-chat` mods (a clone under another name would break
#     pane-chat, spaces-chat, coordinator, which look for mod "chat") plus devin-chat.py, which turns Devin's sqlite
#     session into the log format the chat reads. Re-applied on every install; `shepherdr update` undoes it until then.
if [[ -d "$APP/mods/chat" ]]; then
  backup mods/chat; backup mods/pane-chat
  python3 -I "$HERE/integrations/devin/chat/patch-chat.py" "$APP"
fi

# 4d. Asks (herdr-agent-ask) in Shepherdr's tab bar: engine + button, a small anchored patch to `tabs-tasks`. Re-applied on every
#     install; `shepherdr update` undoes it until then.
if [[ -d "$APP/mods/tabs-tasks" && -d "$APP/mods/tabs-asks" ]]; then
  backup mods/tabs-tasks
  python3 -I "$HERE/integrations/asks/patch-tabs.py" "$APP"
fi

# 5. Agent integrations.
"$HERE/integrations/devin/install.sh"

echo "Installed into $APP. Previous files: $BACKUP"
echo "Check: herdr-app status · shepherdr doctor · then ctrl+shift+l picks the Shepherdr layout"
