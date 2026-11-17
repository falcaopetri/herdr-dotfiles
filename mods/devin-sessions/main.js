// Devin sessions: the recent ones from the CLI's sessions.db, with Desktop's archived flag.
// Up/down move, Enter (or click the row) archives or restores through ~/.local/bin/devin-archive (installed by
// install.sh; it writes Devin Desktop's archived list), "a" shows or hides the archived ones, Esc closes.
// Based on the layout of this repo's `submit` mod, which is based on Herdr's shipped `prompt` (Apache-2.0).

import { View, div } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { closeOverlay, exec, notify, props, theme } from "herdr";
import { keepKeys, dropKeys } from "./keyholder.js";

// While open, this dialog holds the keyboard (keyholder.js): the chat behind it would otherwise take it back after a
// couple of seconds. Renewed every 2 s, since a holder that is not renewed stops counting after 6 s.
const WHO = "dialog:devin-sessions";
const close = () => { dropKeys(WHO); closeOverlay(props()?.overlay); };

const LIST = `sqlite3 -readonly -json "$HOME/.local/share/devin/cli/sessions.db" "select id, title, working_directory as wd, last_activity_at as t from sessions where hidden=0 order by last_activity_at desc limit 80"; echo '@@'; "$HOME/.local/bin/devin-archive" --list`;

const ago = (t) => {
  const s = Math.max(0, Date.now() / 1000 - t);
  if (s < 3600) return `${Math.max(1, Math.round(s / 60))}m`;
  if (s < 86400) return `${Math.round(s / 3600)}h`;
  return `${Math.round(s / 86400)}d`;
};
const clean = (s) => String(s || "(untitled)").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim() || "(untitled)";
const short = (p) => String(p || "").replace(/^\/Users\/[^/]+/, "~");

export default class DevinSessions extends View {
  init(_props, cx) {
    this.rows = [];
    this.archived = new Set();
    this.showArchived = false;
    this.sel = 0;
    this.status = "Loading…";
    this.handle = cx.focus_handle();
    this.keep(cx);
    this.load(cx);
  }

  keep(cx) {
    keepKeys(WHO);
    cx.timer.every(2000, () => keepKeys(WHO));
  }

  visible() { return this.rows.filter((r) => this.showArchived || !this.archived.has(r.id)); }

  load(cx) {
    cx.spawn(async (cx) => {
      try {
        const r = await exec("sh", ["-c", LIST]);
        if (r.code !== 0) throw new Error(r.stderr.trim() || "could not read the sessions");
        const [json, arch] = r.stdout.split("\n@@\n");
        this.rows = json.trim() ? JSON.parse(json) : [];
        this.archived = new Set((arch || "").split("\n").map((x) => x.trim()).filter(Boolean));
        this.status = "";
      } catch (e) { this.status = String(e?.message ?? e); }
      cx.notify();
    });
  }

  toggle(row, cx) {
    if (!row) return;
    const undo = this.archived.has(row.id);
    cx.spawn(async (cx) => {
      try {
        const r = await exec("sh", ["-c", `"$HOME/.local/bin/devin-archive" ${undo ? "--undo " : ""}"$1"`, "sh", row.id]);
        if (r.code !== 0) throw new Error(r.stderr.trim() || "devin-archive failed");
        if (undo) this.archived.delete(row.id); else this.archived.add(row.id);
        this.status = /warning/.test(r.stderr) ? "Devin Desktop is open: quit it, or it may undo this." : "";
        this.sel = Math.min(this.sel, Math.max(0, this.visible().length - 1));
      } catch (e) { this.status = String(e?.message ?? e); }
      cx.notify();
    });
  }

  key(e, cx) {
    const n = this.visible().length;
    if (e.key === "escape") { close(); cx.stop_propagation(); }
    else if (e.key === "down") { this.sel = Math.min(n - 1, this.sel + 1); cx.notify(); }
    else if (e.key === "up") { this.sel = Math.max(0, this.sel - 1); cx.notify(); }
    else if (e.key === "enter") this.toggle(this.visible()[this.sel], cx);
    else if (e.key === "a") { this.showArchived = !this.showArchived; this.sel = 0; cx.notify(); }
  }

  render() {
    const t = theme();
    const rows = this.visible();
    const list = v_flex().id("devin-list").flex_1().min_h(0).overflow_y_scroll().pt(10);
    rows.forEach((r, i) => {
      const gone = this.archived.has(r.id);
      list.child(h_flex().id(`row-${r.id}`).h(34).px(10).gap(10).items_center().rounded(7).cursor_pointer()
        .bg(i === this.sel ? t.raised : t.popover).text_color(gone ? t.dim : t.foreground)
        .on_click((_e, cx) => { this.sel = i; this.toggle(r, cx); })
        .child(div().flex_1().min_w(0).truncate().text_size(12.8).child(clean(r.title)))
        .child(div().w(190).truncate().text_size(11.5).text_color(t.dim).child(short(r.wd)))
        .child(div().w(34).text_size(11.5).text_color(t.dim).child(ago(r.t)))
        .child(div().w(62).text_size(11).text_color(gone ? t.accent : t.dim).child(gone ? "archived" : "")));
    });
    return v_flex().id("devin-sessions").track_focus(this.handle).on_key_down((e, cx) => this.key(e, cx))
      .w_full().h_full().min_h(0).p(18).bg(t.popover).text_color(t.foreground)
      .child(h_flex().items_center().child(div().flex_1().text_size(15).font_semibold().child("Devin sessions"))
        .child(div().text_size(11).text_color(t.dim).child("↑↓ · Enter archive/restore · a show archived · Esc")))
      .child(list)
      .child(div().pt(6).text_size(11.5).text_color(this.status ? t.danger ?? "#e5484d" : t.dim)
        .child(this.status || `${rows.length} shown · ${this.archived.size} archived${this.showArchived ? "" : " (hidden)"}`));
  }
}
