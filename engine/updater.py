"""Bring this copy of Spark up to date with GitHub.

    python3 spark.py update      (or  spark update,  or  /update spark)

An ordinary `git pull` is very nearly the whole job, and the parts that are not
are the parts worth writing down:

  * **Your games are tracked files.** `games/*.json` lives in the repo, so a
    phone where you have been building anything has local changes, and a plain
    pull would refuse or trample them. They are put aside before the pull and
    put back after -- and if putting them back collides, that is said plainly
    rather than left as a half-merged file you find out about later.

  * **`mytiles/approved.json` is not tracked**, on purpose, so an update can
    never switch a Python tile on. A tile file that arrives or changes in the
    pull lands inert, exactly as it would arriving any other way.

  * **`tiles.json` is generated.** After a pull that changed the tile library it
    has to be rewritten, or the offline browser copy shows yesterday's palette.

Nothing here runs unless it is asked to. Spark does not check for updates by
itself, and never will: a game builder that quietly rewrites itself while you
are using it is a worse thing than an out-of-date one.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STASH_NAME = "spark-update"


class UpdateError(Exception):
    """Something went wrong that the person typing needs to read."""


def git(*args, timeout=120):
    """Run git in the Spark folder. Returns (ok, output)."""
    try:
        done = subprocess.run(["git", "-C", str(ROOT), *args],
                              capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise UpdateError("git is not installed. In Termux:  pkg install git")
    except (OSError, subprocess.SubprocessError) as err:
        raise UpdateError("git would not run: %s" % err)
    return done.returncode == 0, (done.stdout + done.stderr).strip()


def head():
    ok, out = git("rev-parse", "--short", "HEAD")
    return out if ok else "?"


def branch():
    ok, out = git("rev-parse", "--abbrev-ref", "HEAD")
    return out if ok and out != "HEAD" else "main"


def dirty():
    """Tracked files changed here since the last commit.

    `diff --name-only` rather than `status --porcelain` because porcelain puts
    a two-letter status and a space in front of each name, and the leading one
    of those is a space for an unstaged change -- which the strip() in git()
    eats, leaving the name one character short. Names with no prefix cannot go
    wrong that way.
    """
    ok, out = git("diff", "--name-only", "HEAD")
    return [line.strip() for line in out.splitlines() if line.strip()] if ok else []


def update(dry_run=False):
    """Do it. Returns a list of lines to print, newest news last."""
    said = []

    ok, _ = git("rev-parse", "--git-dir")
    if not ok:
        raise UpdateError(
            "this Spark is not a git clone, so there is nothing to pull from.\n"
            "  Get one with:  git clone "
            "https://github.com/DarkPhilosopher/spark.git")
    ok, remote = git("remote", "get-url", "origin")
    if not ok or not remote:
        raise UpdateError(
            "this Spark has no `origin` remote, so there is nowhere to pull "
            "from.\n  Add one with:  git remote add origin <your repo url>")

    was, here = head(), branch()
    said.append("from %s, on %s" % (remote, here))

    ok, out = git("fetch", "origin", here)
    if not ok:
        raise UpdateError("could not reach GitHub:\n  " + out)

    ok, behind = git("rev-list", "--count", "HEAD..origin/" + here)
    count = int(behind) if ok and behind.isdigit() else 0
    if count == 0:
        said.append("already up to date at %s" % was)
        return said
    said.append("%d new commit%s" % (count, "" if count == 1 else "s"))

    if dry_run:
        ok, log = git("log", "--oneline", "HEAD..origin/" + here)
        said.extend("  " + line for line in log.splitlines())
        said.append("(nothing changed -- this was a look, not an update)")
        return said

    # Your games are tracked, so anything you have built here is a local change.
    mine = dirty()
    stashed = False
    if mine:
        said.append("putting aside your changes to %d file%s"
                    % (len(mine), "" if len(mine) == 1 else "s"))
        for name in mine[:6]:
            said.append("  " + name)
        if len(mine) > 6:
            said.append("  ...and %d more" % (len(mine) - 6))
        ok, out = git("stash", "push", "-m", STASH_NAME)
        if not ok:
            raise UpdateError("could not put your changes aside:\n  " + out)
        stashed = True

    ok, out = git("merge", "--ff-only", "origin/" + here)
    if not ok:
        if stashed:
            git("stash", "pop")
        raise UpdateError(
            "could not fast-forward -- this copy has commits GitHub does not.\n"
            "  Nothing was changed. Push yours first, or ask for help.\n  " + out)

    said.append("updated %s -> %s" % (was, head()))

    if stashed:
        ok, out = git("stash", "pop")
        if ok:
            said.append("...and put your changes back")
        else:
            said.append("YOUR CHANGES ARE SAFE BUT NOT BACK YET.")
            said.append("They collided with the update. They are kept in the")
            said.append("stash -- get them with:  git -C %s stash pop" % ROOT)
            said.append("  " + out.splitlines()[0] if out else "")

    # tiles.json and games/index.json are generated, and a pull that changed the
    # tile library leaves them stale for the offline browser copy.
    try:
        from . import server
        server.export_static()
        said.append("rewrote tiles.json and games/index.json")
    except Exception as err:                                   # noqa: BLE001
        said.append("could not rewrite tiles.json: %s" % err)

    said.append("restart Spark to run the new version")
    return said
