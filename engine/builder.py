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
    """Show a numbered list. Returns the index, or None for back/blank."""
    for i, label in enumerate(options, 1):
        print(" %2d. %s" % (i, label))
    if allow_back:
        print("  0. %s" % back_label)
    while True:
        answer = ask(prompt, "0" if allow_back else None)
        if answer in ("", "0") and allow_back:
            return None
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        print("  pick one of the numbers shown")


def kinds_in(project):
    return [c["kind"] for c in project.get("characters", [])] + ["anything"]


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
                       "world settings", "save", "start a new game", "open a game"]
        else:
            print(" nothing open yet\n")
            options = ["start a new game", "open a game"]
        choice = menu(options, "pick a number", back_label="quit")
        if choice is None:
            print("bye")
            return
        label = options[choice]

        if label == "play it":
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
        elif label == "start a new game":
            name = ask("Name your game", "mygame").strip() or "mygame"
            project = brain.new_project(name)
        elif label == "open a game":
            project = open_screen() or project
