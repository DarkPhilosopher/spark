"""Projects on disk, and turning tile data back into English."""

import json
from pathlib import Path

from . import tiles

GAMES_DIR = Path(__file__).resolve().parent.parent / "games"


def new_project(name):
    return {
        "name": name,
        "world": {"width": 30, "height": 14, "wrap": False, "speed": 6},
        "characters": [],
    }


def new_character(kind, glyph="?"):
    return {
        "kind": kind,
        "glyph": glyph,
        "color": "white",
        "health": 1,
        "count": 1,
        "solid": False,
        "role": "prop",
        "brain": [],
    }


def load(path):
    return json.loads(Path(path).read_text())


def save(project, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(project, indent=2))
    return path


def list_games():
    """Every saved game. index.json is the listing itself, not a game."""
    GAMES_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(p for p in GAMES_DIR.glob("*.json") if p.stem != "index")


def describe_tile(registry, tile_use):
    tile = registry.get(tile_use["tile"])
    if tile is None:
        return "??? (%s)" % tile_use["tile"]
    return tile.describe(tile_use.get("args", {}))


def describe_row(row):
    when = " and ".join(describe_tile(tiles.SENSORS, t) for t in row.get("when", [])) or "never"
    do = " and ".join(describe_tile(tiles.ACTIONS, t) for t in row.get("do", [])) or "nothing"
    return "WHEN %s  DO %s" % (when, do)
