#!/usr/bin/env python3
"""Stops herdr-chat's timeline from jumping ("sambando") while you scroll through the history, and keeps ↓ Latest from
showing on the first notch of a scroll.
ROOT CAUSE (found with a screen recording and red/blue row markers): the timeline mixed two units. Sizes reported by
on_size_change are multiplied by the UI zoom (settings.json "zoom", here 1.2), but the positions it sets with top()/bottom()
are not. At zoom 1.0 both agree, which is probably how upstream was tested; at any other zoom every position computed from
the stored heights is off in proportion to its distance from the anchor, so rows jump by about one row each time the first
drawn row changes, and a gap opens under the last message. The timeline now measures the scale with a 100 px probe element
and keeps every height in layout px.
Also fixed, because they made it worse (the scroller lays rows out by ESTIMATED heights and corrects afterwards):
  - rows entering the window are first drawn in a zero-height clipped pool, only to be measured; then they join the main
    column, whose top is offsets[first] - top (no estimate in it); a height only counts while the row was drawn (stale
    cached heights from another width or an opened group are re-measured first);
  - the first measure of a row above `top` corrects `top` by the estimate it replaces (upstream subtracted it after storing
    the measure, so the correction was always 0);
  - paging in older history pins a row on screen instead of adding estimates of raw items (which collapse into groups);
  - ↓ Latest and its band are always laid out, only faded, and shown once you are more than 200 px from the bottom.
Not covered: a row that changes height AFTER it was measured, above the screen (async content), still shifts for a frame.
timeline.js is replaced by integrations/chat-scroll/timeline.js (derived from upstream, whose md5 is checked: if herdr-chat
changed it, nothing is touched and the patch must be redone from the new upstream). main.js gets anchored edits.
Idempotent; re-applied by install.sh.
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
