#!/usr/bin/env python3
"""Stops herdr-chat's timeline from jumping ("sambando") while you scroll up through history, and keeps ↓ Latest from
showing on the first notch of a scroll. Four faults in the upstream timeline.js / main.js:
 1. on_size_change computed the correction as `s.height - (old ?? this.h(it))` AFTER storing the new height, so for a row
    measured for the first time it was always 0: the error of the estimated height was never compensated.
 2. Scrolled up, rows were placed at `first - top` from ESTIMATED heights of everything above, so a row entering above
    the screen displaced what you were reading for a frame. Now the rows on screen and above hang UP from the first row
    below the viewport (rows below hang down), so unmeasured rows grow away from what is on screen, and a row only moves
    between those two groups off screen. Sticky uses the same two containers, so leaving the bottom remounts nothing.
 3. Paging older history added the ESTIMATED heights of the raw items to `top`, but the view shows rows (tools collapse
    into groups, hidden items show nothing). Now a row on screen is pinned and `top` is set to keep it where it was.
 4. ↓ Latest and its band were added to/removed from the tree and showed on the first notch. They are now always laid
    out, only faded, and shown once you are more than 200 px from the bottom (`timeline.far`).
timeline.js is replaced by integrations/chat-scroll/timeline.js (derived from upstream, whose md5 is checked: if herdr-chat
changed it, nothing is touched and the patch must be redone from the new upstream). main.js gets anchored edits.
(A simulation of view() on random chats, 8 seeds x 400 scroll steps: upstream 417 jumping frames up to 876 px; this 0 and
0 rows remounted while visible.) Idempotent; re-applied by install.sh.
Usage: patch-timeline.py <app home>"""
import hashlib, pathlib, sys

UPSTREAM_MD5 = "c9a059fa0f1bc8f47813e045d78580ed"  # herdr-chat 5accb11, herdr-app/mods/chat/timeline.js
home = pathlib.Path(sys.argv[1]) / "mods/chat"
mine = (pathlib.Path(__file__).parent / "timeline.js").read_text()

f = home / "timeline.js"
cur = f.read_text()
if cur == mine:
    print("chat timeline: already patched")
elif hashlib.md5(cur.encode()).hexdigest() == UPSTREAM_MD5 or "split = {" in cur or "Patched by herdr-dotfiles" in cur:
    f.write_text(mine)
    print("chat timeline: no jumps while scrolling up (anchored below the viewport, first measure corrects, paging pins a row)")
else:
    sys.exit("patch-timeline.py: %s is neither the herdr-chat version this was made for nor mine; nothing changed (redo the patch)" % f)

OLD_BAND = '.when(!this.timeline.sticky, (e) => e.child(div().absolute().bottom(0).left(0).right(0).h(16).bg(alpha(t.background, 0.92)))))'
EDITS = [
    (OLD_BAND, '.child(div().absolute().bottom(0).left(0).right(0).h(16).bg(alpha(t.background, 0.92)).opacity(this.timeline.far ? 1 : 0)))'),
    (".when(!this.timeline.sticky, (e) => e.child(div().absolute().top(-14).left(0).right(0).flex().justify_center()",
     ".child(div().absolute().top(-14).left(0).right(0).flex().justify_center().opacity(this.timeline.far ? 1 : 0)"),
    ('.child(icon("arrow-down", 12)).child("Latest"))))));', '.child(icon("arrow-down", 12)).child("Latest")))));'),
]
m = home / "main.js"
s = m.read_text()
if "timeline.far" in s:
    print("chat: Latest already patched")
elif "this.timeline.sticky ? 0 : 1" in s:   # the earlier version of this patch (faded on `sticky`)
    m.write_text(s.replace("this.timeline.sticky ? 0 : 1", "this.timeline.far ? 1 : 0"))
    print("chat: Latest shows only when more than 200 px from the bottom")
else:
    for old, new in EDITS:
        if s.count(old) != 1:
            sys.exit("patch-timeline.py: anchor not found in main.js (%r); nothing changed there (update the patch)" % old[:50])
        s = s.replace(old, new)
    m.write_text(s)
    print("chat: Latest and its band always laid out, faded, shown only when more than 200 px from the bottom")
