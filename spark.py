#!/usr/bin/env python3
"""Spark -- build a game by snapping tiles together. No typing code.

    python3 spark.py tutorial              learn it by building a game, offline
    python3 spark.py                       open the menu
    python3 spark.py edit [port]           open the drag-and-drop editor (8765)
    python3 spark.py host [port]           same, but open to others on this wifi
    python3 spark.py host --public         ...and to anyone, through a tunnel
    python3 spark.py people                who else can get at your GitHub repo
    python3 spark.py people NAME [--player]  let a GitHub user in as editor/player
    python3 spark.py play games/chase.json [ticks]   skip straight to playing
    python3 spark.py push [game ...]       overwrite games on GitHub with these
    python3 spark.py pull [game ...]       overwrite games here with GitHub's
    python3 spark.py status                print the Github/Browser/Local line
    python3 spark.py export                refresh tiles.json and games/index.json
    python3 spark.py games/chase.json      open the menu on that game

See README.md for the guide and CHANGELOG.md for what changed when.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine import brain, builder, runner  # noqa: E402


def main():
    args = sys.argv[1:]
    if args and args[0] in ("edit", "host"):
        from engine import server
        port = int(args[1]) if len(args) > 1 and args[1].isdigit() else 8765
        public = "--public" in args
        if public and args[0] == "edit":
            sys.exit("--public needs sharing on: use  spark.py host --public")
        server.serve(port=port,
                     bind="0.0.0.0" if args[0] == "host" else "127.0.0.1",
                     public=public)
        return

    if args and args[0] == "people":
        from engine import sync
        try:
            if len(args) > 1:
                role = "player" if "--player" in args else "editor"
                done = sync.add_person(args[1], role)
                print("  %s is now an %s on %s%s"
                      % (done["user"], done["role"], done["repo"],
                         "" if not done["invited"] else " (invitation sent)"))
            else:
                for who, role in sync.people():
                    print("  %-20s %s" % (who, role))
        except sync.SyncError as err:
            sys.exit(str(err))
        return
    if args and args[0] in ("push", "pull"):
        from engine import sync
        try:
            results, where = (sync.push if args[0] == "push" else sync.pull)(args[1:])
        except sync.SyncError as err:
            sys.exit(str(err))
        arrow = "->" if args[0] == "push" else "<-"
        for game, what in results:
            print("  %s %s %s  (%s)" % (game, arrow, where, what))
        if not results:
            print("nothing to " + args[0])
        return
    if args and args[0] == "tutorial":
        from engine import tutorial
        tutorial.run()
        return
    if args and args[0] == "status":
        from engine import status
        print(status.line())
        return
    if args and args[0] == "export":
        from engine import server
        names = server.export_static()
        print("wrote tiles.json and games/index.json (%d games)" % len(names))
        return
    if args and args[0] == "play":
        if len(args) < 2:
            sys.exit("say which game: spark.py play games/chase.json")
        ticks = int(args[2]) if len(args) > 2 else None
        runner.play(brain.load(args[1]), max_ticks=ticks)
        return
    project = brain.load(args[0]) if args else None
    builder.main_menu(project)


if __name__ == "__main__":
    main()
