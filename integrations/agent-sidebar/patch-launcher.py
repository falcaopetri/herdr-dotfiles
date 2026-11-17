#!/usr/bin/env python3
"""agent-sidebar's launcher (the + and cmd+n): a pi, claude, codex or devin session started in a space that is already
open (the launcher's "tab" placement) opens as a chat of the herdr-chat mod (tab.new {mod: "chat", props: {chat, provider,
cwd}}, what herdr-chat's new-chat does) instead of a terminal running the agent. Anything else (a shell, a program, another
machine, a new space: space.new takes no mod) is as before.
Only for the herdr-chat `chat` mod: install.sh applies this when mods/new-chat exists (herdr-chat installed).
Idempotent; exact anchors, and it changes nothing if one is gone (fix it after a pin bump).
Usage: patch-launcher.py <app home>"""
import sys, pathlib

f = pathlib.Path(sys.argv[1]) / "mods/agent-sidebar/launcher.js"
s = f.read_text()
if "chatOpen(" in s:
    print("agent-sidebar launcher: already opens chats")
    sys.exit(0)

START_OLD = "  closeOverlay(props().overlay);\n  run(action.name, action.args);\n}\n"
START_NEW = ("  closeOverlay(props().overlay);\n"
             "  if (chatOpen(view, program, folder, where === \"tab\" ? tabSpace : null)) return;\n"
             "  run(action.name, action.args);\n}\n\n"
             "// herdr-chat: an agent session in an open space is a chat tab (the host runs the agent), not a terminal.\n"
             "const CHAT_AGENTS = [\"pi\", \"claude\", \"codex\", \"devin\"];\n"
             "function chatOpen(view, program, folder, tabSpace) {\n"
             "  if (!program || !tabSpace || view.machine != null || !CHAT_AGENTS.includes(program.key)) return false;\n"
             "  const chat = `c-${Math.random().toString(16).slice(2, 10).padEnd(8, \"0\")}`;\n"
             "  const cwd = folder.path === \"~\" ? home() : folder.path;\n"
             "  run(\"tab.new\", { name: program.key, space: tabSpace.id, mod: \"chat\", props: { chat, provider: program.key, cwd } });\n"
             "  return true;\n}\n")
if s.count(START_OLD) != 1:
    sys.exit("patch-launcher.py: anchor not found in %s; nothing changed (update the patch)" % f)
f.write_text(s.replace(START_OLD, START_NEW))
print("agent-sidebar launcher: agents in an open space start as herdr-chat chats")
