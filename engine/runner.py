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
    # Whoever's actually being controlled from here -- the same "the
    # hero" every /mine-style chat command already means. None (shown as
    # "-,-") only if the player character has died and there's nothing
    # left to report a position for.
    player = next((t for t in world.things if t.role == "player" and t.alive), None)
    pos = "%d,%d" % (player.x, player.y) if player is not None else "-,-"
    out.append("score %-5d  health %-4d tick %-6d  pos %s" % (world.score, hearts, world.tick, pos))
    out.append((world.message or "")[:world.width + 2])
    out.append("arrows/wasd move . space acts . q quits . / for chat . p for entities")
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


# (category, syntax, description) -- kept in sync by hand with
# world3d.html's own COMMAND_CATALOG. CATEGORY_ORDER below is the
# order "/help commands" groups and lists them in; each category only
# shows up if it actually has a command in it, so the two engines'
# slightly different command sets (no /who or /clear here, no /quit
# there) never leave a heading with nothing under it.
COMMAND_CATALOG = [
    ("info", "/help [commands [description]]",
     "show this, or just the command list (add \"description\" for what each one does)"),
    ("info", "/units", "list everything you own or possess, and where it is"),
    ("info", "/list", "list every entity in the world, yours or not, with its properties"),
    ("action", "/mine <x> <y>", "mine the ore at that spot, if you're next to it"),
    ("action", "/attack <x> <y>", "hit the bandit at that spot, if you're next to it"),
    ("action", "/recruit <x> <y>", "recruit whatever's bare there, if you're next to it"),
    ("action", "/dismiss <x> <y>", "release whatever's yours there, if you're next to it"),
    ("roster", "/name <x> <y> <new name>", "rename whatever's yours at that spot"),
    ("log", "/log [n]", "a numbered page of the log; latest if n is left off"),
    ("log", "/forget <n>", "remove page n from the log for good"),
    ("system", "/quit", "leave the game (same as pressing q)"),
]
CATEGORY_ORDER = ["info", "action", "roster", "log", "system"]
CATEGORY_TITLE = {"info": "Info", "action": "Actions", "roster": "Roster",
                   "log": "Log", "system": "System"}


def _command_list_lines(with_description):
    """The whole command reference, grouped by type -- "/help commands"
    (bare) or "/help commands description" (with what each one does).
    Also folded into plain /help's own tail, after a game's own text."""
    lines = []
    for cat in CATEGORY_ORDER:
        rows = [c for c in COMMAND_CATALOG if c[0] == cat]
        if not rows:
            continue
        lines.append(CATEGORY_TITLE[cat] + ":")
        for _, syntax, desc in rows:
            lines.append("  " + syntax + (" -- " + desc if with_description else ""))
    return lines


def _local_help_lines(project, rest=""):
    """A game's own "how to play" plus the full command reference, or
    -- given "commands" as an argument -- just the reference on its
    own (add "description" too for what each one does). The same
    `help` field and fallback order world3d.html's own /help chat
    command reads -- see that file's CHAT_COMMANDS.help for the JS
    twin of this."""
    words = rest.split()
    if words and words[0] == "commands":
        return _command_list_lines(with_description=len(words) > 1 and words[1] == "description")
    lines = []
    text = project.get("help")
    if text:
        lines.extend(str(text).split("\n"))
        lines.append("")
    lines.extend(_command_list_lines(with_description=True))
    return lines


# How many lines make up one page of /log -- small enough that a page
# plus draw_chat_result's own header/footer still fits MANUAL.md's
# documented 20-row minimum terminal.
PAGE_SIZE = 10


def _history_add(history, lines):
    """Append a command's own result to the running log -- requested
    directly, "consistent log history": mine/units/name results used to
    be purely one-off, gone the moment the next screen replaced them.
    `history` is a plain flat list (None is fine, and skips this, for
    any caller that doesn't care about logging -- most direct tests of
    a single command in isolation)."""
    if history is not None:
        history.extend(lines)


def _history_pages(history):
    if not history:
        return 0
    return (len(history) + PAGE_SIZE - 1) // PAGE_SIZE


def _do_log(history, rest):
    """/log [n]: one page of everything /mine, /units, and /name have
    shown so far, titled by its own page number -- requested directly,
    "title each [page] of chat by page number." Defaults to the most
    recent page. /help, /log, and /forget themselves are deliberately
    NOT logged -- navigating the log shouldn't itself grow the log."""
    total = _history_pages(history)
    if total == 0:
        return ["nothing logged yet"]
    rest = rest.strip()
    if rest:
        try:
            n = int(rest)
        except ValueError:
            return ["page number needs to be a plain number: /log [n]"]
    else:
        n = total
    if n < 1 or n > total:
        return ["no page %d -- there are %d" % (n, total)]
    start = (n - 1) * PAGE_SIZE
    lines = ["-- page %d of %d --" % (n, total)]
    lines.extend(history[start:start + PAGE_SIZE])
    return lines


def _do_forget(history, rest):
    """/forget <n>: remove one page's lines from the log for good --
    requested directly, "remove from history after submited." Pages
    after the removed one shift down and renumber, the same as deleting
    a page from any paginated list would."""
    total = _history_pages(history)
    if total == 0:
        return ["nothing logged yet"]
    try:
        n = int(rest.strip())
    except ValueError:
        return ["page number needs to be a plain number: /forget <n>"]
    if n < 1 or n > total:
        return ["no page %d -- there are %d" % (n, total)]
    start = (n - 1) * PAGE_SIZE
    removed = len(history[start:start + PAGE_SIZE])
    del history[start:start + PAGE_SIZE]
    return ["page %d forgotten (%d line%s removed)"
            % (n, removed, "" if removed == 1 else "s")]


# Structure kinds nobody but the player ever creates in this game, so
# "every wall/turret in the world" already means "every one the player
# built" -- there's no ownership field on a structure the way a
# recruited unit's own `leader` is one. Specific to outpost.json's own
# roster on purpose, rather than a guess at what every possible game
# might call its buildings.
STRUCTURE_KINDS = ("wall", "turret")


def _owned_things(world):
    """The hero, plus everything led by the hero, plus every player-built
    structure -- "yours" for /units and /name. Returns (hero, [things]),
    hero first; (None, []) if there's no living player character at all."""
    hero = next((t for t in world.things if t.role == "player" and t.alive), None)
    if hero is None:
        return None, []
    owned = [hero]
    for t in world.things:
        if t is hero or not t.alive:
            continue
        if t.leader is hero or t.kind in STRUCTURE_KINDS:
            owned.append(t)
    return hero, owned


def _do_units(world):
    """/units: everything you own or possess, named and located, the
    "selector menu" for referring back to something later -- with
    /name, and with /mine already taking a coordinate the same way."""
    if world is None:
        return ["no game running"]
    hero, owned = _owned_things(world)
    if hero is None:
        return ["no player character"]
    lines = ["yours:"]
    for t in owned:
        name = t.label or t.kind
        lines.append("  %s (%s) at (%d, %d)" % (name, t.kind, t.x, t.y))
    return lines


def _do_list(world):
    """/list: every entity currently alive in the world -- not just yours
    (see /units for that narrower "mine" view) -- each with its own
    basic properties: kind, position, health, and whatever else it
    happens to be carrying right now (a custom /name, a leader if
    something's leading it, a non-empty inventory). Requested directly:
    "a list of all entity in workspace in chat command also showing
    its properties" -- the map-wide inspector /units was never meant
    to be. Sorted by kind then position so the same world always lists
    the same way, not by whatever order things happen to sit in
    internally."""
    if world is None:
        return ["no game running"]
    living = [t for t in world.things if t.alive]
    if not living:
        return ["nothing in the world at all"]
    lines = []
    for t in sorted(living, key=lambda t: (t.kind, t.x, t.y)):
        name = ("%s (%s)" % (t.label, t.kind)) if t.label else t.kind
        bits = [name, "at (%d, %d)" % (t.x, t.y), "health %d" % t.health]
        if t.leader is not None and t.leader.alive:
            bits.append("led by " + (t.leader.label or t.leader.kind))
        carrying = {k: v for k, v in t.inventory.items() if v}
        if carrying:
            bits.append("carrying " + ", ".join(
                "%d %s" % (v, k) for k, v in sorted(carrying.items())))
        lines.append("  " + " -- ".join(bits))
    return lines


def _do_name(world, rest):
    """/name <x> <y> <new name>: give whatever's yours at that exact spot
    a custom name, so it shows up as that in /units from then on (and,
    unlike /mine's, this one edit is not range-limited to next to you --
    naming something isn't a physical act the way mining is)."""
    if world is None:
        return ["no game running"]
    parts = rest.split(None, 2)
    if len(parts) < 3:
        return ["try: /name <x> <y> <new name>"]
    try:
        x, y = int(parts[0]), int(parts[1])
    except ValueError:
        return ["x and y need to be plain numbers: /name <x> <y> <new name>"]
    new_name = parts[2].strip()
    if not new_name:
        return ["give it an actual name: /name <x> <y> <new name>"]
    hero, owned = _owned_things(world)
    if hero is None:
        return ["no player character"]
    target = next((t for t in owned if t.x == x and t.y == y), None)
    if target is None:
        return ["nothing of yours at (%d, %d)" % (x, y)]
    target.label = new_name
    return ["%s is now called \"%s\"" % (target.kind, new_name)]


def _hero(world, verb):
    """The living player character, or a one-line complaint -- shared by
    every /<verb> <x> <y> command below. Returns (hero, None) or
    (None, [complaint])."""
    hero = next((t for t in world.things if t.role == "player" and t.alive), None)
    if hero is None:
        return None, ["no player character to %s with" % verb]
    return hero, None


def _parse_xy(rest, usage):
    """Shared arg-parsing for every /<verb> <x> <y> command below. Returns
    ((x, y), None) or (None, [complaint])."""
    parts = rest.split()
    if len(parts) < 2:
        return None, ["try: " + usage]
    try:
        return (int(parts[0]), int(parts[1])), None
    except ValueError:
        return None, ["x and y need to be plain numbers: " + usage]


def _too_far(hero, x, y):
    """None if adjacent (the same one square `touch` itself always
    means), else the complaint -- shared by every physical (not just
    bookkeeping, like /name) /<verb> <x> <y> command below."""
    if max(abs(hero.x - x), abs(hero.y - y)) > 1:
        return ["too far away -- get within one square of (%d, %d) first" % (x, y)]
    return None


def _do_mine(world, rest):
    """/mine <x> <y>: gather from the ore at that exact spot, same as
    walking up and standing there would over time (see the hero's own
    touch(ore) row in games/outpost.json) -- just named by coordinate
    instead, for whenever you already know where one is and don't want
    to walk there blind. Still range-limited to right next to you, the
    same one square `touch` itself always means -- this is a shortcut
    for reaching it, not a way to mine from across the map."""
    if world is None:
        return ["no game running to mine in"]
    xy, err = _parse_xy(rest, "/mine <x> <y>")
    if err:
        return err
    x, y = xy
    hero, err = _hero(world, "mine")
    if err:
        return err
    err = _too_far(hero, x, y)
    if err:
        return err
    target = next((t for t in world.things
                    if t.alive and t.kind == "ore" and t.x == x and t.y == y), None)
    if target is None:
        return ["no ore at (%d, %d)" % (x, y)]
    hero.inventory["ore"] = hero.inventory.get("ore", 0) + 1
    return ["mined 1 ore at (%d, %d) -- you now have %d"
            % (x, y, hero.inventory["ore"])]


ATTACK_DAMAGE = 2   # matches the hero's own touch(bandit) -> damage it 2 row exactly


def _do_attack(world, rest):
    """/attack <x> <y>: hit the bandit at that exact spot, the same
    amount of damage touching one already does -- a shortcut for
    reaching it, not ranged combat from across the map. Kills it
    outright (removed from the world) the same way ordinary contact
    damage already does, once its health runs out."""
    if world is None:
        return ["no game running to attack with"]
    xy, err = _parse_xy(rest, "/attack <x> <y>")
    if err:
        return err
    x, y = xy
    hero, err = _hero(world, "attack")
    if err:
        return err
    err = _too_far(hero, x, y)
    if err:
        return err
    target = next((t for t in world.things
                    if t.alive and t.kind == "bandit" and t.x == x and t.y == y), None)
    if target is None:
        return ["no bandit at (%d, %d)" % (x, y)]
    target.health -= ATTACK_DAMAGE
    if target.health <= 0:
        world.remove(target)
        return ["attacked (%d, %d) -- bandit destroyed" % (x, y)]
    return ["attacked (%d, %d) -- bandit has %d health left" % (x, y, target.health)]


# Kinds a bare, unled one of can be recruited -- everything the hero's
# own "1"/"2" buy rows can hire, plus the free-roaming companions
# already scattered around at the start. Never a bandit or a structure.
RECRUITABLE_KINDS = ("companion", "worker", "soldier")


def _do_recruit(world, rest):
    """/recruit <x> <y>: the same as touching a companion and pressing e
    (see the hero's own `lead` row), just aimed at an exact spot.
    Works on any bare (not already led by someone) companion/worker/
    soldier -- including one you dismissed earlier and want back,
    which the ordinary in-game "e" key can't reach at all, since it
    only ever touches kind "companion"."""
    if world is None:
        return ["no game running to recruit with"]
    xy, err = _parse_xy(rest, "/recruit <x> <y>")
    if err:
        return err
    x, y = xy
    hero, err = _hero(world, "recruit")
    if err:
        return err
    err = _too_far(hero, x, y)
    if err:
        return err
    target = next((t for t in world.things
                    if t.alive and t.kind in RECRUITABLE_KINDS and t.leader is None
                    and t.x == x and t.y == y), None)
    if target is None:
        return ["nothing recruitable at (%d, %d)" % (x, y)]
    target.leader = hero
    return ["recruited the %s at (%d, %d)" % (target.kind, x, y)]


def _do_dismiss(world, rest):
    """/dismiss <x> <y>: the same as touching one of yours and pressing
    r, just aimed at an exact spot -- and, unlike the ordinary "r" key
    (which only ever touches kind "companion"), works on a bought
    worker or soldier too, which otherwise has no way to be released
    at all."""
    if world is None:
        return ["no game running to dismiss with"]
    xy, err = _parse_xy(rest, "/dismiss <x> <y>")
    if err:
        return err
    x, y = xy
    hero, err = _hero(world, "dismiss")
    if err:
        return err
    err = _too_far(hero, x, y)
    if err:
        return err
    target = next((t for t in world.things
                    if t.alive and t.leader is hero and t.x == x and t.y == y), None)
    if target is None:
        return ["nothing of yours to dismiss at (%d, %d)" % (x, y)]
    target.leader = None
    return ["dismissed the %s at (%d, %d)" % (target.kind, x, y)]


def run_local_command(said, project, world=None, history=None):
    """A single typed command line's result, as the lines chat_break
    should show. Purely local -- there is no server connection from the
    plain terminal player the way world3d.html/index.html have, so this
    is deliberately a smaller set than their own CHAT_COMMANDS: nobody
    else to /who, nothing here to /clear. Blank input is treated as
    /help, the friendliest thing to do with a stray keypress. `world`
    is the live game; `history` is the running log /log and /forget work
    against (both None is fine for anything that doesn't need them,
    including most direct tests of a single command in isolation).

    Returns ("quit", None) if the command means leave the game, or
    ("show", lines) with what to put on the result screen otherwise.
    """
    said = said.strip().lstrip("/")
    cut = said.find(" ")
    word = (said if cut < 0 else said[:cut]).lower() or "help"
    rest = "" if cut < 0 else said[cut + 1:]
    if word == "help":
        return "show", _local_help_lines(project, rest)
    if word == "mine":
        lines = _do_mine(world, rest)
        _history_add(history, lines)
        return "show", lines
    if word == "attack":
        lines = _do_attack(world, rest)
        _history_add(history, lines)
        return "show", lines
    if word == "recruit":
        lines = _do_recruit(world, rest)
        _history_add(history, lines)
        return "show", lines
    if word == "dismiss":
        lines = _do_dismiss(world, rest)
        _history_add(history, lines)
        return "show", lines
    if word == "units":
        lines = _do_units(world)
        _history_add(history, lines)
        return "show", lines
    if word == "list":
        lines = _do_list(world)
        _history_add(history, lines)
        return "show", lines
    if word == "name":
        lines = _do_name(world, rest)
        _history_add(history, lines)
        return "show", lines
    if word == "log":
        return "show", _do_log(history, rest)
    if word == "forget":
        return "show", _do_forget(history, rest)
    if word in ("quit", "q"):
        return "quit", None
    return "show", ["no such command: /%s -- try /help" % word]


def draw_chat_result(lines):
    out = [HOME_CLEAR, "=" * 40, " chat", "=" * 40, ""]
    out.extend(lines if lines else ["(type a command, e.g. /help)"])
    out.append("")
    out.append("(blank line closes chat)")
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


def chat_break(project, keyboard, world, history):
    """Pressed "/" during play: opens a chat session that stays open --
    requested directly ("fix chat to stay open") after it turned out to
    be one command and straight back to the game every single time.
    Hands the terminal back to normal cooked input the whole time it's
    open (so the phone's own text box/keyboard behaves exactly like it
    does everywhere else in this app, rather than gameplay's usual
    single-key swallowing): type a command, see its result on its own
    screen, type the next one right after with no need to press "/"
    again, however many in a row -- a blank line (or Ctrl-D) is what
    actually closes it and goes back to the running game. `history` is
    play()'s own running log, the same list across every call this
    session -- see run_local_command for what actually lands in it, and
    /log and /forget for reading it back and trimming it.

    Returns True if the command was to quit the game outright.
    """
    keyboard.pause()
    sys.stdout.write(SHOW)
    sys.stdout.flush()
    lines = []
    while True:
        draw_chat_result(lines)
        try:
            said = input("\n/")
        except EOFError:
            said = "quit"   # the same safety-valve exit pressing q always is
        if not said.strip():
            break
        kind, lines = run_local_command(said, project, world, history)
        if kind == "quit":
            sys.stdout.write(HIDE)
            return True
    sys.stdout.write(HIDE)
    keyboard.resume()
    return False


def _entity_line(t):
    """One entity's own line, in /list's exact format -- kept as one
    spot so the menu and the chat command never drift apart."""
    name = ("%s (%s)" % (t.label, t.kind)) if t.label else t.kind
    return "%s at (%d, %d) -- health %d" % (name, t.x, t.y, t.health)


def _act_on_screen(builder, keyboard, world, target, history):
    """Do what to the entity just picked -- the same four verbs /name,
    /recruit, /dismiss and /attack already are, just aimed by picking
    from a menu instead of typing coordinates by hand. Reuses those
    exact functions (and so their exact validation/messages -- "too
    far away", "nothing recruitable there", and so on) rather than
    a second copy of the same rules."""
    coord = "%d %d" % (target.x, target.y)
    while target.alive:
        sys.stdout.write(HOME_CLEAR)
        print(_entity_line(target) + "\n")
        idx = builder.menu(["name it", "recruit it", "dismiss it", "attack it"],
                            prompt="do what?", back_label="back")
        if idx is None:
            return
        if idx == 0:
            sys.stdout.write(SHOW)
            keyboard.pause()
            new_name = input("call it what? ")
            keyboard.resume()
            sys.stdout.write(HIDE)
            lines = (_do_name(world, coord + " " + new_name) if new_name.strip()
                      else ["give it an actual name"])
        elif idx == 1:
            lines = _do_recruit(world, coord)
        elif idx == 2:
            lines = _do_dismiss(world, coord)
        else:
            lines = _do_attack(world, coord)
        _history_add(history, lines)
        sys.stdout.write(HOME_CLEAR)
        print("\n".join(lines))
        sys.stdout.write(SHOW)
        keyboard.pause()
        input("\nenter to continue ")
        keyboard.resume()
        sys.stdout.write(HIDE)


def _pick_existing_screen(builder, keyboard, world, history):
    """Page one: every entity currently in the world (the same list
    /list prints), pick one to act on."""
    while True:
        things = sorted((t for t in world.things if t.alive),
                         key=lambda t: (t.kind, t.x, t.y))
        sys.stdout.write(HOME_CLEAR)
        if not things:
            print("nothing in the world")
            sys.stdout.write(SHOW)
            keyboard.pause()
            input("\nenter to go back ")
            keyboard.resume()
            sys.stdout.write(HIDE)
            return
        print("pick one to act on\n")
        idx = builder.menu([_entity_line(t) for t in things],
                            prompt="", back_label="back")
        if idx is None:
            return
        _act_on_screen(builder, keyboard, world, things[idx], history)


def _pick_spawn_screen(builder, keyboard, project, world):
    """Page two: every kind this game's roster defines (in the order
    the roster lists them, each kind once even if it appears more than
    once with different starting counts), pick one to spawn fresh --
    at the hero's own spot, the same "arrives standing on you" place
    the recruit tile already spawns a bought unit at, or an empty
    square if there's no living hero to stand on.

    role "player" kinds are left off this list on purpose: a spawned
    copy has no controller of its own (nothing here hands it one), and
    an uncontrolled character answers to the very same keypresses the
    real one does (see World.keys_for) -- so a second "hero" would not
    sit there inertly, it would move in lockstep with the real one,
    step for step, forever. Spawning more of whatever you already are
    was never really "populating the world" the way a bandit or a
    turret is."""
    kinds = []
    seen = set()
    for char in project.get("characters", []):
        kind = str(char.get("kind", "")).strip()
        if kind and kind not in seen and char.get("role") != "player":
            seen.add(kind)
            kinds.append(kind)
    sys.stdout.write(HOME_CLEAR)
    if not kinds:
        print("this game has no characters defined")
        sys.stdout.write(SHOW)
        keyboard.pause()
        input("\nenter to go back ")
        keyboard.resume()
        sys.stdout.write(HIDE)
        return
    print("spawn which kind?\n")
    idx = builder.menu(kinds, prompt="", back_label="back")
    if idx is None:
        return
    kind = kinds[idx]
    hero = next((t for t in world.things if t.role == "player" and t.alive), None)
    thing = (world.spawn(kind, hero.x, hero.y) if hero is not None
             else world.spawn_somewhere(kind))
    sys.stdout.write(HOME_CLEAR)
    print("spawned a %s at (%d, %d)" % (thing.kind, thing.x, thing.y) if thing is not None
          else "could not spawn a %s" % kind)
    sys.stdout.write(SHOW)
    keyboard.pause()
    input("\nenter to continue ")
    keyboard.resume()
    sys.stdout.write(HIDE)


def entities_screen(project, keyboard, world, history):
    """Pressed "p" during play: an arrow-key alternative to typing
    /list, /name, /recruit, /dismiss and /attack's coordinates by
    hand -- requested directly, "menu selector for existing and also
    separate page potential entity to manipulate or spawn into the
    world... menus work also with arrows and blue highlight... but
    also number for which choice." Reuses builder.menu() exactly, the
    same arrow+highlight+digit-jump menu every terminal screen already
    uses, rather than a second menu component of its own.

    No keyboard.pause()/.resume() needed around builder.menu() itself
    -- it wants the same raw/cbreak mode gameplay is already in, unlike
    chat_break's cooked input() line. Only the name prompt and the
    "enter to continue" pauses need that dance, same as chat_break.

    One known, narrow gap: SPARK_PLAIN (or any terminal builder.menu()
    itself decides can't do arrows) falls back to a numbered, typed
    list -- normally fine, but that fallback never touches Keyboard
    mode at all, so here specifically it would run with the ambient
    mode still cbreak (echo off, no line editing) rather than properly
    cooked. Accepted rather than fixed: SPARK_PLAIN is already a
    documented, explicit opt-out for exotic terminals, and pressing
    "p" while it's set is a narrow combination on top of an already
    narrow one.
    """
    from . import builder   # deferred: builder.py itself imports this module
    while True:
        sys.stdout.write(HOME_CLEAR)
        print("entities\n")
        choice = builder.menu(["existing entities", "spawn a new entity"],
                               prompt="entities", back_label="back to the game")
        if choice is None:
            return
        if choice == 0:
            _pick_existing_screen(builder, keyboard, world, history)
        else:
            _pick_spawn_screen(builder, keyboard, project, world)


def play(project, max_ticks=None, history=None):
    """Run a project. With max_ticks set, runs headless -- handy for testing.

    `history` lets a caller hand in its own running log instead of this
    call starting a fresh one -- see engine/chatshell.py, which launches
    play() as one "program" among several sharing a single log that is
    never cleared across the whole session, requested directly: "launches
    different programs using always same chat log never deleting it."
    """
    world = World(project)
    speed = max(1, project.get("world", {}).get("speed", 6))
    delay = 1.0 / speed
    headless = max_ticks is not None or not sys.stdin.isatty()
    # You are playing your own game on your own phone, so the `open` tile is
    # allowed here. live.Session deliberately leaves it off.
    world.may_open = not headless
    # /mine, /units, /name results, for /log and /forget -- a caller's own
    # list if it gave one, else a fresh one just for this call, same as always.
    chat_history = history if history is not None else []

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
                    if chat_break(project, keyboard, world, chat_history):
                        break
                    continue   # this tick's own keys are stale by now
                if "p" in world.keys and not headless:
                    entities_screen(project, keyboard, world, chat_history)
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
