#!/usr/bin/env python3
"""Check tiles you wrote yourself in Python, and the gate in front of them.

    python3 tests/check_mytiles.py

This is the only part of Spark that runs code rather than reading data, so it
is the part where a mistake is not a wrong answer but somebody else's program
running on your phone. Two things are therefore tested harder than anything
else in this project:

    a file does nothing until THIS device has approved it, and approval is
    recorded against the exact text approved;

    only the owner may write one -- an `edit` code, which may rewrite every
    game you own, may not put a single line of Python on your disk.

The rest is ordinary: a broken file must not stop Spark starting, and saving a
file again must take its old tiles off the menus before putting the new ones on.

Everything here happens in a folder of its own under /tmp, so your real
mytiles/ is not touched.
"""

import json
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import live, mytiles, server, tiles              # noqa: E402

passed = failed = 0

# Work somewhere disposable rather than in the real mytiles/.
SANDBOX = Path(tempfile.mkdtemp(prefix="spark-mytiles-"))
mytiles.FOLDER = SANDBOX
mytiles.APPROVED = SANDBOX / "approved.json"


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


def write_raw(name, text):
    """Put a file there without going through save(), as a git pull would."""
    (SANDBOX / (name + ".py")).write_text(text)


TILE = ('@action("wobble", "wobble {much}", Param("much", "How far?", '
        '"int", [], 1))\ndef w(obj, world, a, it):\n    obj.x += 1\n')
OTHER = '@action("shuffle", "shuffle about")\ndef s(obj, world, a, it):\n    pass\n'


def clean():
    for path in list(SANDBOX.glob("*.py")):
        mytiles.forget(path.stem)
        path.unlink()
    if mytiles.APPROVED.exists():
        mytiles.APPROVED.unlink()
    for tile_id in ("wobble", "shuffle", "sneaky"):
        tiles.SENSORS.pop(tile_id, None)
        tiles.ACTIONS.pop(tile_id, None)


# -- the gate ---------------------------------------------------------------

print("a file does nothing until this device approves it\n")

clean()
write_raw("arrived", TILE)
mytiles.load()
check("a file that simply appeared does not load", "wobble" not in tiles.ACTIONS)
row = [f for f in mytiles.listing() if f["name"] == "arrived"][0]
check("...and is shown as not approved", row["approved"] is False, row)
check("...and not as changed either, having never been approved",
      row["changed"] is False, row)

mytiles.approve("arrived", True)
mytiles.load()
check("approving it lets it load", "wobble" in tiles.ACTIONS)

write_raw("arrived", OTHER)
mytiles.load()
check("editing it behind our back stops it loading",
      "shuffle" not in tiles.ACTIONS)
check("...and takes the tiles it used to give off the menus too",
      "wobble" not in tiles.ACTIONS)
row = [f for f in mytiles.listing() if f["name"] == "arrived"][0]
check("...and says it changed since approval, not merely that it is off",
      row["changed"] is True and row["approved"] is False, row)

mytiles.approve("arrived", True)
mytiles.load()
check("approving the new text loads the new tile", "shuffle" in tiles.ACTIONS)

mytiles.approve("arrived", False)
mytiles.load()
check("switching it off takes its tiles away again",
      "shuffle" not in tiles.ACTIONS)

print("\nthe approval never travels with the file")

clean()
mytiles.save("mine", TILE)
check("saving records approval", mytiles.read_approvals().get("mine"))
check("approval lives in its own file, not in the .py",
      mytiles.APPROVED.name == "approved.json")
gitignore = (ROOT / ".gitignore").read_text()
check("that file is gitignored, which is what makes the promise hold",
      "mytiles/approved.json" in gitignore, gitignore)

# -- saving replaces cleanly ------------------------------------------------

print("\nsaving a file again")

clean()
mytiles.save("mine", TILE)
mytiles.load()
check("its tile is on the menus", "wobble" in tiles.ACTIONS)
mytiles.save("mine", OTHER)
mytiles.load()
check("saving different text puts the new tile on", "shuffle" in tiles.ACTIONS)
check("...and takes the old one off", "wobble" not in tiles.ACTIONS)
mytiles.delete("mine")
check("deleting takes its tiles off too", "shuffle" not in tiles.ACTIONS)
check("...and removes the file", not (SANDBOX / "mine.py").exists())
check("...and its approval", "mine" not in mytiles.read_approvals())

# -- a broken file ----------------------------------------------------------

print("\na file that will not run")

clean()
mytiles.save("good", TILE)
mytiles.save("bad", "this is not python(((\n")
loaded = mytiles.load()
check("the good one still loads", "wobble" in tiles.ACTIONS)
check("only the good one counts as loaded", loaded == 1, loaded)
check("the bad one's trouble is kept, to be shown in the editor",
      bool(mytiles.errors.get("bad")))
row = [f for f in mytiles.listing() if f["name"] == "bad"][0]
check("...and reaches the editor", bool(row["error"]), row)

clean()
mytiles.save("halfway",
             TILE + '\nraise ValueError("falls over after registering")\n')
mytiles.load()
check("a file that falls over halfway leaves nothing registered",
      "wobble" not in tiles.ACTIONS)

# -- names ------------------------------------------------------------------

print("\nnames that try to leave the folder")

for bad in ("../../evil", "a/b", "x.py", "..", "", "   ", "a" * 61):
    check("rejected: %r" % bad, mytiles.safe_name(bad) is None)
for good in ("my tile", "tile-2", "under_score", "Tile9"):
    check("allowed:  %r" % good, mytiles.safe_name(good) == good)
check("a rejected name writes nothing", mytiles.save("../../evil", "x") is None)

# -- who may write one ------------------------------------------------------

print("\nonly the owner may put Python on this phone")

clean()
PORT = 8874
BASE = "http://127.0.0.1:%d" % PORT
server.OWNER_KEY = "ownerkey"
server.LOOPBACK_IS_OWNER = False
httpd = server.ThreadingHTTPServer(("127.0.0.1", PORT), server.Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.3)


def call(method, path, body=None, owner=False, token=None):
    headers = {"Content-Type": "application/json"}
    if owner:
        headers["X-Spark-Owner"] = "ownerkey"
    if token:
        headers["X-Spark-Token"] = token
    request = urllib.request.Request(
        BASE + path, method=method, headers=headers,
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as err:
        return err.code, {}


invite = live.SESSION.invite("edit", "own", "tester")
_, joined = call("POST", "/api/join", {"code": invite.code, "name": "Guest"})
token = joined.get("token")
check("a guest joined holding an EDIT code",
      token and live.SESSION.who(token).role == "edit")

check("an editor may not read them",
      call("GET", "/api/mytiles", token=token)[0] == 403)
check("an editor may not write one",
      call("POST", "/api/mytiles",
           {"name": "sneaky", "text": "import os"}, token=token)[0] == 403)
check("an editor may not switch one on",
      call("POST", "/api/mytiles/approve",
           {"name": "sneaky", "on": True}, token=token)[0] == 403)
check("an editor may not delete one",
      call("DELETE", "/api/mytiles?name=good", token=token)[0] == 403)
check("nothing of theirs reached the disk",
      not (SANDBOX / "sneaky.py").exists())
check("but an editor may still save a game, as before",
      call("POST", "/api/game",
           {"name": "guest probe", "world": {}, "characters": []},
           token=token)[0] == 200)

check("the owner may read them", call("GET", "/api/mytiles", owner=True)[0] == 200)
status, out = call("POST", "/api/mytiles",
                   {"name": "by owner", "text": TILE}, owner=True)
check("the owner may write one", status == 200 and
      any(f["name"] == "by owner" for f in out.get("files", [])), out)
check("...and it is switched on by the writing of it",
      [f for f in out["files"] if f["name"] == "by owner"][0]["approved"])
check("a name that tries to escape is refused over HTTP too",
      call("POST", "/api/mytiles",
           {"name": "../../pwned", "text": "x"}, owner=True)[0] == 400)
check("nothing was written outside the folder",
      not (ROOT.parent / "pwned.py").exists())

(ROOT / "games" / "guest probe.json").unlink(missing_ok=True)
clean()

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
