#!/usr/bin/env python3
"""Check the terminal's own entities menu -- pressing "p" during play for
an arrow-key alternative to typing /list, /name, /recruit, /dismiss and
/attack's coordinates by hand, plus a separate page to spawn a fresh
entity of any kind the game defines.

    python3 tests/check_entities_screen.py

Same trick as tests/check_menu.py and tests/check_frames_screen.py:
drives a real pseudo-terminal, since this is exactly the difference a
plain pipe can't tell apart from a real one, and the big-picture menu
this screen is built from (see builder.menu()) only engages on a real
terminal. Not sharing that file's own Session class, by established
precedent -- see check_lead.py's own long comment for why a small
self-contained copy per file beats a shared one here.
"""

import fcntl
import json
import os
import pty
import select
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


ENTER = b"\r"
UP = b"\x1b[A"


class Session:
    def __init__(self, code, rows=40, cols=100):
        self.master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.proc = subprocess.Popen(
            [sys.executable, "-c", code], cwd=str(ROOT),
            stdin=slave, stdout=slave, stderr=slave, close_fds=True)
        os.close(slave)
        select.select([self.master], [], [], 1.0)

    def send(self, data, wait=0.15):
        os.write(self.master, data)
        time.sleep(wait)

    def drain(self, timeout=0.5):
        out = b""
        end = time.time() + timeout
        while time.time() < end:
            ready, _, _ = select.select([self.master], [], [], 0.1)
            if self.master not in ready:
                continue
            try:
                chunk = os.read(self.master, 4096)
            except OSError:
                break
            if not chunk:
                break
            out += chunk
        return out.decode("utf-8", "replace")

    def close(self):
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        os.close(self.master)


def back(s, wait=0.3):
    """Selects whatever this screen's own back_label is, regardless of
    how many real options sit above it -- a fresh menu() call always
    starts on the FIRST item, and up from there always wraps to the
    LAST (the back label). Same trick check_frames_screen.py uses."""
    s.send(UP, wait=0.1)
    s.send(ENTER, wait=wait)


def scratch_game():
    """A tiny, private fixture -- not one of the shared games/*.json
    fixtures, so there's nothing here another test could collide with.
    A 2x2 world guarantees the hero and the companion always spawn
    within one square of each other (the biggest possible gap on a
    2x2 grid is exactly 1), so /recruit-style adjacency never flakes
    on wherever they happened to land."""
    name = "_entitiestest_%d" % os.getpid()
    path = ROOT / "games" / (name + ".json")
    data = {
        "name": name,
        "world": {"width": 2, "height": 2, "speed": 6},
        "characters": [
            {"kind": "hero", "glyph": "@", "color": "green", "role": "player",
             "count": 1, "brain": []},
            {"kind": "companion", "glyph": "c", "color": "yellow", "role": "prop",
             "count": 1, "brain": []},
            {"kind": "wall", "glyph": "#", "color": "grey", "role": "prop",
             "count": 0, "brain": []},
        ],
    }
    path.write_text(json.dumps(data))
    return path


def probe(path):
    return (
        "import sys; sys.path.insert(0, %r)\n"
        "from engine import brain, runner\n"
        "p = brain.load(%r)\n"
        "runner.play(p)\n"
    ) % (str(ROOT), str(path))


path = scratch_game()
try:
    print("pressing p during play: the entities menu opens, arrows/digits work")
    s = Session(probe(path))
    s.drain(0.3)   # let the game render its first frame

    s.send(b"p")
    out = s.drain(0.4)
    check("the entities menu opens, a screen distinct from the running world",
          "entities" in out and "score" not in out, out[-400:])
    check("both pages are offered", "existing entities" in out and "spawn a new entity" in out,
          out[-400:])

    print("\nspawn a new entity: a separate page, every kind the game defines")
    s.send(b"2")   # jump straight to "spawn a new entity"
    out = s.drain(0.4)
    check("lists every kind in the roster", all(k in out for k in ("hero", "companion", "wall")),
          out[-400:])

    s.send(b"3")   # jump straight to "wall" (3rd kind listed)
    out = s.drain(0.4)
    check("a fresh wall actually spawns, and says so",
          "spawned a wall at (" in out, out[-400:])

    s.send(ENTER)   # "enter to continue" -> back to the entities top menu
    out = s.drain(0.4)
    check("back at the entities top menu", "existing entities" in out, out[-400:])

    print("\nexisting entities: every living thing, including the one just spawned")
    s.send(b"1")   # jump straight to "existing entities"
    out = s.drain(0.4)
    check("the fresh wall shows up here too, alongside the hero and companion",
          all(k in out for k in ("hero", "companion", "wall")), out[-400:])

    print("\npicking one opens a real action menu -- name/recruit/dismiss/attack")
    s.send(b"1")   # jump to the first entity listed (sorted by kind: companion, hero, wall)
    out = s.drain(0.4)
    check("shows which entity this is", "companion" in out, out[-400:])
    check("offers all four actions", all(a in out for a in
          ("name it", "recruit it", "dismiss it", "attack it")), out[-400:])

    s.send(b"2")   # recruit it
    out = s.drain(0.4)
    check("recruits it -- guaranteed adjacent on a 2x2 world",
          "recruited the companion at (" in out, out[-400:])

    s.send(ENTER)   # "enter to continue" -> back to this same entity's own action menu
    out = s.drain(0.4)
    check("back on the same entity's action menu, not dumped out to the game",
          "recruit it" in out, out[-400:])

    print("\nbacking all the way out returns to the running game, unharmed")
    back(s)                 # action menu -> existing entities list
    out = s.drain(0.3)
    check("back on the existing-entities list", "existing entities" not in out and
          all(k in out for k in ("hero", "wall")), out[-400:])
    back(s)                 # existing entities -> entities top menu
    out = s.drain(0.3)
    check("back on the entities top menu", "existing entities" in out, out[-400:])
    back(s)                 # entities top menu -> the running game
    out = s.drain(0.4)
    check("the running game is back, redrawn", "score" in out, out[-300:])

    print("\nordinary gameplay still works fine afterward")
    s.send(b"q")
    s.drain(0.4)
    s.send(ENTER)   # play()'s own "press enter to go back to the menu" prompt
    s.close()
    check("the process actually exited", s.proc.returncode == 0, s.proc.returncode)
finally:
    path.unlink(missing_ok=True)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
