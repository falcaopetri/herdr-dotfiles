#!/usr/bin/env python3
"""reopen-tab brings a closed herdr-chat chat tab back as a chat. A chat tab's only terminal is its host
(`herdr-chat-host serve --chat <id> --cwd <dir> --provider <p> ...`), so the borrowed mod reopened it as a plain terminal
running that host: no chat view, just the host's text under pane-chat's Chat/Terminal toggle. With this patch a closed tab
whose first terminal is such a host is reopened with tab.new {mod: "chat", props: {chat, provider, cwd}}: the same chat id,
so the host resumes the session its registry records. (A space reopened as a whole is handled too: its shell tab is swapped for the chat tab. A chat split beside other panes
still comes back the old way.)
Only for the herdr-chat `chat` mod: install.sh applies this when mods/new-chat exists. Idempotent; exact anchors, and it
changes nothing if one is gone (fix it after a pin bump).
Usage: patch-chat.py <app home>"""
import sys, pathlib

mod = pathlib.Path(sys.argv[1]) / "mods/reopen-tab"
plan, main = mod / "plan.js", mod / "main.js"
ps, ms = plan.read_text(), main.read_text()
if "chatOf" in ps and "chatOf(first)" in ms and "chatSpace" in ms and "argv && !chatOf(first)" in ms:
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
SP_OLD = """  const pane = await until(cx, () => panesIn(firstTab)[0], "tab's pane");
  await remember({ spaces: { [plan.oldSpace]: space } });
"""
SP_NEW = """  const chatSpace = chatOf(first);
  if (chatSpace) {
    const shell = firstTab;
    run("tab.new", { space, name: tab || chatSpace.provider, mod: "chat", props: chatSpace });
    const chatTab = (await until(cx, () => tabsOf(space).find((t) => t.id !== shell), "chat tab")).id;
    run("tab.close", { id: shell });
    const chatPane = await until(cx, () => panesIn(chatTab)[0], "tab's pane");
    await remember({ spaces: { [plan.oldSpace]: space } });
    await splitRest(cx, chatTab, chatPane, rest);
    return { space, tab: chatTab, pane: chatPane };
  }
"""
SN_OLD = '  run("space.new", { ...(name ? { name } : {}), ...(folder ? { folder } : {}), ...(tab ? { tab } : {}), ...(argv ? { argv } : {}),'
SN_NEW = '  run("space.new", { ...(name ? { name } : {}), ...(folder ? { folder } : {}), ...(tab ? { tab } : {}), ...(argv && !chatOf(first) ? { argv } : {}),'
edits = [  # (file text, anchor, replacement, label, already-applied marker)
    ("p", PLAN_ANCHOR, PLAN_NEW + PLAN_ANCHOR, "plan.js", "export function chatOf"),
    ("m", IMPORT_OLD, IMPORT_NEW, "main.js import", "import { chatOf,"),
    ("m", TAB_OLD, TAB_NEW, "main.js tab.new", "const chat = chatOf(first)"),
    ("m", SP_OLD, SP_NEW + SP_OLD, "main.js space.new", "const chatSpace"),
    ("m", SN_OLD, SN_NEW, "main.js space.new argv", "argv && !chatOf(first)"),
]
texts = {"p": ps, "m": ms}
for f, old, new, label, mark in edits:
    if mark in texts[f]:
        continue
    if texts[f].count(old) != 1:
        sys.exit("patch-chat.py: anchor not found (%s); nothing changed (update the patch)" % label)
    texts[f] = texts[f].replace(old, new)
plan.write_text(texts["p"])
main.write_text(texts["m"])
print("reopen-tab: a closed chat tab (or space) comes back as a chat")
