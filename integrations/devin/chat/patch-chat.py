#!/usr/bin/env python3
"""Teaches Shepherdr's `chat` mod to follow Devin. Usage: patch-chat.py <app home>

Idempotent. Each edit is an exact string anchor in the upstream mod; if an anchor is gone (Shepherdr changed that
code) it stops with an error and changes nothing, so a pin bump never half-patches the mod.
What it does: `devin` joins the CLIs the chat knows (and pane-chat's Chat | Terminal switch shows for it); FIND maps the Devin process to its session (session_locks);
the question card's "Other" box holds the keyboard while focused (the chat stole it back after ~2 s);
LOG first refreshes the Claude-style copy of the session that devin-chat.py writes from Devin's sqlite db.
"""
import os, shutil, sys

app = sys.argv[1]
mods = os.path.join(app, "mods")
mod = os.path.join(mods, "chat")
here = os.path.dirname(os.path.abspath(__file__))
MARK = "devin-chat"

KINDS_OLD = '{ "claude-code": "claude", claude: "claude", codex: "codex" }'
KINDS_NEW = '{ "claude-code": "claude", claude: "claude", codex: "codex", devin: "devin" }'

FIND_OLD = 'for p in "$pid" $(kids "$pid"); do\n'
FIND_NEW = FIND_OLD + '''  # devin-chat: the Devin process names its session in session_locks; devin-chat.py writes the log we read
  if [ "$kind" = devin ]; then
    l=$(grep -lx "$p" "$HOME"/.local/share/devin/cli/session_locks/*.lock 2>/dev/null | head -1)
    [ -n "$l" ] || continue
    python3 -I "$HOME/.config/herdr-app/mods/chat/devin-chat.py" "$(basename "$l" .lock)"
    exit 0
  fi
'''

LOG_OLD = 'mode="$1"; f="$2"\n'
LOG_NEW = LOG_OLD + '''# devin-chat: a Devin session's log is a copy of its sqlite db: refresh it before reading
case "$f" in */data/devin-chat/*.jsonl) python3 -I "$HOME/.config/herdr-app/mods/chat/devin-chat.py" "$(basename "$f" .jsonl)" >/dev/null 2>&1;; esac
'''

NAMES_OLD = '{ claude: "Claude Code", codex: "Codex" }'
NAMES_NEW = '{ claude: "Claude Code", codex: "Codex", devin: "Devin" }'

CHATTY_OLD = '(["claude-code", "codex"].includes(p.app) || ["claude", "codex"].includes(p.program?.key))'
CHATTY_NEW = '(["claude-code", "codex", "devin"].includes(p.app) || ["claude", "codex", "devin"].includes(p.program?.key))'

SLASH_NEW = r'''  if (kind === "devin") {
    const dk = `devin|${machine ?? ""}|${cwd ?? ""}`;
    if (!cache.has(dk)) cache.set(dk, exec("sh", ["-c", 'cd "$1" 2>/dev/null; devin skills list 2>/dev/null | awk \'match($0, /^  \\/[^ ]+/) { n = substr($0, 4, RLENGTH - 3); i = index($0, ") - "); printf "%s\\t%s\\n", n, (i ? substr($0, i + 4, 90) : "Skill") }\'', "scan", cwd ?? ""], { on: machine }).then((r) => scanned(r.stdout)).catch(() => []));
    return await cache.get(dk);
  }
  if (kind !== "claude") return commandList(kind);
'''

# (path under mods/, old, new). pane-chat's `chatty` is what shows the Chat | Terminal switch in an agent's header.
EDITS = [
    ("pane-chat/main.js", CHATTY_OLD, CHATTY_NEW),
    ("chat/main.js", "const KINDS = " + KINDS_OLD, "const KINDS = " + KINDS_NEW),
    ("chat/core/chat-reader.js", "export const KINDS = " + KINDS_OLD, "export const KINDS = " + KINDS_NEW),
    ("chat/core/agents.js", "export const NAMES = " + NAMES_OLD, "export const NAMES = " + NAMES_NEW),
    ("chat/core/chat-log.js", FIND_OLD, FIND_NEW),
    ("chat/core/chat-log.js", LOG_OLD, LOG_NEW),
    # "/" autocomplete for Devin: its skills, from `devin skills list` (user-invocable lines start with "/"), in the agent's folder.
    ("chat/slash.js", '  if (kind !== "claude") return commandList(kind);\n', SLASH_NEW),
    # A question card's "Other" box takes the keyboard from the chat's own box: without saying so (keyholder.js) the chat
    # took it back about 2 s later. The box now holds the keyboard under its own name while it has focus.
    ("chat/cards.js", 'import { InputState } from "gpui-base";\n', 'import { InputState } from "gpui-base";\nimport { holdKeys } from "./keyholder.js";\n'),
    ("chat/cards.js", 'q.boxes[i].on("change", (_e, cx) => cx.notify()); }', 'q.boxes[i].on("change", (_e, cx) => cx.notify()); q.boxes[i].on("focus", () => holdKeys("card")); }'),
]

texts, todo = {}, []
for rel, old, new in EDITS:
    p = os.path.join(mods, rel)
    texts.setdefault(rel, open(p, encoding="utf-8").read())
    t = texts[rel]
    if new in t:
        continue
    if t.count(old) != 1:
        sys.exit("patch-chat: anchor not found in %s (Shepherdr changed it): %r" % (rel, old[:60]))
    texts[rel] = t.replace(old, new)
    todo.append(rel)

for rel in set(todo):
    open(os.path.join(mods, rel), "w", encoding="utf-8").write(texts[rel])
shutil.copy(os.path.join(here, "devin-chat.py"), os.path.join(mod, "devin-chat.py"))
print("chat   patched for Devin (%d edits)" % len(todo) if todo else "chat   already patched for Devin")
