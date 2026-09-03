#!/usr/bin/env python3
"""Check the undo stack behind the brain editor.

    python3 tests/check_undo.py

The terminal menus and the browser keep separate but identical stacks: the whole
game copied as text, once per change. This exercises the Python one directly,
without going through the menus, because what can go wrong is not the menus --
it is the stack.

The subtle one is the last test here. Undo refills the project dict in place
rather than rebinding it, because every screen in builder.py is holding that
same dict; a rebind would leave them all editing an abandoned copy. The screens
still have to unwind afterwards, since the characters and rows *inside* it are
new objects, and that is what the UNDONE signal is for.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import builder                                   # noqa: E402

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


def game():
    return {"name": "undo_probe",
            "world": {"width": 9, "height": 5, "speed": 6},
            "characters": [{"kind": "hero", "glyph": "@", "color": "green",
                            "health": 1, "count": 1, "solid": False,
                            "role": "player", "brain": []}]}


def rows(project):
    return project["characters"][0]["brain"]


ROW = {"when": [{"tile": "always", "args": {}}],
       "do": [{"tile": "say", "args": {"text": "hi"}}]}


print("one change, one step back\n")

builder.forget_history()
project = game()
builder.remember(project)
rows(project).append(dict(ROW))
check("a row was added", len(rows(project)) == 1)
check("undo reports that it moved", builder.undo(project) is True)
check("...and the row is gone", rows(project) == [], project)
check("nothing left to undo", builder.undo(project) is False)

print("\nseveral changes, in order")

builder.forget_history()
project = game()
for i in range(3):
    builder.remember(project)
    rows(project).append({"when": [], "do": [
        {"tile": "say", "args": {"text": str(i)}}]})
check("three rows", len(rows(project)) == 3)
builder.undo(project)
check("one back leaves two", len(rows(project)) == 2, rows(project))
builder.undo(project)
builder.undo(project)
check("all the way back leaves none", rows(project) == [], rows(project))
check("and then it stops", builder.undo(project) is False)

print("\na mark that changed nothing is dropped")

builder.forget_history()
project = game()
builder.remember(project)
builder.forget_if_same(project)
check("an untouched mark is forgotten", builder.undo(project) is False)

builder.remember(project)
rows(project).append(dict(ROW))
builder.forget_if_same(project)
check("a mark with a real change after it is kept",
      builder.undo(project) is True and rows(project) == [], project)

print("\nthe stack has a floor and a ceiling")

builder.forget_history()
project = game()
for i in range(builder.UNDO_DEPTH + 20):
    builder.remember(project)
    rows(project).append({"when": [], "do": []})
check("the stack stops growing at UNDO_DEPTH",
      len(builder._history) == builder.UNDO_DEPTH, len(builder._history))
steps = 0
while builder.undo(project):
    steps += 1
check("...and undoes exactly that many times", steps == builder.UNDO_DEPTH, steps)
check("the oldest changes are the ones that fell off the end",
      len(rows(project)) == 20, len(rows(project)))

print("\nundo refills the project rather than replacing it")

builder.forget_history()
project = game()
same_dict = project                       # what every screen in builder.py holds
builder.remember(project)
rows(project).append(dict(ROW))
builder.undo(project)
check("the caller's own dict is the one that changed", same_dict is project)
check("...and it really did change back", rows(same_dict) == [], same_dict)

print("\nforgetting the history")

builder.forget_history()
project = game()
builder.remember(project)
rows(project).append(dict(ROW))
builder.forget_history()
check("after forgetting, there is nothing to undo",
      builder.undo(project) is False)
check("...and the game is left as it was", len(rows(project)) == 1)

print("\nwhat the menu line says")

builder.forget_history()
check("empty stack says so", "nothing yet" in builder.undo_label(),
      builder.undo_label())
project = game()
builder.remember(project)
builder.remember(project)
check("a stack of two says two", "(2)" in builder.undo_label(),
      builder.undo_label())

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
