"""An example tile, shipped switched OFF.

This file is here to be read, and to show you the gate working: it came with
Spark rather than being written by you on this phone, so it is sitting inert.
Nothing in it has run. Open `your own tiles, written in Python` in the browser
editor, read it, and press `switch on` if you want it -- or write your own and
leave this alone.

That is the rule for every file in this folder, wherever it came from: pulled
from GitHub, handed over by another player, or copied off an SD card. Approval
is recorded on this device only (in `approved.json`, which is never committed),
against the exact text approved, so a file that changes afterwards goes quiet
again until you have looked at it.

Writing one
-----------
Everything from engine/tiles.py is already in scope: `sensor`, `action` and
`Param`. The built-in tiles are all this short -- read engine/tiles.py for
thirty-five worked examples.

A sensor is given (obj, world, a) and answers true or false; answering with a
character instead makes that character the row's "it". An action is given
(obj, world, a, it) and changes something.

    obj     the character running the row -- obj.x, obj.y, obj.health
    world   everything else -- world.score, world.tick, world.rng, world.things
    a       this tile's own settings, as you named them in its Params
    it      whoever the WHEN half found, or None

One thing to know
-----------------
These run in Termux, in the Python engine. The 3D view carries a second engine
written in JavaScript for when nothing is reachable, and it cannot run Python --
so a game that uses a tile from this folder plays through Termux, but its rows
will not fire in that offline browser engine. Tiles you fold together out of
existing tiles (the O button on a row) have no such limit and travel anywhere.
"""


@action("pace", "pace {far} squares {way}",
        Param("far", "How many squares?", "int", [], 1),
        Param("way", "Which way?", "choice", ["across", "down"], "across"))
def pace(obj, world, a, it):
    """Shuffle back and forth for ever, turning round at the edges.

    Which way it is going is kept on the character itself rather than in a
    placeholder, so two of these never tread on one another -- a plain Python
    attribute is per-character, where a placeholder is shared by the world.
    """
    far = max(1, a.get("far", 1))
    step = getattr(obj, "pace_step", far)
    if a.get("way") == "down":
        if not world.try_move(obj, 0, step):
            step = -step
    elif not world.try_move(obj, step, 0):
        step = -step
    obj.pace_step = step


@sensor("standing_still", "I have not moved for {ticks} ticks",
        Param("ticks", "How many ticks?", "int", [], 10))
def standing_still(obj, world, a):
    """True once a character has stayed on the same square a while.

    Shows the other half of the idea: remember something on the character,
    compare it next tick. `travelled` is counted for you by the engine.
    """
    was = getattr(obj, "still_at", None)
    since = getattr(obj, "still_since", 0)
    if was != (obj.x, obj.y):
        obj.still_at = (obj.x, obj.y)
        obj.still_since = world.tick
        return False
    return world.tick - since >= max(1, a.get("ticks", 10))
