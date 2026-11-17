#!/bin/sh
# Report Devin's state to Herdr via OSC 7501. Usage: herdr-status.sh <idle|working|done|blocked>
# Also sets the terminal title to the session's title (Devin's sessions.db, newest in this folder), which the tab bar
# shows as the tab name (integrations/auto-tabs). Devin itself only sets "devin: <folder>".
cat >/dev/null 2>&1 &
t=/dev/tty
( : >"$t" ) 2>/dev/null || t="/dev/$(ps -o tty= -p "$PPID" | tr -d ' ')"
printf '\033]7501;state=%s:app=devin\033\\' "$1" >"$t" 2>/dev/null
db="${DEVIN_DATA_HOME:-$HOME/.local/share/devin}/cli/sessions.db"
if [ "$1" != idle ] && [ -r "$db" ] && command -v sqlite3 >/dev/null 2>&1; then
  dir=$(printf '%s' "$PWD" | sed "s/'/''/g")
  title=$(sqlite3 -readonly "$db" "select title from sessions where working_directory='$dir' and title is not null and hidden=0 order by last_activity_at desc limit 1" 2>/dev/null \
    | tr -d '\000-\037' | sed 's/<[^>]*>//g' | cut -c1-80)
  [ -n "$title" ] && printf '\033]2;%s\033\\' "$title" >"$t" 2>/dev/null
fi
exit 0
