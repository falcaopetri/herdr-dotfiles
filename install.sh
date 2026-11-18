#!/usr/bin/env bash
# Installs this setup into the Herdr desktop app (~/.config/herdr-app); safe to re-run.
#   Shepherdr (pinned, shepherdr.pin) + my mod keys-help + borrowed mods (sources.tsv) + Devin status hooks
#   + a patch that lets Shepherdr's chat follow Devin.
#   ./install.sh                 everything
#   ./install.sh --no-shepherdr  skip Shepherdr
#   ./install.sh --fetch         only download (the one step that needs the internet), then stop
# Everything from the internet is downloaded first, in step 0 (one tarball per repo, one git fetch for Shepherdr),
# into $CACHE; the rest works offline, so switching networks only has to cover `./install.sh --fetch`.
# Replaced files are copied first to $APP/backup-<time>/. Needs jq, git, rsync, python3.
set -euo pipefail
readonly HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly APP="${HERDR_APP_HOME:-$HOME/.config/herdr-app}"
readonly BACKUP="$APP/backup-$(date +%Y%m%d-%H%M%S)"
readonly SRC="${SHEPHERDR_SRC:-$HOME/src/shepherdr}"
readonly CACHE="${HERDR_DOTFILES_CACHE:-$HOME/.cache/herdr-dotfiles}"
extra=" $* "

[[ -d "$APP" ]] || { echo "No $APP: open the Herdr app once, then run this again." >&2; exit 1; }
for c in jq git rsync python3 curl tar; do command -v "$c" >/dev/null || { echo "$c is required." >&2; exit 1; }; done
# herdr-chat installed (its new-chat mod is in the app home): its `chat` mod stands in for Shepherdr's, which lives on as mods/chat.orig.
# Shepherdr's installer would put its own `chat` back, and the patches for Shepherdr's chat (4c) have nothing to patch.
HERDR_CHAT=0; [[ -f "$APP/mods/new-chat/mod.json" ]] && HERDR_CHAT=1
backup() { [[ -e "$APP/$1" ]] || return 0; mkdir -p "$BACKUP/$(dirname "$1")"; cp -R "$APP/$1" "$BACKUP/$1"; }

# 0. Download everything that is needed (the only step that uses the network); what is already in $CACHE / $SRC is skipped.
#    Shepherdr: its clone in $SRC (`shepherdr update` pulls there), one fetch. Mods: one tarball per repo@commit.
want() { [[ $2 == default || $extra == *" $1 "* ]]; }   # want <mod> <mode>
tarball() { echo "$CACHE/${1//\//_}-$2.tar.gz"; }          # tarball <repo> <sha>
mkdir -p "$CACHE"
if [[ $extra != *" --no-shepherdr "* ]]; then
  read -r srepo ssha < <(grep -v '^#' "$HERE/shepherdr.pin")
  [[ -d "$SRC/.git" ]] || git clone -q --no-checkout "https://github.com/$srepo" "$SRC"
  git -C "$SRC" cat-file -e "$ssha^{commit}" 2>/dev/null || { echo "fetch shepherdr@${ssha:0:7}"; git -C "$SRC" fetch -q origin; }
fi
while IFS=$'\t' read -r mod repo _subpath sha _license mode; do
  [[ -z $mod || $mod == \#* ]] && continue
  want "$mod" "$mode" || continue
  f=$(tarball "$repo" "$sha"); [[ -s $f ]] && continue
  echo "fetch $repo@${sha:0:7}"
  curl -fsSL --retry 3 -o "$f.part" "https://codeload.github.com/$repo/tar.gz/$sha" && mv "$f.part" "$f"
done < "$HERE/sources.tsv"
if [[ $extra == *" --fetch "* ]]; then echo "Downloaded into $CACHE (and $SRC). Run ./install.sh to install, offline."; exit 0; fi

# 1. Shepherdr, at its pinned commit, from a stable clone ($SRC).
#    --no-build: no web app/service (needs bun + tailscale; rerun without it to add them).
if [[ $extra != *" --no-shepherdr "* && $HERDR_CHAT = 1 ]]; then
  echo "skip  Shepherdr (herdr-chat's chat mod is installed: Shepherdr's installer would replace it; use --no-shepherdr to hide this)"
elif [[ $extra != *" --no-shepherdr "* ]]; then
  git -C "$SRC" checkout -q "$ssha"
  "$SRC/install.sh" --no-build --yes --keys keep
fi

# 2. App files: programs.json (merged) and icons; keys.json is merged (this repo wins per key).
backup keys.json; backup programs.json
for f in keys programs; do
  if [[ -f "$APP/$f.json" ]]; then jq -s '.[0] * .[1]' "$APP/$f.json" "$HERE/$f.json" > "$APP/$f.json.tmp" && mv "$APP/$f.json.tmp" "$APP/$f.json"
  else cp "$HERE/$f.json" "$APP/$f.json"; fi
done
mkdir -p "$APP/my-icons" && cp "$HERE"/my-icons/* "$APP/my-icons/"
echo "$HERE" > "$APP/dotfiles-path"   # where the `submit` mod appends requests.md

# 2b. Nothing goes back to the internet: the app's anonymous telemetry off, and Shepherdr's "Feedback offers" off (agents
#     never offer to file issues on GitHub; ideas go to requests.md via the `submit` mod). Both are merged into live files.
backup settings.json
jq '.telemetry = false' "$APP/settings.json" > "$APP/settings.json.tmp" && mv "$APP/settings.json.tmp" "$APP/settings.json"
SCFG="$HOME/.config/shepherdr/settings.json"
if [[ -f "$SCFG" ]]; then
  mkdir -p "$BACKUP/shepherdr" && cp "$SCFG" "$BACKUP/shepherdr/settings.json"
  jq '.everywhere.agents.feedback = false' "$SCFG" > "$SCFG.tmp" && mv "$SCFG.tmp" "$SCFG"
fi

# 3. My mods.
for d in "$HERE"/mods/*/; do
  n=$(basename "$d"); backup "mods/$n"
  mkdir -p "$APP/mods/$n" && rsync -a --delete "$d" "$APP/mods/$n/"
done

# 4. Other people's mods, at the commit in sources.tsv.
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
while IFS=$'\t' read -r mod repo subpath sha license mode; do
  [[ -z $mod || $mod == \#* ]] && continue
  want "$mod" "$mode" || { echo "skip  $mod (optional: ./install.sh $mod)"; continue; }
  mkdir -p "$tmp/$mod" && tar -xzf "$(tarball "$repo" "$sha")" -C "$tmp/$mod" --strip-components=1
  backup "mods/$mod"
  mkdir -p "$APP/mods/$mod" && rsync -a --delete --exclude '*.d.ts' --exclude jsconfig.json "$tmp/$mod/$subpath/" "$APP/mods/$mod/"
  echo "mod   $mod  ($repo@${sha:0:7}, $license)"
done < "$HERE/sources.tsv"

# 4b. Layout "shepherdr-files": Shepherdr's layout with its Files panel swapped for the file-editor mod.
#     Generated from the live layouts/shepherdr.json each time, so Shepherdr updates carry over. Its keys
#     (layout:shepherdr) are copied to layout:shepherdr-files, then mine from keys.json (layout:shepherdr, layout:shepherdr-files) win.
if [[ -f "$APP/layouts/shepherdr.json" && -d "$APP/mods/file-editor" ]]; then
  backup layouts/shepherdr-files.json; backup keys.json
  # Also swaps the sidebar's Spaces list (spaces-chat) for my space-tree (each space with its agents and terminals under it), and docks desktop-notifications (0px block): the top node is wrapped in a column and its root-only keys move up to it.
  sb=space-tree; [[ -d "$APP/mods/agent-sidebar" ]] && sb=agent-sidebar   # jeffarese's sidebar (borrowed, patched in 4f) when present, else my space-tree
  jq --arg sb "$sb" '(.. | objects | select(.id? == "files" and .type? == "block") | .content.mod) = "file-editor"
      | ["titlebar","traffic_lights","terminal_padding","background","preview","terminal_menu","toast","theme","colors","font","font_size","ui_font","terminal_opacity"] as $rk
      | with_entries(select(.key as $k | $rk | index($k))) + {id: "frame", type: "column", children: [
          with_entries(select(.key as $k | ($rk | index($k)) | not)),
          {id: "notifications", type: "block", content: {mod: "desktop-notifications"}, size: {px: 0}}]}
      | (.. | objects | select(.id? == "spaces" and .type? == "block") | .content.mod) = $sb' \
    "$APP/layouts/shepherdr.json" > "$APP/layouts/shepherdr-files.json.tmp" && mv "$APP/layouts/shepherdr-files.json.tmp" "$APP/layouts/shepherdr-files.json"
  jq --slurpfile mine "$HERE/keys.json" '."layout:shepherdr-files" = ((."layout:shepherdr" // {}) + ($mine[0]["layout:shepherdr"] // {}) + ($mine[0]["layout:shepherdr-files"] // {}))' \
    "$APP/keys.json" > "$APP/keys.json.tmp" && mv "$APP/keys.json.tmp" "$APP/keys.json"
  echo "layout shepherdr-files  (Shepherdr + file-editor in place of Files; ctrl+shift+l to switch)"
fi

# 4c. Devin in Shepherdr's chat: a small, anchored patch to its `chat` and `pane-chat` mods (a clone under another name would break
#     pane-chat, spaces-chat, coordinator, which look for mod "chat") plus devin-chat.py, which turns Devin's sqlite
#     session into the log format the chat reads. Re-applied on every install; `shepherdr update` undoes it until then.
if [[ -d "$APP/mods/chat" && $HERDR_CHAT = 0 ]]; then
  backup mods/chat; backup mods/pane-chat
  python3 -I "$HERE/integrations/devin/chat/patch-chat.py" "$APP"
fi

# 4d. Tabs name themselves (longwave/herdr-auto-tabs' names.js, plus Devin) from Shepherdr's tab bar: a small anchored patch to
#     `tabs-tasks`. Re-applied on every install; `shepherdr update` undoes it until then.
if [[ -d "$APP/mods/tabs-tasks" && -f "$APP/mods/auto-tabs/names.js" ]]; then
  backup mods/tabs-tasks
  python3 -I "$HERE/integrations/auto-tabs/patch-tabs.py" "$APP"
fi

# 4e. Reopen a closed tab with its Devin session: one anchored entry in reopen-tab's RESUME table (claude and codex only upstream).
#     Re-applied on every install; moving the pin in sources.tsv undoes it until then.
if [[ -f "$APP/mods/reopen-tab/plan.js" ]]; then
  backup mods/reopen-tab
  python3 -I "$HERE/integrations/reopen/patch-plan.py" "$APP"
  # With herdr-chat installed, a closed chat tab comes back as a chat (not as its host's terminal).
  [[ -f "$APP/mods/new-chat/mod.json" ]] && python3 -I "$HERE/integrations/reopen/patch-chat.py" "$APP"
fi

# 4e2. tmux-prefix (borrowed example): my commands and the live Keep awake toggle in its list, prefix shown as cmd+e.
if [[ -f "$APP/mods/tmux-prefix/main.js" ]]; then
  python3 -I "$HERE/integrations/tmux-prefix/patch-bindings.py" "$APP"
fi

# 4e3. herdr-chat's timeline: no jump while scrolling up through history (rows above the screen were placed by estimated heights).
if [[ $HERDR_CHAT = 1 && -f "$APP/mods/chat/timeline.js" ]]; then
  backup mods/chat
  python3 -I "$HERE/integrations/chat-scroll/patch-timeline.py" "$APP"
fi

# 4e4. herdr-chat opens Shepherdr's Assistant tab (props role/slot/folder/settings, no chat id).
if [[ $HERDR_CHAT = 1 && -f "$APP/mods/chat/main.js" ]]; then
  backup mods/chat
  python3 -I "$HERE/integrations/assistant/patch-assistant.py" "$APP"
fi

# 4f. agent-sidebar (optional mod): folder headings always, and agent-sidebar.<n> jump commands (cmd+1..9 in shepherdr-files).
#     Re-applied on every install; moving the pin in sources.tsv undoes it until then.
if [[ -f "$APP/mods/agent-sidebar/main.js" ]]; then
  backup mods/agent-sidebar
  python3 -I "$HERE/integrations/agent-sidebar/patch-sidebar.py" "$APP"
  # With herdr-chat installed (its new-chat mod), a new agent session in an open space is one of its chats.
  [[ -f "$APP/mods/new-chat/mod.json" && -f "$APP/mods/agent-sidebar/launcher.js" ]] &&
    python3 -I "$HERE/integrations/agent-sidebar/patch-launcher.py" "$APP"
fi

# 4f2. herdr-chat's `chat` has no session-note.sh, but the SessionStart hook Shepherdr put in Claude's/Codex's config still points at
#      mods/chat/session-note.sh ("hook failed: No such file"). Give it Shepherdr's copy (kept in mods/chat.orig).
if [[ $HERDR_CHAT = 1 && -f "$APP/mods/chat.orig/session-note.sh" && -d "$APP/mods/chat" ]]; then
  install -m 755 "$APP/mods/chat.orig/session-note.sh" "$APP/mods/chat/session-note.sh"
fi

# 4g. Agents open in chat view: a small anchored addition to pane-chat (once per terminal). Re-applied on every install;
#     `shepherdr update` undoes it until then.
# DISABLED: the loop made tabs flap (it focused chats that were already open). Re-enable after fixing patch-auto-chat.py.
# if [[ -f "$APP/mods/pane-chat/main.js" ]]; then
#   backup mods/pane-chat
#   python3 -I "$HERE/integrations/auto-chat/patch-auto-chat.py" "$APP"
# fi

# 5. Agent integrations.
"$HERE/integrations/devin/install.sh"

echo "Installed into $APP. Previous files: $BACKUP"
echo "Check: herdr-app status · shepherdr doctor · then ctrl+shift+l picks the Shepherdr layout"
