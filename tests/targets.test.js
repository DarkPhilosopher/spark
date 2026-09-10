// mark_target/recall_target -- the JS twin of engine/tiles.py's own
// mark_target/recall_target, checked here against the exact same cases
// tests/check_targets.py runs against the Python engine. Not the same
// mechanism as check_engines.py's shared snapshot/parity harness
// (deliberately not extended for this -- see check_harvest.py's own
// long comment for why), but the same goal: catching either engine
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
new Function("module", src + "\nmodule.exports = {Thing, SENSORS, ACTIONS};")(mod);
const {Thing, SENSORS, ACTIONS} = mod.exports;

let pass = 0, fail = 0;
const ok = (name, cond, extra) => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra !== undefined ? "  -> " + JSON.stringify(extra) : "")); }
};

const thing = (kind, x, y) => new Thing(kind, x || 0, y || 0, {glyph: kind[0], color: "white"});
// tryMove applies the step unconditionally, standing in for the real
// one's bounds/solidity checks, which mark_target/recall_target never
// touch anyway.
const world = () => ({targets: {}, tryMove: (obj, dx, dy) => { obj.x += dx; obj.y += dy; }});

console.log("mark_target: with an it, saves the actual character -- a live reference");
{
  const hero = thing("hero", 1, 1), enemy = thing("bandit", 5, 1);
  const w = world();
  ACTIONS.mark_target(hero, w, {name: "enemy"}, enemy);
  ok("the bandit itself is what got saved, not a copy", w.targets.enemy === enemy);
}

console.log("\nrecall_target: hands the saved character back as it, so \"toward it\" chases it live");
{
  const hero = thing("hero", 1, 1), enemy = thing("bandit", 5, 1);
  const w = world();
  ACTIONS.mark_target(hero, w, {name: "enemy"}, enemy);
  let it = SENSORS.recall_target(hero, w, {name: "enemy"});
  ACTIONS.move(hero, w, {dir: "toward it"}, it);
  ok("took a step toward it right away", hero.x === 2, hero.x);

  enemy.x = 8;   // the bandit itself moved -- a placeholder's frozen vector couldn't follow this
  it = SENSORS.recall_target(hero, w, {name: "enemy"});
  ACTIONS.move(hero, w, {dir: "toward it"}, it);
  ok("recall_target still points at the SAME (now-moved) bandit -- keeps following it",
     hero.x === 3, hero.x);
}

console.log("\na name never marked reads false, not a crash");
{
  const hero = thing("hero", 1, 1);
  const w = world();
  const it = SENSORS.recall_target(hero, w, {name: "enemy"});
  ok("nothing marked yet -- reads false", it === false, it);
}

console.log("\na dead target is the same as never having marked one -- no chasing a corpse");
{
  const hero = thing("hero", 1, 1), enemy = thing("bandit", 5, 1);
  const w = world();
  ACTIONS.mark_target(hero, w, {name: "enemy"});   // no it yet -- overwritten below
  ACTIONS.mark_target(hero, w, {name: "enemy"}, enemy);
  enemy.alive = false;
  const it = SENSORS.recall_target(hero, w, {name: "enemy"});
  ok("the reference is still in world.targets (nothing clears it on death)...",
     w.targets.enemy === enemy);
  ok("...but recall_target reads false once it's dead, so no more chasing", it === false, it);
}

console.log("\nmark_target: with no it at all, saves my OWN spot as a frozen location");
{
  const hero = thing("hero", 4, 6);
  const w = world();
  ACTIONS.mark_target(hero, w, {name: "spot"}, null);
  const spot = w.targets.spot;
  ok("something got saved", !!spot);
  ok("it sits at the hero's own square", spot.x === 4 && spot.y === 6, [spot.x, spot.y]);
  ok("it's a real Thing instance -- move/face/shoot can read it.x/it.y",
     spot instanceof Thing);
}

console.log("\nan empty name is refused, same as remember's own");
{
  const hero = thing("hero", 1, 1);
  const w = world();
  ACTIONS.mark_target(hero, w, {name: "   "}, null);
  ok("nothing gets saved under a blank name", Object.keys(w.targets).length === 0, w.targets);
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
