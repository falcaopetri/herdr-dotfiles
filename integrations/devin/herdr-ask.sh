#!/bin/sh
# Devin's PermissionRequest hook -> the Shepherdr chat's approval card. It hands Devin's hook input to the chat's own
# ask-hook.sh (written for Claude Code: it leaves the request for the chat card and waits for the answer, up to 30 minutes)
# and turns the answer into Devin's decision format. No answer, or no chat: it prints nothing and Devin asks in the terminal.
#   Claude: {"hookSpecificOutput":{"decision":{"behavior":"allow"|"deny","message":..}}}
#   Devin:  {"decision":"approve"|"block","reason":..}
hook="${HERDR_APP_HOME:-$HOME/.config/herdr-app}/mods/chat/ask-hook.sh"
[ -f "$hook" ] && command -v jq >/dev/null 2>&1 || exit 0
out=$(sh "$hook") || exit 0
[ -n "$out" ] || exit 0
printf '%s' "$out" | jq -c '(.hookSpecificOutput.decision // {}) as $d
  | if $d.behavior == "allow" then {decision: "approve"}
    elif $d.behavior == "deny" then {decision: "block", reason: ($d.message // "Denied in Herdr")}
    else empty end' 2>/dev/null
exit 0
