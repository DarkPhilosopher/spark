#!/usr/bin/env python3
"""Check give_item/has_item/harvestable -- the tiles behind "walk up, pick
it from a list, wait a few seconds, get an item" (see world3d.html's own
Harvest section, which runs the actual wait/flash/give sequence; these
three tiles are only the data half, usable from any brain in either
engine).

    python3 tests/check_harvest.py

Deliberately not wired into tests/check_engines.py's own snapshot/parity
harness (which compares a fixed, hand-picked set of Thing fields between
the two engines) -- inventory/harvest are real, gameplay-affecting fields,
but extending that shared comparison shape is its own, riskier change to
a delicate piece of test infrastructure both engines already lean on.
This file and its JS twin, tests/harvest_tiles.test.js, check each
engine's own implementation directly against the same cases instead --
not the same mechanism as check_engines.py, but the same goal: neither
engine quietly drifting from what the other one does.
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


ALWAYS = [{"tile": "always", "args": {}}]


def game(rows, extra_characters=None, width=9, height=5):
    chars = [{"kind": "hero", "glyph": "@", "color": "green",
              "role": "player", "count": 1, "brain": rows}]
    chars.extend(extra_characters or [])
    return {"name": "harvest_probe",
            "world": {"width": width, "height": height, "speed": 6},
            "characters": chars}


def run(do, ticks=1, when=None, **kwargs):
    world = World(game([{"when": when or ALWAYS, "do": do}], **kwargs))
    for _ in range(ticks):
        world.step()
    return world


def give(target, item, amount):
    return {"tile": "give_item",
            "args": {"target": target, "item": item, "amount": amount}}


def hero(world):
    return next(t for t in world.things if t.role == "player")


print("give_item: builds up, and can take away, a Thing's own count\n")

w = run([give("self", "gold", 3)])
check("a fresh item starts from zero and counts up", hero(w).inventory.get("gold") == 3,
      hero(w).inventory)

w = run([give("self", "gold", 3), give("self", "gold", 4)])
check("giving the same item again adds to what's already there",
      hero(w).inventory.get("gold") == 7, hero(w).inventory)

w = run([give("self", "gold", 5), give("self", "gold", -2)])
check("a negative amount takes some away", hero(w).inventory.get("gold") == 3,
      hero(w).inventory)

w = run([give("self", "gold", 2), give("self", "gold", -99)])
check("taking away more than there is stops at zero, not negative",
      hero(w).inventory.get("gold") == 0, hero(w).inventory)

w = run([give("self", "gold", 3), give("self", "silver", 1)])
h = hero(w)
check("different items keep their own separate counts",
      h.inventory.get("gold") == 3 and h.inventory.get("silver") == 1, h.inventory)

w = run([give("self", "  ", 5)])
check("a blank item name gives nothing, doesn't crash", hero(w).inventory == {},
      hero(w).inventory)

print("\nhas_item: reads a Thing's own count, never world memory\n")

w = run([{"tile": "score", "args": {"amount": 0}}])   # a no-op row, nothing given
check("an item nobody's ever been given at all reads as zero, not missing",
      hero(w).inventory.get("gold", 0) == 0)

world = World(game([
    {"when": ALWAYS, "do": [give("self", "gold", 5)]},
    {"when": [{"tile": "has_item", "args": {"item": "gold", "amount": 5}}],
     "do": [{"tile": "say", "args": {"text": "rich enough"}}]},
]))
world.step()
check("has_item sees a count given the very same tick it was given",
      world.message == "rich enough", world.message)

world = World(game([
    {"when": ALWAYS, "do": [give("self", "gold", 4)]},
    {"when": [{"tile": "has_item", "args": {"item": "gold", "amount": 5}}],
     "do": [{"tile": "say", "args": {"text": "rich enough"}}]},
]))
world.step()
check("has_item with too few of the item stays false",
      world.message != "rich enough", world.message)

# Two characters: give_item(it, ...) after a touch establishes "it", the
# same shape a real "pick it up" row would actually take.
world = World(game([
    {"when": [{"tile": "touch", "args": {"kind": "chest"}}],
     "do": [give("it", "gold", 10)]},
], extra_characters=[
    {"kind": "chest", "glyph": "c", "color": "yellow", "solid": False,
     "count": 1, "brain": []},
], width=3, height=3))
# hero and chest start at different empty cells picked by World.spawn --
# force them adjacent so touch (range 1) actually fires.
h = next(t for t in world.things if t.kind == "hero")
c = next(t for t in world.things if t.kind == "chest")
h.x, h.y = 1, 1
c.x, c.y = 1, 1
world.step()
check("give_item(it, ...) gives to the touched object, not the toucher",
      c.inventory.get("gold") == 10 and h.inventory.get("gold", 0) == 0,
      (h.inventory, c.inventory))

print("\nharvestable: stamps config onto a Thing, nothing more\n")

world = World(game([
    {"when": ALWAYS, "do": [{"tile": "harvestable",
                              "args": {"target": "self", "item": "wood",
                                       "amount": 2, "seconds": 3, "flashes": 5}}]},
]))
world.step()
h = hero(world)
check("harvest config lands exactly as given",
      h.harvest == {"item": "wood", "amount": 2, "seconds": 3, "flashes": 5}, h.harvest)

world = World(game([
    {"when": ALWAYS, "do": [{"tile": "harvestable", "args": {
        "target": "self", "item": "wood", "amount": 0, "seconds": 0, "flashes": 0}}]},
]))
world.step()
h = hero(world)
check("amount/seconds/flashes can never be stamped as zero or negative -- floored at 1",
      h.harvest == {"item": "wood", "amount": 1, "seconds": 1, "flashes": 1}, h.harvest)

world = World(game([{"when": ALWAYS, "do": [{"tile": "harvestable",
                     "args": {"target": "self", "item": "  ", "amount": 1,
                              "seconds": 1, "flashes": 1}}]}]))
world.step()
check("a blank item name falls back to the word \"item\", not empty",
      hero(world).harvest["item"] == "item", hero(world).harvest)

world = World(game([
    {"when": ALWAYS, "do": [
        {"tile": "harvestable", "args": {"target": "self", "item": "wood",
                                          "amount": 1, "seconds": 5, "flashes": 4}},
        {"tile": "harvestable", "args": {"target": "self", "item": "stone",
                                          "amount": 9, "seconds": 1, "flashes": 1}},
    ]},
]))
world.step()
check("calling harvestable again replaces the config, last call wins",
      hero(world).harvest["item"] == "stone", hero(world).harvest)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
