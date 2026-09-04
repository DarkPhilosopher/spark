// draw_line/world.lines -- the JS twin of engine/tiles.py's own draw_line,
// checked against the same cases tests/check_draw_line.py runs against
// the Python engine (same reasoning as harvest_tiles.test.js/
// check_harvest.py: not wired into check_engines.py's shared snapshot
// harness, each engine checked against the same cases in its own
// dedicated test instead). Plus pushLine() itself, the one shape here
// whose long axis isn't x/y/z the way pushBox's always is -- worth
// checking its vertex count, that every number in it is finite, and that
// its face normals actually are unit length, the same things a headless
// render can't confirm here but arithmetic can.

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

const src = slice("const num = ", "// ==== SPARK-ENGINE-END ====") +
            slice("function pushLine(", "const SHAPES = [");

const mod = {exports: {}};
new Function("module", src + "\nmodule.exports = {Thing, SENSORS, ACTIONS, pushLine};")(mod);
const {Thing, ACTIONS, pushLine} = mod.exports;

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
};

const thing = (kind, x, y, z) => {
  const t = new Thing(kind, x, y, {glyph: kind[0], color: "white"});
  t.z = z || 0;
  return t;
};
const draw = (obj, world, start, end, color, it) =>
  ACTIONS.draw_line(obj, world, {start, end, color}, it);

console.log("draw_line: records exactly what was asked, nothing more");
{
  const hero = thing("hero", 1, 1, 0), world = {lines: []};
  draw(hero, world, "self", "self", "gold");
  ok("self-to-self records a zero-length line, not nothing",
     JSON.stringify(world.lines) ===
     JSON.stringify([{x1: 1, y1: 1, z1: 0, x2: 1, y2: 1, z2: 0, color: "gold"}]), world.lines);

  const hero2 = thing("hero", 1, 1, 0), cone = thing("cone", 1, 1, 2), world2 = {lines: []};
  draw(hero2, world2, "self", "it", "pink", cone);
  ok("self-to-it records both ends' real positions, altitude included",
     JSON.stringify(world2.lines) ===
     JSON.stringify([{x1: 1, y1: 1, z1: 0, x2: 1, y2: 1, z2: 2, color: "pink"}]), world2.lines);

  const hero3 = thing("hero", 0, 0, 0), world3 = {lines: []};
  draw(hero3, world3, "self", "it", "white", null);
  ok("no \"it\" established -- draws nothing, not a stray line to the origin",
     world3.lines.length === 0, world3.lines);
}

console.log("\npushLine: valid triangle geometry, the same standard the other push* shapes meet");
{
  const out = [];
  pushLine(out, 0, 0, 0, 1, 0, 0, [1, 0.8, 0.2], 1, 0.06);
  const stride = 10;
  ok("a full box between two points: 6 faces x 2 triangles x 3 vertices",
     out.length === 6 * 2 * 3 * stride, out.length / stride);
  ok("every number in it is finite, none are NaN",
     out.every(Number.isFinite), out.filter(n => !Number.isFinite(n)));
  let normalsOk = true;
  for (let i = 0; i < out.length; i += stride) {
    const len = Math.hypot(out[i + 3], out[i + 4], out[i + 5]);
    if (Math.abs(len - 1) > 1e-4) normalsOk = false;
  }
  ok("every vertex's normal is unit length", normalsOk);

  const empty = [];
  pushLine(empty, 2, 2, 2, 2, 2, 2, [1, 1, 1], 1, 0.06);
  ok("coincident endpoints push no geometry at all, not a zero-size box", empty.length === 0);

  const vertical = [];
  pushLine(vertical, 0, 0, 0, 0, 5, 0, [1, 1, 1], 1, 0.06);
  ok("a straight-up line (parallel to the usual \"up\" reference) still produces a valid box",
     vertical.length === 6 * 2 * 3 * stride && vertical.every(Number.isFinite));
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
