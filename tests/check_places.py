#!/usr/bin/env python3
"""Check placeholders: the three faces, the sums, and the fences round them.

    python3 tests/check_places.py

A placeholder is the one piece of Spark that does arithmetic, which makes it
the one piece with edges worth pinning down: what an empty box means, what an
unwritten placeholder reads as, what dividing by nothing does, and what happens
when a sum runs off the end of the numbers. Every one of those answers is also
written into world3d.html by hand, so getting them wrong here means the two
engines disagree -- tests/check_engines.py is the other half of this test.

Nothing here touches the disk or the network. Each case builds a one-character
world, runs it for a tick or two, and reads the slots back.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import tiles                                     # noqa: E402
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


def game(rows, width=9, height=5):
    return {"name": "place_probe",
            "world": {"width": width, "height": height, "speed": 6},
            "characters": [{"kind": "hero", "glyph": "@", "color": "green",
                            "role": "player", "count": 1, "brain": rows}]}


ALWAYS = [{"tile": "always", "args": {}}]


def run(do, ticks=1, when=None, **world_args):
    """One character, one row, so many ticks. Returns the finished world."""
    world = World(game([{"when": when or ALWAYS, "do": do}], **world_args))
    for _ in range(ticks):
        world.step()
    return world


def value(who, a, op="plus", b="0"):
    return {"tile": "place_value", "args": {"who": who, "a": a, "op": op, "b": b}}


def vector(who, axis, a, op="plus", b="0"):
    return {"tile": "place_vector",
            "args": {"who": who, "axis": axis, "a": a, "op": op, "b": b}}


def slot(world, who):
    return world.places.get(who, {})


# -- the three faces --------------------------------------------------------

print("one placeholder, regarded three ways\n")

world = run([{"tile": "place_name", "args": {"who": "thing", "text": "hero"}},
             value("thing", "40", "plus", "2"),
             vector("thing", "x", "1"), vector("thing", "y", "2"),
             vector("thing", "z", "3")])
spot = slot(world, "thing")
check("the name face holds text", spot.get("name") == "hero", spot)
check("the value face holds a number", spot.get("value") == 42, spot)
check("the vector face holds x, y and z",
      (spot.get("x"), spot.get("y"), spot.get("z")) == (1, 2, 3), spot)
check("all three faces belong to the one slot", len(world.places) == 1,
      list(world.places))

# -- what an untouched placeholder is ---------------------------------------

print("\nnothing has to be filled in first")

world = run([value("counter", "counter", "plus", "1")])
check("an unwritten value reads as 0, so counting starts at 1",
      slot(world, "counter").get("value") == 1, world.places)

world = run([{"tile": "say", "args": {"text": "x"}}],
            when=[{"tile": "place_has",
                   "args": {"who": "nobody", "face": "value",
                            "test": "exactly", "amount": 0}}])
check("an unwritten placeholder answers a WHEN tile as 0",
      world.message == "x", world.message)
check("...and reading it did not create it", "nobody" not in world.places,
      list(world.places))

world = run([value("thing", "ghost", "plus", "ghost")])
check("a name nobody has written is 0 inside a sum",
      slot(world, "thing").get("value") == 0, world.places)

# -- names ------------------------------------------------------------------

print("\nnaming a placeholder")

world = run([value("Home", "5"), value("HOME", "home", "plus", "1")])
check("a placeholder's name ignores capitals and spare space",
      list(world.places) == ["home"] and slot(world, "home")["value"] == 6,
      world.places)

world = run([value("  ", "5"), {"tile": "place_name",
                                "args": {"who": "", "text": "x"}}])
check("a blank placeholder name writes nothing at all",
      world.places == {}, world.places)

# -- the sums ---------------------------------------------------------------

print("\nthe sum in the right-hand half")

cases = [
    ("plus", "7", "5", 12),
    ("minus", "7", "5", 2),
    ("minus", "5", "7", -2),
    ("times", "7", "5", 35),
    ("times", "-3", "5", -15),
    ("divided by", "7", "5", 1),
    ("divided by", "-7", "5", -1),        # cut toward zero, both engines alike
    ("divided by", "7", "0", 0),          # nothing sensible, so zero
    ("plus", "2.9", "0", 2),              # the fraction is dropped
    ("plus", "-2.9", "0", -2),
    ("plus", "", "3", 3),                 # an empty box is nothing
    ("plus", "banana", "3", 3),           # so is a word that means nothing
]
for op, a, b, want in cases:
    world = run([value("thing", a, op, b)])
    got = slot(world, "thing").get("value")
    check("%-11s %-8s %-4s = %d" % (op, repr(a), repr(b), want), got == want, got)

world = run([value("thing", "1000000001", "plus", "0")])
check("a number past the fence is held at the fence",
      slot(world, "thing").get("value") == tiles.LIMIT, world.places)
world = run([value("thing", "1000000000", "times", "1000000000")])
check("a sum that runs off the end is held there too",
      slot(world, "thing").get("value") == tiles.LIMIT, world.places)
world = run([value("thing", "0", "minus", "999999999999")])
check("and the same at the bottom end",
      slot(world, "thing").get("value") == -tiles.LIMIT, world.places)

world = run([value("thing", "0x10", "plus", "0")])
check("hexadecimal is not a number here (JavaScript would say 16)",
      slot(world, "thing").get("value") == 0, world.places)
world = run([value("thing", "1_0", "plus", "0")])
check("nor is 1_0 (Python would say ten)",
      slot(world, "thing").get("value") == 0, world.places)

# -- the words a box may hold -----------------------------------------------

print("\nthe words a box of a sum understands")

world = run([value("thing", "my x", "plus", "my y")])
hero = world.things[0]
check("my x and my y are where I stand",
      slot(world, "thing").get("value") == hero.x + hero.y,
      (world.places, hero.x, hero.y))

world = run([{"tile": "score", "args": {"amount": 3}},
             value("thing", "score", "plus", "tick")])
check("score and tick are about the world",
      slot(world, "thing").get("value") == 3 + world.tick, world.places)

world = run([value("thing", "my health", "times", "2")])
check("my health is readable too",
      slot(world, "thing").get("value") == world.things[0].health * 2,
      world.places)

world = run([vector("home", "x", "4"), value("thing", "home x", "plus", "1")])
check("a name with x after it reads one axis of a vector",
      slot(world, "thing").get("value") == 5, world.places)

world = run([value("home", "4"), value("thing", "home", "plus", "1")])
check("a name on its own reads the value face",
      slot(world, "thing").get("value") == 5, world.places)

world = run([value("thing", "it x", "plus", "it health")])
check("it is 0 when the WHEN half found nobody, rather than breaking",
      slot(world, "thing").get("value") == 0, world.places)

# -- the WHEN tiles ---------------------------------------------------------

print("\nasking about a placeholder")

for test, amount, want in (("at least", 5, True), ("at least", 6, False),
                           ("at most", 5, True), ("at most", 4, False),
                           ("exactly", 5, True), ("exactly", 4, False)):
    world = World(game([
        {"when": ALWAYS, "do": [value("thing", "5")]},
        {"when": [{"tile": "place_has",
                   "args": {"who": "thing", "face": "value",
                            "test": test, "amount": amount}}],
         "do": [{"tile": "say", "args": {"text": "yes"}}]},
    ]))
    world.step()
    check("value 5 %s %d -> %s" % (test, amount, want),
          (world.message == "yes") == want, world.message)

world = World(game([
    {"when": ALWAYS, "do": [vector("thing", "y", "9")]},
    {"when": [{"tile": "place_has",
               "args": {"who": "thing", "face": "y",
                        "test": "at least", "amount": 9}}],
     "do": [{"tile": "say", "args": {"text": "yes"}}]},
]))
world.step()
check("a WHEN tile can ask about one axis", world.message == "yes",
      world.message)

world = World(game([
    {"when": ALWAYS,
     "do": [{"tile": "place_name", "args": {"who": "target", "text": "apple"}}]},
    {"when": [{"tile": "place_named", "args": {"who": "target", "text": "apple"}}],
     "do": [{"tile": "say", "args": {"text": "yes"}}]},
]))
world.step()
check("a WHEN tile can ask what a placeholder is named",
      world.message == "yes", world.message)

world = World(game([
    {"when": [{"tile": "place_named",
               "args": {"who": "target", "text": "apple"}}],
     "do": [{"tile": "say", "args": {"text": "yes"}}]},
]))
world.step()
check("an unnamed placeholder is not named anything",
      world.message == "", world.message)

# -- vectors that move something --------------------------------------------

print("\nvectors that do something")

world = World(game([
    {"when": ALWAYS, "do": [{"tile": "place_here", "args": {"who": "home"}}]},
]))
world.step()
hero = world.things[0]
check("copying my place writes x and y",
      (slot(world, "home")["x"], slot(world, "home")["y"]) == (hero.x, hero.y),
      world.places)
check("...and leaves z alone", slot(world, "home")["z"] == 0, world.places)

world = World(game([
    {"when": ALWAYS, "do": [vector("step", "x", "1"), vector("step", "y", "0"),
                            {"tile": "place_move", "args": {"who": "step"}}]},
]), )
before = world.things[0].x
world.step()
check("moving by a vector takes that step",
      world.things[0].x == before + 1, (before, world.things[0].x))

world = World(game([
    {"when": ALWAYS, "do": [vector("far", "x", "500"), vector("far", "y", "500"),
                            {"tile": "place_jump", "args": {"who": "far"}}]},
]))
at = (world.things[0].x, world.things[0].y)
world.step()
check("jumping off the board does nothing rather than pinning me to the rim",
      (world.things[0].x, world.things[0].y) == at, world.places)

world = World(game([
    {"when": ALWAYS, "do": [vector("spot", "x", "2"), vector("spot", "y", "3"),
                            {"tile": "place_jump", "args": {"who": "spot"}}]},
]))
world.step()
check("jumping to a square on the board lands there",
      (world.things[0].x, world.things[0].y) == (2, 3),
      (world.things[0].x, world.things[0].y))

world = World(game([
    {"when": ALWAYS, "do": [{"tile": "place_jump", "args": {"who": "never"}},
                            {"tile": "place_move", "args": {"who": "never"}}]},
]))
at = (world.things[0].x, world.things[0].y)
world.step()
check("jumping or moving by a placeholder nobody wrote does nothing",
      (world.things[0].x, world.things[0].y) == at and world.places == {},
      world.places)

# -- placeholders are shared, and start empty -------------------------------

print("\nwhere placeholders live")

world = World(game([{"when": ALWAYS, "do": [value("thing", "1")]}]))
check("a new world has no placeholders at all", world.places == {}, world.places)
world.step()
check("...until a row writes one", list(world.places) == ["thing"], world.places)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
