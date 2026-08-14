# Changelog

Everything that has changed in Spark, newest first, in plain language.
The guide itself is [README.md](README.md).

**House rule:** every change to Spark updates this file *and* the README in the
same breath. If you add a tile, it goes in the tile table in the README and in a
line here. If behaviour changes, say so here even if no file was renamed. A
change that is not written down is a change nobody can find again.

Each entry says **what** changed and, where it is not obvious, **why**.

---

## Unreleased

### Added

- **Tiles of your own: fold a whole row up under a name.** The **⊞** button on a
  row in the browser, or *fold a row into one tile of your own* on the terminal
  brain menu. The new tile joins the palette and can be used anywhere, as often
  as you like.

      the row:  WHEN I see apple within 6   DO move toward it, hurt it by 1

      folded as "hunt":

      WHEN ⊞ hunt      the seeing part is tested
      DO   ⊞ hunt      the moving and hurting part runs

  **Both halves go in together**, which is the whole point: one tile that works
  on either side and does the matching half of what you folded. The row you
  folded is replaced by the new tile in both halves, so the character carries on
  doing exactly what it did — folding tidies, it never changes behaviour.

  *Why:* rows repeat. The same three or four tiles get rebuilt on every enemy,
  and changing the idea meant changing it everywhere. This is the smallest thing
  that fixes that without inventing a second language: a named tile is only
  other tiles, so it needs no new syntax, runs no code, and cannot do anything
  the tiles it is made of could not.

  **"it" reaches inside.** A sensor within your tile that finds a character
  hands it out to the row; an action within it is handed whatever the row found.
  So a tile made only of `hurt it` still hurts whatever the row's WHEN half saw.

  **They live in the game file**, under `tiles`, so they travel with the game to
  GitHub and to anyone who joins your world — nothing to install, no code run.
  They may hold each other up to eight deep, and one that contains itself stops
  at that depth rather than spinning for ever.

  A name nobody has defined does not fire, and is skipped in the DO half, so a
  game whose tile has been renamed or deleted goes quiet rather than breaking.
  Deleting a tile therefore leaves rows that used it alone, and the chip says
  `(no such tile)`.

  Internally `run_row` was split into `check_all` and `do_all` so that a named
  tile is checked and run by exactly the code an ordinary row is — there is no
  second implementation to drift. `tests/check_tiles_of_mine.py` — 18 checks —
  covers both halves, empty halves, "it" passing through, unknown names,
  nesting, and self-reference; `games/placeholders.json` now uses three named
  tiles so `check_engines.py` compares them across both engines and four seeds.

- **Undo, in both brain editors.** A button beside *+ add a row* in the browser,
  and *undo the last change* on the brain and row menus in the terminal. Both
  show how many steps are left, and both remember the last **60** changes.

  It covers everything the brain editor does — adding and removing rows, moving
  them, adding and removing tiles, changing a tile's settings, dragging a tile
  between rows — plus deleting a character, since that throws whole brains away.
  It does not cover a character's colour, glyph or health, which are one retype
  to put back, nor world settings.

  *How it works, and why:* the whole game is copied as text once per change.
  Games are a few kilobytes, so sixty copies cost less than one photograph, and
  keeping the entire thing means nothing can ever be half-undone and no screen
  has to know which fields it owns. Opening a different game empties the history
  so undo can never quietly swap one game for another.

  Two wrinkles worth writing down. Opening a tile's settings and closing them
  again costs no step — the mark is dropped if nothing actually moved, and the
  browser hooks the dialog's own close event so Escape and tapping the backdrop
  count too. And in the terminal, undo refills the project dictionary in place
  rather than rebinding it, because every menu screen is holding that same
  dictionary; the screens then unwind to the character list, which re-reads
  everything, because the characters and rows *inside* it are new objects.
  `tests/check_undo.py` — 19 checks — pins both of those down.

- **Every tile is offered in both halves.** The browser palette shows the half
  you are on, then every other tile as well, dashed and dimmed under a heading;
  the terminal menus list the strays too, marked with what they will do. A
  button at the top of the palette goes back to only the tiles that fit.

  *Why:* which tile belongs where is the engine's rule, and there is no reason
  to hide the rest from the person building the game — you can decide what to
  use. What the engine actually does with a stray is now stated rather than
  left to be discovered: a **DO** tile in the **WHEN** half makes the row never
  fire at all, and a **WHEN** tile in the **DO** half is quietly skipped. Placed
  strays stay marked, so a row that never fires shows why on its face.

### Fixed

- **The local server now answers `/tiles.json`.** It served the tile catalogue
  at `api/tiles` but 404'd on the filename that GitHub Pages, and a plain
  folder, both use — so anything written against the URL that works everywhere
  else broke the moment the server was running. It is answered from the live
  registries rather than the file on disk, so it can never be a stale copy from
  before the last `spark.py export`.

### Changed

- **Placeholders hold decimals now, not just whole numbers.** `7 divided by 2`
  is `3.5` where it used to be `3`, and `value creep = creep plus 0.25` counts
  up in quarters. Every face takes them — the value and all three axes of a
  vector.

  *Why:* whole numbers were a shortcut taken to guarantee the two engines could
  never disagree, and it turned out not to be needed. Python and JavaScript use
  the very same 64-bit floating-point numbers, so `+`, `−`, `×`, `÷` and square
  root are bit-for-bit identical on both. What actually keeps them in step is
  the fence, which stays, plus refusing the few operations where the languages
  really do differ — see the sign rules below.

  **The grid has not become fractional.** *jump to vector* and *move by vector*
  round to the nearest square, halves away from zero, so a vector of `0.4` moves
  you nowhere and `0.6` moves you a full square. To creep along slower than a
  square a tick, keep the fraction in a placeholder and move by its whole part:

      WHEN always  DO value creep = creep plus 0.25
                      vector step x = down creep plus 0
                      value creep = creep remainder 1

  Two consequences worth knowing. `divided by` no longer cuts toward zero, so
  the old identity with `remainder` needs the cut written back in explicitly —
  `down (7 divided by 5) times 5 plus (7 remainder 5)` is 7 — and only at or
  above zero, since `down` cuts the other way below it. And `to the power of`
  now **rounds** its exponent rather than requiring a whole one; fractional
  powers stay out on purpose, because `2 ** 0.5` is where the two languages can
  differ in the last bit, and that is what `root` is for.

### Added

- **Five words that work on a single box: `root`, `round`, `down`, `up` and
  `random`.** They complete the arithmetic — square roots, all three kinds of
  rounding, and dice — without a single new tile, because they are read inside
  a box rather than being tiles of their own:

      value side = root area plus 0
      value roll = random 6 plus 1
      value step = down creep plus 0

  Each takes a box of its own, so they nest one level: `root home x`,
  `round root 17`, `random my health`.

  `random` rolls the **world's own dice** — the same source `move random` uses —
  so a seeded world rolls the same numbers in both engines, and
  `check_engines.py` proves it. `random 6` gives 0 to 5, making ordinary dice
  `random 6 plus 1`; the number of sides is rounded down first, and zero or
  fewer sides gives 0 rather than an error, because a sum is not a place a game
  may fall over.

  `round` is spelt out rather than handed to either language, which disagree
  with each other and with intuition: Python's `round(2.5)` is `2` (nearest
  even) and JavaScript's `Math.round(-2.5)` is `-2` (halves upward). Spark sends
  exact halves **away from zero**, in both engines.

- **The `placeholder ... has ...` WHEN tile compares against a whole box**, not
  just a fixed number. So a row can now compare two moving things:

      WHEN placeholder gap has value at least my health   DO ...

  *Why:* it was the one place a number had to be typed literally, which made
  half the box vocabulary unreachable from the WHEN half. Old games are
  unaffected — a stored number still reads as itself. There is no `it` while a
  WHEN tile is being read, `it` being what the sensors produce, so `it x` in
  that box is 0.

  `tests/check_places.py` grows to 118 checks.

- **Nine operations in a sum, up from four.** The `=` tiles now offer
  `remainder`, `to the power of`, `but no more than`, `but no less than` and
  `how far from`, alongside the original `plus`, `minus`, `times` and
  `divided by`. No new tiles — the same two `=` tiles, a longer list on the
  menu — so nothing has to be rebuilt and old games keep working, `plus` being
  the default as before.

  *Why:* the first four covered arithmetic but not the four things games
  actually keep needing. `remainder` is how anything goes round in a circle —
  `tick remainder 4` counts 0, 1, 2, 3, 0, 1, 2, 3 for ever, which is a
  four-frame animation or a four-step patrol. `but no more than` and `but no
  less than` are a ceiling and a floor, so two tiles now fence a value into a
  range instead of several rows faking it. `how far from` is distance along an
  axis and never comes out negative, which also makes it the only way to get
  absolute value.

  **Two sign traps are pinned down rather than left to the languages.** Python
  and JavaScript disagree about both, so Spark defines its own and neither
  language's operator is used:

  | | Spark | Python alone | JavaScript alone |
  |---|---|---|---|
  | `-7 divided by 5` | `-1` | `-2` | `-1` |
  | `-7 remainder 5` | `-2` | `3` | `-2` |

  Division cuts toward zero, remainder takes the sign of the left box, and the
  two are defined off each other so they always reconcile back to the original
  number. Dividing by zero, and the remainder of zero, are both **0** — a row
  sitting on `always` must not be able to break the world.

  `to the power of` has no negative exponents (that would be a fraction) and is
  worked out by multiplying step by step, clamping as it goes, so `10 to the
  power of 999` stops at the fence with the right sign instead of building a
  thousand-digit number in one engine and an infinity in the other.

  `tests/check_places.py` grows to 78 checks, and `games/placeholders.json` now
  uses the new operations so `check_engines.py` proves both engines agree about
  them too.

- **Placeholders: an arbitrary named slot you can regard three ways at once —
  as a name, as a value, or as a vector.** Eight new tiles, six DO and two WHEN.
  Invent any name and the slot appears underneath it; nothing has to be declared
  or set up first.

      WHEN always          DO name target is "apple"
      WHEN every 1 ticks   DO value steps = steps plus 1
      WHEN key h pressed   DO vector home x = my x plus 0
                              vector home y = my y plus 0
      WHEN key g pressed   DO jump to vector home

  The three faces belong to the one slot, so `home` can be named, valued and
  pointed at a square all at once, and each face is read back on its own. The
  right-hand half of a `=` tile is a **sum**: two boxes with **plus**,
  **minus**, **times** or **divided by** between them. A box takes a number, or
  `my x` / `it y` / `score` / `tick`, or the name of another placeholder —
  `speed` for its value, `home x` for one axis of its vector.

  *Why:* every tile until now either moved something or named something.
  Nothing could **hold a number and do arithmetic on it**, so a game could not
  count its own steps, measure the gap between two characters, or remember a
  square to come back to. `remember` was the closest thing and it only holds
  text. Splitting the idea into a name face, a value face and a vector face —
  rather than three separate kinds of variable — means the same slot can be
  regarded whichever way the row happens to need, which is what makes the tiles
  snap together instead of sitting next to each other.

  The full list: `name <who> is "<text>"`, `value <who> = <box> <op> <box>`,
  `vector <who> <axis> = <box> <op> <box>`, `copy my place into vector <who>`,
  `jump to vector <who>`, `move by vector <who>`, and the two WHEN tiles
  `placeholder <who> has <face> <test> <n>` and
  `placeholder <who> is named "<text>"`. That takes Spark from 11 × 14 tiles to
  **13 × 20**.

  Two rules worth knowing, both in [MANUAL.md](MANUAL.md) in full: everything a
  placeholder holds is a **whole number** between −1,000,000,000 and
  1,000,000,000, stopping at the fence rather than wrapping; and an **unwritten
  placeholder reads as 0** on every face and an empty name, so a row can read
  one before any row has written it. Reading a name does not create it, so a
  typo stays a quiet zero.

- **`games/placeholders.json`** — a small worked game using all eight tiles: a
  step counter, a home square you can jump back to, arrow keys driving a vector,
  and a win condition read off a placeholder. It doubles as the parity fixture,
  so `check_engines.py` now plays the new tiles in both engines too.

- **`tests/check_places.py`** — 50 checks on the placeholder tiles: each face,
  every operation, dividing by zero, the fence at both ends, what an empty box
  means, what an unwritten placeholder means, and that `0x10` and `1_0` are not
  numbers in either engine.

- **Three tiles that work on names instead of the grid: `remember`, `I
  remember`, and `open`.** `remember chrome is com.android.chrome` ties a short
  name to a long value; `open chrome at home` hands a target to another app on
  the phone. Every box takes either a remembered name or the literal thing, so
  nothing has to be remembered first:

      WHEN always            DO remember chrome is com.android.chrome
                                remember home is http://127.0.0.1:8765/
      WHEN key o is pressed  DO open chrome at home

  *Why:* every tile until now moved something around a grid. These are the two
  smallest pieces that let a game reach off it — one that names a thing, one
  that acts on the name — rather than a single `open chrome` tile that would
  have been useless for anything but Chrome.
  `I remember <name> is <value>` is the WHEN half, and since nothing is
  remembered when a game starts, it is also how a game asks *has this happened
  yet*.
- **`tests/check_open.py`** — 16 checks on those tiles, most of them on the
  fences below. It fails if the guest fence is removed; I checked by removing
  it.
- **A player count on the status line, and a `players` command to name them.**
  The line ends with `Players 3`, and typing `players` at any menu prompt — or
  running `python3 spark.py players` — lists everyone connected, **in the order
  they joined**, with the game each one is inside and how long ago they
  arrived. `who` works too, and `players` goes wherever `browser` goes.
  *Why:* hosting was blind. You handed out invite codes and then had no way to
  tell whether anybody used them, how many people were in there, or who. The
  browser had a people button; the terminal, where you actually host from, had
  nothing. A count answers "is anyone there" at a glance and the list answers
  "who" without opening a browser.
  Somebody who leaves and rejoins goes to the **bottom** of the list: the order
  is when they joined *this* world, not when you first met them.

- **A fourth flag: `Cloudflare`.** The status line now reads
  `Spark exe  Github T  Browser T  Local T  Cloudflare T`. It is `T` while a
  cloudflared tunnel is up and serving the public address, in the terminal and
  in the browser header alike.
  *Why:* the tunnel was the one connection you could not see. The address is
  printed once when hosting starts and then scrolls away, and it dies silently
  whenever Spark stops — so there was no way to answer "is the link I sent my
  friend still alive?" without sending a message and waiting. Now it is one
  glance, from the same line as everything else.
  The flag names cloudflared exactly: if Spark fell back to ngrok you get a
  working address but `Cloudflare F`.

- **A 3D view of your world, on a button, that works with nothing behind it.**
  The browser editor has a **▶ 3D** button; it opens a second tab where the
  board stands up off the page as blocks you can turn with one finger and pinch
  to zoom, each still wearing the glyph and colour you gave it.

  The tab shows the real running game when a Spark server answers — badge
  `LIVE`, mirrored tick for tick, guests included — and plays the game itself
  when none does — badge `RUNNING HERE`. That covers the local server, a
  Cloudflare tunnel, the GitHub Pages copy, aeroplane mode with Termux shut, and
  the file saved and reopened on its own. If the server vanishes mid-watch it
  switches over rather than freezing.

  *Why:* the flat grid of letters is honest about the rules but says nothing
  about the shape of a world, and the moment you want to show somebody what you
  built, a wall of monospace is the wrong thing to hand them. The awkward part
  was that "show it to somebody" and "have it work" pull in opposite directions:
  anything drawn with a library fetched from a CDN goes blank the moment the
  signal does, which is exactly when a phone game matters. So the 3D is raw
  WebGL, already in the browser, and **nothing is downloaded at any point**. The
  game itself rides inside the link after the `#`, which never travels to any
  server — so the tab has the world before it asks anyone for anything, and it
  shows what is on your screen rather than what you last saved.
- **`world3d.html`** — the 3D view, and with it a second copy of Spark's rules
  written in JavaScript, so a browser on its own can play a game.
- **Seeded worlds, and `engine/rng.py`.** `World(project, seed=7)` now replays
  exactly, in both languages. Unseeded play is untouched and still genuinely
  random.
  *Why:* two engines can only be *proved* to agree if they can be made to roll
  the same dice, and Python's `random` is a Mersenne Twister that no reasonable
  amount of JavaScript will reproduce. A small generator both languages run in
  exact integer arithmetic costs almost nothing and makes the check below
  possible.
- **`tests/check_engines.py`** — plays every game in `games/` twice, once with
  each engine, from the same seed and with the same keys pressed on the same
  ticks, and fails unless every character is in the same square with the same
  health on every tick.
  *Why:* two copies of a rule drift apart, and drift here would mean the 3D view
  quietly lying to you about your own game. This is what makes a second engine
  safe to keep. It fails if you change a rule in one engine and forget the
  other; I checked by flipping a single sign in the JavaScript, and it caught it
  in nine of the twelve game-and-seed runs.

### Changed

- **The server writes the tunnel's name and address into `.spark-state.json`.**
  *Why:* the tunnel only ever existed as an object inside the serving process,
  so the menus — a different process — had no way to know about it. This is the
  same note the Browser flag already travels on.
- **Both live flags now share one check that the server is still listening.**
  *Why:* a note in the state file outlives a hard kill. Tying it to a socket
  that answers means a stale note reads `F` rather than lying, and it costs one
  probe instead of two. The player count rides the same check, so a roster left
  behind by a killed server reads `Players 0` instead of a number of ghosts.
- **A player now remembers when they joined, separately from when they were
  last seen.** *Why:* `seen` moves every time their browser polls, so it could
  never say who arrived first. Ordering needs a timestamp that does not move.
- **`tests/check_docs.py` can spell past thirteen.** *Why:* it verifies the
  README's tile count against the real registries by parsing the number word,
  and the DO tiles just became fourteen. Extending its vocabulary keeps the
  check as strict as it was; leaving it would have meant deleting the check.

- **The editor is built for thumbs.** Nothing you press is under 48 pixels tall
  now — tiles, row buttons, character pills, the pad. The top is two rows
  instead of one: the game you are on with its two icon buttons, and beneath it
  a full-width row of the three things you actually reach for — **▶ 3D**,
  **save**, **new**, in that order.
  *Why:* the header had grown to five controls on one line, several of them
  smaller than a fingertip, on a device with no pointer. Putting playing first
  and giving it real area matches what the loop actually is: change a rule, look
  at it, change it again.
- **The 3D pad is two to three times the size it was, and no longer sits on top
  of the world.** The screen is now two regions that never overlap — world
  above, pad below, or side by side when the phone is turned sideways, where
  there is width to spare and no height to spare. The camera fits the board to
  whichever region it is given, so nothing is drawn underneath a button.
  The pad fills what is left, measured as a share of the screen it is actually
  on: half the height upright, half the width sideways, capped so a tablet does
  not get a pad the size of a dinner plate. That puts a key between 89px on a
  small phone and 144px on a tablet, up from a flat 56px.
  **restart**, **centre** and **run here** moved to the top bar.
  *Why:* the pad had been floating over the canvas, which meant every pixel it
  gained was a pixel of the game it covered — so it could not grow without
  taking away the thing it was there to play. Giving it a region of its own
  turns that into a straight split, and the camera was already fitting the
  board to the canvas rather than the window, so it followed for free.
  Sizing in `vh`/`vw` rather than pixels is what makes it land right on a
  screen nobody has tested it on.

### Security

- **The `open` tile is fenced three ways.** A game file is a thing people
  share — it comes down from GitHub, and a guest holding an `edit` code can
  rewrite one — so a tile that launches apps has to say no by default.
  1. **A shared world never opens anything.** `runner.play` turns opening on
     for a game you play yourself; `live.Session` leaves it off, so a guest
     cannot make the host's phone launch anything however they edit the game.
  2. **A cooldown of 30 ticks per target**, so a row on `always` asks about
     once every five seconds rather than six times a second.
  3. **It never waits for the app**, so a slow launch cannot stall the world.

---

## 0.9.0 — 2026-08-09

Aiming, and shots that stop somewhere.

### Added

- **`face <bearing>`, a DO tile.** Turns a character on the spot without moving
  it. The choices are the eight compass points — north, north-east, east,
  south-east, south, south-west, west, north-west — plus toward it and away
  from it. North is up the screen.
  *Why:* until now the only way to point somewhere was to walk there, so a
  turret could not aim, and nothing could shoot diagonally at all — the four
  diagonals existed nowhere in the tile set. `move forward` and `shoot forward`
  now follow whatever `face` last set.
- **`shoot` asks two more questions: reach and longevity.** *How many squares
  does it fly* kills the shot once it is that far from you; *how many ticks does
  it last* kills it once it has been alive that long. Either can be 0 for no
  limit, and old games that saved a `shoot` tile with only a direction get the
  defaults, 8 squares and 12 ticks.
  *Why:* every shot used to fly until it hit something or reached the edge, so
  a pistol and a laser were the same weapon.
- **`my range or time has run out`, a WHEN tile.** How the two limits above
  actually take effect: it is a plain row in the built-in `shot` brain, so it
  can be read, copied and rewritten like any other tile rather than hiding in
  the engine.

### Changed

- Characters now count the ticks they have lived (`age`) and the squares they
  have actually moved (`travelled`). Only the new WHEN tile reads them, and
  moving is counted on success, so a shot held against a wall keeps ageing
  without covering ground.
- `tiles.json` gained a `bearings` list next to `directions`, and has been
  re-exported.

---

## 0.8.0 — 2026-08-09

Getting in and out of Spark with one word each.

### Added

- **`python3 spark.py install`** — writes a small `spark` script into Termux's
  bin folder, so from then on you type `spark` from anywhere instead of a path.
  It also writes one inside the PRoot distro, which needs a different first line
  because Android has no `/bin/sh`. Every command works the short way after
  that: `spark tutorial`, `spark edit`, `spark host`.
- **Typing `browser` at any menu prompt** opens the drag-and-drop editor. It
  starts the server on its own thread, so the menus stay exactly where they
  were and you have both editors at once, sharing the same `games/` folder.
  `b` works too.
- The main menu now says so, rather than leaving you to guess.

### Changed

- The server can be started quietly, without printing its banner, which is what
  lets the menus open it without scribbling over the screen.
- Asking for the browser twice reuses the server already running instead of
  trying to claim the port again, and says plainly what to do if the port is
  taken by something else.

---

## 0.7.0 — 2026-08-09

A way in for someone who has never done this before.

### Added

- **`python3 spark.py tutorial`** — ten guided lessons in the terminal that
  build a real, playable game one row at a time. Runs entirely on the phone:
  no browser, no wifi, no GitHub, nothing to install.
- It is also the first item on the main menu, worded as **learn how**, because
  somebody meeting Spark for the first time has no reason to know a command
  exists.
- The lessons **ask you which tile does the job** rather than telling you.
  A wrong answer is explained and you try again; nothing is scored and nothing
  is lost. Being handed the answer teaches nothing.
- It **offers to play what you have built** at four points along the way, so
  each idea is felt rather than described.
- Lesson 6 is about the word **"it"** alone, since that is the single idea that
  makes tiles connect to each other, and it is the thing people miss.
- At the end you **name the game and keep it**, saved into `games/` like any
  other and openable in either editor.

---

## 0.6.1 — 2026-08-09

### Added

- **cloudflared is now installed** on this phone, in both Termux and the PRoot
  distro, so `spark.py host --public` works without further setup. Confirmed
  end to end: the public address served the editor, and a stranger asking for
  the game list through it was refused, which is the owner-key fix doing its job
  from the far side of the internet.

### Fixed

- The instructions said `pkg install cloudflared`. That is wrong here: `pkg`
  refuses to run as root, which is what you are inside the PRoot distro. The
  documents and the message Spark prints when no tunnel is found now give the
  method that actually works — fetching the `aarch64` binary from Cloudflare's
  releases.

---

## 0.6.0 — 2026-08-09

Other people. Spark can now be shared — a world several of you are in at once,
or a repo someone else can edit.

### Added

- **`python3 spark.py host`** — the editor, but open to everyone on your wifi.
  It prints the address they type in. `spark.py edit` is unchanged and still
  only listens to this phone.
- **A shared world.** The host runs the game; everyone else's browser draws it
  and sends keypresses. Each person drives their own character, so two people
  can move at the same time without treading on each other.
- **Invite codes with permissions.** The host makes a code and says what it is
  worth:
  - **edit** — change games and save them, and play
  - **play** — join the world and press keys, nothing else
  - **watch** — see the world, press nothing
  A code can also say which character that person drives, either their own copy
  of the player character or a named one. Codes can be revoked, which also
  removes anyone who used them.
- **Where to make codes:** the terminal main menu → *invite someone to play*,
  or the 👥 button in the browser.
- **On-screen controls** for the shared game, so a phone with no keyboard can
  play.
- **`python3 spark.py host --public`** — runs a tunnel program you have already
  installed (cloudflared or ngrok) and prints an address anyone in the world can
  use. If neither is installed it says so plainly and carries on over wifi.
- **`python3 spark.py people`** — who else can reach your GitHub repo, and
  `python3 spark.py people NAME` to let another GitHub user in as an editor
  (push access) or with `--player` as a reader.
- **Two test files**: `check_permissions.py` (36 checks) and
  `check_multiplayer.py` (12 checks).

### Changed

- A character can now be driven by a named player. Solo play is untouched: a
  character nobody has claimed still answers to the keyboard in front of it.

### Fixed

- **A hole worth understanding.** Spark decided you were the owner if your
  request came from the phone itself. That is fine while only the phone can
  reach it — but a tunnel forwards the whole internet through the phone, so
  every stranger would have arrived looking like the owner and could have
  deleted your games. Now, whenever Spark is shared, being on the phone proves
  nothing: the owner has to present a key that is printed in the terminal at
  startup and put in the link it opens for you.

### Known limits

- Live play needs everyone on the same wifi, or a tunnel. A phone has no address
  the internet can dial on its own; that is a fact about mobile networks, not
  something Spark can fix.
- The tunnel address changes every time you start it, and dies when you stop.
- Guests are trusted not to hammer the server; there is no rate limiting. Do not
  hand codes to people you would not hand your phone to.

---

## 0.5.0 — 2026-08-09

Moving single worlds between the phone and GitHub, and renaming what you have
already made.

### Added

- **`python3 spark.py push [game ...]`** — overwrite what is on GitHub with what
  is on this phone. Name one world to send just that one, several to send those,
  or none to send all of them. It uses the login you already did with
  `gh auth login`, so there is no second token to keep.
- **`python3 spark.py pull [game ...]`** — the same in reverse: GitHub's copy
  replaces the one here.
- **Send this game to GitHub** in the terminal main menu, which pushes whichever
  game is open.
- **Rename this game** — in the terminal main menu, and in the browser under
  world settings. It saves under the new name and offers to delete the old copy.
- **[MANUAL.md](MANUAL.md)** — system requirements, every key and button in all
  three interfaces, every command, and exact step-by-step instructions for
  connecting the browser interface and GitHub, including how to make the token.
- **`python3 tests/check_sync.py`** — 19 offline checks on the push and pull
  logic, with the network and git stood in for.

### Changed

- The README now names all three documents at the top.
- Deleting a game is possible from the browser, which is what makes renaming
  tidy rather than leaving a copy behind every time.

### Fixed

- The README check was only spotting commands written one particular way, so
  `pull` was going unverified. It now reads both forms.

### Notes

- `push` and `pull` do not merge and do not ask. Whichever side you name in the
  command replaces the other for the games you listed.
- Spark never deletes anything from your GitHub repo. Renaming and then pushing
  leaves the old name there until you remove it on github.com yourself.

---

## 0.4.0 — 2026-08-09

Writing things down, and making it impossible to forget to.

### Added

- **This file.** Every change to Spark now has a dated entry in plain language,
  linked from the top of the README.
- **`python3 tests/check_docs.py`** — fails if the README has drifted from the
  code. It checks that every tile appears in the README's tile table, that every
  command the launcher answers to is documented, that every file that ships is
  listed, that the README still links here, and that the tile count claimed in
  the README is the real one. Run it before committing.

### Changed

- The README was rewritten to be complete rather than merely correct: a table
  of contents, both folder paths spelled out, every command in one table, an
  explanation of what a game file contains, a plain account of how a brain runs
  tick by tick, and a troubleshooting section.

### Fixed

- The README claimed "twelve tiles crossed with nine". It is nine WHEN tiles and
  eleven DO tiles. The new check makes that particular mistake impossible to
  repeat.

---

## 0.3.0 — 2026-08-09

The editor learned to live on the internet without giving up working offline.

### Added

- **Runs from GitHub Pages.** The editor page now works with no Python behind
  it at all, so the repo can be published and opened from any device. It figures
  out for itself which situation it is in: if the local server is there it reads
  and writes `games/` on disk exactly as before; if not, it falls back to files
  and to browser storage.
- **`tiles.json` and `games/index.json`.** A page with no server cannot ask
  Python what tiles exist, so the tile list and the game list are now written
  out to disk as ordinary files. `python3 spark.py export` refreshes them, and
  starting the server does it automatically.
- **Saving to GitHub from the phone.** In the browser, ⚙ takes a GitHub user,
  repo, branch and a fine-grained token (Contents: read and write, that one repo
  only). With it set, pressing save also commits `games/*.json` to the repo.
  Without it, saving still works — it just stays in the browser.
- **The status line.** `Spark exe  Github F  Browser F  Local T`, printed above
  every terminal menu and shown in the browser header, so you can see which of
  the three channels is live before you type anything. Also on demand with
  `python3 spark.py status`. See the README for what each flag means.
- **`python3 spark.py status`** and **`python3 spark.py export`** commands.
- **Tests.** `node tests/store.test.js` — 17 checks on the editor's save and
  load logic. Worth having because that logic runs in a browser, where the rest
  of the project's testing cannot reach it.
- **A git repository**, with `.gitignore` and `.nojekyll` (which stops GitHub
  Pages trying to be clever with the files).

### Changed

- `editor.html` is now **`index.html`**, so that both the local server and
  GitHub Pages serve it at the plain address with nothing after the slash.
- The game list no longer treats `games/index.json` as a game called "index".

### Fixed

- Opening a game that does not exist, or losing the network mid-request, no
  longer throws an error at the page — it reports it and carries on.
- Opening the page as a `file://` path now explains the real problem instead of
  failing silently. Browsers forbid a local page from reading the files next to
  it, so that route cannot be made to work; `spark.py edit` is the offline path.

### Known limits

- GitHub Pages is free on **public** repos only. A private repo needs a paid
  plan before its Pages link works.
- The GitHub token is kept in browser storage. Anyone holding the unlocked phone
  can read it. Use a fine-grained token limited to the one repo, and use ⚙ →
  *forget token* when you are done.

---

## 0.2.0 — 2026-08-09

A drag-and-drop editor, because numbered menus are hard work on a phone.

### Added

- **`index.html`** (then called `editor.html`) — the visual editor. Tap a tile
  in the palette to drop it into the highlighted row, tap a placed tile to
  change its numbers, drag a tile to another row or onto the bin to delete it.
- **`engine/server.py`** — a small local server so the browser can read and
  write `games/` directly, instead of leaving files in a downloads folder.
  It listens on `127.0.0.1` only, so nothing off the phone can reach it.
- **`python3 spark.py edit`** to start it.

### Notes

- The palette is **generated from `engine/tiles.py`**, never typed into the HTML.
  This is the reason a new tile shows up in both editors with no further work.
- Touch was designed for first: phones do not fire the drag events desktop web
  pages use, so tapping is the main way to place a tile and dragging is only for
  rearranging.

### Fixed

- A drag that ended on a tile no longer pops open that tile's settings box.

---

## 0.1.0 — 2026-08-09

First working version: the idea, the engine, and a game to poke at.

### Added

- **The brain model.** A game is a cast of characters; each has a brain, which
  is a list of `WHEN <sensor> DO <action>` rows, read top to bottom every tick.
- **The word "it".** A sensor can hand what it found to the actions on its row,
  which is what makes `WHEN I see apple within 6 DO move toward it` possible.
  Without it the tiles would not connect to each other.
- **20 tiles** — 9 WHEN, 11 DO. Listed in the README.
- **`engine/tiles.py`** as the one place tiles are defined, so nothing else has
  to be kept in step when you add one.
- **`engine/world.py`** — the grid, the characters on it, and the rule engine.
- **`engine/builder.py`** — the terminal editor, all numbered menus, no typing
  of code.
- **`engine/runner.py`** — the keyboard and the drawing, at 6 ticks a second.
- **`games/chase.json`** — the demo. Eat five apples to win; two bugs chase you;
  walls block; space shoots.
- **`README.md`**.
