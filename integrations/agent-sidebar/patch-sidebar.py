#!/usr/bin/env python3
"""Two small changes to the borrowed agent-sidebar mod (jeffarese/herdr-agents-sidebar):
1. a folder heading is drawn for every session, not only when a folder holds two or more;
2. keys.json "agent-sidebar.<n>" opens the nth session as the list shows it now (the order follows the list,
   so it moves when sessions change status; sub-agents are not counted).
3. a session without a pane is previewed in chat view (my session-peek bar over the `chat` mod, as a thread) instead of
   Herdr's terminal peek; programs with no chat (shells) keep the terminal peek.
4. a folder heading folds its sessions on click (chevron; the one you are in stays; search and filters open all).
5. a session with sub-agents under it gets a chevron that folds them (search and filters open all).
6. opening a session takes it out of pane-chat's "manual terminal" list, so it opens as chat (integrations/auto-chat).
7. agent-sidebar.close (⌘W in shepherdr-files): puts the focused agent away without ending it (its chat pane is closed, or its
   terminal parked: it keeps running, listed in the sidebar), whether or not it is the last pane of its space; anything else gets tab.close.
8. opening a session whose agent sits in a terminal pane switches that pane to chat (pane-chat.toggle) once it is shown: at once
   in the tab on screen, after 2.3 s elsewhere (pane-chat's header ignores a toggle in its first 2 s). Clicks and ⌘1..9 both.
9. the preview can be turned off (shared "session-peek.off", toggled by `herdr-app do agent-sidebar.preview`): opening a session
   without a pane then keeps it at once (a pane of its own, as chat) instead of previewing.
10. the scheduler's own session (herdr-automations, kept by herdr-core for Shepherdr) is not listed.
Re-applied by install.sh; idempotent; exact anchors, and it changes nothing if one is gone (fix it after a pin bump).
Usage: patch-sidebar.py <app home>"""
import sys, pathlib

f = pathlib.Path(sys.argv[1]) / "mods/agent-sidebar/main.js"
s = f.read_text()

EDITS = [
    ("Boolean(folder.key) && folder.sessions > 1;", "Boolean(folder.key);"),
    ('        else if (command === "density") this.toggleDensity();\n',
     '        else if (command === "density") this.toggleDensity();\n'
     '        else if (/^\\d+$/.test(command)) this.open(this.visible.filter(r => !r.inner)[Number(command) - 1]);\n'
     '        else if (command === "close") this.putAway();\n'
     '        else if (command === "preview") setShared("session-peek.off", !shared("session-peek.off"));\n'),
    ("  open(row) {\n",
     "  // Closing the focused pane without ending its agent: a chat just closes (the agent runs on without a pane), a terminal\n"
     "  // pane of an agent is parked. Shells and the rest close their tab as before.\n"
     "  putAway() {\n"
     "    const f = focused();\n"
     "    const p = panes().find(x => x.pane === f?.pane);\n"
     "    if (p?.mod === \"chat\") run(\"pane.close\", { pane: p.pane });\n"
     "    else if (p?.terminal && terminals().find(x => x.address === p.terminal)?.program?.agent) run(\"terminal.park\", { terminal: p.terminal });\n"
     "    else run(\"tab.close\");\n"
     "  }\n\n  open(row) {\n"),
]
OPEN_OLD = "  open(row) {\n    const action = openAction(row);\n"
OPEN_NEW = OPEN_OLD + (
    '    const chatty = !row?.pane && ["claude", "codex", "devin"].includes(row?.program?.key);\n'
    '    if (chatty && row.available && shared("session-peek.off")) {\n'
    '      const terminal = row.terminal ?? row.address;\n'
    '      run("terminal.keep", { terminal });\n'
    '      this.chatNext = { terminal, due: Date.now() + 2600 };\n'
    '      return;\n    }\n'
    '    if (chatty && row.available) {\n'
    '      const terminal = row.terminal ?? row.address;\n'
    '      setShared("session-peek.window", openOverlay({ kind: "window", key: "session-peek", width: 0.7, height: 0.8, layout: { type: "column", children: [\n'
    '        { type: "block", size: { px: 34 }, content: { mod: "session-peek", props: { terminal } } },\n'
    '        { type: "block", content: { mod: "chat", props: { terminal, thread: true } } }] } }));\n'
    '      return;\n    }\n')
OPEN_NEW += '    if (row?.pane) setShared("pane-chat.manual", (shared("pane-chat.manual") ?? []).filter(x => x !== (row.terminal ?? row.address)));\n'
OPEN_NEW += (
    '    const asTerminal = panes().find(x => x.pane === row?.pane);\n'
    '    if (asTerminal?.terminal && ["claude", "codex", "devin"].includes(row.program?.key))\n'
    '      this.chatNext = { pane: row.pane, due: Date.now() + (focused()?.tab === asTerminal.tab ? 200 : 2300) };\n')
EDITS.append((OPEN_OLD, OPEN_NEW))
EDITS.append((
    "    cx.timer.every(30000, cx => cx.notify());\n",
    "    cx.timer.every(30000, cx => cx.notify());\n"
    "    // A session opened from here that sits in a terminal pane goes to chat (open()).\n"
    "    cx.timer.every(250, () => {\n"
    "      const next = this.chatNext;\n"
    "      if (!next || Date.now() < next.due) return;\n"
    "      this.chatNext = null;\n"
    "      if (next.terminal) { run(\"pane.focus\", { terminal: next.terminal }); run(\"pane-chat.toggle\"); return; }\n"
    "      const p = panes().find(x => x.pane === next.pane);\n"
    "      if (p?.terminal && focused()?.pane === next.pane) run(\"pane-chat.toggle\");\n"
    "    });\n"))
EDITS.append((
    "    return h_flex().id(`folder-${group.key}:${section.id}:${folder.key}`).h(20).flex_none().pl(12).pr(8).gap(5).items_center()\n",
    "    const fk = `folder:${group.key}:${section.id}:${folder.key}`;\n    const open = this.isOpen(fk);\n"
    "    return h_flex().id(`folder-${group.key}:${section.id}:${folder.key}`).h(20).flex_none().pl(12).pr(8).gap(5).items_center()\n"
    "      .cursor_pointer().hover(s => s.bg(t.hover)).on_click((_e, cx) => this.toggle(fk, cx))\n"))
EDITS.append((
    "      .child(div().flex_none().text_color(t.dim).child(String(folder.sessions)));\n",
    "      .child(div().flex_none().text_color(t.dim).child(String(folder.sessions)))\n"
    "      .child(div().flex_1())\n      .child(glyph(open ? \"chevron-down\" : \"chevron-right\", 10).text_color(t.dim));\n"))
EDITS.append((
    "          for (const entry of folder.entries) if (open || entry.row.focused) add(",
    "          const shut = grouped && !this.isOpen(`folder:${group.key}:${section.id}:${folder.key}`);\n"
    "          for (const entry of folder.entries) if ((open && !shut) || entry.row.focused) add("))
EDITS.append((
    "          for (const entry of folder.entries) if ((open && !shut) || entry.row.focused) add(entry.row, this.row(t, entry, section.id, now, grouped));\n",
    "          let cut = null;\n"
    "          folder.entries.forEach((entry, i) => {\n"
    "            if (cut !== null && entry.depth > cut) return;\n"
    "            cut = null;\n"
    "            const kids = (folder.entries[i + 1]?.depth ?? 0) > entry.depth;\n"
    "            entry.kids = kids ? (this.isOpen(`kids:${entry.row.address}`) ? \"open\" : \"shut\") : null;\n"
    "            if (entry.kids === \"shut\") cut = entry.depth;\n"
    "            if ((open && !shut) || entry.row.focused) add(entry.row, this.row(t, entry, section.id, now, grouped));\n"
    "          });\n"))
EDITS.append((
    '      .when(Boolean(row.parent), el => el.child(glyph("sub", 11)',
    '      .when(Boolean(entry.kids), el => el.child(div().id(`kids-${row.address}`).absolute().left(0).top(0).bottom(0).w(14).flex().items_center().justify_center()\n'
    '        .cursor_pointer().on_click((_e, cx) => { cx.stop_propagation(); this.toggle(`kids:${row.address}`, cx); })\n'
    '        .child(glyph(entry.kids === "open" ? "chevron-down" : "chevron-right", 9).text_color(t.dim))))\n'
    '      .when(Boolean(row.parent), el => el.child(glyph("sub", 11)'))
EDITS.append((
    "    const all = holdDone(dropLeaving(built, ",
    "    const all = holdDone(dropLeaving(built.filter(r => r.title !== \"herdr-automations\"), "))
# 11. the row of the session on screen stays painted also when it is shown as a chat pane (focused().agent / pane), not only as a terminal.
EDITS.append((
    "    const on = row.focused;\n    const picked",
    "    const onScreen = focused();\n"
    "    const on = row.focused || (!row.inner && onScreen?.agent === row.address);\n    const picked"))
for old, new in EDITS:
    # The folding of sub-agents (the last edit on the entries loop) supersedes the one for folders: the second no longer shows.
    if new in s or (old.startswith("          for (const entry of folder.entries) if (open ||") and "let cut = null;" in s):
        continue
    if s.count(old) != 1:
        sys.exit("patch-sidebar.py: anchor not found in %s: %r; nothing changed (update the patch)" % (f, old[:50]))
    s = s.replace(old, new)
f.write_text(s)
print("agent-sidebar: folder headings always, agent-sidebar.<n> jumps")
