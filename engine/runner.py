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

    def pause(self):
        """Hand the terminal back to its normal, cooked, line-editing self
        -- so a plain input() call (the chat command line; see chat_break
        below) gets a real text box, backspace and all, the same as
        anywhere else in this app, rather than swallowing every key one
        at a time the way gameplay itself needs to."""
        self.__exit__()

    def resume(self):
        """Undo pause(): back to swallowing single keys for gameplay,
        with nothing going to a text box at all."""
        self.__enter__()

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


def read_key(fd):
    """Block for exactly one keypress, decoding an arrow-key escape sequence.

    A separate blocking read from Keyboard.pressed()'s non-blocking poll,
    which the tick loop above needs instead -- this one is for the menus
    (see builder.py's big-picture menu), which want to sit still until
    something is actually pressed rather than spin a loop.

    An escape sequence arrives as three bytes close together: ESC, `[`, then
    the direction letter. A lone Escape keypress is only the first of those,
    so the short wait below is what tells the two apart -- if nothing more
    shows up in 50ms, it was just Escape.
    """
    ch = os.read(fd, 1).decode("utf-8", "replace")
    if ch == "\x1b":
        if select.select([fd], [], [], 0.05)[0]:
            rest = os.read(fd, 2).decode("utf-8", "replace")
            if rest[:1] == "[":
                return ESCAPES.get(rest[1:2], "escape")
        return "escape"
    if ch in ("\r", "\n"):
        return "enter"
    if ch in ("\x03", "\x04"):
        return "quit"
    return ch.lower()


def draw(world, speed):
    out = [HOME_CLEAR]
    out += world.render()
    hearts = sum(t.health for t in world.things if t.role == "player")
    out.append("score %-5d  health %-4d tick %-6d" % (world.score, hearts, world.tick))
    out.append((world.message or "")[:world.width + 2])
    out.append("arrows/wasd move . space acts . q quits . / for chat")
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


def _local_help_lines(project):
    """A game's own "how to play", the same `help` field and fallback
    order world3d.html's own /help chat command reads -- see that file's
    CHAT_COMMANDS.help for the JS twin of this."""
    lines = []
    text = project.get("help")
    if text:
        lines.extend(str(text).split("\n"))
        lines.append("")
    lines.append("/help -- show this")
    lines.append("/quit -- leave the game (same as pressing q)")
    return lines


def run_local_command(said, project):
    """A single typed command line's result, as the lines chat_break
    should show. Purely local -- there is no server connection from the
    plain terminal player the way world3d.html/index.html have, so this
    is deliberately a smaller set than their own CHAT_COMMANDS: nobody
    else to /who, nothing here to /clear. Blank input is treated as
    /help, the friendliest thing to do with a stray keypress.

    Returns ("quit", None) if the command means leave the game, or
    ("show", lines) with what to put on the result screen otherwise.
    """
    word = said.strip().lstrip("/").split(None, 1)
    word = word[0].lower() if word else "help"
    if word == "help":
        return "show", _local_help_lines(project)
    if word in ("quit", "q"):
        return "quit", None
    return "show", ["no such command: /%s -- try /help" % word]


def draw_chat_result(lines):
    out = [HOME_CLEAR, "=" * 40, " chat", "=" * 40, ""]
    out.extend(lines)
    out.append("")
    out.append("(press any key to go back)")
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


def chat_break(project, keyboard):
    """Pressed "/" during play: hand the terminal back to normal cooked
    input for one line (so the phone's own text box/keyboard behaves
    exactly like it does everywhere else in this app, rather than
    gameplay's usual single-key swallowing), run whatever was typed as
    a command, and show the result as its own screen -- a second,
    separate view from the running world -- until any key dismisses it.

    Returns True if the command was to quit the game outright.
    """
    keyboard.pause()
    sys.stdout.write(SHOW)
    sys.stdout.flush()
    try:
        said = input("\n/")
    except EOFError:
        said = "quit"
    sys.stdout.write(HIDE)
    kind, lines = run_local_command(said, project)
    if kind == "quit":
        return True
    keyboard.resume()
    draw_chat_result(lines)
    read_key(keyboard.fd)   # block for exactly one key, then back to the game
    return False


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
                if "/" in world.keys and not headless:
                    if chat_break(project, keyboard):
                        break
                    continue   # this tick's own keys are stale by now
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
