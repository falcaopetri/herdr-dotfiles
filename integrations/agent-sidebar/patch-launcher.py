#!/usr/bin/env python3
"""agent-sidebar's launcher (the + and cmd+n): a pi, claude, codex or devin session started in a space that is already
open (the launcher's "tab" placement) opens as a chat of the herdr-chat mod (tab.new {mod: "chat", props: {chat, provider,
cwd}}, what herdr-chat's new-chat does) instead of a terminal running the agent. With no space open for the folder (e.g. just after the app starts) it opens the space, adds the chat tab (space.new takes
no mod) and closes the shell tab. Anything else (a shell, a program, another machine) is as before.
Only for the herdr-chat `chat` mod: install.sh applies this when mods/new-chat exists (herdr-chat installed).
Idempotent; exact anchors, and it changes nothing if one is gone (fix it after a pin bump).
Usage: patch-launcher.py <app home>"""
import sys, pathlib

f = pathlib.Path(sys.argv[1]) / "mods/agent-sidebar/launcher.js"
s = f.read_text()
if "chatNewSpace(" in s:
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
if "chatOpen(" not in s:
    if s.count(START_OLD) != 1:
        sys.exit("patch-launcher.py: anchor not found in %s; nothing changed (update the patch)" % f)
    s = s.replace(START_OLD, START_NEW)

# A new space (none open for the folder, e.g. just after the app starts): space.new takes no mod, so open the space,
# put the chat tab in it, and close the shell tab it started with.
G_OLD = "  if (!program || !tabSpace || view.machine != null || !CHAT_AGENTS.includes(program.key)) return false;\n"
G_NEW = "  if (!program || view.machine != null || !CHAT_AGENTS.includes(program.key)) return false;\n"
U_OLD = '  run("tab.new", { name: program.key, space: tabSpace.id, mod: "chat", props: { chat, provider: program.key, cwd } });\n  return true;\n}\n'
U_NEW = ('  if (!tabSpace) { chatNewSpace(program, cwd, chat); return true; }\n' + U_OLD +
         '\nfunction chatNewSpace(program, cwd, chat) {\n'
         '  // One shell does all three steps: the launcher is closed (its JS stops) right after start(), so nothing can await here.\n'
         '  const props = JSON.stringify({ chat, provider: program.key, cwd });\n'
         '  const sh = \'o=$(herdr-app do space.new --folder "$1") || exit 1; \'\n'
         '    + \'sp=$(printf %s "$o" | jq -r .space); tb=$(printf %s "$o" | jq -r .tab); \'\n'
         '    + \'herdr-app do tab.new --space "$sp" --name "$2" --mod chat --props "$3" >/dev/null && \'\n'
         '    + \'herdr-app do tab.close --id "$tb" --confirmed true >/dev/null\';\n'
         '  exec("sh", ["-c", sh, "sh", cwd, program.key, props]);\n}\n')
if s.count(G_OLD) != 1 or s.count(U_OLD) != 1:
    sys.exit("patch-launcher.py: chatOpen anchors not found in %s; nothing changed (update the patch)" % f)
f.write_text(s.replace(G_OLD, G_NEW).replace(U_OLD, U_NEW))
print("agent-sidebar launcher: agents start as herdr-chat chats (in a new space too)")
