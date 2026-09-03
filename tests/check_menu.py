#!/usr/bin/env python3
"""Check the terminal's "big picture" menu: arrow keys, digits, escape, and
the fallback to a plain numbered list wherever a real terminal isn't there.

    python3 tests/check_menu.py

builder.menu() behaves differently depending on whether it is actually
talking to a terminal, which os.pipe()-based stdin/stdout (what most testing
would reach for) cannot tell apart from a real one the way a pty can -- so
this drives it through an actual pseudo-terminal, the same way a phone's
terminal app would, and separately confirms the classic fallback over plain
pipes.
"""

import os
import pty
import select
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


# -- driving a real pty --------------------------------------------------

UP, DOWN, ENTER, ESCAPE = b"\x1b[A", b"\x1b[B", b"\r", b"\x1b"


class Session:
    """One child process, talking to us over a real pseudo-terminal."""

    def __init__(self, code):
        self.master, slave = pty.openpty()
        self.proc = subprocess.Popen(
            [sys.executable, "-c", code], cwd=str(ROOT),
            stdin=slave, stdout=slave, stderr=slave, close_fds=True)
        os.close(slave)
        time.sleep(0.3)

    def send(self, keys, wait=0.12):
        os.write(self.master, keys)
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


def menu_probe():
    """A tiny child that opens one menu() call and prints what it returns --
    reused by every arrow/digit/escape case below."""
    return (
        "import sys; sys.path.insert(0, %r)\n"
        "from engine import builder\n"
        "r = builder.menu(['alpha', 'beta', 'gamma'])\n"
        "print('RESULT=' + repr(r))\n"
    ) % str(ROOT)


# -- arrow keys move the highlight, enter picks it ------------------------

print("arrow keys and enter, in a real pty")
s = Session(menu_probe())
s.send(DOWN)
s.send(DOWN)
s.send(ENTER)
out = s.drain(0.6)
s.close()
check("down, down, enter lands on the third option (gamma, index 2)",
      "RESULT=2" in out, out[-120:])
check("the highlight actually moved -- 'gamma' appears reverse-styled",
      "\x1b[1;36m > \x1b[0m\x1b[1;36mgamma" in out, out)

# -- a digit jumps straight there ------------------------------------------

print("\na digit jumps straight to that option")
s = Session(menu_probe())
s.send(b"3")
s.send(ENTER)
out = s.drain(0.6)
s.close()
check("'3' then enter picks the third option without arrowing there",
      "RESULT=2" in out, out[-120:])

# -- escape and 0 both mean back -------------------------------------------

print("\nescape and 0 both back out")
for key, label in ((ESCAPE, "escape"), (b"0", "the digit 0")):
    s = Session(menu_probe())
    s.send(key)
    out = s.drain(0.6)
    s.close()
    check(label + " returns None (back), not a crash",
          "RESULT=None" in out, out[-120:])

# -- no real terminal: falls back to the classic numbered list -------------

print("\nno real terminal -> the classic numbered list, unchanged")
proc = subprocess.Popen(
    [sys.executable, "-c", menu_probe()], cwd=str(ROOT),
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out, _ = proc.communicate(b"2\n", timeout=5)
text = out.decode("utf-8", "replace")
check("piped input never sees the big-picture menu",
      "1;36m" not in text, text)
check("typing a number at the classic prompt still works",
      "RESULT=1" in text, text)
check("the classic list itself is still there to type against",
      "1. alpha" in text and "0. back" in text, text)

# -- SPARK_PLAIN opts out even on a real terminal --------------------------

print("\nSPARK_PLAIN forces the classic list even on a real pty")
master, slave = pty.openpty()
env = dict(os.environ, SPARK_PLAIN="1")
proc = subprocess.Popen([sys.executable, "-c", menu_probe()], cwd=str(ROOT),
                         env=env, stdin=slave, stdout=slave, stderr=slave,
                         close_fds=True)
os.close(slave)
time.sleep(0.3)
os.write(master, b"2\n")
time.sleep(0.3)
out = b""
while select.select([master], [], [], 0.3)[0]:
    try:
        out += os.read(master, 4096)
    except OSError:
        break
proc.wait(timeout=5)
os.close(master)
text = out.decode("utf-8", "replace")
check("SPARK_PLAIN=1 skips the big-picture menu on a real terminal",
      "1;36m" not in text, text)
check("...and the classic prompt still works there",
      "RESULT=1" in text, text)

# -- the title screen and the editor behind it, end to end -----------------

print("\nthe title screen: play/editor/new/open, and editor one tap in")
child = (
    "import sys; sys.path.insert(0, %r)\n"
    "from engine import brain, builder\n"
    "p = brain.load('games/chase.json')\n"
    "builder.main_menu(p)\n"
) % str(ROOT)
s = Session(child)
title = s.drain(0.5)
check("the title screen shows the big SPARK logo",
      "####" in title, title)
check("...and offers editor, not the old flat list",
      "editor" in title and "characters and their brains" not in title, title)

s.send(DOWN)          # play it -> editor
s.send(ENTER)
opened = s.drain(0.5)
check("picking editor opens the editor screen",
      "Editor for 'chase'" in opened, opened)
check("...with the game-changing options moved in here",
      "characters and their brains" in opened, opened)

s.send(b"0")           # back to the title screen
back = s.drain(0.5)
check("'0' from the editor returns to the title screen",
      "play it" in back and "editor" in back, back)

s.send(ESCAPE)          # quit
bye = s.drain(0.5)
check("escape at the title screen quits cleanly", "bye" in bye, bye)
s.close()
check("...and the process actually exited", s.proc.returncode == 0, s.proc.returncode)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
