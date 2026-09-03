"""The no-code editor: every choice is a numbered menu, nothing is typed as code."""

import json
import sys

from . import brain, runner, status, tiles
from .world import COLORS

CLEAR = "\033[H\033[2J"

# ---------------------------------------------------------------------------
# undo
#
# The whole game, copied as text, once per change. Games are small, so sixty
# copies cost nothing, and keeping the entire thing means nothing can be
# half-undone and no screen has to know which fields it owns.
#
# Restoring empties the dict and refills it rather than rebinding the name,
# because every screen here is holding the same dict and a rebind would leave
# them all editing the abandoned one.
#
# The browser keeps its own identical stack. They are deliberately separate:
# each undoes what you did in front of it.
# ---------------------------------------------------------------------------

UNDO_DEPTH = 60
_history = []


def remember(project):
    if project is None:
        return
    _history.append(json.dumps(project))
    if len(_history) > UNDO_DEPTH:
        _history.pop(0)


def forget_if_same(project):
    """Drop the last mark if nothing changed after it."""
    if _history and _history[-1] == json.dumps(project):
        _history.pop()


def undo(project):
    """Put the game back as it was before the last change. True if it moved."""
    if not _history:
        return False
    project.clear()
    project.update(json.loads(_history.pop()))
    return True


def undo_label():
    return ("undo the last change (%d)" % len(_history) if _history
            else "undo the last change (nothing yet)")


def forget_history():
    """A different game means a fresh history -- see openGame in index.html."""
    _history.clear()


# --------------------------------------------------------------------------
# tiny prompt helpers -- all input goes through these
# --------------------------------------------------------------------------

def header(title):
    print(CLEAR + status.line())
    print("=" * 46)
    print(" " + title)
    print("=" * 46)


def ask(prompt, default=None):
    suffix = " [%s]" % default if default not in (None, "") else ""
    try:
        answer = input("%s%s: " % (prompt, suffix)).strip()
    except EOFError:
        raise SystemExit(0)
    return answer or (str(default) if default is not None else "")


def ask_int(prompt, default):
    while True:
        answer = ask(prompt, default)
        try:
            return int(answer)
        except ValueError:
            print("  numbers only, please")


def ask_yes(prompt, default=False):
    answer = ask(prompt + " (y/n)", "y" if default else "n").lower()
    return answer.startswith("y")


def menu(options, prompt="pick a number", allow_back=True, back_label="back"):
    """Show a numbered list. Returns the index, or None for back/blank.

    Two words work at any menu instead of a number: `browser` opens the
    drag-and-drop editor, `players` lists who is connected.
    """
    for i, label in enumerate(options, 1):
        print(" %2d. %s" % (i, label))
    if allow_back:
        print("  0. %s" % back_label)
    while True:
        answer = ask(prompt, "0" if allow_back else None)
        word = answer.strip().lower()
        if word in ("browser", "b"):
            open_browser_editor()
            continue
        if word in ("players", "who"):
            players_screen()
            continue
        if answer in ("", "0") and allow_back:
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        print("  pick one of the numbers shown, or type browser or players")


def kinds_in(project):
    return [c["kind"] for c in project.get("characters", [])] + ["anything"]


# --------------------------------------------------------------------------
# opening the browser editor without leaving the menus
# --------------------------------------------------------------------------

_server_thread = None


def open_browser_editor(share=False):
    """Start the editor server alongside the menus and open it.

    It runs on its own thread so the terminal stays usable -- you can have
    both editors open at once. They read and write the same games/ folder.
    """
    global _server_thread
    import subprocess
    import threading
    import time
    from . import server

    header("Browser editor")
    if _server_thread is None or not _server_thread.is_alive():
        server.OWNER_URL = ""
        _server_thread = threading.Thread(
            target=server.serve,
            kwargs={"bind": "0.0.0.0" if share else "127.0.0.1",
                    "open_browser": False, "quiet": True},
            daemon=True)
        _server_thread.start()
        for _ in range(40):                     # wait for it to claim the port
            if server.OWNER_URL:
                break
            time.sleep(0.05)

    if not server.OWNER_URL:
        print(" could not start it -- is something already on port 8765?")
        print(" try:  python3 spark.py edit 9000")
        ask("press enter")
        return

    print(" Open on this phone:\n")
    print("   " + server.OWNER_URL + "\n")
    if share:
        print(" Others on this wifi: " + server.lan_address(8765) + "\n")
    opened = False
    try:
        subprocess.run(["termux-open-url", server.OWNER_URL], timeout=5,
                       capture_output=True)
        opened = True
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    print(wrap_note(
        "Opening your browser now." if opened else
        "Type that address into your browser -- termux-open-url is not "
        "installed here, so I cannot open it for you."))
    print(wrap_note(
        "Both editors are live at once and share the games/ folder. Save in "
        "one, then re-open the game in the other to see the change. The "
        "server stops when you leave Spark."))
    ask("press enter")


def wrap_note(text, width=44):
    words, line, out = text.split(), "", []
    for word in words:
        if len(line) + len(word) + 1 > width:
            out.append(" " + line)
            line = word
        else:
            line = (line + " " + word).strip()
    out.append(" " + line)
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# placing one tile: ask its question list, one plain-English prompt each
# --------------------------------------------------------------------------

def fill_params(tile, project):
    args = {}
    for param in tile.params:
        if param.kind == "int":
            args[param.name] = ask_int("  " + param.prompt, param.default)
        elif param.kind == "choice":
            print("  " + param.prompt)
            index = menu(param.choices, "  pick", allow_back=False)
            args[param.name] = param.choices[index]
        elif param.kind == "kind":
            choices = kinds_in(project)
            print("  " + param.prompt)
            index = menu(choices, "  pick", allow_back=False)
            args[param.name] = choices[index]
        else:
            args[param.name] = ask("  " + param.prompt, param.default)
    return args


def my_tiles(project):
    """Your own named tiles, kept in the game file so they travel with it."""
    return project.setdefault("tiles", [])


def find_my_tile(project, name):
    for own in my_tiles(project):
        if own.get("name") == name:
            return own
    return None


def describe_mine(side, own):
    """One of your tiles, as it reads in the half it has been put in."""
    inside = len(own.get(side, []))
    return "%s%s" % (own.get("name", "?"),
                     "" if inside else
                     "   (nothing in its %s half)" % side.upper())


def fold_row(project, rows, index):
    """Fold a whole row into one tile of your own, and take its place.

    Both halves go in together, which is what makes the result usable on either
    side. The row is then replaced by the new tile in both halves, so the
    character carries on doing exactly what it did -- a fold is a tidying, not
    a change of behaviour.
    """
    row = rows[index]
    if not (row.get("when") or row.get("do")):
        print("  that row is empty")
        ask("press enter")
        return
    header("Fold a row into one tile")
    print(" " + brain.describe_row(row) + "\n")
    name = ask("Name this tile", "my tile").strip()
    if not name:
        return
    if len(name) > 40:
        print("  that name is too long")
        ask("press enter")
        return
    already = find_my_tile(project, name)
    if already and not ask_yes("You already have a tile called '%s'. "
                               "Replace what is inside it" % name):
        return

    remember(project)
    made = {"name": name,
            "when": json.loads(json.dumps(row.get("when", []))),
            "do": json.loads(json.dumps(row.get("do", [])))}
    if already:
        already.clear()
        already.update(made)
    else:
        my_tiles(project).append(made)
    rows[index] = {"when": [{"tile": "combo", "args": {"name": name}}],
                   "do": [{"tile": "combo", "args": {"name": name}}]}
    print("\n  made the tile '%s'. It is on the tile menus now, in both "
          "halves." % name)
    ask("press enter")


def my_tiles_screen(project):
    """See what your own tiles hold, and throw one away."""
    while True:
        header("Your own tiles")
        mine = my_tiles(project)
        if not mine:
            print(" (none yet)\n")
            print(wrap_note(
                "Build a row you like, then pick 'fold a row into one tile' on "
                "a character's brain menu. Both halves of the row go in "
                "together, so the tile works wherever you drop it."))
            ask("press enter")
            return
        for i, own in enumerate(mine, 1):
            print(" %2d. %s" % (i, own.get("name", "?")))
            print("     WHEN %s" % (" and ".join(
                brain.describe_tile(tiles.SENSORS, t)
                for t in own.get("when", [])) or "(nothing)"))
            print("     DO   %s" % (" and ".join(
                brain.describe_tile(tiles.ACTIONS, t)
                for t in own.get("do", [])) or "(nothing)"))
        print()
        choice = menu(["delete one of them"], back_label="done")
        if choice is None:
            return
        header("Delete which of your tiles?")
        index = menu([own.get("name", "?") for own in mine])
        if index is None:
            continue
        name = mine[index].get("name", "?")
        if ask_yes("Delete '%s'? Rows using it will stop doing anything, "
                   "but are not themselves deleted" % name):
            remember(project)
            mine.pop(index)


def pick_tile(registry, project, what):
    """Every tile, this half's first and the other half's after.

    The browser palette offers both halves too. Nothing is hidden: which tile
    belongs where is the engine's rule, and you may want to place one anyway to
    see what it does. The ones that will not fire are marked rather than
    withheld -- a DO tile among the WHEN tiles stops its row firing at all, and
    a WHEN tile among the DO tiles is skipped.
    """
    other = tiles.ACTIONS if registry is tiles.SENSORS else tiles.SENSORS
    other_name = "DO" if registry is tiles.SENSORS else "WHEN"
    warning = ("stops the row firing" if registry is tiles.SENSORS
               else "is skipped here")

    side = "when" if registry is tiles.SENSORS else "do"
    mine = my_tiles(project)

    header("Pick a %s tile" % what)
    # `combo` is the machinery behind your own tiles; it is offered as those
    # by name rather than as a raw tile asking you to type one.
    ids = [i for i in registry if i != "combo"] + \
          [i for i in other if i != "combo"]
    labels = (["your tile: " + describe_mine(side, own) for own in mine] +
              [registry[i].label for i in ids if i in registry] +
              ["%s  <- %s tile, %s" % (other[i].label, other_name, warning)
               for i in ids if i in other])
    index = menu(labels)
    if index is None:
        return None
    if index < len(mine):
        return {"tile": "combo", "args": {"name": mine[index].get("name", "")}}
    tile_id = ids[index - len(mine)]
    tile = registry[tile_id] if tile_id in registry else other[tile_id]
    return {"tile": tile.id, "args": fill_params(tile, project)}


def edit_row(project, row):
    while True:
        header("Editing one brain row")
        print(" " + brain.describe_row(row) + "\n")
        choice = menu([
            "add a WHEN tile (a sensor)",
            "add a DO tile (an action)",
            "remove a WHEN tile",
            "remove a DO tile",
            undo_label(),
        ], back_label="done")
        if choice is None:
            return row
        if choice == 4:
            # A row being edited may itself be undone out of existence, so the
            # caller redraws from the project rather than from this row.
            if undo(project):
                return None
            print("  nothing to undo")
            ask("press enter")
            continue
        if choice == 0:
            tile_use = pick_tile(tiles.SENSORS, project, "WHEN")
            if tile_use:
                remember(project)
                row["when"].append(tile_use)
        elif choice == 1:
            tile_use = pick_tile(tiles.ACTIONS, project, "DO")
            if tile_use:
                remember(project)
                row["do"].append(tile_use)
        elif choice in (2, 3):
            key = "when" if choice == 2 else "do"
            registry = tiles.SENSORS if key == "when" else tiles.ACTIONS
            if not row[key]:
                continue
            header("Remove which tile?")
            index = menu([brain.describe_tile(registry, t) for t in row[key]])
            if index is not None:
                remember(project)
                row[key].pop(index)


# What a screen returns when an undo has just replaced the project's contents.
# Every screen below holds a reference into the project -- a character, its list
# of rows -- and undo swaps those objects for the restored ones, so the old
# references are dangling. Rather than trying to patch them up, the screens
# unwind to characters_screen, which re-reads everything from the project each
# time round its loop.
UNDONE = "undone"


def brain_screen(project, char):
    while True:
        rows = char["brain"]
        header("Brain of '%s'  %s" % (char["kind"], char["glyph"]))
        if rows:
            for i, row in enumerate(rows, 1):
                print(" %2d. %s" % (i, brain.describe_row(row)))
        else:
            print(" (empty -- this character just sits there)")
        print()
        choice = menu(["add a new row", "change a row", "delete a row",
                       "move a row up", "fold a row into one tile of your own",
                       undo_label()], back_label="done")
        if choice is None:
            return None
        if choice == 4 and rows:
            header("Fold which row?")
            index = menu([brain.describe_row(r) for r in rows])
            if index is not None:
                fold_row(project, rows, index)
        elif choice == 5:
            if undo(project):
                return UNDONE
            print("  nothing to undo")
            ask("press enter")
        elif choice == 0:
            # The row joins the project before it is filled in, so that undo
            # inside the row editor has something real to undo. If it is left
            # empty it is taken away again, and forget_if_same then drops the
            # mark, so adding a row and changing your mind costs no undo step.
            remember(project)
            rows.append({"when": [], "do": []})
            if edit_row(project, rows[-1]) is None:
                return UNDONE
            if not (rows[-1]["when"] or rows[-1]["do"]):
                rows.pop()
                forget_if_same(project)
        elif choice == 1 and rows:
            header("Change which row?")
            index = menu([brain.describe_row(r) for r in rows])
            if index is not None:
                if edit_row(project, rows[index]) is None:
                    return UNDONE
        elif choice == 2 and rows:
            header("Delete which row?")
            index = menu([brain.describe_row(r) for r in rows])
            if index is not None:
                remember(project)
                rows.pop(index)
        elif choice == 3 and len(rows) > 1:
            header("Move which row up?")
            index = menu([brain.describe_row(r) for r in rows])
            if index is not None and index > 0:
                remember(project)
                rows[index - 1], rows[index] = rows[index], rows[index - 1]


def character_screen(project, char):
    while True:
        header("Character '%s'" % char["kind"])
        print(" looks like : %s   colour: %s" % (char["glyph"], char["color"]))
        print(" health     : %d   how many at the start: %d"
              % (char["health"], char["count"]))
        print(" role       : %s   solid (blocks others): %s"
              % (char["role"], "yes" if char["solid"] else "no"))
        print(" brain rows : %d\n" % len(char["brain"]))
        choice = menu(["edit its brain", "change how it looks",
                       "change its colour", "change its health",
                       "change how many start", "player or prop",
                       "solid or walk-through", "delete this character"],
                      back_label="done")
        if choice is None:
            return True
        if choice == 0:
            if brain_screen(project, char) is UNDONE:
                return UNDONE          # `char` is now a dangling reference
        elif choice == 1:
            char["glyph"] = (ask("One letter or symbol", char["glyph"]) or "?")[:1]
        elif choice == 2:
            names = list(COLORS)
            index = menu(names, "pick a colour", allow_back=False)
            char["color"] = names[index]
        elif choice == 3:
            char["health"] = max(1, ask_int("How much health", char["health"]))
        elif choice == 4:
            char["count"] = max(0, ask_int("How many at the start", char["count"]))
        elif choice == 5:
            index = menu(["player (the game ends if all of them die)",
                          "prop (scenery, enemies, pickups)"],
                         "pick", allow_back=False)
            char["role"] = ["player", "prop"][index]
        elif choice == 6:
            char["solid"] = ask_yes("Should it block others from walking through",
                                    char["solid"])
        elif choice == 7:
            if ask_yes("Really delete '%s'" % char["kind"]):
                # Deleting a character throws away every brain row it had, so
                # this one is worth an undo mark even though the other settings
                # on this screen are not -- see undo_label.
                remember(project)
                project["characters"].remove(char)
                return True


def characters_screen(project):
    while True:
        header("Characters in '%s'" % project["name"])
        chars = project["characters"]
        for i, c in enumerate(chars, 1):
            print(" %2d. %s  %-10s %d rows, %d at start"
                  % (i, c["glyph"], c["kind"], len(c["brain"]), c["count"]))
        if not chars:
            print(" (none yet)")
        print()
        choice = menu(["add a new character", "edit a character"],
                      back_label="done")
        if choice is None:
            return
        if choice == 0:
            name = ask("Name it (one word, e.g. hero, apple, bug)").strip()
            if not name:
                continue
            if name in [c["kind"] for c in chars]:
                print("  that name is taken")
                continue
            glyph = (ask("One letter or symbol to draw it with", name[0]) or "?")[:1]
            remember(project)
            char = brain.new_character(name, glyph)
            chars.append(char)
            character_screen(project, char)
        elif choice == 1 and chars:
            header("Edit which character?")
            index = menu(["%s  %s" % (c["glyph"], c["kind"]) for c in chars])
            if index is not None:
                character_screen(project, chars[index])
        # Either way, the loop re-reads project["characters"] next time round,
        # which is exactly what makes it safe to come back here after an undo.


def world_screen(project):
    settings = project["world"]
    header("World settings")
    settings["width"] = max(5, min(70, ask_int("Width in squares", settings["width"])))
    settings["height"] = max(5, min(20, ask_int("Height in squares", settings["height"])))
    settings["speed"] = max(1, min(30, ask_int("Speed (ticks per second)",
                                               settings.get("speed", 6))))
    settings["wrap"] = ask_yes("Should the edges wrap around", settings.get("wrap", False))


# --------------------------------------------------------------------------
# top level
# --------------------------------------------------------------------------

def rename_screen(project):
    """Rename the open game, taking its file with it."""
    header("Rename '%s'" % project["name"])
    was = project["name"]
    now = ask("New name", was).strip()
    if not now or now == was:
        return
    project["name"] = now
    brain.save(project, brain.GAMES_DIR / (now + ".json"))
    old = brain.GAMES_DIR / (was + ".json")
    if old.exists() and ask_yes("Delete the old file '%s.json'" % was, True):
        old.unlink()
    print(" now saved as %s.json" % now)
    ask("press enter")


def push_screen(project):
    from . import sync
    header("Send '%s' to GitHub" % project["name"])
    print(" This overwrites the copy on GitHub with the one on this phone.\n")
    if not ask_yes("Go ahead", True):
        return
    try:
        results, where = sync.push([project["name"]])
        for game, what in results:
            print("  %s -> %s  (%s)" % (game, where, what))
    except sync.SyncError as err:
        print("  " + str(err))
    ask("press enter")


def invite_screen():
    """Make and revoke codes for other people, from the terminal."""
    from . import live, server
    while True:
        header("Invite someone")
        session = live.SESSION
        print(" They open %s in their browser" % server.lan_address(
            _read_port() or 8765))
        print(" and type one of these codes.\n")
        if session.invites:
            for code, invite in session.invites.items():
                print("  %s   may %-5s  drives %-8s %s"
                      % (code, invite.role, invite.character, invite.note))
        else:
            print("  (no codes yet)")
        print()
        choice = menu(["make a code that can play",
                       "make a code that can edit too",
                       "make a code that can only watch",
                       "revoke a code"], back_label="done")
        if choice is None:
            return
        if choice == 3:
            if not session.invites:
                continue
            header("Revoke which code?")
            codes = list(session.invites)
            index = menu(codes)
            if index is not None:
                session.revoke(codes[index])
            continue
        role = ["play", "edit", "watch"][choice]
        note = ask("Who is it for (just a label)", "")
        invite = session.invite(role, "watch" if role == "watch" else "own", note)
        header("Their code is")
        print("\n      %s\n" % invite.code)
        print(" They may %s. Revoke it here whenever you like." % role)
        ask("press enter")


def _ago(when):
    """How long ago, in words. Rough on purpose -- nobody counts seconds."""
    import time
    gap = time.time() - (when or 0)
    if gap < 45:
        return "just now"
    if gap < 3600:
        return "%dm ago" % round(gap / 60)
    return "%dh ago" % round(gap / 3600)


def print_players():
    """The roster as plain lines. Shared by the menu screen and `spark players`."""
    people = status.players()
    if not people:
        print(" nobody is connected.\n")
        print(wrap_note(
            "People show up here once you are hosting and someone has typed "
            "an invite code. Start hosting with `python3 spark.py host`, then "
            "make a code from `invite someone to play`."))
        return people

    print(" %-3s %-16s %-6s %-14s %s" % ("", "name", "may", "inside", "joined"))
    print(" " + "-" * 52)
    for place, person in enumerate(people, 1):
        print(" %-3s %-16s %-6s %-14s %s"
              % (str(place) + ".", str(person.get("name", "?"))[:16],
                 person.get("role", "?"), person.get("game") or "no game yet",
                 _ago(person.get("joined"))))
    print()
    print(" %d connected. The one who joined first is at the top." % len(people))
    return people


def players_screen():
    """Who is connected right now, whoever arrived first at the top."""
    header("Players connected")
    print_players()
    ask("\npress enter")


def _read_port():
    from . import status
    try:
        import json
        return json.loads(status.STATE.read_text()).get("port")
    except (OSError, ValueError):
        return None


def open_screen():
    games = brain.list_games()
    if not games:
        header("No saved games yet")
        ask("press enter")
        return None
    header("Open which game?")
    index = menu([p.stem for p in games])
    return brain.load(games[index]) if index is not None else None


def main_menu(project=None):
    while True:
        header("SPARK  --  build a game out of tiles")
        if project:
            print(" open: %s  (%d characters)\n"
                  % (project["name"], len(project["characters"])))
            options = ["play it", "characters and their brains",
                       "your own tiles (%d)" % len(my_tiles(project)),
                       "world settings", "save", "rename this game",
                       "send this game to GitHub", "invite someone to play",
                       "start a new game", "open a game"]
        else:
            print(" nothing open yet\n")
            options = ["learn how (guided, about ten minutes)",
                       "start a new game", "open a game"]
        print(" (type browser at any prompt for the drag-and-drop editor,")
        print("  or players to see who is connected)\n")
        choice = menu(options, "pick a number", back_label="quit")
        if choice is None:
            print("bye")
            return
        label = options[choice]

        if label == "learn how (guided, about ten minutes)":
            from . import tutorial
            saved = tutorial.run()
            project = brain.load(saved)
        elif label == "play it":
            runner.play(project)
        elif label == "characters and their brains":
            characters_screen(project)
        elif label.startswith("your own tiles"):
            my_tiles_screen(project)
        elif label == "world settings":
            world_screen(project)
        elif label == "save":
            path = brain.save(project, brain.GAMES_DIR / (project["name"] + ".json"))
            header("Saved")
            print(" " + str(path))
            ask("press enter")
        elif label == "rename this game":
            rename_screen(project)
        elif label == "send this game to GitHub":
            push_screen(project)
        elif label == "invite someone to play":
            invite_screen()
        elif label == "start a new game":
            name = ask("Name your game", "mygame").strip() or "mygame"
            project = brain.new_project(name)
            forget_history()
        elif label == "open a game":
            opened = open_screen()
            if opened is not None:
                project = opened
                forget_history()   # undoing into the last game would swap it in
