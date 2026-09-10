#!/usr/bin/env python3
"""Check the terminal player's own status line -- score/health/tick,
and now the player's own coordinates too, right under the map.

    python3 tests/check_status_line.py
"""

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.runner import draw                                    # noqa: E402
from engine.world import World                                    # noqa: E402

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


def project():
    return {
        "name": "status_probe", "world": {"width": 12, "height": 8, "speed": 6},
        "characters": [
            {"kind": "hero", "glyph": "@", "color": "green", "role": "player",
             "count": 0, "health": 12, "brain": []},
        ],
    }


def status_line(world):
    buf = io.StringIO()
    with redirect_stdout(buf):
        draw(world, 6)
    lines = buf.getvalue().splitlines()
    return next(line for line in lines if line.startswith("score"))


print("draw(): the status line right under the map shows the player's own position")

w = World(project())
hero = w.spawn("hero", 3, 5)
line = status_line(w)
check("shows the player's own x,y", "pos 3,5" in line, line)
check("still shows score/health/tick, unchanged", "score" in line and "health 12" in line
      and "tick 0" in line, line)

hero.x, hero.y = 7, 1
line = status_line(w)
check("updates as the player actually moves", "pos 7,1" in line, line)

w2 = World(project())
hero2 = w2.spawn("hero", 4, 4)
hero2.health = 0
hero2.alive = False
line = status_line(w2)
check("a dead player (nothing left to report a position for) shows a placeholder, not a crash",
      "pos -,-" in line, line)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
