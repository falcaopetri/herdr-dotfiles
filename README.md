# herdr-dotfiles

My setup for the [Herdr](https://herdr.dev) desktop app: the
[Shepherdr](https://github.com/eliasstravik/shepherdr) layout, a shortcuts window, reopen-closed-tab and
Devin status reporting. Nothing else: no hand-made layouts, no other mods.
Only *my* files live here; other people's code is fetched, pinned, from their own repos.

## Install

```sh
git clone https://github.com/falcaopetri/herdr-dotfiles ~/herdr-dotfiles
~/herdr-dotfiles/install.sh              # needs jq, git, rsync, python3; the Herdr app opened once
```

Re-run after `git pull` to update. Whatever it replaces is saved in `~/.config/herdr-app/backup-<time>/`.
`keys.json` and `programs.json` are merged (this repo wins per key), so keys from other sources survive.
`./install.sh --no-shepherdr` skips Shepherdr, `--no-herdr-chat` skips herdr-chat. `./install.sh --fetch` only downloads (the one step that needs the internet: one tarball per mod repo, one `git fetch` for Shepherdr, cached in `~/.cache/herdr-dotfiles`, override with `HERDR_DOTFILES_CACHE`); a plain `./install.sh` afterwards works offline, so on a restricted network run `--fetch` there and install anywhere. `HERDR_APP_HOME`, `DEVIN_CONFIG_HOME` and `SHEPHERDR_SRC`
(default `~/src/shepherdr`) override locations.
Then `shepherdr doctor`, and `ctrl+shift+l` to pick the Shepherdr layout.

## What it installs

| Piece | What | From | License |
|---|---|---|---|
| Shepherdr | layout + 28 mods + helpers (`herdr-task`, ...) + agent hooks; pinned in `shepherdr.pin`, cloned to `~/src/shepherdr`, installed with `--no-build` (no web service) | [eliasstravik/shepherdr](https://github.com/eliasstravik/shepherdr) | see its repo |
| `submit` | bug/feature request dialog (`cmd+shift+b`): appends `- [ ] date · bug\|feature · text` to `requests.md` in this repo, which the agent working here reads as the backlog and ticks (like Plate's Submit); `install.sh` writes the repo path to `~/.config/herdr-app/dotfiles-path` | this repo; based on Herdr's `prompt` | Apache-2.0 |
| `keys-help` | all shortcuts window (`cmd+/`) | this repo; based on Herdr's `help` | Apache-2.0 |
| `tmux-prefix` | prefix menu (`cmd+e`): tmux-style keys + my commands + a live Keep awake toggle (`caffeinate -dis -w <Herdr pid>`: quitting Herdr ends it; pid in `keep-awake.pid`); patched by `integrations/tmux-prefix/patch-bindings.py` (step 4e2, one anchored edit set, re-applied on install; runs `hc` to forward keys, `exec` for caffeinate) | [herdrdev/herdr-layout-examples](https://github.com/herdrdev/herdr-layout-examples) | none stated |
| `reopen-tab` | reopen closed tabs (`cmd+shift+t`) | [mustafaTokmak/herdr-reopen-tab](https://github.com/mustafaTokmak/herdr-reopen-tab) | MIT |
| `file-editor` | file tree and tabbed editor (syntax highlighting, Markdown/SVG preview); used by the `shepherdr-files` layout; elsewhere `herdr-app do pane.split --direction right --mod file-editor` | [werlang/herdr-file-editor](https://github.com/werlang/herdr-file-editor) | none stated |
| `session-peek` | bar (name, status, Keep, ✕) over the chat-view preview of a session that has no pane; opened by the patched `agent-sidebar` | this repo; based on Herdr's `peek` | Apache-2.0 |
| Agents in chat view | **disabled** (the loop made tabs flap); `integrations/auto-chat/patch-auto-chat.py` is kept but `install.sh` step 4g is commented out | `integrations/auto-chat/` | |
| `agent-sidebar` | sessions sidebar for `shepherdr-files` (see below); patched by `integrations/agent-sidebar/patch-sidebar.py` | [jeffarese/herdr-agents-sidebar](https://github.com/jeffarese/herdr-agents-sidebar) | MIT |
| `desktop-notifications` | "needs you" / "finished" agent alerts in the macOS Notification Center (docked as a 0px block in `shepherdr-files`; `brew install terminal-notifier` for click-to-focus) | [benjaminsicard/herdr-mods](https://github.com/benjaminsicard/herdr-mods/tree/main/desktop-notifications) | none stated |
| `auto-tabs` | tabs name themselves: a Claude Code or Devin tab takes the conversation's title, a terminal tab its program or folder; a tab you rename yourself is left alone. Runs inside Shepherdr's tab bar (`tabs-tasks`) via `integrations/auto-tabs/patch-tabs.py` (install.sh step 4d), not as its own tab bar or layout | [longwave/herdr-auto-tabs](https://github.com/longwave/herdr-auto-tabs) | none stated |
| Devin hooks | Devin's status in Herdr, and its icon (`programs.json`) | `integrations/devin/` | |
| Devin in the chat | Shepherdr's chat view follows Devin: a small patch to its `chat` mod, applied by `install.sh` | `integrations/devin/chat/` | |

Shepherdr runs programs (`herdr-task`, `git`, `gh`, `hc`, ...), reads files outside its mod folders and reaches
GitHub (and ElevenLabs, if you turn on voice). `reopen-tab` runs `hc` and `git` and keeps a ledger in `data/reopen-tab/`.
`file-editor` reads and writes files (and runs `git`, plus `herdr-core exec` over SSH). `desktop-notifications` runs `terminal-notifier`/`osascript` and `herdr-app`; it reads no files and uses no network.
Not installed: Shepherdr's web app/service and voice (they need bun, and tailscale for the web app).
Run `~/src/shepherdr/install.sh` without `--no-build` to add them.

`install.sh` also writes the layout `shepherdr-files` (not versioned): Shepherdr's layout with its Files panel replaced by
`file-editor`. It is generated from the live `layouts/shepherdr.json` on every install, so Shepherdr updates carry over, and
Shepherdr's `layout:shepherdr` keys plus mine are copied to `layout:shepherdr-files`. It also docks `desktop-notifications` there as a 0px block; other layouts need it added by hand. Pick it with `ctrl+shift+l`. The Files button in the tab bar only shows if the app's shared `workspace.panels` includes `files`
(it is `[]` after the welcome screen skips it); it lives in `shared.json`, which the app overwrites, so it can't be set from here.

## Keys (`keys.json`)

| Keys | Action |
|---|---|
| `cmd+/`, `cmd+shift+/` | all shortcuts |
| `cmd+shift+t` | reopen the last closed tab |
| `cmd+shift+b` | submit a bug or feature request about this setup (`submit`) |
| `cmd+e` | prefix menu (`tmux-prefix`, borrowed and patched): tmux-style tab/pane/space keys plus mine (`a` Keep awake, live ON/off, `b` submit, `e` Devin sessions, `s` keep, `r` reopen, `i` chat input, `/` shortcuts); `?` lists all |
| `cmd+shift+e` | Devin sessions: list, archive or restore with Enter (`devin-sessions`, uses `devin-archive`) |
| `cmd+l` | focus the input box of the Shepherdr chat on screen (`chat.focus`) |
| `cmd+1..9` | open the Nth session as the sidebar lists it now (`agent-sidebar.N`), each row shows its ⌘N, in `shepherdr-files` only; replaces `cmd+1..9` = tabs there (the order follows the list, so it moves with status) |
| `cmd+n` | new session: the sidebar's launcher (`agent-sidebar.new`), in `shepherdr-files` |
| `cmd+shift+k` | Keep the session being previewed in chat view: gives it a pane (`session-peek.keep`) |
| `cmd+w` | in `shepherdr-files`: put the focused agent away without ending it (its chat pane closes, or its terminal is parked; it keeps running and stays in the sidebar), even as the last pane of a space; shells and other panes close their tab as before (`agent-sidebar.close`) |

There is one layout, `shepherdr-files`, and everything I add goes into it.

Shepherdr merges its own keys (`ctrl+k` jump, `ctrl+shift+?`, `alt+1..9`, ...) at install.

## Privacy

`install.sh` (step 2b) sets `telemetry: false` in the app's `settings.json` (no anonymous usage data) and `everywhere.agents.feedback: false` in `~/.config/shepherdr/settings.json` (agents never offer to file Shepherdr problems as GitHub issues). Ideas and bugs go to `requests.md` through the `submit` mod and stay on this machine.

With herdr-chat installed, step 4e3 runs `integrations/chat-scroll/patch-timeline.py`: scrolling through the chat history made the conversation jump ("sambando") and left a gap under the last message. Root cause: herdr-chat's timeline mixes two units. `on_size_change` reports sizes multiplied by the UI zoom (`settings.json` `zoom`), while the positions it sets are not scaled, so at any zoom other than 1.0 every position computed from stored heights is wrong in proportion to its distance from the anchor. The patch replaces its `timeline.js` with `integrations/chat-scroll/timeline.js` (derived from upstream, whose md5 it checks; if herdr-chat changes the file the patch stops and changes nothing) and edits `main.js`: it measures the scale with a 100 px probe and keeps every height in layout px; rows entering the window are measured in a hidden pool before they join the visible column; the first measure corrects the scroll position (upstream's correction was always 0); paging in older history pins a row; and ↓ Latest is always laid out (faded) and shown only when more than 200 px from the bottom. A row that changes height after it was measured, above the screen, is not covered. Re-applied on every install.

With herdr-chat installed, `install.sh` also copies Shepherdr's `session-note.sh` (from `mods/chat.orig`) into herdr-chat's `mods/chat`, because the SessionStart hook in Claude's and Codex's config still points there.

## Reopen a closed tab with its Devin session

`reopen-tab` (`cmd+shift+t`) resumes Claude and Codex but started a blank Devin. `install.sh` step 4e runs `integrations/reopen/patch-plan.py`: one exact edit to its `plan.js` that reopens Devin with `devin -r <session>`, choosing the folder's most recent session that no live Devin process holds (locks in `~/.local/share/devin/cli/session_locks`), so with several Devins in one folder the closed one comes back. No session found: a fresh Devin. Re-applied on every install; if a pin bump moves the anchor the patch stops and changes nothing.

With herdr-chat installed (its `new-chat` mod in the app home), step 4e also runs `integrations/reopen/patch-chat.py`: a closed chat tab's only terminal is its host (`herdr-chat-host serve --chat <id> …`), which the borrowed mod reopened as a plain terminal (the host's text under the Chat/Terminal toggle, no chat view). The patch reopens such a tab as `tab.new {mod: "chat", props: {chat, provider, cwd}}` with the same chat id, so the host resumes the session its registry records. A whole space reopened at once, and a chat split beside other panes, still come back the old way.

## Devin approvals in the chat

Devin's `PermissionRequest` hook also runs `integrations/devin/herdr-ask.sh` (copied to `~/.config/devin/`, 30-minute timeout, after the status hook): it passes Devin's hook input to the chat's own `ask-hook.sh` and turns the card's Allow/Deny into Devin's `{"decision":"approve"|"block"}`. No answer or no chat: Devin asks in the terminal as before. The translation was tested with a stub; a real Devin approval end to end was not. Restart running Devin sessions after `install.sh`.

## Space tree (sidebar)

`space-tree` (my own mod) replaces Shepherdr's Spaces list in the generated `shepherdr-files` layout (install.sh step 4b): each space with its agents and terminals under it, one row per terminal pane; a tab with only a mod pane (the Assistant chat) is one row with the tab's name. Click shows that space and tab and focuses the pane. Status glyphs (spinner, dot, "!") come from `agents()`, `panes()` and `terminals()`; agents hosted by Shepherdr's chat report no status to the app, so their rows show no glyph yet. The top tab bar (`tabs-tasks`) stays, because it also holds the Files, Tasks and Artifacts buttons. The `spaces-chat` features (chat badges, the + button) are not in the tree.

## Trying jeffarese's agents sidebar

`./install.sh` fetches [jeffarese/herdr-agents-sidebar](https://github.com/jeffarese/herdr-agents-sidebar) (MIT, pinned in `sources.tsv`; it reads Claude's session logs and `ps`, runs no network calls) and step 4b puts it in the generated layout instead of `space-tree`. It lists agents, shells and programs grouped by what they need (Needs you / Working / Done / Idle) with search and filters, not nested under each space. To go back to `space-tree`: mark it `optional` in `sources.tsv`, delete `~/.config/herdr-app/mods/agent-sidebar` and re-run `./install.sh --no-shepherdr`. Several changes by patch (step 4f): opening a session (click or `cmd+1..9`) whose agent sits in a terminal pane switches it to chat (`pane-chat.toggle`, at once on the tab on screen, after 2.3 s on another); a session with no pane (claude, codex, devin) is previewed (turn that off with `herdr-app do agent-sidebar.preview`: it is then kept at once, as chat) in chat view instead of the terminal peek; a folder heading is drawn for every session and folds its sessions on click, and a session with sub-agents folds them too (chevron) (upstream: only for 2 or more in one folder), and `agent-sidebar.<n>` jumps to the nth session as listed. Herdr-jump (`spaces-jump`, `agents-jump`) and my `space-jump` are gone.

With [herdr-chat](https://github.com/ChmaraX/herdr-chat) installed in the app home (its `new-chat` mod is there), step 4f also applies `integrations/agent-sidebar/patch-launcher.py`: a pi, claude, codex or devin session started from the launcher (`cmd+n`, the +) in a space that is already open becomes a herdr-chat chat tab (`tab.new {mod: "chat", props: {chat, provider, cwd}}`) instead of a terminal running the agent. With no space open for the folder (e.g. right after the app starts) it does `space.new`, adds the chat tab to it (`space.new` takes no mod) and closes the shell tab the space started with. Shells and other machines work as before. herdr-chat's `chat` mod has the same name as Shepherdr's, so Shepherdr's is moved to `mods/chat.orig`.

**herdr-chat as the chat view (the official setup).** `./install.sh` installs it itself (step 0b, before Shepherdr): `herdr-chat.pin` pins my fork [falcaopetri/herdr-chat](https://github.com/falcaopetri/herdr-chat), branch `devin-provider` (ChmaraX's herdr-chat plus Devin as a provider), cloned to `~/src/herdr-chat` (override with `HERDR_CHAT_SRC`; `--fetch` downloads it too). Step 0b moves Shepherdr's `mods/chat` to `mods/chat.orig` (herdr-chat's installer refuses a `mods/chat` that is not its own), then runs the clone's `install.sh --no-subagents` with `HERDR_APP_HOME` set. It needs node >= 24, `hc` and one agent on PATH; if the installer fails, Shepherdr's chat is put back and the install goes on without herdr-chat. `--no-herdr-chat` skips it. With herdr-chat's `new-chat` in the app home the install skips Shepherdr's installer (which would put its `chat` back) and the patches for Shepherdr's chat (step 4c), and applies the herdr-chat patches above. `./upstream.sh` also reports the fork's branch and how far ChmaraX's `main` is ahead of it. What stops working, because herdr-chat's `chat` takes `{chat, cwd, provider}` and not Shepherdr's `{terminal, thread}`: the Chat view of `pane-chat` over a terminal agent, and the sidebar's chat preview of a session without a pane (`session-peek`; turn it off with `herdr-app do agent-sidebar.preview`). **Back to Shepherdr's chat:** `./install.sh --uninstall` in `~/src/herdr-chat`, then `rm -rf mods/chat && mv mods/chat.orig mods/chat`, then `./install.sh --no-herdr-chat` here (it reinstalls Shepherdr and its patches).

**Assistant tab:** Shepherdr's Assistant opens `chat` with `{role, slot, folder, settings}`; `integrations/assistant/patch-assistant.py` (install.sh step 4e4) makes herdr-chat derive the chat id from `slot`, the folder from `folder` and the agent from `settings.agent`. Its Chat/Terminal toggle (from `pane-chat`) still does nothing there.

## Archiving Devin sessions

The `devin-sessions` mod (`cmd+shift+e`) is its window: recent sessions with the archived ones dimmed, ↑↓ and Enter (or a click) to archive or restore, `a` to show the archived. `devin-archive` (installed to `~/.local/bin` by `install.sh`) archives Devin sessions the way Devin Desktop does, so they leave its list and Plate's Needs you. Archiving is not in the CLI's `sessions.db`: it is the JSON list `windsurf.acp.session/archivedSessions` in Desktop's `state.vscdb`. No argument: the latest session of the current folder that no live Devin holds; or give ids. `--undo <id>` restores, `--list` shows. Quit Devin Desktop first: it keeps the list in memory and may write its own copy back. Tested on a copy of the database.

## Updating pins

`./upstream.sh` (needs `gh`) says which pins (`shepherdr.pin`, `sources.tsv`) have news. To move one, edit the
commit and re-run `./install.sh`.

## Layout of this repo

| Path | What |
|---|---|
| `keys.json`, `programs.json`, `my-icons/` | merged into the app home |
| `mods/keys-help/`, `mods/submit/` | my mods |
| `requests.md` | backlog written by `submit` (created on first use) |
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

The script also sets the terminal title to the session's title (newest session of the current folder in `sessions.db`, which is
roughly the first message, cut to 80 characters; Devin itself only sets `devin: <folder>`), and `auto-tabs` shows it as the tab
name. Two Devin sessions in one folder can get each other's title. Running sessions need a restart to pick the hook up.

### Devin in Shepherdr's chat

`patch-chat.py` also makes a question card's "Other" box hold the keyboard while focused (`keyholder.js`); without it the chat's own box took focus back after about 2 s.

Shepherdr's `chat` mod only follows Claude Code and Codex (it reads their JSONL session logs). Devin keeps its live
conversation in `~/.local/share/devin/cli/sessions.db` (sqlite, `message_nodes`) and only writes
`transcripts/*.json` at the end, so `install.sh` step 4c:

- copies `integrations/devin/chat/devin-chat.py` into `mods/chat/`. It turns a Devin session into a Claude-style JSONL at
  `~/.config/herdr-app/data/devin-chat/<session>.jsonl` (Devin tools are renamed to Claude's, e.g. `exec` → `Bash`), so the
  chat's own parser does the rest;
- runs `patch-chat.py`, six exact-string edits to `mods/chat` and `mods/pane-chat` (`devin` in `KINDS` and `NAMES`, and in pane-chat's `chatty`, which shows the Chat | Terminal switch in the pane header; `FIND` maps the Devin pid to
  its session through `session_locks/*.lock`; `LOG` refreshes the JSONL before each read). If Shepherdr changes one of those
  spots the patch stops without touching anything: look at the anchor and adjust.

Why a patch and not a clone: `pane-chat`, `spaces-chat` and `coordinator` look for panes whose mod is `chat`.
`shepherdr update` replaces them; run `./install.sh --no-shepherdr` again afterwards.
Limits: local machine only; branches/rewinds in Devin's message tree are flattened (first copy of each message wins);
Devin's tool argument names are guessed from Claude's (unknown ones show as "Used <tool>"); no steering, background jobs or model picker.

**TODO:** stop and think about an upstream request to Shepherdr for a pluggable agent log reader (so Devin needs no
patch), instead of carrying this one.
