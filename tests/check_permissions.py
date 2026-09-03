#!/usr/bin/env python3
"""Check that a guest can only do what their invite code allowed.

    python3 tests/check_permissions.py

`spark.py host` opens Spark to everyone on the wifi, so this is the test that
matters most. It starts a real server, joins it as three different kinds of
guest and as a stranger with no code at all, and tries things each of them
should not be able to do.

Everything here comes from 127.0.0.1, which is what the host looks like. So the
test puts the server in the state `spark.py host` uses, where being on loopback
proves nothing and the owner must present the key printed in the terminal --
exactly the arrangement that stops a tunnel handing strangers the keys.
"""

import json
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import live, server                             # noqa: E402

PORT = 8899
BASE = "http://127.0.0.1:%d" % PORT

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


def call(method, path, token=None, body=None, owner_key=None):
    request = urllib.request.Request(
        BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json",
                 **({"X-Spark-Token": token} if token else {}),
                 **({"X-Spark-Owner": owner_key} if owner_key else {})})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as err:
        try:
            return err.code, json.loads(err.read() or b"{}")
        except ValueError:
            return err.code, {}


# -- a real server, on a thread, in the state hosting puts it in -------------

server.OWNER_KEY = "test-owner-key"
server.LOOPBACK_IS_OWNER = False

httpd = server.ThreadingHTTPServer(("127.0.0.1", PORT), server.Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.3)

session = live.SESSION
codes = {role: session.invite(role, "own" if role != "watch" else "watch").code
         for role in ("edit", "play", "watch")}

tokens = {}
for role, code in codes.items():
    status, body = call("POST", "/api/join", body={"code": code, "name": role})
    tokens[role] = body.get("token")
    check("joining with an %s code works" % role, status == 200 and tokens[role])

status, body = call("POST", "/api/join", body={"code": "BOGUS1", "name": "x"})
check("a made-up code is refused", status == 403, body)

# -- what each role may do ---------------------------------------------------

print("\nreading the game list (editors only)")
for role in ("edit", "play", "watch", None):
    status, _ = call("GET", "/api/games", tokens.get(role))
    want = 200 if role == "edit" else 403
    check("%-9s -> %d" % (role or "no code", want), status == want, status)

print("\nsaving a game (editors only)")
for role in ("edit", "play", "watch", None):
    status, _ = call("POST", "/api/game", tokens.get(role),
                     {"name": "perm_probe_" + (role or "none"), "characters": []})
    want = 200 if role == "edit" else 403
    check("%-9s -> %d" % (role or "no code", want), status == want, status)

print("\ndeleting a game (editors only)")
for role in ("play", "watch", None):
    status, _ = call("DELETE", "/api/game?name=chase", tokens.get(role))
    check("%-9s -> 403" % (role or "no code"), status == 403, status)
check("chase survived every attempt", (ROOT / "games" / "chase.json").exists())

print("\nhost controls (the phone itself only)")
for role in ("edit", "play", "watch", None):
    status, _ = call("POST", "/api/host/start", tokens.get(role), {"game": "chase"})
    check("%-9s -> 403" % (role or "no code"), status == 403, status)
for role in ("edit", "play", "watch", None):
    status, _ = call("GET", "/api/host/invites", tokens.get(role))
    check("%-9s cannot list invites" % (role or "no code"), status == 403, status)

print("\nwatching the world (any guest) and pressing keys (players only)")
session.start("chase")
time.sleep(0.4)
for role in ("edit", "play", "watch"):
    status, snap = call("GET", "/api/live", tokens[role])
    check("%-5s can see the world" % role, status == 200 and snap.get("things"), status)
status, _ = call("GET", "/api/live", None)
check("a stranger sees nothing", status == 403, status)

status, _ = call("POST", "/api/key", tokens["watch"], {"keys": ["right"]})
check("watcher cannot press keys", status == 403, status)
status, _ = call("POST", "/api/key", tokens["play"], {"keys": ["right"]})
check("player can press keys", status == 200, status)

watcher = session.who(tokens["watch"])
check("watcher was never given a character", watcher.thing is None)
player = session.who(tokens["play"])
check("player was given a character", player.thing is not None)
check("player's character answers only to them",
      player.thing.controller == player.id)

print("\nthe owner key still opens everything")
status, _ = call("GET", "/api/host/invites", owner_key="test-owner-key")
check("right key -> allowed", status == 200, status)
status, _ = call("GET", "/api/host/invites", owner_key="wrong-key")
check("wrong key -> refused", status == 403, status)

print("\nrevoking a code cuts off whoever used it")
session.revoke(codes["play"])
status, _ = call("GET", "/api/live", tokens["play"])
check("revoked token is a stranger again", status == 403, status)

session.stop()
httpd.shutdown()

for stray in ROOT.glob("games/perm_probe_*.json"):
    stray.unlink()

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
