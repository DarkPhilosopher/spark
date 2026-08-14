"""The world: characters, the grid they live on, and the rule engine.

Every tick, each character reads its brain top to bottom. A row fires when all
of its WHEN tiles pass; then all of its DO tiles run. That is the whole engine.
"""

from . import rng as _rng
from . import tiles

COLORS = {
    "white": 37, "red": 31, "green": 32, "yellow": 33,
    "blue": 34, "magenta": 35, "cyan": 36, "grey": 90,
}


class Thing:
    """One character standing on the grid."""

    def __init__(self, kind, x, y, template):
        self.kind = kind
        self.x, self.y = x, y
        self.glyph = template.get("glyph", "?")[:1] or "?"
        self.color = template.get("color", "white")
        self.health = template.get("health", 1)
        self.solid = template.get("solid", False)
        self.role = template.get("role", "prop")
        self.brain = template.get("brain", [])
        self.facing = (0, -1)       # north, until a face/move/shoot tile turns it
        self.owner = None
        self.alive = True
        self.age = 0                # ticks lived
        self.travelled = 0          # squares actually moved
        self.max_life = 0           # longevity, stamped on by the shoot tile
        self.max_range = 0          # reach, likewise. 0 on both means for ever
        self.controller = None      # which player drives this one, if any


class World:
    def __init__(self, project, seed=None):
        self.project = project
        # Dice first: the opening spawns below already need them. A seed makes
        # the whole game reproducible, here and in world3d.html alike.
        self.rng = _rng.Rng(seed)
        self.seed = seed
        settings = project.get("world", {})
        self.width = settings.get("width", 30)
        self.height = settings.get("height", 14)
        self.wrap = settings.get("wrap", False)

        self.templates = {c["kind"]: c for c in project.get("characters", [])}
        self.templates.setdefault("shot", {
            "kind": "shot", "glyph": "*", "color": "yellow",
            "health": 1, "brain": tiles.SHOT_BRAIN,
        })

        self.things = []
        self.tick = 0
        self.score = 0
        self.message = ""
        self.status = None          # None | "win" | "lose"
        self.keys = set()           # keys at this device, for solo play
        self.player_keys = {}       # player id -> keys, for a shared world

        self.memory = {}            # name -> value, written by the remember tile
        # name -> {"name", "value", "x", "y", "z"}: the placeholders, each an
        # arbitrary slot with three faces. Made on demand by the tiles that
        # write to them -- see tiles.place.
        self.places = {}
        # Handing a URL to another app is the one tile that reaches outside the
        # game, so it is off unless whoever is playing turned it on. A shared
        # world never does -- see the `open` tile.
        self.may_open = False
        self.opened = {}            # what was opened, and on which tick

        for char in project.get("characters", []):
            for _ in range(char.get("count", 1)):
                self.spawn_somewhere(char["kind"])

    def keys_for(self, thing):
        """Whose keypresses this character listens to.

        Unclaimed characters answer to the keyboard in front of the world, so
        a single-player game behaves exactly as it always did.
        """
        if thing.controller is None:
            return self.keys
        return self.player_keys.get(thing.controller, ())

    # -- grid queries ------------------------------------------------------

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def at(self, x, y):
        return [t for t in self.things if t.alive and t.x == x and t.y == y]

    def empty_cell(self):
        for _ in range(200):
            x = self.rng.randrange(self.width)
            y = self.rng.randrange(self.height)
            if not self.at(x, y):
                return (x, y)
        return None

    def nearest(self, obj, kind, reach):
        """Closest living thing of `kind` within `reach` squares, or None.

        Skips the seeker, whoever fired it, and its sibling shots -- otherwise
        a bullet detonates on its owner the instant it appears.
        """
        best, best_d = None, None
        for other in self.things:
            if other is obj or not other.alive or other is obj.owner:
                continue
            if obj.owner is not None and other.owner is obj.owner:
                continue
            if not tiles.matches(other, kind):
                continue
            dist = max(abs(other.x - obj.x), abs(other.y - obj.y))
            if dist <= reach and (best_d is None or dist < best_d):
                best, best_d = other, dist
        return best

    # -- mutation ----------------------------------------------------------

    def spawn(self, kind, x, y):
        template = self.templates.get(kind)
        if template is None:
            return None
        if not self.in_bounds(x, y):
            return None
        thing = Thing(kind, x, y, template)
        self.things.append(thing)
        return thing

    def spawn_somewhere(self, kind):
        spot = self.empty_cell()
        return self.spawn(kind, *spot) if spot else None

    def remove(self, thing):
        thing.alive = False

    def try_move(self, thing, dx, dy):
        x, y = thing.x + dx, thing.y + dy
        if self.wrap:
            x, y = x % self.width, y % self.height
        elif not self.in_bounds(x, y):
            return False
        if any(o.solid for o in self.at(x, y)):
            return False
        thing.x, thing.y = x, y
        thing.travelled += 1
        return True

    # -- the rule engine ---------------------------------------------------

    def run_row(self, thing, row):
        it = None
        for tile_use in row.get("when", []):
            tile = tiles.SENSORS.get(tile_use["tile"])
            if tile is None:
                return
            result = tile.fn(thing, self, tile_use.get("args", {}))
            if not result:
                return
            if it is None and isinstance(result, Thing):
                it = result
        for tile_use in row.get("do", []):
            tile = tiles.ACTIONS.get(tile_use["tile"])
            if tile is not None:
                tile.fn(thing, self, tile_use.get("args", {}), it)

    def step(self):
        self.tick += 1
        for thing in list(self.things):
            if not thing.alive or self.status:
                continue
            thing.age += 1
            for row in thing.brain:
                if not thing.alive:
                    break
                self.run_row(thing, row)

        self.things = [t for t in self.things if t.alive]

        players = [t for t in self.things if t.role == "player"]
        if not players and any(c.get("role") == "player"
                               for c in self.project.get("characters", [])):
            self.status = "lose"

    # -- drawing -----------------------------------------------------------

    def render(self, color=True):
        grid = [[" "] * self.width for _ in range(self.height)]
        for thing in self.things:
            if self.in_bounds(thing.x, thing.y):
                cell = thing.glyph
                if color:
                    cell = "\033[%dm%s\033[0m" % (COLORS.get(thing.color, 37), cell)
                grid[thing.y][thing.x] = cell
        lines = ["+" + "-" * self.width + "+"]
        lines += ["|" + "".join(row) + "|" for row in grid]
        lines.append("+" + "-" * self.width + "+")
        return lines
