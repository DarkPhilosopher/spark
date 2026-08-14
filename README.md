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

That is the whole idea, and it is the idea Kodu and Project Spark used. Fourteen
WHEN tiles crossed with twenty-one DO tiles is two hundred and ninety-four
different sentences, and rows can hold more than one tile each, so the real
number is much larger. One of those tiles is **your own**: fold any row up under
a name and it joins the palette like the rest.

---

## Contents

- [Where Spark lives](#where-spark-lives)
- [Start it](#start-it)
- [Knowing where you are](#knowing-where-you-are)
- [The tiles](#the-tiles)
- [How a brain runs](#how-a-brain-runs)
- [Seeing it in 3D](#seeing-it-in-3d)
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

**One-time setup**, so you can type one word instead of a path:

    cd ~/spark
    python3 spark.py install

After that, `spark` on its own starts it from anywhere in Termux. Every command
below can drop the `python3 spark.py` and just say `spark`.

**Never used it before? Start here:**

    spark tutorial

Ten short lessons in the terminal that build a real game one row at a time. You
pick the tiles yourself and play what you have built four times along the way.
It takes about ten minutes, runs entirely on your phone with no internet, and
leaves you with a game saved in `games/`. It is also the first item on the main
menu, as *learn how*.

Otherwise, there are three ways in. All of them edit the same `games/*.json`
files, so you can start a game in one and finish it in another.

### The deck: six buttons and a box

The browser opens on **six buttons and a box to type in**, filling the screen.

| | |
|---|---|
| **play** | run the game — live through Termux, or in the 3D view if there is no server |
| **edit** | open, save, rename, new, GitHub, sharing |
| **characters** | the cast, and what each one looks like |
| **brain** | the rows, the tiles, undo, and ⊞ fold |
| **tiles** | your own — folded ones and Python ones |
| **save** | write the game down |

**Every screen is the same six-button formation** — not just this one. Opening
*characters* gives you a button per character; opening one of those gives you a
button per setting; *brain* gives a button per row, and a row gives a button per
tile. The tile palette is buttons too, all thirty-five of them, which is what
the scrolling is for. `‹` beside the box goes back up one.

Only two things are not buttons, because they cannot be: a tile's settings, and
the Python text editor. Both open over the deck.

**How it sits on the screen.** Eight cells. Six are buttons, and the two left
over are the box.

    held upright                 held sideways
    ┌──────────┬──────────┐      ┌───────┬───────┬───────┬────────┐
    │  play    │  edit    │      │ play  │ chars │ tiles │        │
    ├──────────┼──────────┤      ├───────┼───────┼───────┤  box   │
    │ characters│ brain   │      │ edit  │ brain │ save  │        │
    ├──────────┼──────────┤      └───────┴───────┴───────┴────────┘
    │  tiles   │  save    │
    ├──────────┴──────────┤      /swap side chat puts the box on the left
    │        box          │
    └─────────────────────┘

The buttons resize to fill whatever screen they are on, and the whole thing
fits without the page ever scrolling. If there are ever more than six buttons,
the button area **scrolls up and down** in the same formation — the columns stay
put and the rows run on.

**The box** takes commands, or plain words to talk to whoever else is in your
world:

| Typed | What happens |
|---|---|
| `/help` | everything below, on screen |
| `/play` `/edit` `/characters` `/brain` `/tiles` `/save` | the same as the buttons |
| `/pin "feed the bug first"` | keep a note. Quotes optional |
| `/pins` | list them |
| `/unpin 2` | remove one |
| `/back` `/home` | up one screen; back to the six |
| `/swap side chat` | put the box on the other side when the phone is sideways |
| `/who` | who is connected |
| `/clear` | empty the log |
| anything not starting with `/` | said to the others, if there are any |

Notes are kept in this browser. Chat needs the server running — everyone who can
see the world can talk, **watchers included**, since somebody who may only look
is still a person in the room. One line is capped at 300 characters and only the
last 40 are kept: a shared world is a conversation while it is happening, not a
record afterwards, so nothing said reaches the disk.

Guests get the deck too — **play** and the box — but not the four buttons that
change the game.

### 1. Drag and drop, in your browser

    spark edit

Then open <http://127.0.0.1:8765> if it does not open by itself.

Or, if you are already in the menus, **type `browser`** at any prompt. It starts
the editor beside the menus and opens it, and you keep both — they share the
same `games/` folder, so save in one and re-open the game in the other to see
the change.

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

    Spark exe  Github F  Browser F  Local T  Cloudflare F  Players 0

| Flag | `T` means |
|---|---|
| **Github** | a remote is set **and** every commit is pushed. `F` means no remote yet, or you have commits sitting unpushed. |
| **Browser** | an editor page has spoken to the local server within the last 90 seconds. In the browser this is always `T`, because you are in one. |
| **Local** | the Python engine is on this device, so you can play and edit with no internet at all. |
| **Cloudflare** | a cloudflared tunnel is up, so the public address works and anyone anywhere can join. Only `spark.py host --public` raises it, and it drops back to `F` the moment Spark stops. ngrok shows `F` — this flag names cloudflared exactly. |

**Players** is a count, not a `T` or an `F`: how many people are connected to
your world this second. It counts everyone who typed a valid invite code,
whether they are playing, editing or only watching, and it drops on its own
about 25 seconds after somebody closes their tab.

Ask any time:

    python3 spark.py status

### Who exactly is connected

    python3 spark.py players

or type **`players`** at any menu prompt — the same word works everywhere
`browser` does. It prints them **in the order they joined**, oldest at the top,
with the game each one is inside:

         name             may    inside         joined
     ----------------------------------------------------
     1.  Gabriel          edit   chase          14m ago
     2.  sam              play   chase          6m ago
     3.  bex              watch  chase          just now

     3 connected. The one who joined first is at the top.

If somebody leaves and comes back they go to the **bottom**, because that is
when they joined the world you have now. `inside` reads `no game yet` for people
who arrived before you started a game — they are connected and waiting.

---

## The tiles

| WHEN (sensors) | DO (actions) |
|---|---|
| always | move — up, down, left, right, random, toward it, away from it, forward |
| key `<key>` is pressed | face `<bearing>` — the eight compass points, or toward / away from it |
| I see `<kind>` within `<n>` | shoot `<direction>` up to `<n>` squares, for `<n>` ticks |
| I am touching `<kind>` | say "`<text>`" |
| every `<n>` ticks | change the score by `<n>` |
| my health is below `<n>` | hurt it / self by `<n>` |
| the score is at least `<n>` | heal myself by `<n>` |
| `<n>`% of the time | make a new `<kind>` |
| I am at the edge of the world | make it / self disappear |
| my range or time has run out | jump to a random empty square |
| I remember `<name>` is `<value>` | remember `<name>` is `<value>` |
| placeholder `<who>` has `<face>` `<test>` `<n>` | open `<object>` at `<target>` |
| placeholder `<who>` is named "`<text>`" | name `<who>` is "`<text>`" |
| the tile called "`<name>`" — one of your own | the tile called "`<name>`" — one of your own |
| | value `<who>` = `<box>` `<op>` `<box>` |
| | vector `<who>` `<axis>` = `<box>` `<op>` `<box>` |
| | copy my place into vector `<who>` |
| | jump to vector `<who>` |
| | move by vector `<who>` |
| | win the game |
| | lose the game |

`<kind>` is the name of one of your characters, or **anything**, which matches
all of them.

### Every tile is offered in both halves

The palette shows the half you are on first, then **every other tile as well**,
dashed and dimmed under a heading. The terminal menus do the same, marking the
strays. Nothing is withheld from you — which tile belongs where is the engine's
rule, and you may want to place one anyway to see what happens.

What happens is worth knowing before you do:

| Where | What the engine does |
|---|---|
| a **DO** tile in the **WHEN** half | the row **never fires at all** — the engine looks for it among the sensors, does not find it, and abandons the row |
| a **WHEN** tile in the **DO** half | it is quietly skipped; the rest of the row still runs |

Placed strays stay marked, so a row that never fires shows why on its face. Tap
the button at the top of the palette to go back to only the tiles that fit.

### Making a tile of your own

Build a row you like, then fold the whole thing up under a name. It joins the
palette and you can use it anywhere, as often as you like.

- **In the browser** — the **⊞** button on the row.
- **In the terminal** — *fold a row into one tile of your own*, on the brain
  menu.

**Both halves go in together.** That is what makes it worth doing: the one tile
works on either side, and does the matching half of what you folded.

    the row:  WHEN I see apple within 6   DO move toward it, hurt it by 1

    folded as "hunt", it becomes:

    WHEN ⊞ hunt   the seeing part is tested
    DO   ⊞ hunt   the moving and hurting part runs

The row you folded is replaced by the new tile in both halves, so the character
carries on doing exactly what it did — folding tidies, it never changes
behaviour.

**"it" reaches inside.** A sensor inside your tile that finds a character hands
it out to the row, and an action inside your tile is handed whatever the row
found. So `⊞ hunt` above still moves toward the apple its own sensor saw, and a
tile made only of `hurt it` still hurts whatever the row's WHEN half saw.

**Your tiles can hold your tiles**, up to eight deep. One that contains itself
stops at that depth rather than spinning for ever.

**They live in the game file**, under `tiles`, so they travel with the game
everywhere it goes — to GitHub, and to anyone who joins your world. Nothing has
to be installed and no code is run: a named tile is only other tiles.

Delete one with the **✕** on its palette chip, or from *your own tiles* on the
main menu in the terminal. Rows still pointing at a deleted tile are left alone
— the engine treats a name nobody has defined as simply not firing, and the chip
says `(no such tile)` — which is kinder than deleting those rows too.

### Writing a tile in Python

There is a plain-text editor in the browser — **your own tiles, written in
Python** — that writes files into `mytiles/`. A tile there is an ordinary Spark
tile: it appears on the menus and is used like any other.

    @action("pace", "pace {far} squares {way}",
            Param("far", "How many squares?", "int", [], 1),
            Param("way", "Which way?", "choice", ["across", "down"], "across"))
    def pace(obj, world, a, it):
        ...

`mytiles/example.py` ships with Spark, switched off, with the whole shape
explained inside. Read it first.

**This is the one part of Spark that runs code**, rather than reading a
description of what to do. Python can do whatever Python can do — read your
files, reach the network, delete things. So there are two rules, and they are
enforced rather than remembered:

**1. Only you can write one.** The browser routes for these answer the **owner**
only: whoever is at the phone, or holds the key printed in the terminal.
Somebody holding an `edit` code may rewrite every game you own and cannot put a
single line of Python on your disk. That is deliberate — an `edit` guest cannot
even make your phone open a link (see the fences on `open`), and this would have
walked past all of it.

**2. A file does nothing until this device says so.** Approval is recorded in
`mytiles/approved.json`, against the exact text approved — and that file is
**never committed**. So:

| Where the file came from | What happens |
|---|---|
| you wrote it in the browser | approved as it is saved — writing it *is* approving it |
| pulled from GitHub, sent by another player, copied off an SD card | it sits there **inert** until you have read it and pressed *switch on* |
| approved once, then changed by anything but you | stops loading, and says *changed since you approved it* |

None of this is a sandbox — there is no such thing for Python, and pretending
otherwise would be worse than useless. It is a gate, and the gate is your
consent.

**One real limit.** These run in Termux, in the Python engine. The 3D view
carries [a second engine written in JavaScript](#two-engines-kept-honest) for
when nothing is reachable, and it cannot run Python. A game using a tile from
`mytiles/` plays fine through Termux and through the server, but those rows will
not fire in the browser's own offline engine.

If you want a tile of your own that works **everywhere** — offline in the
browser, on GitHub Pages, on another player's phone — fold one out of existing
tiles instead. That is [the section above](#making-a-tile-of-your-own), and it
needs no code and no permission.

A tile that will not compile is reported in the editor and skipped; it can never
stop Spark starting, because you would then have no way back in to fix it.

### Undoing

Both editors keep an undo of the last **60** changes to the brain you are
editing:

- **In the browser** — the `undo` button beside *+ add a row*. It counts what is
  left, and greys out when there is nothing.
- **In the terminal** — *undo the last change* on the brain menu and on the
  row-editing menu, with the same count in brackets.

It covers everything the brain editor does — adding and removing rows, moving
them, adding and removing tiles, changing a tile's settings, dragging a tile
between rows — and deleting a character, since that throws brains away. It does
**not** cover a character's colour, glyph or health, which are one retype to put
back, nor world settings.

The two stacks are separate on purpose: each undoes what you did in front of it.
Opening a different game empties the history, so undo can never quietly swap one
game for another.

### Remembering something, and opening another app

Two tiles that have nothing to do with the grid. **remember** ties a short name
to a longer value, and every tile afterwards can use the short one:

    WHEN always              DO remember chrome is com.android.chrome
                                remember home is http://127.0.0.1:8765/

**open** hands a target to another app on the phone. Because of the two rows
above, this now reads the way you would say it out loud:

    WHEN key o is pressed    DO open chrome at home

Both boxes take **either** a name you remembered **or** the real thing, so the
whole game can also be written in one row with nothing remembered at all:

    WHEN key o is pressed    DO open com.android.chrome at http://127.0.0.1:8765/

Leave the app box empty to use whatever the phone normally opens links with.
The matching WHEN tile, **I remember `<name>` is `<value>`**, reads a name back,
which is how a game asks *has this happened yet* — nothing is remembered when a
game starts.

**Three things fence `open` in**, because it is the only tile that reaches out
of the game:

- **A shared world never opens anything.** Only a game you are playing yourself
  can. Somebody holding an `edit` code cannot add an `open` row and make your
  phone launch things, and neither can a game that came down from GitHub until
  you play it.
- **The same thing will not open twice within 30 ticks**, so a row on `always`
  asks about once every five seconds instead of six times a second.
- **It never waits for the app**, so a slow one cannot freeze the world.

If nothing happens, the phone has nothing that opens that kind of link — see
[When something goes wrong](#when-something-goes-wrong).

### Placeholders: one slot, regarded three ways

A **placeholder** is a name you invent — `speed`, `home`, `target`, anything at
all — and the world keeps a slot under it. The slot has **three faces at once**,
and each tile says which face it is regarding:

| Face | What it holds | The tile that writes it |
|---|---|---|
| its **name** | a piece of text | name `<who>` is "`<text>`" |
| its **value** | one number, decimals and all | value `<who>` = `<box>` `<op>` `<box>` |
| its **vector** | three numbers — x, y and z | vector `<who>` `<axis>` = `<box>` `<op>` `<box>` |

They are three faces of the same slot, not three slots. `home` can be named,
valued and pointed at a square all at the same time, and each face is read back
on its own.

**Nothing has to be set up first.** You do not declare a placeholder; you just
use the name and the slot appears underneath it. One nobody has written to has
an empty name, a value of **0** and a vector of **(0, 0, 0)**, so a row may read
one before any row has written it and still get a sensible answer. That is what
makes it a *placeholder* — it stands in for something before there is anything
there. Capitals and spare spaces are ignored, so `Home` and `home` are the one
slot.

**The `=` half is a sum.** Two boxes with one of nine words between them:

| Word | What it does | Reads as |
|---|---|---|
| **plus** | add the two boxes | `value gold = gold plus 5` |
| **minus** | take the second from the first | `value gap = it x minus my x` |
| **times** | multiply them | `value area = side times side` |
| **divided by** | divide. `7 divided by 2` is `3.5`. Dividing by 0 gives 0 | `value half = gold divided by 2` |
| **remainder** | what is left over after dividing — the `%` you were thinking of | `value spin = tick remainder 4` |
| **to the power of** | the first multiplied by itself that many times | `value big = 2 to the power of 8` |
| **but no more than** | the smaller of the two — a ceiling | `value speed = speed but no more than 5` |
| **but no less than** | the larger of the two — a floor | `value health = health but no less than 0` |
| **how far from** | the gap between them, never negative | `value away = my x how far from it x` |

The last four are the ones worth knowing about, because they are the ones you
would otherwise need several rows to fake:

- **remainder** is how you make anything go round in a circle. `tick remainder
  4` counts 0, 1, 2, 3, 0, 1, 2, 3… for ever, which is a four-frame animation,
  a four-step patrol, or every-fourth-turn behaviour.
- **but no more than** / **but no less than** are a ceiling and a floor. Chain
  them and a value is fenced into a range in two tiles:

      DO value speed = speed but no more than 5
         value speed = speed but no less than 1

- **how far from** is distance along one axis, and it never comes out negative.
  Against `0` it is plain absolute value, which nothing else here gives you.

**Signs, pinned down.** `remainder` has a trap in it, and Spark picks one answer
for both engines rather than letting each language decide:

| | Spark says | Python alone would say | JavaScript alone would say |
|---|---|---|---|
| `-7 remainder 5` | `-2` — the sign of the **left** box | 3 | −2 |
| `7 remainder -5` | `2` | −3 | 2 |

The leftover always takes the sign of the thing being divided up. It is measured
against a division cut *toward zero*, which is not quite what `divided by` does
now that it keeps the fraction — so at or above zero the two reconcile as
`down (7 divided by 5) times 5 plus (7 remainder 5) = 7`, and below zero `down`
cuts the other way and they no longer line up in tiles.

**to the power of** rounds its exponent to a whole number, and a negative one
gives 0 — a fractional power is what `root` is for. Anything to the power of 0
is 1, including 0 itself. A power that runs off the end stops at the fence with
the right sign rather than building a thousand-digit number.

**What you can put in a box.** Read in this order, first match wins:

| In the box | What it means |
|---|---|
| *(empty)* | 0 |
| `12`, `-3`, `2.5`, `.5` | that number, fraction and all |
| `root <box>` | its square root — below zero there is none, so 0 |
| `round <box>` | the nearest whole number, halves away from zero |
| `down <box>` | the whole number at or below it |
| `up <box>` | the whole number at or above it |
| `random <box>` | a whole number from 0 up to but **not including** it |
| `my x`, `my y`, `my health`, `my age`, `my travelled` | about me |
| `it x`, `it y`, `it health`, `it age`, `it travelled` | about whoever the WHEN half found |
| `score`, `tick` | about the world |
| `speed` | the **value** face of the placeholder called speed |
| `home x` | one axis of the **vector** face of the placeholder home |
| anything else | 0 |

The five word forms take a box of their own, so they nest one deep:
`root home x`, `random my health`, `round root 17`. A box holds **one** thing —
it is not a formula, and `7 divided by 5` is a whole tile, not something you can
write inside a box.

**Dice.** `random 6` gives 0, 1, 2, 3, 4 or 5, so ordinary dice are
`random 6 plus 1`. It rolls the world's own dice, which means a seeded world
rolls the same numbers in both engines. `random` of zero or less is 0 rather
than an error.

So a counter is one row, reading its own placeholder and writing it back:

    WHEN every 1 ticks   DO value steps = steps plus 1

and a placeholder can measure the gap between two characters:

    WHEN I see apple within 6   DO value gap = it x minus my x

**Vectors that do something.** Three tiles make a vector more than bookkeeping:

    WHEN key h is pressed   DO copy my place into vector home
    WHEN key g is pressed   DO jump to vector home

*copy my place into vector* writes where you are standing into x and y, leaving
z alone. *jump to vector* stands you on that square — it obeys the edges of the
world, and does nothing at all if the vector points off the board. *move by
vector* takes one step of that size and direction, going through the same walls
and wrapping edges as the ordinary *move* tile. z is kept for you but never
travelled: the world is flat, and z is there for holding a third number.

**Asking about one.** Two WHEN tiles read placeholders back:

    WHEN placeholder eaten has value at least 5    DO win the game
    WHEN placeholder target is named "apple"       DO ...

The first picks its face — **value**, **x**, **y** or **z** — and its
comparison — **at least**, **at most** or **exactly**. Its right-hand side is a
whole **box**, not merely a number, so it compares two moving things as readily
as one against a constant:

    WHEN placeholder gap has value at least my health   DO ...

(There is no `it` in the WHEN half — `it` is what the sensors produce — so
`it x` in that box reads as 0.)

The second tile reads the name face, which is how a row asks *which thing is
this placeholder standing in for at the moment*.

**Decimals, inside a fence.** A placeholder holds ordinary decimal numbers — a
half stays a half — between −1,000,000,000 and 1,000,000,000. A sum that runs
past either end stops there.

The fence is what keeps the browser's copy of the engine in step. Both engines
use the very same 64-bit numbers, so `+`, `−`, `×`, `÷` and `root` give
bit-for-bit identical answers on each — but only while values stay in a sane
range. See [Two engines, kept honest](#two-engines-kept-honest).

**Squares are still whole.** The grid has not become fractional: *jump to
vector* and *move by vector* round to the nearest square, so a vector of `0.4`
moves you nowhere and `0.6` moves you a full square. To creep along slower than
a square a tick, add the fraction to a placeholder every tick and move by the
whole part of it:

    WHEN always  DO value creep = creep plus 0.25
                    vector step x = down creep plus 0
                    value creep = creep remainder 1

`games/placeholders.json` is a small worked game that uses all of this — open it
and read the rows.

### Which way am I pointing

**face** turns a character on the spot. Nothing moves; only its bearing
changes. The eight choices are the compass rose — **north**, **north-east**,
**east**, **south-east**, **south**, **south-west**, **west**, **north-west** —
plus **toward it** and **away from it**. North is up the screen.

That bearing is what **forward** means afterwards, for both *move forward* and
*shoot forward*. The diagonals live only on the compass, so this is the way to
get a diagonal shot:

    WHEN key e is pressed      DO face north-east
    WHEN key space is pressed  DO shoot forward

*move* and *shoot* also set the bearing as a side effect, so a character that
walks left is then facing left. Use *face* when you want to aim without
walking — a turret, or a gun that turns while its owner stands still.

### How far a shot goes, and how long it lasts

The **shoot** tile asks two more questions after the direction:

| Question | What it sets |
|---|---|
| how many squares does it fly | its **reach** — it dies once it is that many squares from you |
| how many ticks does it last | its **longevity** — it dies once it has been alive that long |

Either can be **0**, meaning no limit from that one. Both at 0 and the shot
flies until it hits something or reaches the edge of the world. A short reach
makes a punch; a long reach with a short life makes a shot that fades in
mid-air; blockers matter too, because a shot pinned against a wall stops
covering ground but keeps ageing.

The limits are not secret machinery. They are read by the WHEN tile **my range
or time has run out**, which is an ordinary row in the shot's brain:

    WHEN always                  DO move forward
    WHEN I am touching anything  DO hurt it by 1, make self disappear
    WHEN my range or time has run out  DO make self disappear
    WHEN I am at the edge of the world DO make self disappear

Make your own character called `shot` and you can rewrite those rows however
you like — have it explode into something, or bounce, or score.

### The word "it"

**"it"** is whatever the WHEN tile found.

    WHEN I see apple within 6   DO move toward it

The seeing tile finds an apple and hands it to the moving tile. That one word is
what makes tiles stick together instead of just sitting next to each other. The
tiles that produce an "it" are *I see* and *I am touching*; the ones that use it
are *move* and *face toward/away from it*, *hurt it*, and *make it disappear*.

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
  hurt the first thing they touch, and vanish at the edge, when their reach runs
  out, or when their time does. They never hit whoever fired them.

---

## Seeing it in 3D

There is a **▶ 3D** button at the top of the browser editor. It opens a second
tab where the same world stands up off the page: every character becomes a
block on a board you can turn with one finger and pinch to zoom. The glyph you
chose sits on top of its block, so a `@` is still a `@`, and the colours are the
ones you picked.

Nothing is downloaded to make that happen. The 3D is drawn with WebGL, which is
already in the phone's browser, and no library is fetched from anywhere -- a
page that reaches out to a CDN is a page that goes blank the moment you lose
signal, which is the opposite of what this is for.

**It works whether or not anything is running.** The tab looks for a Spark
server first, and shows one of two badges in the corner:

| Badge | What you are looking at |
|---|---|
| `LIVE` | the real game running in Termux, mirrored tick for tick — what everyone else in a shared world sees |
| `RUNNING HERE` | the tab playing the game by itself, in the browser |

So the same link behaves sensibly in all of these:

    spark.py host, phone on wifi        LIVE  -- the shared world, in 3D
    spark.py host --public, tunnel      LIVE  -- guests see it too
    the GitHub Pages copy               RUNNING HERE
    aeroplane mode, Termux closed       RUNNING HERE
    the .html file saved and reopened   RUNNING HERE

The last two work because the **▶ 3D** button packs the whole game into the
link itself, after the `#`. A fragment never travels to any server, so the tab
already has everything it needs before it asks anyone for anything. That also
means it shows the game as it is *on screen* — you do not have to save first.

The `run here` button forces the local engine even when a server is there, which
is the quickest way to try a change without disturbing a game other people are
playing. `centre` puts the camera back where it started.

### Two engines, kept honest

Running a game with no server means Spark now has its rules written down twice:
in `engine/world.py`, and again in JavaScript inside `world3d.html`. Two copies
of anything drift apart, and rules that drift would mean the 3D view quietly
telling you a lie about your own game.

`tests/check_engines.py` is what stops that. It plays every game in `games/`
twice, once with each engine, from the same seed and with the same keys pressed
on the same ticks, and demands that every character be in the same square with
the same health on every tick. It fails if you change a rule in one engine and
forget the other; I checked by flipping a single sign in the JavaScript, and it
caught it.

The two can only agree about luck because a seeded world stops using Python's
own `random` — which no JavaScript could reproduce — and uses `engine/rng.py`
instead, a small generator both languages run in exact integer arithmetic.
**Ordinary play is unchanged and still genuinely random**; the seed exists for
the test.

One tile behaves differently in the 3D tab, and it is the one you would want to
be careful about: `open` does nothing there. A browser tab has no way to hand a
URL to an Android app the way `termux-open-url` does, so it says so in the game
rather than pretending. The Python engine still opens things when you play in
the terminal and opening is on.

---

## Every command

Once `python3 spark.py install` has been run, every one of these works as plain
`spark ...` too.

| Command | What it does |
|---|---|
| `python3 spark.py install` | make `spark` work as a command (do this once) |
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
| `python3 spark.py status` | print the Github / Browser / Local / Cloudflare line |
| `python3 spark.py players` | list who is connected, whoever joined first at the top |
| `python3 spark.py export` | rewrite `tiles.json` and `games/index.json` |
| `python3 spark.py push [game ...]` | overwrite games on GitHub with this phone's |
| `python3 spark.py pull [game ...]` | overwrite games here with GitHub's |
| `python3 spark.py games/chase.json` | open the menus with that game already loaded |
| `node tests/store.test.js` | check the editor's save and load logic |
| `node tests/deck.test.js` | check the six buttons and what the box understands |
| `python3 tests/check_docs.py` | check this README still matches the code |
| `python3 tests/check_sync.py` | check the GitHub push/pull logic |
| `python3 tests/check_permissions.py` | check guests cannot exceed their code |
| `python3 tests/check_open.py` | check the remember/open tiles and their fences |
| `python3 tests/check_places.py` | check placeholders: the three faces and the sums |
| `python3 tests/check_undo.py` | check the undo stack behind both brain editors |
| `python3 tests/check_tiles_of_mine.py` | check your own named tiles, and the ways they can be malformed |
| `python3 tests/check_mytiles.py` | check the gate in front of Python tiles, and who may write one |
| `python3 tests/check_multiplayer.py` | check two players share one world |
| `python3 tests/check_engines.py` | check the Python and JavaScript engines still agree |

---

## Where things live

    spark.py             the launcher — every command above goes through it
    index.html           the drag-and-drop editor (served locally or by Pages)
    world3d.html         the 3D view, and a second copy of the rules in JavaScript
    README.md            this guide
    MANUAL.md            controls, requirements, and how to connect things
    CHANGELOG.md         what changed and when
    tiles.json           the tile list, written out for when no server is running
    games/*.json         your games, one file each
    games/index.json     the list of games, for when no server is running
    mytiles/*.py         tiles you wrote yourself, in Python
    mytiles/example.py   one shipped switched off, explaining how to write one
    mytiles/approved.json  which of them THIS device runs (never committed)
    engine/tiles.py      the tile library      <- add new pieces here
    engine/mytiles.py    loads mytiles/, and the gate that decides what runs
    engine/world.py      the grid, the characters, and the rule engine
    engine/brain.py      reading and writing game files
    engine/builder.py    the terminal menus
    engine/tutorial.py   the ten guided lessons
    engine/launcher.py   writes the `spark` command into your bin folders
    engine/runner.py     the keyboard and the drawing
    engine/server.py     serves the editor, reads and writes games/
    engine/status.py     works out the flags, the player count, and the roster
    engine/sync.py       push and pull single games to and from GitHub
    engine/live.py       the shared world: invite codes, roles, connected people
    engine/tunnel.py     finds and runs cloudflared or ngrok for public play
    engine/rng.py        seeded dice, so both engines can roll the same numbers
    tests/store.test.js  17 checks on the editor's save and load logic
    tests/deck.test.js   82 checks: every screen builds, and what the box understands
    tests/check_docs.py  fails if this README has drifted from the code
    tests/check_sync.py  checks the GitHub push/pull logic, without the network
    tests/check_permissions.py  checks a guest can only do what their code allows
    tests/check_multiplayer.py  two players in one world, over real HTTP
    tests/check_open.py  checks remember/open, and that a guest cannot launch apps
    tests/check_places.py       checks the placeholder tiles, their sums and their edges
    tests/check_undo.py         checks the undo stack both brain editors keep
    tests/check_tiles_of_mine.py  checks named tiles, nesting, and self-reference
    tests/check_mytiles.py      checks the approval gate, and that a guest cannot write code
    tests/check_engines.py      plays every game twice, once per engine, and compares
    tests/engine_trace.js       runs the JavaScript engine from a terminal, for that test

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
  "tiles": [
    {
      "name": "hunt",
      "when": [ { "tile": "see", "args": { "kind": "apple", "range": 6 } } ],
      "do":   [ { "tile": "move", "args": { "dir": "toward it" } } ]
    }
  ],
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

**Spark says "Opening your browser now" and nothing opens.**
There is probably no browser installed. Spark asks Android to open the address
and is not told whether anything answered, so it says the same thing either way.
Check with:

    pm query-activities --user 0 -a android.intent.action.VIEW -d https://example.com

`No activities found` means nothing on the phone opens web links — install a
browser, or reach Spark from another device with `spark host` and the wifi
address it prints. The same answer explains an `open` tile that appears to do
nothing.

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
