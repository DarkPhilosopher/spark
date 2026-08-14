"""The tile library: the fundamental pieces you snap together.

A brain row is  WHEN <sensor(s)>  DO <action(s)>.
Everything the builder offers on its menus comes from the two registries below.

To invent a new piece, write one small function and decorate it. Nothing else
in the project needs to change -- it shows up on the menus automatically.

    @sensor("hurt", "my health is below {value}",
            Param("value", "Below what health?", "int", default=2))
    def s_hurt(obj, world, a):
        return obj.health < a["value"]
"""

import random
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable

OPEN_COOLDOWN = 30      # ticks before the same thing may be opened again

DIRECTIONS = ["up", "down", "left", "right", "random", "toward it", "away from it", "forward"]
STEPS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
KEYS = ["up", "down", "left", "right", "space", "w", "a", "s", "d", "e", "f"]

# The compass rose. North is up the screen, so its step is (0, -1). The four
# diagonals are here and nowhere else, which is what makes `face` worth having:
# once a character faces north-east, `move forward` and `shoot forward` go
# diagonally too.
COMPASS = {
    "north": (0, -1), "north-east": (1, -1), "east": (1, 0), "south-east": (1, 1),
    "south": (0, 1), "south-west": (-1, 1), "west": (-1, 0), "north-west": (-1, -1),
}
STEPS.update(COMPASS)
BEARINGS = list(COMPASS) + ["toward it", "away from it"]

# What `move random` picks from, fixed in one place because the JavaScript
# engine in world3d.html has to walk the same twelve steps in the same order
# for a seeded world to come out the same in both. Insertion order: the four
# arrows first, then the compass.
STEP_LIST = list(STEPS.values())


@dataclass
class Param:
    """One question the builder asks when you place a tile."""
    name: str
    prompt: str
    kind: str = "text"          # "text" | "int" | "choice" | "kind"
    choices: list = field(default_factory=list)
    default: Any = None


@dataclass
class Tile:
    id: str
    label: str                   # e.g. "see {kind} within {range}"
    params: list
    fn: Callable

    def describe(self, args):
        text = self.label
        for p in self.params:
            text = text.replace("{%s}" % p.name, str(args.get(p.name, p.default)))
        return text


SENSORS: dict[str, Tile] = {}
ACTIONS: dict[str, Tile] = {}


def sensor(tile_id, label, *params):
    def deco(fn):
        SENSORS[tile_id] = Tile(tile_id, label, list(params), fn)
        return fn
    return deco


def action(tile_id, label, *params):
    def deco(fn):
        ACTIONS[tile_id] = Tile(tile_id, label, list(params), fn)
        return fn
    return deco


# --------------------------------------------------------------------------
# helpers shared by tiles
# --------------------------------------------------------------------------

def matches(obj, kind):
    return kind == "anything" or obj.kind == kind


def resolve_step(name, obj, it, rng=None):
    """Turn a direction name into a (dx, dy) step.

    `rng` is the world's dice, so that a seeded world moves the same way twice.
    It stays optional because the direction names that need luck are the rare
    ones -- everything else here is pure arithmetic.
    """
    if name in STEPS:
        return STEPS[name]
    if name == "random":
        return (rng.choice(STEP_LIST) if rng is not None
                else random.choice(STEP_LIST))
    if name == "forward":
        return obj.facing
    if it is None:
        return (0, 0)
    dx, dy = it.x - obj.x, it.y - obj.y
    if name == "away from it":
        dx, dy = -dx, -dy
    # step along the axis we are furthest off, so chases look deliberate
    if abs(dx) >= abs(dy):
        return ((1 if dx > 0 else -1) if dx else 0, 0)
    return (0, (1 if dy > 0 else -1) if dy else 0)


def remembered(world, text):
    """What a box of text means: a remembered name, or else itself.

    This is what lets one word stand in for a long one. Remember `chrome` is
    `com.android.chrome` once, and every tile afterwards can just say chrome.
    A name nobody has remembered is taken at face value, so nothing has to be
    remembered first and short games never need the idea at all.
    """
    text = str(text or "").strip()
    return str(world.memory.get(text, text))


# --------------------------------------------------------------------------
# placeholders: one arbitrary slot, regarded three ways
# --------------------------------------------------------------------------
#
# A placeholder is a name you invent -- `speed`, `home`, `thing`, anything --
# that the world keeps a slot for. The slot has three faces at once and you
# choose which one a tile regards:
#
#     its NAME     a piece of text, for labelling
#     its VALUE    one whole number
#     its VECTOR   three whole numbers, x, y and z
#
# Nothing has to be filled in first. A placeholder nobody has written to has an
# empty name, a value of 0 and a vector of (0, 0, 0), so a row may read one
# before any row has written it and still get a sensible answer. That is what
# makes it a placeholder rather than a declaration: you use the name, and the
# slot appears underneath it.

FACES = ["value", "x", "y", "z"]        # which face a tile regards
AXES = ["x", "y", "z"]
TESTS = ["at least", "at most", "exactly"]
OPS = ["plus", "minus", "times", "divided by"]

# Every number in a placeholder is a whole number inside this fence. Both the
# fence and the whole-number rule are here for the same reason: world3d.html
# has to compute the identical answer in JavaScript, whose numbers stop being
# exact above about nine thousand million million. Clamping first means the two
# engines agree on every sum anybody can actually write, and squares on a grid
# were never fractional anyway.
LIMIT = 1000000000

# What counts as typed-in number. Deliberately stricter than either language's
# own parser -- Python reads "1_0" as ten and JavaScript reads "0x10" as
# sixteen, and a sum must not mean two different things in the two engines.
NUMBER = re.compile(r"^([+-]?)(\d+)(?:\.\d+)?$")


def clamp(n):
    return max(-LIMIT, min(LIMIT, int(n)))


def place(world, who):
    """The placeholder called `who`, made empty the first time it is written.

    Names are trimmed and lowercased, so `Home` and `home` are the one slot --
    a placeholder is meant to be typed twice from memory without ceremony.
    An empty name is nobody, and the tiles that get None here do nothing.
    """
    who = str(who or "").strip().lower()
    if not who:
        return None
    spot = world.places.get(who)
    if spot is None:
        spot = {"name": "", "value": 0, "x": 0, "y": 0, "z": 0}
        world.places[who] = spot
    return spot


def about(thing, what):
    """One number off a character, for the `my ...` and `it ...` words."""
    if thing is None:
        return 0
    if what == "x":
        return thing.x
    if what == "y":
        return thing.y
    if what == "health":
        return thing.health
    if what == "age":
        return thing.age
    if what == "travelled":
        return thing.travelled
    return 0


def number(text, obj, world, it):
    """What one box of a sum means, as a whole number.

    Read in this order, and the first that fits wins:

        (nothing)          0
        12  -3  2.7        that number, with any fraction dropped
        my x, my y,        about me: also health, age, travelled
        my health ...
        it x, it y,        about whoever the WHEN half found -- 0 if it found
        it health ...      nobody, so a row can never break for want of an `it`
        score, tick        about the world
        speed              the VALUE of the placeholder called speed
        home x             one axis of the VECTOR of the placeholder home

    Anything else is 0. Reading an unknown name does not create it: only the
    writing tiles do that, so a typo stays a quiet zero instead of quietly
    filling the world with slots.
    """
    text = str(text if text is not None else "").strip().lower()
    if not text:
        return 0
    digits = NUMBER.match(text)
    if digits:
        got = int(digits.group(2))
        return clamp(-got if digits.group(1) == "-" else got)
    head, _, tail = text.partition(" ")
    tail = tail.strip()
    if head == "my":
        return clamp(about(obj, tail))
    if head == "it":
        return clamp(about(it, tail))
    if text == "score":
        return clamp(world.score)
    if text == "tick":
        return clamp(world.tick)
    spot = world.places.get(text)
    if spot is not None:
        return clamp(spot["value"])
    if tail in AXES:
        spot = world.places.get(head)
        if spot is not None:
            return clamp(spot[tail])
    return 0


def total(a, op, b, obj, world, it):
    """The sum in the right-hand half of a `=` tile: one box, a word, one box."""
    left = number(a, obj, world, it)
    right = number(b, obj, world, it)
    if op == "minus":
        return clamp(left - right)
    if op == "times":
        return clamp(left * right)
    if op == "divided by":
        if not right:
            return 0                    # nothing sensible to return, so zero
        whole = abs(left) // abs(right)
        return clamp(-whole if (left < 0) != (right < 0) else whole)
    return clamp(left + right)


def compare(got, test, amount):
    if test == "at most":
        return got <= amount
    if test == "exactly":
        return got == amount
    return got >= amount


# --------------------------------------------------------------------------
# SENSORS -- the WHEN half
# --------------------------------------------------------------------------

@sensor("always", "always")
def s_always(obj, world, a):
    return True


@sensor("key", "key {key} is pressed",
        Param("key", "Which key?", "choice", KEYS, "up"))
def s_key(obj, world, a):
    # In a shared world each character answers only to its own player.
    return a["key"] in world.keys_for(obj)


@sensor("see", "I see {kind} within {range}",
        Param("kind", "See what?", "kind", [], "anything"),
        Param("range", "How many squares away?", "int", [], 6))
def s_see(obj, world, a):
    return world.nearest(obj, a["kind"], a["range"])


@sensor("touch", "I am touching {kind}",
        Param("kind", "Touching what?", "kind", [], "anything"))
def s_touch(obj, world, a):
    return world.nearest(obj, a["kind"], 1)


@sensor("timer", "every {every} ticks",
        Param("every", "How many ticks between firings?", "int", [], 4))
def s_timer(obj, world, a):
    every = max(1, a["every"])
    return world.tick % every == 0


@sensor("health_below", "my health is below {value}",
        Param("value", "Below what health?", "int", [], 2))
def s_health_below(obj, world, a):
    return obj.health < a["value"]


@sensor("score_at_least", "the score is at least {value}",
        Param("value", "What score?", "int", [], 10))
def s_score(obj, world, a):
    return world.score >= a["value"]


@sensor("chance", "{percent}% of the time",
        Param("percent", "Percent chance (0-100)?", "int", [], 25))
def s_chance(obj, world, a):
    return world.rng.randrange(100) < a["percent"]


@sensor("at_edge", "I am at the edge of the world")
def s_at_edge(obj, world, a):
    return obj.x in (0, world.width - 1) or obj.y in (0, world.height - 1)


@sensor("recall", "I remember {name} is {value}",
        Param("name", "Which name?", "text", [], "chrome"),
        Param("value", "Is what?", "text", [], "com.android.chrome"),)
def s_recall(obj, world, a):
    """True when a name has been remembered as exactly this value.

    Nothing is remembered when a game starts, so this is False until some row
    has run a `remember` tile. That is the useful shape: it is how a game asks
    "has this happened yet".
    """
    return world.memory.get(str(a.get("name", "")).strip()) == \
        str(a.get("value", ""))


@sensor("spent", "my range or time has run out")
def s_spent(obj, world, a):
    """True once a character has flown its reach or lived out its longevity.

    Both limits are stamped on by whoever fired it -- see the `shoot` tile.
    Nothing else in the world has them, so for everyone else this is False.
    """
    if obj.max_range and obj.travelled >= obj.max_range:
        return True
    return bool(obj.max_life and obj.age >= obj.max_life)


@sensor("place_has", "placeholder {who} has {face} {test} {amount}",
        Param("who", "Which placeholder?", "text", [], "thing"),
        Param("face", "Regard it as what?", "choice", FACES, "value"),
        Param("test", "Compared how?", "choice", TESTS, "at least"),
        Param("amount", "Compared with what number?", "int", [], 1))
def s_place_has(obj, world, a):
    """True when one face of a placeholder stands in the stated relation.

    An untouched placeholder reads as 0 on every face, so this answers before
    anything has written to it rather than refusing to.
    """
    spot = world.places.get(str(a.get("who", "")).strip().lower())
    face = a.get("face", "value")
    got = clamp(spot[face]) if spot is not None and face in spot else 0
    return compare(got, a.get("test", "at least"), int(a.get("amount", 1)))


@sensor("place_named", "placeholder {who} is named \"{text}\"",
        Param("who", "Which placeholder?", "text", [], "thing"),
        Param("text", "Named what?", "text", [], "hero"))
def s_place_named(obj, world, a):
    """True when a placeholder's NAME face is exactly this text.

    The name face is the one that is text rather than arithmetic, so this is
    how a row asks which of several things a placeholder is currently standing
    in for -- `placeholder target is named "apple"`.
    """
    spot = world.places.get(str(a.get("who", "")).strip().lower())
    return spot is not None and spot["name"] == str(a.get("text", ""))


# --------------------------------------------------------------------------
# ACTIONS -- the DO half
# --------------------------------------------------------------------------

@action("move", "move {dir}",
        Param("dir", "Move which way?", "choice", DIRECTIONS, "toward it"))
def a_move(obj, world, a, it):
    dx, dy = resolve_step(a["dir"], obj, it, world.rng)
    if dx or dy:
        obj.facing = (dx, dy)
        world.try_move(obj, dx, dy)


@action("face", "face {dir}",
        Param("dir", "Which way do I face?", "choice", BEARINGS, "north"))
def a_face(obj, world, a, it):
    """Turn on the spot. Nothing moves; `forward` just means somewhere new."""
    dx, dy = resolve_step(a["dir"], obj, it, world.rng)
    if dx or dy:
        obj.facing = (dx, dy)


@action("shoot", "shoot {dir} up to {reach} squares, for {life} ticks",
        Param("dir", "Shoot which way?", "choice", DIRECTIONS, "forward"),
        Param("reach", "How many squares does it fly? (0 = for ever)", "int", [], 8),
        Param("life", "How many ticks does it last? (0 = for ever)", "int", [], 12))
def a_shoot(obj, world, a, it):
    dx, dy = resolve_step(a["dir"], obj, it, world.rng)
    if not (dx or dy):
        return
    shot = world.spawn("shot", obj.x + dx, obj.y + dy)
    if shot:
        shot.facing = (dx, dy)
        shot.owner = obj
        shot.max_range = max(0, a.get("reach", 8))
        shot.max_life = max(0, a.get("life", 12))


@action("say", "say \"{text}\"",
        Param("text", "Say what?", "text", [], "hello!"))
def a_say(obj, world, a, it):
    world.message = a["text"]


@action("score", "change the score by {amount}",
        Param("amount", "Change score by how much?", "int", [], 1))
def a_score(obj, world, a, it):
    world.score += a["amount"]


@action("damage", "hurt {target} by {amount}",
        Param("target", "Hurt whom?", "choice", ["it", "self"], "it"),
        Param("amount", "By how much?", "int", [], 1))
def a_damage(obj, world, a, it):
    victim = obj if a["target"] == "self" else it
    if victim is not None:
        victim.health -= a["amount"]
        if victim.health <= 0:
            world.remove(victim)


@action("heal", "heal myself by {amount}",
        Param("amount", "By how much?", "int", [], 1))
def a_heal(obj, world, a, it):
    obj.health += a["amount"]


@action("spawn", "make a new {kind}",
        Param("kind", "Make what?", "kind", [], "apple"))
def a_spawn(obj, world, a, it):
    world.spawn_somewhere(a["kind"])


@action("remember", "remember {name} is {value}",
        Param("name", "Call it what?", "text", [], "chrome"),
        Param("value", "Which is?", "text", [], "com.android.chrome"))
def a_remember(obj, world, a, it):
    """Tie a short name to a long value, for the rest of this game."""
    name = str(a.get("name", "")).strip()
    if name:
        world.memory[name] = str(a.get("value", ""))


@action("open", "open {object} at {target}",
        Param("object", "Which app? (a name you remembered, or a package)",
              "text", [], "chrome"),
        Param("target", "Open what? (a name you remembered, or a URL)",
              "text", [], "http://127.0.0.1:8765/"))
def a_open(obj, world, a, it):
    """Hand a URL to another app on the phone.

    The only tile that reaches outside the game, so it is fenced three ways:

      * it does nothing unless whoever is playing turned opening on, which a
        shared world never does -- a guest cannot make the host's phone launch
        anything, however they edit the game
      * the same thing cannot be opened twice within OPEN_COOLDOWN ticks, so a
        row on `always` asks once a few seconds rather than six times a second
      * it never waits for the app, so a slow launch cannot stall the world
    """
    if not world.may_open:
        world.message = "opening is off in this world"
        return
    package = remembered(world, a.get("object", ""))
    target = remembered(world, a.get("target", ""))
    if not target:
        return
    key = (package, target)
    when = world.opened.get(key)
    if when is not None and world.tick - when < OPEN_COOLDOWN:
        return
    world.opened[key] = world.tick
    command = ["termux-open-url", target] + ([package] if package else [])
    try:
        subprocess.Popen(command, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
        world.message = "opening " + target
    except OSError:
        # No termux-open-url: a laptop, or a stripped-down phone. Say so in the
        # game rather than dying, since a game may be sitting on this row.
        world.message = "cannot open things on this device"


@action("vanish", "make {target} disappear",
        Param("target", "Who disappears?", "choice", ["it", "self"], "it"))
def a_vanish(obj, world, a, it):
    victim = obj if a["target"] == "self" else it
    if victim is not None:
        world.remove(victim)


@action("teleport", "jump to a random empty square")
def a_teleport(obj, world, a, it):
    spot = world.empty_cell()
    if spot:
        obj.x, obj.y = spot


@action("place_name", "name {who} is \"{text}\"",
        Param("who", "Which placeholder?", "text", [], "thing"),
        Param("text", "Name it what?", "text", [], "hero"))
def a_place_name(obj, world, a, it):
    """Regard a placeholder as a name, and write that name."""
    spot = place(world, a.get("who"))
    if spot is not None:
        spot["name"] = str(a.get("text", ""))


@action("place_value", "value {who} = {a} {op} {b}",
        Param("who", "Which placeholder?", "text", [], "thing"),
        Param("a", "First box of the sum?", "text", [], "0"),
        Param("op", "And then?", "choice", OPS, "plus"),
        Param("b", "Second box of the sum?", "text", [], "1"))
def a_place_value(obj, world, a, it):
    """Regard a placeholder as a value, and write the sum into it.

    Both boxes take a number, a `my`/`it`/`score`/`tick` word, or the name of
    another placeholder -- so `value score = score plus 1` counts, and
    `value gap = my x minus it x` measures.
    """
    spot = place(world, a.get("who"))
    if spot is not None:
        spot["value"] = total(a.get("a"), a.get("op"), a.get("b"),
                              obj, world, it)


@action("place_vector", "vector {who} {axis} = {a} {op} {b}",
        Param("who", "Which placeholder?", "text", [], "thing"),
        Param("axis", "Which axis -- x, y or z?", "choice", AXES, "x"),
        Param("a", "First box of the sum?", "text", [], "0"),
        Param("op", "And then?", "choice", OPS, "plus"),
        Param("b", "Second box of the sum?", "text", [], "1"))
def a_place_vector(obj, world, a, it):
    """Regard a placeholder as a vector, and write one axis of it.

    One axis per tile, so a row that sets all three is three of these -- which
    is also what lets a row set only the one axis it cares about and leave the
    others where they were.
    """
    spot = place(world, a.get("who"))
    axis = a.get("axis", "x")
    if spot is not None and axis in AXES:
        spot[axis] = total(a.get("a"), a.get("op"), a.get("b"), obj, world, it)


@action("place_here", "copy my place into vector {who}",
        Param("who", "Which placeholder?", "text", [], "home"))
def a_place_here(obj, world, a, it):
    """Write where I am standing into a vector, x and y, leaving z alone."""
    spot = place(world, a.get("who"))
    if spot is not None:
        spot["x"], spot["y"] = clamp(obj.x), clamp(obj.y)


@action("place_jump", "jump to vector {who}",
        Param("who", "Which placeholder?", "text", [], "home"))
def a_place_jump(obj, world, a, it):
    """Stand at the square a vector points to, if there is such a square.

    Deliberately obeys the edges but not solidity: it is a teleport, and the
    matching `teleport` tile does not check either. A vector pointing off the
    board does nothing rather than pinning you to the rim.
    """
    spot = world.places.get(str(a.get("who", "")).strip().lower())
    if spot is None:
        return
    x, y = clamp(spot["x"]), clamp(spot["y"])
    if world.in_bounds(x, y):
        obj.x, obj.y = x, y


@action("place_move", "move by vector {who}",
        Param("who", "Which placeholder?", "text", [], "step"))
def a_place_move(obj, world, a, it):
    """Take one step of the size and direction a vector holds.

    This goes through the same try_move as the `move` tile, so walls stop it
    and wrapping edges wrap it. z is ignored: the world is flat, and z is there
    for keeping a third number, not for a third direction of travel.
    """
    spot = world.places.get(str(a.get("who", "")).strip().lower())
    if spot is None:
        return
    dx, dy = clamp(spot["x"]), clamp(spot["y"])
    if dx or dy:
        obj.facing = (1 if dx > 0 else -1 if dx else 0,
                      1 if dy > 0 else -1 if dy else 0)
        world.try_move(obj, dx, dy)


@action("win", "win the game")
def a_win(obj, world, a, it):
    world.status = "win"


@action("lose", "lose the game")
def a_lose(obj, world, a, it):
    world.status = "lose"


# --------------------------------------------------------------------------
# Built-in brain for bullets, so "shoot" works before you design a shot.
# It is ordinary tile data -- copy it into a character to customise it.
# --------------------------------------------------------------------------

SHOT_BRAIN = [
    {"when": [{"tile": "always", "args": {}}],
     "do": [{"tile": "move", "args": {"dir": "forward"}}]},
    {"when": [{"tile": "touch", "args": {"kind": "anything"}}],
     "do": [{"tile": "damage", "args": {"target": "it", "amount": 1}},
            {"tile": "vanish", "args": {"target": "self"}}]},
    {"when": [{"tile": "spent", "args": {}}],
     "do": [{"tile": "vanish", "args": {"target": "self"}}]},
    {"when": [{"tile": "at_edge", "args": {}}],
     "do": [{"tile": "vanish", "args": {"target": "self"}}]},
]
