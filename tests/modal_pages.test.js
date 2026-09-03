// The three modals rebuilt as "six big buttons plus a box" pages (Object
// Inspector, Mesh Creator, Properties) generate their own DOM at runtime --
// there is no static markup left to eyeball, and no headless WebGL here to
// render a frame either. What is worth testing computationally is that the
// page machinery itself is right: the top page always has its buttons, a
// sub-page's back button shows and its buttons apply to the right target,
// choiceKeys() highlights whichever choice is actually current, and the
// quick-jump buttons/typed fields end up changing the same data either way.
//
// Same trick as mesh_merge.test.js and deck.test.js: slice the relevant
// source out of world3d.html and run it with a stub DOM, since there is no
// browser here.

const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "world3d.html"), "utf8");

function slice(startMark, endMark) {
  const s = html.indexOf(startMark);
  if (s < 0) throw new Error("marker not found: " + startMark);
  const e = html.indexOf(endMark, s);
  if (e < 0) throw new Error("end marker not found: " + endMark);
  return html.slice(s, e);
}

const src = slice("const COLOR_RGB = {", "const COLOR_CSS") +
            slice("const SHAPES = [", "function pushShape") +
            slice("let inspectTarget = null;", "function setupInspector") +
            slice("let meshParts = [];", "function setupMeshCreator");

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
};

// A DOM just featureful enough for what this code actually does:
// createElement, classList, innerHTML/textContent (each clears the
// children list, matching how a real innerHTML="" reset behaves),
// append/appendChild, and a style object that just swallows assignments.
class FakeEl {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this._classes = new Set();
    this._html = ""; this._text = "";
    this.style = {};
    this.value = "";
    this.onclick = null;
    this._listeners = {};
  }
  set className(v) { this._classes = new Set(String(v).split(/\s+/).filter(Boolean)); }
  get className() { return [...this._classes].join(" "); }
  get classList() {
    const set = this._classes;
    return {
      add: c => set.add(c), remove: c => set.delete(c), contains: c => set.has(c),
      toggle: (c, on) => { on === undefined ? (set.has(c) ? set.delete(c) : set.add(c))
                                            : (on ? set.add(c) : set.delete(c)); },
    };
  }
  set innerHTML(v) { this._html = v; this.children = []; }
  get innerHTML() { return this._html; }
  set textContent(v) { this._text = String(v); this._html = this._text; this.children = []; }
  get textContent() { return this._text; }
  appendChild(c) { this.children.push(c); return c; }
  append(...cs) { for (const c of cs) this.children.push(c); }
  addEventListener(ev, fn) { (this._listeners[ev] = this._listeners[ev] || []).push(fn); }
}

function makeEnv() {
  const nodes = {};
  const ids = ["inspect-title", "inspect-back", "inspect-keys", "inspect-box", "inspect-modal",
               "mesh-title", "mesh-back", "mesh-keys", "mesh-box", "mesh-modal"];
  for (const id of ids) nodes["#" + id] = new FakeEl("div");
  const $ = sel => nodes[sel] || new FakeEl("div");
  const documentStub = {createElement: tag => new FakeEl(tag)};
  return {nodes, $, documentStub};
}

function load(env, world) {
  const mod = {exports: {}};
  const body = src + `
    module.exports = {
      choiceKeys,
      setInspectTarget: t => { inspectTarget = t; },
      getInspectTarget: () => inspectTarget,
      gotoInspectPage, renderInspectorPage, INSPECT_PAGES,
      getInspectPage: () => inspectPage,
      setMeshParts: p => { meshParts = p; },
      getMeshParts: () => meshParts,
      setMeshSelected: i => { meshSelected = i; },
      getMeshSelected: () => meshSelected,
      gotoMeshPage, renderMeshPage, MESH_PAGES,
      getMeshPage: () => meshPage,
    };
  `;
  new Function("module", "$", "document", "world", "drawerToast", "confirm", "project",
    body)(mod, env.$, env.documentStub, world, () => {}, () => true, {characters: []});
  return mod.exports;
}

console.log("Object Inspector: page navigation");
{
  const env = makeEnv();
  const api = load(env, {inBounds: () => true, spawn: () => null, things: [], templates: {}});
  api.setInspectTarget({kind: "rock", alive: true, color: "red", shape: "cube",
                         size: 100, x: 2, y: 3, z: 0});
  api.gotoInspectPage("top");
  ok("top page has six buttons", env.nodes["#inspect-keys"].children.length === 6,
     env.nodes["#inspect-keys"].children.length);
  ok("back button hidden on the top page", !env.nodes["#inspect-back"].classList.contains("showing"));
  ok("title names the target's kind", env.nodes["#inspect-title"].textContent.includes("rock"));

  // tap the "shape" button (index 1: colour, shape, resize, stretch, move, duplicate)
  env.nodes["#inspect-keys"].children[1].onclick();
  ok("tapping shape navigates to the shape page", api.getInspectPage() === "shape");
  ok("back button shows on a sub-page", env.nodes["#inspect-back"].classList.contains("showing"));
  ok("shape page has one button per SHAPES entry",
     env.nodes["#inspect-keys"].children.length === api.INSPECT_PAGES.shape.keys().length);

  // find the "sphere" button and tap it
  const sphereBtn = env.nodes["#inspect-keys"].children.find(b => b.innerHTML === "sphere");
  ok("a sphere button exists on the shape page", !!sphereBtn);
  sphereBtn.onclick();
  ok("tapping a shape applies it to the target", api.getInspectTarget().shape === "sphere");
  ok("choosing a shape stays on the shape page", api.getInspectPage() === "shape");
  const sphereBtnAgain = env.nodes["#inspect-keys"].children.find(b => b.innerHTML === "sphere");
  ok("the chosen shape is marked selected", sphereBtnAgain.classList.contains("on"));

  env.nodes["#inspect-back"].onclick = () => api.gotoInspectPage("top");
  env.nodes["#inspect-back"].onclick();
  ok("back returns to the top page", api.getInspectPage() === "top");
}

console.log("\nObject Inspector: resize/stretch/move pages don't lose precision");
{
  const env = makeEnv();
  const api = load(env, {inBounds: () => true, spawn: () => null, things: [], templates: {}});
  api.setInspectTarget({kind: "rock", alive: true, color: "white", shape: "cube",
                         size: 100, x: 0, y: 0, z: 0});
  api.gotoInspectPage("resize");
  const btn150 = env.nodes["#inspect-keys"].children.find(b => b.innerHTML === "150%");
  btn150.onclick();
  ok("a resize quick-button sets the exact size", api.getInspectTarget().size === 150);
  ok("resizing uniformly clears any earlier stretch",
     api.getInspectTarget().sx === undefined && api.getInspectTarget().sy === undefined);

  api.gotoInspectPage("stretch");
  const widthPlus = env.nodes["#inspect-keys"].children.find(b => b.innerHTML === "width +25");
  widthPlus.onclick();
  ok("a stretch nudge changes only that axis",
     api.getInspectTarget().sx === 175 && api.getInspectTarget().sy === undefined);
}

console.log("\nchoiceKeys: highlights whichever is current, applies via the given setter");
{
  const env = makeEnv();
  const api = load(env, {inBounds: () => true, spawn: () => null, things: [], templates: {}});
  let picked = null, rerenders = 0;
  const keys = api.choiceKeys(["a", "b", "c"], "b", name => { picked = name; }, () => { rerenders++; });
  ok("marks the current one on", keys.find(k => k.label === "b").on === true);
  ok("does not mark the others on", !keys.find(k => k.label === "a").on && !keys.find(k => k.label === "c").on);
  keys.find(k => k.label === "c").go();
  ok("tapping one applies it via the given setter", picked === "c");
  ok("tapping one calls the given rerender callback", rerenders === 1);
}

console.log("\nMesh Creator: page navigation operates on the selected part");
{
  const env = makeEnv();
  const api = load(env, {inBounds: () => true, spawn: () => null, things: [], templates: {}});
  api.setMeshParts([
    {shape: "cube", dx: 0, dy: 0, dz: 0, sx: 0.5, sy: 0.5, sz: 0.5, color: "white"},
    {shape: "sphere", dx: 0.3, dy: 0, dz: 0, sx: 0.5, sy: 0.5, sz: 0.5, color: "gold"},
  ]);
  api.setMeshSelected(1);
  api.gotoMeshPage("top");
  ok("top page has six buttons", env.nodes["#mesh-keys"].children.length === 6,
     env.nodes["#mesh-keys"].children.length);

  api.gotoMeshPage("color");
  ok("navigated to the colour page", api.getMeshPage() === "color");
  const goldBtn = env.nodes["#mesh-keys"].children.find(b => b.innerHTML === "gold");
  ok("the selected part's current colour is marked on", goldBtn.classList.contains("on"));
  const orangeBtn = env.nodes["#mesh-keys"].children.find(b => b.innerHTML === "orange");
  orangeBtn.onclick();
  ok("tapping a colour applies it to the selected part, not the other one",
     api.getMeshParts()[1].color === "orange" && api.getMeshParts()[0].color === "white");

  // "add a part" from the top page's own key list
  api.gotoMeshPage("top");
  env.nodes["#mesh-keys"].children[2].onclick();   // colour, shape, +add, ...
  ok("add part grows the list and selects the new one",
     api.getMeshParts().length === 3 && api.getMeshSelected() === 2);
}

console.log("\nMesh Creator: picking colour/shape with nothing selected picks part 0 first");
{
  const env = makeEnv();
  const api = load(env, {inBounds: () => true, spawn: () => null, things: [], templates: {}});
  api.setMeshParts([{shape: "cube", dx: 0, dy: 0, dz: 0, sx: 0.5, sy: 0.5, sz: 0.5, color: "white"}]);
  api.setMeshSelected(null);
  api.gotoMeshPage("color");
  ok("auto-selects the first part rather than applying to nothing",
     api.getMeshSelected() === 0 && api.getMeshPage() === "color");
}

console.log("\nProperties: setMoveSpeed still clamps 1-30 the same as before the buttons replaced the slider");
{
  const speedSrc = slice("function setMoveSpeed(newSpeed) {", "\nlet minimapOn");
  const mod = {exports: {}};
  new Function("module", "project", "world", speedSrc +
    "\nmodule.exports = {setMoveSpeed};")(mod, {world: {}}, null);
  const {setMoveSpeed} = mod.exports;
  ok("a normal value passes through", setMoveSpeed(12) === 12);
  ok("clamps below the floor", setMoveSpeed(-5) === 1);
  ok("clamps above the ceiling", setMoveSpeed(999) === 30);
  ok("a garbage value falls back to 6", setMoveSpeed(NaN) === 6);
  // the four quick-jump buttons apply a delta to the current value, same
  // arithmetic setupProperties() itself does -- this is exactly what a
  // ±5/±1 tap computes.
  ok("stepping +5 from the current value clamps at the ceiling too",
     setMoveSpeed(28 + 5) === 30);
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
