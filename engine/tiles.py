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


def resolve_step(name, obj, it):
    """Turn a direction name into a (dx, dy) step."""
    if name in STEPS:
        return STEPS[name]
    if name == "random":
        return random.choice(list(STEPS.values()))
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
    return random.randrange(100) < a["percent"]


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


# --------------------------------------------------------------------------
# ACTIONS -- the DO half
# --------------------------------------------------------------------------

@action("move", "move {dir}",
        Param("dir", "Move which way?", "choice", DIRECTIONS, "toward it"))
def a_move(obj, world, a, it):
    dx, dy = resolve_step(a["dir"], obj, it)
    if dx or dy:
        obj.facing = (dx, dy)
        world.try_move(obj, dx, dy)


@action("face", "face {dir}",
        Param("dir", "Which way do I face?", "choice", BEARINGS, "north"))
def a_face(obj, world, a, it):
    """Turn on the spot. Nothing moves; `forward` just means somewhere new."""
    dx, dy = resolve_step(a["dir"], obj, it)
    if dx or dy:
        obj.facing = (dx, dy)


@action("shoot", "shoot {dir} up to {reach} squares, for {life} ticks",
        Param("dir", "Shoot which way?", "choice", DIRECTIONS, "forward"),
        Param("reach", "How many squares does it fly? (0 = for ever)", "int", [], 8),
        Param("life", "How many ticks does it last? (0 = for ever)", "int", [], 12))
def a_shoot(obj, world, a, it):
    dx, dy = resolve_step(a["dir"], obj, it)
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
