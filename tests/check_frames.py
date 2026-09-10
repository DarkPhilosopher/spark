#!/usr/bin/env python3
"""Check set_frame/next_frame and World.render()'s own multi-cell sprite
drawing -- a character's own `frames` field, each one a list of
{dx, dy, glyph, color} pixels relative to its (x, y), authored with the
terminal builder's own Frames screen (see tests/check_frames_screen.py
for that) or directly in a game's own JSON.

    python3 tests/check_frames.py

Deliberately not folded into tests/check_engines.py's own shared
snapshot/parity harness, for the same reason check_harvest.py and
check_lead.py give: a real, gameplay-affecting field, but extending
that shared comparison shape is its own riskier change. This file and
its JS twin, tests/frames_tiles.test.js, check each engine's own
implementation directly against the same cases.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.tiles import a_next_frame, a_set_frame                # noqa: E402
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


def game(frames=None, width=8, height=5):
    chars = [{"kind": "blob", "glyph": "b", "color": "white", "health": 1,
              "count": 0, "role": "prop", "brain": []}]
    if frames is not None:
        chars[0]["frames"] = frames
    chars.append({"kind": "plain", "glyph": "P", "color": "white", "health": 1,
                  "count": 0, "role": "prop", "brain": []})
    return {"name": "frames_probe", "world": {"width": width, "height": height, "speed": 6},
            "characters": chars}


print("render(): a Thing with no frames at all draws exactly as it always did")

w = World(game(frames=None))
blob = w.spawn("blob", 2, 2)
lines = w.render(color=False)
check("the plain single glyph shows at its own spot, nothing else changed",
      lines[1 + blob.y][1 + blob.x] == "b", lines)

print("\nrender(): a multi-cell frame draws every one of its own pixels")

w = World(game(frames=[
    [{"dx": 0, "dy": 0, "glyph": "/", "color": "white"},
     {"dx": 1, "dy": 0, "glyph": "\\", "color": "white"}],
]))
blob = w.spawn("blob", 2, 2)
plain = w.spawn("plain", 5, 2)
lines = w.render(color=False)
check("both pixels of the frame show up, at the right offsets",
      lines[1 + 2][1 + 2] == "/" and lines[1 + 2][1 + 3] == "\\", lines)
check("the Thing's own (x, y) itself is not separately drawn underneath",
      lines[1 + 2].count("/") == 1, lines[1 + 2])
check("an ordinary frame-less Thing elsewhere is untouched by any of this",
      lines[1 + plain.y][1 + plain.x] == "P", lines)

print("\nrender(): an empty frame (0 pixels) falls back to the plain glyph too")

w = World(game(frames=[[]]))
blob = w.spawn("blob", 2, 2)
lines = w.render(color=False)
check("falls back the same way as having no frames at all",
      lines[1 + blob.y][1 + blob.x] == "b", lines)

print("\nset_frame / next_frame: jump to or step through a Thing's own frames")

w = World(game(frames=[
    [{"dx": 0, "dy": 0, "glyph": "A", "color": "white"}],
    [{"dx": 0, "dy": 0, "glyph": "B", "color": "white"}],
    [{"dx": 0, "dy": 0, "glyph": "C", "color": "white"}],
]))
blob = w.spawn("blob", 2, 2)
check("starts on frame 0", blob.frame_index == 0)

a_next_frame(blob, w, {}, None)
check("next_frame steps forward by exactly one",
      blob.frame_index == 1 and w.render(color=False)[1 + 2][1 + 2] == "B")

a_set_frame(blob, w, {"index": 2}, None)
check("set_frame jumps straight to the one asked for",
      blob.frame_index == 2 and w.render(color=False)[1 + 2][1 + 2] == "C")

a_next_frame(blob, w, {}, None)
check("stepping past the last one wraps back around to the first, via render()'s own modulo",
      blob.frame_index == 3 and w.render(color=False)[1 + 2][1 + 2] == "A",
      (blob.frame_index, w.render(color=False)[1 + 2]))

a_set_frame(blob, w, {"index": -5}, None)
check("set_frame never goes negative, even if asked to",
      blob.frame_index == 0, blob.frame_index)

print("\nset_frame / next_frame are safe to call even with no frames at all yet")

w2 = World(game(frames=None))
plainer = w2.spawn("blob", 1, 1)
a_next_frame(plainer, w2, {}, None)
a_set_frame(plainer, w2, {"index": 3}, None)
lines = w2.render(color=False)
check("still just draws the plain glyph -- no crash, frame_index quietly meaningless "
      "without any frames to index into",
      lines[1 + plainer.y][1 + plainer.x] == "b", lines)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
