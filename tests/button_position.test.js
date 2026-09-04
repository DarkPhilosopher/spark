// The button editor's saved custom positions -- reported from a real
// phone: every button drifted to the wrong spot on rotating the screen,
// because the old storage was a fixed pixel offset computed once, for
// whatever orientation happened to be current at the time. Fixed by
// storing a target *percent* of the viewport instead (see
// applyButtonStyle's own long comment in world3d.html) and recomputing
// the actual pixel transform fresh every time against the current
// window size and the button's current plain (untransformed) position.
//
// What's worth testing computationally, since there's no real screen to
// rotate here: does a saved position actually land at the right percent
// after a "resize" this fake DOM simulates (different window size *and*
// a different plain/natural position, standing in for a layout whose
// grid or flex rules genuinely changed between portrait and landscape,
// not just a smaller version of the same layout).

const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "world3d.html"), "utf8");

const s = html.indexOf("const BUTTON_LAYOUT_KEY");
if (s < 0) throw new Error("marker not found: const BUTTON_LAYOUT_KEY");
const e = html.indexOf("function selectEditable", s);
if (e < 0) throw new Error("end marker not found: function selectEditable");
const src = html.slice(s, e);

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
};

// A fake button whose "plain" (untransformed) position is whatever the
// test sets it to -- standing in for wherever a real grid/flex layout
// would have put it, which is exactly what changes across a real resize
// or orientation flip. getBoundingClientRect() adds back whatever
// translate() is currently in style.transform, the same as a real
// browser reporting the rendered (post-transform) box.
class FakeButton {
  constructor(naturalLeft, naturalTop, width, height) {
    this.natural = {left: naturalLeft, top: naturalTop, width, height};
    this.style = {transform: "", opacity: ""};
  }
  getBoundingClientRect() {
    const m = /translate\(([-\d.]+)px, ([-\d.]+)px\)/.exec(this.style.transform || "");
    const tx = m ? parseFloat(m[1]) : 0, ty = m ? parseFloat(m[2]) : 0;
    const {left, top, width, height} = this.natural;
    return {left: left + tx, top: top + ty, width, height,
            right: left + tx + width, bottom: top + ty + height};
  }
}

function load() {
  const store = {};
  const gridSizeEl = {value: "5"};
  const globals = {
    $: sel => (sel === "#edit-grid-size" ? gridSizeEl : {value: "", textContent: "", classList: {toggle() {}}}),
    localStorage: {
      getItem: k => (k in store ? store[k] : null),
      setItem: (k, v) => { store[k] = String(v); },
    },
    window: {innerWidth: 400, innerHeight: 800},
  };
  const mod = {exports: {}};
  const body = src + `
    module.exports = {
      applyButtonStyle, syncButtonPositions, clampToScreen, snapElementToGrid,
      currentPercent, editableButtons, buttonLayout,
      setGridLock: v => { gridLockOn = v; },
      setWindow: (w, h) => { window.innerWidth = w; window.innerHeight = h; },
    };
  `;
  new Function("module", "$", "localStorage", "window", body)(
    mod, globals.$, globals.localStorage, globals.window);
  return {api: mod.exports, window: globals.window};
}

console.log("applyButtonStyle: lands the button at the saved percent of the CURRENT window");
{
  const {api} = load();
  const btn = new FakeButton(0, 0, 40, 40);   // plain position: pinned top-left
  const entry = {xPercent: 50, yPercent: 50};   // dead centre
  api.applyButtonStyle(btn, entry);
  const rect = btn.getBoundingClientRect();
  const cx = rect.left + rect.width / 2, cy = rect.top + rect.height / 2;
  ok("lands at 50%,50% of a 400x800 window (200,400)",
     Math.abs(cx - 200) < 0.01 && Math.abs(cy - 400) < 0.01, [cx, cy]);
}

console.log("\nThe orientation bug itself: a saved percent survives a resize AND a changed plain position");
{
  const {api, window} = load();
  const uid = "test-btn";
  // Portrait: 400x800, plain (grid/flex) position happens to be (10,700) --
  // a button sitting low on the screen, the way the pad's own buttons do.
  const btn = new FakeButton(10, 700, 40, 40);
  api.editableButtons.set(uid, {el: btn, label: "test"});
  api.buttonLayout[uid] = {};
  // Drag it to (roughly) the horizontal centre, a bit up from the bottom.
  api.buttonLayout[uid].xPercent = 50;
  api.buttonLayout[uid].yPercent = 80;
  api.applyButtonStyle(btn, api.buttonLayout[uid]);
  let pos = api.currentPercent(btn);
  ok("lands at the saved percent in portrait", Math.abs(pos.x - 50) < 0.2 && Math.abs(pos.y - 80) < 0.2, pos);

  // Rotate: 800x400 now, AND the plain position is somewhere completely
  // different -- not just scaled, a genuinely different layout (the pad
  // moves from bottom-centre to bottom-right in landscape, e.g.).
  window.innerWidth = 800; window.innerHeight = 400;
  btn.natural = {left: 600, top: 300, width: 40, height: 40};
  api.syncButtonPositions();
  pos = api.currentPercent(btn);
  ok("still lands at the SAME saved percent after the resize, not the old pixel spot",
     Math.abs(pos.x - 50) < 0.2 && Math.abs(pos.y - 80) < 0.2, pos);
  ok("buttonLayout itself is unchanged by the resize -- still 50/80, not rewritten",
     api.buttonLayout[uid].xPercent === 50 && api.buttonLayout[uid].yPercent === 80,
     api.buttonLayout[uid]);
}

console.log("\nclampToScreen: keeps the saved percent itself a safe margin from every edge");
{
  const {api} = load();
  const btn = new FakeButton(0, 0, 40, 40);
  const entry = {xPercent: 100, yPercent: -5};   // off past the right and above the top
  api.applyButtonStyle(btn, entry);
  api.clampToScreen(btn, entry);
  ok("x pulled back in from the right edge", entry.xPercent < 100 && entry.xPercent > 90, entry.xPercent);
  ok("y pulled back in from the top edge", entry.yPercent > 0 && entry.yPercent < 10, entry.yPercent);

  const btn2 = new FakeButton(0, 0, 40, 40);
  const entry2 = {xPercent: 50, yPercent: 50};
  api.applyButtonStyle(btn2, entry2);
  api.clampToScreen(btn2, entry2);
  ok("a comfortably centred position is left untouched", entry2.xPercent === 50 && entry2.yPercent === 50);
}

console.log("\nsnapElementToGrid: rounds the saved percent to the nearest grid line, nothing else");
{
  const {api} = load();
  api.setGridLock(true);
  const btn = new FakeButton(0, 0, 40, 40);
  const entry = {xPercent: 47, yPercent: 53};   // grid size defaults to 5
  api.snapElementToGrid(btn, entry);
  ok("47 snaps to 45", entry.xPercent === 45, entry.xPercent);
  ok("53 snaps to 55", entry.yPercent === 55, entry.yPercent);

  api.setGridLock(false);
  const entry2 = {xPercent: 47, yPercent: 53};
  api.snapElementToGrid(btn, entry2);
  ok("grid lock off leaves it alone", entry2.xPercent === 47 && entry2.yPercent === 53);
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
