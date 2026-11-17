#!/usr/bin/env python3
"""reopen-tab brings a closed herdr-chat chat tab back as a chat. A chat tab's only terminal is its host
(`herdr-chat-host serve --chat <id> --cwd <dir> --provider <p> ...`), so the borrowed mod reopened it as a plain terminal
running that host: no chat view, just the host's text under pane-chat's Chat/Terminal toggle. With this patch a closed tab
whose first terminal is such a host is reopened with tab.new {mod: "chat", props: {chat, provider, cwd}}: the same chat id,
so the host resumes the session its registry records. (A space reopened as a whole, and a chat split beside other panes,
still come back the old way.)
Only for the herdr-chat `chat` mod: install.sh applies this when mods/new-chat exists. Idempotent; exact anchors, and it
changes nothing if one is gone (fix it after a pin bump).
Usage: patch-chat.py <app home>"""
import sys, pathlib

mod = pathlib.Path(sys.argv[1]) / "mods/reopen-tab"
plan, main = mod / "plan.js", mod / "main.js"
ps, ms = plan.read_text(), main.read_text()
if "chatOf" in ps and "chatOf" in ms:
    print("reopen-tab already reopens chats")
    sys.exit(0)

PLAN_ANCHOR = "/** The agent command for `tab.new`/`space.new` (Herdr wraps it in the shell itself), or null for a shell. */\n"
PLAN_NEW = '''/** A herdr-chat host (`herdr-chat-host serve --chat <id> --cwd <dir> --provider <p> ...`): the props of its chat tab, else null. */
export function chatOf(record) {
  const { folder, argv } = start(record);
  const { cmd } = unwrap(argv);
  const i = (cmd || []).findIndex((a, k) => cmd[k + 1] === "serve" && /(^|\\/)herdr-chat-host$|(^|\\/)host\\/main\\.(ts|js)$/.test(a));
  if (i < 0) return null;
  const flag = (name) => { const j = cmd.indexOf(name, i); return j >= 0 ? cmd[j + 1] : null; };
  const chat = flag("--chat");
  if (!chat) return null;
  const cwd = flag("--cwd") || folder;
  return { chat, provider: flag("--provider") || "pi", ...(cwd ? { cwd } : {}) };
}

'''
IMPORT_OLD = "import { closedTabs, nextClose, position, splitArgv, tabArgv, start,"
IMPORT_NEW = "import { chatOf, closedTabs, nextClose, position, splitArgv, tabArgv, start,"
TAB_OLD = '  run("tab.new", { space, ...(name ? { name } : {}), ...(folder ? { folder } : {}), ...(argv ? { argv } : {}) });\n'
TAB_NEW = ('  const chat = chatOf(first);\n'
           '  if (chat) run("tab.new", { space, name: name || chat.provider, mod: "chat", props: chat });\n'
           '  else run("tab.new", { space, ...(name ? { name } : {}), ...(folder ? { folder } : {}), ...(argv ? { argv } : {}) });\n')
for s, a, label in ((ps, PLAN_ANCHOR, "plan.js"), (ms, IMPORT_OLD, "main.js import"), (ms, TAB_OLD, "main.js tab.new")):
    if s.count(a) != 1:
        sys.exit("patch-chat.py: anchor not found (%s); nothing changed (update the patch)" % label)
plan.write_text(ps.replace(PLAN_ANCHOR, PLAN_NEW + PLAN_ANCHOR))
main.write_text(ms.replace(IMPORT_OLD, IMPORT_NEW).replace(TAB_OLD, TAB_NEW))
print("reopen-tab: a closed chat tab comes back as a chat")
