#!/usr/bin/env python3
"""Check the terminal player's own "/" command line: pressing "/" during
play swallows nothing gameplay would have used it for (nothing does --
see engine/runner.py's Keyboard.pause/resume comments), drops into a
real, cooked-mode text line so the phone's own keyboard/text box behaves
normally, runs the command, and shows the result as its own screen
before any key brings the running world back.

    python3 tests/check_chat_break.py

Same trick as tests/check_menu.py: drives a real pseudo-terminal, since
this is exactly the difference a plain pipe can't tell apart from a real
terminal (isatty()), and this feature only engages on a real one.
"""

import os
import pty
import select
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.runner import run_local_command, _local_help_lines   # noqa: E402

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


# -- the pure logic, no terminal involved ----------------------------------

print("run_local_command: purely local, no server, deliberately a small set")

game_with_help = {"help": "line one\nline two"}
kind, lines = run_local_command("/help", game_with_help)
check("/help shows the game's own text", kind == "show" and "line one" in lines, lines)
check("...both lines of it", "line two" in lines, lines)

kind, lines = run_local_command("", {})
check("blank input is treated as /help, not an error", kind == "show", (kind, lines))
check("a game with no help field still gets the command list",
      any("/help" in l for l in lines), lines)

kind, lines = run_local_command("/quit", {})
check("/quit signals quit", kind == "quit" and lines is None)
kind, lines = run_local_command("/q", {})
check("/q is the same as /quit", kind == "quit")

kind, lines = run_local_command("/nonsense", {})
check("an unknown command says so, doesn't crash",
      kind == "show" and any("no such command" in l for l in lines), lines)

print("\n%d passed, %d failed (pure logic)\n" % (passed, failed))

# -- end to end, through a real pty ----------------------------------------

UP = b"\x1b[A"


class Session:
    def __init__(self, code):
        self.master, slave = pty.openpty()
        self.proc = subprocess.Popen(
            [sys.executable, "-c", code], cwd=str(ROOT),
            stdin=slave, stdout=slave, stderr=slave, close_fds=True)
        os.close(slave)
        time.sleep(0.3)

    def send(self, data, wait=0.15):
        os.write(self.master, data)
        time.sleep(wait)

    def drain(self, timeout=0.4):
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


play_probe = (
    "import sys; sys.path.insert(0, %r)\n"
    "from engine import brain, runner\n"
    "p = brain.load('games/outpost.json')\n"
    "runner.play(p)\n"
) % str(ROOT)

print("pressing / during play: a real cooked line, then its own result screen")
s = Session(play_probe)
s.drain(0.3)   # let the game render its first frame
s.send(b"/")
s.drain(0.2)
s.send(b"help\r")
out = s.drain(0.6)
check("the game's own help text made it onto the result screen",
      "frontier camp" in out, out[-400:])
check("...and the chat header too, a screen distinct from the running world",
      "chat" in out.lower(), out[-400:])

s.send(b" ")   # any key dismisses the result screen
back = s.drain(0.6)
check("a key afterward goes back to the running game (the world redraws)",
      "score" in back, back[-200:])

s.send(b"q")
s.drain(0.4)
s.send(b"\r")   # play()'s own "press enter to go back to the menu" prompt
bye = s.drain(0.6)
s.close()
check("q still quits normally afterward", s.proc.returncode == 0, s.proc.returncode)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
