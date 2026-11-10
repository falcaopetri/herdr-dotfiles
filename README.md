# herdr-devin

Makes [Devin for Terminal](https://devin.ai) show up as a proper agent in [herdr-app](https://herdr.dev):
name, icon, "New → Devin" in the + menu, and live status (idle / working / blocked / done).

## What it does

1. `programs.json` entry — names the program `Devin`, gives it an icon and a launcher (`run: ["devin"]`).
2. `bin/herdr-status.sh` — writes the OSC 7501 status escape (`state=…:app=devin`) to the terminal.
3. Devin hooks in `~/.config/devin/config.json` call that script:

| Devin hook | Herdr status |
|---|---|
| SessionStart | idle |
| UserPromptSubmit, PreToolUse, PostToolUse | working |
| PermissionRequest | blocked |
| Stop | done |

## Install

    ./install.sh

Requires `jq`. Merges into existing config (backups: `*.bak`), and only replaces hook entries that reference `herdr-status.sh`.
Override locations with `HERDR_APP_HOME` / `DEVIN_CONFIG_HOME`. Restart running Devin sessions afterwards.

## Notes

- The script finds the terminal via `/dev/tty`, falling back to the parent process's tty, because Devin runs hooks without a controlling terminal.
- Verify with `hc ls --json`: the Devin terminal should report `status` changing.
