# Spark manual — requirements, controls, commands, connecting

The short guide is [README.md](README.md). The history is
[CHANGELOG.md](CHANGELOG.md). This file is the exact reference: what Spark
needs, every button and key, every command, and step-by-step instructions for
turning on the browser interface and GitHub.

## Contents

- [The tutorial](#the-tutorial)
- [System requirements](#system-requirements)
- [Controls: the deck (what the browser opens on)](#controls-the-deck-what-the-browser-opens-on)
- [Controls: playing a game](#controls-playing-a-game)
- [Controls: the terminal menus](#controls-the-terminal-menus)
- [Controls: the browser editor](#controls-the-browser-editor)
- [Controls: the 3D view](#controls-the-3d-view)
- [Placeholders: the exact rules](#placeholders-the-exact-rules)
- [Targets: the exact rules](#targets-the-exact-rules)
- [Tiles you write in Python: the exact rules](#tiles-you-write-in-python-the-exact-rules)
- [Every command](#every-command)
- [Connecting the browser interface](#connecting-the-browser-interface)
- [Connecting another person: live play](#connecting-another-person-live-play)
- [Connecting GitHub](#connecting-github)
- [Moving games between phone and GitHub](#moving-games-between-phone-and-github)
- [Renaming a game](#renaming-a-game)
- [What each of the four connections gives you](#what-each-of-the-four-connections-gives-you)

---

## The tutorial

    cd ~/spark
    python3 spark.py tutorial

Or pick **learn how** from the main menu. It needs nothing but Termux and
Python — no browser, no wifi, no GitHub account. Everything happens on the
phone.

Ten lessons, about ten minutes:

| # | Lesson | What you end up with |
|---|---|---|
| 1 | What a game is here | the WHEN / DO idea |
| 2 | Your character | a hero, drawn how you like |
| 3 | Making it move | four rows wired to the arrow keys |
| 4 | Something to collect | five apples |
| 5 | Picking them up | a scoring row with three DO tiles |
| 6 | The most important word: it | why tiles connect at all |
| 7 | Winning | an ending |
| 8 | An enemy | a bug that chases you |
| 9 | Getting hurt | a chase with consequences |
| 10 | It is yours now | the game saved under your own name |

How it works:

- **You choose the tiles.** Each lesson asks which tile does the job, from
  three plausible options. A wrong answer is explained and you try again —
  nothing is lost and nothing is scored.
- **You play as you go.** At four points it offers to run what you have built
  so far. Press `q` to come back. Answer `n` to skip.
- **It leaves you a real game.** At the end you name it and it is saved into
  `games/` like any other, openable in the menus or the drag-and-drop editor.
- **Stopping.** Ctrl-C leaves at any point. Nothing is saved until lesson 10,
  so starting again is no loss.

Run it as many times as you like — give the game a different name each time and
they all keep.

## System requirements

**Needed:**

| Thing | Version | Notes |
|---|---|---|
| Android with Termux | any recent | Spark lives in Termux's home folder |
| Python | 3.9 or newer | this phone has 3.13 in Termux and 3.13 in PRoot; both work |
| A terminal at least 34 columns wide and 20 rows tall | | the default 80×24 is plenty |

Nothing to install beyond Python. Spark uses only what comes with it — no pip,
no packages, no internet needed to run.

**Optional:**

| Thing | For what | If missing |
|---|---|---|
| Any browser | the drag-and-drop editor, and joining a shared game | the terminal menus do everything the browser does, except joining someone else's world |
| A wifi network you and your friend are both on | live multiplayer | see the tunnel row below |
| `cloudflared` or `ngrok` | live multiplayer with someone far away | wifi play still works; Spark tells you if neither is installed. cloudflared **is** installed on this phone |
| `termux-api` package + Termux:API app | making `spark.py edit` open the browser for you | it prints the address for you to open yourself |
| `git` and `gh` | putting Spark on GitHub | everything local still works |
| `node` | running `tests/store.test.js` | the other test, `check_docs.py`, is Python |

**Disk:** under 200 KB, plus a few KB per game.

**Where it lives:** `/data/data/com.termux/files/home/spark`. From Termux that
is `~/spark`. Inside the PRoot Linux distro `~` means `/root`, so use the full
path there.

**The `spark` command.** Run `python3 spark.py install` once and a small script
is written into Termux's `bin` folder (and into `/usr/local/bin` inside PRoot,
which needs a different first line because Android has no `/bin/sh`). After
that, typing `spark` anywhere starts it, and `spark edit`, `spark tutorial` and
the rest all work. The script only finds Spark, picks whichever Python is
installed, and hands over — if you ever move the spark folder, run install
again.

---

## Controls: playing a game

While a game is running (`spark.py play ...`, or **play it** in the menus):

| Key | Does |
|---|---|
| ↑ ↓ ← → | whatever the character's brain says for that key |
| space | usually shoot — again, whatever the brain says |
| w a s d, e, f, r, m, 1, 2 | available as tiles, if you build rows that use them |
| `/` | a command line — see below |
| `q` | quit back to the menu |
| Ctrl-C | quit |

Keys are not hard-wired. `WHEN key up is pressed DO move up` is a brain row you
built; delete it and the up arrow stops doing anything. The demo game wires the
arrows and space for you.

The display shows the world, then `score`, `health`, `tick`, and your own
`pos` (x,y) right under the map, then the most recent **say** message.

**`/`** hands the terminal back to a normal, cooked text line — a real
text box, backspace and all, exactly like typing anywhere else in this
app — instead of gameplay's usual one-key-at-a-time reading. Nothing
you type there ever reaches a game's own `WHEN key` rows; it's
swallowed before any of that runs. Type a command, see its result on
its own screen — a second view, distinct from the running world — then
type the next one right there, however many in a row, with no need to
press `/` again each time; a **blank line** (or Ctrl-D) is what
actually closes chat and goes back to the running game. `/quit` typed
mid-chat leaves the whole game outright instead, the same as pressing
`q` would.

`/help` shows the game's own "how to play," if it wrote one into its
`help` field (`games/outpost.json` does), then the full command
reference, grouped by type. `/help commands` shows just that
reference on its own — add `description` too (`/help commands
description`) for what each one does; bare `/help commands` is names
and syntax only. An unrecognised command says so rather than doing
nothing.

Four commands act on an exact spot instead of making you walk there
and touch it first — the same one square `touch` itself always means,
so none of these reach across the map: `/mine <x> <y>` gathers ore the
same as standing there does over time; `/attack <x> <y>` hits a bandit
there for the same damage ordinary contact does; `/recruit <x> <y>`
recruits whatever's bare there — a companion, or a worker/soldier
you'd dismissed earlier, which the ordinary `e` key can't reach at all
since it only ever touches companions; `/dismiss <x> <y>` releases
whatever of yours is there, worker/soldier included, which the
ordinary `r` key can't do either for the same reason.

`/units` lists everything you own or possess — the hero, every
recruited companion/worker/soldier, every wall and turret you've
built — each with where it is, and its name if you've given it one.
`/name <x> <y> <new name>` gives whatever's yours at that exact spot a
name, which is what shows in `/units` from then on instead of its bare
kind; unlike the four above, naming isn't range-limited — it's
bookkeeping, not a physical act.

`/list` is `/units` widened to the whole map — every entity alive
anywhere, yours or not (bandits, unrecruited companions, all of it),
each with its own kind, position, health, who's leading it if
anyone is, and what it's carrying if anything — a full inspector for
the workspace, not just your own roster.

`/mine`/`/attack`/`/recruit`/`/dismiss`/`/units`/`/list`/`/name`
results are kept, not just shown once — a real log, paginated 10 to a
page. `/log [n]` shows one page (the latest if you leave the number
off), titled by its own page number; `/forget <n>` deletes a page for
good, and later pages shift down and renumber to fill the gap.

---

## Controls: the terminal menus

A big **SPARK** title screen, one option highlighted at a time — a game menu,
not a numbered list, on any real terminal:

| Key | Does |
|---|---|
| ↑ ↓ | move the highlight |
| enter | pick the highlighted option |
| a digit, 1–9 | jump straight to that option, no arrows needed |
| `0`, or Escape | go back, or quit at the title screen |
| `b` | open the drag-and-drop editor |
| `w` | who is connected |
| enter on a question | accept the `[default]` shown in brackets |
| Ctrl-C | leave Spark |

**Wherever that cannot work** — input piped in from a script, output piped to
a file, an old or unusual terminal — every menu falls back on its own to a
plain numbered list instead: type the number, press enter. Typing `browser`
(or just `b`) still opens the drag-and-drop editor there, and `players` (or
`w`) still lists who is connected, both at any prompt. Nothing about Spark
needs a real interactive terminal to run; the big-picture menu is purely a
nicer way to use one when you have it.

**`SPARK_PLAIN=1`** asks for the plain numbered list even on a terminal that
would otherwise get the big-picture one — for a terminal that answers
`isatty()` with yes but does not actually handle this cleanly (some SSH
clients, some IDE terminal panes), or simply a preference for typing
numbers.

Opening the browser editor (`b`, or `browser`) starts the editor server next
to the menus and opens your browser at it. You keep both: the menus stay where
they were, and both editors read and write the same `games/` folder. They do
not watch each other, so after saving in one, re-open the game in the other to
see the change. The server stops when you leave Spark.

The screens, in order of depth:

1. **Title screen** — with nothing open: *learn how* (the tutorial), new game,
   open a game. With a game open: play it, editor, new game, open a game — a
   game menu first, an editor second, the way play and options stay apart in
   any game.
2. **Editor** — one tap (or digit) in from the title screen, with a game open:
   characters and their brains, your own tiles, world settings, save, rename,
   send to GitHub, invite someone to play.
3. **Characters** — add a character, or pick one to edit.
4. **One character** — its brain, its frames, its letter, colour, health, how
   many start, player or prop, solid or walk-through, delete.
5. **Its brain** — the list of `WHEN ... DO ...` rows: add, change, delete, move
   a row up.
6. **One row** — add or remove WHEN tiles and DO tiles.
7. **One tile** — answer its questions, one per screen.
8. **Its frames** — a multi-cell ASCII sprite: add a frame, or pick one to
   edit; remove one. Only the terminal engine draws these — see below.
9. **One frame** — a list of pixels: add one (a grid position relative to the
   character's own spot, a letter, a colour), or remove one. A small
   coloured preview of the frame so far shows above the list.

A character with frames draws every one of that frame's own pixels instead
of its plain single letter — a real multi-cell ASCII sprite. `set_frame`
and `next_frame` (both engines) switch which frame is currently showing;
pair `next_frame` with `timer` for a real animation loop, e.g. `WHEN timer
10 DO next_frame`. `games/outpost.json`'s own turret does exactly that —
its scanning light blinks silver/yellow every 10 ticks. Only the terminal
engine actually draws frames; world3d.html carries the field (so a
save/load round trip never loses it, and `set_frame`/`next_frame` still
run identically in both engines) but has its own 3D shape/parts system
already and doesn't interpret this one.

---

## Controls: the deck (what the browser opens on)

A title screen, then an editor — a game menu first, filling the screen.

| Button | Opens |
|---|---|
| play | the game — live through Termux, or the 3D view with no server |
| continue | reopens whichever game you last had open, then plays it |
| new game | start again, blank |
| editor | six more buttons, everything that changes the game |

**Editor**, one tap in:

| Button | Opens |
|---|---|
| edit | open, new, rename, world, share, github |
| characters | a button per character, then a button per setting |
| brain | a button per row, then a button per tile in it |
| tiles | your folded tiles, and the Python editor |
| save | writes the game down. No screen: it saves and says where |
| 3d world | a fresh, empty 3D world, ready to move around in |

**Every screen is the same formation.** There is no long page anywhere. What
used to be a panel is now a screen of buttons:

| Screen | Its buttons |
|---|---|
| title | play · continue · new game · editor |
| editor | edit · characters · brain · tiles · save · 3d world |
| edit | open · new · rename · world · share · github |
| open | one per saved game |
| world | width · height · speed · edges |
| characters | one per character · + new |
| one character | name · drawn as · colour · health · how many · role · solid · brain · delete |
| brain | one per row · + row · undo |
| one row | one per tile in it · + WHEN · + DO · ⊞ fold · delete row |
| add a tile | your own tiles, then all thirty-five — **this is what the scrolling is for** |
| your tiles | one per folded tile (tap to delete) · fold a row · python |

`‹` beside the box goes back one screen; `/home` returns to the title screen.

**The two things that are not buttons**, because they cannot be: a tile's
settings, and the Python text editor. Both open over the deck with their own
back button.

### The formation

Eight cells, up to six of them buttons — the title screen only fills four and
leaves the rest of the grid empty, the editor and most other screens use the
full six.

| Held | Grid | Buttons | Box |
|---|---|---|---|
| upright | 2 across, 4 down | the first 3 rows | the last row, across both columns |
| sideways | 4 across, 2 down | the first 3 columns | the 4th column |

Buttons stretch to fill the screen; the deck itself never scrolls. Should there
ever be more than six, the **button area** scrolls up and down only, keeping the
same columns.

`/swap side chat` moves the box to the other side when the phone is sideways,
and remembers which side you left it on. `/swap side chat left` and
`... right` name a side outright.

### The box

| Typed | What happens |
|---|---|
| `/help` | lists all of this on screen |
| `/play` `/continue` `/editor` `/edit` `/characters` `/brain` `/tiles` `/save` | the same as the buttons |
| `/pin "note"` | keeps a note. Quotes are optional: `/pin feed the bug` works |
| `/pins` | lists them, numbered |
| `/unpin 2` | removes number 2 |
| `/back` | up one screen — the same as `‹` |
| `/home` | back to the title screen |
| `/swap side chat` | the box changes sides when sideways |
| `/who` | who is connected |
| `/clear` | empties the log |
| anything else | said to everyone else in your world |

An unrecognised `/word` says so and is **not** sent as chat, so a mistyped
command never gets broadcast.

Notes live in this browser (`localStorage`), not in the game, so they follow the
device rather than the game file.

### Chat

| | |
|---|---|
| Who may talk | anyone who can see the world — **owner, edit, play and watch** |
| Who may not | somebody with no valid code: 403 |
| One line | trimmed of extra spaces, cut at **300** characters |
| How many kept | the last **40**, in memory only |
| Where it is stored | nowhere. It never reaches the disk and does not survive a restart |
| How it arrives | with the world snapshot, so there is no extra polling |

A watcher can talk because somebody who may only look is still a person in the
room, and saying something changes nothing about the world.

Chat needs the server running. Opened from GitHub Pages with no server, the box
still does every `/command`, and says so if you try to talk.

---

## Controls: the browser editor

| Gesture | Does |
|---|---|
| **tap** a tile in the bottom palette | adds it to the highlighted row |
| **tap** the WHEN / DO tabs | chooses which half of the row tiles land in |
| **tap** a row | highlights it, so tiles land there |
| **tap** a placed tile | opens its settings, with a **remove tile** button |
| **drag** a placed tile | moves it to another row |
| **drag** a placed tile onto the red bar | deletes it |
| **↑** on a row | moves that row up |
| **✕** on a row | deletes that row |
| **+ add a row** | new empty row at the bottom |
| **+ character** | new character |
| **save** | writes the game (see below for where) |
| **▶ 3D** | opens this world in 3D, in a second tab |
| **⚙** | GitHub settings — only shown when there is no local server |
| **👥** | share and multiplayer — only shown when there is one |

The top of the editor is two rows: a thin one with the game you are on and the
two icon buttons, and under it a row of full-width buttons — **▶ 3D**, **save**,
**new** — sized for a thumb rather than a mouse pointer. Everything you press
anywhere in the editor is at least 48 pixels tall for the same reason.

In a shared game, the on-screen pad replaces the editor:

| Button | Does |
|---|---|
| ▲ ▼ ◀ ▶ | the direction keys, for whoever your character is |
| ● | the space key, usually shoot |
| **leave the game** | back to the editor, or to the join screen if you are a guest |

A real keyboard works too — arrows, space, and letter keys all get sent.

Tap **world settings** to open width, height, speed, edge wrapping, and the
**rename this game** button.

---

## Controls: the 3D view

Press **▶ 3D** in the browser editor. The world opens in a second tab as a board
of blocks, with each character's glyph floating over its own block.

| Gesture | Does |
|---|---|
| **drag** one finger | turns the camera around the board |
| **pinch** two fingers | moves the camera closer or further away |
| **scroll wheel** | the same, with a mouse |
| ▲ ▼ ◀ ▶ | the direction keys, for your character |
| ● (space) | usually shoot |
| ⟲ (`e`) | cycle the touched object's shape — cube, sphere, cone, cylinder, pyramid, wedge, octahedron |
| + (`f`) | resize the touched object (uniformly — see 🎯 below for width/height/depth apart) |
| ⤒ (`w`) | fly up — only while flying, see `d` below |
| ⤓ (`s`) | fly down — only while flying |
| ▦ (`a`) | add a 3D object where you stand, see-through until pressed again to confirm it |
| `d` | toggle walking (grounded, `w`/`s` do nothing) ↔ flying |
| 🗑 | arm removal — the *next* object touched is deleted, not whatever was already selected; drawer bubbles marked `locked` (the built-in ones) can never be picked this way |
| 🎨 | Build mode: a searchable, alphabetical palette of every kind the game defines, to place where you stand — or open the Mesh Creator to design a new multi-part shape and add it to that palette. Local play only |
| 🎯 | the Object Inspector: recolour (nineteen colours), cycle the shape (seven of them), resize uniformly or stretch width/height/depth independently ("reset stretch to size" undoes just the stretch), relocate, duplicate, or delete whatever you're touching (or a pending ghost from ▦, before it's even confirmed). **Tap anything in the world to select it directly**, without touching it on the ground first — a glowing ring marks the current selection. Local play only |
| 🧬 | Merge: arms it (the bubble itself pulses while armed, same idea as 🗑's own pulse), then tap several objects (each gets its own green ring) and tap 🧬 again to combine all of them into one new placeable kind — you're asked for a name and a glyph, the same as saving from the Mesh Creator. Any part that ends up sitting entirely inside another is dropped from the result; parts that only partly overlap keep their full geometry. Tapping 🧬 again with fewer than two queued cancels instead, and so does closing the drawer while it's armed. Local play only |
| 📦 | Inventory — a plain, read-only list of what you're carrying (from harvesting, or `give_item`). Nothing to do with the Backpack below; that's a dev tool, this is a game one. Local play only |
| **restart** | starts the game again from the beginning (local play only) |
| **recentre** | puts the camera back where it started |
| **save** / **save as new** | quick-saves back to the file this world came from, or always asks for a new name |
| **⛶** | fullscreen |
| **🎒** | Backpack, a small virtual file system |
| **⚙** | Properties — grid-lock status, move speed, an opt-in minimap, and a clock, all driven by the world itself |
| **💬** | Chat — the exact same conversation the browser editor's own box has, one per hosted game; anything typed without a leading `/` is said to the others, which only means anything in `LIVE` mode — there's nobody else to talk to in a local, single-tab copy. **Always open** — on from the moment a game loads, with no way to close it; tapping `💬` just (re-)focuses the input. Sending a message with Enter never closes it, of course. `/who` and `/clear` work either way. `/help` shows the game's own "how to play" first, if it has one (`games/outpost.json` does), then the full command reference grouped by type; `/help commands` (add `description` too) shows just that reference on its own. `/mine`/`/attack`/`/recruit`/`/dismiss x y` act on an exact spot the same as touching it would — gather ore, hit a bandit, recruit or release a bare/led companion/worker/soldier — one square away at most; `/units` lists everything you own or possess with its location, `/list` widens that to every entity in the world whether it's yours or not (kind, position, health, leader, inventory), `/name x y <new name>` renames whatever's yours there. All local-play only like Build/Harvest above. Nothing here is ever silently lost — the whole log is kept, titled into numbered pages of 10; `/log n` scrolls to one, `/forget n` removes one for good, its own number never reused even after |
| **✎** | the button editor — select, drag, resize, and fade any button here, including the drawer's own |
| **run here** / **go live** | switches between the running game and this tab's own engine |

**Harvest** is the one panel here that isn't opened from anywhere — it
appears on its own, above the pads, the moment you're standing next to
something `harvestable` (set with that tile, on any kind), naming
whichever one(s) are within reach. Tap one to start a timed harvest: the
panel switches to a countdown, ending in the target flashing the
configured number of times and then vanishing while the item lands in
your Inventory (📦, above). Walking out of reach mid-harvest cancels it —
no partial reward. `games/Game 008008.json`'s pink cones are a working
example: `harvestable`, giving ten pink metal for five seconds' wait and
four flashes.

**Backpack, Properties, Mesh Creator, Build, and the Object Inspector are
all the same shape now** — up to six large buttons filling most of the
screen, with a box off to the side for whatever those buttons don't cover,
the exact same "six panel buttons besides a box" formation the browser
editor's own deck uses (see its own "How it sits on the screen" above).
Backpack used to be a deliberate Windows-Explorer-styled exception to the
game's own gray/light-blue look; folded into the same shell and theme as
the rest on request, so nothing here stands apart from the rest by look
any more, only the Backpack's icons-and-folders idea of what a button
*does* stays its own thing. Where a screen has more to say than six
buttons can hold — nineteen colours, seven shapes, every kind Build can
place — those become the buttons themselves, scrolling, the same
"however many there are" idea already used for the browser editor's own
big lists (the tile palette, there). Continuous controls that a button
grid genuinely cannot replace — the Mesh Creator's exact part
position/size, the Inspector's exact resize/stretch/position, Properties'
exact move speed, Build's search box, Backpack's file grid — live in the
box instead, next to a handful of quick-jump buttons for the common
cases, so nothing about the fine control here was lost, only relocated:
- **Object Inspector** taps into Colour, Shape, Resize, Stretch, and Move
  as their own pages (a `‹` appears next to the title to back out of
  one), plus a Duplicate button on the top page; Delete stays a small
  icon by the title, since it is rare and destructive rather than
  something to tap into by accident. Resize offers 50/75/100/150/200/300%
  quick buttons with the exact typed value still in the box; Stretch
  offers ±25 nudges per axis with the same three sliders as before,
  moved into the box; Move offers ±1 nudges per axis (±1 altitude too)
  with the same typed x/y/z fields.
- **Mesh Creator** taps into Part Colour and Part Shape as their own
  pages, the same way; Add/Duplicate/Delete Part and Save as a new kind
  are buttons on the top page. The live preview canvas stays visible on
  every page rather than being rebuilt each time — it is its own WebGL
  context, worth keeping alive rather than tearing down and recreating on
  every tap. The part list, the exact dx/dy/dz/sx/sy/sz fields for
  whichever part is selected, and loading/deleting a previously-saved
  mesh live in the box.
- **Build** turns every placeable kind into one big button itself
  (scrolling, same as the tile palette); the search box that filters them
  lives in the box, and 🧩 (open the Mesh Creator) moves next to the
  title as a small icon.
- **Backpack** turns Up/New folder/New item/Delete into the four big
  buttons; the breadcrumb and the file grid live in the box.
- **Properties** turns grid-lock and minimap into toggle buttons and move
  speed into ±1/±5 quick-jump buttons; the world clock and the exact
  typed speed live in the box.

The **compass**, a meter across the top of the screen rather than a dial,
scrolls sideways as the camera turns so the current heading always sits
under the fixed centre marker — this world's own idea of "north," not a
real one. It lives inside the top bar itself (below the title and both
rows of buttons), so it always sits under whatever the bar's own real
height happens to be on your phone rather than at a fixed distance from
the top that could land on top of the bar's own buttons. The **quickbar**
is seven empty, always-visible bubble slots with no drawer to open first,
there to have something assigned to them later.

"Local play only" above means the feature edits the live JavaScript world
directly, in this tab's own copy of the game — it has no effect, and does
not appear to make sense, while watching a `LIVE` server-hosted game (see
the badge table below), since there is no local copy to edit.

**The world always fills the whole screen** — the top bar, the pad, the
button drawer, the compass, and the quickbar all float over it as
translucent panels rather than splitting the page into a world region and
a controls region, in either orientation. The empty space around the pad
still passes a swipe straight through to the camera underneath it.

**One combined pad**, nine keys, three by three — briefly split into two
separate thumb-zone pads, merged back into one block on request. Read
left to right, top to bottom: ⟲ (flip shape), ● (space), + (resize) along
the top; ⤓ (fly down), ▲ (up), ⤒ (fly up) in the middle, so the two fly
keys flank the movement up-arrow directly below space; ◀ (left), ▼ (down),
▶ (right) along the bottom. Sized **as a share of your own screen** rather
than in fixed pixels, capped in landscape so it cannot grow tall enough to
reach the top bar, and capped altogether so a tablet does not hand you a
pad the size of a dinner plate. Nothing is measured against any
particular phone, so a screen I have never seen gets a pad in the same
proportion.

Every button here — the pad, the top bar, the drawer's own bubbles —
can be dragged to a new spot, resized, and faded from the button editor
(✎), either by touch or by typing an exact position as a decimal percent
of the screen. Anywhere in the world you touch that is not a button turns
the camera. A drag can never leave a button entirely past an edge of the
screen with no way back to it — it always keeps a small margin of itself
reachable, correcting on its own if it ever ends up otherwise. A moved
button's saved position is that percent of the screen, recomputed fresh
against whatever the screen actually is each time — not a fixed distance
from wherever it started, which used to leave a customized button in the
wrong spot after rotating between portrait and landscape, since a couple
of these layouts are genuinely different shapes rather than just smaller
or larger versions of one another.

**Portrait and landscape each keep their own arrangement**, not one
shared between them — customize a button while upright, rotate, and
whatever you'd set up sideways (or the plain default, the first time)
is what's there instead; rotate back and portrait's own arrangement is
exactly as you left it. Nothing extra to do for this — dragging already
saves, same as always, just into whichever orientation you're actually
in at the time. "Reset ALL buttons" clears both; "reset this button"
(singular) only clears the one you're looking at right now.

👁, its own small button at the top right below the bar (not itself
draggable, on purpose — the one control that should never get lost or
hidden), hides every other button and panel on screen for an
unobstructed view of the world; tap it again, same button, to bring
everything back. Doesn't persist — always starts shown again next time.

The button editor's own panel is eight big buttons and a box, the same
shape every other modal in this file uses: **done editing**, **grid
lock**, **pick on screen**, **size −10%**/**+10%**, **reset this
button**, **reset ALL buttons**, and **save layout as…**. The box below
them holds the button-picker list (grouped under a numbered "button
group 001," "002," … heading, the pad, the top bar, the drawer, and the
quickbar each their own, instead of one flat list of everything on the
page at once) and the saved-layouts list.

Tapping a row in the button-picker list opens that button's own **full
page of properties** — its own titlebar with a **‹** back button, the
same sub-page pattern the Object Inspector and Mesh Creator already use
— covering the list while it's open: the precise size/opacity fields,
the exact x/y position (typed or "go to"), the grid size, and "hide this
panel while dragging." **‹**, or the page's own **✓ done** in the
titlebar, closes it back to the picker list without losing the
selection — the dashed outline stays on that button, and tapping the
same row again reopens straight back to its properties.

The panel covers most of the screen, which can get in the way of seeing
exactly where a button lands relative to everything else while dragging
it — "hide this panel while dragging a button," on by default, makes the
panel itself disappear for the length of each drag and come straight
back the moment you let go. ✎ (top right) itself also shows/hides the
panel once you're already editing — tap it any time to close the panel
and see the screen clearly (dragging still works with the panel closed),
then the same button brings it straight back.

**👆 pick on screen** goes further: it hides the panel the same way, but
keeps a small floating readout on screen — a size meter, an opacity box,
and the tapped button's own name — in sync with whatever you tap next,
so checking or nudging several buttons in a row doesn't mean reopening
the full panel each time. ✎, or the readout's own small ✎, brings the
full panel back and leaves this mode.

Actually leaving edit mode — the dashed outlines and all — is "✓ done
editing," which also leaves pick on screen if it was on.

The drawer's own bubbles are a column, tallest on a tall screen — if there
get to be enough of them (built-ins plus whatever you've added with the +
control) that the column would run past the bottom of the screen, it wraps
sideways into a second column instead of letting the bottom ones run off
the edge where you could no longer reach them.

A real keyboard works: arrows, space, and `w a s d e f`.

**The badge in the top corner tells you what you are watching.**

| Badge | Meaning |
|---|---|
| `LIVE` | the real game running in Termux, mirrored as it plays |
| `RUNNING HERE` | this tab is playing the game itself, in the browser |

It picks `LIVE` whenever a Spark server answers, and falls back to
`RUNNING HERE` when none does — including in aeroplane mode, with Termux shut,
or from the GitHub Pages copy. The game travels inside the link after the `#`,
which never leaves the browser, so the 3D tab shows what is on your screen right
now whether or not you have saved it.

If the server disappears while you are watching `LIVE` — you closed Termux, or
the tunnel dropped — the tab does not freeze. It switches itself to
`RUNNING HERE` and carries on from a fresh start of the same game.

### What it needs

WebGL, which every current phone browser has. No library is downloaded, so
nothing here needs the internet, GitHub or Cloudflare. If the browser refuses
WebGL the tab says so plainly and offers you the flat editor instead, rather
than showing a black screen.

**If anything else goes wrong it is written on the screen too**, with a
**reload** button. That is deliberate: Chrome on Android has no console you can
open, so an error with nowhere to go would leave you looking at a black
rectangle with no way to say what happened. Read the message out, or photograph
it — it is enough to find the fault.

### The one thing it will not do

The `open` tile does nothing in the 3D tab. A browser tab cannot hand a URL to
an Android app the way `termux-open-url` can, so instead of pretending, it puts
`cannot open things from a browser tab` on screen. Play in the terminal, with
opening turned on, if a game depends on that tile.

---

## Placeholders: the exact rules

The README explains what a placeholder is and why you would want one. This is
the precise reference: exactly what each box accepts and exactly what comes out.

### The slot

One placeholder is one slot in the world, under a name you invent. It has three
faces at once, and every face exists from the moment the name does:

| Face | Type | Empty means | Written by |
|---|---|---|---|
| name | text | `""` | name `<who>` is "`<text>`" |
| value | one number, decimals allowed | `0` | value `<who>` = ... |
| x, y, z | three numbers, decimals allowed | `0, 0, 0` | vector `<who>` `<axis>` = ... |

- The name is **trimmed and lowercased**: ` Home `, `HOME` and `home` are the
  one slot.
- A **blank** placeholder name is nobody. Tiles given one do nothing.
- Placeholders belong to the **world**, not to a character, so every character
  reads and writes the same ones. There is no private placeholder.
- They start **empty every time a game starts**, exactly like the score. They
  are not saved into the game file.
- **Writing** a placeholder creates it. **Reading** one does not: a name that
  has never been written reads as 0 and leaves nothing behind, so a typo is a
  quiet zero rather than a slot full of rubbish.

### What a box of a sum accepts

Each `=` tile has two boxes with an operation between them. A box is read in
this order, and the first line that fits wins:

| Box contains | Result |
|---|---|
| nothing, or only spaces | `0` |
| `12`, `-3`, `+8` | that whole number |
| `2.7`, `-2.7`, `.5`, `3.` | that number, fraction kept |
| `root <box>` | its square root. `root 9` is `3`. **Below zero there is none, so `0`** |
| `round <box>` | nearest whole number, exact halves going **away from zero** |
| `down <box>` | the whole number at or below it. `down -2.1` is `-3` |
| `up <box>` | the whole number at or above it. `up -2.9` is `-2` |
| `random <box>` | a whole number from `0` to that number minus one. `0` or less gives `0` |
| `my x` `my y` `my health` `my age` `my travelled` | that number about the character running the row |
| `it x` `it y` `it health` `it age` `it travelled` | that number about whoever the WHEN half found; `0` if it found nobody |
| `score` | the score |
| `tick` | how many ticks the game has run |
| `<name>` | the **value** face of that placeholder |
| `<name> x`, `<name> y`, `<name> z` | that axis of that placeholder's **vector** face |
| anything else | `0` |

Boxes are lowercased before reading, so `My X` works.

The five word forms take a box of their own and so nest one level:
`root home x`, `round root 17`, `random my health`. The word must be followed by
something — a bare `root` is `0` — and a word that merely *starts* with one of
them (`rootle 9`) is not a word form.

What a box is **not**: a formula. There is one operation per tile and no
brackets, so `7 divided by 5` cannot go inside a box. To build something longer,
use several tiles in the one row, each writing a placeholder the next one reads:

    DO value q = 7 divided by 5       (1.4)
       value q = down q plus 0        (1)
       value q = q times 5            (5)

### Rounding, exactly

`round` is spelt out rather than handed to either language, because they
disagree and so does everybody's intuition:

| | Spark | Python's `round` | JavaScript's `Math.round` |
|---|---|---|---|
| `round 2.5` | `3` | `2` (nearest even) | `3` |
| `round -2.5` | `-3` | `-2` | `-2` (halves go up) |

Spark sends exact halves **away from zero**, in both engines.

### Dice

`random <box>` rolls the world's own dice — the same source `move random` uses —
so a **seeded** world rolls the same numbers in both engines, and an unseeded one
is real randomness.

| Written | Gives |
|---|---|
| `random 6` | `0` to `5` |
| `random 6` plus `1` | `1` to `6` — ordinary dice |
| `random 0`, `random -3`, `random 0.4` | `0`. Not an error: a sum is not a place a game may fall over |

The number of sides is rounded **down** first, so `random 6.9` is a six-sided
die.

Two things that look like numbers are deliberately **not** numbers here, because
Python and JavaScript disagree about them and a sum must not mean two different
things depending on which engine is running:

| Typed | Python alone would say | JavaScript alone would say | Spark says |
|---|---|---|---|
| `0x10` | error | 16 | `0` |
| `1_0` | 10 | error | `0` |

### The operations

Nine, all taking two boxes and giving one whole number. There is one operation
per tile and no brackets: to build something longer, write several tiles into
the one row, each writing a placeholder the next one reads.

| Word | Result | `7`, `5` | `-7`, `5` | `7`, `0` |
|---|---|---|---|---|
| plus | first + second | `12` | `-2` | `7` |
| minus | first − second | `2` | `-12` | `7` |
| times | first × second | `35` | `-35` | `0` |
| divided by | first ÷ second, **fraction kept** | `1.4` | `-1.4` | `0` |
| remainder | what is left over, taking the sign of the **first** box | `2` | `-2` | `0` |
| to the power of | first multiplied by itself `second` times | `16807` | `-16807` | `1` |
| but no more than | the smaller of the two | `5` | `-7` | `0` |
| but no less than | the larger of the two | `7` | `5` | `7` |
| how far from | the size of the gap, never negative | `2` | `12` | `7` |

An unrecognised word adds, so a game file written by a newer Spark still runs
here rather than refusing to.

**Dividing by zero, and the remainder of zero, are both `0`.** Not an error and
not a stopped game: a row sitting on `always` must not be able to break the
world, so the answer is the least surprising number and play continues.

**The sign trap.** Python and JavaScript disagree about the sign of a
remainder, so Spark defines it itself and neither language's own operator is
used — not even JavaScript's, which happens to agree:

| | Spark | Python alone | JavaScript alone |
|---|---|---|---|
| `-7 remainder 5` | `-2` | `3` | `-2` |
| `7 remainder -5` | `2` | `-3` | `2` |
| `-7 remainder -5` | `-2` | `-2` | `-2` |
| `7.5 remainder 2` | `1.5` | `1.5` | `1.5` |

The leftover always takes the sign of the **left** box — the thing being divided
up.

It is measured against a division cut **toward zero**, which is no longer what
`divided by` does now that it keeps the fraction. So the two reconcile only with
the cut written back in, and only at or above zero, where cutting toward zero
and `down` are the same thing:

    down (first ÷ second) × second  +  (first remainder second)  =  first

Below zero, `down` cuts the other way and the pair does not line up in tiles.

**to the power of**, exactly:

| Case | Result |
|---|---|
| fractional exponent | **rounded** to a whole number first — `2 to the power of 3.6` is `16` |
| exponent below 0 | `0`. A fractional power is what `root` is for |
| exponent 0 | `1`, including `0 to the power of 0` |
| fractional base | fine — `1.5 to the power of 2` is `2.25` |
| result past the fence | the fence, **with the correct sign** — `-10 to the power of 999` is −1,000,000,000 and `-10 to the power of 1000` is +1,000,000,000 |

It is worked out by multiplying step by step and clamping at each step, never
by asking either language for a power — `10 to the power of 999` would build a
thousand-digit number in Python and an infinity in JavaScript, and both engines
have to arrive at the same fenced answer instead. Fractional exponents are left
out for the same reason: `2 ** 0.5` risks the two engines differing in the last
bit, and `root` gives that answer exactly on both.

### The fence

Every number a placeholder holds runs from **−1,000,000,000** to
**1,000,000,000**. Anything larger, in a box or as the result of a sum, stops at
the fence rather than wrapping or erroring. Fractions are not fenced — they are
as fine as the numbers themselves go.

This is not tidiness. `world3d.html` carries a second copy of the rules in
JavaScript. Both languages use the very same 64-bit floating-point numbers, so
`+`, `−`, `×`, `÷` and square root are bit-for-bit identical on each — but only
while values stay in a sane range, since above about 9,000,000,000,000,000 they
stop being exact. Clamping first is what lets
`python3 tests/check_engines.py` prove the two engines compute every sum
identically.

Nothing that comes out of a sum can ever be infinite or not-a-number. That is
enforced rather than hoped for: JSON can write neither, so one loose in a
placeholder would make a saved game or a live snapshot unreadable instead of
merely wrong.

### The vector tiles

| Tile | Exactly what it does |
|---|---|
| copy my place into vector `<who>` | writes my x and my y into the vector. **z is left alone** |
| jump to vector `<who>` | stands me on square (x, y). Obeys the edges: a vector pointing off the board does nothing. Ignores solidity, like the *jump to a random empty square* tile |
| move by vector `<who>` | one step of (x, y), through the normal movement rules — walls block it, wrapping edges wrap it. Also sets my facing |

**Squares are whole even though vectors are not.** Both movement tiles
**round** the vector — nearest square, halves away from zero — so `3.4` lands on
`3` and `3.6` on `4`. A vector of `0.4` moves you nowhere; one of `0.6` moves
you a full square.

To travel slower than a square a tick, keep the fraction in a placeholder and
move by its whole part, putting the remainder back:

    WHEN always  DO value creep = creep plus 0.25
                    vector step x = down creep plus 0
                    value creep = creep remainder 1

`z` is stored and read back but never travelled. The world is a flat grid; z is
there so a vector can carry a third number.

### The two WHEN tiles

| Tile | True when |
|---|---|
| placeholder `<who>` has `<face>` `<test>` `<box>` | the chosen face — **value**, **x**, **y** or **z** — is **at least** / **at most** / **exactly** what the box says. An unwritten placeholder is 0 on every face |
| placeholder `<who>` is named "`<text>`" | the **name** face is exactly that text. An unwritten placeholder is named nothing, so this is false |

The right-hand side of the first is a **whole box**, not merely a number, so it
compares two moving things as readily as one against a constant:

    WHEN placeholder gap has value at least my health
    WHEN placeholder loot has value at least root 100

`it` is what the sensors *produce*, so there is none available while a WHEN tile
is being read: `it x` in that box is `0`. Neither tile produces an "it" either,
so neither can feed *move toward it*.

---

## Targets: the exact rules

A placeholder's vector face is three numbers, frozen the instant you write
them. A **target** is the other kind of slot: it holds the actual character
(or, failing that, a plain spot), and reading it back hands you that same
live thing — which is what lets it keep following something that moves.

- **mark `<name>` as a target** saves whatever `it` is when the tile runs.
  If an earlier WHEN tile in the same row found an object or a character,
  that is what gets saved — the real one, not a copy. If there was no `it` at
  all, your own square right now is saved instead, frozen, as a location.
- **I recall the target `<name>`** hands back whatever was saved, *as* `it` —
  so `move toward it`, `face toward it`, `shoot toward it`, and anything else
  that reads `it` all work with it unchanged, exactly as if a `see` or
  `touch` tile had found it moments ago.
- A target that was an object or character keeps being read back **live**: if
  it moves, `recall the target` sees the new position; if it dies, `recall
  the target` reads False from then on, the same as never having marked one.
  A target that was a location never changes — it is not a Thing that can die
  or move, just a frozen square.
- Targets belong to the **world**, not to a character, the same as
  placeholders — every character reads and writes the same ones. They start
  empty every game and are not saved into the game file.
- A **blank** name is refused; nothing is saved.
- Marking under a name that already holds something replaces it outright.

---

## Tiles you write in Python: the exact rules

The README explains what these are and why the gate exists. This is the precise
reference.

### Where they live

| Path | What it is |
|---|---|
| `mytiles/<name>.py` | one file, holding one or more tiles |
| `mytiles/approved.json` | which files **this device** runs. **Never committed** — it is in `.gitignore` |
| `mytiles/example.py` | shipped with Spark, switched **off**, explaining how to write one |

Names may hold letters, digits, spaces, dashes and underscores, up to 60
characters. No dots, so no `..` and no pretending to be another kind of file;
the `.py` is added for you. A name outside that is refused, in the editor and
over HTTP alike.

### Who may write one

| Role | Read them | Write / switch on / delete | Edit games |
|---|---|---|---|
| **owner** — at the phone, or holding the printed key | yes | yes | yes |
| **edit** guest | **no** | **no** | yes |
| **play** / **watch** guest | no | no | no |

An `edit` code is trusted with your games and not with your phone. Writing
Python means running Python here, which would step past every other fence in
Spark — including the one that stops a guest making your phone open a link.

### When a file runs

A file is run only when `approved.json` holds a fingerprint for it that matches
the file's **current** text, exactly.

| Situation | Loads? | The editor says |
|---|---|---|
| you saved it in the browser | yes | *switched on* |
| it arrived from GitHub, another player, or the SD card | **no** | *not switched on* |
| you read it and pressed *switch on* | yes | *switched on* |
| it changed after you approved it | **no** | *changed since you approved it* |
| you pressed *switch off* | no | *not switched on* |

Saving from the browser approves it in the same movement: you are the owner and
writing it is the act of consenting to it.

### When a file is broken

| What happens | Result |
|---|---|
| it will not compile | skipped; the error is shown in the editor; every other file still loads |
| it throws while loading | skipped; **anything it managed to register first is taken back off**, so a half-run file leaves nothing behind |
| it is saved again | its old tiles come off the menus before the new ones go on |
| it is deleted | its tiles come off, and its approval is forgotten |

A broken tile can never stop Spark starting. If it could, you would have no way
back into the editor to fix it.

### What a tile file gets

Already in scope, with no imports:

| Name | What it is |
|---|---|
| `sensor(id, label, *params)` | the decorator for a WHEN tile |
| `action(id, label, *params)` | the decorator for a DO tile |
| `Param(name, prompt, kind, choices, default)` | one question the editor asks. `kind` is `text`, `int`, `choice` or `kind` |
| `tiles` | the tile module itself, for its helpers |

A sensor is called `(obj, world, a)` and returns true or false — or a character,
which becomes the row's `it`. An action is called `(obj, world, a, it)`.

| Argument | What it is |
|---|---|
| `obj` | the character running the row — `.x`, `.y`, `.health`, `.facing`, `.age` |
| `world` | everything else — `.score`, `.tick`, `.rng`, `.things`, `.try_move(...)` |
| `a` | this tile's own settings, keyed by your `Param` names |
| `it` | whoever the WHEN half found, or `None` |

Anything you hang on `obj` yourself is **per character**, where a placeholder is
shared by the whole world — that is how `example.py` gives each pacing character
its own direction.

### The one real limit

These run in the Python engine, in Termux. `world3d.html` carries a second
engine in JavaScript for when nothing is reachable, and it cannot run Python.

| Where the game is played | Do your Python tiles fire? |
|---|---|
| `spark.py play`, and the terminal menus | yes |
| the browser, with the server running (`LIVE`) | yes — the server is running the world |
| the 3D view with no server (`RUNNING HERE`) | **no** |
| GitHub Pages, with no Termux anywhere | **no** |

For a tile of your own that works everywhere, fold one out of existing tiles
instead — that needs no code, no approval, and travels with the game.

---

## Every command

Run these from inside the spark folder (`cd ~/spark` in Termux) — or from
anywhere, as plain `spark ...`, once you have run the install command.

| Command | Does |
|---|---|
| `python3 spark.py install` | write the `spark` and `update` commands, and `/update` where it can |
| `/update spark` | pull the newest Spark from GitHub (PRoot distro) |
| `update spark` | the same, and works in Termux proper too |
| `python3 spark.py update` | the same, with no install needed |
| `python3 spark.py update --check` | say what an update would bring, then stop |
| `python3 spark.py tutorial` | ten guided lessons, offline, building a real game |
| `python3 spark.py` | open the terminal menus |
| `python3 spark.py games/chase.json` | open the menus with that game loaded |
| `python3 spark.py edit` | start the browser editor on port 8765 |
| `python3 spark.py edit 9000` | start it on a port you pick |
| `python3 spark.py host` | the editor, open to others on this wifi |
| `python3 spark.py host 9000` | same, on a port you pick |
| `python3 spark.py host --public` | ...and to anyone, through a tunnel |
| `python3 spark.py people` | list who can reach your GitHub repo |
| `python3 spark.py people NAME` | let that GitHub user edit your games |
| `python3 spark.py people NAME --player` | let them read it only |
| `python3 spark.py play games/chase.json` | play a game right now |
| `python3 spark.py play games/chase.json 200` | run 200 ticks with no display, for testing |
| `python3 spark.py status` | print the Github / Browser / Local / Cloudflare line |
| `python3 spark.py players` | list who is connected, first to join at the top |
| `python3 spark.py export` | rewrite `tiles.json` and `games/index.json` |
| `python3 spark.py push` | overwrite **every** game on GitHub with this phone's |
| `python3 spark.py push chase` | overwrite just that one game on GitHub |
| `python3 spark.py push chase maze` | overwrite those two |
| `python3 spark.py pull` | overwrite every game here with GitHub's |
| `python3 spark.py pull chase` | overwrite just that one here |
| `python3 tests/check_docs.py` | check the README still matches the code |
| `python3 tests/check_sync.py` | check the GitHub push/pull logic, offline |
| `python3 tests/check_places.py` | check the placeholder tiles and their sums |
| `python3 tests/check_undo.py` | check the undo stack both brain editors keep |
| `python3 tests/check_tiles_of_mine.py` | check your own named tiles and their edges |
| `python3 tests/check_mytiles.py` | check the gate in front of Python tiles |
| `python3 tests/check_update.py` | check updating, in throwaway clones |
| `python3 tests/check_engines.py` | check both engines still play games identically |
| `python3 tests/check_menu.py` | check the terminal's big-picture menu and its fallback |
| `node tests/store.test.js` | check the editor's save and load logic |
| `node tests/deck.test.js` | check the deck's screens and the box you type in |

---

## Connecting the browser interface

**Step 1.** In Termux:

    cd ~/spark
    python3 spark.py edit

**Step 2.** It prints an address, normally `http://127.0.0.1:8765`. If you have
the `termux-api` package and the Termux:API app, it opens your browser by
itself. Otherwise open that address yourself: switch to your browser and type it
into the address bar.

**Step 3.** The header should read `Local T`. That means the page found the
Python server and is reading and writing `games/` on the phone directly. Press
**save** and the file appears in `~/spark/games/`.

**Step 4.** To stop it, go back to Termux and press Ctrl-C.

Notes:

- It listens on `127.0.0.1`, which is your phone talking to itself. Nothing on
  your wifi or anywhere else can reach it. This also means you cannot open it
  from a laptop — that is what GitHub Pages is for.
- Termux must stay running. If Android kills it in the background the page
  stops saving; acquire a wakelock from the Termux notification if that happens.
- **Opening `index.html` by tapping the file will not work.** Browsers refuse to
  let a `file://` page read the files beside it. There is no way around it; use
  the server.
- If port 8765 is busy, use another: `python3 spark.py edit 9000`.

### If nothing opens

Spark hands the address to Android and is never told whether anything caught
it, so it prints "Opening your browser now" either way. If no browser appears,
first find out whether this phone has one at all:

    pm query-activities --user 0 -a android.intent.action.VIEW -d https://example.com

- **`No activities found`** — nothing here opens web links. Install a browser,
  or skip the phone entirely: `python3 spark.py host` and type the wifi address
  it prints on a laptop or another phone.
- **A browser is listed but the wrong one opens** — name the one you want.
  `termux-open-url` takes a package as its second argument, so
  `termux-open-url http://127.0.0.1:8765/ com.android.chrome` goes straight to
  Chrome. That is exactly what the `open` tile does with its two boxes.

The same check explains an `open` tile that appears to do nothing.

---

## Connecting another person: live play

Everyone is in the same world at the same time, each driving their own
character. One phone is the host and runs the game; everyone else's browser
draws it and sends keypresses.

### Step by step, on the same wifi

**Step 1 — start hosting.** On your phone:

    cd ~/spark
    python3 spark.py host

It prints two different addresses. They are not interchangeable:

    You are hosting. Open this on THIS phone to be in charge:
      http://127.0.0.1:8765/#owner=fNdicZw49F2qjKam     <- yours, keep private
    Others on this wifi go to http://192.168.1.97:8765/  <- read this one out

The first has a key in it that makes you the owner. Open it on your own phone.
The second is the plain address for everyone else.

**Step 2 — make a code.** Either:

- terminal main menu → **invite someone to play** → pick what they may do, or
- in the browser, the **👥** button → *make a code*.

You get six characters, like `KQDAD5`.

**Step 3 — start a game for everyone.** 👥 → **start '<your game>' for
everyone**. Nothing is shared until you do this.

**Step 4 — they join.** They open the second address, type the code and a name,
and they are in. They get arrow buttons on screen, and a real keyboard works too
if they have one.

**Step 5 — watch or play along.** 👥 → **watch the game** puts you in the same
view.

To stop: 👥 → *stop the shared game*, or Ctrl-C in the terminal.

### What each code is worth

| Code says | Change games | Press keys | See the world |
|---|---|---|---|
| **edit** | yes | yes | yes |
| **play** | no | yes | yes |
| **watch** | no | no | yes |
| no code | no | no | no |

A code can also say **which character** that person drives — their own copy of
your player character (the default), or a named one, so a friend could drive the
bugs while you are the hero. Set that when you make the code.

Codes can be handed to several people at once, or limited to a single use. To
take access back, revoke the code: anyone who joined with it is dropped
immediately.

### Seeing who is in there

The header counts them — `Players 3` — and one word lists them by name:

    python3 spark.py players

Typing **`players`** at any menu prompt does the same thing without leaving the
menus, exactly like `browser`. Either way you get:

         name             may    inside         joined
     ----------------------------------------------------
     1.  Gabriel          edit   chase          14m ago
     2.  sam              play   chase          6m ago
     3.  bex              watch  chase          just now

     3 connected. The one who joined first is at the top.

| Column | What it is |
|---|---|
| the number | join order. 1 has been here longest. Someone who leaves and rejoins goes to the bottom, because the world they are in now is the one they just joined. |
| **name** | what they typed when they entered the code, cut to 16 letters |
| **may** | `edit`, `play` or `watch` — whatever their code granted |
| **inside** | the game they are in. `no game yet` means they are connected and waiting, having arrived before you started one. |
| **joined** | how long ago, rounded — `just now`, `6m ago`, `2h ago` |

The list is only ever as fresh as the last thing that happened: people are
dropped about 25 seconds after their browser goes quiet, so someone who closed
their tab a moment ago may still be shown. It works from a second Termux tab
too — the serving copy of Spark writes the roster to `.spark-state.json` and any
other copy reads it, so you can host in one tab and check in another.

### Step by step, for someone far away

    python3 spark.py host --public

This needs a tunnel program. **cloudflared is already installed on this phone**,
in both Termux and the PRoot distro, so this should work as-is.

If you ever need to install it again, note that `pkg install` refuses to run as
root, which is what you are inside the PRoot distro. Fetch the binary instead —
this phone is `aarch64`:

    # for Termux
    curl -L -o $PREFIX/bin/cloudflared \
      https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
    chmod +x $PREFIX/bin/cloudflared

    # for the PRoot distro
    curl -L -o /usr/local/bin/cloudflared \
      https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
    chmod +x /usr/local/bin/cloudflared

Check it with `cloudflared --version`.

Spark runs whichever tunnel it finds and prints an address anyone in the world
can open, like `https://butter-illinois-residents-ended.trycloudflare.com`. It
is different every time and stops working the moment you stop Spark. If no
tunnel is installed, Spark says so and carries on serving your wifi.

While that address is live the header reads `Cloudflare T`, on this phone and in
every browser that joined through it, so you can tell at a glance whether the
link you handed out still works. It falls back to `F` when Spark stops. The flag
tracks cloudflared only — if Spark fell back to ngrok you get a working address
but `Cloudflare F`.

Why this is needed: your phone has no address the internet can dial. A tunnel
borrows one from a company's server and forwards it to you. That is the only way
without renting a server.

### Safety, in plain terms

- **When you share, being on the phone is no longer enough to be the owner.**
  You must open the link containing the key. This is deliberate: a tunnel makes
  every visitor in the world *look* like they are on your phone, so if being on
  the phone still counted, a stranger could delete your games.
- **Your key is in that link.** Anyone you give it to is you. Read out the
  second address, never the first.
- **There is no rate limiting and no accounts.** A guest who wanted to could
  spam the server. Give codes to people you would hand your phone to.
- **Only the games folder is ever exposed.** No other file on your phone is
  reachable, and every route refuses anyone whose code does not cover it.
- **A shared world cannot open other apps.** The `open` tile is the one tile
  that reaches off the grid, and it does nothing in a hosted game. Somebody
  with an `edit` code can put an `open` row in a game and save it; it will sit
  there doing nothing until *you* play that game yourself on this phone. The
  same goes for a game pulled down from GitHub.
- Stopping Spark ends everything: all codes, all sessions, the tunnel.

## Connecting GitHub

Three separate things. You can do the first only, the first two, or all three.

### Part 1 — put Spark on GitHub (once)

**Step 1.** Log in. This is interactive, so type it yourself:

    gh auth login

Choose **GitHub.com**, then **HTTPS**, then **Login with a web browser**. It
shows you a one-time code; the GitHub app you are already signed into will take
it.

**Step 2.** Create the repo and push:

    cd ~/spark
    gh repo create spark --public --source=. --push

It must be **public** if you want the Pages link in Part 2 — GitHub Pages on a
private repo needs a paid plan.

**Step 3.** Check it worked:

    python3 spark.py status

`Github` should now read `T`. It means a remote is set and every commit is
pushed. If it says `F`, you have commits you have not pushed — `git push`.

### Part 2 — open the editor from a web address

**Step 1.** Turn on Pages:

    gh api -X POST repos/YOURNAME/spark/pages \
      -f 'source[branch]=main' -f 'source[path]=/'

Or on github.com: **Settings → Pages → Source: Deploy from a branch → main → /
(root) → Save**.

**Step 2.** Wait a minute or two, then open
`https://YOURNAME.github.io/spark/`.

**Step 3.** The header will read `Github T  Browser T  Local F  Cloudflare F`.
`Local F` is correct and expected — there is no Python behind a Pages site, and
`Cloudflare F` for the same reason: Pages is already public, so no tunnel is
involved. The editor works anyway: it reads `tiles.json` and `games/index.json`,
and keeps your edits in the browser's own storage.

**Remember:** anything generated has to be committed or the Pages copy is stale.
After adding a tile, run `python3 spark.py export`, then commit and push.

### Part 3 — save to GitHub from the browser

This makes **save** in the Pages editor write a real file into the repo.

**Step 1.** On github.com: **Settings → Developer settings → Personal access
tokens → Fine-grained tokens → Generate new token**.

**Step 2.** Set it up:

- **Repository access:** Only select repositories → your `spark` repo.
- **Permissions:** Repository permissions → **Contents: Read and write**.
  Nothing else. No other permission is needed and none should be given.
- **Expiration:** as short as you are willing to re-do. 90 days is sensible.

**Step 3.** Copy the token. It is shown once.

**Step 4.** In the Pages editor, tap **⚙** and fill in: your GitHub username,
`spark`, `main`, and paste the token. Tap **done**.

**Step 5.** Press **save**. The message should end with
`this browser + YOURNAME/spark`.

**About the token's safety.** It is kept in that browser's storage on that
device. Anyone with your phone unlocked can read it. That is why it should be
fine-grained, limited to the one repo, and Contents-only: the worst it can do is
change files in your Spark repo. Tap **⚙ → forget token** when you are done, and
delete it on github.com if you stop using it.

---

### Part 4 — let another person edit your games

This is the slow way of sharing: not the same world at the same time, but the
same repo over days and weeks. They need a GitHub account.

**Make them an editor** (they can change games and commit them back):

    python3 spark.py people theirusername

**Make them a reader:**

    python3 spark.py people theirusername --player

**See who already has access:**

    python3 spark.py people

GitHub emails them an invitation; access begins when they accept.

One thing that surprises people: on a **public** repo, `--player` changes
nothing, because anybody can already read a public repo and play from your Pages
link. Reader access only means something if the repo is private.

To remove someone, do it on github.com: **Settings → Collaborators → Remove**.

## Moving games between phone and GitHub

Once Part 1 is done you do not need a token for this — it borrows your
`gh auth login`.

**Phone wins, one world:**

    python3 spark.py push chase

**Phone wins, everything:**

    python3 spark.py push

**GitHub wins, one world:**

    python3 spark.py pull chase

**GitHub wins, everything:**

    python3 spark.py pull

There is no merging and no asking. Whichever side you name in the command
replaces the other for the games listed. `push` also refreshes the game list on
GitHub so the Pages editor sees the change.

From the terminal menus, **send this game to GitHub** does the same as
`push <the open game>`.

If you get `not logged in to GitHub`, do Part 1 Step 1. If you get `no GitHub
remote yet`, do Part 1 Step 2.

---

## Renaming a game

**In the terminal:** main menu → **rename this game**. It saves under the new
name and offers to delete the old file.

**In the browser:** **world settings** → **rename this game**. Same thing: it
saves a copy under the new name, then asks whether to delete the old one.

Renaming does not touch GitHub. To make GitHub match, `push` the new name — and
delete the old file on github.com yourself, since Spark never deletes anything
from your repo.

---

## What each of the four connections gives you

| | Github | Browser | Local | Cloudflare |
|---|---|---|---|---|
| Play games | no | no | **yes** | no |
| Drag-and-drop editing | via Pages | **yes** | — | via the public address |
| Works with no internet | no | yes, with the local server | **yes** | no |
| Edit from a laptop | **yes**, via Pages | no | no | **yes**, if you are hosting |
| Games stored where | in the repo | in browser storage | in `~/spark/games` | in `~/spark/games` |
| Needed for the others | no | no | no | needs Local |

The first three do not depend on each other. The terminal alone is a complete
Spark; the browser makes it pleasant; GitHub makes it portable and backed up.
Cloudflare is the exception — it publishes the server this phone is running, so
it is only ever `T` while Spark is hosting here.

## The two ways of sharing, compared

| | Live play (`host`) | GitHub (`people`) |
|---|---|---|
| Same world at the same time | **yes** | no |
| Works with no internet | **yes**, over wifi | no |
| Works with someone far away | only with a tunnel | **yes**, always |
| They need an account | no | a GitHub account |
| Access lasts | until you stop Spark | until you remove them |
| Permissions | edit / play / watch, per code | editor / player, per person |
| Good for | playing together now | building together over time |
