// Every shortcut in one filterable list (keys.json, through keys()).
// Based on Herdr's shipped `help` mod (Apache-2.0).

import { View, div } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { closeOverlay, keys, props, theme } from "herdr";

const GROUPS = [
  ["spaces", /^space\./],
  ["tabs", /^tab\./],
  ["panes", /^pane\./],
  ["agents", /^agent\./],
  ["terminal", /^terminal\.|^send:/],
  ["window", /./],
];

// An action is "name", "name:value", "send:text" or {command, args}.
function label(action) {
  if (typeof action !== "string") {
    const args = Object.values(action.args ?? {}).map((v) => (typeof v === "string" ? v : JSON.stringify(v))).join(" ");
    return `${action.command.replace(/[._]/g, " ")}${args ? " " + args : ""}`;
  }
  if (action.startsWith("send:")) return "type " + JSON.stringify(action.slice(5));
  const [name, arg] = action.split(":");
  const words = name.replace(/[._]/g, " ");
  return arg ? `${words} ${arg}` : words;
}

export default class KeysHelp extends View {
  init(_props, cx) {
    this.filter = "";
    this.input = InputState.new({ placeholder: "Search a key or an action…" });
    this.input.on("change", (_e, cx) => { this.filter = this.input.value(); cx.notify(); });
    this.input.focus();
    cx.timer.after(600, () => this.input.focus());
    this.handle = cx.focus_handle();
  }

  render() {
    const t = theme();
    const f = this.filter.toLowerCase();
    const hit = (keysText, what) => !f || keysText.toLowerCase().includes(f) || what.toLowerCase().includes(f);
    const seen = new Set();
    const all = keys().filter((k) => !k.section.startsWith("mod:"));
    const sections = [
      ...GROUPS.map(([name, re]) => [`Herdr · ${name}`, all
        .filter((k) => !seen.has(k) && re.test(typeof k.action === "string" ? k.action : k.action.command) && seen.add(k))
        .map((k) => [k.keys + (k.section !== "global" ? `  (${k.section})` : ""), label(k.action)])]),
    ].map(([name, rows]) => [name, rows.filter(([k, w]) => hit(k, w))]).filter(([, rows]) => rows.length);

    return v_flex().id("keys-help").track_focus(this.handle)
      .on_key_down((e) => { if (e.key === "escape") closeOverlay(props().overlay); })
      .size_full().min_h(0).p(18).gap(14).bg(t.popover).text_size(12)
      .child(h_flex().h(22).items_center().justify_between()
        .child(div().text_size(15).font_semibold().text_color(t.foreground).child("Shortcuts"))
        .child(div().id("keys-esc").px(6).py(2).rounded(5).text_size(11).text_color(t.dim).cursor_pointer()
          .hover((s) => s.bg(t.hover).text_color(t.foreground)).on_click(() => closeOverlay(props().overlay)).child("Esc")))
      .child(Input.new(this.input).h(36).flex_none().px(10).rounded(9).border_1().border_color(t.accent).bg(t.background).text_size(12.8).text_color(t.foreground))
      .child(v_flex().flex_1().min_h(0).overflow_y_scrollbar().py(2).gap(10).children(
        sections.map(([name, rows]) => v_flex().gap(2)
          .child(div().text_size(11.5).font_medium().text_color(t.dim).child(name))
          .children(rows.map(([k, w]) => h_flex().h(28).px(8).rounded(7).items_center()
            .child(div().w(190).text_color(t.accent).child(k))
            .child(div().text_color(t.foreground).child(w)))))));
  }
}
