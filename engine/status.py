"""Where is Spark running right now?

Three plain flags, shown above every prompt and in the browser header:

    Github   your commits are all pushed to a remote
    Browser  an editor page has talked to the local server in the last 90s
    Local    the Python engine is here and usable offline right now

The browser flag needs the server and the terminal to talk, so the server
leaves a small note in .spark-state.json (gitignored) and the terminal reads it.
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
    return {
        "github": github_ok(),
        "browser": (time.time() - state.get("browser_seen", 0) < FRESH
                    and server_listening(state.get("port"))),
        "local": (ROOT / "spark.py").exists(),
    }


def line(color=True):
    flags = probe()
    parts = []
    for name in ("github", "browser", "local"):
        mark = "T" if flags[name] else "F"
        if color:
            mark = (GREEN if flags[name] else GREY) + mark + OFF
        parts.append("%s %s" % (name.capitalize(), mark))
    return "Spark exe  " + "  ".join(parts)
