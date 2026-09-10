#!/usr/bin/env python3
"""Check the terminal player's own "/" command line: pressing "/" during
play swallows nothing gameplay would have used it for (nothing does --
see engine/runner.py's Keyboard.pause/resume comments), drops into a
real, cooked-mode text line so the phone's own keyboard/text box behaves
normally, runs the command, shows the result as its own screen, and
stays open for as many more commands as you like, in a row -- a blank
line is what actually closes it and goes back to the running world.

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
from engine.world import World                                   # noqa: E402

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

print("\n/help commands [description]: the reference on its own, grouped by type")

kind, lines = run_local_command("/help commands", {})
check("just the reference -- no game text, even if there is one to skip",
      lines[0] == "Info:", lines)
check("bare syntax only, no descriptions", not any(" -- " in l for l in lines), lines)
check("grouped under headings, in a fixed order",
      lines.index("Actions:") > lines.index("Info:")
      and lines.index("Log:") > lines.index("Actions:"), lines)

kind, lines = run_local_command("/help commands description", {})
check("same reference, with what each one does this time",
      lines[0] == "Info:" and any(" -- " in l for l in lines), lines)

print("\n/attack <x> <y>: hit a bandit at a known spot instead of walking up to it blind")


def attack_game(hero_pos, bandit_pos, bandit_health=6):
    project = {
        "name": "attack_probe", "world": {"width": 12, "height": 12, "speed": 6},
        "characters": [
            {"kind": "hero", "glyph": "@", "color": "green", "role": "player",
             "count": 0, "brain": []},
            {"kind": "bandit", "glyph": "x", "color": "red", "role": "prop",
             "count": 0, "brain": []},
        ],
    }
    w = World(project)
    w.spawn("hero", *hero_pos)
    b = w.spawn("bandit", *bandit_pos)
    b.health = bandit_health
    return w, b


kind, lines = run_local_command("/attack 5 5", None)
check("with no world running, says so rather than crashing",
      "no game running" in lines[0], lines)

w, bandit = attack_game((5, 5), (6, 5))
kind, lines = run_local_command("/attack 6 5", w.project, w)
check("attacking an adjacent bandit does 2 damage, the same touch already does",
      "attacked" in lines[0] and bandit.health == 4, (lines, bandit.health))
check("it's still alive with health left", bandit.alive)

w, bandit = attack_game((5, 5), (6, 5), bandit_health=2)
kind, lines = run_local_command("/attack 6 5", w.project, w)
check("killing it outright removes it from the world, same as ordinary contact damage",
      "destroyed" in lines[0] and not bandit.alive, (lines, bandit.alive))

w, bandit = attack_game((0, 0), (6, 5))
kind, lines = run_local_command("/attack 6 5", w.project, w)
check("too far away refuses", "too far" in lines[0], lines)

w, bandit = attack_game((5, 5), (6, 5))
kind, lines = run_local_command("/attack 5 6", w.project, w)   # adjacent, nothing there
check("adjacent but nothing there says so", "no bandit at" in lines[0], lines)

print("\n/recruit <x> <y> and /dismiss <x> <y>: the same as e/r, aimed at a spot")


def squad_game(hero_pos, worker_pos, worker_leader=None):
    project = {
        "name": "squad_probe", "world": {"width": 12, "height": 12, "speed": 6},
        "characters": [
            {"kind": "hero", "glyph": "@", "color": "green", "role": "player",
             "count": 0, "brain": []},
            {"kind": "worker", "glyph": "w", "color": "lime", "role": "prop",
             "count": 0, "brain": []},
            {"kind": "bandit", "glyph": "x", "color": "red", "role": "prop",
             "count": 0, "brain": []},
        ],
    }
    w = World(project)
    hero = w.spawn("hero", *hero_pos)
    worker = w.spawn("worker", *worker_pos)
    worker.leader = worker_leader
    return w, hero, worker


kind, lines = run_local_command("/recruit 5 5", None)
check("with no world running, says so rather than crashing", "no game running" in lines[0], lines)

w, hero, worker = squad_game((5, 5), (6, 5))   # bare (unled) worker, adjacent
kind, lines = run_local_command("/recruit 6 5", w.project, w)
check("recruiting a bare worker (not just a companion) works",
      "recruited the worker" in lines[0] and worker.leader is hero, (lines, worker.leader))

w, hero, worker = squad_game((5, 5), (6, 5), worker_leader="someone else already")
kind, lines = run_local_command("/recruit 6 5", w.project, w)
check("can't recruit something already led by someone", "nothing recruitable" in lines[0], lines)

w, hero, worker = squad_game((0, 0), (6, 5))
kind, lines = run_local_command("/recruit 6 5", w.project, w)
check("too far away refuses", "too far" in lines[0], lines)

bandit_only = {
    "name": "bandit_probe", "world": {"width": 12, "height": 12, "speed": 6},
    "characters": [
        {"kind": "hero", "glyph": "@", "color": "green", "role": "player", "count": 0, "brain": []},
        {"kind": "bandit", "glyph": "x", "color": "red", "role": "prop", "count": 0, "brain": []},
    ],
}
w2 = World(bandit_only)
w2.spawn("hero", 5, 5)
w2.spawn("bandit", 6, 5)
kind, lines = run_local_command("/recruit 6 5", w2.project, w2)
check("a bandit is never recruitable, even bare and adjacent", "nothing recruitable" in lines[0], lines)

w, hero, worker = squad_game((5, 5), (6, 5))
worker.leader = hero
kind, lines = run_local_command("/dismiss 6 5", w.project, w)
check("dismissing a bought worker works, not just a companion",
      "dismissed the worker" in lines[0] and worker.leader is None, (lines, worker.leader))

w, hero, worker = squad_game((5, 5), (6, 5))   # bare, not led by hero
kind, lines = run_local_command("/dismiss 6 5", w.project, w)
check("can't dismiss something that isn't yours", "nothing of yours" in lines[0], lines)

w, hero, worker = squad_game((0, 0), (6, 5))
worker.leader = hero
kind, lines = run_local_command("/dismiss 6 5", w.project, w)
check("too far away refuses", "too far" in lines[0], lines)

print("\n/mine <x> <y>: gather from a known spot instead of walking up to it blind")


def mine_game(hero_pos, ore_pos):
    project = {
        "name": "mine_probe", "world": {"width": 12, "height": 12, "speed": 6},
        "characters": [
            {"kind": "hero", "glyph": "@", "color": "green", "role": "player",
             "count": 0, "brain": []},
            {"kind": "ore", "glyph": "o", "color": "gold", "role": "prop",
             "count": 0, "brain": []},
        ],
    }
    w = World(project)
    w.spawn("hero", *hero_pos)
    w.spawn("ore", *ore_pos)
    return w


kind, lines = run_local_command("/mine 5 5", None)
check("with no world running, says so rather than crashing",
      kind == "show" and "no game running" in lines[0], lines)

w = mine_game((5, 5), (6, 5))   # adjacent
hero = next(t for t in w.things if t.kind == "hero")
kind, lines = run_local_command("/mine 6 5", w.project, w)
check("mining an adjacent, real ore spot works", "mined 1 ore" in lines[0], lines)
check("...and it actually lands in the hero's own count", hero.inventory.get("ore") == 1)

w = mine_game((0, 0), (6, 5))   # far away
kind, lines = run_local_command("/mine 6 5", w.project, w)
check("too far away refuses, doesn't teleport-mine across the map",
      "too far" in lines[0], lines)

w = mine_game((5, 5), (6, 5))
kind, lines = run_local_command("/mine 5 6", w.project, w)   # adjacent, but nothing there
check("adjacent but nothing there says so", "no ore at" in lines[0], lines)

w = mine_game((5, 5), (6, 5))
kind, lines = run_local_command("/mine", w.project, w)
check("missing coordinates gives a usage line, not a crash", "try: /mine" in lines[0], lines)
kind, lines = run_local_command("/mine x y", w.project, w)
check("non-numeric coordinates say so, not a crash", "plain numbers" in lines[0], lines)

print("\n/units and /name: the roster -- everything yours, named and located")


def roster_game():
    project = {
        "name": "roster_probe", "world": {"width": 12, "height": 12, "speed": 6},
        "characters": [
            {"kind": "hero", "glyph": "@", "color": "green", "role": "player",
             "count": 0, "brain": []},
            {"kind": "companion", "glyph": "c", "color": "yellow", "role": "prop",
             "count": 0, "brain": []},
            {"kind": "bandit", "glyph": "x", "color": "red", "role": "prop",
             "count": 0, "brain": []},
            {"kind": "wall", "glyph": "#", "color": "grey", "role": "prop",
             "count": 0, "brain": []},
            {"kind": "turret", "glyph": "T", "color": "silver", "role": "prop",
             "count": 0, "brain": []},
        ],
    }
    w = World(project)
    hero = w.spawn("hero", 1, 1)
    companion = w.spawn("companion", 2, 2)
    companion.leader = hero
    stray = w.spawn("companion", 3, 3)          # NOT led -- shouldn't show up as ours
    enemy = w.spawn("bandit", 4, 4)              # never ours
    wall = w.spawn("wall", 5, 5)                 # structures are ours by kind alone
    turret = w.spawn("turret", 6, 6)
    return w, hero, companion, stray, enemy, wall, turret


w, hero, companion, stray, enemy, wall, turret = roster_game()
kind, lines = run_local_command("/units", w.project, w)
check("lists the hero", any("hero" in l and "(1, 1)" in l for l in lines), lines)
check("lists a recruited companion", any("(2, 2)" in l for l in lines), lines)
check("does NOT list an unled companion -- not ours just for existing",
      not any("(3, 3)" in l for l in lines), lines)
check("does NOT list a bandit", not any("bandit" in l for l in lines), lines)
check("lists a wall (structures are ours by kind, no leader needed)",
      any("(5, 5)" in l for l in lines), lines)
check("lists a turret the same way", any("(6, 6)" in l for l in lines), lines)

kind, lines = run_local_command("/units", None)
check("with no world running, says so rather than crashing",
      "no game running" in lines[0], lines)

w, hero, companion, stray, enemy, wall, turret = roster_game()
kind, lines = run_local_command("/name 6 6 North Gate", w.project, w)
check("naming something of yours works", "North Gate" in lines[0], lines)
check("...and the name actually sticks on the Thing", turret.label == "North Gate")
kind, lines = run_local_command("/units", w.project, w)
check("the custom name shows up in /units from then on",
      any("North Gate" in l for l in lines), lines)

kind, lines = run_local_command("/name 3 3 Sneaky", w.project, w)   # the unled stray
check("can't name something that isn't yours", "nothing of yours" in lines[0], lines)

kind, lines = run_local_command("/name 6 6", w.project, w)
check("missing a name gives a usage line, not a crash", "try: /name" in lines[0], lines)
kind, lines = run_local_command("/name x y Bob", w.project, w)
check("non-numeric coordinates say so, not a crash", "plain numbers" in lines[0], lines)

print("\n/log [n] and /forget <n>: a real, paginated log -- \"consistent log history\"")

history = []
kind, lines = run_local_command("/log", {}, None, history)
check("nothing logged yet, says so", "nothing logged yet" in lines[0], lines)

history = ["line %d" % i for i in range(25)]
kind, lines = run_local_command("/log", {}, None, history)
check("with no page given, shows the LATEST page, titled with its own number",
      lines[0] == "-- page 3 of 3 --" and lines[-1] == "line 24", lines)
kind, lines = run_local_command("/log 1", {}, None, history)
check("an explicit page number shows that one instead",
      lines[0] == "-- page 1 of 3 --" and lines[1] == "line 0", lines)
kind, lines = run_local_command("/log 99", {}, None, history)
check("an out-of-range page says so", "no page 99" in lines[0], lines)
kind, lines = run_local_command("/log x", {}, None, history)
check("a non-numeric page says so, not a crash", "plain number" in lines[0], lines)
check("none of the above actually changed the log itself",
      len(history) == 25 and history[0] == "line 0", history)

history = ["line %d" % i for i in range(25)]
kind, lines = run_local_command("/forget 2", {}, None, history)
check("its own confirmation names the page and how many lines",
      "page 2 forgotten (10 lines removed)" in lines[0], lines)
check("those exact 10 lines are actually gone from the log",
      "line 10" not in history and "line 19" not in history, history)
check("earlier pages are untouched", history[0] == "line 0", history)
check("later pages shift down and renumber -- what was page 3 is now page 2",
      len(history) == 15 and history[10] == "line 20", history)

kind, lines = run_local_command("/forget 99", {}, None, history)
check("forgetting a page that never existed says so", "no page 99" in lines[0], lines)
kind, lines = run_local_command("/forget x", {}, None, history)
check("a non-numeric page says so, not a crash", "plain number" in lines[0], lines)

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

print("pressing / during play: a real cooked line, its own result screen, and it stays open")
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
check("the reference mentions /mine too",
      "/mine" in out, out[-400:])

s.send(b"units\r")   # a second command, right after the first, with no re-pressing /
out2 = s.drain(0.6)
check("chat stayed open -- a second command runs without pressing / again",
      "yours:" in out2, out2[-400:])
check("still on the chat screen, not back in the running game yet",
      "chat" in out2.lower() and "score" not in out2, out2[-400:])

s.send(b"\r")   # a blank line is what actually closes chat
back = s.drain(0.6)
check("a blank line closes chat and goes back to the running game (the world redraws)",
      "score" in back, back[-200:])

print("\npressing space during play makes a new ore vein (the \"press a button\" ask)")
s.send(b" ")
made = s.drain(0.6)
check("the hero's own space row fires -- a fresh ore vein message shows up",
      "ore vein appeared" in made, made[-200:])

print("\n/quit from inside an open chat leaves the game outright, same as pressing q")
s.send(b"/")
s.drain(0.2)
s.send(b"quit\r")
s.drain(0.4)
s.send(b"\r")   # play()'s own "press enter to go back to the menu" prompt
s.close()
check("the process actually exited", s.proc.returncode == 0, s.proc.returncode)

s2 = Session(play_probe)
s2.drain(0.3)
s2.send(b"q")
s2.drain(0.4)
s2.send(b"\r")   # play()'s own "press enter to go back to the menu" prompt
s2.close()
check("q still quits normally too, without ever opening chat", s2.proc.returncode == 0, s2.proc.returncode)

print("\n%d passed, %d failed" % (passed, failed))
sys.exit(1 if failed else 0)
