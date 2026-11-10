#!/bin/sh
# Installs Devin support for herdr-app. Idempotent; backs up files it changes.
set -e
here=$(cd "$(dirname "$0")" && pwd)
HERDR=${HERDR_APP_HOME:-$HOME/.config/herdr-app}
DEVIN=${DEVIN_CONFIG_HOME:-$HOME/.config/devin}
command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }
mkdir -p "$HERDR/my-icons" "$DEVIN"

cp "$here/assets/devin.png" "$HERDR/my-icons/devin.png"
cp "$here/bin/herdr-status.sh" "$DEVIN/herdr-status.sh"; chmod +x "$DEVIN/herdr-status.sh"

merge() { # merge <target> <filter> <snippet...>
  t=$1; f=$2; shift 2
  [ -f "$t" ] || echo '{}' > "$t"
  cp "$t" "$t.bak"
  jq "$f" "$t.bak" "$@" > "$t.tmp" && mv "$t.tmp" "$t"
}

# programs.json: add/override the devin entry
merge "$HERDR/programs.json" '.programs.devin = $s[0].programs.devin' --slurpfile s "$here/programs.snippet.json"

# Devin hooks: replace only hook commands that point at herdr-status.sh, keep others
script="$DEVIN/herdr-status.sh"
sed "s#__SCRIPT__#$script#g" "$here/hooks.snippet.json" > "$here/.hooks.tmp"
merge "$DEVIN/config.json" '
  ($s[0].hooks) as $new
  | .hooks = ((.hooks // {}) as $old
    | reduce ($new|keys[]) as $k ($old;
        .[$k] = ((.[$k] // [] | map(select(([.hooks[]?.command] | any(test("herdr-status.sh"))) | not))) + $new[$k])))
' --slurpfile s "$here/.hooks.tmp"
rm -f "$here/.hooks.tmp"
echo "Done. Restart Devin sessions; check with: herdr-app status"
