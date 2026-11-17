#!/usr/bin/env python3
"""Teaches the borrowed reopen-tab mod to bring Devin back: plan.js's RESUME table lists claude and codex only, so a
reopened Devin tab started a blank session. The entry added here resumes the most recent session of that folder that no
live Devin process holds (sessions are locked by pid in ~/.local/share/devin/cli/session_locks), so with several Devin
tabs in one folder it is still the closed one that comes back. Re-applied by install.sh; idempotent; one exact anchor,
and it changes nothing if the anchor is gone (fix it after a pin bump).
Usage: patch-plan.py <app home>"""
import json, sys, pathlib

SCRIPT = r'''d=$(pwd); base=${DEVIN_DATA:-$HOME/.local/share/devin/cli}; q=$(printf %s "$d" | sed "s/'/''/g"); id=""
for s in $(sqlite3 -readonly "$base/sessions.db" "select id from sessions where working_directory='$q' and hidden=0 order by last_activity_at desc limit 25" 2>/dev/null); do
  p=$(cat "$base/session_locks/$s.lock" 2>/dev/null)
  if [ -n "$p" ] && kill -0 "$p" 2>/dev/null; then continue; fi
  id=$s; break
done
if [ -n "$id" ]; then exec "$@" -r "$id"; else exec "$@"; fi'''

ANCHOR = '  codex: {\n    session: ["resume"],'
ENTRY = ('  devin: {\n    session: ["-c", "--continue", "-r", "--resume"],\n'
         '    skip: ["-p", "--print", "-h", "--help", "-V", "--version"],\n'
         '    resume: (cmd) => ["sh", "-c", %s, "sh", ...cmd],\n  },\n') % json.dumps(SCRIPT)

f = pathlib.Path(sys.argv[1]) / "mods/reopen-tab/plan.js"
s = f.read_text()
if "\n  devin: {" in s:
    print("reopen-tab already resumes Devin"); sys.exit(0)
if s.count(ANCHOR) != 1:
    sys.exit("patch-plan.py: anchor not found in %s; nothing changed (update the patch)" % f)
f.write_text(s.replace(ANCHOR, ENTRY + ANCHOR))
print("reopen-tab: Devin resumes its closed session")
