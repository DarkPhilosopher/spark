# Spark

Build a game by snapping tiles together. You never type code.

A game is a cast of **characters**. Each character has a **brain**, and a brain
is a list of rows. Every row reads the same way:

    WHEN something is true   DO something

That is the entire idea, and it is the same idea Kodu and Project Spark used.
Twelve tiles crossed with nine tiles is a hundred-odd sentences you can write
without knowing any Python.

## Start it

Two ways to build, both editing the same `games/*.json` files.

**Drag and drop, in your browser** (nicer on a phone):

    python3 ~/spark/spark.py edit

Then open <http://127.0.0.1:8765> if it does not open by itself. Tap a tile in
the palette to drop it into the highlighted row; tap a placed tile to change its
numbers; drag one to move it to another row or onto the bin. Press **save** and
the file lands in `games/`. Ctrl-C in the terminal stops the server. It listens
on 127.0.0.1 only, so nothing off your phone can reach it.

**From GitHub Pages**, once this repo is pushed: open your Pages link on any
device. Same editor, no Termux needed. Games save into the browser straight
away; tap ⚙ and paste a fine-grained token (Contents: read and write, this repo
only) and saving also commits `games/*.json` for real.

One catch: opening `index.html` as a `file://` path does not work — browsers
refuse to let a local page read its sibling files. Use `spark.py edit` for
offline; that is what it is for.

**Numbered menus, in the terminal** (works with no browser):

    python3 ~/spark/spark.py

To watch the demo first:

    python3 ~/spark/spark.py play games/chase.json

Arrow keys move, space shoots, `q` quits. Eat five apples to win; the bugs bite.

Then open `chase` from the menu and change it — that is the fastest way in.

## Knowing where you are

Every menu screen, and the browser header, starts with the same line:

    Spark exe  Github F  Browser F  Local T

- **Github** — a remote is set and every commit is pushed. `F` means either no
  remote yet, or you have commits sitting unpushed.
- **Browser** — an editor page has talked to the local server in the last 90
  seconds. In the browser this is always `T`, since you are in one.
- **Local** — the Python engine is on this device, so you can play and edit
  with no internet.

Ask any time with `python3 spark.py status`.

## The tiles

WHEN (sensors)                  DO (actions)
------------------------------  ------------------------------
always                          move up/down/left/right/random/toward it/away/forward
key <key> is pressed            shoot <direction>
I see <kind> within <n>         say "<text>"
I am touching <kind>            change the score by <n>
every <n> ticks                 hurt it/self by <n>
my health is below <n>          heal myself by <n>
the score is at least <n>       make a new <kind>
<n>% of the time                make it/self disappear
I am at the edge                jump to a random empty square
                                win / lose

**"it"** is whatever the WHEN tile found. `WHEN I see apple within 6 DO move
toward it` works because the seeing tile hands the apple to the moving tile.
That one word is what makes the tiles stick together.

Rows run top to bottom, every tick, and every row that fires gets to act. Put
`every 2 ticks` in front of a chase to make a slow enemy.

## Where things live

    spark.py            the launcher
    index.html          the drag-and-drop editor (works served or on Pages)
    tiles.json          the tile list, baked out for when no server is running
    games/*.json        your games, one file each
    games/index.json    the listing the static page reads
    engine/tiles.py     the tile library  <- add new pieces here
    engine/world.py     the grid and the rule engine
    engine/builder.py   the terminal menus
    engine/runner.py    keyboard and drawing
    engine/server.py    serves the editor, reads and writes games/
    engine/status.py    works out the Github / Browser / Local flags
    tests/store.test.js checks the editor's save/load logic (run: node tests/store.test.js)

`tiles.json` is generated. After adding a tile, run `python3 spark.py export`
and commit it, or the Pages copy will not show the new tile. Starting the
local server rewrites it for you.

## Inventing a new tile

One function. It appears on the menus by itself — nothing else to edit.

```python
@sensor("richer_than", "the score is above {value}",
        Param("value", "Above what score?", "int", [], 20))
def s_richer(obj, world, a):
    return world.score > a["value"]
```

A sensor returns `True`/`False`, or returns a character to hand it along as
"it". An action takes `(obj, world, args, it)` and changes something.

Your new tile appears in the terminal menus **and** in the browser palette by
itself — the editor asks the server for the tile list at startup and draws
whatever it finds, so there is no HTML to keep in sync.
