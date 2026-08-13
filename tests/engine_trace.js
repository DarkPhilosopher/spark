// Run the JavaScript engine out of world3d.html and print what happened.
//
//     node tests/engine_trace.js games/chase.json 7 60
//
// Prints one JSON line per tick. tests/check_engines.py runs the Python engine
// over the same game and seed and demands the very same lines back, which is
// what stops the two engines drifting apart. Nothing here knows about WebGL --
// the engine section of that file is deliberately free of the DOM so it can be
// lifted out and driven from a terminal.

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const START = "// ==== SPARK-ENGINE-START ====";
const END = "// ==== SPARK-ENGINE-END ====";

function loadEngine() {
  const html = fs.readFileSync(path.join(ROOT, "world3d.html"), "utf8");
  const from = html.indexOf(START);
  const to = html.indexOf(END);
  if (from < 0 || to < 0)
    throw new Error("the engine markers are gone from world3d.html");
  const src = html.slice(from + START.length, to);
  return new Function(src + "\nreturn {World, Rng, Thing, STEP_LIST};")();
}

// The same keys the Python side presses, on the same ticks, so that games
// built around `key` tiles are exercised rather than sitting still.
const KEY_CYCLE = ["up", "right", "space", "down", "left"];

function trace(engine, project, seed, ticks) {
  const world = new engine.World(project, seed);
  const lines = [snapshot(world)];
  for (let i = 0; i < ticks; i++) {
    world.keys = new Set([KEY_CYCLE[world.tick % KEY_CYCLE.length]]);
    world.step();
    lines.push(snapshot(world));
  }
  return lines;
}

function snapshot(world) {
  return {
    tick: world.tick,
    score: world.score,
    status: world.status,
    message: world.message,
    memory: world.memory,
    things: world.things.map(t => [
      t.kind, t.x, t.y, t.health, t.glyph, t.color,
      t.facing[0], t.facing[1], t.age, t.travelled, t.solid ? 1 : 0,
    ]),
  };
}

function main() {
  const [game, seed, ticks] = process.argv.slice(2);
  const project = JSON.parse(fs.readFileSync(path.join(ROOT, game), "utf8"));
  const engine = loadEngine();
  for (const line of trace(engine, project, Number(seed), Number(ticks)))
    process.stdout.write(JSON.stringify(line) + "\n");
}

main();
