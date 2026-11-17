// The bar over a session's preview in chat view (opened by agent-sidebar, see
// integrations/agent-sidebar/patch-sidebar.py): who it is, "Keep" (⌘⇧K, `session-peek.keep`) to give
// the session a pane of its own, ✕ to close. Props: { terminal }. The window's id is in shared "session-peek.window".
// Based on Herdr's `peek` mod (Apache-2.0).

import { View, div } from "gpui-kit";
import { h_flex } from "gpui-base";
import { terminals, agents, run, theme, props, shared, closeOverlay, nextCommand } from "herdr";

const WORDS = { working: "working", blocked: "needs you", done: "finished", idle: "idle" };

export default class SessionPeek extends View {
  init(_props, cx) {
    this.keeping = false;
    cx.spawn(async cx => {
      for (;;) {
        const c = await nextCommand();
        if (c === "keep") await this.keep(cx);
      }
    });
  }

  // A kept session comes up as a terminal pane. pane-chat's header ignores a toggle in its first
  // 2 s, so wait it out, then switch that pane to chat view, as the preview was.
  async keep(cx) {
    const terminal = props()?.terminal;
    if (!terminal || this.keeping) return;
    this.keeping = true;
    cx.notify();
    run("terminal.keep", { terminal });
    run("pane.focus", { terminal });
    await cx.sleep(2600);
    run("pane.focus", { terminal });
    run("pane-chat.toggle");
    this.close();
  }

  close() {
    const id = shared("session-peek.window");
    if (id) closeOverlay(id);
  }

  button(t, id, label, onClick) {
    return div().id(id).px(8).py(2).rounded(5).text_color(t.muted).cursor_pointer()
      .hover(s => s.bg(t.hover).text_color(t.foreground)).on_click(onClick).child(label);
  }

  render() {
    const t = theme();
    const terminal = props()?.terminal;
    const k = terminals().find(x => x.address === terminal);
    const st = agents().find(a => a.address === terminal)?.status ?? k?.status ?? null;
    return h_flex().size_full().px(12).gap(8).items_center().bg(t.surface).border_b(1).border_color(t.border).text_size(12)
      .child(div().truncate().font_semibold().text_color(t.foreground).child(k?.name || k?.program?.name || terminal || ""))
      .when(Boolean(st), el => el.child(div().flex_none().text_color(t[st] ?? t.dim).child(WORDS[st] ?? st)))
      .child(div().flex_1())
      .child(this.button(t, "keep", this.keeping ? "Keeping…" : "↗ Keep  ⌘⇧K", (_e, cx) => this.keep(cx)))
      .child(this.button(t, "close", "✕", () => this.close()));
  }
}
