#!/usr/bin/env python3
"""Tabs name themselves: longwave/herdr-auto-tabs' names.js, run from Shepherdr's tab bar (`tabs-tasks`).
1. Copies names.js (borrowed, pinned in sources.tsv as mod `auto-tabs`) next to tabs-tasks/main.js, with one change:
   Devin (OSC 7501 app=devin) is named after its terminal title like Claude Code (herdr-status.sh sets that title
   to the session's title).
2. tabs-tasks/main.js imports it and calls syncNames() every 3 s.
Re-applied by install.sh; idempotent; exact anchors, and it changes nothing if one is gone (fix it after a Shepherdr update).
Usage: patch-tabs.py <app home>"""
import sys, pathlib

home = pathlib.Path(sys.argv[1])
src = home / "mods/auto-tabs/names.js"
mod = home / "mods/tabs-tasks"
main = mod / "main.js"

names = src.read_text()
A = 'if (p.app === "claude-code") return'
B = 'const DEFAULTS = new Set(["Claude Code"]);'
for a in (A, B):
    if names.count(a) != 1:
        sys.exit("patch-tabs.py: anchor %r not found in %s; nothing changed (update the patch)" % (a, src))
names = names.replace(A, 'if (p.app === "claude-code" || p.app === "devin") return')
names = names.replace(B, 'const DEFAULTS = new Set(["Claude Code", "Devin"]);')
names = names.replace('(p.app === "claude-code" && cur.app !== "claude-code")', '((p.app === "claude-code" || p.app === "devin") && cur.app !== "claude-code" && cur.app !== "devin")')

s = main.read_text()
IMP = 'import { Engine as AsksEngine }'
TIMER = "    cx.timer.every(5000, () => sweep());\n"
MARK = "// auto-tabs-patch"
if MARK not in s:
    if s.count(TIMER) != 1 or 'import { dirsReady } from "./dirs.js";\n' not in s:
        sys.exit("patch-tabs.py: anchor not found in %s; nothing changed (update the patch)" % main)
    s = s.replace('import { dirsReady } from "./dirs.js";\n', 'import { dirsReady } from "./dirs.js";\nimport { syncNames } from "./names.js";  ' + MARK + "\n")
    s = s.replace(TIMER, TIMER + "    cx.timer.every(3000, () => syncNames());  " + MARK + "\n")
(mod / "names.js").write_text(names)
main.write_text(s)
print("tabs-tasks: tabs name themselves (claude-code, devin, programs, folders)")
