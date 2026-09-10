// lead/dismiss/has_leader -- the JS twin of engine/tiles.py's own
// lead/dismiss/has_leader, checked here against the exact same cases
// tests/check_lead.py runs against the Python engine. Not the same
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
// A world just featureful enough for the move tile: tryMove applies the
// step unconditionally, standing in for the real one's bounds/solidity
// checks, which lead/dismiss/has_leader themselves never touch anyway.
const world = () => ({tryMove: (obj, dx, dy) => { obj.x += dx; obj.y += dy; }});

console.log("lead: touching a companion makes it follow whoever touched it, not the other way");
{
  const hero = thing("hero"), companion = thing("companion");
  ACTIONS.lead(hero, world(), {target: "it"}, companion);
  ok("the companion's leader becomes the hero", companion.leader === hero, companion.leader);
  ok("the hero itself gets no leader -- lead never runs on the recruiter", hero.leader === null);
}

console.log("\nhas_leader: hands the leader back as `it`, so the ordinary move tile can chase it");
{
  const hero = thing("hero", 5, 5), companion = thing("companion", 5, 2);
  ok("no leader yet reads false, not the companion itself",
     SENSORS.has_leader(companion) === false);

  ACTIONS.lead(hero, world(), {target: "it"}, companion);
  const leader = SENSORS.has_leader(companion);
  ok("has_leader returns the leader Thing once recruited", leader === hero);

  ACTIONS.move(companion, world(), {dir: "toward it"}, leader);
  ok("move toward it (unchanged) chases the leader it was handed",
     companion.y === 3, companion.y);
}

console.log("\ndismiss: lets a companion go, and it stops chasing");
{
  const hero = thing("hero"), companion = thing("companion");
  ACTIONS.lead(hero, world(), {target: "it"}, companion);
  ok("recruited first", companion.leader === hero);
  ACTIONS.dismiss(hero, world(), {target: "it"}, companion);
  ok("dismissing clears the leader", companion.leader === null, companion.leader);
}

console.log("\na dead leader is the same as never having had one -- no chasing a corpse");
{
  const hero = thing("hero"), companion = thing("companion");
  ACTIONS.lead(hero, world(), {target: "it"}, companion);
  ok("recruited", companion.leader === hero);
  hero.alive = false;
  ok("the leader reference is still there (nothing clears it on death)...",
     companion.leader === hero);
  ok("...but has_leader reads false once it's dead, so no more chasing",
     SENSORS.has_leader(companion) === false);
}

console.log("\ntarget \"self\": a companion can dismiss (or lead) itself, not just whoever it touches");
{
  const hero = thing("hero"), companion = thing("companion");
  ACTIONS.lead(hero, world(), {target: "it"}, companion);
  ok("recruited", companion.leader === hero);
  ACTIONS.dismiss(companion, world(), {target: "self"}, hero);
  ok("dismissing itself clears its own leader regardless of `it`",
     companion.leader === null, companion.leader);

  const loner = thing("loner");
  ACTIONS.lead(loner, world(), {target: "self"}, null);
  ok("leading \"self\" with no `it` around still just works (no crash, no-op target)",
     loner.leader === loner);
}

console.log("\nrecruit: \"buy a unit\" -- spawns at MY spot, already following me");
{
  // A world just featureful enough for the real spawn() to work off of:
  // a templates lookup and in-bounds check, exactly what recruit itself
  // calls through.
  const templates = {worker: {glyph: "w", color: "yellow"}};
  const w = {
    templates, things: [],
    inBounds: () => true,
    spawn(kind, x, y) {
      const t = templates[kind];
      if (!t) return null;
      const fresh = new Thing(kind, x, y, t);
      this.things.push(fresh);
      return fresh;
    },
  };
  const hero = thing("hero", 5, 5);
  ACTIONS.recruit(hero, w, {kind: "worker"});
  ok("a fresh worker actually appears", w.things.length === 1, w.things.map(t => t.kind));
  const fresh = w.things[0];
  ok("it spawns at the recruiter's own spot, not a random empty cell",
     fresh.x === 5 && fresh.y === 5, [fresh.x, fresh.y]);
  ok("...and already follows whoever recruited it -- no separate lead needed",
     fresh.leader === hero, fresh.leader);

  ACTIONS.recruit(hero, w, {kind: "no-such-kind"});
  ok("an unknown kind is simply a no-op, not a crash", w.things.length === 1);
}

console.log("\n" + pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
