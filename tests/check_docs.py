#!/usr/bin/env python3
"""Fail if README.md has drifted away from the code.

Documentation rots quietly. This makes it rot loudly instead:

    python3 tests/check_docs.py

It checks that every tile, every command and every file is written down, and
that the README still points at the changelog.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import tiles                                    # noqa: E402

README = (ROOT / "README.md").read_text()
CHANGELOG = (ROOT / "CHANGELOG.md").read_text()
LAUNCHER = (ROOT / "spark.py").read_text()

problems = []


def check(condition, complaint):
    if not condition:
        problems.append(complaint)


def words(label):
    """Significant words of a tile label, ignoring its {placeholders}."""
    bare = re.sub(r"\{\w+\}", " ", label)
    return [w for w in re.findall(r"[a-z]+", bare.lower()) if len(w) > 2]


# -- every tile is in the README's table ------------------------------------

for registry, half in ((tiles.SENSORS, "WHEN"), (tiles.ACTIONS, "DO")):
    for tile in registry.values():
        needed = words(tile.label)
        found = any(all(w in line.lower() for w in needed)
                    for line in README.splitlines())
        check(found, "%s tile '%s' (%s) is not in the README tile table"
                     % (half, tile.id, tile.label))

# -- every command the launcher answers to is documented --------------------

# the launcher matches a command either as == "x" or as in ("x", "y")
commands = set(re.findall(r'args\[0\] == "(\w+)"', LAUNCHER))
for group in re.findall(r"args\[0\] in \(([^)]*)\)", LAUNCHER):
    commands.update(re.findall(r'"(\w+)"', group))
for name in commands:
    check(re.search(r"spark\.py %s\b" % name, README),
          "command 'spark.py %s' is not in the README" % name)

# -- every file that ships is listed ----------------------------------------

# __init__.py only marks engine/ as a package; naming it would be noise
skip = {".spark-state.json", "index.json", "tiles.json", "__init__.py"}
for path in sorted(ROOT.rglob("*")):
    if path.is_dir() or "__pycache__" in path.parts or ".git" in path.parts:
        continue
    if path.suffix not in (".py", ".html", ".md", ".js"):
        continue
    if path.name in skip:
        continue
    rel = path.relative_to(ROOT).as_posix()
    check(rel in README or path.name in README,
          "%s exists but is not mentioned in the README" % rel)

# -- the two documents point at each other ----------------------------------

check("CHANGELOG.md" in README[:800],
      "the README must link to CHANGELOG.md near the top")
check("README.md" in CHANGELOG,
      "the CHANGELOG must link back to README.md")

# -- the tile count claimed in the README is the real one -------------------

flowed = " ".join(README.split())          # the sentence may wrap across lines
claim = re.search(r"([\w-]+) WHEN tiles crossed with ([\w-]+) DO tiles", flowed)
numbers = {"nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
           "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
           "eighteen": 18, "nineteen": 19, "twenty": 20,
           "twenty-one": 21, "twenty-two": 22, "twenty-three": 23,
           "twenty-four": 24, "twenty-five": 25, "twenty-six": 26,
           "twenty-seven": 27, "twenty-eight": 28, "twenty-nine": 29,
           "thirty": 30}
if claim:
    said = (numbers.get(claim.group(1).lower()), numbers.get(claim.group(2).lower()))
    check(said == (len(tiles.SENSORS), len(tiles.ACTIONS)),
          "the README says %s x %s tiles, but there are %d x %d"
          % (claim.group(1), claim.group(2), len(tiles.SENSORS), len(tiles.ACTIONS)))
else:
    problems.append("could not find the tile-count sentence in the README")

# ---------------------------------------------------------------------------

if problems:
    print("README is out of date:\n")
    for problem in problems:
        print("  - " + problem)
    sys.exit(1)

print("README matches the code: %d tiles, %d commands, all files listed"
      % (len(tiles.SENSORS) + len(tiles.ACTIONS), len(commands)))
