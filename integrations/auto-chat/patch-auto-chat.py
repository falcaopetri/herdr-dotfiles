#!/usr/bin/env python3
"""Agents open in chat view: a small, anchored addition to Shepherdr's `pane-chat` mod.
1. Each agent pane's header (it exists while the pane is shown) switches a terminal-view pane to chat 0.3 s after it
   appears (the same swap as its Chat/Terminal switch), unless that terminal is in shared "pane-chat.manual".
2. Choosing Terminal (the switch or pane-chat.toggle) puts the terminal in "pane-chat.manual", so it stays a terminal;
   clicking the session in agent-sidebar takes it out again (patch-sidebar.py), so it opens as chat.
Re-applied by install.sh; idempotent (an earlier version of block 1 is replaced); exact anchors, and it changes nothing
if one is gone (fix it after a Shepherdr update).
Usage: patch-auto-chat.py <app home>"""
import sys, pathlib

f = pathlib.Path(sys.argv[1]) / "mods/pane-chat/main.js"
s = f.read_text()

MARK = "    // Agents open in chat view (my patch, integrations/auto-chat)"
END = "        return;\n      }\n    });\n"
BLOCK = MARK + ''': a terminal-view agent pane goes to chat, unless chosen as terminal.
    cx.spawn(async (cx) => {
      for (;;) {
        await cx.sleep(300);
        const self = this.me();
        if (!self || self.mod === CHAT || !chatty(self)) continue;
        if ((shared("pane-chat.manual") ?? []).includes(self.terminal)) continue;
        if (Date.now() - this.born < 300 || Date.now() - lastSwap < 1500 || this.busy) continue;
        lastSwap = Date.now();
        this.toChat(self, cx);
      }
    });
'''
ANCHOR = "        else if (chatty(self)) this.toChat(self, cx);\n      }\n    });\n"
T_OLD = "  toTerminal(chat, cx) {\n    const terminal = agentOf(chat);\n"
T_NEW = T_OLD + '    if (terminal) setShared("pane-chat.manual", [...new Set([...(shared("pane-chat.manual") ?? []), terminal])].slice(-300));\n'

if MARK in s:
    i = s.index(MARK); j = s.index(END, i) + len(END)
    s = s[:i] + BLOCK + s[j:]
elif s.count(ANCHOR) == 1:
    s = s.replace(ANCHOR, ANCHOR + BLOCK)
else:
    sys.exit("patch-auto-chat.py: anchor not found in %s; nothing changed (update the patch)" % f)
if "pane-chat.manual\") ?? []), terminal" not in s:
    if s.count(T_OLD) != 1:
        sys.exit("patch-auto-chat.py: toTerminal anchor not found in %s; nothing changed (update the patch)" % f)
    s = s.replace(T_OLD, T_NEW)
f.write_text(s)
print("pane-chat: agents open in chat view")
