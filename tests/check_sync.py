#!/usr/bin/env python3
"""Check the GitHub push/pull logic without touching GitHub.

    python3 tests/check_sync.py

Everything that talks to the network or to git is swapped for a stand-in, so
this runs offline and proves the parts that are easy to get wrong: reading the
repo out of a remote URL, failing with a useful sentence, and sending exactly
one world when you name one world.
"""

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import sync                                     # noqa: E402

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


print("reading the repo out of a remote URL")
for url, want in [
    ("https://github.com/me/spark.git", ("me", "spark")),
    ("https://github.com/me/spark", ("me", "spark")),
    ("git@github.com:me/spark.git", ("me", "spark")),
    ("ssh://git@github.com/me/my.repo", ("me", "my.repo")),
    ("https://github.com/me/spark/", ("me", "spark")),
]:
    sync._run = lambda *a, u=url: u
    check(url, sync.repo() == want, sync.repo())

print("\nrefusing to guess when it cannot know")
sync._run = lambda *a: None
for fn, expect in [(sync.token, "not logged in"), (sync.repo, "no GitHub remote")]:
    try:
        fn()
        check(fn.__name__ + " errors clearly", False, "no error raised")
    except sync.SyncError as err:
        check(fn.__name__ + " errors clearly", expect in str(err), err)

sync._run = lambda *a: "https://gitlab.com/me/spark.git"
try:
    sync.repo()
    check("non-GitHub remote rejected", False)
except sync.SyncError as err:
    check("non-GitHub remote rejected", "cannot read a GitHub repo" in str(err))

print("\nnaming a game that does not exist")
try:
    sync._resolve(["ghost"], ["chase", "maze"], "local")
    check("unknown game named", False)
except sync.SyncError as err:
    check("unknown game named", "ghost" in str(err) and "chase, maze" in str(err), err)
check("no names means all of them",
      sync._resolve([], ["chase", "maze"], "l") == ["chase", "maze"])
check("one name means just that one",
      sync._resolve(["maze"], ["chase", "maze"], "l") == ["maze"])

print("\npush sends the right bodies")
calls = []


def fake_api(method, path, tok, body=None):
    calls.append((method, path, body))
    if method == "GET" and "contents/games?" in path:
        return 200, [{"name": "chase.json"}, {"name": "index.json"}]
    if method == "GET":
        return (200, {"sha": "OLD"}) if "chase" in path else (404, {})
    return 201, {}


sync.api = fake_api
sync.token = lambda: "tok"
sync.repo = lambda: ("me", "spark")
sync.branch = lambda: "main"

results, where = sync.push(["chase"])
puts = [c for c in calls if c[0] == "PUT"]
check("overwrote the one game and the listing", len(puts) == 2, len(puts))
check("reported it as an update, not a create", results == [("chase", "updated")], results)
check("sent the existing sha, so GitHub allows the overwrite",
      puts[0][2].get("sha") == "OLD")
sent = json.loads(base64.b64decode(puts[0][2]["content"]))
check("sent the real local file", sent["name"] == "chase" and sent["characters"])
check("wrote the individual world's path",
      puts[0][1].endswith("/contents/games/chase.json"), puts[0][1])
check("said where it went", where == "me/spark")

print("\npull writes what GitHub returns")
target = sync.brain.GAMES_DIR / "pulled_probe.json"
sync.api = lambda method, path, tok, body=None: (
    (200, [{"name": "pulled_probe.json"}]) if "contents/games?" in path
    else (200, {"content": base64.b64encode(b'{"name":"from_github"}').decode()}))
try:
    results, _ = sync.pull(["pulled_probe"])
    check("brought the file down", target.exists() and
          json.loads(target.read_text())["name"] == "from_github")
    check("said it was added, not overwritten", results == [("pulled_probe", "added")],
          results)
finally:
    if target.exists():
        target.unlink()

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
