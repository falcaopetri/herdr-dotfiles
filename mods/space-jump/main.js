// space-jump: keys.json "space-jump.<n>" goes to the nth space. Draws nothing: dock it in a 0px block.
// Order is Herdr's own (this machine first, then other machines by name), which is the list's order
// unless Pinned or sections move rows around. Idea from jorgeorejas/herdr-jump (Apache-2.0).

import { View, div } from "gpui-kit";
import { spaces, run, nextCommand } from "herdr";

export default class SpaceJump extends View {
  init(_props, cx) {
    cx.spawn(async () => {
      for (;;) {
        const n = Number(await nextCommand());
        const id = n >= 1 ? spaces()[n - 1]?.id : null;
        if (id) run("space.select", { id });
      }
    });
  }

  render() {
    return div().id("space-jump").size_full();
  }
}
