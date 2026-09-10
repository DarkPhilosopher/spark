"""The world: characters, the grid they live on, and the rule engine.

Every tick, each character reads its brain top to bottom. A row fires when all
of its WHEN tiles pass; then all of its DO tiles run. That is the whole engine.
"""

from . import rng as _rng
from . import tiles

COLORS = {
    "white": 37, "red": 31, "green": 32, "yellow": 33,
    "blue": 34, "magenta": 35, "cyan": 36, "grey": 90, "pink": 95,
    # Sixteen ANSI codes only go so far -- past here, each is the nearest
    # basic/bright terminal colour to the real RGB world3d.html draws (see
    # its COLOR_RGB/COLOR_CSS), several sharing a code with an existing
    # name. The terminal's own render() was always an approximation; only
    # the 3D view and the browser editor's swatches show the real colour.
    "orange": 33, "purple": 35, "brown": 33, "black": 30, "lime": 92,
    "teal": 96, "navy": 34, "maroon": 31, "gold": 93, "silver": 97,
}

# Every shape a character can be. Only world3d.html actually draws these
# (see its own matching SHAPES and the push*() functions each name is
# backed by) -- kept here too, in the same order, so the `shape` tile
# cycles through an identical sequence in both engines even though only
# one of them can show the result.
SHAPES = ["cube", "sphere", "cone", "cylinder", "pyramid", "wedge", "octahedron"]


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
        self.shape = template.get("shape", "cube")   # one of SHAPES, above
        self.size = template.get("size", 100)        # percent; 100 = normal
        # Per-axis overrides, percent like size -- None means "use size",
        # the same on all three axes, which is how everything behaves
        # until something explicitly stretches just one of them (see the
        # `stretch` tile). Only world3d.html actually draws the result.
        self.sx = template.get("sx", None)
        self.sy = template.get("sy", None)
        self.sz = template.get("sz", None)
        self.z = template.get("z", 0)                # altitude; 0 = ground
        self.full = template.get("full", False)      # fills its whole grid cell
        self.ghost = template.get("ghost", False)     # placed but not confirmed yet
        self.flying = template.get("flying", False)   # walking (grounded) unless true
        # A multi-part shape (the mesh creator's output): a list of
        # {shape, dx, dy, dz, sx, sy, sz, color} offsets from this thing's
        # own (x, y, z), each rendered as its own box or sphere. Only
        # world3d.html draws them -- kept here too so both engines carry
        # the same Thing shape and a save/load round trip never drops it.
        self.parts = template.get("parts", None)
        self.brain = template.get("brain", [])
        self.facing = (0, -1)       # north, until a face/move/shoot tile turns it
        self.owner = None
        self.alive = True
        self.age = 0                # ticks lived
        self.travelled = 0          # squares actually moved
        self.max_life = 0           # longevity, stamped on by the shoot tile
        self.max_range = 0          # reach, likewise. 0 on both means for ever
        self.controller = None      # which player drives this one, if any
        # item name -> count, this Thing's own -- see the give_item/
        # has_item tiles. Deliberately per-Thing, not world.memory (which
        # `remember`/`recall` share across the whole world, wrong for
        # "how much of this do *I* have" once two players share a game).
        self.inventory = {}
        # Harvest config ({item, amount, seconds, flashes}) or None -- see
        # the `harvestable` tile. The actual wait/flash/give sequence is
        # local-play-only UI in world3d.html; this is just the data half,
        # carried by both engines so it survives a save/load either way.
        self.harvest = template.get("harvest", None)
        # Who I follow/obey, or None -- see the lead/dismiss/has_leader
        # tiles. A Thing reference, not a name, so "move toward it" (the
        # ordinary move tile, unchanged) already knows how to chase it the
        # moment a sensor hands that Thing back as `it`.
        self.leader = None
        # A custom display name, or None -- purely cosmetic bookkeeping
        # for the terminal/chat /units and /name commands (see
        # engine/runner.py), never read by any tile or sensor. Not part
        # of the template; nothing sets this at spawn time.
        self.label = None


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
        # {x1,y1,z1,x2,y2,z2,color}[] -- see the draw_line tile. Cleared at
        # the top of every step() and rebuilt by whichever rows fire that
        # tick, so a line only shows for as long as the row drawing it keeps
        # firing (WHEN that made it true going false makes it vanish, same
        # tick, with nothing extra to clean up). Only world3d.html actually
        # draws these; Python carries the list so a save/load round trip and
        # the two engines agree on what a game *asked* to have drawn, even
        # though only one of them can show it.
        self.lines = []
        self.status = None          # None | "win" | "lose"
        self.keys = set()           # keys at this device, for solo play
        self.player_keys = {}       # player id -> keys, for a shared world

        # The named tiles this game carries: a name -> a stored row, with a
        # `when` half and a `do` half. They live in the game file, so they
        # travel to GitHub and to other players along with everything else.
        self.combos = {str(c.get("name", "")): c
                       for c in project.get("tiles", [])
                       if str(c.get("name", "")).strip()}
        self.combo_depth = 0        # how deep one named tile is inside another

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

    def check_all(self, thing, uses):
        """Every sensor in the list must pass.

        Returns False if any fails, otherwise the first character one of them
        found -- which becomes "it" -- or plain True if none found anybody. An
        empty list passes, which is why a row with no WHEN tiles runs its
        actions every tick.

        Split out of run_row so that a named tile made of several sensors is
        checked by the very same code as a row of them.
        """
        it = None
        for tile_use in uses:
            tile = tiles.SENSORS.get(tile_use["tile"])
            if tile is None:
                return False
            result = tile.fn(thing, self, tile_use.get("args", {}))
            if not result:
                return False
            if it is None and isinstance(result, Thing):
                it = result
        return it if it is not None else True

    def do_all(self, thing, uses, it):
        """Run every action in the list, handing each the same "it"."""
        for tile_use in uses:
            tile = tiles.ACTIONS.get(tile_use["tile"])
            if tile is not None:
                tile.fn(thing, self, tile_use.get("args", {}), it)

    def run_row(self, thing, row):
        found = self.check_all(thing, row.get("when", []))
        if not found:
            return
        self.do_all(thing, row.get("do", []),
                    found if isinstance(found, Thing) else None)

    def step(self):
        self.tick += 1
        self.lines = []       # see draw_line -- a fresh slate each tick
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
