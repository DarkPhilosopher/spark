"""The local server: serves the editor, and hosts the shared world.

Two ways to run it:

    spark.py edit    only this phone can reach it (127.0.0.1)
    spark.py host    anyone on the same wifi can reach it (0.0.0.0)

Because `host` opens a door, every route states who may use it. The rule is
default deny: unknown callers get the join page and nothing else.

    owner   whoever is on the phone itself (127.0.0.1) -- can do everything
    edit    a guest whose invite code said "edit"
    play    a guest who may join the world and press keys
    watch   a guest who may only look
"""

import json
import secrets
import socket
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import brain, live, status, tiles
from .world import COLORS

ROOT = Path(__file__).resolve().parent.parent
EDITOR = ROOT / "index.html"
WORLD3D = ROOT / "world3d.html"

MAY_EDIT = ("owner", "edit")
MAY_PLAY = ("owner", "edit", "play")
MAY_LOOK = ("owner", "edit", "play", "watch")

# Who counts as the owner. When Spark is only listening to this phone, being on
# this phone is proof enough. The moment it is shared -- and especially behind a
# tunnel, where every visitor arrives looking like 127.0.0.1 -- that stops being
# true, so the owner has to present a key printed in the terminal instead.
OWNER_KEY = ""
LOOPBACK_IS_OWNER = True
OWNER_URL = ""          # the address that makes you the owner, once serving


def export_static():
    """Write the files the page needs when no server is running.

    GitHub Pages can only serve static files, so the tile catalogue and the
    game list get baked out to disk. Re-run after adding a tile.
    """
    (ROOT / "tiles.json").write_text(json.dumps(catalog(), indent=2))
    names = [p.stem for p in brain.list_games()]
    (brain.GAMES_DIR / "index.json").write_text(json.dumps(names, indent=2))
    return names


def catalog():
    """The tile registries, as JSON -- this is what draws the palette."""
    def pack(registry):
        return [{
            "id": tile.id,
            "label": tile.label,
            "params": [{"name": p.name, "prompt": p.prompt, "kind": p.kind,
                        "choices": list(p.choices), "default": p.default}
                       for p in tile.params],
        } for tile in registry.values()]

    return {"sensors": pack(tiles.SENSORS), "actions": pack(tiles.ACTIONS),
            "colors": list(COLORS), "directions": tiles.DIRECTIONS,
            "bearings": tiles.BEARINGS, "keys": tiles.KEYS}


def lan_address(port):
    """The address to read out to someone on the same wifi."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("10.255.255.255", 1))     # no packets are actually sent
        host = probe.getsockname()[0]
    except OSError:
        host = "127.0.0.1"
    finally:
        probe.close()
    return "http://%s:%d/" % (host, port)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass                                    # keep the terminal quiet

    # -- who is asking ----------------------------------------------------

    def caller(self):
        """Returns (role, player)."""
        if OWNER_KEY and self.headers.get("X-Spark-Owner", "") == OWNER_KEY:
            return "owner", None
        if LOOPBACK_IS_OWNER and self.client_address[0] in ("127.0.0.1", "::1"):
            return "owner", None
        token = self.headers.get("X-Spark-Token", "")
        player = live.SESSION.who(token)
        if player is None:
            return "none", None
        return player.role, player

    def allow(self, roles):
        role, player = self.caller()
        if role in roles:
            return player, True
        self.send_json({"error": "not allowed", "role": role}, 403)
        return None, False

    # -- replies ----------------------------------------------------------

    def send_json(self, payload, code=200):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path):
        if not path.exists():
            self.send_error(404, "%s is missing" % path.name)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return None

    # -- routes -----------------------------------------------------------

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        status.note_browser()
        path = url.path

        if path in ("/", "/index.html"):
            return self.send_file(EDITOR)
        # The 3D view. Handing over the page itself is no more of a door than
        # handing over the editor: it holds no game data, and everything it
        # asks for afterwards -- api/live, api/key -- is checked by role like
        # every other route. A stranger who opens it gets the same nothing.
        if path in ("/3d", "/world3d.html"):
            return self.send_file(WORLD3D)
        if path == "/api/tiles":
            return self.send_json(catalog())
        if path == "/api/status":
            return self.send_json(status.probe())

        if path == "/api/live":
            player, ok = self.allow(MAY_LOOK)
            return self.send_json(live.SESSION.snapshot(player)) if ok else None

        if path == "/api/host/invites":
            _, ok = self.allow(("owner",))
            if not ok:
                return
            return self.send_json({
                "invites": [i.public() for i in live.SESSION.invites.values()],
                "people": live.SESSION._people(),
                "join_url": lan_address(self.server.server_address[1]),
                "running": live.SESSION.running,
                "game": live.SESSION.game_name})

        if path == "/api/games":
            _, ok = self.allow(MAY_EDIT)
            return self.send_json([p.stem for p in brain.list_games()]) if ok else None

        if path == "/api/game":
            _, ok = self.allow(MAY_EDIT)
            if not ok:
                return
            name = (query.get("name") or [""])[0]
            path_ = brain.GAMES_DIR / (name + ".json")
            if not name or not path_.exists():
                return self.send_json({"error": "no such game"}, 404)
            return self.send_json(brain.load(path_))

        self.send_error(404)

    def do_POST(self):
        url = urlparse(self.path)
        status.note_browser()
        path, sent = url.path, self.body()
        if sent is None:
            return self.send_json({"error": "bad json"}, 400)

        if path == "/api/join":
            player, why = live.SESSION.join(sent.get("code"), sent.get("name"))
            if player is None:
                return self.send_json({"error": why}, 403)
            return self.send_json({"token": player.token, "role": player.role,
                                   "name": player.name})

        if path == "/api/key":
            player, ok = self.allow(MAY_PLAY)
            if not ok:
                return
            keys = sent.get("keys") or []
            if player is None:                          # the host's own browser
                with live.SESSION.lock:
                    if live.SESSION.world:
                        live.SESSION.world.keys = set(keys)
            else:
                live.SESSION.press(player, keys)
            return self.send_json({"ok": True})

        if path.startswith("/api/host/"):
            _, ok = self.allow(("owner",))
            if not ok:
                return
            what = path[len("/api/host/"):]
            if what == "start":
                name = sent.get("game") or ""
                if not (brain.GAMES_DIR / (name + ".json")).exists():
                    return self.send_json({"error": "no such game"}, 404)
                live.SESSION.start(name)
                return self.send_json({"running": True, "game": name})
            if what == "stop":
                live.SESSION.stop()
                return self.send_json({"running": False})
            if what == "invite":
                invite = live.SESSION.invite(
                    sent.get("role", "watch"), sent.get("character", "own"),
                    sent.get("note", ""), int(sent.get("uses", 0) or 0))
                return self.send_json(invite.public())
            if what == "revoke":
                return self.send_json({"revoked":
                                       live.SESSION.revoke(sent.get("code", ""))})
            return self.send_error(404)

        if path == "/api/game":
            _, ok = self.allow(MAY_EDIT)
            if not ok:
                return
            name = str(sent.get("name", "")).strip()
            # keep saves inside games/ -- no path tricks from the page
            safe = "".join(c for c in name if c.isalnum() or c in "-_ ").strip()
            if not safe:
                return self.send_json({"error": "give the game a name"}, 400)
            sent["name"] = safe
            saved = brain.save(sent, brain.GAMES_DIR / (safe + ".json"))
            export_static()                     # keep the offline listing fresh
            return self.send_json({"saved": str(saved), "name": safe})

        self.send_error(404)

    def do_DELETE(self):
        url = urlparse(self.path)
        status.note_browser()
        if url.path != "/api/game":
            return self.send_error(404)
        _, ok = self.allow(MAY_EDIT)
        if not ok:
            return
        name = (parse_qs(url.query).get("name") or [""])[0]
        path = brain.GAMES_DIR / (name + ".json")
        if not name or path.parent != brain.GAMES_DIR or not path.exists():
            return self.send_json({"error": "no such game"}, 404)
        path.unlink()
        export_static()
        return self.send_json({"deleted": name})


def serve(port=8765, open_browser=True, bind="127.0.0.1", public=False,
          quiet=False):
    global OWNER_KEY, LOOPBACK_IS_OWNER, OWNER_URL
    export_static()
    status.note_server(port)
    shared = bind not in ("127.0.0.1", "localhost")
    OWNER_KEY = secrets.token_urlsafe(12)
    # Shared means strangers may be arriving; then loopback proves nothing.
    LOOPBACK_IS_OWNER = not shared

    with ThreadingHTTPServer((bind, port), Handler) as httpd:
        local = "http://127.0.0.1:%d/" % port
        owner_url = local + "#owner=" + OWNER_KEY
        OWNER_URL = owner_url
        say = (lambda *a: None) if quiet else print
        say(status.line())
        if shared:
            say("You are hosting. Open this on THIS phone to be in charge:")
            say("  " + owner_url)
            say("Others on this wifi go to " + lan_address(port))
            say("and type an invite code. Make codes from the host panel.")
        else:
            say("Spark editor running at " + local)
            say("only this phone can reach it -- use `spark.py host` to share")
        link = None
        if public:
            from . import tunnel
            if not tunnel.available():
                say("\n" + tunnel.advice() + "\n")
            else:
                say("opening a public address, this takes a moment...")
                link = tunnel.Tunnel(port)
                address = link.start()
                if address:
                    status.note_tunnel(link.name, address)
                    say("anyone anywhere can join at " + address)
                    say("(that address dies when you stop Spark)")
                else:
                    say("the tunnel did not come up; wifi still works")
                    link = None

        say("games folder: %s" % brain.GAMES_DIR)
        say("press ctrl-c to stop")
        if open_browser:
            try:
                subprocess.run(["termux-open-url", owner_url], timeout=5,
                               capture_output=True)
            except (FileNotFoundError, subprocess.SubprocessError):
                say("(open that address in your browser)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
        finally:
            if link:
                link.stop()
            live.SESSION.stop()
            status.clear_tunnel()
            status.clear_players()
            status.clear_server()
