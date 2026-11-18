// The timeline's own scroller. Only the rows on screen (plus some margin)
// are built, as ordinary elements, so cards can have their own click and
// hover handlers (rows of the app's virtual lists can't). Each row's height
// is measured with on_size_change once drawn; unmeasured rows use an
// estimate. While sticky, the last row's bottom is pinned to the viewport's
// bottom (absolute bottom 0), so a growing streamed answer needs no second
// layout pass. Scrolling up unsticks; reaching the bottom sticks again.
// (Patched by herdr-dotfiles, integrations/chat-scroll: scrolled up, the rows on screen and above hang UP from the first
// row below the viewport and the rows below it hang down, so a row measured for the first time never pushes what is
// being read; the first measure of a row above corrects `top`; paging in older history pins a row; `far` says when
// ↓ Latest is worth showing.)
// A new row is drawn in the frame that makes room for it, with no fade: the
// rows above move at once, so a fade would show a blank hole first (#16).

import { div } from "gpui-kit";
import { v_flex } from "gpui-base";

const OVERSCAN = 400;
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
    this.aboveIds = new Set();
    this.anchor = null;
    this.pin = null;
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
    let place;
    let split = null; // scrolled up: rows[0..a) hang up from y, rows[a..) hang down from y
    this.aboveIds = new Set();
    if (this.sticky || total <= this.viewH) {
      let used = 0;
      let i = items.length - 1;
      while (i >= 0 && used < this.viewH + OVERSCAN) used += this.h(items[i--]);
      for (let k = i + 1; k < items.length; k++) rows.push(k);
      this.top = Math.max(0, total - this.viewH);
      // Same two containers as scrolled up (everything in the upper one, hung from the bottom edge), so leaving the bottom
      // does not move any row to another parent.
      if (total <= this.viewH) place = (e) => e.top(0);
      else {
        split = { a: rows.length, y: this.viewH };
        place = (e) => e.top(split.y);
      }
    } else {
      if (this.pin) {
        const k = items.findIndex((r) => r.id === this.pin.id);
        if (k >= 0) this.top = offs[k] - this.pin.y;
        this.pin = null;
      }
      this.top = Math.max(0, Math.min(this.top, total - this.viewH));
      const edge = this.top + this.viewH;
      let lo = 0;
      while (lo < items.length && offs[lo] + this.h(items[lo]) < this.top - OVERSCAN) lo++;
      let a = lo;
      while (a < items.length && offs[a] < edge) a++; // the first row that starts at or below the viewport's bottom
      let hi = a;
      while (hi < items.length && offs[hi] < edge + OVERSCAN) hi++;
      for (let i = lo; i < hi; i++) rows.push(i);
      split = { a: a - lo, y: (a < items.length ? offs[a] : total) - this.top };
      for (let i = lo; i < a; i++) this.aboveIds.add(items[i].id);
      place = (e) => e.top(split.y);
      const c = items.findIndex((r, i) => i >= lo && offs[i] + this.h(r) > this.top); // the row across the top: for pinning
      this.anchor = c >= 0 ? { id: items[c].id, y: offs[c] - this.top } : null;
    }
    this.offsets = new Map(rows.map((i) => [items[i].id, offs[i]]));
    this.shown = rows.map((i) => items[i].id);
    if (this.top < 300 && onNearTop && !this.sticky) onNearTop();
    else if (this.sticky && total < this.viewH && onNearTop) onNearTop();
    const measured = (it) => div().id(`row-${it.id}`).w_full()
      .child(row(it)).on_size_change((s, cx) => {
      const old = this.heights.get(it.id);
      if (old === s.height) return;
      const was = old ?? this.h(it); // the estimate, read before the measure replaces it
      this.heights.set(it.id, s.height);
      this.heightsSeen?.add(it.id, Math.round(s.height));
      // A row above the viewport changed size: keep the view still.
      const off = this.offsets.get(it.id);
      if (!this.sticky && (this.aboveIds.has(it.id) || (off !== undefined && off < this.top))) this.top += s.height - was;
      // Sticky, a known row growing needs no redraw: it's pinned to the bottom.
      if (!this.sticky || old === undefined) cx.notify();
    });
    return div().id(this.id).relative().flex_1().min_h(0).w_full().overflow_hidden()
      .on_size_change((s, cx) => {
        if (s.height === this.viewH) return;
        this.viewH = s.height;
        cx.notify();
      })
      .on_scroll_wheel((e, cx) => {
        const before = [this.top, this.sticky];
        this.scrollBy(e.delta.y);
        if (before[0] !== this.top || before[1] !== this.sticky) cx.notify();
      })
      .child(place(v_flex().absolute().left(0).right(0)).children((split ? rows.slice(split.a) : rows).map((i) => measured(items[i]))))
      .when(Boolean(split && split.a > 0), (e) => e.child(v_flex().absolute().left(0).right(0).bottom(this.viewH - split.y)
        .children(rows.slice(0, split.a).map((i) => measured(items[i])))))
      .when(!this.sticky && total > this.viewH && Boolean(thumb), (e) => {
        const h = Math.max(28, (this.viewH * this.viewH) / total);
        const y = ((this.viewH - h) * this.top) / Math.max(1, total - this.viewH);
        return e.child(div().absolute().right(3).top(y).w(5).h(h).rounded(3).bg(thumb));
      });
  }
}
