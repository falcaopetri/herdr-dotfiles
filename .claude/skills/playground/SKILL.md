---
name: playground
description: Open a disposable second Herdr window (own home, theme inverse to the main one) to try mods, layouts, themes or installers without touching the user's real setup. Use when the user says /playground, or wants to "brincar", test or experiment with Herdr.
---

# Herdr playground

A second Herdr app with its own home, `~/.config/herdr-app-test`, started with `HERDR_APP_HOME`. Mods, keys, layouts and settings live in that home, so what we break there never reaches `~/.config/herdr-app`. Speak Portuguese with the user.

## Open it

1. **Copy the real home** (skip if the user wants to keep what is already there):
   ```sh
   rsync -a --delete --exclude 'herdr-app.sock' --exclude 'backup-*' ~/.config/herdr-app/ ~/.config/herdr-app-test/
   ```
   Never `cp -R`: it fails on the socket (`cannot create special file`) and drags the 50+ `backup-*` folders along. Before `--delete`, check no playground window is running (step 4), or its socket is deleted under it.
2. **Make it look different.** Read the main appearance: `defaults read -g AppleInterfaceStyle` prints `Dark` in dark mode and errors in light mode (unless the main `settings.json` has an `appearance`, which wins). Set the opposite in the playground's `settings.json`:
   - main dark → `"appearance": "light", "theme": "paper"`
   - main light → `"appearance": "dark", "theme": "graphite"`

   Use `appearance`: `app.theme` only sets the half of the theme pair that matches the current appearance, so on its own it changes nothing visible. Edit the JSON with python, not sed (BSD `sed -i` needs a suffix). It applies live.
3. **Start it** in the background, so it does not block the shell:
   ```sh
   (HERDR_APP_HOME=~/.config/herdr-app-test nohup herdr-app >/dev/null 2>&1 &)
   ```
4. **Verify**: `HERDR_APP_HOME=~/.config/herdr-app-test herdr-app status` answers with the window's state, and `herdr-app shot <file.png>` (same variable) saves a frame; read the PNG to confirm the inverse look. Tell the user: "a janela clara/escura é o playground".

Every `herdr-app …` and `hc` command aimed at the playground needs `HERDR_APP_HOME=~/.config/herdr-app-test` in front. Without it the command reaches the main window.

## What is not isolated

- **Terminals.** `hc` (herdr-core) is shared and the copied `view.json` points at the same terminals, so the playground shows the user's real terminals. Typing in one types in the real one. Open new tabs there for experiments.
- **This repo's `install.sh`.** It honors `HERDR_APP_HOME`, so to try a change from the repo in the playground run `HERDR_APP_HOME=~/.config/herdr-app-test ./install.sh --no-shepherdr`. Without `--no-shepherdr` it touches `~/src/shepherdr` and `~/.config/shepherdr`, which are global. Never run it without the variable while testing: it would write into the live app home.
- **Installers that write outside the home** (herdr-chat writes `~/.local/share/herdr-chat`, notes in `~/.claude/CLAUDE.md`, `~/.pi`, `~/.codex`, and `hc` templates). Read the installer first, pass `HERDR_APP_HOME=...`, and prefer its opt-outs (`--no-subagents`). Say which parts stay global.
- **Name collisions.** The user's setup already has a mod called `chat` (the Chat/Terminal toggle; others like `chat-call`, `confirm-chat` depend on it). herdr-chat refuses to overwrite it: in the playground only, `mv ~/.config/herdr-app-test/mods/chat ~/.config/herdr-app-test/mods/chat.orig` first, and expect the `*-chat` mods to misbehave there.

## Close or reset it

- Close: find the process with `ps eww -ax | grep -E 'herdr-app$|HERDR_APP_HOME=.*herdr-app-test'`, check the PID's `HERDR_APP_HOME` says `herdr-app-test`, then `kill <pid>`. Never `pkill herdr-app`: the main window is `Herdr.app`, a different process, but the check costs nothing.
- Reset to the real setup: close it, then run step 1 again.
- Forget it: close it, then `rm -rf ~/.config/herdr-app-test`.
