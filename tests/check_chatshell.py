#!/usr/bin/env python3
"""Check engine/chatshell.py -- Spark as one ASCII display and one
never-cleared chat log, navigated by typed commands, replacing
builder.py's arrow-key menus for the flows it covers (games, characters,
brain rows, world settings, play).

    python3 tests/check_chatshell.py

Every command is a plain function of (state, rest), so almost all of
this is pure-logic, no terminal needed -- see check_chat_break.py's own
docstring for why check_engines.py's shared snapshot harness isn't
extended for this kind of thing either. The one pty section at the
bottom drives the real terminal loop end to end.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import chatshell, brain                            # noqa: E402

passed = failed = 0


def check(name, condition, extra=""):
    global passed, failed
    if condition:
        passed += 1
        print("  ok   " + name)
    else:
        failed += 1
        print("  FAIL " + name + ("  -> " + str(extra) if extra else ""))


def say(state, line):
    """One typed line, run exactly the way the real loop would."""
    return chatshell.run_command(state, line)


print("run_command: dispatch, /help on a blank line, an unknown command says so")
s = chatshell.new_state()
check("blank line is /help", say(s, "") == chatshell.cmd_help(s, ""))
check("bare / is also /help", say(s, "/") == chatshell.cmd_help(s, ""))
out = say(s, "/nonsense")
check("an unknown command says so, doesn't crash", "no such command" in out[0], out)
check("running a command logs both what was said and its result",
      any(l.startswith("you: /nonsense") for l in s["history"]) and
      any("no such command" in l for l in s["history"]), s["history"])

print("\nat the top level: /games, /new, /open")
s = chatshell.new_state()
check("no project open -- most commands say so",
      "open a game first" in chatshell.cmd_characters(s, "")[0])
out = say(s, "/new")
check("a blank name is refused", "try: /new" in out[0], out)
out = say(s, "/new probe_%d" % os.getpid())
check("starts a new project", s["project"] is not None and
      s["project"]["name"] == "probe_%d" % os.getpid(), s["project"])
check("brand new, no characters yet", s["project"]["characters"] == [])

s2 = chatshell.new_state()
out = say(s2, "/open definitely_not_a_real_game_xyz")
check("opening a game that doesn't exist says so, not a crash",
      "no game called" in out[0], out)

print("\n/back walks out one level at a time: row -> character -> game -> top")
s = chatshell.new_state()
say(s, "/new probe2_%d" % os.getpid())
say(s, "/newchar hero")
say(s, "/newrow")
check("building a row", s["building"] is not None)
say(s, "/back")
check("back cancels the row being built, keeps the character focused",
      s["building"] is None and s["focus"] == "hero", s)
say(s, "/back")
check("back un-focuses the character, keeps the game open",
      s["focus"] is None and s["project"] is not None, s)
say(s, "/back")
check("back closes the game entirely", s["project"] is None, s)
out = say(s, "/back")
check("back at the top already, says so rather than crashing",
      "already at the top" in out[0], out)

print("\ncharacters: /newchar, /character, listing, duplicate names refused")
s = chatshell.new_state()
say(s, "/new probe3_%d" % os.getpid())
out = say(s, "/newchar")
check("a blank kind is refused", "try: /newchar" in out[0], out)
say(s, "/newchar bandit")
check("newchar focuses the new character right away", s["focus"] == "bandit")
out = say(s, "/newchar bandit")
check("a duplicate kind is refused", "already exists" in out[0], out)
say(s, "/back")
out = say(s, "/characters")
check("lists what's there", any("bandit" in l for l in out), out)
out = say(s, "/character bandit")
check("focusing an existing character works", s["focus"] == "bandit")
out = say(s, "/character nope")
check("focusing one that doesn't exist says so", "no character called" in out[0], out)

print("\nswitching focus mid-row-build discards the row -- a real bug caught on self-review")
print("(it used to silently attach the half-built row to whichever character ended up")
print("focused next, regardless of who it was actually being built for)")
s = chatshell.new_state()
say(s, "/new probe3b_%d" % os.getpid())
say(s, "/newchar hero")
say(s, "/newrow")
say(s, "/when touch kind=anything")
out = say(s, "/newchar bandit")
check("switching to a newly-made character discards the pending row, and says so",
      s["building"] is None and any("discarded" in l for l in out), out)
say(s, "/done")
hero = next(c for c in s["project"]["characters"] if c["kind"] == "hero")
bandit = next(c for c in s["project"]["characters"] if c["kind"] == "bandit")
check("the row landed on NEITHER character -- it's really gone, not misattached",
      hero["brain"] == [] and bandit["brain"] == [], (hero["brain"], bandit["brain"]))

say(s, "/character hero")
say(s, "/newrow")
say(s, "/when touch kind=anything")
out = say(s, "/character hero")   # re-focusing the SAME character, mid-build
check("re-focusing the character you're ALREADY on doesn't discard anything",
      s["building"] is not None and not any("discarded" in l for l in out), out)
say(s, "/do say text=hi")
say(s, "/done")
check("...and the row completes normally, attached to the right character",
      len(hero["brain"]) == 1, hero["brain"])

say(s, "/newrow")
say(s, "/when touch kind=anything")
out = say(s, "/open definitely_not_a_real_game_xyz")   # fails, but happens BEFORE the check
check("a failed /open doesn't touch the pending row at all",
      s["building"] is not None, s["building"])
out = say(s, "/new probe3c_%d" % os.getpid())
check("but a REAL /open or /new (switching games entirely) does discard it, and says so",
      s["building"] is None and any("discarded" in l for l in out), out)

print("\ncharacter fields: glyph/color/role/count/health/solid, each validated")
s = chatshell.new_state()
say(s, "/new probe4_%d" % os.getpid())
say(s, "/newchar ore")
char = chatshell._current_char(s)
say(s, "/glyph O")
check("glyph set", char["glyph"] == "O")
out = say(s, "/color chartreuse")
check("an invalid colour is refused, lists real ones", "not a colour" in out[0], out)
say(s, "/color yellow")
check("a valid colour (any case) is accepted", char["color"] == "yellow")
say(s, "/color YELLOW")
check("case-insensitive", char["color"] == "yellow")
out = say(s, "/role sidekick")
check("an invalid role is refused", "try: /role" in out[0], out)
say(s, "/role player")
check("role set", char["role"] == "player")
say(s, "/count 5")
check("count set", char["count"] == 5)
out = say(s, "/count -3")
check("count never goes negative", char["count"] == 0, char["count"])
say(s, "/health 20")
check("health set", char["health"] == 20)
out = say(s, "/health 0")
check("health never goes below 1", char["health"] == 1, char["health"])
say(s, "/solid yes")
check("solid set", char["solid"] is True)
say(s, "/solid no")
check("solid unset", char["solid"] is False)
out = say(s, "/solid maybe")
check("garbage is refused, not silently applied", "try: /solid" in out[0] and
      char["solid"] is False, out)

print("\nfield commands with no character focused all say so, not a crash")
s = chatshell.new_state()
say(s, "/new probe5_%d" % os.getpid())
for cmd in ("/glyph X", "/color red", "/role prop", "/count 1", "/health 5",
            "/solid yes", "/rows", "/newrow", "/delrow 1"):
    out = say(s, cmd)
    check("%-12s refuses cleanly with no character focused" % cmd,
          "focus a character first" in out[0], out)

print("\nworld settings: read with no args, write with args, clamped, validated")
s = chatshell.new_state()
say(s, "/new probe6_%d" % os.getpid())
out = say(s, "/world")
check("no args reads the current settings back", "width" in out[0], out)
say(s, "/world width=9999, height=1, speed=0")
w = s["project"]["world"]
check("width clamped to the max (70)", w["width"] == 70, w)
check("height clamped to the min (5)", w["height"] == 5, w)
check("speed clamped to the min (1)", w["speed"] == 1, w)
say(s, "/world wrap=yes")
check("wrap accepted", w["wrap"] is True)
out = say(s, "/world width=abc")
check("a non-numeric value is refused, nothing crashes", "plain numbers" in out[0], out)

before = dict(w)
say(s, "/world width=50, height=abc")
check("a bad value refuses the WHOLE command atomically -- a good value earlier "
      "in the same line (width) must not silently apply while the command as a "
      "whole reports failure (caught on self-review, real bug: it used to)",
      dict(w) == before, (before, dict(w)))

print("\nbrain rows: /newrow, /when, /do, /tiles, /done, /cancel, /delrow")
s = chatshell.new_state()
say(s, "/new probe7_%d" % os.getpid())
say(s, "/newchar hero")
out = say(s, "/when")
check("/when with nothing being built says so", "/newrow first" in out[0], out)
say(s, "/newrow")
out = say(s, "/tiles")
check("/tiles lists real tile ids", any("touch" in l for l in out) and
      any("move" in l for l in out), out)
out = say(s, "/when nosuchtile")
check("an unknown tile name says so", "no tile called" in out[0], out)
out = say(s, "/when move")
check("a DO tile typed on the WHEN side is refused, names which side it's for",
      "DO tile" in out[0], out)
say(s, "/when touch kind=hero")
check("a valid WHEN tile is added to the row being built",
      s["building"]["when"] == [{"tile": "touch", "args": {"kind": "hero"}}], s["building"])
say(s, "/do move dir=toward it")
check("a valid DO tile, with a space in its value, parses correctly",
      s["building"]["do"] == [{"tile": "move", "args": {"dir": "toward it"}}], s["building"])
say(s, "/cancel")
check("cancel discards the row -- nothing landed on the character",
      s["building"] is None and chatshell._current_char(s)["brain"] == [])

say(s, "/newrow")
say(s, "/when touch kind=hero")
say(s, "/do move dir=toward it")
say(s, "/done")
char = chatshell._current_char(s)
check("done saves the row to the character's own brain",
      len(char["brain"]) == 1 and char["brain"][0]["when"][0]["tile"] == "touch", char["brain"])
check("building is cleared afterward", s["building"] is None)

say(s, "/newrow")
say(s, "/done")
check("an empty row is discarded, not saved as a no-op row",
      len(char["brain"]) == 1, char["brain"])

out = say(s, "/rows")
check("/rows lists the one real row", "touch" in out[0] and "move" in out[0], out)
out = say(s, "/delrow 99")
check("deleting a row number that doesn't exist says so", "no row 99" in out[0], out)
say(s, "/delrow 1")
check("delrow actually removes it", char["brain"] == [], char["brain"])

print("\ntile args: named, comma-separated, defaults fill in what's left out")
fake_project = {"characters": [{"kind": "bandit"}]}
tile = chatshell.tiles.SENSORS["see"]
args, errors = chatshell.fill_tile_args(tile, fake_project, chatshell.parse_args_text("kind=bandit"))
check("one named arg given, the other (range) defaults", args == {"kind": "bandit", "range": 6} and
      not errors, (args, errors))
args, errors = chatshell.fill_tile_args(tile, fake_project, chatshell.parse_args_text(""))
check("no args at all -- every default", args == {"kind": "anything", "range": 6}, args)
args, errors = chatshell.fill_tile_args(tile, fake_project, chatshell.parse_args_text("kind=nosuchkind"))
check("a kind that isn't in this project's own roster is a real error",
      errors and "must be one of" in errors[0], errors)
int_tile = chatshell.tiles.SENSORS["timer"]
args, errors = chatshell.fill_tile_args(int_tile, fake_project, chatshell.parse_args_text("every=abc"))
check("a non-numeric value for an int param is a real error, not silently 0",
      errors and "plain number" in errors[0], errors)

print("\nsave/rename actually touch disk, cleaned up after")
scratch = "probe_disk_%d" % os.getpid()
s = chatshell.new_state()
say(s, "/new " + scratch)
try:
    out = say(s, "/save")
    check("save reports a real path", scratch in out[0] and out[0].endswith(".json"), out)
    check("...and it's really there", (brain.GAMES_DIR / (scratch + ".json")).exists())

    out = say(s, "/rename " + scratch + "_renamed")
    check("rename updates the in-memory name", s["project"]["name"] == scratch + "_renamed", out)
    say(s, "/save")
    check("saving after a rename writes the NEW filename",
          (brain.GAMES_DIR / (scratch + "_renamed.json")).exists())

    s2 = chatshell.new_state()
    out = say(s2, "/open " + scratch + "_renamed")
    check("what got saved can be opened back up", s2["project"]["name"] == scratch + "_renamed", out)
finally:
    (brain.GAMES_DIR / (scratch + ".json")).unlink(missing_ok=True)
    (brain.GAMES_DIR / (scratch + "_renamed.json")).unlink(missing_ok=True)

print("\n/page: paginated, permanent history -- nothing here is ever silently lost")
s = chatshell.new_state()
s["history"] = ["line %d" % i for i in range(25)]
out = say(s, "/page")
check("no page number given shows the latest page",
      out[0].startswith("-- page 3 of 3 --"), out)
out = say(s, "/page 1")
check("an explicit page shows that one", out[0] == "-- page 1 of 3 --" and
      out[1] == "line 0", out)
out = say(s, "/page 99")
check("out of range says so", "no page 99" in out[0], out)
out = say(s, "/page x")
check("non-numeric says so, not a crash", "plain number" in out[0], out)
check("navigating pages never grows the log itself",
      len(s["history"]) == 25, len(s["history"]))
out = say(s, "/help")
check("/help itself isn't logged either", len(s["history"]) == 25, len(s["history"]))

print("\n%d passed, %d failed (pure logic)\n" % (passed, failed))

# -- end to end, through a real pty -----------------------------------------

import fcntl                                                    # noqa: E402
import pty                                                      # noqa: E402
import select                                                    # noqa: E402
import struct                                                    # noqa: E402
import subprocess                                                # noqa: E402
import termios                                                   # noqa: E402
import time                                                      # noqa: E402


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


probe = (
    "import sys; sys.path.insert(0, %r)\n"
    "from engine import chatshell\n"
    "chatshell.run()\n"
) % str(ROOT)

scratch2 = "probe_pty_%d" % os.getpid()
try:
    print("end to end through a real pty: build a game, play it, come back, quit")
    s = Session(probe)
    out = s.drain(0.4)
    check("opens with the block-letter logo and the top-level breadcrumb",
          "###" in out and "top level" in out, out[:400])

    s.send(("/new " + scratch2 + "\r").encode())
    out = s.drain(0.3)
    check("a new game is open", "editing" in out and scratch2 in out, out[-300:])

    s.send(b"/newchar hero\r")
    s.drain(0.2)
    s.send(b"/role player\r")
    s.drain(0.2)
    s.send(b"/newrow\r")
    s.drain(0.2)
    s.send(b"/when key key=space\r")
    s.drain(0.2)
    s.send(b"/do say text=hi\r")
    out = s.drain(0.3)
    check("the DO tile was added, with its own argument", "say" in out and "hi" in out, out[-300:])
    s.send(b"/done\r")
    out = s.drain(0.3)
    check("the row was saved to the character's brain", "added:" in out, out[-300:])
    s.send(b"/back\r")
    s.drain(0.2)   # un-focus the character
    s.send(b"/save\r")
    out = s.drain(0.4)
    check("saved for real", (brain.GAMES_DIR / (scratch2 + ".json")).exists(), out[-300:])

    print("\n/play launches a real running game, sharing the very same log")
    s.send(b"/play\r")
    played = s.drain(0.6)
    check("the world actually started rendering (score/health/tick line)",
          "score" in played, played[-300:])
    s.send(b"q")   # quit the running game
    played2 = s.drain(0.4)
    s.send(b"\r")  # play()'s own "press enter to go back to the menu" prompt
    back = s.drain(0.6)
    check("back in the chat shell afterward, not stuck in the game",
          "top level" not in back and scratch2 in back, back[-400:])
    check("the shell says so plainly", "back from playing" in back, back[-400:])

    s.send(b"/quit\r")
    s.close()
    check("the whole process exits cleanly", s.proc.returncode == 0, s.proc.returncode)
finally:
    (brain.GAMES_DIR / (scratch2 + ".json")).unlink(missing_ok=True)

print("\nCtrl-D at the prompt leaves cleanly too, not a traceback")
# Not Ctrl-C here, on purpose -- same wrinkle tests/test_pty.py in
# ~/termux-chat already ran into and wrote up: this pty is never made
# the child's controlling terminal the way a real shell's is, so the
# kernel has no foreground process group to deliver the real SIGINT
# Ctrl-C generates to -- confirmed directly, the byte is silently
# swallowed by the line discipline here, the process never even sees
# it. run()'s own `except KeyboardInterrupt` is still correct,
# real-terminal behaviour regardless. Ctrl-D (EOF at the start of a
# line, even in cooked/canonical mode) has no such wrinkle, so it's
# what's actually checked here -- run()'s existing `except EOFError`
# already covers it.
s2 = Session(probe)
s2.drain(0.3)
s2.send(b"\x04")
s2.close()
check("clean exit, code 0", s2.proc.returncode == 0, s2.proc.returncode)

print("\na command that genuinely raises doesn't take the whole session down")
# A silent crash and "nothing is responding" look identical from outside
# a real terminal -- this is the actual failure mode a real bug report
# ("nothing responding or prompting in chat at all for spark") could be
# describing, so it's worth a real pty check, not just trusting the
# try/except reads correctly. /explode is injected only for this probe.
crash_probe = (
    "import sys; sys.path.insert(0, %r)\n"
    "from engine import chatshell\n"
    "chatshell.COMMANDS['explode'] = lambda state, rest: 1 / 0\n"
    "chatshell.run()\n"
) % str(ROOT)
s3 = Session(crash_probe)
s3.drain(0.3)
s3.send(b"/explode\r")
out = s3.drain(0.4)
check("the error lands right in the log, readable, not a bare crash",
      "something went wrong" in out and "ZeroDivisionError" in out, out[-500:])
s3.send(b"/games\r")
out = s3.drain(0.4)
check("...and ordinary commands still work right after",
      "saved game" in out or "no saved games" in out, out[-400:])
s3.send(b"/quit\r")
s3.close()
check("still exits cleanly afterward", s3.proc.returncode == 0, s3.proc.returncode)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
