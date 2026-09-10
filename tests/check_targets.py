#!/usr/bin/env python3
"""Check mark_target/recall_target -- a named slot that holds the actual
character (or a plain spot on the map) instead of a placeholder's frozen
numbers, so "toward it" keeps following a moving thing tick after tick.

    python3 tests/check_targets.py

Deliberately not wired into tests/check_engines.py's own snapshot/parity
harness, for the same reason check_lead.py gives (a real, gameplay-
affecting field, but extending that shared comparison shape is its own
riskier change). This file and its JS twin, tests/targets.test.js, check
each engine's own implementation directly against the same cases.

The `move` tile itself is untouched -- recall_target just needs to hand
the saved Thing back as `it`, and "move toward it" (already there,
already used by `see`/`touch`-driven chasing) does the rest. So the case
worth the most attention here isn't movement, it's what gets saved: an
object/character (a live reference, kept live even as it moves or dies)
versus a location (a frozen snapshot, since there was no `it` to save).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.world import World                                # noqa: E402

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


def game(hero_rows, width=9, height=9, extra_characters=None):
    return {
        "name": "targets_probe",
        "world": {"width": width, "height": height, "speed": 6},
        "characters": [
            {"kind": "hero", "glyph": "@", "color": "green", "role": "player",
             "count": 0, "brain": hero_rows},
            {"kind": "bandit", "glyph": "x", "color": "red", "role": "prop",
             "count": 0, "brain": []},
        ] + (extra_characters or []),
    }


def hero(world):
    return next(t for t in world.things if t.kind == "hero")


def bandit(world):
    return next(t for t in world.things if t.kind == "bandit")


ALWAYS = [{"tile": "always", "args": {}}]
SEE_BANDIT = [{"tile": "see", "args": {"kind": "bandit", "range": 10}}]
MARK_ENEMY = [{"tile": "mark_target", "args": {"name": "enemy"}}]
RECALL_ENEMY = [{"tile": "recall_target", "args": {"name": "enemy"}}]
MOVE_TOWARD_IT = [{"tile": "move", "args": {"dir": "toward it"}}]

print("mark_target: with an `it`, saves the actual character -- a live reference")

world = World(game([{"when": SEE_BANDIT, "do": MARK_ENEMY}]))
world.spawn("hero", 1, 1)
b = world.spawn("bandit", 5, 1)
world.step()
check("the bandit itself is what got saved, not a copy",
      world.targets.get("enemy") is b, world.targets.get("enemy"))

print("\nrecall_target: hands the saved character back as `it`, so \"toward it\" chases it live")

world = World(game([
    {"when": SEE_BANDIT, "do": MARK_ENEMY},
    {"when": RECALL_ENEMY, "do": MOVE_TOWARD_IT},
]))
world.spawn("hero", 1, 1)
world.spawn("bandit", 5, 1)
world.step()
check("marked this tick, and already took a step toward it in the very same tick",
      hero(world).x == 2, hero(world).x)
bandit(world).x = 8   # the bandit itself moved -- a placeholder's frozen vector couldn't follow this
world.step()
check("recall_target still points at the SAME (now-moved) bandit -- keeps following it",
      hero(world).x == 3, hero(world).x)

print("\na name never marked reads False, not a crash")

world = World(game([{"when": RECALL_ENEMY, "do": MOVE_TOWARD_IT}]))
h = world.spawn("hero", 1, 1)
before = (h.x, h.y)
world.step()
check("nothing marked yet -- no movement, no error", (h.x, h.y) == before, (h.x, h.y))

print("\na dead target is the same as never having marked one -- no chasing a corpse")

world = World(game([
    {"when": SEE_BANDIT, "do": MARK_ENEMY},
    {"when": RECALL_ENEMY, "do": MOVE_TOWARD_IT},
]))
world.spawn("hero", 1, 1)
world.spawn("bandit", 5, 1)
world.step()   # marks and takes a first step
world.remove(bandit(world))
before = hero(world).x
world.step()
check("the reference is still in world.targets (nothing clears it on death)...",
      world.targets.get("enemy") is not None)
check("...but recall_target reads False once it's dead, so no more chasing",
      hero(world).x == before, (before, hero(world).x))

print("\nmark_target: with no `it` at all, saves my OWN spot as a frozen location")

world = World(game([{"when": ALWAYS, "do": [{"tile": "mark_target", "args": {"name": "spot"}}]}]))
world.spawn("hero", 4, 6)
world.step()
spot = world.targets.get("spot")
check("something got saved", spot is not None)
check("it sits at the hero's own square", (spot.x, spot.y) == (4, 6), (spot.x, spot.y))
check("the marker is never added to the world -- doesn't render, tick, or collide",
      spot not in world.things, [id(t) for t in world.things])

print("\na marked location stays put even after I walk away -- a real frozen snapshot")

world = World(game([
    {"when": [{"tile": "key", "args": {"key": "m"}}], "do": [{"tile": "mark_target", "args": {"name": "home"}}]},
    {"when": [{"tile": "key", "args": {"key": "r"}}, {"tile": "recall_target", "args": {"name": "home"}}],
     "do": MOVE_TOWARD_IT},
]))
h = world.spawn("hero", 2, 2)
world.keys = {"m"}
world.step()
world.keys = set()
h.x, h.y = 6, 6   # walked far away
world.keys = {"r"}
world.step()
check("moved one step back toward the frozen (2, 2) mark, not toward wherever I am now",
      (h.x, h.y) == (5, 6), (h.x, h.y))

print("\nan empty name is refused, same as remember's own")

world = World(game([{"when": ALWAYS, "do": [{"tile": "mark_target", "args": {"name": "  "}}]}]))
world.spawn("hero", 1, 1)
world.step()
check("nothing gets saved under a blank name", world.targets == {}, world.targets)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
