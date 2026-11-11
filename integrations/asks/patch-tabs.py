#!/usr/bin/env python3
"""Adds the Asks panel's button and engine to Shepherdr's `tabs-tasks`. Usage: patch-tabs.py <app home>

Asks is sachin-philip/herdr-agent-ask (MIT), installed from sources.tsv: its `asks` mod is the panel, and its `tabs-asks`
is Herdr's tab bar plus an Asks button and the engine that finds the questions. Shepherdr's tab bar is `tabs-tasks`, so
this copies tabs-asks' engine.js and state.js into it and adds, by exact-string edits, the same few things tabs-asks adds:
the engine and its timers, an "asks-toggle"/"asks-recheck" command, "asks" among the panels, and the button with its count.
Idempotent. If an anchor is gone (Shepherdr changed that code) it stops with an error and changes nothing.
"""
import os, shutil, sys

mods = os.path.join(sys.argv[1], "mods")
src, mod = os.path.join(mods, "tabs-asks"), os.path.join(mods, "tabs-tasks")
MAIN = os.path.join(mod, "main.js")

IMPORT_OLD = 'import { watchViews } from "./usage.js";\n'
IMPORT_NEW = IMPORT_OLD + '''import { Engine as AsksEngine } from "./engine.js";  // asks-patch
import { readState as asksState, loadConfig as asksConfig } from "./state.js";
'''

INIT_OLD = '    startBridge(cx);\n'
INIT_NEW = INIT_OLD + '''    // asks-patch: the Asks engine finds, reads and toasts questions before the panel is opened.
    this.asks = new AsksEngine();
    const asksCfg = (cx) => cx.spawn(async (cx) => { this.asks.config = await asksConfig(); cx.notify(); });
    asksCfg(cx);
    cx.timer.every(30000, asksCfg);
    cx.timer.every(1000, (cx) => this.asks.tick(cx));
'''

CMD_OLD = '        if (c === "close" && tab) closeTab(tab.id);\n'
CMD_NEW = '''        if (c === "asks-toggle" || c === "asks-open") {  // asks-patch
          const root = layout(), pan = find(root, "panel"), bod = find(root, "panel-body");
          if (pan && !pan.hidden && bod?.active === "asks" && c === "asks-toggle") run("layout.hide", { id: "panel" });
          else { run("layout.select", { stack: "panel-body", child: "asks" }); run("layout.show", { id: "panel" }); }
        }
        if (c === "asks-recheck") this.asks.recheck();
''' + CMD_OLD

DRAW_OLD = '    serveRemote();\n'
DRAW_NEW = DRAW_OLD + '    this.asks.tick(cx);  // asks-patch\n'

PANELS_OLD = '"tasks", ...(addonOn("artifacts")'
PANELS_NEW = '"tasks", "asks", ...(addonOn("artifacts")'

BTN_OLD = '      .child(panelButton("tasks", "Tasks",'
BTN_NEW = '''      .child(panelButton("asks", this.asks.config?.label ?? "Asks", "mods/asks/asks.svg", asksCount(spaces().find(s => s.active)?.id ?? focused()?.space)))  // asks-patch
''' + BTN_OLD

HELPER_OLD = 'export default class'
HELPER_NEW = '''// asks-patch: Asks' pending questions as [here, elsewhere] for the panel button's count.
function asksCount(space) {
  const pending = asksState().asks.filter(a => a.state === "pending");
  const here = pending.filter(a => a.space === space).length;
  return [here, 0];
}

''' + HELPER_OLD

IMPORT_HERDR_OLD = 'import { panes, run, openOverlay,'
IMPORT_HERDR_NEW = 'import { focused, panes, run, openOverlay,'

EDITS = [(IMPORT_OLD, IMPORT_NEW), (IMPORT_HERDR_OLD, IMPORT_HERDR_NEW), (HELPER_OLD, HELPER_NEW), (INIT_OLD, INIT_NEW),
         (CMD_OLD, CMD_NEW), (DRAW_OLD, DRAW_NEW), (PANELS_OLD, PANELS_NEW), (BTN_OLD, BTN_NEW)]

text, done = open(MAIN, encoding="utf-8").read(), 0
if "asks-patch" not in text:
    for old, new in EDITS:
        if text.count(old) != 1:
            sys.exit("patch-tabs: anchor not found in tabs-tasks/main.js (Shepherdr changed it): %r" % old[:60])
        text = text.replace(old, new)
        done += 1
    open(MAIN, "w", encoding="utf-8").write(text)
for f in ("engine.js", "state.js"):
    shutil.copy(os.path.join(src, f), os.path.join(mod, f))
print("tabs-tasks  patched for Asks (%d edits)" % done if done else "tabs-tasks  already patched for Asks")
