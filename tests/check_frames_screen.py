#!/usr/bin/env python3
"""Check the terminal builder's own Frames screen -- the "built in
utility" for authoring a character's multi-cell ASCII sprite, one pixel
(grid position, letter, colour) at a time, one frame at a time.

    python3 tests/check_frames_screen.py

Same trick as tests/check_menu.py: drives a real pseudo-terminal, since
this is exactly the difference a plain pipe can't tell apart from a
real one, and the big-picture menu this screen is built from only
engages on a real terminal.
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

from engine.builder import _frame_preview                          # noqa: E402

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


print("_frame_preview: a small colourised look at one frame's own pixels")

check("an empty frame says so rather than showing nothing at all",
      _frame_preview([]) == ["  (empty -- the plain glyph shows until you add a pixel)"])

one = _frame_preview([{"dx": 0, "dy": 0, "glyph": "X", "color": "white"}])
check("a single pixel at the origin is one row, one column",
      len(one) == 1 and "X" in one[0], one)

two_wide = _frame_preview([
    {"dx": 0, "dy": 0, "glyph": "/", "color": "white"},
    {"dx": 1, "dy": 0, "glyph": "\\", "color": "white"},
])
check("two pixels side by side land on the same row, in order",
      len(two_wide) == 1 and two_wide[0].index("/") < two_wide[0].index("\\"), two_wide)

negative = _frame_preview([
    {"dx": -1, "dy": -1, "glyph": "A", "color": "white"},
    {"dx": 1, "dy": 1, "glyph": "B", "color": "white"},
])
# y spans -1..1, so the bounding box is 3 rows tall -- the empty middle
# row (dy=0, nothing placed there) has to stay, not collapse away, or
# A and B's actual relative spacing would be lost.
check("negative offsets (up/left of centre) still place correctly, "
      "preserving the gap between them",
      len(negative) == 3 and "A" in negative[0] and negative[1].strip() == ""
      and "B" in negative[2], negative)

print("\n%d passed, %d failed (pure logic)\n" % (passed, failed))

# -- end to end, through a real pty ----------------------------------------

UP, DOWN, ENTER = b"\x1b[A", b"\x1b[B", b"\r"


class Session:
    def __init__(self, code, rows=40, cols=80):
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


def scratch_game():
    """A private copy of chase.json this whole file plays against,
    cleaned up (even on a failure) by the caller's own try/finally.

    Critically, this also renames the copy's own internal "name" field
    -- editor_screen's own "save" always writes to
    games/<project name>.json, using the name INSIDE the project, not
    whatever file it happened to be loaded from. Skipping this step
    would make every "save" below silently overwrite the real, shared
    games/chase.json instead of this scratch copy -- exactly the
    mistake made once already while first hand-testing this feature,
    caught only by noticing `git diff` on a file this session never
    meant to touch. Never repeat that."""
    name = "_frametest_%d" % os.getpid()
    path = ROOT / "games" / (name + ".json")
    data = json.loads((ROOT / "games" / "chase.json").read_text())
    data["name"] = name
    path.write_text(json.dumps(data))
    return path


def probe(path):
    return (
        "import sys; sys.path.insert(0, %r)\n"
        "from engine import brain, builder\n"
        "p = brain.load(%r)\n"
        "builder.main_menu(p)\n"
    ) % (str(ROOT), str(path))


def back(s, wait=0.3):
    """Selects whatever this screen's own back_label ("done", almost
    always) is, regardless of how many real options sit above it in
    the list -- the big-picture menu always appends back_label as the
    LAST item, and a fresh menu() call always starts back on the FIRST
    one selected, so pressing up once from there wraps straight to the
    last, whatever that list's own length happens to be. Much more
    robust than counting how many downs a given screen needs by hand."""
    s.send(UP, wait=0.1)
    s.send(ENTER, wait=wait)


path = scratch_game()
try:
    print("adding a frame and a pixel, then confirming it's actually saved to disk")
    s = Session(probe(path))
    s.drain(0.3)
    s.send(DOWN); s.drain(0.2)          # title -> editor
    s.send(ENTER); s.drain(0.3)
    s.send(ENTER); s.drain(0.3)          # editor -> characters and their brains
    s.send(DOWN); s.drain(0.2)          # -> edit a character
    s.send(ENTER); s.drain(0.3)
    s.send(ENTER); s.drain(0.3)          # -> hero (first one)
    s.send(DOWN); s.drain(0.2)          # -> edit its frames
    out = s.drain(0.3)
    s.send(ENTER)
    out = s.drain(0.4)
    check("the frames screen opens, empty, naming the character",
          "Frames for 'hero'" in out and "0 saved" in out, out[-400:])

    s.send(ENTER)                         # add a new frame
    out = s.drain(0.4)
    check("a fresh, empty frame opens straight into its own edit screen",
          "0 pixels" in out, out[-400:])

    s.send(ENTER)                         # add a pixel
    s.drain(0.2)
    s.send(b"2\r"); s.drain(0.2)          # dx
    s.send(b"-1\r"); s.drain(0.2)         # dy
    s.send(b"X\r"); s.drain(0.2)          # glyph
    # colour: cyan (7th in the list). This is the raw big-menu, not a
    # cooked prompt -- a bare digit 1-9 selects immediately, no Enter
    # needed (and a trailing one here would be a stray keystroke that
    # bleeds into whatever screen comes right after).
    s.send(b"7")
    out = s.drain(0.5)
    check("the new pixel shows up in the frame's own list",
          "(2,-1) 'X' cyan" in out, out[-500:])

    back(s)                               # done (edit frame) -> back to frames list
    out = s.drain(0.3)
    check("the frames list now shows 1 frame, 1 pixel",
          "1 saved" in out and "1 pixel" in out, out[-400:])

    back(s)                               # done (frames) -> back to character screen
    out = s.drain(0.3)
    check("the character screen's own summary line picked it up",
          "sprite frames: 1" in out, out[-400:])

    # Back out the rest of the way and save.
    back(s)                               # done (character)
    back(s)                               # done (characters) -> back in editor
    out = s.drain(0.3)
    # editor_screen's own options are listed in a known, fixed order:
    # characters, your own tiles, world settings, save, rename, GitHub,
    # invite -- "save" is the 4th, so 3 downs from the top selection
    # get there without needing to parse the render.
    s.send(DOWN); s.send(DOWN); s.send(DOWN)
    out = s.drain(0.3)
    check("arrowed down to \"save\" specifically",
          "\x1b[1;36m > \x1b[0m\x1b[1;36msave" in out, out[-400:])
    s.send(ENTER)
    out = s.drain(0.4)
    check("saved", "Saved" in out, out[-300:])
    s.send(ENTER)   # "press enter" past the confirmation
    s.drain(0.3)

    s.close()

    saved = json.loads(path.read_text())
    hero = next(c for c in saved["characters"] if c["kind"] == "hero")
    check("the pixel is really in the saved file, not just on screen",
          hero.get("frames") == [[{"dx": 2, "dy": -1, "glyph": "X", "color": "cyan"}]],
          hero.get("frames"))

    print("\nopening Frames and backing straight out (no frames added) leaves no trace")
    s = Session(probe(path))
    s.drain(0.3)
    s.send(DOWN); s.drain(0.2)
    s.send(ENTER); s.drain(0.3)
    s.send(ENTER); s.drain(0.3)
    s.send(DOWN); s.drain(0.2)
    s.send(ENTER); s.drain(0.3)
    s.send(DOWN); s.drain(0.2)            # -> apple (second character)
    s.send(ENTER); s.drain(0.3)
    s.send(DOWN); s.drain(0.2)            # -> edit its frames
    s.send(ENTER); s.drain(0.3)
    back(s)                               # done immediately, nothing added
    out = s.drain(0.3)
    check("back on the character screen, no frames were added",
          "sprite frames: 0" in out, out[-400:])

    back(s)                               # done (character)
    back(s)                               # done (characters) -> back in editor
    s.send(DOWN); s.send(DOWN); s.send(DOWN)   # -> save (see the comment above)
    s.drain(0.3)
    s.send(ENTER)
    s.drain(0.4)
    s.send(ENTER)   # "press enter" past the "Saved" confirmation
    s.drain(0.3)
    s.close()

    saved2 = json.loads(path.read_text())
    apple = next(c for c in saved2["characters"] if c["kind"] == "apple")
    check("no empty \"frames\": [] left cluttering a character that never used it",
          "frames" not in apple, apple)
    check("the earlier character's own frame is still there, untouched",
          next(c for c in saved2["characters"] if c["kind"] == "hero").get("frames")
          == [[{"dx": 2, "dy": -1, "glyph": "X", "color": "cyan"}]])
finally:
    path.unlink(missing_ok=True)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
