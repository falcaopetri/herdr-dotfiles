// Space tree: the sidebar list where each space shows its agents and terminals under it, instead of a tab bar.
// One row per terminal pane (an agent shows its live title, a shell its program), a tab with only a mod pane
// (the Assistant chat) shows as one row with the tab's name. Click: show that space and tab and focus the pane.
// Rows and status glyphs follow Herdr's own `agents` mod (the dot/spinner/"Needs you" language).

import { View, div, svg } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { agents, spaces, panes, terminals, run, theme } from "herdr";

// An agent puts a status glyph or spinner before its title: drop it (as the agents mod does).
const clean = (s) => (s ?? "").replace(/^[^\p{L}\p{N}\p{Ps}\p{Pi}]+/u, "").replace(/^\[ [!.] \] /, "").trim();

function rowLabel(p, tab) {
  if (p.terminal === null) return tab.named ? tab.name : p.title || tab.name;
  const prog = p.program?.name;
  if (p.program?.agent) {
    const live = clean(p.title);
    const path = /^[~/]/.test((p.title ?? "").replace(/^[^\p{L}\p{N}~/]+/u, ""));
    if (live && !path && !live.includes("@") && live !== p.terminal && live !== prog) return live;
    return tab.named ? tab.name : prog ?? "Agent";
  }
  return tab.named ? tab.name : prog ?? "Terminal";
}

export default class SpaceTree extends View {
  glyph(t, status) {
    if (status === "working") return svg("mods/workspace-chrome/spinner.svg").size(12).mx(1).flex_none().text_color(t.working).spin(900);
    if (status === "blocked") return div().size(14).flex_none().rounded(4).bg(t.blocked + "26").text_size(10.5).font_bold().text_color(t.blocked).flex().items_center().justify_center().child("!");
    if (status === "idle") return div().size(7).mx(3).flex_none().rounded(4).border(1.5).border_color(t.idle ?? t.dim);
    if (status === "done") return div().size(7).mx(3).flex_none().rounded(4).bg(t.done ?? t.dim);
    return div().size(7).mx(3).flex_none();
  }

  render() {
    const t = theme();
    const all = panes();
    // An agent's live status comes from agents(); Shepherdr's chat-hosted agents are not in it, so the tab's own status
    // (what the tab bar's spinner shows) stands in when the tab has one row.
    const live = new Map(agents().map((a) => [a.pane, a.status]));
    // Shepherdr's chat-hosted agents report no status to the app (agents() and panes() lack them), but herdr-core knows it:
    // terminals() is `hc ls`, with the status as a word.
    const core = new Map(terminals().map((x) => [x.address, typeof x.status === "string" ? x.status : x.status?.state]));
    const list = v_flex().id("space-tree").w_full().h_full().min_h(0).overflow_y_scroll().px(8).py(6).gap(2);
    for (const s of spaces()) {
      list.child(h_flex().id(`space-${s.id}`).h(30).px(8).gap(8).items_center().rounded(7).cursor_pointer()
        .bg(s.active ? t.raised : t.background).text_color(s.active ? t.foreground : t.dim)
        .on_click(() => run("space.select", { id: s.id }))
        .child(div().text_size(12).text_color(t.dim).child("#"))
        .child(div().flex_1().min_w(0).truncate().text_size(13).font_medium().child(s.name))
        .child(this.glyph(t, s.status)));
      for (const tab of s.tabs) {
        const mine = all.filter((p) => p.tab === tab.id);
        const rows = mine.some((p) => p.terminal !== null) ? mine.filter((p) => p.terminal !== null) : mine.slice(0, 1);
        for (const p of rows) {
          const here = s.active && tab.active && (p.focused || rows.length === 1);
          list.child(h_flex().id(`pane-${p.pane}`).h(26).pl(26).pr(8).gap(8).items_center().rounded(6).cursor_pointer()
            .bg(here ? t.raised : t.background).text_color(here ? t.foreground : t.dim)
            .on_click(() => { run("space.select", { id: s.id }); run("tab.select", { id: tab.id }); run("pane.focus", { pane: p.pane }); })
            .child(div().flex_1().min_w(0).truncate().text_size(12.3).child(rowLabel(p, tab)))
            .child(this.glyph(t, live.get(p.pane) || p.status || core.get(p.terminal) || (rows.length === 1 ? tab.status : null))));
        }
      }
    }
    return list;
  }
}
