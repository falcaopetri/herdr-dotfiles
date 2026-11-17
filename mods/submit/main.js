// Submit a bug or feature request about this Herdr setup: appends a line to requests.md in the
// herdr-dotfiles repo (`- [ ] YYYY-MM-DD HH:MM · bug|feature · text`). The agent working in the repo reads the
// open entries as the backlog and ticks them. Same idea as the Submit button in Plate.
// The repo path comes from <app home>/dotfiles-path, written by install.sh.
// Based on Herdr's shipped `prompt` mod (Apache-2.0).

import { View, div } from "gpui-kit";
import { v_flex, h_flex, InputState, Input } from "gpui-base";
import { appHome, closeOverlay, notify, props, readTextFile, theme, writeTextFile } from "herdr";

const pad = (n) => String(n).padStart(2, "0");
const stamp = () => {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

export default class Submit extends View {
  init(_props, cx) {
    this.kind = "bug";
    this.error = "";
    this.input = InputState.new({ placeholder: "What is broken, or what should it do?" });
    this.inputFocused = true;
    this.input.on("submit", (_e, cx) => this.submit(cx));
    this.input.on("focus", (_e, cx) => { this.inputFocused = true; cx.notify(); });
    this.input.on("blur", (_e, cx) => { this.inputFocused = false; cx.notify(); });
    this.input.focus();
    cx.timer.after(600, () => this.input.focus());
    this.handle = cx.focus_handle();
  }

  submit(cx) {
    const text = this.input.value().replace(/\s+/g, " ").trim();
    if (!text) return;
    const overlay = props()?.overlay;
    cx.spawn(async (cx) => {
      try {
        const where = (await readTextFile(`${appHome()}/dotfiles-path`))?.trim();
        if (!where) throw new Error("no dotfiles-path: run ./install.sh");
        const file = `${where}/requests.md`;
        const old = await readTextFile(file);
        const head = old === null ? "# Requests\n\nBugs and feature requests about this setup, from the Submit dialog (`cmd+shift+b`). Open ones are `- [ ]`.\n\n" : old.replace(/\n*$/, "\n");
        await writeTextFile(file, `${head}- [ ] ${stamp()} · ${this.kind} · ${text}\n`, old);
        closeOverlay(overlay);
        notify({ title: "Submitted", body: `${this.kind}: ${text}`, level: "info", timeout: 3000 });
      } catch (e) {
        this.error = String(e?.message ?? e);
        cx.notify();
      }
    });
  }

  key(e, cx) {
    if (e.key === "escape") { closeOverlay(props()?.overlay); cx.stop_propagation(); }
  }

  render() {
    const t = theme();
    const button = (id, text, primary, action) => h_flex().id(id).h(32).px(14).items_center().rounded(8)
      .border_1().border_color(primary ? t.solid : t.input).bg(primary ? t.solid : t.raised)
      .text_color(primary ? t.solid_foreground : t.foreground).text_size(12.5).font_medium().cursor_pointer()
      .hover(s => s.opacity(0.88)).on_click(action).child(text);
    const tab = (kind) => h_flex().id(`kind-${kind}`).h(28).px(12).items_center().rounded(7).cursor_pointer()
      .text_size(12.5).border_1()
      .border_color(this.kind === kind ? t.accent : t.input)
      .bg(this.kind === kind ? t.raised : t.background)
      .text_color(this.kind === kind ? t.foreground : t.dim)
      .on_click((_e, cx) => { this.kind = kind; this.input.focus(); cx.notify(); }).child(kind);
    return v_flex().id("submit").track_focus(this.handle).on_key_down((e, cx) => this.key(e, cx))
      .w_full().min_h(0).p(18).bg(t.popover).text_color(t.foreground)
      .child(h_flex().items_center().child(div().flex_1().text_size(15).font_semibold().child("Submit a request"))
        .child(div().text_size(11).text_color(t.dim).child("Esc")))
      .child(h_flex().pt(16).gap(8).child(tab("bug")).child(tab("feature")))
      .child(div().pt(12))
      .child(Input.new(this.input).h(36).px(10).rounded(9).border_1().border_color(this.inputFocused ? t.accent : t.input).bg(t.background).text_size(12.8).text_color(t.foreground))
      .child(div().pt(6).text_size(11.5).text_color(this.error ? t.danger ?? "#e5484d" : t.dim)
        .child(this.error || "Appended to requests.md in the herdr-dotfiles repo."))
      .child(h_flex().pt(20).gap(8).justify_end()
        .child(button("submit-cancel", "Cancel", false, () => closeOverlay(props()?.overlay)))
        .child(button("submit-ok", "Submit", true, (_e, cx) => this.submit(cx))));
  }
}
