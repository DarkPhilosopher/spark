"""A tiny local server so the browser editor can read and write games/.

Binds to 127.0.0.1 only -- nothing outside the phone can reach it.
"""

import json
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import brain, status, tiles
from .world import COLORS

ROOT = Path(__file__).resolve().parent.parent
EDITOR = ROOT / "index.html"


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
            "colors": list(COLORS), "directions": tiles.DIRECTIONS, "keys": tiles.KEYS}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass                                    # keep the terminal quiet

    def send_json(self, payload, code=200):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path):
        if not path.exists():
            self.send_error(404, "editor.html is missing")
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        status.note_browser()

        if url.path == "/api/status":
            return self.send_json(status.probe())
        if url.path in ("/", "/index.html"):
            return self.send_file(EDITOR)
        if url.path == "/api/tiles":
            return self.send_json(catalog())
        if url.path == "/api/games":
            return self.send_json([p.stem for p in brain.list_games()])
        if url.path == "/api/game":
            name = (query.get("name") or [""])[0]
            path = brain.GAMES_DIR / (name + ".json")
            if not name or not path.exists():
                return self.send_json({"error": "no such game"}, 404)
            return self.send_json(brain.load(path))
        self.send_error(404)

    def do_DELETE(self):
        url = urlparse(self.path)
        status.note_browser()
        if url.path != "/api/game":
            return self.send_error(404)
        name = (parse_qs(url.query).get("name") or [""])[0]
        path = brain.GAMES_DIR / (name + ".json")
        if not name or path.parent != brain.GAMES_DIR or not path.exists():
            return self.send_json({"error": "no such game"}, 404)
        path.unlink()
        export_static()
        return self.send_json({"deleted": name})

    def do_POST(self):
        url = urlparse(self.path)
        status.note_browser()
        if url.path != "/api/game":
            return self.send_error(404)
        length = int(self.headers.get("Content-Length", 0))
        try:
            project = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self.send_json({"error": "bad json"}, 400)

        name = str(project.get("name", "")).strip()
        # keep saves inside games/ -- no path tricks from the page
        safe = "".join(c for c in name if c.isalnum() or c in "-_ ").strip()
        if not safe:
            return self.send_json({"error": "give the game a name"}, 400)
        project["name"] = safe
        path = brain.save(project, brain.GAMES_DIR / (safe + ".json"))
        export_static()                         # keep the offline listing fresh
        return self.send_json({"saved": str(path), "name": safe})


def serve(port=8765, open_browser=True):
    export_static()
    status.note_server(port)
    address = ("127.0.0.1", port)
    with ThreadingHTTPServer(address, Handler) as httpd:
        url = "http://127.0.0.1:%d/" % port
        print(status.line())
        print("Spark editor running at " + url)
        print("games folder: %s" % brain.GAMES_DIR)
        print("press ctrl-c to stop")
        if open_browser:
            try:
                subprocess.run(["termux-open-url", url], timeout=5,
                               capture_output=True)
            except (FileNotFoundError, subprocess.SubprocessError):
                print("(open that address in your browser)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
        finally:
            status.clear_server()
