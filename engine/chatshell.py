"""Spark, as one ASCII display and one chat log -- everything (browsing
games, building characters and brains, playing) reached by typed
commands over a single, never-cleared history, rather than the
arrow-key menus builder.py's screens use.

Requested directly, after confirming full scope ("everything, editor
included"): "make so spark entirely is just one ASC display and chat
entirely but launches different programs using always same chat log
never deleting it and uses chat commands to navigate."

    python3 spark.py                 # now opens this, not builder.main_menu
    python3 spark.py games/x.json    # same, with that game already open

This is a first pass, not a 1:1 port of every builder.py screen: games
(list/new/open), characters (list/add/focus/edit basic fields), brain
rows (list/add via /when+/do/delete), world settings, rename, save,
and playing (launches runner.play() with THIS module's own history, so
the log really does carry across into a running game and back) are
all here. GitHub push/pull/invite, the players list, the frames sprite
editor, Python "your own tiles" approval, folding a row into a named
tile, deleting a character, and undo are not yet ported -- builder.py's
own screens for those still work standalone (`python3 -c "from engine
import builder; builder.push_screen(project)"`, e.g.), just not
reachable from here yet. Said plainly rather than silently: this is a
big, honest first increment of a very large ask, not a finished
replacement of every
feature.

Design: every command is a small function of (state, rest) -> lines,
called directly by tests too (no terminal needed) -- see
tests/check_chatshell.py. The terminal loop itself (run(), _draw()) is
deliberately thin on top of that, the same split runner.py and
termux_chat.py both already use.
"""

import shutil
import sys
import traceback

from . import brain, builder, runner, tiles
from .runner import HOME_CLEAR
from .world import COLORS

PAGE_SIZE = 10   # matches runner.py's own /log convention


# ---------------------------------------------------------------------------
# tile calls typed inline -- "touch kind=companion" or "move dir=toward it"
# ---------------------------------------------------------------------------

def parse_args_text(text):
    """"a=1, b=hello there" -> {"a": "1", "b": "hello there"} -- comma-
    separated, not space-separated, specifically so a value (a `choice`
    param like "toward it") can hold spaces without needing quoting."""
    args = {}
    text = text.strip()
    if not text:
        return args
    for piece in text.split(","):
        if "=" not in piece:
            continue
        k, v = piece.split("=", 1)
        k = k.strip()
        if k:
            args[k] = v.strip()
    return args


def fill_tile_args(tile, project, raw_args):
    """raw_args: {name: string}, from parse_args_text. Returns (args,
    errors) -- args has every one of tile's own params, using its
    default for whichever raw_args left out; errors is a list of plain-
    English complaints (int/choice/kind values that don't fit), empty
    if everything given was valid."""
    args = {}
    errors = []
    for param in tile.params:
        raw = raw_args.get(param.name)
        if raw is None:
            args[param.name] = param.default
            continue
        if param.kind == "int":
            try:
                args[param.name] = int(raw)
            except ValueError:
                errors.append("%s needs a plain number, not '%s'" % (param.name, raw))
        elif param.kind == "choice":
            match = next((c for c in param.choices if c.lower() == raw.lower()), None)
            if match is None:
                errors.append("%s must be one of: %s" % (param.name, ", ".join(param.choices)))
            else:
                args[param.name] = match
        elif param.kind == "kind":
            choices = builder.kinds_in(project)
            match = next((c for c in choices if c.lower() == raw.lower()), None)
            if match is None:
                errors.append("%s must be one of: %s" % (param.name, ", ".join(choices)))
            else:
                args[param.name] = match
        else:
            args[param.name] = raw
    return args, errors


# ---------------------------------------------------------------------------
# state -- one dict, mutated in place by every command
# ---------------------------------------------------------------------------

def new_state():
    return {
        "project": None,    # the open game, or None (top level)
        "focus": None,       # a character's own "kind", or None
        "building": None,    # {"when": [...], "do": [...]} while composing a row
        "history": [],       # every result line ever shown -- never cleared
    }


def _current_char(state):
    if state["project"] is None or state["focus"] is None:
        return None
    return next((c for c in state["project"]["characters"] if c["kind"] == state["focus"]),
                None)


def _describe_char(char):
    return ("%s (%s): health %d, %d at start, %s, %s, %d brain row%s, %d sprite frame%s"
            % (char["kind"], char["glyph"], char["health"], char["count"], char["role"],
               "solid" if char["solid"] else "walk-through",
               len(char["brain"]), "" if len(char["brain"]) == 1 else "s",
               len(char.get("frames") or []), "" if len(char.get("frames") or []) == 1 else "s"))


# ---------------------------------------------------------------------------
# commands -- each one a plain function of (state, rest), returning the
# lines to show, OR {"action": "play"} / {"action": "quit"}, the two the
# main loop itself has to act on rather than just print
# ---------------------------------------------------------------------------

def cmd_help(state, rest):
    if state["building"] is not None:
        return ["/when <tile> [args]  and  /do <tile> [args] -- add to this row",
                "/tiles -- every tile you can use in each",
                "/done -- save this row to the brain",
                "/cancel -- throw it away instead"]
    if state["focus"] is not None:
        return ["/glyph <c>  /color <name>  /role player|prop  /count <n>",
                "/health <n>  /solid yes|no",
                "/rows -- list its brain  /newrow  /delrow <n>",
                "/back -- done with this character"]
    if state["project"] is not None:
        return ["/characters  /character <kind>  /newchar <kind>",
                "/world width=.. height=.. speed=.. wrap=..",
                "/rename <name>  /save  /play",
                "/back -- close this game",
                "/page [n]  /quit"]
    return ["/games -- what's saved  /new <name>  /open <name>",
            "/page [n]  /quit"]


def cmd_games(state, rest):
    games = brain.list_games()
    if not games:
        return ["no saved games yet -- /new <name> to make one"]
    return (["%d saved game%s:" % (len(games), "" if len(games) == 1 else "s")]
            + ["  " + p.stem for p in games])


def _drop_building(state):
    """Clears any row still being built, and says so if one really was
    lost -- caught on self-review, a real bug: switching which
    character (or which game entirely) was focused used to leave
    state["building"] pointing at the OLD character's half-finished
    row, so a /done typed afterward silently attached it to whichever
    character happened to be focused by then instead, not the one it
    was actually being built for. Called by every command that changes
    state["focus"] or state["project"]. Returns a warning line, or
    None if nothing was actually lost."""
    if state["building"] is None:
        return None
    state["building"] = None
    return "(a row you were building for someone else was discarded)"


def cmd_new(state, rest):
    name = rest.strip()
    if not name:
        return ["try: /new <name>"]
    if (brain.GAMES_DIR / (name + ".json")).exists():
        return ["a game called '%s' already exists -- /open %s instead" % (name, name)]
    warning = _drop_building(state)
    state["project"] = brain.new_project(name)
    state["focus"] = None
    lines = ["started a new game called '%s' -- /save to write it to disk" % name]
    return lines + [warning] if warning else lines


def cmd_open(state, rest):
    name = rest.strip()
    if not name:
        return ["try: /open <name>"]
    path = brain.GAMES_DIR / (name + ".json")
    if not path.exists():
        return ["no game called '%s' -- /games to see what's saved" % name]
    warning = _drop_building(state)
    state["project"] = brain.load(path)
    state["focus"] = None
    lines = ["opened '%s' (%d characters)" % (name, len(state["project"]["characters"]))]
    return lines + [warning] if warning else lines


def cmd_save(state, rest):
    if state["project"] is None:
        return ["nothing open to save"]
    path = brain.save(state["project"], brain.GAMES_DIR / (state["project"]["name"] + ".json"))
    return ["saved to " + str(path)]


def cmd_rename(state, rest):
    if state["project"] is None:
        return ["nothing open to rename"]
    name = rest.strip()
    if not name:
        return ["try: /rename <name>"]
    was = state["project"]["name"]
    state["project"]["name"] = name
    return ["renamed '%s' to '%s' -- /save to write it under the new name" % (was, name)]


def cmd_back(state, rest):
    if state["building"] is not None:
        state["building"] = None
        return ["discarded -- back to the brain"]
    if state["focus"] is not None:
        state["focus"] = None
        return ["back to the character list"]
    if state["project"] is not None:
        state["project"] = None
        return ["closed -- back to the top"]
    return ["already at the top"]


def cmd_characters(state, rest):
    if state["project"] is None:
        return ["open a game first -- /open <name> or /new <name>"]
    chars = state["project"]["characters"]
    if not chars:
        return ["no characters yet -- /newchar <kind>"]
    return ["%s  %-12s %d rows, %d at start" % (c["glyph"], c["kind"], len(c["brain"]), c["count"])
            for c in chars]


def cmd_newchar(state, rest):
    if state["project"] is None:
        return ["open a game first"]
    name = rest.strip()
    if not name:
        return ["try: /newchar <kind>"]
    chars = state["project"]["characters"]
    if any(c["kind"] == name for c in chars):
        return ["'%s' already exists -- /character %s to edit it" % (name, name)]
    # A brand new kind can never be the one already focused, so this is
    # always a genuine switch away from whoever (if anyone) that was.
    warning = _drop_building(state)
    char = brain.new_character(name, name[0])
    chars.append(char)
    state["focus"] = name
    lines = ["made '%s' -- /glyph, /color, /role, /count to fine-tune it" % name]
    return lines + [warning] if warning else lines


def cmd_character(state, rest):
    if state["project"] is None:
        return ["open a game first"]
    name = rest.strip()
    char = next((c for c in state["project"]["characters"] if c["kind"] == name), None)
    if char is None:
        return ["no character called '%s' -- /characters to see what's there" % name]
    # Re-focusing the SAME character you're already on (e.g. mid-row-build)
    # isn't a real switch -- nothing to lose, nothing to warn about.
    warning = _drop_building(state) if name != state["focus"] else None
    state["focus"] = name
    lines = [_describe_char(char)]
    return lines + [warning] if warning else lines


def cmd_glyph(state, rest):
    char = _current_char(state)
    if char is None:
        return ["focus a character first -- /character <kind>"]
    g = rest.strip()
    if not g:
        return ["try: /glyph <c>"]
    char["glyph"] = g[:1]
    return ["'%s' now looks like '%s'" % (char["kind"], char["glyph"])]


def cmd_color(state, rest):
    char = _current_char(state)
    if char is None:
        return ["focus a character first"]
    name = rest.strip().lower()
    match = next((c for c in COLORS if c.lower() == name), None)
    if match is None:
        return ["not a colour -- try one of: " + ", ".join(COLORS)]
    char["color"] = match
    return ["'%s' is now %s" % (char["kind"], match)]


def cmd_role(state, rest):
    char = _current_char(state)
    if char is None:
        return ["focus a character first"]
    word = rest.strip().lower()
    if word not in ("player", "prop"):
        return ["try: /role player  or  /role prop"]
    char["role"] = word
    return ["'%s' is now %s" % (char["kind"], word)]


def cmd_count(state, rest):
    char = _current_char(state)
    if char is None:
        return ["focus a character first"]
    try:
        n = max(0, int(rest.strip()))
    except ValueError:
        return ["try: /count <n>"]
    char["count"] = n
    return ["%d of '%s' will start in the world" % (n, char["kind"])]


def cmd_health(state, rest):
    char = _current_char(state)
    if char is None:
        return ["focus a character first"]
    try:
        n = max(1, int(rest.strip()))
    except ValueError:
        return ["try: /health <n>"]
    char["health"] = n
    return ["'%s' now has %d health" % (char["kind"], n)]


def cmd_solid(state, rest):
    char = _current_char(state)
    if char is None:
        return ["focus a character first"]
    word = rest.strip().lower()
    if word not in ("yes", "no"):
        return ["try: /solid yes  or  /solid no"]
    char["solid"] = (word == "yes")
    return ["'%s' is now %s" % (char["kind"], "solid" if char["solid"] else "walk-through")]


def cmd_rows(state, rest):
    char = _current_char(state)
    if char is None:
        return ["focus a character first"]
    if not char["brain"]:
        return ["no rows yet -- /newrow to add one"]
    return ["%d. %s" % (i, brain.describe_row(r)) for i, r in enumerate(char["brain"], 1)]


def cmd_newrow(state, rest):
    if _current_char(state) is None:
        return ["focus a character first"]
    state["building"] = {"when": [], "do": []}
    return ["building a new row -- /when <tile> [args], /do <tile> [args], /tiles, /done, /cancel"]


def cmd_delrow(state, rest):
    char = _current_char(state)
    if char is None:
        return ["focus a character first"]
    try:
        n = int(rest.strip())
    except ValueError:
        return ["try: /delrow <n>"]
    if n < 1 or n > len(char["brain"]):
        return ["no row %d" % n]
    removed = char["brain"].pop(n - 1)
    return ["removed row %d: %s" % (n, brain.describe_row(removed))]


def cmd_tiles(state, rest):
    return ["WHEN tiles: " + ", ".join(sorted(tiles.SENSORS)),
            "DO tiles: " + ", ".join(sorted(tiles.ACTIONS))]


def _add_tile(state, registry, side_label, rest):
    if state["building"] is None:
        return ["/newrow first"]
    parts = rest.strip().split(None, 1)
    if not parts:
        return ["try: /%s <tile> [args]" % side_label.lower()]
    tile_id, arg_text = parts[0], (parts[1] if len(parts) > 1 else "")
    tile = registry.get(tile_id)
    if tile is None:
        other = tiles.ACTIONS if registry is tiles.SENSORS else tiles.SENSORS
        if tile_id in other:
            other_label = "DO" if registry is tiles.SENSORS else "WHEN"
            return ["'%s' is a %s tile, not %s -- /tiles to see what fits here"
                    % (tile_id, other_label, side_label)]
        return ["no tile called '%s' -- /tiles to see what's available" % tile_id]
    args, errors = fill_tile_args(tile, state["project"], parse_args_text(arg_text))
    if errors:
        return errors
    side = "when" if registry is tiles.SENSORS else "do"
    state["building"][side].append({"tile": tile.id, "args": args})
    return ["added: " + tile.describe(args)]


def cmd_when(state, rest):
    return _add_tile(state, tiles.SENSORS, "WHEN", rest)


def cmd_do(state, rest):
    return _add_tile(state, tiles.ACTIONS, "DO", rest)


def cmd_done(state, rest):
    if state["building"] is None:
        return ["nothing being built -- /newrow first"]
    row = state["building"]
    state["building"] = None
    if not (row["when"] or row["do"]):
        return ["empty row discarded"]
    _current_char(state)["brain"].append(row)
    return ["added: " + brain.describe_row(row)]


def cmd_cancel(state, rest):
    if state["building"] is None:
        return ["nothing being built"]
    state["building"] = None
    return ["discarded"]


def cmd_world(state, rest):
    if state["project"] is None:
        return ["open a game first"]
    settings = state["project"]["world"]
    kv = parse_args_text(rest)
    if not kv:
        return ["width %d, height %d, speed %d, wrap %s"
                % (settings["width"], settings["height"], settings.get("speed", 6),
                   "yes" if settings.get("wrap") else "no")]
    # Parse and clamp into a scratch dict first, settings itself untouched --
    # a bad value anywhere (caught here on self-review: "/world width=50,
    # height=abc" was silently leaving width changed even while reporting
    # failure) must refuse the WHOLE command, not apply everything that
    # happened to come before the bad one.
    new = {}
    try:
        if "width" in kv:
            new["width"] = max(5, min(70, int(kv["width"])))
        if "height" in kv:
            new["height"] = max(5, min(20, int(kv["height"])))
        if "speed" in kv:
            new["speed"] = max(1, min(30, int(kv["speed"])))
    except ValueError:
        return ["width/height/speed need plain numbers -- nothing changed"]
    if "wrap" in kv:
        new["wrap"] = kv["wrap"].strip().lower() in ("yes", "true", "1", "on")
    if not new:
        return ["try: /world width=.. height=.. speed=.. wrap=.."]
    settings.update(new)
    return ["updated: " + ", ".join(sorted(new))]


def cmd_play(state, rest):
    if state["project"] is None:
        return ["open a game first"]
    return {"action": "play"}


def cmd_quit(state, rest):
    return {"action": "quit"}


def _page_count(history):
    if not history:
        return 0
    return -(-len(history) // PAGE_SIZE)


def cmd_page(state, rest):
    total = _page_count(state["history"])
    if total == 0:
        return ["nothing logged yet"]
    rest = rest.strip()
    if rest:
        try:
            n = int(rest)
        except ValueError:
            return ["page number needs to be a plain number: /page [n]"]
    else:
        n = total
    if n < 1 or n > total:
        return ["no page %d -- there are %d" % (n, total)]
    start = (n - 1) * PAGE_SIZE
    lines = ["-- page %d of %d --" % (n, total)]
    lines.extend(state["history"][start:start + PAGE_SIZE])
    return lines


COMMANDS = {
    "help": cmd_help, "games": cmd_games, "new": cmd_new, "open": cmd_open,
    "characters": cmd_characters, "character": cmd_character, "newchar": cmd_newchar,
    "glyph": cmd_glyph, "color": cmd_color, "role": cmd_role, "count": cmd_count,
    "health": cmd_health, "solid": cmd_solid,
    "rows": cmd_rows, "newrow": cmd_newrow, "delrow": cmd_delrow,
    "when": cmd_when, "do": cmd_do, "tiles": cmd_tiles, "done": cmd_done, "cancel": cmd_cancel,
    "world": cmd_world, "rename": cmd_rename, "save": cmd_save,
    "back": cmd_back, "play": cmd_play,
    "page": cmd_page, "log": cmd_page,
    "quit": cmd_quit, "q": cmd_quit,
}


# Navigating the log itself must never grow the log -- the same reasoning
# runner.py's own /log, /forget and /help already follow (see its
# _do_log's own docstring).
_NOT_LOGGED = {"help", "page", "log"}


def run_command(state, said):
    """Runs one typed line, appends whatever it says to state["history"]
    (never trimmed -- requested directly, "always same chat log never
    deleting it"), and returns the same result. A blank line (or one
    that's just "/") is /help, the friendliest thing to do with a stray
    press."""
    said = said.strip()
    if not said or said == "/":
        said = "/help"
    said = said.lstrip("/")
    cut = said.find(" ")
    word = (said if cut < 0 else said[:cut]).lower()
    rest = "" if cut < 0 else said[cut + 1:]
    fn = COMMANDS.get(word)
    if fn is None:
        result = ["no such command: /%s -- /help to see what's available" % word]
    else:
        result = fn(state, rest)
    if isinstance(result, list) and word not in _NOT_LOGGED:
        state["history"].append("you: /" + word + ((" " + rest) if rest else ""))
        state["history"].extend(result)
    return result


# ---------------------------------------------------------------------------
# the terminal loop -- thin: draws, reads a cooked line, runs it
# ---------------------------------------------------------------------------

def _breadcrumb(state):
    if state["project"] is None:
        return "top level"
    parts = ["editing '%s'" % state["project"]["name"]]
    if state["focus"] is not None:
        parts.append("character '%s'" % state["focus"])
    if state["building"] is not None:
        parts.append("building a row")
    return " > ".join(parts)


def _fit(text, width):
    """Truncate to at most `width` visible columns, marking it with an
    ellipsis if anything was cut -- same shape as builder.py's own
    private _fit(), kept as its own small copy here rather than
    reaching into another module's underscore-prefixed helper."""
    if width < 1:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return "…"
    return text[:width - 1] + "…"


def _draw(state):
    cols, rows = shutil.get_terminal_size(fallback=(80, 24))
    # 5 logo rows + a blank + the breadcrumb + two rules + the input line
    # itself, recomputed from the real terminal size every redraw -- never
    # a guessed constant, the same lesson this whole project's other
    # screens already learned the hard way.
    log_h = max(3, rows - 10)
    out = [HOME_CLEAR]
    out.extend(_fit(" " + line, cols) for line in builder.logo())
    out.append("")
    out.append(_fit(" " + _breadcrumb(state), cols))
    out.append("-" * min(40, cols))
    for line in state["history"][-log_h:]:
        out.append(_fit(line, cols))
    out.append("-" * min(40, cols))
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


def run(project=None):
    state = new_state()
    if project is not None:
        state["project"] = project
        state["history"].append("opened '%s' (%d characters)"
                                 % (project["name"], len(project["characters"])))
    state["history"].append("type /help any time to see what you can do")
    while True:
        try:
            _draw(state)
        except Exception:
            # Bare-bones fallback, no logo/truncation/anything fancy that
            # could itself be what broke -- the goal here is only ever
            # "show SOMETHING," since a silent failure at this exact spot
            # would look identical to the process having simply stopped
            # responding, with no way to tell the difference or report it.
            print(HOME_CLEAR)
            print("(the normal display broke -- this is a fallback)\n")
            print(traceback.format_exc())
        try:
            said = input("\n> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            # Cooked mode (no termios switching happens anywhere in this
            # module, unlike runner.py/termux_chat.py's raw-key loops) means
            # Ctrl-C here really is a plain KeyboardInterrupt, not silently
            # swallowed -- leave the same way /quit does, not a traceback.
            print()
            break
        try:
            result = run_command(state, said)
            if isinstance(result, dict):
                if result["action"] == "quit":
                    break
                if result["action"] == "play":
                    runner.play(state["project"], history=state["history"])
                    state["history"].append("back from playing '%s'" % state["project"]["name"])
        except Exception:
            # One bad command must never take the whole session down --
            # "always same chat log never deleting it" means the log has
            # to survive a real bug in a single command too, not just
            # normal use. The error itself lands right in the log, plain
            # to read (and to report back), instead of a traceback that
            # scrolls past and looks indistinguishable from the process
            # having simply stopped responding.
            state["history"].append("something went wrong running that -- " + said)
            state["history"].extend(traceback.format_exc().rstrip("\n").split("\n"))
    print("bye")
