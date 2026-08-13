#!/usr/bin/env python3
"""Check that the two engines agree, tick for tick.

    python3 tests/check_engines.py

Spark has two copies of its rules now: engine/world.py, and the JavaScript one
inside world3d.html that runs when nothing is reachable -- no Termux, no
Cloudflare, no GitHub. Two copies of anything drift apart. This is what stops
them: every game gets played twice, once by each engine, from the same seed and
with the same keys pressed on the same ticks, and every character must be in
the same square with the same health at every tick.

If this fails after you changed a rule, you changed it in one engine only.

Needs node. Without it the check says so and stops rather than pretending.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import brain                                        # noqa: E402
from engine.world import World                                  # noqa: E402

# Must match KEY_CYCLE in tests/engine_trace.js.
KEY_CYCLE = ["up", "right", "space", "down", "left"]

SEEDS = [1, 7, 12345, 2 ** 31]
TICKS = 60

passed = failed = 0


def check(label, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print("  ok   %s" % label)
    else:
        failed += 1
        print("  FAIL %s" % label)
        if detail:
            for line in str(detail).splitlines():
                print("       " + line)


def snapshot(world):
    """Exactly the shape tests/engine_trace.js prints."""
    return {
        "tick": world.tick,
        "score": world.score,
        "status": world.status,
        "message": world.message,
        "memory": world.memory,
        "things": [[t.kind, t.x, t.y, t.health, t.glyph, t.color,
                    t.facing[0], t.facing[1], t.age, t.travelled,
                    1 if t.solid else 0]
                   for t in world.things],
    }


def python_trace(project, seed, ticks):
    world = World(project, seed=seed)
    lines = [snapshot(world)]
    for _ in range(ticks):
        world.keys = {KEY_CYCLE[world.tick % len(KEY_CYCLE)]}
        world.step()
        lines.append(snapshot(world))
    return lines


def js_trace(game, seed, ticks):
    out = subprocess.run(
        ["node", str(ROOT / "tests" / "engine_trace.js"), game,
         str(seed), str(ticks)],
        capture_output=True, text=True, cwd=str(ROOT))
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or "node failed")
    return [json.loads(line) for line in out.stdout.splitlines() if line.strip()]


def first_difference(a, b):
    """Where the two traces part company, in words."""
    for i, (left, right) in enumerate(zip(a, b)):
        if left == right:
            continue
        for key in ("tick", "score", "status", "message", "memory"):
            if left.get(key) != right.get(key):
                return "tick %d: %s  python=%r  js=%r" % (
                    i, key, left.get(key), right.get(key))
        lt, rt = left["things"], right["things"]
        if len(lt) != len(rt):
            return "tick %d: %d characters in python, %d in js" % (i, len(lt), len(rt))
        for j, (lthing, rthing) in enumerate(zip(lt, rt)):
            if lthing != rthing:
                return "tick %d, character %d:\n  python=%r\n  js=%r" % (
                    i, j, lthing, rthing)
        return "tick %d differs" % i
    if len(a) != len(b):
        return "python gave %d ticks, js gave %d" % (len(a), len(b))
    return "no difference found"


def main():
    print("the two engines play the same games\n")

    if shutil.which("node") is None:
        print("  node is not installed, so the JavaScript engine cannot be run.")
        print("  In Termux:  pkg install nodejs")
        return 2

    games = [p for p in sorted(brain.GAMES_DIR.glob("*.json")) if p.stem != "index"]
    if not games:
        print("  no games to test with")
        return 1

    for game in games:
        rel = game.relative_to(ROOT).as_posix()
        project = brain.load(game)
        for seed in SEEDS:
            label = "%s, seed %d" % (game.stem, seed)
            try:
                mine = python_trace(project, seed, TICKS)
                theirs = js_trace(rel, seed, TICKS)
            except Exception as err:                    # noqa: BLE001
                check(label, False, err)
                continue
            check(label, mine == theirs,
                  "" if mine == theirs else first_difference(mine, theirs))

    print("\nthe seeded dice are the same dice")
    from engine.rng import Rng
    rolls = [Rng(7).randrange(1000) for _ in range(2)]
    check("a seed replays exactly", rolls[0] == rolls[1])
    check("no seed is still real randomness",
          Rng(None).seeded is False)

    print("\n%d passed, %d failed" % (passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
