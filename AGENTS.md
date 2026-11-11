# herdr-dotfiles

This repo is the source of truth for my customizations of the [Herdr](https://herdr.dev) desktop app. A space opens
here whenever I want to change how my Herdr works: keys, mods, icons, agent hooks, Shepherdr. The README is the user-facing
description; this file is for the agent working here.

## Two folders, one direction

| Folder | Role |
|---|---|
| `~/herdr-dotfiles` (this repo) | what I own and version. Edit here. |
| `~/.config/herdr-app` (`$HERDR_APP_HOME`) | the Herdr app's live home, written by the app, Shepherdr and `install.sh`. Not versioned. |

(It is `herdr-app`, not `herdr`: there is no `~/.config/herdr`.)

Flow: edit the repo, then run `./install.sh` (safe to re-run; add `--no-shepherdr` to skip the Shepherdr step when only
my own files changed). It copies or merges into the app home and saves whatever it replaces in
`~/.config/herdr-app/backup-<time>/`. The app watches its folder and redraws within about a second.

Prototyping directly in the app home is fine, since changes apply live. But anything worth keeping must be ported back
into this repo, or the next `install.sh` will overwrite or lose it (`mods/<name>` is replaced with `rsync --delete`).

## What lives where

| Path here | Goes to (in the app home) | How |
|---|---|---|
| `keys.json`, `programs.json` | same names | **merged** with jq (`app * repo`): this repo wins per key, other keys survive |
| `my-icons/` | `my-icons/` | copied |
| `mods/keys-help/` | `mods/keys-help/` | my own mod, synced with `--delete` |
| `sources.tsv` | `mods/<name>/` | other people's mods: fetched at install, pinned to a commit, never copied into this repo |
| `shepherdr.pin` | `~/src/shepherdr` clone, installed with `--no-build --yes --keys keep` | pinned commit of [eliasstravik/shepherdr](https://github.com/eliasstravik/shepherdr) |
| `integrations/devin/` | Devin's hooks config | Devin status in Herdr (OSC 7501) |

Do not edit, in the app home or here, anything that belongs to someone else:
- Shepherdr's mods and layout (`tabs-tasks`, `chat`, `newspace`, `layouts/shepherdr.json`, ...) and Herdr's own shipped
  mods and layouts. They are replaced on update. To change their behavior, use a key, a setting, or clone the mod under a new
  name into `mods/` here.
- Borrowed mods listed in `sources.tsv` (`reopen-tab`). Move the pin instead.

Only my own files are committed. No custom layouts, no other mods for now (see README).

## Keys

`keys.json` has sections: `global`, `terminal`, `mod:<name>` and `layout:<name>`. Key names use dashes (`cmd-shift-t`).
Shepherdr's keys are merged into the app home by its own installer. Mine live here and
only carry what I added or overrode.
- A key meant only for the Shepherdr layout goes in `layout:shepherdr` (e.g. `cmd-n` → `tabs-tasks.newspace`, which
  overrides the global `cmd-n` → `space.new`).
- Check for a clash first: `grep '"cmd-n"' ~/.config/herdr-app/keys.json`.
- Keep the README's key table in sync with `keys.json`.
- `ctrl-alt-shift-escape` is the escape hatch and cannot be rebound: it sets the shown layout and `keys.json` aside and returns
  to the default layout.

## Writing or changing a mod

The Herdr app writes its own full guide to `~/.config/herdr-app/AGENTS.md` on every start (about 1,000 lines, overwritten, never
edit it). **Read it before writing a mod or layout**, along with `gpui-kit.d.ts` and `herdr.d.ts` next to it, which are the
truth for the API. In short:
- A mod is a folder with `mod.json` and `main.js` (gpui-kit: JS that describes GPUI elements; no DOM, no CSS, no Node).
- Verify with `herdr-app check <mod folder>`; never call a mod done without a passing check, and also try it in the app.
  `herdr-app shot` saves a PNG of the window for UI work.
- An invalid file keeps the last good version and writes `<name>.error` (`keys.error`, `layout.error`, `settings.error`,
  `programs.error`) in the app home. Look there after every edit.
- `keys-help` is derived from Herdr's `help` mod (Apache-2.0); keep attribution when touching it.

## Pins and updates

`./upstream.sh` (needs `gh`) reports which pins (`shepherdr.pin`, `sources.tsv`) have newer commits. To move one, edit the
commit and re-run `./install.sh`. Read the upstream diff first: these mods run programs and read files on this machine
(see the README's note on what Shepherdr and `reopen-tab` touch).

## Rules

- Do not commit secrets, tokens or anything from `~/.config/herdr-app/data/`, the backups, or `*.error` files.
- Do not delete `backup-*` folders in the app home without asking.
- Match the existing style of `install.sh`: `set -euo pipefail`, idempotent, back up before replacing.
- After changing install behavior, keys or the file layout, update the README in the same change.
- Commit only when asked. Messages are short and imperative, in English, like the existing log
  (`Add cmd+l: focus the on-screen Shepherdr chat input`).
- Shepherdr's source is at `~/src/shepherdr` (docs in `docs/`, e.g. `settings.md`, `parity/dialogs.md`). Read it for how its
  parts behave, and don't edit it. It is a pinned clone.
- Tools: `herdr-app` (the window: `status`, `check`, `shot`), `hc` (herdr-core: terminals and agents), `herdr-task`
  and `shepherdr doctor` (Shepherdr).
