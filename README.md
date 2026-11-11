# herdr-dotfiles

My setup for the [Herdr](https://herdr.dev) desktop app: the
[Shepherdr](https://github.com/eliasstravik/shepherdr) layout, a shortcuts window, reopen-closed-tab and
Devin status reporting. Nothing else: no custom layouts, no leader menu, no other mods.
Only *my* files live here; other people's code is fetched, pinned, from their own repos.

## Install

```sh
git clone https://github.com/falcaopetri/herdr-dotfiles ~/herdr-dotfiles
~/herdr-dotfiles/install.sh              # needs jq, git, rsync, python3; the Herdr app opened once
```

Re-run after `git pull` to update. Whatever it replaces is saved in `~/.config/herdr-app/backup-<time>/`.
`keys.json` and `programs.json` are merged (this repo wins per key), so keys from other sources survive.
`./install.sh --no-shepherdr` skips Shepherdr. `HERDR_APP_HOME`, `DEVIN_CONFIG_HOME` and `SHEPHERDR_SRC`
(default `~/src/shepherdr`) override locations.
Then `shepherdr doctor`, and `ctrl+shift+l` to pick the Shepherdr layout.

## What it installs

| Piece | What | From | License |
|---|---|---|---|
| Shepherdr | layout + 28 mods + helpers (`herdr-task`, ...) + agent hooks; pinned in `shepherdr.pin`, cloned to `~/src/shepherdr`, installed with `--no-build` (no web service) | [eliasstravik/shepherdr](https://github.com/eliasstravik/shepherdr) | see its repo |
| `keys-help` | all shortcuts window (`cmd+/`) | this repo; based on Herdr's `help` | Apache-2.0 |
| `reopen-tab` | reopen closed tabs (`cmd+shift+t`) | [mustafaTokmak/herdr-reopen-tab](https://github.com/mustafaTokmak/herdr-reopen-tab) | MIT |
| `file-editor` | file tree and tabbed editor (syntax highlighting, Markdown/SVG preview); no layout uses it yet, open with `herdr-app do pane.split --direction right --mod file-editor` | [werlang/herdr-file-editor](https://github.com/werlang/herdr-file-editor) | none stated |
| Devin hooks | Devin's status in Herdr, and its icon (`programs.json`) | `integrations/devin/` | |

Shepherdr runs programs (`herdr-task`, `git`, `gh`, `hc`, ...), reads files outside its mod folders and reaches
GitHub (and ElevenLabs, if you turn on voice). `reopen-tab` runs `hc` and `git` and keeps a ledger in `data/reopen-tab/`.
`file-editor` reads and writes files (and runs `git`, plus `herdr-core exec` over SSH).
Not installed: Shepherdr's web app/service and voice (they need bun, and tailscale for the web app).
Run `~/src/shepherdr/install.sh` without `--no-build` to add them.

## Keys (`keys.json`)

| Keys | Action |
|---|---|
| `cmd+/`, `cmd+shift+/` | all shortcuts |
| `cmd+shift+t` | reopen the last closed tab |
| `cmd+l` | focus the input box of the Shepherdr chat on screen (`chat.focus`) |
| `cmd+n` | Shepherdr's New space dialog (`tabs-tasks.newspace`), in the Shepherdr layout; same as `ctrl+shift+n` |

Shepherdr merges its own keys (`ctrl+k` jump, `ctrl+shift+?`, `alt+1..9`, ...) at install.

## Updating pins

`./upstream.sh` (needs `gh`) says which pins (`shepherdr.pin`, `sources.tsv`) have news. To move one, edit the
commit and re-run `./install.sh`.

## Layout of this repo

| Path | What |
|---|---|
| `keys.json`, `programs.json`, `my-icons/` | merged into the app home |
| `mods/keys-help/` | my mod |
| `sources.tsv` | borrowed mods: repo, path, commit, license, default/optional |
| `shepherdr.pin` | Shepherdr's repo and commit |
| `install.sh`, `upstream.sh` | install; newer commits upstream |
| `integrations/devin/` | hooks reporting Devin's status to Herdr (OSC 7501) |

## Devin

| Devin hook | Herdr status |
|---|---|
| SessionStart | idle |
| UserPromptSubmit, PreToolUse, PostToolUse | working |
| PermissionRequest | blocked |
| Stop | done |

The script writes to `/dev/tty`, falling back to the parent's tty, since Devin runs hooks without a controlling terminal.
Verify with `hc ls --json`.
