#!/bin/sh
# Report Devin's state to Herdr via OSC 7501. Usage: herdr-status.sh <idle|working|done|blocked>
cat >/dev/null 2>&1 &
t=/dev/tty
( : >"$t" ) 2>/dev/null || t="/dev/$(ps -o tty= -p "$PPID" | tr -d ' ')"
printf '\033]7501;state=%s:app=devin\033\\' "$1" >"$t" 2>/dev/null
exit 0
