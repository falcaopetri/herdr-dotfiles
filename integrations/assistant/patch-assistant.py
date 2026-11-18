#!/usr/bin/env python3
"""Lets herdr-chat's `chat` mod open Shepherdr's Assistant tab. Shepherdr's coordinator opens it with
`tab.new {mod: "chat", props: {role: "coordinator", template, space, folder, slot, settings}}`; herdr-chat only knows
`{chat, provider, cwd}`, so it became chat "c-unknown", never found its pane and sat on "Connecting… (waiting for the
chat's tab)". With this patch the chat id is derived from `slot` (stable, so a reopened tab keeps its history), the folder
is `folder` and the agent is `settings.agent`. Idempotent; re-applied by install.sh (only while herdr-chat is installed).
Usage: patch-assistant.py <app home>"""
import pathlib, sys

home = pathlib.Path(sys.argv[1]) / "mods/chat"

HELPER = '''
// Patched by herdr-dotfiles (integrations/assistant): the Assistant tab has a slot, not a chat id.
export const chatIdOf = (p) => {
  if (p?.chat) return p.chat;
  if (!p?.slot) return null;
  let h = 2166136261;
  for (const c of String(p.slot)) h = Math.imul(h ^ c.charCodeAt(0), 16777619) >>> 0;
  return "c-" + h.toString(16).padStart(8, "0");
};
'''

def edit(name, pairs, append=None, marker="chatIdOf"):
    f = home / name
    s = f.read_text()
    if marker in s:
        print(f"{name}: already patched"); return
    for old, new in pairs:
        if s.count(old) != 1:
            sys.exit(f"patch-assistant.py: anchor not found in {name} (redo the patch): {old[:60]}")
        s = s.replace(old, new)
    f.write_text(s + (append or ""))
    print(f"{name}: patched")

edit("util.js", [], append=HELPER)
edit("hostpane.js", [
    ('import { randomBytes } from "crypto";', 'import { randomBytes } from "crypto";\nimport { chatIdOf } from "./util.js";'),
    ("c.props?.chat === chat && !me", "chatIdOf(c.props) === chat && !me"),
])
edit("main.js", [
    ("PROVIDER_NAMES, alpha,", "PROVIDER_NAMES, chatIdOf, alpha,"),
    ('this.chat = p.chat ?? "c-unknown";', 'this.chat = chatIdOf(p) ?? "c-unknown";'),
    ("this.provider = p.provider ?? null;", "this.provider = p.provider ?? (PROVIDERS.includes(p.settings?.agent) ? p.settings.agent : null);"),
    ("this.cwd = p.cwd || null;", "this.cwd = p.cwd || p.folder || null;"),
    ("this.docPanes.filter((x) => x.props?.chat === this.chat)", "this.docPanes.filter((x) => chatIdOf(x.props) === this.chat)"),
    ("this.docPanes.map((x) => x.props?.chat)", "this.docPanes.map((x) => chatIdOf(x.props))"),
])
