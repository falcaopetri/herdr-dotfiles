#!/bin/sh
# Copies this repo's files into the herdr-app home (backing up what it replaces),
# then installs integrations. herdr-app hot-reloads, so no restart needed.
set -e
here=$(cd "$(dirname "$0")" && pwd)
HERDR=${HERDR_APP_HOME:-$HOME/.config/herdr-app}
mkdir -p "$HERDR/my-icons"
# keys.json is merged (repo wins per key) so sections added by other packages survive
if [ -f "$HERDR/keys.json" ]; then
  cp "$HERDR/keys.json" "$HERDR/keys.json.bak"
  jq -s '.[0] * .[1]' "$HERDR/keys.json.bak" "$here/keys.json" > "$HERDR/keys.json.tmp" && mv "$HERDR/keys.json.tmp" "$HERDR/keys.json"
else cp "$here/keys.json" "$HERDR/keys.json"; fi
for f in settings.json programs.json; do
  [ -f "$HERDR/$f" ] && ! cmp -s "$here/$f" "$HERDR/$f" && cp "$HERDR/$f" "$HERDR/$f.bak"
  cp "$here/$f" "$HERDR/$f"
done
cp "$here"/my-icons/* "$HERDR/my-icons/"
"$here/integrations/devin/install.sh"
echo "Done. Check: herdr-app status"
