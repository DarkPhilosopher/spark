// set_frame/next_frame -- the JS twin of engine/tiles.py's own
// set_frame/next_frame, checked here against the same cases
// tests/check_frames.py runs against the Python engine, minus the
// render() assertions -- this 3D view never draws a Thing's own
// `frames` (it has its own shape/parts system already), only carries
// the field and keeps frameIndex in sync, for a save/load round trip.
// Not the same mechanism as check_engines.py's shared snapshot/parity
// harness (deliberately not extended for this -- see check_harvest.py's
// own long comment for why), but the same goal: catching either engine
// quietly drifting from what the other one does.

const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "world3d.html"), "utf8");

const s = html.indexOf("// ==== SPARK-ENGINE-START ====");
if (s < 0) throw new Error("marker not found: SPARK-ENGINE-START");
const e = html.indexOf("// ==== SPARK-ENGINE-END ====", s);
if (e < 0) throw new Error("end marker not found: SPARK-ENGINE-END");
const src = html.slice(s, e);

const mod = {exports: {}};
new Function("module", src + "\nmodule.exports = {Thing, ACTIONS};")(mod);
const {Thing, ACTIONS} = mod.exports;

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
};

console.log("Thing: picks up a template's own frames, starts on frame 0");
{
  const framesTemplate = {glyph: "b", color: "white", frames: [
    [{dx: 0, dy: 0, glyph: "A", color: "white"}],
    [{dx: 0, dy: 0, glyph: "B", color: "white"}],
  ]};
  const withFrames = new Thing("blob", 2, 2, framesTemplate);
  ok("carries the template's own frames array", withFrames.frames === framesTemplate.frames);
  ok("starts on frame 0", withFrames.frameIndex === 0);

  const withoutFrames = new Thing("plain", 1, 1, {glyph: "P", color: "white"});
  ok("no frames field on the template -> null, not a crash", withoutFrames.frames === null);
  ok("frameIndex still defaults to 0 either way", withoutFrames.frameIndex === 0);
}

console.log("\nset_frame / next_frame: keep frameIndex in sync (this view never renders it)");
{
  const blob = new Thing("blob", 2, 2, {glyph: "b", color: "white", frames: [[], [], []]});

  ACTIONS.next_frame(blob);
  ok("next_frame steps forward by exactly one", blob.frameIndex === 1);

  ACTIONS.set_frame(blob, {}, {index: 2});
  ok("set_frame jumps straight to the one asked for", blob.frameIndex === 2);

  ACTIONS.next_frame(blob);
  ok("just keeps counting up past however many frames exist -- wrapping, if any, is "
     + "the terminal renderer's own job, not this tile's",
     blob.frameIndex === 3);

  ACTIONS.set_frame(blob, {}, {index: -5});
  ok("set_frame never goes negative, even if asked to", blob.frameIndex === 0);
}

console.log("\nset_frame / next_frame are safe to call even with no frames at all yet");
{
  const plain = new Thing("plain", 1, 1, {glyph: "P", color: "white"});
  ACTIONS.next_frame(plain);
  ACTIONS.set_frame(plain, {}, {index: 3});
  ok("no crash -- frameIndex just quietly changes, meaningless without frames to index into",
     plain.frameIndex === 3);
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
