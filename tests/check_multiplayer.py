#!/usr/bin/env python3
"""Two people, one world, over real HTTP.

    python3 tests/check_multiplayer.py

Starts a host, joins as two separate players the way two phones would, and
checks that each one's arrow keys move their own character and nobody else's.
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

PORT = 8898
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


def call(method, path, token=None, body=None):
    request = urllib.request.Request(
        BASE + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json",
                 **({"X-Spark-Token": token} if token else {})})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as err:
        return err.code, {}


server.OWNER_KEY = "k"
server.LOOPBACK_IS_OWNER = False
httpd = server.ThreadingHTTPServer(("127.0.0.1", PORT), server.Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.3)

session = live.SESSION
code = session.invite("play", "own", "players").code

_, one = call("POST", "/api/join", body={"code": code, "name": "Ash"})
_, two = call("POST", "/api/join", body={"code": code, "name": "Bo"})
check("two people joined on one code", one.get("token") and two.get("token"))
check("they got different tokens", one["token"] != two["token"])

session.start("chase")
time.sleep(0.5)

p1, p2 = session.who(one["token"]), session.who(two["token"])
check("each has their own character", p1.thing is not None and p2.thing is not None
      and p1.thing is not p2.thing)

# park them somewhere known, out of each other's way
with session.lock:
    p1.thing.x, p1.thing.y = 3, 3
    p2.thing.x, p2.thing.y = 20, 9
    start1 = (p1.thing.x, p1.thing.y)
    start2 = (p2.thing.x, p2.thing.y)

print("\none player presses a key")
call("POST", "/api/key", one["token"], {"keys": ["right"]})
time.sleep(0.6)
with session.lock:
    moved1 = (p1.thing.x, p1.thing.y)
    moved2 = (p2.thing.x, p2.thing.y)
check("the presser moved", moved1 != start1, (start1, moved1))
check("the other player did not", moved2 == start2, (start2, moved2))

print("\nthe other one presses a different key")
with session.lock:
    before = (p2.thing.x, p2.thing.y)
call("POST", "/api/key", two["token"], {"keys": ["down"]})
time.sleep(0.6)
with session.lock:
    after = (p2.thing.x, p2.thing.y)
check("they moved downward", after[1] > before[1] or after != before, (before, after))

print("\nwhat each player sees")
status, snap = call("GET", "/api/live", one["token"])
check("the world comes back drawable",
      status == 200 and snap["w"] == 30 and len(snap["things"]) > 3)
check("they are told who they are", snap["you"]["name"] == "Ash", snap["you"])
check("they can see who else is here",
      sorted(p["name"] for p in snap["people"]) == ["Ash", "Bo"], snap["people"])
check("health is reported for the hud", snap["you"]["health"] is not None)

print("\nleaving")
session.drop(two["token"])
time.sleep(0.4)
status, _ = call("GET", "/api/live", two["token"])
check("a departed player is a stranger again", status == 403, status)
status, snap = call("GET", "/api/live", one["token"])
check("the one still here keeps playing", status == 200 and len(snap["people"]) == 1)

session.stop()
httpd.shutdown()
print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
