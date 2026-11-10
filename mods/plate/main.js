// Plate for herdr-app: a native view of the Plate webapp (~/Not Synced/plate), read from its /api/state.
// The server runs in the "plate" space (npm start). Set PLATE_URL below if you change the port.
import { View, div } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { theme, exec, run } from "herdr";

const URL = "http://localhost:4173";
const PRIO = { p1: 0, p2: 1, p3: 2, urgent: 0, high: 1, normal: 2, low: 3, p4: 3 };

export default class Plate extends View {
  init(_props, cx) {
    this.state = null;
    this.err = null;
    cx.timer.every(20000, (cx) => this.load(cx));
    this.load(cx);
  }

  load(cx) {
    cx.spawn(async (cx) => {
      try {
        const r = await fetch(URL + "/api/state");
        this.state = await r.json();
        this.err = null;
      } catch (e) {
        this.err = String(e?.message ?? e);
      }
      cx.notify();
    });
  }

  open(url) { exec("open", [url]); }

  row(t, id, title, sub, url, color) {
    return h_flex().id(id).gap(8).px(10).py(4).items_center()
      .hover((s) => s.bg(t.hover))
      .on_click(() => this.open(url))
      .child(div().w(6).h(6).rounded(3).bg(color ?? t.dim))
      .child(div().flex_1().truncate().text_color(t.foreground).child(title))
      .child(sub ? div().text_color(t.dim).text_size(11).child(sub) : div());
  }

  section(t, label, n) {
    return h_flex().px(10).pt(10).pb(2).gap(6)
      .child(div().text_size(11).font_semibold().text_color(t.muted).child(label.toUpperCase()))
      .child(div().text_size(11).text_color(t.dim).child(String(n)));
  }

  render(cx) {
    const t = theme();
    const s = this.state;
    const root = v_flex().id("plate").size_full().bg(t.surface).text_size(13).overflow_y_scrollbar();
    const header = h_flex().px(10).py(8).gap(8).items_center()
      .child(div().flex_1().font_semibold().text_color(t.foreground).child("Plate" + (s ? ` · ${s.today}` : "")))
      .child(div().id("plate-sync").px(6).py(2).rounded(4).text_size(11).text_color(t.muted).hover((x) => x.bg(t.hover))
        .child("Sync").on_click((_e, cx) => {
          cx.spawn(async (cx) => { try { await fetch(URL + "/api/sync", { method: "POST" }); } catch {} this.load(cx); });
        }))
      .child(div().id("plate-web").px(6).py(2).rounded(4).text_size(11).text_color(t.accent).hover((x) => x.bg(t.hover))
        .child("Abrir ↗").on_click(() => this.open(URL)));
    root.child(header);

    if (!s) {
      return root.child(div().px(10).text_color(t.muted).child(this.err
        ? `Servidor fora do ar (${URL}). Rode npm start no space "plate".`
        : "Carregando…"));
    }

    const byId = new Map(s.items.map((i) => [i.id, i]));
    const ws = new Map(s.workstreams.map((w) => [w.slug, w]));
    const label = (e) => {
      if (e.type === "ws") return { title: ws.get(e.ref)?.name ?? e.ref, url: URL };
      const i = byId.get(e.ref);
      return { title: i?.title ?? e.ref, url: i?.url ?? URL };
    };

    const doing = s.doing ?? [];
    root.child(this.section(t, "Fazendo", doing.length));
    doing.forEach((e, k) => { const l = label(e); root.child(this.row(t, `d${k}`, l.title, e.type === "ws" ? "workstream" : "", l.url, t.working)); });

    const top = s.top3 ?? [];
    if (top.length) {
      root.child(this.section(t, "Top 3", top.length));
      top.forEach((e, k) => { const l = label(e); root.child(this.row(t, `t${k}`, l.title, "", l.url, t.accent)); });
    }

    const today = s.today;
    const open = s.items.filter((i) => i.source !== "session" && i.state === "open" && i.due && i.due <= today)
      .sort((a, b) => a.due.localeCompare(b.due) || (PRIO[a.priority] ?? 9) - (PRIO[b.priority] ?? 9));
    root.child(this.section(t, "Vencido / hoje", open.length));
    open.slice(0, 15).forEach((i) =>
      root.child(this.row(t, i.id, i.title, i.due === today ? "hoje" : i.due.slice(5), i.url, i.due < today ? t.blocked : t.done)));

    const waiting = s.items.filter((i) => i.kind === "session" && i.state === "waiting");
    if (waiting.length) {
      root.child(this.section(t, "Sessões esperando", waiting.length));
      waiting.forEach((i) => root.child(this.row(t, i.id, i.title, i.tool, URL, t.blocked)));
    }
    return root;
  }
}
