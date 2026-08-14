#!/usr/bin/env python3
"""Check `spark update` -- and above all that it never eats your games.

    python3 tests/check_update.py

`games/*.json` are tracked files, so a phone anybody has actually built on has
local changes, and a plain `git pull` would either refuse or trample them. The
important test here is the one that edits two games, updates, and demands both
edits back.

Everything happens in throwaway clones under a temporary folder. Nothing here
touches the real Spark, which is the whole reason this file exists: the updater
is the one piece that cannot be tried out safely in place.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

passed = failed = 0
WORK = Path(tempfile.mkdtemp(prefix="spark-update-"))


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


def git(where, *args):
    return subprocess.run(["git", "-C", str(where), *args],
                          capture_output=True, text=True, timeout=60)


def run_update(where, *args):
    """Run the updater inside a clone, with this Spark's copy of the code."""
    for name in ("spark.py",):
        shutil.copy(ROOT / name, where / name)
    shutil.copy(ROOT / "engine" / "updater.py", where / "engine" / "updater.py")
    done = subprocess.run([sys.executable, "spark.py", "update", *args],
                          cwd=str(where), capture_output=True, text=True,
                          timeout=180)
    return done.returncode, done.stdout + done.stderr


def make_origin():
    """A bare repo standing in for GitHub, with two commits in it."""
    origin = WORK / "origin.git"
    seed = WORK / "seed"
    subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
    shutil.copytree(ROOT, seed, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__",
                                                  "*.pyc", "approved.json"))
    git(seed, "add", "-A")
    git(seed, "-c", "user.email=t@t", "-c", "user.name=t",
        "commit", "-qm", "first")
    (seed / "NEWTHING.md").write_text("something new\n")
    git(seed, "add", "-A")
    git(seed, "-c", "user.email=t@t", "-c", "user.name=t",
        "commit", "-qm", "second")
    subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(origin)],
                   check=True)
    return origin


def clone_behind(origin, name):
    """A clone sitting one commit behind, as a phone would be."""
    where = WORK / name
    subprocess.run(["git", "clone", "-q", str(origin), str(where)], check=True)
    git(where, "reset", "--hard", "-q", "HEAD~1")
    return where


print("a clone that is one commit behind\n")

origin = make_origin()

where = clone_behind(origin, "look")
code, out = run_update(where, "--check")
check("--check sees the new commit", "1 new commit" in out, out)
check("--check changes nothing", not (where / "NEWTHING.md").exists(), out)
check("--check says it changed nothing", "was a look" in out, out)

where = clone_behind(origin, "plain")
code, out = run_update(where)
check("a plain update pulls it in", (where / "NEWTHING.md").exists(), out)
check("...and says what it did", "updated" in out, out)
check("...and rewrites the generated files", "rewrote tiles.json" in out, out)

code, out = run_update(where)
check("running it again says there is nothing to do",
      "already up to date" in out, out)

print("\nyour games are tracked, so they must survive")

where = clone_behind(origin, "mine")
edits = {}
for name, speed in (("chase", 11), ("mygame", 7)):
    path = where / "games" / (name + ".json")
    if not path.exists():
        continue
    game = json.loads(path.read_text())
    game["world"]["speed"] = speed
    path.write_text(json.dumps(game, indent=2))
    edits[name] = speed
code, out = run_update(where)
check("it says it is putting your changes aside",
      "putting aside your changes" in out, out)
check("the file names come out whole, not a character short",
      "games/chase.json" in out and "ames/chase.json" not in
      out.replace("games/chase.json", ""), out)
check("...and puts them back", "put your changes back" in out, out)
for name, speed in edits.items():
    got = json.loads((where / "games" / (name + ".json")).read_text())
    check("%s kept your edit" % name, got["world"]["speed"] == speed, got["world"])
check("the update still happened", (where / "NEWTHING.md").exists())
check("nothing was left stuck in the stash",
      not git(where, "stash", "list").stdout.strip(),
      git(where, "stash", "list").stdout)

print("\nwhen it must refuse")

where = clone_behind(origin, "noremote")
git(where, "remote", "remove", "origin")
code, out = run_update(where)
check("no remote: refuses and says how to fix it",
      code != 0 and "no `origin` remote" in out, out)

where = clone_behind(origin, "nogit")
shutil.rmtree(where / ".git")
code, out = run_update(where)
check("not a clone: refuses and says how to get one",
      code != 0 and "not a git clone" in out, out)

where = clone_behind(origin, "unreachable")
git(where, "remote", "set-url", "origin", "https://example.invalid/no.git")
code, out = run_update(where)
check("unreachable: refuses and shows git's own words",
      code != 0 and "could not reach" in out, out)

where = clone_behind(origin, "diverged")
(where / "README.md").write_text("mine\n")
git(where, "-c", "user.email=t@t", "-c", "user.name=t",
    "commit", "-qam", "a commit of my own")
was = git(where, "rev-parse", "HEAD").stdout.strip()
code, out = run_update(where)
check("commits of your own: refuses rather than guessing",
      code != 0 and "fast-forward" in out, out)
check("...and changes nothing at all",
      git(where, "rev-parse", "HEAD").stdout.strip() == was)
check("...and says nothing was changed", "Nothing was changed" in out, out)

print("\nthe command that runs it")

from engine import launcher                                  # noqa: E402
names = [p.name for p, _, _ in launcher.update_targets()]
check("an `update` command goes into the bin folders", "update" in names, names)
check("`/update` is offered where the root can be written",
      "update" in names, names)
script = launcher.UPDATE_SCRIPT.format(shell="/bin/sh", root=ROOT)
check("the script accepts the word `spark` after it", "spark|Spark|SPARK" in script)
check("...and refuses anything else", "I only know how to update spark" in script)
check("...and ends up running spark.py update", "spark.py update" in script)

shutil.rmtree(WORK, ignore_errors=True)
print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
