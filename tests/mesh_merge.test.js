// Pull the merge-geometry functions out of world3d.html and drive them
// directly, since there is no headless WebGL here to render an actual
// frame and look at it -- the same trick store.test.js and deck.test.js
// use for index.html. What's worth testing here is not the rendering
// (which needs eyes on a real device) but the arithmetic: does merging
// two objects produce the offsets it should, and does dropHiddenParts
// actually drop what's fully hidden while keeping everything that isn't.

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

// SHAPES/ROUND_HEIGHT_SHAPES, effectiveDims(), and the merge functions
// (partBounds/boxInside/dropHiddenParts/mergeThings) -- deliberately not
// mergeSelectedObjects/toggleMerge/addToMergeSelection/drawMergeHighlights,
// which need a DOM (prompt, $, world, project) this harness doesn't have.
const src = slice("const SHAPES = [", "function pushShape") +
            slice("function effectiveDims(thing) {", "\n\nclass Renderer") +
            slice("function partBounds(p) {", "\nfunction mergeSelectedObjects");

const mod = {exports: {}};
new Function("module", src + "\nmodule.exports = " +
  "{effectiveDims, partBounds, boxInside, dropHiddenParts, mergeThings};")(mod);
const {effectiveDims, boxInside, dropHiddenParts, mergeThings} = mod.exports;

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
};

// A minimal stand-in for a live Thing -- only the fields effectiveDims()
// and mergeThings() actually read.
const T = (x, y, extra = {}) => ({
  kind: "t", x, y, z: 0, color: "white", role: "prop", solid: true,
  shape: "cube", size: 100, sx: undefined, sy: undefined, sz: undefined,
  ...extra,
});

console.log("effectiveDims: matches the known single-shape formula");
{
  const d = effectiveDims(T(0, 0));
  ok("a default solid prop cube is 0.86 wide/deep, 1.0 tall (solid -> tall=1.0)",
     Math.abs(d.sizeX - 0.86) < 1e-9 && Math.abs(d.height - 1.0) < 1e-9, d);
  const full = effectiveDims(T(0, 0, {full: true}));
  ok("full fills the whole cell in every dimension",
     full.sizeX === 1 && full.height === 1 && full.sizeZ === 1, full);
  const round = effectiveDims(T(0, 0, {shape: "sphere", sx: 200}));
  ok("a round shape's height follows its own stretched width when sy is unset",
     Math.abs(round.height - round.sizeX) < 1e-9, round);
}

console.log("\nmergeThings: basic geometry");
{
  const a = T(5, 5), b = T(6, 5);
  const m = mergeThings([a, b]);
  ok("two objects -> two parts", m.parts.length === 2, m.parts);
  ok("the first object is the reference, offset (0,0,0)",
     m.parts[0].dx === 0 && m.parts[0].dy === 0 && m.parts[0].dz === 0, m.parts[0]);
  ok("the second is offset by exactly the grid distance between them",
     m.parts[1].dx === 1 && m.parts[1].dy === 0, m.parts[1]);
  ok("fewer than two selected -> null, nothing to merge", mergeThings([a]) === null);
}

console.log("\nmergeThings + dropHiddenParts: the 'remove inner geometry' case");
{
  // A big full-cell block, and a small default prop sitting in the very
  // same cell -- the small one's box is entirely inside the big one's.
  const big = T(3, 3, {full: true, size: 300});
  const small = T(3, 3, {size: 40});
  const m = mergeThings([big, small]);
  ok("the fully-contained part is dropped", m.parts.length === 1, m.parts);
  ok("...and it's the big one that survives, not the hidden small one",
     m.parts[0].sx > 1, m.parts[0]);
}
{
  // Two objects that only partly overlap must both survive -- this is
  // exactly the case real CSG would clip, and this deliberately does not
  // attempt to (see the comment above dropHiddenParts in world3d.html).
  const a = T(0, 0, {full: true}), b = T(1, 0, {full: true});
  const m = mergeThings([a, b]);
  m.parts[1].dx = 0.5;   // hand-contrive a half-overlap between them
  const kept = dropHiddenParts(m.parts);
  ok("a part that only partly overlaps another survives, both of them",
     kept.length === 2, kept);
}
{
  // Two parts with identical bounds: exactly one should survive, not
  // zero (both mutually "contained") and not both (never de-duplicated).
  const parts = [
    {shape: "cube", dx: 0, dy: 0, dz: 0, sx: 0.5, sy: 0.5, sz: 0.5, color: "red"},
    {shape: "cube", dx: 0, dy: 0, dz: 0, sx: 0.5, sy: 0.5, sz: 0.5, color: "blue"},
  ];
  const kept = dropHiddenParts(parts);
  ok("an exact duplicate pair collapses to exactly one, not zero or two",
     kept.length === 1, kept);
}

console.log("\nmergeThings: composing an already-merged object");
{
  const alreadyMerged = T(2, 2, {
    parts: [{shape: "cube", dx: 0.2, dy: 0, dz: 0, sx: 0.3, sy: 0.3, sz: 0.3, color: "gold"},
            {shape: "sphere", dx: -0.2, dy: 0, dz: 0, sx: 0.3, sy: 0.3, sz: 0.3, color: "gold"}],
  });
  const plain = T(3, 2);
  const m = mergeThings([alreadyMerged, plain]);
  ok("a Thing with its own parts contributes each of them, not one flattened box",
     m.parts.length === 3, m.parts);
  ok("its parts keep their own offsets composed with the Thing's own offset",
     m.parts[0].dx === 0.2 && m.parts[1].dx === -0.2, m.parts.slice(0, 2));
  ok("the plain object after it is offset by the grid distance from the reference",
     m.parts[2].dx === 1, m.parts[2]);
}

console.log("\nboxInside: the containment test itself");
{
  const outer = {x0: 0, x1: 2, y0: 0, y1: 2, z0: 0, z1: 2};
  const innerStrict = {x0: 0.5, x1: 1, y0: 0.5, y1: 1, z0: 0.5, z1: 1};
  const sameAsOuter = {...outer};
  const overlapping = {x0: 1, x1: 3, y0: 0, y1: 2, z0: 0, z1: 2};
  ok("a strictly smaller box inside another is 'inside'", boxInside(innerStrict, outer));
  ok("a box is inside an identical one (used for the tie-break)", boxInside(sameAsOuter, outer));
  ok("a box sticking out on one side is not 'inside'", !boxInside(overlapping, outer));
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
