// The timeline's own scroller. Only the rows on screen (plus some margin)
// are built, as ordinary elements, so cards can have their own click and
// hover handlers (rows of the app's virtual lists can't). Each row's height
// is measured with on_size_change once drawn; unmeasured rows use an
// estimate. While sticky, the last row's bottom is pinned to the viewport's
// bottom (absolute bottom 0), so a growing streamed answer needs no second
// layout pass. Scrolling up unsticks; reaching the bottom sticks again.
// (Patched by herdr-dotfiles, integrations/chat-scroll. The rule: a row whose height is not known is never laid out among
// the visible ones. Scrolled up, rows entering the window are first drawn in a zero-height clipped pool, only to be
// measured; once measured they join the main column, whose top is `offsets[first] - top`, so its position never depends
// on an estimate and a row never changes parent afterwards. The first measure of a row above `top` corrects `top` by the
// estimate it replaces; paging in older history pins a row; `far` says when ↓ Latest is worth showing.)
// A new row is drawn in the frame that makes room for it, with no fade: the
// rows above move at once, so a fade would show a blank hole first (#16).

import { div } from "gpui-kit";
import { v_flex } from "gpui-base";

const OVERSCAN = 400;
const POOL_TRIES = 3;
const EST = { user: 80, assistant: 120, thinking: 34, tool: 44, notice: 32, custom: 56, group: 40, footer: 32, activity: 38 };

export class Timeline {
  constructor(id) {
    this.id = id;
    this.heights = new Map();
    this.offsets = new Map();
    this.sticky = true;
    this.top = 0;
    this.viewH = 0;
    this.total = 0;
    this.shown = [];
    this.anchor = null;
    this.pin = null;
    this.poolAge = new Map();
    this.viewRaw = 0; // the container's height as reported (zoomed)
    this.scale = 1; // what on_size_change reports per layout px (the UI zoom): measured by the probe in view(); every height is kept in layout px
    this.fresh = new Set(); // rows measured while they were drawn: a cached height from long ago (another width, a group that was open) is only an estimate
    this.heightsSeen = null; // debug only (trace()): row id → [[ms, height]…], the heights it was measured at
  }

  h(r) {
    return this.heights.get(r.id) ?? EST[r.kind === "item" ? r.item.kind : r.kind] ?? 60;
  }

  // Far enough from the bottom to offer ↓ Latest (not on the first notch of a scroll).
  get far() {
    return !this.sticky && this.total - this.viewH - this.top > 200;
  }

  scrollBy(dy) {
    if (this.sticky && dy > 0) {
      this.sticky = false;
      this.top = Math.max(0, this.total - this.viewH);
    }
    if (this.sticky) return;
    this.top -= dy;
    if (this.top < 0) this.top = 0;
    if (this.top >= this.total - this.viewH - 2) this.sticky = true;
  }

  trace(debug) {
    this.heightsSeen = debug.trace();
  }

  toBottom() {
    this.sticky = true;
  }

  // Items were put in front (history): keep what's on screen where it is.
  prepended(items) {
    if (this.sticky) return;
    this.pin = this.anchor; // the rows these items become are not the items: pin a row instead of adding estimates
  }

  // items: the rows (rows.js); row(r): its element; onNearTop(): page older
  // items; thumb: the scrollbar's color (drawn at the pane's edge while scrolled up).
  view(items, row, { onNearTop, thumb } = {}) {
    let total = 0;
    const offs = new Array(items.length);
    for (let i = 0; i < items.length; i++) {
      offs[i] = total;
      total += this.h(items[i]);
    }
    this.total = total;
    const rows = [];
    const pending = []; // in the window but not measured yet: drawn clipped to zero height, only to be measured
    let place;
    if (this.sticky || total <= this.viewH) {
      let used = 0;
      let i = items.length - 1;
      while (i >= 0 && used < this.viewH + OVERSCAN) used += this.h(items[i--]);
      for (let k = i + 1; k < items.length; k++) rows.push(k);
      this.top = Math.max(0, total - this.viewH);
      place = (e) => (total <= this.viewH ? e.top(0) : e.bottom(0));
    } else {
      if (this.pin) {
        const k = items.findIndex((r) => r.id === this.pin.id);
        if (k >= 0) this.top = offs[k] - this.pin.y;
        this.pin = null;
      }
      this.top = Math.max(0, Math.min(this.top, total - this.viewH));
      let lo = 0;
      while (lo < items.length && offs[lo] + this.h(items[lo]) < this.top - OVERSCAN) lo++;
      let hi = lo;
      while (hi < items.length && offs[hi] < this.top + this.viewH + OVERSCAN) hi++;
      // The main column starts at the first row that is measured, or that has waited in the pool for POOL_TRIES renders
      // (in case the pool is never measured: then it degrades to estimates, never to a hole) and runs to the end of the
      // window: unmeasured rows BELOW a measured one only move rows further down. Rows above wait in the pool.
      let s0 = lo;
      while (s0 < hi && !this.fresh.has(items[s0].id) && (this.poolAge.get(items[s0].id) ?? 0) < POOL_TRIES) s0++;
      for (let i = lo; i < hi; i++) (i >= s0 ? rows : pending).push(i);
      for (const i of pending) this.poolAge.set(items[i].id, (this.poolAge.get(items[i].id) ?? 0) + 1);
      const first = s0 < hi ? offs[s0] : 0;
      place = (e) => e.top(first - this.top);
      const c = rows.find((i) => offs[i] + this.h(items[i]) > this.top); // the row across the top: for pinning
      this.anchor = c !== undefined ? { id: items[c].id, y: offs[c] - this.top } : null;
    }
    this.offsets = new Map([...rows, ...pending].map((i) => [items[i].id, offs[i]]));
    for (const id of this.fresh) if (!this.offsets.has(id)) this.fresh.delete(id); // not drawn this frame: its height may go stale
    for (const id of this.poolAge.keys()) if (!this.offsets.has(id)) this.poolAge.delete(id);
    this.shown = rows.map((i) => items[i].id);
    if (this.top < 300 && onNearTop && !this.sticky) onNearTop();
    else if (this.sticky && total < this.viewH && onNearTop) onNearTop();
    const measured = (it) => div().id(`row-${it.id}`).w_full()
      .child(row(it)).on_size_change((s, cx) => {
      const hgt = s.height / this.scale;
      const old = this.heights.get(it.id);
      const wasFresh = this.fresh.has(it.id);
      this.fresh.add(it.id);
      if (old === hgt) {
        if (!wasFresh && !this.sticky) cx.notify(); // confirmed: it may join the main column now
        return;
      }
      const was = old ?? this.h(it); // the estimate, read before the measure replaces it
      this.heights.set(it.id, hgt);
      this.heightsSeen?.add(it.id, Math.round(hgt));
      // A row above the viewport changed size: keep the view still.
      const off = this.offsets.get(it.id);
      if (!this.sticky && off !== undefined && off < this.top) this.top += hgt - was;
      // Sticky, a known row growing needs no redraw: it's pinned to the bottom.
      if (!this.sticky || old === undefined) cx.notify();
    });
    const probe = div().absolute().top(0).left(0).w(1).h(100).on_size_change((s, cx) => {
      const k = s.height / 100;
      if (!(k > 0) || Math.abs(k - this.scale) < 0.001) return;
      this.scale = k; // sizes kept so far were in the old unit
      this.heights.clear();
      this.fresh.clear();
      if (this.viewRaw) this.viewH = this.viewRaw / k;
      cx.notify();
    });
    return div().id(this.id).relative().flex_1().min_h(0).w_full().overflow_hidden().child(probe)
      .on_size_change((s, cx) => {
        this.viewRaw = s.height;
        const vh = s.height / this.scale;
        if (vh === this.viewH) return;
        this.viewH = vh;
        cx.notify();
      })
      .on_scroll_wheel((e, cx) => {
        const before = [this.top, this.sticky];
        this.scrollBy(e.delta.y);
        if (before[0] !== this.top || before[1] !== this.sticky) cx.notify();
      })
      .child(place(v_flex().absolute().left(0).right(0)).children(rows.map((i) => measured(items[i]))))
      .when(pending.length > 0, (e) => e.child(v_flex().absolute().left(0).right(0).top(0).h(0).overflow_hidden()
        .children(pending.map((i) => measured(items[i]).flex_none()))))
      .when(!this.sticky && total > this.viewH && Boolean(thumb), (e) => {
        const h = Math.max(28, (this.viewH * this.viewH) / total);
        const y = ((this.viewH - h) * this.top) / Math.max(1, total - this.viewH);
        return e.child(div().absolute().right(3).top(y).w(5).h(h).rounded(3).bg(thumb));
      });
  }
}
