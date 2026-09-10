#!/usr/bin/env python3
"""Check lead/dismiss/has_leader -- the tiles behind "touch a companion to
recruit it, it follows you, dismiss it to let it go."

    python3 tests/check_lead.py

Deliberately not wired into tests/check_engines.py's own snapshot/parity
harness, for the same reason check_harvest.py gives (a real,
gameplay-affecting field, but extending that shared comparison shape is
its own riskier change). This file and its JS twin, tests/lead.test.js,
check each engine's own implementation directly against the same cases.

The move tile itself is untouched -- has_leader just needs to hand the
leader back as `it`, and "move toward it" (already there, already used
by `see`/`touch`-driven chasing) does the rest. So the case worth the
most attention here isn't movement, it's the *targeting*: who becomes
whose leader when `lead`/`dismiss` run with target "it" vs "self".
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


def game(hero_rows, companion_rows=None, width=9, height=9, extra_characters=None):
    """Every character starts at count 0 -- every test spawns them itself,
    at exact positions, with world.spawn(). Random placement (the normal
    "count: N" startup path) would make every adjacency/direction check
    below flaky by design."""
    return {
        "name": "lead_probe",
        "world": {"width": width, "height": height, "speed": 6},
        "characters": [
            {"kind": "hero", "glyph": "@", "color": "green", "role": "player",
             "count": 0, "brain": hero_rows},
            {"kind": "companion", "glyph": "c", "color": "yellow", "role": "prop",
             "count": 0, "brain": companion_rows or []},
        ] + (extra_characters or []),
    }


def hero(world):
    return next(t for t in world.things if t.kind == "hero")


def companion(world):
    return next(t for t in world.things if t.kind == "companion")


ALWAYS = [{"tile": "always", "args": {}}]
TOUCH_COMPANION = [{"tile": "touch", "args": {"kind": "companion"}}]
LEAD_IT = [{"tile": "lead", "args": {"target": "it"}}]
DISMISS_IT = [{"tile": "dismiss", "args": {"target": "it"}}]
CHASE_LEADER = [{"when": [{"tile": "has_leader", "args": {}}],
                 "do": [{"tile": "move", "args": {"dir": "toward it"}}]}]

print("lead: touching a companion makes it follow whoever touched it, not the other way")

world = World(game([{"when": TOUCH_COMPANION, "do": LEAD_IT}]))
world.spawn("hero", 5, 5)
world.spawn("companion", 5, 4)   # adjacent -- touch fires this tick
world.step()
check("the companion's leader becomes the hero", companion(world).leader is hero(world),
      companion(world).leader)
check("the hero itself gets no leader -- lead never runs on the recruiter",
      hero(world).leader is None)

print("\nhas_leader: hands the leader back as `it`, so the ordinary move tile can chase it")

world = World(game([{"when": TOUCH_COMPANION, "do": LEAD_IT}], CHASE_LEADER))
world.spawn("hero", 5, 5)
world.spawn("companion", 5, 2)   # 3 apart -- not touching, no recruiting yet
world.step()
check("not adjacent -- no leader assigned, no movement",
      companion(world).leader is None and companion(world).y == 2,
      (companion(world).leader, companion(world).y))

world = World(game([{"when": TOUCH_COMPANION, "do": LEAD_IT}], CHASE_LEADER))
world.spawn("hero", 5, 5)
world.spawn("companion", 5, 4)   # adjacent -- recruits this tick
world.step()
# Things are processed in spawn order (hero, then companion), so the
# companion's own has_leader row sees the leader hero's row just set,
# same tick -- recruiting and the first step of chasing both land here.
check("adjacent -- recruited the same tick", companion(world).leader is hero(world))
check("...and immediately takes its first step toward its new leader",
      companion(world).y == 5, companion(world).y)

print("\ndismiss: lets a companion go, and it stops chasing")

world = World(game([{"when": TOUCH_COMPANION, "do": LEAD_IT}], CHASE_LEADER))
world.spawn("hero", 5, 5)
world.spawn("companion", 5, 4)
world.step()   # recruits
check("recruited first", companion(world).leader is not None)
hero(world).brain = [{"when": TOUCH_COMPANION, "do": DISMISS_IT}]
world.step()
check("dismissing (still touching) clears the leader",
      companion(world).leader is None, companion(world).leader)

print("\na dead leader is the same as never having had one -- no chasing a corpse")

world = World(game([{"when": TOUCH_COMPANION, "do": LEAD_IT}], CHASE_LEADER))
world.spawn("hero", 5, 5)
world.spawn("companion", 5, 4)
world.step()
check("recruited", companion(world).leader is not None)
world.remove(hero(world))
before_y = companion(world).y
world.step()
check("the leader reference is still there (nothing clears it on death)...",
      companion(world).leader is not None)
check("...but has_leader reads false once it's dead, so no more chasing",
      companion(world).y == before_y, (before_y, companion(world).y))

print("\ntarget \"self\": a companion can dismiss (or lead) itself, not just whoever it touches")

world = World(game(
    [{"when": TOUCH_COMPANION, "do": LEAD_IT}],
    [{"when": [{"tile": "health_below", "args": {"value": 999}}],
      "do": [{"tile": "dismiss", "args": {"target": "self"}}]}],
))
world.spawn("hero", 5, 5)
world.spawn("companion", 5, 4)
world.step()
check("recruited, then dismisses itself in the very same tick's companion rules",
      companion(world).leader is None, companion(world).leader)

print("\nrecruit: \"buy a unit\" -- spawns at MY spot, already following me")

WORKER_TEMPLATE = {"kind": "worker", "glyph": "w", "color": "yellow",
                    "role": "prop", "count": 0, "brain": []}
RECRUIT_WORKER = [{"tile": "recruit", "args": {"kind": "worker"}}]

world = World(game([{"when": ALWAYS, "do": RECRUIT_WORKER}],
                    extra_characters=[WORKER_TEMPLATE]))
world.spawn("hero", 5, 5)
before = len(world.things)
world.step()
check("a fresh worker actually appears", len(world.things) == before + 1,
      [t.kind for t in world.things])
new_worker = next(t for t in world.things if t.kind == "worker")
check("it spawns at the recruiter's own spot, not a random empty cell",
      (new_worker.x, new_worker.y) == (5, 5), (new_worker.x, new_worker.y))
check("...and already follows whoever recruited it -- no separate lead needed",
      new_worker.leader is hero(world), new_worker.leader)

print("\nrecruit is exactly the right hook for a real \"pay ore for a unit\" row")

world = World(game(
    [{"when": [{"tile": "has_item", "args": {"item": "ore", "amount": 5}}],
      "do": [{"tile": "give_item", "args": {"target": "self", "item": "ore", "amount": -5}}]
            + RECRUIT_WORKER}],
    extra_characters=[WORKER_TEMPLATE],
))
h = world.spawn("hero", 5, 5)
h.inventory["ore"] = 3
world.step()
check("can't afford it yet -- no worker, ore untouched",
      not any(t.kind == "worker" for t in world.things) and h.inventory["ore"] == 3,
      h.inventory)
h.inventory["ore"] = 5
world.step()
check("affordable now -- hired, and the cost is actually deducted",
      any(t.kind == "worker" for t in world.things) and h.inventory["ore"] == 0,
      (h.inventory, [t.kind for t in world.things]))

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
