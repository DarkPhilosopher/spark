#!/usr/bin/env python3
"""Check draw_line and world.lines -- a WHEN/DO-usable line between two
targets (see tests/harvest_tiles.test.js's own line-drawing checks, and
the Harvest section of world3d.html which uses this same list directly,
not through the tile, for the beam it draws during a countdown).

    python3 tests/check_draw_line.py

Only world3d.html actually draws anything -- Python has no renderer, so
what's worth checking here is that world.lines carries exactly what a row
asked for, and that it starts fresh every tick the same way both engines'
own comments say it does.
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
    return {"name": "line_probe",
            "world": {"width": width, "height": height, "speed": 6},
            "characters": chars}


def line(start, end, color="white"):
    return {"tile": "draw_line", "args": {"start": start, "end": end, "color": color}}


def hero(world):
    return next(t for t in world.things if t.role == "player")


print("draw_line: records exactly what was asked, nothing more\n")

world = World(game([{"when": ALWAYS, "do": [line("self", "self", "gold")]}]))
world.step()
h = hero(world)
check("self-to-self records a zero-length line, not nothing",
      world.lines == [{"x1": h.x, "y1": h.y, "z1": 0,
                        "x2": h.x, "y2": h.y, "z2": 0, "color": "gold"}], world.lines)

world = World(game([
    {"when": [{"tile": "touch", "args": {"kind": "cone"}}],
     "do": [line("self", "it", "pink")]},
], extra_characters=[
    {"kind": "cone", "glyph": "c", "color": "pink", "solid": False,
     "count": 1, "brain": []},
], width=3, height=3))
h = next(t for t in world.things if t.kind == "hero")
c = next(t for t in world.things if t.kind == "cone")
h.x, h.y, h.z = 1, 1, 0
c.x, c.y, c.z = 1, 1, 2
world.step()
check("self-to-it records both ends' real positions, altitude included",
      world.lines == [{"x1": 1, "y1": 1, "z1": 0, "x2": 1, "y2": 1, "z2": 2, "color": "pink"}],
      world.lines)

world = World(game([{"when": ALWAYS, "do": [line("self", "it", "white")]}]))
world.step()
check("no \"it\" established (a plain always row) -- draws nothing, not a stray line",
      world.lines == [], world.lines)

print("\nworld.lines: a fresh slate every tick, not a growing trail\n")

world = World(game([{"when": ALWAYS, "do": [line("self", "self")]}]))
world.step()
first_tick_count = len(world.lines)
world.step()
check("firing every tick keeps exactly one line, not one more each tick",
      len(world.lines) == first_tick_count == 1, len(world.lines))

world = World(game([
    {"when": [{"tile": "score_at_least", "args": {"value": 999}}],
     "do": [line("self", "self")]},
]))
world.step()
check("a row that never fires never draws, world.lines starts empty",
      world.lines == [], world.lines)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
