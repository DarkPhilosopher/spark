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

// A persistent, stateful stand-in for a handful of real elements --
// #edit-grid-size and everything #edit-mini holds -- so a value set() on
// one $() call is still there to read back on the next one, the way a
// real DOM element (one object, however many times you re-select it) is.
function makeNodeRegistry() {
  const nodes = {};
  for (const id of ["edit-grid-size", "edit-mini-label", "edit-mini-size", "edit-mini-opacity",
                     "edit-props-title"]) {
    nodes["#" + id] = {value: "", textContent: ""};
  }
  const classes = new Set();
  nodes["#edit-mini"] = {classList: {
    add: c => classes.add(c), remove: c => classes.delete(c), contains: c => classes.has(c),
  }};
  const propsClasses = new Set();
  nodes["#edit-props-page"] = {classList: {
    add: c => propsClasses.add(c), remove: c => propsClasses.delete(c), contains: c => propsClasses.has(c),
  }};
  nodes["#edit-grid-size"].value = "5";
  return nodes;
}

function load(presetStore) {
  const store = presetStore || {};
  const nodes = makeNodeRegistry();
  const globals = {
    $: sel => nodes[sel] || {value: "", textContent: "", classList: {toggle() {}, add() {}, remove() {}}},
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
      exitPickMode, updateMiniPopup,
      openPropertiesPage, closePropertiesPage,
      currentOrientation, allButtonLayouts, checkOrientationSwitch,
      getButtonLayout: () => buttonLayout,   // buttonLayout itself gets reassigned on a switch
      setGridLock: v => { gridLockOn = v; },
      setPickMode: v => { pickModeOn = v; },
      getPickMode: () => pickModeOn,
      setSelected: uid => { editSelected = uid; },
      getSelected: () => editSelected,
      setWindow: (w, h) => { window.innerWidth = w; window.innerHeight = h; },
    };
  `;
  new Function("module", "$", "localStorage", "window", body)(
    mod, globals.$, globals.localStorage, globals.window);
  return {api: mod.exports, window: globals.window, nodes};
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

console.log("\n\"pick on screen\": the floating readout tracks whatever's selected");
{
  const {api, nodes} = load();
  const uid = "restart";
  api.editableButtons.set(uid, {el: new FakeButton(0, 0, 40, 40), label: "restart"});
  api.buttonLayout[uid] = {scale: 1.2, opacity: 0.5};

  api.setPickMode(false);
  api.setSelected(uid);
  api.updateMiniPopup();
  ok("does nothing while pick mode is off", nodes["#edit-mini-label"].textContent === "");

  api.setPickMode(true);
  api.setSelected(null);
  api.updateMiniPopup();
  ok("with nothing selected, says so rather than showing stale data",
     nodes["#edit-mini-label"].textContent === "tap a button…");

  api.setSelected(uid);
  api.updateMiniPopup();
  ok("shows the selected button's own label", nodes["#edit-mini-label"].textContent === "restart");
  ok("the meter reads that button's saved size (scale 1.2 -> 120%)",
     Math.abs(parseFloat(nodes["#edit-mini-size"].value) - 120) < 0.01,
     nodes["#edit-mini-size"].value);
  ok("the text box reads that button's saved opacity (0.5 -> 50%)",
     Math.abs(parseFloat(nodes["#edit-mini-opacity"].value) - 50) < 0.01,
     nodes["#edit-mini-opacity"].value);

  api.exitPickMode();
  ok("exitPickMode turns pick mode off", api.getPickMode() === false);
  ok("...and hides the readout", !nodes["#edit-mini"].classList.contains("on"));
}

console.log("\nthe properties page: opens for a real selection, closes without deselecting");
{
  const {api, nodes} = load();
  const uid = "restart";
  api.editableButtons.set(uid, {el: new FakeButton(0, 0, 40, 40), label: "restart"});
  api.buttonLayout[uid] = {};

  api.setSelected(null);
  api.openPropertiesPage();
  ok("nothing selected -> refuses to open", !nodes["#edit-props-page"].classList.contains("on"));

  api.setSelected(uid);
  api.openPropertiesPage();
  ok("a real selection -> opens", nodes["#edit-props-page"].classList.contains("on"));
  ok("titles itself with the selected button's own label",
     nodes["#edit-props-title"].textContent === "restart");

  api.closePropertiesPage();
  ok("closing hides the page again", !nodes["#edit-props-page"].classList.contains("on"));
  ok("...but does NOT deselect -- reopening picks up where it left off", api.getSelected() === uid);
  api.openPropertiesPage();
  ok("reopening after a close (same selection still standing) works again",
     nodes["#edit-props-page"].classList.contains("on"));
}

console.log("\none preset per rotation: portrait and landscape stay independent");
{
  const {api} = load();   // window starts at 400x800 -- portrait
  ok("starts in portrait", api.currentOrientation() === "portrait");

  const uid = "restart";
  api.editableButtons.set(uid, {el: new FakeButton(0, 0, 40, 40), label: "restart"});
  // Customize it in portrait.
  api.getButtonLayout()[uid] = {xPercent: 10, yPercent: 10};

  api.setWindow(800, 400);   // rotate
  api.checkOrientationSwitch();
  ok("checkOrientationSwitch flips currentOrientation", api.currentOrientation() === "landscape");
  ok("buttonLayout now points at the landscape preset, not portrait's",
     api.getButtonLayout() === api.allButtonLayouts.landscape);
  ok("landscape has no preset for this button yet -- it's not carried over from portrait",
     api.getButtonLayout()[uid] === undefined);
  ok("the element itself was reset (no leftover portrait transform)",
     api.editableButtons.get(uid).el.style.transform === "");

  // Customize it differently in landscape.
  api.getButtonLayout()[uid] = {xPercent: 90, yPercent: 90};

  api.setWindow(400, 800);   // rotate back
  api.checkOrientationSwitch();
  ok("back to portrait", api.currentOrientation() === "portrait");
  ok("portrait's own customization is exactly as it was left, untouched by landscape's",
     api.getButtonLayout()[uid].xPercent === 10 && api.getButtonLayout()[uid].yPercent === 10,
     api.getButtonLayout()[uid]);
  ok("landscape's customization is still there too, independently",
     api.allButtonLayouts.landscape[uid].xPercent === 90);
}

console.log("\ncheckOrientationSwitch: a plain resize within the same orientation is a no-op");
{
  const {api} = load();
  const before = api.getButtonLayout();
  api.setWindow(420, 900);   // still portrait, just a different height (address bar, e.g.)
  api.checkOrientationSwitch();
  ok("still portrait", api.currentOrientation() === "portrait");
  ok("buttonLayout is the exact same object, not swapped for nothing",
     api.getButtonLayout() === before);
}

console.log("\nan old, pre-preset save (one flat {uid: entry}) migrates into both, once");
{
  const oldFlatSave = {"restart": {xPercent: 33, yPercent: 66}};
  const {api} = load({"spark3d-button-layout": JSON.stringify(oldFlatSave)});
  ok("portrait picks up the old save", api.allButtonLayouts.portrait.restart.xPercent === 33,
     api.allButtonLayouts.portrait);
  ok("landscape picks up the same old save too, not left empty",
     api.allButtonLayouts.landscape.restart.xPercent === 33, api.allButtonLayouts.landscape);
  ok("the two are separate copies, not the same object (editing one can't leak into the other)",
     api.allButtonLayouts.portrait.restart !== api.allButtonLayouts.landscape.restart);
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
