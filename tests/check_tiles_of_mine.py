#!/usr/bin/env python3
"""Check your own named tiles -- a whole row folded up under a name.

    python3 tests/check_tiles_of_mine.py

A named tile keeps both halves of the row it came from, so the same one is
checked when it sits in the WHEN half and run when it sits in the DO half. That
is the thing worth testing: that it composes exactly like the tiles it is made
of, including handing "it" through, and that the ways it can be malformed --
naming a tile nobody defined, or a tile that contains itself -- leave the game
running instead of breaking it.

Nothing here touches the disk. Each case builds a tiny world and steps it.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import builder, tiles                            # noqa: E402
from engine.world import World                               # noqa: E402

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


def game(brain, mine=None, extra=None):
    chars = [{"kind": "hero", "glyph": "@", "color": "cyan", "health": 3,
              "count": 1, "solid": False, "role": "player", "brain": brain}]
    chars += extra or []
    return {"name": "mine_probe", "tiles": mine or [],
            "world": {"width": 11, "height": 5, "wrap": False, "speed": 6},
            "characters": chars}


USE = {"tile": "combo", "args": {"name": "thing"}}


def run(brain, mine=None, ticks=1, extra=None, seed=5):
    world = World(game(brain, mine, extra), seed=seed)
    for _ in range(ticks):
        world.step()
    return world


# -- both halves live in the one tile ---------------------------------------

print("one named tile, two halves\n")

mine = [{"name": "thing",
         "when": [{"tile": "always", "args": {}}],
         "do": [{"tile": "say", "args": {"text": "ran"}}]}]

world = run([{"when": [USE], "do": [USE]}], mine)
check("it fires in the WHEN half and runs in the DO half",
      world.message == "ran", world.message)

world = run([{"when": [USE], "do": [{"tile": "score", "args": {"amount": 5}}]}],
            mine)
check("used only in the WHEN half, its actions do not run",
      world.score == 5 and world.message == "", (world.score, world.message))

world = run([{"when": [{"tile": "always", "args": {}}], "do": [USE]}], mine)
check("used only in the DO half, its sensors are not consulted",
      world.message == "ran", world.message)

# a named tile whose WHEN half is false stops the row it sits in
never = [{"name": "thing",
          "when": [{"tile": "health_below", "args": {"value": 0}}],
          "do": [{"tile": "say", "args": {"text": "ran"}}]}]
world = run([{"when": [USE], "do": [{"tile": "score", "args": {"amount": 5}}]}],
            never)
check("a named tile that does not pass stops its row",
      world.score == 0, world.score)

# -- an empty half ----------------------------------------------------------

print("\nhalves that are empty")

half = [{"name": "thing", "when": [],
         "do": [{"tile": "say", "args": {"text": "ran"}}]}]
world = run([{"when": [USE], "do": [{"tile": "score", "args": {"amount": 1}}]}],
            half)
check("an empty WHEN half passes, as an empty row's does",
      world.score == 1, world.score)

half = [{"name": "thing",
         "when": [{"tile": "always", "args": {}}], "do": []}]
world = run([{"when": [{"tile": "always", "args": {}}], "do": [USE]}], half)
check("an empty DO half does nothing at all, quietly",
      world.message == "", world.message)

# -- "it" passes through ----------------------------------------------------

print("\nthe word \"it\" reaches inside")

apple = [{"kind": "apple", "glyph": "o", "color": "green", "health": 1,
          "count": 1, "solid": False, "role": "prop", "brain": []}]

seek = [{"name": "thing",
         "when": [{"tile": "see", "args": {"kind": "apple", "range": 9}}],
         "do": [{"tile": "move", "args": {"dir": "toward it"}}]}]
world = World(game([{"when": [USE], "do": [USE]}], seek, apple), seed=5)
hero = [t for t in world.things if t.kind == "hero"][0]
target = [t for t in world.things if t.kind == "apple"][0]
hero.x, hero.y = 0, 0
target.x, target.y = 6, 0
for _ in range(8):
    world.step()
check("a sensor inside it finds a character, and an action inside it moves to "
      "that character", hero.x == 6, (hero.x, target.x))

# a named tile in the DO half is handed whoever the ROW's WHEN half found
hit = [{"name": "thing", "when": [],
        "do": [{"tile": "vanish", "args": {"target": "it"}}]}]
world = World(game([{"when": [{"tile": "see", "args": {"kind": "apple",
                                                      "range": 9}}],
                     "do": [USE]}], hit, apple), seed=5)
world.step()
check("the row's \"it\" is handed through into the named tile",
      not [t for t in world.things if t.kind == "apple"],
      [t.kind for t in world.things])

# -- names that do not resolve ----------------------------------------------

print("\nnames nobody has defined")

world = run([{"when": [USE], "do": [{"tile": "win", "args": {}}]}], [])
check("an unknown name in the WHEN half simply does not fire",
      world.status is None, world.status)

world = run([{"when": [{"tile": "always", "args": {}}],
              "do": [USE, {"tile": "score", "args": {"amount": 3}}]}], [])
check("an unknown name in the DO half is skipped, and the rest of the row runs",
      world.score == 3, world.score)

blank = [{"name": "  ", "when": [], "do": []}]
world = World(game([], blank))
check("a tile with a blank name is not registered at all",
      world.combos == {}, world.combos)

# -- a tile that contains itself --------------------------------------------

print("\na named tile that contains itself")

loop = [{"name": "thing",
         "when": [{"tile": "combo", "args": {"name": "thing"}}],
         "do": [{"tile": "combo", "args": {"name": "thing"}},
                {"tile": "score", "args": {"amount": 1}}]}]
world = run([{"when": [{"tile": "always", "args": {}}], "do": [USE]}], loop,
            ticks=3)
check("it stops rather than spinning for ever", True)
check("the depth counter is back to nothing afterwards",
      world.combo_depth == 0, world.combo_depth)
check("it ran a bounded number of times, not none and not for ever",
      0 < world.score <= 3 * tiles.MAX_COMBO_DEPTH, world.score)

# two tiles that contain each other
pair = [{"name": "thing", "when": [], "do": [{"tile": "combo",
                                              "args": {"name": "other"}}]},
        {"name": "other", "when": [], "do": [{"tile": "combo",
                                              "args": {"name": "thing"}}]}]
world = run([{"when": [{"tile": "always", "args": {}}], "do": [USE]}], pair,
            ticks=2)
check("two tiles containing each other also stop",
      world.combo_depth == 0, world.combo_depth)

# -- one tile inside another, which is the point of them --------------------

print("\none named tile inside another")

nest = [{"name": "inner", "when": [{"tile": "always", "args": {}}],
         "do": [{"tile": "score", "args": {"amount": 2}}]},
        {"name": "thing", "when": [{"tile": "combo", "args": {"name": "inner"}}],
         "do": [{"tile": "combo", "args": {"name": "inner"}}]}]
world = run([{"when": [USE], "do": [USE]}], nest)
check("a named tile may hold another one", world.score == 2, world.score)

# -- folding, as the editors do it ------------------------------------------

print("\nfolding a row, the way both editors do")

project = game([{"when": [{"tile": "always", "args": {}}],
                 "do": [{"tile": "say", "args": {"text": "ran"}}]}])
rows = project["characters"][0]["brain"]
before = World(project, seed=5)
before.step()
was = before.message

builder.forget_history()
made = {"name": "folded",
        "when": [dict(t) for t in rows[0]["when"]],
        "do": [dict(t) for t in rows[0]["do"]]}
builder.my_tiles(project).append(made)
rows[0] = {"when": [{"tile": "combo", "args": {"name": "folded"}}],
           "do": [{"tile": "combo", "args": {"name": "folded"}}]}

after = World(project, seed=5)
after.step()
check("a folded row does exactly what it did before", after.message == was,
      (was, after.message))
check("the game now carries one tile of its own",
      len(project["tiles"]) == 1, project["tiles"])

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
