#!/usr/bin/env python3
"""Makes the borrowed tmux-prefix mod mine: the prefix is shown as cmd+e (keys.json opens it), my own commands sit at the
top of its BINDINGS list, and "a" is a live Keep awake toggle (`caffeinate -dis -w <Herdr's pid>`, so quitting Herdr ends it; pid in <app home>/keep-awake.pid): the
row shows ON/off, flips in place and leaves the popup open. Anchored edits; nothing changes if one is gone, or if the
patch was already applied (fix it after a pin bump). Re-applied by install.sh.
Usage: patch-bindings.py <app home>"""
import sys, pathlib

f = pathlib.Path(sys.argv[1]) / "mods/tmux-prefix/main.js"
s = f.read_text()
if "@awake" in s:
    print("tmux-prefix already patched"); sys.exit(0)

MINE = '''const BINDINGS = [
  ["a", "Keep awake (no sleep)", "@awake"],
  ["b", "Submit bug / feature request", "mod.open", { name: "submit" }],
  ["e", "Devin sessions (archive/restore)", "mod.open", { name: "devin-sessions" }],
  ["s", "Keep session (peek)", "session-peek.keep"],
  ["r", "Reopen closed tab", "mod.open", { name: "reopen-tab" }],
  ["i", "Focus chat input", "chat.focus"],
  ["/", "All shortcuts", "mod.open", { name: "keys-help" }],
'''
METHODS = '''  pidFile() { return `${appHome()}/keep-awake.pid`; }

  refreshAwake(cx) {
    cx.spawn(async (cx) => {
      const r = await exec("sh", ["-c", `p=$(cat "${this.pidFile()}" 2>/dev/null); [ -n "$p" ] && ps -p "$p" -o comm= 2>/dev/null | grep -q caffeinate && echo on || echo off`]);
      this.awake = r.stdout.trim() === "on";
      cx.notify();
    });
  }

  toggleAwake(cx) {
    const f = this.pidFile();
    const script = this.awake
      ? `kill "$(cat "${f}")" 2>/dev/null; rm -f "${f}"`
      : `h=$(pgrep -x Herdr | head -1); nohup caffeinate -dis \\${h:+-w $h} >/dev/null 2>&1 & echo $! > "${f}"`;
    cx.spawn(async (cx) => {
      try { await exec("sh", ["-c", script]); this.awake = !this.awake; } catch (e) { console.log(`tmux-prefix: ${e}`); }
      cx.notify();
    });
  }

  dismiss() {'''
EDITS = [
  ('import { closeOverlay, focused, hc, nextCommand, props, run, theme } from "herdr";',
   'import { appHome, closeOverlay, exec, focused, hc, nextCommand, props, run, theme } from "herdr";'),
  ("const BINDINGS = [\n", MINE),
  ("    this.all = false;\n", "    this.all = false;\n    this.awake = null;\n    this.refreshAwake(cx);\n"),
  ("  dismiss() {", METHODS),
  ("    if (!repeatable) this.dismiss();\n",
   '    if (command === "@awake") { this.toggleAwake(cx); return; }\n    if (!repeatable) this.dismiss();\n'),
  ('"Ctrl+B · waiting for a key"', '"⌘E · waiting for a key"'),
  ('"Esc cancel · ^B send prefix"', '"Esc cancel"'),
  ('.child(div().text_color(t.dim).child(repeatable ? "repeat" : ""))',
   '.child(div().text_color(key === "a" && this.awake ? t.accent : t.dim).child(key === "a" ? (this.awake === null ? "" : this.awake ? "● ON" : "○ off") : repeatable ? "repeat" : ""))'),
]
for old, new in EDITS:
    if s.count(old) != 1:
        sys.exit("patch-bindings.py: anchor not found (%r); nothing changed (update the patch)" % old[:40])
    s = s.replace(old, new)
f.write_text(s)
print("tmux-prefix: my commands, cmd+e header, live Keep awake")
