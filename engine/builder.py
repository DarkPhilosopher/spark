"""The no-code editor: every choice is a numbered menu, nothing is typed as code."""

import sys

from . import brain, runner, status, tiles
from .world import COLORS

CLEAR = "\033[H\033[2J"


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


def pick_tile(registry, project, what):
    header("Pick a %s tile" % what)
    ids = list(registry)
    labels = [registry[i].label for i in ids]
    index = menu(labels)
    if index is None:
        return None
    tile = registry[ids[index]]
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
        ], back_label="done")
        if choice is None:
            return row
        if choice == 0:
            tile_use = pick_tile(tiles.SENSORS, project, "WHEN")
            if tile_use:
                row["when"].append(tile_use)
        elif choice == 1:
            tile_use = pick_tile(tiles.ACTIONS, project, "DO")
            if tile_use:
                row["do"].append(tile_use)
        elif choice in (2, 3):
            key = "when" if choice == 2 else "do"
            registry = tiles.SENSORS if key == "when" else tiles.ACTIONS
            if not row[key]:
                continue
            header("Remove which tile?")
            index = menu([brain.describe_tile(registry, t) for t in row[key]])
            if index is not None:
                row[key].pop(index)


def brain_screen(project, char):
    rows = char["brain"]
    while True:
        header("Brain of '%s'  %s" % (char["kind"], char["glyph"]))
        if rows:
            for i, row in enumerate(rows, 1):
                print(" %2d. %s" % (i, brain.describe_row(row)))
        else:
            print(" (empty -- this character just sits there)")
        print()
        choice = menu(["add a new row", "change a row", "delete a row",
                       "move a row up"], back_label="done")
        if choice is None:
            return
        if choice == 0:
            row = edit_row(project, {"when": [], "do": []})
            if row["when"] or row["do"]:
                rows.append(row)
        elif choice == 1 and rows:
            header("Change which row?")
            index = menu([brain.describe_row(r) for r in rows])
            if index is not None:
                edit_row(project, rows[index])
        elif choice == 2 and rows:
            header("Delete which row?")
            index = menu([brain.describe_row(r) for r in rows])
            if index is not None:
                rows.pop(index)
        elif choice == 3 and len(rows) > 1:
            header("Move which row up?")
            index = menu([brain.describe_row(r) for r in rows])
            if index is not None and index > 0:
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
            brain_screen(project, char)
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
            char = brain.new_character(name, glyph)
            chars.append(char)
            character_screen(project, char)
        elif choice == 1 and chars:
            header("Edit which character?")
            index = menu(["%s  %s" % (c["glyph"], c["kind"]) for c in chars])
            if index is not None:
                character_screen(project, chars[index])


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
        elif label == "open a game":
            project = open_screen() or project
