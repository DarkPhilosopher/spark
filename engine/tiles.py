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
from dataclasses import dataclass, field
from typing import Any, Callable

DIRECTIONS = ["up", "down", "left", "right", "random", "toward it", "away from it", "forward"]
STEPS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
KEYS = ["up", "down", "left", "right", "space", "w", "a", "s", "d", "e", "f"]


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


@action("shoot", "shoot {dir}",
        Param("dir", "Shoot which way?", "choice", DIRECTIONS, "forward"))
def a_shoot(obj, world, a, it):
    dx, dy = resolve_step(a["dir"], obj, it)
    if not (dx or dy):
        return
    shot = world.spawn("shot", obj.x + dx, obj.y + dy)
    if shot:
        shot.facing = (dx, dy)
        shot.owner = obj


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
    {"when": [{"tile": "at_edge", "args": {}}],
     "do": [{"tile": "vanish", "args": {"target": "self"}}]},
]
