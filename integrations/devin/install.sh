#!/bin/sh
# Installs the Devin -> herdr status hooks. Idempotent; backs up config.json to config.json.bak.
set -e
here=$(cd "$(dirname "$0")" && pwd)
DEVIN=${DEVIN_CONFIG_HOME:-$HOME/.config/devin}
command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }
mkdir -p "$DEVIN"
cp "$here/herdr-status.sh" "$DEVIN/herdr-status.sh"; chmod +x "$DEVIN/herdr-status.sh"
t=$DEVIN/config.json
[ -f "$t" ] || echo '{}' > "$t"
cp "$t" "$t.bak"
hooks=$(sed "s#__SCRIPT__#$DEVIN/herdr-status.sh#g" "$here/hooks.snippet.json")
# replace only entries that reference herdr-status.sh; keep the user's other hooks
jq --argjson new "$hooks" '
  .hooks = ((.hooks // {}) as $old
    | reduce ($new.hooks|keys[]) as $k ($old;
        .[$k] = ((.[$k] // [] | map(select(([.hooks[]?.command] | any(test("herdr-status.sh"))) | not))) + $new.hooks[$k])))
' "$t.bak" > "$t.tmp" && mv "$t.tmp" "$t"
echo "Devin hooks installed. Restart running Devin sessions."
