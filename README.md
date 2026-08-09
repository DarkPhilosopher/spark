# Spark

Build a game by snapping tiles together. You never type code.

> Three documents live in this folder, and every change to Spark updates all
> three that it touches:
>
> - **README.md** — this file. The guide: what Spark is and how to use it.
> - **[MANUAL.md](MANUAL.md)** — the exact reference. System requirements, every
>   key and button, every command, and step-by-step instructions for connecting
>   the browser interface and GitHub.
> - **[CHANGELOG.md](CHANGELOG.md)** — what changed, when, and why.

A game is a cast of **characters**. Each character has a **brain**, and a brain
is a list of rows. Every row reads the same way:

    WHEN something is true   DO something

That is the whole idea, and it is the idea Kodu and Project Spark used. Nine
WHEN tiles crossed with eleven DO tiles is ninety-nine different sentences, and
rows can hold more than one tile each, so the real number is much larger.

---

## Contents

- [Where Spark lives](#where-spark-lives)
- [Start it](#start-it)
- [Knowing where you are](#knowing-where-you-are)
- [The tiles](#the-tiles)
- [How a brain runs](#how-a-brain-runs)
- [Every command](#every-command)
- [Where things live](#where-things-live)
- [What a game file looks like](#what-a-game-file-looks-like)
- [Playing with someone else](#playing-with-someone-else)
- [Putting it on GitHub](#putting-it-on-github)
- [Inventing a new tile](#inventing-a-new-tile)
- [When something goes wrong](#when-something-goes-wrong)

---

## Where Spark lives

    /data/data/com.termux/files/home/spark

That folder is Termux's home directory, so **from Termux** you can call it
`~/spark`. Inside the PRoot Linux distro `~` means `/root` instead, so there you
need the full path. Everything below writes `spark.py`, meaning "run it from
inside the spark folder":

    cd ~/spark            # from Termux
    python3 spark.py

Both Pythons on this phone run Spark — Termux's own (`python`) and the one
inside PRoot (`python3`). Nothing else needs installing.

---

## Start it

**Never used it before? Start here:**

    cd ~/spark
    python3 spark.py tutorial

Ten short lessons in the terminal that build a real game one row at a time. You
pick the tiles yourself and play what you have built four times along the way.
It takes about ten minutes, runs entirely on your phone with no internet, and
leaves you with a game saved in `games/`. It is also the first item on the main
menu, as *learn how*.

Otherwise, there are three ways in. All of them edit the same `games/*.json`
files, so you can start a game in one and finish it in another.

### 1. Drag and drop, in your browser

    python3 spark.py edit

Then open <http://127.0.0.1:8765> if it does not open by itself.

- **Tap** a tile in the palette at the bottom — it drops into the highlighted
  row. The WHEN / DO tabs choose which half of the row it lands in.
- **Tap** a tile you have already placed to change its numbers, or remove it.
- **Drag** a placed tile to move it to another row, or onto the red bin.
- **save** writes the file into `games/`.
- Ctrl-C in the terminal stops the server.

It listens on `127.0.0.1` only, which means nothing outside your phone can
reach it, even on shared wifi.

### 2. From GitHub Pages

Once the repo is pushed, open your Pages link on any device. Same editor, no
Termux needed, works on a laptop or someone else's phone.

Games save into the browser immediately. If you want them saved into the repo
for real, tap ⚙ and fill in your GitHub user, the repo, the branch, and a
fine-grained token with **Contents: read and write** on that one repo. Then
every save also commits `games/*.json`. See
[Putting it on GitHub](#putting-it-on-github).

### 3. Numbered menus, in the terminal

    python3 spark.py

No browser involved. Every choice is a number you type. Slower than dragging,
but it works anywhere, including over a phone keyboard with one thumb.

### See the demo first

    python3 spark.py play games/chase.json

Arrow keys move, space shoots, `q` quits. Eat five apples to win; two bugs chase
you and bite. Then open `chase` in either editor and change something — that is
the fastest way to understand the whole system.

---

## Knowing where you are

Every menu screen, and the browser header, starts with the same line:

    Spark exe  Github F  Browser F  Local T

| Flag | `T` means |
|---|---|
| **Github** | a remote is set **and** every commit is pushed. `F` means no remote yet, or you have commits sitting unpushed. |
| **Browser** | an editor page has spoken to the local server within the last 90 seconds. In the browser this is always `T`, because you are in one. |
| **Local** | the Python engine is on this device, so you can play and edit with no internet at all. |

Ask any time:

    python3 spark.py status

---

## The tiles

| WHEN (sensors) | DO (actions) |
|---|---|
| always | move — up, down, left, right, random, toward it, away from it, forward |
| key `<key>` is pressed | shoot `<direction>` |
| I see `<kind>` within `<n>` | say "`<text>`" |
| I am touching `<kind>` | change the score by `<n>` |
| every `<n>` ticks | hurt it / self by `<n>` |
| my health is below `<n>` | heal myself by `<n>` |
| the score is at least `<n>` | make a new `<kind>` |
| `<n>`% of the time | make it / self disappear |
| I am at the edge of the world | jump to a random empty square |
| | win the game |
| | lose the game |

`<kind>` is the name of one of your characters, or **anything**, which matches
all of them.

### The word "it"

**"it"** is whatever the WHEN tile found.

    WHEN I see apple within 6   DO move toward it

The seeing tile finds an apple and hands it to the moving tile. That one word is
what makes tiles stick together instead of just sitting next to each other. The
tiles that produce an "it" are *I see* and *I am touching*; the ones that use it
are *move toward/away from it*, *hurt it*, and *make it disappear*.

If a row has no sensor that found something, "it" is empty and those actions do
nothing rather than misfiring.

---

## How a brain runs

Six times a second (the speed is yours to change), for each character:

1. Read the brain rows from top to bottom.
2. A row fires when **all** of its WHEN tiles are true. Two WHEN tiles on one
   row means *and*.
3. When a row fires, **all** of its DO tiles run.
4. Keep going. Every row that fires gets to act, not just the first one.

That last point is worth knowing: put `every 2 ticks` in front of a chase to
make a slow enemy, because otherwise the enemy moves as often as you do.

Some other rules worth knowing:

- A character with **role: player** ends the game if all of them die. Everything
  else is scenery, enemies or pickups.
- A **solid** character blocks others from walking through it. Walls are solid.
- Health starts wherever you set it; at zero the character disappears.
- Bullets are a character called `shot` that Spark provides. They fly forward,
  hurt the first thing they touch, and vanish at the edge. They never hit
  whoever fired them.

---

## Every command

| Command | What it does |
|---|---|
| `python3 spark.py tutorial` | ten guided lessons that build your first game |
| `python3 spark.py` | the terminal menus |
| `python3 spark.py edit` | the browser editor on port 8765 |
| `python3 spark.py edit 9000` | same, on a port you choose |
| `python3 spark.py host` | the editor, open to others on this wifi |
| `python3 spark.py host --public` | ...and to anyone, through a tunnel |
| `python3 spark.py people` | who else can reach your GitHub repo |
| `python3 spark.py people NAME` | let a GitHub user edit your games |
| `python3 spark.py play games/chase.json` | play a game straight away |
| `python3 spark.py play games/chase.json 200` | run 200 ticks with no display, for testing |
| `python3 spark.py status` | print the Github / Browser / Local line |
| `python3 spark.py export` | rewrite `tiles.json` and `games/index.json` |
| `python3 spark.py push [game ...]` | overwrite games on GitHub with this phone's |
| `python3 spark.py pull [game ...]` | overwrite games here with GitHub's |
| `python3 spark.py games/chase.json` | open the menus with that game already loaded |
| `node tests/store.test.js` | check the editor's save and load logic |
| `python3 tests/check_docs.py` | check this README still matches the code |
| `python3 tests/check_sync.py` | check the GitHub push/pull logic |
| `python3 tests/check_permissions.py` | check guests cannot exceed their code |
| `python3 tests/check_multiplayer.py` | check two players share one world |

---

## Where things live

    spark.py             the launcher — every command above goes through it
    index.html           the drag-and-drop editor (served locally or by Pages)
    README.md            this guide
    MANUAL.md            controls, requirements, and how to connect things
    CHANGELOG.md         what changed and when
    tiles.json           the tile list, written out for when no server is running
    games/*.json         your games, one file each
    games/index.json     the list of games, for when no server is running
    engine/tiles.py      the tile library      <- add new pieces here
    engine/world.py      the grid, the characters, and the rule engine
    engine/brain.py      reading and writing game files
    engine/builder.py    the terminal menus
    engine/tutorial.py   the ten guided lessons
    engine/runner.py     the keyboard and the drawing
    engine/server.py     serves the editor, reads and writes games/
    engine/status.py     works out the Github / Browser / Local flags
    engine/sync.py       push and pull single games to and from GitHub
    engine/live.py       the shared world: invite codes, roles, connected people
    engine/tunnel.py     finds and runs cloudflared or ngrok for public play
    tests/store.test.js  17 checks on the editor's save and load logic
    tests/check_docs.py  fails if this README has drifted from the code
    tests/check_sync.py  checks the GitHub push/pull logic, without the network
    tests/check_permissions.py  checks a guest can only do what their code allows
    tests/check_multiplayer.py  two players in one world, over real HTTP

Two files are **generated** — do not edit them by hand:

- `tiles.json` and `games/index.json`. Run `python3 spark.py export` after
  adding a tile, and commit the result, or the GitHub Pages copy will not show
  it. Starting the local server rewrites them for you.

One file is ignored by git: `.spark-state.json`, which is how the server tells
the terminal that a browser is connected.

---

## What a game file looks like

You never have to read this — both editors write it for you — but it is plain
text, and knowing the shape makes the whole thing less mysterious.

```json
{
  "name": "chase",
  "world": { "width": 30, "height": 14, "wrap": false, "speed": 6 },
  "characters": [
    {
      "kind": "hero",
      "glyph": "@",
      "color": "cyan",
      "health": 3,
      "count": 1,
      "solid": false,
      "role": "player",
      "brain": [
        { "when": [ { "tile": "key",   "args": { "key": "up" } } ],
          "do":   [ { "tile": "move",  "args": { "dir": "up" } } ] }
      ]
    }
  ]
}
```

- **glyph** is the single letter drawn on the grid, **count** is how many exist
  when the game starts, **speed** is ticks per second, **wrap** makes walking
  off one edge bring you back on the other.
- Each brain row is `{"when": [...], "do": [...]}`, and each tile inside is
  `{"tile": "<id>", "args": {...}}`. That is the entire format.

---

## Playing with someone else

Instead of `edit`, run:

    python3 spark.py host

It prints two addresses. The first is for **you**, on this phone, and carries a
key that makes you the owner. The second is the one you read out to whoever is
on the same wifi.

Then make them a code — terminal main menu → **invite someone to play**, or the
👥 button in the browser. They open your address, type the code, and they are
in. Everyone plays the same world at the same time, each driving their own
character.

The code decides what they may do:

| Code says | They can |
|---|---|
| **edit** | change games and save them, and play |
| **play** | join the world and press keys, nothing else |
| **watch** | see the world, and nothing else |

Revoke a code at any time. Anyone who joined with it is removed with it.

**For people not on your wifi:**

    python3 spark.py host --public

That needs a tunnel program, and **cloudflared is already installed here**, so it
should just work. Spark runs it and prints an address anyone in the world can
open. Without one, it says so and wifi still works. Your phone has no address the
internet can dial by itself; that is how mobile networks are, not something Spark
can fix. [MANUAL.md](MANUAL.md) has installation instructions if you ever need
them again — `pkg install` will not do it, because it refuses to run as root.

**Two things worth knowing.** When you share, being on the phone is no longer
enough to make you the owner — you must open the link with the key in it, which
is why the terminal prints it. And there is no rate limiting: hand codes to
people you would hand your phone to.

There is also a slower way to share, over GitHub instead of live —
`python3 spark.py people NAME` lets another GitHub user edit your games. See
[MANUAL.md](MANUAL.md).

## Putting it on GitHub

Two separate things, and it is worth keeping them apart in your head:

1. **Publishing the editor** so you can open it from a web address. Push the
   repo, turn on GitHub Pages, and the Pages link serves `index.html`. This
   needs a **public** repo — Pages on a private repo requires a paid plan.
2. **Saving games back into the repo from the browser.** That is the ⚙ button
   and the token, and it is entirely optional.

**About the token.** Make a fine-grained one, scoped to that single repo, with
Contents: read and write and nothing else. It is stored in your browser, which
means anyone holding your unlocked phone can read it. ⚙ → *forget token*
removes it. Never paste a classic token with wide access.

Publishing the editor does **not** stop it working offline. The local server and
the Pages copy are the same file behaving differently depending on whether a
server answers it.

---

## Inventing a new tile

One function. It appears on the menus and in the browser palette by itself.

```python
@sensor("richer_than", "the score is above {value}",
        Param("value", "Above what score?", "int", [], 20))
def s_richer(obj, world, a):
    return world.score > a["value"]
```

- The first line is the tile's id, then the sentence shown on the menus. Every
  `{name}` in that sentence must match a `Param`, or the label will not fill in.
- A **sensor** returns `True`/`False`, or returns a character to hand it along
  as "it".
- An **action** takes `(obj, world, args, it)` and changes something.

Then run `python3 spark.py export` so the offline and Pages copies know about
it, and add it to the tile table above and to `CHANGELOG.md`.

The reason there is no HTML to edit: the editor asks for the tile list at
startup — from the server if there is one, from `tiles.json` if not — and draws
whatever it finds. `engine/tiles.py` is the only place tiles are defined.

---

## When something goes wrong

**The page says it cannot read `tiles.json`.**
You opened `index.html` by tapping the file itself. Browsers forbid a `file://`
page from reading the files next to it, and that cannot be worked around. Use
`python3 spark.py edit`, or the Pages link.

**A new tile is missing from the browser editor.**
Run `python3 spark.py export`, then reload. If it is missing on GitHub Pages,
you also need to commit and push the new `tiles.json`.

**Saving says "this browser" when you expected a commit.**
The token is missing, expired, or lacks Contents: read and write on that repo.
The message after a failed commit says what GitHub complained about. Your game
is safe either way — it saved in the browser first.

**Github shows `F` when you think you have pushed.**
Either there is no remote yet, or there are commits you have not pushed. Check
with `git status -sb`.

**The keyboard does nothing while playing.**
The game needs a real terminal. Playing through a pipe, or with output
redirected, runs the world without reading keys — which is what
`play games/chase.json 200` deliberately does.

**A character will not move.**
Check the row order and whether something solid is in the way. Remember that a
row with no WHEN tile never fires, and one with no DO tile does nothing; the
editor shows both as *never fires* and *does nothing*.
