#!/bin/sh
# Copies this repo's files into the herdr-app home (backing up what it replaces),
# then installs integrations. herdr-app hot-reloads, so no restart needed.
set -e
here=$(cd "$(dirname "$0")" && pwd)
HERDR=${HERDR_APP_HOME:-$HOME/.config/herdr-app}
mkdir -p "$HERDR/mods" "$HERDR/my-icons"
for f in keys.json settings.json programs.json; do
  [ -f "$HERDR/$f" ] && ! cmp -s "$here/$f" "$HERDR/$f" && cp "$HERDR/$f" "$HERDR/$f.bak"
  cp "$here/$f" "$HERDR/$f"
done
cp "$here"/my-icons/* "$HERDR/my-icons/"
for m in "$here"/mods/*/; do
  name=$(basename "$m"); mkdir -p "$HERDR/mods/$name"; cp -R "$m". "$HERDR/mods/$name/"
done
"$here/integrations/devin/install.sh"
echo "Done. Check: herdr-app status"
