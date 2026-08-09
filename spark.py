#!/usr/bin/env python3
"""Spark -- build a game by snapping tiles together. No typing code.

    python3 spark.py                       open the menu
    python3 spark.py edit [port]           open the drag-and-drop editor (8765)
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
    if args and args[0] == "edit":
        from engine import server
        server.serve(port=int(args[1]) if len(args) > 1 else 8765)
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
