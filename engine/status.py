"""Where is Spark running right now?

Four plain flags, shown above every prompt and in the browser header:

    Github      your commits are all pushed to a remote
    Browser     an editor page has talked to the local server in the last 90s
    Local       the Python engine is here and usable offline right now
    Cloudflare  a cloudflared tunnel is up, so anyone anywhere can join

and then a count, which is not a yes-or-no thing:

    Players     how many people are connected to the world right now

The last three need the server and the terminal to talk, so the server leaves a
small note in .spark-state.json (gitignored) and the terminal reads it. The
roster goes in the same note, oldest joiner first, which is what `players` in
the menus prints.
"""

import json
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / ".spark-state.json"
FRESH = 90          # seconds a browser counts as "still there"

GREEN, GREY, OFF = "\033[32m", "\033[90m", "\033[0m"


def _read_state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {}


def _write_state(**changes):
    state = _read_state()
    state.update(changes)
    try:
        STATE.write_text(json.dumps(state))
    except OSError:
        pass


def note_browser():
    """Called by the server whenever a page asks it for something."""
    state = _read_state()
    if time.time() - state.get("browser_seen", 0) > 2:      # throttle writes
        _write_state(browser_seen=time.time())


def note_server(port):
    _write_state(port=port, server_pid_time=time.time())


def clear_server():
    _write_state(port=0)


def note_tunnel(name, url):
    """Called by the server once a tunnel program hands us an address."""
    _write_state(tunnel_name=name, tunnel_url=url)


def clear_tunnel():
    _write_state(tunnel_name="", tunnel_url="")


def note_players(people):
    """Called by the live session whenever somebody joins or leaves.

    `people` is a list of {name, role, game, joined}, and it is the only way a
    second process -- the menus, usually -- can see who is in the world.
    """
    _write_state(players=people)


def clear_players():
    _write_state(players=[])


def players():
    """Who is connected, oldest joiner first. Empty if nothing is serving."""
    state = _read_state()
    if not server_listening(state.get("port")):
        return []
    return _in_join_order(state.get("players"))


def _in_join_order(people):
    """Sort defensively: the note is written by another process, so trust its
    timestamps rather than the order they happen to arrive in."""
    if not isinstance(people, list):
        return []
    return sorted((p for p in people if isinstance(p, dict)),
                  key=lambda p: p.get("joined") or 0)


def _git(*args):
    try:
        done = subprocess.run(["git", "-C", str(ROOT), *args],
                              capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def github_ok():
    if _git("rev-parse", "--git-dir") is None:
        return False
    if not _git("remote"):
        return False
    branch = (_git("status", "-sb") or "").splitlines()
    if not branch:
        return False
    head = branch[0]
    if "..." not in head:           # no upstream yet -- never pushed
        return False
    return "[ahead" not in head     # unpushed commits means not in sync


def server_listening(port):
    if not port:
        return False
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except OSError:
        return False


def probe():
    state = _read_state()
    # Both live flags below mean nothing if the server that wrote them is gone,
    # so one check covers them and a stale note heals itself.
    up = server_listening(state.get("port"))
    return {
        "github": github_ok(),
        "browser": (time.time() - state.get("browser_seen", 0) < FRESH and up),
        "local": (ROOT / "spark.py").exists(),
        "cloudflare": (state.get("tunnel_name") == "cloudflared"
                       and bool(state.get("tunnel_url")) and up),
        "players": len(_in_join_order(state.get("players"))) if up else 0,
    }


def line(color=True):
    flags = probe()
    parts = []
    for name in ("github", "browser", "local", "cloudflare"):
        mark = "T" if flags[name] else "F"
        if color:
            mark = (GREEN if flags[name] else GREY) + mark + OFF
        parts.append("%s %s" % (name.capitalize(), mark))
    count = str(flags["players"])
    if color:
        count = (GREEN if flags["players"] else GREY) + count + OFF
    parts.append("Players " + count)
    return "Spark exe  " + "  ".join(parts)
