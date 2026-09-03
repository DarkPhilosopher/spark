"""Playing a project: keyboard input, the tick loop, and drawing."""

import os
import select
import sys
import termios
import time
import tty

from .world import World

ESCAPES = {"A": "up", "B": "down", "C": "right", "D": "left"}
HIDE, SHOW = "\033[?25l", "\033[?25h"
HOME_CLEAR = "\033[H\033[2J"


class Keyboard:
    """Non-blocking single-key reads, restoring the terminal on the way out."""

    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.saved = None

    def __enter__(self):
        if sys.stdin.isatty():
            self.saved = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        return self

    def __exit__(self, *exc):
        if self.saved is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)

    def pressed(self):
        """Every key seen since the last call, as a set of names."""
        keys = set()
        if self.saved is None:
            return keys
        while select.select([sys.stdin], [], [], 0)[0]:
            data = os.read(self.fd, 64).decode("utf-8", "replace")
            if not data:
                break
            i = 0
            while i < len(data):
                ch = data[i]
                if ch == "\x1b" and data[i + 1:i + 2] == "[":
                    keys.add(ESCAPES.get(data[i + 2:i + 3], "escape"))
                    i += 3
                    continue
                if ch == " ":
                    keys.add("space")
                elif ch in ("\x03", "\x04"):
                    keys.add("quit")
                else:
                    keys.add(ch.lower())
                i += 1
        return keys


def draw(world, speed):
    out = [HOME_CLEAR]
    out += world.render()
    hearts = sum(t.health for t in world.things if t.role == "player")
    out.append("score %-5d  health %-4d tick %-6d" % (world.score, hearts, world.tick))
    out.append((world.message or "")[:world.width + 2])
    out.append("arrows/wasd move . space acts . q quits")
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


def play(project, max_ticks=None):
    """Run a project. With max_ticks set, runs headless -- handy for testing."""
    world = World(project)
    speed = max(1, project.get("world", {}).get("speed", 6))
    delay = 1.0 / speed
    headless = max_ticks is not None or not sys.stdin.isatty()
    # You are playing your own game on your own phone, so the `open` tile is
    # allowed here. live.Session deliberately leaves it off.
    world.may_open = not headless

    with Keyboard() as keyboard:
        if not headless:
            sys.stdout.write(HIDE)
        try:
            while world.status is None:
                if max_ticks is not None and world.tick >= max_ticks:
                    break
                world.keys = keyboard.pressed()
                if "q" in world.keys or "quit" in world.keys:
                    break
                world.step()
                if not headless:
                    draw(world, speed)
                    time.sleep(delay)
        except KeyboardInterrupt:
            pass
        finally:
            if not headless:
                sys.stdout.write(SHOW)
                sys.stdout.flush()

    if not headless:
        draw(world, speed)
        if world.status == "win":
            print("\n  *** YOU WIN ***")
        elif world.status == "lose":
            print("\n  *** YOU LOSE ***")
        input("\npress enter to go back to the menu ")
    return world
