#!/usr/bin/env python3
"""Check the remember / recall / open tiles, and the fence around opening.

    python3 tests/check_open.py

`open` is the only tile that reaches outside the game -- it hands a URL to
another app on the phone. That makes it the one tile worth testing on its own,
because a game file is a thing people share: it comes down from GitHub, and a
guest holding an `edit` code can rewrite one. Neither of those people should be
able to make this phone launch anything.

Nothing is really launched here. subprocess.Popen is swapped for a recorder, so
what the test inspects is the exact command the tile would have run.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import brain, live, tiles                       # noqa: E402
from engine.world import World                              # noqa: E402

passed = failed = 0
launched = []


class Recorder:
    """Stands in for subprocess.Popen: remembers, launches nothing."""

    def __init__(self, command, **kwargs):
        launched.append(list(command))


tiles.subprocess.Popen = Recorder


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


def game(rows):
    return {"name": "open_probe", "world": {"width": 9, "height": 5, "speed": 6},
            "characters": [{"kind": "hero", "glyph": "@", "color": "green",
                            "role": "player", "count": 1, "brain": rows}]}


def row(when, do):
    return {"when": when, "do": do}


ALWAYS = [{"tile": "always", "args": {}}]


def run(rows, ticks=1, may_open=True):
    launched.clear()
    world = World(game(rows))
    world.may_open = may_open
    for _ in range(ticks):
        world.step()
    return world


# -- remembering ------------------------------------------------------------

print("a name can be remembered and read back")

world = run([row(ALWAYS, [{"tile": "remember",
                           "args": {"name": "chrome",
                                    "value": "com.android.chrome"}}])])
check("the value is kept", world.memory.get("chrome") == "com.android.chrome",
      world.memory)

world = run([
    row(ALWAYS, [{"tile": "remember", "args": {"name": "seen", "value": "yes"}}]),
    row([{"tile": "recall", "args": {"name": "seen", "value": "yes"}}],
        [{"tile": "say", "args": {"text": "found it"}}]),
])
check("a WHEN can read it back", world.message == "found it", world.message)

world = run([row([{"tile": "recall", "args": {"name": "seen", "value": "yes"}}],
                 [{"tile": "say", "args": {"text": "found it"}}])])
check("nothing is remembered at the start", world.message != "found it")

world = run([
    row(ALWAYS, [{"tile": "remember", "args": {"name": "n", "value": "one"}},
                 {"tile": "remember", "args": {"name": "n", "value": "two"}}]),
])
check("remembering again overwrites", world.memory.get("n") == "two",
      world.memory)

# -- opening ----------------------------------------------------------------

print("\nopen hands the target to the app")

run([row(ALWAYS, [
    {"tile": "remember", "args": {"name": "chrome", "value": "com.android.chrome"}},
    {"tile": "remember", "args": {"name": "home", "value": "http://127.0.0.1:8765/"}},
    {"tile": "open", "args": {"object": "chrome", "target": "home"}}])])
check("remembered names are looked up",
      launched == [["termux-open-url", "http://127.0.0.1:8765/",
                    "com.android.chrome"]], launched)

run([row(ALWAYS, [{"tile": "open", "args": {"object": "org.mozilla.firefox",
                                            "target": "https://example.com"}}])])
check("a name nobody remembered is used as-is",
      launched == [["termux-open-url", "https://example.com",
                    "org.mozilla.firefox"]], launched)

run([row(ALWAYS, [{"tile": "open", "args": {"object": "",
                                            "target": "https://example.com"}}])])
check("no app named means the phone's usual one",
      launched == [["termux-open-url", "https://example.com"]], launched)

run([row(ALWAYS, [{"tile": "open", "args": {"object": "com.android.chrome",
                                            "target": ""}}])])
check("nothing to open means nothing happens", launched == [], launched)

# -- the fences -------------------------------------------------------------

print("\na row on `always` does not open six times a second")

world = run([row(ALWAYS, [{"tile": "open",
                           "args": {"object": "com.android.chrome",
                                    "target": "https://example.com"}}])],
            ticks=tiles.OPEN_COOLDOWN + 2)
check("the same thing waits out the cooldown", len(launched) == 2, len(launched))

launched.clear()
world = World(game([row(ALWAYS, [
    {"tile": "open", "args": {"object": "com.android.chrome",
                              "target": "https://one.example"}},
    {"tile": "open", "args": {"object": "com.android.chrome",
                              "target": "https://two.example"}}])]))
world.may_open = True
world.step()
check("different targets are not held up by each other", len(launched) == 2,
      launched)

print("\nopening is off unless whoever plays turned it on")

world = run([row(ALWAYS, [{"tile": "open",
                           "args": {"object": "com.android.chrome",
                                    "target": "https://example.com"}}])],
            may_open=False)
check("a world that did not ask for it opens nothing", launched == [], launched)
check("the world says so instead", "off" in world.message, world.message)

world = World(game([]))
check("worlds start with opening off", world.may_open is False)

# -- the one that matters: a shared world -----------------------------------

print("\na guest cannot make the host's phone launch anything")

hostile = game([row(ALWAYS, [{"tile": "open",
                              "args": {"object": "com.android.chrome",
                                       "target": "https://example.com"}}])])
hostile["name"] = "open_probe_hostile"
path = brain.save(hostile, brain.GAMES_DIR / "open_probe_hostile.json")

launched.clear()
session = live.Session()
invite = session.invite("play", "own", "a guest")
session.join(invite.code, "guest")
session.start("open_probe_hostile")
time.sleep(0.8)
session.stop()

check("the shared world really did run", session.world.tick > 0,
      session.world.tick)
check("...with opening off", session.world.may_open is False)
check("...and launched nothing", launched == [], launched)

Path(path).unlink(missing_ok=True)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
