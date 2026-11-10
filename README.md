# herdr-dotfiles

My [herdr-app](https://herdr.dev) setup: keys, settings, program table, custom mods, and agent integrations.
Mirrors `~/.config/herdr-app`; only *my* files live here. Shipped layouts/mods/themes, app-written state
(`view.json`, `shared.json`, `data/`, ...) and third-party packages are not tracked.

| Path | What |
|---|---|
| `keys.json`, `settings.json`, `programs.json` | copied into the herdr-app home |
| `my-icons/` | icons referenced by `programs.json` (Devin) |
| `mods/plate/` | panel for [Plate](https://github.com/falcaopetri/plate) |
| `integrations/devin/` | hooks that report Devin's status (idle/working/blocked/done) to herdr via OSC 7501 |

## Install

    ./install.sh        # requires jq

Backs up replaced files as `*.bak`. `HERDR_APP_HOME` / `DEVIN_CONFIG_HOME` override locations.
Re-running is safe. Then restart running Devin sessions.

## Devin

| Devin hook | Herdr status |
|---|---|
| SessionStart | idle |
| UserPromptSubmit, PreToolUse, PostToolUse | working |
| PermissionRequest | blocked |
| Stop | done |

The script writes to `/dev/tty`, falling back to the parent's tty, since Devin runs hooks without a controlling terminal.
Verify with `hc ls --json`.
