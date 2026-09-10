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

- **The plain terminal player has its own "/" command line and `/help`
  now, not just world3d.html's chat** — requested directly: get the
  keys `outpost` actually plays with to stop leaking into some text box,
  and put a second, dedicated screen behind the keyboard for `/help` and
  commands, in the terminal (`python3 spark.py play`), not just the
  browser. Pressing `/` during play hands the terminal back to normal
  cooked line input for one line — a real text box, backspace and all,
  the same as it behaves anywhere else in this app — rather than
  gameplay's usual one-key-at-a-time swallowing (`Keyboard.pause()`/
  `.resume()`, wrapping the exact termios restore/re-apply
  `__exit__`/`__enter__` already did). Whatever's typed runs as a
  command and its result shows on its own screen — `/help` reads the
  same `help` field a game's `/help` in chat does (see below), a small,
  deliberately local set otherwise (there's no server connection from
  the plain terminal player the way the browser clients have, so no
  `/who` to answer or `/clear` to run) — until any key dismisses it and
  the running world comes back.

  `tests/check_chat_break.py` (new, 11 checks): the pure command logic
  directly (help text, blank input treated as help, unknown commands,
  /quit), and a real pty end to end — pressing `/`, typing `help`,
  confirming `outpost`'s own instructions and a distinct "chat" screen
  show up, a key afterward returning to the running game, and `q`
  still quitting normally afterward. Same trick `check_menu.py` already
  uses for this exact reason: a plain pipe can't tell apart from a real
  terminal the way this feature needs to.

- **`recruit`: "buy a unit" for a price** — requested directly, right
  after asking for the chat/help work above: "I wanted into outpost...
  to buy with ore amount a new unit entity to my team for work or
  combat, name one soldier and one worker." One new tile: `recruit`
  spawns a new `{kind}` at the recruiter's OWN spot (not a random empty
  square, the way plain `spawn` works) and already following them --
  `spawn` then `lead` in the same row could never target the thing
  `spawn` just made, since a row's DO tiles all get the same `it` from
  the WHEN half. Pair it with `has_item` (WHEN) and a negative
  `give_item` (DO) in the same row to actually charge for it -- neither
  tile enforces a cost on its own, `recruit` only handles the
  spawn-and-follow half.

  `games/outpost.json`'s hero can now press `1` for a `worker` (8 ore --
  gathers ore twice as fast as a plain recruited companion, no combat
  at all) or `2` for a `soldier` (15 ore -- more health and reach than a
  companion, hits harder, doesn't gather) -- each a distinct kind with
  its own ordinary brain rows (`has_leader`/`see`/`touch`, nothing new),
  not a new engine-level unit type. Both appear already following the
  hero, at the hero's own feet, the instant they're bought. Added `"1"`,
  `"2"`, and (from the release-key work in the previous entry) `"r"` to
  the shared `KEYS` list -- all three worked already (the engine only
  ever checks key membership, never the suggested-choices list) but
  weren't real picks in the tile editor's own dropdown until now.

  `tests/check_lead.py` extended (+5 checks, 16 total) and
  `tests/lead.test.js` extended (+4 checks, 17 total): a fresh unit
  actually appears, at the recruiter's own spot, already led by them --
  and one row combining `has_item`/`give_item`/`recruit` together,
  confirming it silently does nothing while unaffordable and actually
  deducts the cost once it is. `check_engines.py` picked up the whole
  updated `outpost.json` for free (it discovers every `games/*.json`),
  confirmed bit-for-bit identical between the two engines across four
  seeds with the new kinds and buy rows in place. Also manually hired
  one of each and watched the game run another 500 ticks with no
  crashes. Validated with `node --check`, a full `html.parser` pass,
  `python3 -m py_compile`, and the full existing suite, all green. Not
  seen running in either the terminal or world3d.html on a real device
  yet.

- **A game can carry its own "how to play," shown any time with `/help`
  in chat** — requested directly, right after simulating a playthrough
  of `outpost`: "add to spark > outpost instructions how to play also
  accessible later with /help." `/help` already existed as a chat
  command (it listed the OTHER chat commands); it now also prints a
  game's own `help` field first, if it has one — a plain multi-line
  string on the game JSON itself, alongside `name`/`world`/
  `characters`, round-tripping through save/load with no engine change
  needed since `brain.load`/`brain.save` were already schema-free
  `json.loads`/`json.dumps` on the whole project. A game with no `help`
  field just goes straight to the command legend, unchanged from
  before. Works whether or not the server's running (unlike sending a
  message, showing your own local text needs nothing else), so it's
  reachable in local play too, not just `LIVE` games. `games/outpost.json`
  is the first game to actually carry one, covering movement, recruiting
  (`e`)/releasing (`r`) a companion, fighting, gathering, and Build mode.
  Also added `"r"` to the shared `KEYS` list (the `key` tile's own
  choices) — `outpost`'s own release key, which worked already (the
  engine only ever checks membership, never the suggested-choices list)
  but wasn't a real pick in the tile editor's own dropdown until now.

  `tests/chat.test.js` extended (+3 checks, 13 total): a game's help
  text shows in full ahead of the command legend, a game with no help
  field skips straight to the legend, both checked with the exact
  `outpost.json` data through the real code path (not just a mocked
  string). Validated with `node --check`, a full `html.parser` pass,
  and the full existing suite, all green.

- **`lead`/`dismiss`/`has_leader`: recruit a companion by touching it, and
  it follows you** — requested directly: an RTS/Kenshi-style "command
  units" mechanic, "with when do code" (tile-authored, not bespoke UI
  logic the way Harvest is). `lead` sets whoever you touch to follow
  *you* — always the recruiter, never the one recruited, so it only
  does the right thing authored on the recruiter's own brain ("WHEN
  touching companion DO lead it"). `dismiss` clears it again. A
  recruited companion finds out through its own new `has_leader`
  sensor, which hands its leader back as `it` — so "WHEN has_leader DO
  move toward it" (the ordinary `move` tile, completely unchanged, the
  same "toward it" the `see`/`touch` sensors already drive chasing
  with) is all a companion's own brain needs to actually follow along.
  A leader who has since died reads the same as never having had one,
  so nobody chases a corpse. New `Thing.leader` field (both engines) --
  a Thing reference, not a name, following the same "per-Thing, not
  world-shared" reasoning `inventory` and `harvest` already established.

  New demo game, `games/outpost.json`: a small frontier camp with a
  player hero, three recruitable companions, wandering bandits, and
  `harvestable` ore veins (the existing tile from the harvest work
  above) standing in for Kenshi's ore nodes. Companions fight whatever
  bandit they see nearest and chase it down on their own (`see`/`touch`
  + `damage`, no new tiles needed for that part), and slowly gather
  from any ore tile they stand next to into their own inventory
  (`timer` + `touch` + `give_item`) -- the "worker" and "soldier" roles
  from the request, authored as ordinary brain rows rather than any new
  engine-level unit type. Build mode (already generic, any game) is how
  you'd wall the camp in — a buildable `wall` kind (count 0, solid,
  placeable) is included for exactly that. Recruiting/dismissing is
  bound to `e`/`r` while touching a companion. No new UI: this plays
  through the existing terminal menus (`python3 spark.py`) and
  world3d.html exactly like any other Spark game.

  `tests/check_lead.py` (11 checks) and `tests/lead.test.js` (13
  checks, same cases) cover the new tiles directly, the way
  `check_harvest.py`/`harvest_tiles.test.js` already do for
  `give_item`/`has_item`/`harvestable` -- deliberately not folded into
  `check_engines.py`'s shared snapshot harness, same reasoning as that
  file's own long comment gives. `games/outpost.json` itself, though,
  needed no new test file at all: `check_engines.py` already discovers
  every game under `games/*.json` and replays it seeded in both
  engines, so it started covering `outpost`'s own recruiting, chasing,
  gathering, and its "chance"-driven random wander automatically,
  confirmed bit-for-bit identical between the two engines across four
  seeds. Also validated by loading and stepping it directly (500 ticks,
  several seeds, no crashes) and via `spark.py play games/outpost.json`
  headless. Not seen running in either the terminal or world3d.html
  yet.

### Fixed

- **Text doubling on the terminal selection menu** — reported directly
  ("text is doubling on termux selection menu first of spark"). The
  big-picture menu (`builder.menu()`'s arrow-key mode) redraws itself in
  place by moving the cursor up a fixed number of rows and overwriting
  them — correct only as long as every row it writes is exactly one
  physical terminal row. Two of the lines it always writes are wide
  enough to wrap on an ordinary phone-width terminal: the built-in
  control hint ("↑↓ move . enter pick . 1-9 jump . b browser . w who's
  here", 59 characters) shows on *every* menu, and the very first
  screen's own "learn how (guided, about ten minutes)" option (38
  characters plus the arrow) is wider still. Once a line wraps, the next
  redraw moves the cursor up one row too few and overwrites only part of
  the previous render — the untouched leftover sits next to the new
  render, which reads as the reported doubled text. Fixed with a new
  `_fit()` that truncates (with a trailing "…") every line `_render_menu`
  prints to the real terminal's own current width first, so none of them
  can wrap regardless of how long an option's label is or how narrow the
  screen is.

  `tests/check_menu.py` extended (+1 case): a narrow (32-column) real pty
  with a deliberately long option label, checking that no rendered row —
  ANSI styling and the pty's own `\r` stripped back off first — is ever
  wider than the terminal actually is. Confirmed this fails against the
  unfixed code (with exactly the two wide lines named above) before
  confirming it passes fixed. Validated with `python3 -m py_compile` and
  the rest of the existing suite, all green.

### Added

- **Portrait and landscape now keep their own remembered button
  arrangement, not one shared between them** — requested directly,
  right after the position-drift fix below: "one [preset] for each
  screen rotation." Nothing new to press for this: every existing "drag
  a button" already saved into `buttonLayout`; that's now one of two
  objects (`allButtonLayouts.portrait`/`.landscape`), and dragging just
  writes into whichever the device is in *right now*. Rotating swaps
  which one is active (`checkOrientationSwitch()`, called from the same
  `onResize()` the position-drift fix's own `syncButtonPositions()`
  already runs from, on a genuine orientation flip rather than every
  resize — Chrome's address bar sliding away, e.g., fires plenty of
  those within the same orientation) and resets every button to that
  orientation's own preset, or its plain default if nothing's been
  customized there yet — not the other orientation's arrangement
  recomputed against the new screen, which would be a different, wrong
  thing. A pre-existing save (one flat `{uid: entry}`, from before this)
  migrates into *both* once, so nobody's already-customized position
  silently vanishes the first time this runs; from there the two drift
  independently, same as any other button editor change. "Reset ALL
  buttons" now clears both presets, not just the one on screen (its
  confirm text says so); "reset this button" (singular) still only
  touches whichever orientation you're looking at, on purpose — the
  narrower reset for anyone who wants that instead.

  `tests/button_position.test.js` extended (+13 checks, 30 total): a
  rotation swaps to the other preset (not carrying the first
  orientation's customization over, and not losing it either — it's
  still there on rotating back), a same-orientation resize is a no-op
  (same object, not needlessly reset), and the old-save migration
  copies into both as two genuinely separate objects, not one shared
  reference. Validated with `node --check`, a full `html.parser` pass,
  and the full existing suite, all green. Not seen on a real screen yet.

- **A button's properties are their own full page now, opened and closed
  explicitly** — requested directly: "make close and open for full page
  properties article of button editor." Tapping a row in the
  button-picker list still selects that button, and now also opens a
  dedicated sub-page over the list — its own titlebar (`‹` back, plus a
  `✓ done` on the page itself) covering the size/opacity fields, the
  exact x/y position and "go to," the grid size, and "hide this panel
  while dragging," the same `.modal-titlebar`/`.modal-back` sub-page
  pattern the Object Inspector and Mesh Creator already use, rather than
  those fields sitting exposed in the box alongside the picker list all
  the time. Closing (`‹`, or the page's own done) never deselects —
  reopening (tap the same row again) picks up exactly where that left
  off, same as leaving and returning to any of Inspector's own sub-pages
  does.

  `tests/button_position.test.js` extended (+6 checks, 36 total):
  refuses to open with nothing selected, opens and titles itself
  correctly for a real one, closing hides it without clearing the
  selection, and reopening after a close works again. Validated with
  `node --check`, a full `html.parser` pass, and the full existing
  suite, all green. Not seen on a real screen yet.

### Changed

- **The button editor's own panel is eight big buttons plus a box now**,
  the same "buttons plus a box" shape every other modal in this file
  already uses, requested directly ("make the whole thing 8 buttons...
  scroll the large 8 button formation"). Done editing, grid lock, pick
  on screen (new, see below), size −10%/+10%, reset this button, reset
  ALL buttons, and save layout as… are the eight; the button-picker
  list, the exact size/opacity/position fields, the grid size, and the
  saved-layouts list all live in the box, scrolling in the same
  portrait-2-column/landscape-3-column formation the other modals'
  button grids already do. Grid lock changed from a checkbox to a
  button+state pair (matching Properties' own grid-lock button exactly)
  to fit the new shape; every other field kept its id, so nothing about
  how they're read or written changed underneath.

  **New: 👆 "pick on screen"**, requested directly right after ("a new
  button... to hide editor page while editor is yet enabled to select
  any button on screen than show only meter and text box for button
  properties"). Hides the full panel — the same way ✎ itself already
  can — but unlike a plain hide, keeps a small floating readout
  (`#edit-mini`, deliberately outside `#edit-panel` so it can stay
  visible while that panel is hidden) in sync with whatever gets
  selected next: a size meter, an opacity box, and the button's own
  label — so tapping around the screen to check or nudge several
  buttons doesn't mean reopening the full panel each time. ✎, or the
  readout's own small ✎, leaves pick mode and brings the full panel
  back; "done editing" leaves it too, along with edit mode itself.

  `tests/button_position.test.js` extended (+7 checks, 17 total): the
  readout tracks the selected button's real saved size/opacity, says so
  rather than showing stale data with nothing selected, does nothing
  at all while pick mode is off, and `exitPickMode()` genuinely turns
  both the mode and the readout off. Validated with `node --check`, a
  full `html.parser` pass, and the full existing suite, all green. Not
  seen on a real screen yet.

### Fixed

- **A customized button's position drifted to the wrong spot on rotating
  the phone between portrait and landscape** — reported directly ("all
  buttons are shifting to incorrect screen position"). The button
  editor's saved positions were a fixed *pixel* offset from wherever a
  button's plain grid/flex position happened to be at the moment it was
  dragged — fine as long as the screen never changed shape afterward,
  wrong the moment it did, since several of these layouts aren't just
  smaller/larger versions of each other (the pad's own `#controls`
  switches from centred to right-anchored between orientations, e.g.):
  the same fixed pixel offset landed on top of a completely different
  starting point. `buttonLayout` entries now store `xPercent`/`yPercent`
  — a target position as percent of the *viewport*, the same numbers "go
  to x%, y%" already showed — and `applyButtonStyle()` recomputes the
  actual pixel transform fresh every time: momentarily clear whatever
  transform is already there, measure the button's real plain position
  with `getBoundingClientRect()`, then set exactly the offset needed to
  reach the saved percent from there. `clampToScreen()`/
  `snapElementToGrid()` simplified to match — clamping/snapping the
  percent directly instead of computing pixel deltas. New
  `syncButtonPositions()` re-applies every saved position on
  resize/orientationchange (the same events the camera's own re-framing
  and `syncBarHeight()` already listen for), so a button doesn't wait
  for its next drag to land back in the right place. An old save with
  only the previous pixel `dx`/`dy` (no `xPercent`) is treated as having
  no custom position at all rather than migrated forward — that data was
  already wrong for at least one orientation, so there was nothing
  correct in it worth preserving; the button just returns to its plain
  position, ready to be repositioned properly. `tests/button_position.test.js`
  (new, 10 checks) simulates the actual bug: a saved position, then a
  resize *and* a changed plain position (not just smaller/larger, a
  different layout, matching what an orientation flip really does),
  confirming the button lands at the same percent afterward — the case
  that was broken before this. Validated with `node --check`, a full
  `html.parser` pass, and the full existing suite. Not seen fixed on a
  real screen yet.

### Added

- **👁: one button that hides every other button and panel on screen at
  once, for an unobstructed view of the world.** Requested directly. Its
  own small always-visible control (top right, below the bar) — not
  itself draggable, so it can never be the one thing that gets lost or
  hidden — toggling a `body.ui-hidden` class that hides the top bar, the
  pad, the drawer, the quickbar, the HUD/say text, the minimap, and the
  Harvest panel all at once via CSS. Tap it again, same button, to bring
  everything back. Not a persisted preference: always starts shown again
  on the next visit, rather than a reload looking like every button
  vanished for no reason. Disabled (like everything else in the top bar)
  while the button editor owns taps.

- **💬 Chat, talking to the exact same `api/chat` the browser editor's
  own box already uses.** Requested directly, with text commands. One
  shared chat per hosted game — chat rides along with the same world
  snapshot `poll()` was already fetching for everything else, so this
  needed no polling of its own, just reading `liveSnapshot.chat`
  (`showNewChat()`, deliberately mirroring index.html's own function of
  the same name and job). `LIVE` mode only, the *opposite* of every
  other panel in this file (all local-play-only) — a local, single-tab
  copy of the game has nobody else in it to talk to, so opening it
  without a live game just says so rather than pretending to work.
  `/who` (who's connected), `/clear` (empty the log), `/help` — a
  smaller command set than the browser editor's own box, since there's
  nothing here for `/play` or `/editor` to navigate to; anything else
  typed is said to the others, the same `/word` parsing as index.html's
  `runSaid`. `tests/chat.test.js` (new, 10 checks): the dedup logic
  (never shows your own line twice, only lines newer than the last one
  seen) and the command dispatch (each command, an unknown one, and
  plain text routing to chat instead), against the same kind of stub
  DOM/fetch this file's other JS tests already use. Validated with
  `node --check`, a full `html.parser` pass, and the full existing
  suite. Not seen running against a real server from this tab yet.

- **`draw_line`: a new tile that draws a real beam between two targets,
  used to connect the harvester and whatever they're harvesting for the
  length of the countdown.** Requested directly, after harvesting itself:
  "draw a line from one target to another, then use that during the
  harvest." `draw_line` (DO, both engines) takes `start`/`end` (each
  self/it) and a colour, and appends `{x1,y1,z1,x2,y2,z2,color}` to a new
  `world.lines` — cleared at the top of every tick (`World.step()`), so a
  line only keeps showing for as long as whatever's drawing it keeps
  asking every tick; there's no separate "stop drawing" tile, the same
  way a `say` line just stops when nothing sets it any more. Python
  carries `world.lines` but never draws from it (same reasoning as
  shape/size); world3d.html's new `pushLine()` renders each one as an
  actual thin oriented 3D box between the two points — not an
  axis-aligned box like `pushBox`, so it builds its own little basis
  (two axes perpendicular to the line) rather than reusing the shared
  `FACES` table the other shapes do, same flat-face-normal low-poly
  look throughout. A third `Renderer` buffer (`lineBuf`, alongside the
  existing floor/things ones) costs nothing extra to draw, since
  `draw()` already looped over a list of `[buffer, count]` pairs.

  The Harvest panel now draws exactly this line between the harvester
  and their target for as long as a harvest is in progress — pushed
  into `world.lines` every rendered frame rather than through the tile
  (it's driven by a real-time countdown, not a WHEN/DO row), but
  rendered through the exact same path. `world.step()` clears the list
  once a tick; `frame()` runs far more often than that, so the line
  keeps reappearing well before a clear could ever leave a visible gap.

  Validated the same way as harvesting: `tests/check_draw_line.py` (5
  checks, Python) and `tests/draw_line.test.js` (8 checks, JS — 3
  matching the Python cases, plus 5 checking `pushLine()`'s own
  geometry: vertex count, that every number is finite, that every
  normal is unit length, that coincident endpoints produce nothing
  rather than a degenerate box, and that a straight-up line — the one
  case where the "up" reference used to build the cross-section would
  itself be parallel to the line — still comes out valid). Deliberately
  not wired into `check_engines.py`'s shared snapshot/parity harness,
  same reasoning as the harvest tiles. `node --check`, a full
  `html.parser` pass, and the full existing suite all green. The beam
  itself has not been seen on a real screen yet.

- **Harvesting: a new `harvestable` tile, an inventory (`give_item`/
  `has_item`), and a small panel in the 3D view that appears on its own
  whenever you're standing next to something harvestable.** Requested
  directly, using `games/Game 008008.json`'s pink cones (previously an
  instant touch-to-mine) as the worked example.

  `harvestable` (DO, both engines) stamps `{item, amount, seconds,
  flashes}` config onto a Thing — what it gives, how many, how long the
  harvest takes, and how many times it flashes right before vanishing.
  That's the whole tile; running the actual wait/flash/give sequence
  once someone picks it is inherently an interactive, player-input flow
  (stand near it, choose it off a list, watch a countdown) rather than
  something a tick-driven WHEN/DO row can usefully express on its own —
  the same reasoning Build mode and the Object Inspector are already
  "local play only" for, so that half lives entirely in world3d.html.

  `give_item`/`has_item` (DO/WHEN, both engines) are the general,
  reusable half: each Thing keeps its own `{item: count}` inventory —
  deliberately its own field, not built on top of `remember`/`recall`
  (a single value shared by the *whole world*, wrong the moment two
  players are in one game and each needs their own count). `give_item`
  adds (or, with a negative amount, removes, floored at zero) some of a
  named item on `self`/`it`; `has_item` checks a count is at least some
  amount. Useful on their own too, not just from a harvest completing —
  a chest a key opens, say.

  The 3D view's own Harvest panel appears automatically (not opened
  from anywhere) the moment you're within reach of ≥1 harvestable thing,
  listing each one; picking one switches the same panel to a countdown,
  ending in the target flashing (excluded from that frame's render on
  its "off" phases, the same trick the merge-selection rings already
  use for a blink) the configured number of times, then vanishing while
  the item lands in your inventory. Walking out of reach mid-harvest
  cancels it, no partial reward. A new, deliberately simple **Inventory**
  panel (📦, in the button drawer) shows what you're actually carrying —
  a plain read-only list, not the six-buttons-plus-a-box shape the other
  modals share, since there's nothing here to act on besides looking.
  Kept separate from the existing Backpack on purpose: Backpack is a dev
  tool for saved buttons/notes, unrelated to anything a *game* means by
  "carrying an item," and conflating the two would have confused both.

  `games/Game 008008.json`'s cones now carry `"harvest": {"item": "pink
  metal", "amount": 10, "seconds": 5, "flashes": 4}` directly in their
  template (equivalent to the tile, just authored straight into the
  JSON since the cone has no brain rows of its own) in place of the
  hero's old "touch cone → score +5, vanish, say mined iron ore!" row,
  which is removed — walking into one no longer does anything by
  itself; standing near it does.

  Validated three ways: `tests/check_harvest.py` (14 checks, Python) and
  `tests/harvest_tiles.test.js` (15 checks, JS) run the same cases
  against each engine's own implementation directly — deliberately
  *not* wired into `check_engines.py`'s shared snapshot/parity harness,
  which compares a fixed, hand-picked set of Thing fields between the
  two engines; extending that shape is its own, riskier change to a
  delicate piece of shared test infrastructure, so each engine gets
  checked against the same cases in its own dedicated test instead —
  not the same mechanism, but the same goal, catching either engine
  quietly drifting from what the other one does. Plus `python3 -m
  py_compile`, `node --check`, a full `html.parser` pass, loading
  `Game 008008.json` through `engine.brain.load`/`engine.world.World`
  and stepping it, and the full existing suite, all green. The panel
  itself, its countdown, and the flash have not been seen running on a
  real screen yet.

### Changed

- **The two thumb-zone pads (`#pad-move`/`#pad-actions`) merged back into
  one combined pad, rearranged** — requested directly, with an exact,
  specific layout: read left to right, top to bottom, ⟲ (flip shape), ●
  (space/jump), + (resize) along the top row; ⤓ (fly down), ▲ (up), ⤒
  (fly up) in the middle, putting the two fly keys either side of the
  movement up-arrow, directly under space; ◀ (left), ▼ (down), ▶ (right)
  along the bottom. All nine `data-key` values unchanged throughout, so
  saved button-editor layouts keep matching by key regardless of which
  pad formation they were saved under. `--pad` (the shared size
  variable) went back to its original single-pad share,
  `min(94vw, 50vh, 460px)`, since one pad has the screen to itself
  again rather than splitting it with a second one; `#controls` went
  back to centring it (`justify-content:center`) instead of
  `space-between`. The button editor's own list groups these nine uids
  under one "pad" heading again too (`EDIT_GROUPS`), not the two
  "pad (move)"/"pad (actions)" headings the split briefly needed —
  `tests/edit_groups.test.js` updated to match. Validated with
  `node --check`, a full `html.parser` pass, and the full existing
  suite; not seen on a real screen yet.

- **The button drawer moved 8px in from the true left edge of the
  screen (and picked up fully-rounded corners to match)** — requested
  from a real phone. It used to sit flush at `left:0`, which is not
  just an awkward reach right in the corner but can also land in the
  strip of the screen a phone's own edge-swipe gesture (Android's
  gesture-nav back swipe, e.g.) claims for itself before a web page
  ever sees the touch. Inset to the same 8px margin every other
  floating panel in this file already uses (`#hud`/`#say`/`#minimap`),
  `env(safe-area-inset-left)` added on top for a phone that has one.
  The closed-state slide math (`-100% + var(--util)`) is relative to
  the drawer's own width either way, so the collapsed sliver is still
  exactly the tab's own width, just starting 8px in instead of flush
  against the edge. The tab's border-radius went from rounded-on-the-
  right-only (which made sense flush against the edge, not floating
  clear of it) to rounded on all four corners, matching the tab; a 6px
  gap now separates the tab from the bubbles panel when open, since the
  two are independently rounded floating pieces now rather than one
  flush block.

- **✎ now shows/hides the button editor's own panel once already
  editing, instead of only ever turning the whole of edit mode on or
  off.** Requested from a real phone: tap ✎ to enter edit mode as
  before, but a second tap no longer leaves edit mode entirely — it
  just closes the panel (dashed outlines, selection, and dragging all
  stay active), and the same button, top right, brings it straight back
  open without losing your place. Actually leaving edit mode moved to a
  new "✓ done editing" button at the top of the panel itself. Shares its
  visibility flag with "hide this panel while dragging" (`updateEditPanelVisibility()`,
  reconciling the two so neither can clobber the other — ending a drag
  no longer reopens a panel closed manually first, and closing it
  manually survives the next drag starting and ending).

- **The button editor's list now groups every editable button/bubble/
  slot under a numbered "button group 001", "002", … heading**, instead
  of one flat list of everything on the page — the pads, the top bar,
  the button drawer, and the quickbar each get their own, gathered by
  matching each entry's uid (`EDIT_GROUPS`) rather than relying on
  whatever order they happened to register in, so a drawer bubble added
  or removed can't shuffle a later group's numbering. Anything that
  matches no known group (there is nothing that currently doesn't,
  short of a future button nobody's added to the list yet) falls into a
  final "other" group rather than vanishing or crashing.
  `tests/edit_groups.test.js` (new, 41 checks): every real uid in the
  app lands in the group a person would expect, an unrecognised one
  falls into "other", and no uid matches more than one group.

### Fixed

- **A button could be dragged (or end up saved) off the edge of the
  screen with no way back to it except knowing about the button
  editor's own `#edit-list` workaround** — reported from a real phone,
  the button drawer specifically. `buttonLayout` entries (the saved
  `dx`/`dy` a button's own drag leaves behind) had no bound on them at
  all — a drag that ended near an edge, a screen rotated or resized
  after a position was saved, or anything else that shifted a button's
  effective position could leave it wholly past a screen edge, unable
  to be tapped again short of "reset all buttons" (which throws away
  every other customization too, not just that one button's). New
  `clampToScreen()`: after any drag, and once on every load for every
  registered button, keeps at least a 24px margin of it on screen by
  correcting `dx`/`dy` (and re-saving the correction, so it does not
  need re-earning on the next reload) rather than only offering a way
  to *find* an off-screen button after the fact. The drawer's own tab
  isn't itself draggable (only its bubbles are, individually) — if this
  turns out not to have been the actual cause, worth a follow-up with
  more specifics about what was seen.

- **A mental playthrough of the 3D view's controls, tool by tool, turned
  up three more ergonomic gaps beyond the compass fix below — fixed all
  three, not just written down:**

  1. **Both thumb-zone pads had dead zones.** `.pad` (the shared grid
     both `#pad-move` and `#pad-actions` sit in) had `pointer-events:auto`
     on the whole 3×3 grid, not just its buttons — and neither pad fills
     all nine cells (pad-move uses 4, pad-actions 5). A swipe starting in
     one of the empty cells was swallowed by the grid instead of passing
     through to turn the camera, contradicting the file's own stated
     design ("the empty space around the pad still passes a swipe
     straight through"). Moved `pointer-events:auto` onto `.pad button`
     itself; the empty cells fall through correctly now.

  2. **`#quickbar` and the button drawer's tab could end up under the
     HUD.** Their 245px/250px top offsets were budgeted against the
     HUD's size *at the time they were written* (a real number, but a
     guessed one) rather than measured — the same kind of guess that
     already broke for `#hud`/`#say` and the compass above once
     something upstream changed and nobody remembered to bump these
     too. `syncBarHeight()` (already added for `--bar-h`) now also
     measures `#hud`/`#say`'s real bottom edge into a `--hud-bottom`
     custom property, re-measured on resize/orientationchange and
     whenever the HUD's own line count changes (score/health/tick, plus
     an optional "near" line) — `#quickbar`/the drawer's `top` is now
     `max(245px/250px, --hud-bottom + 8px)`, so a HUD grown taller than
     the original budget expected pushes them down instead of sitting
     under it unnoticed.

  3. **Merge (🧬) armed was invisible once you closed the drawer, and
     wasn't cancelled by closing it either — inconsistent with Remove
     (🗑), which is both.** Tapping 🧬 to arm it, then closing the
     drawer without tapping 🧬 again, left `mergeArmed` silently true:
     the *next* object tapped anywhere would still queue for merging
     instead of opening the Inspector, with only a small green ring (if
     any objects were already queued) to explain why. Fixed two ways:
     closing the drawer now cancels an armed merge the same way it
     already cancelled an armed remove (a plain reset, not
     `toggleMerge()` — that would try to *complete* the merge instead of
     cancel it); and while the drawer is open, the 🧬 bubble itself now
     pulses (a new, generalized `.bubble.armed` style, reusing remove's
     existing `.control.remove.armed` pulse *idea* without redefining
     its red colouring) for as long as `mergeArmed` is true, the same
     immediate feedback Remove's own bubble already had and Merge did
     not.

  All three found and fixed by reasoning through the actual DOM/CSS/JS,
  not from a screenshot — validated with `node --check` and a full
  `html.parser` pass; not one of them has been seen working on a real
  screen yet.

- **The compass overlapped the top bar's title/badge in portrait (and
  landscape) — it sat at a flat 8px from the top of the screen, which
  was only ever clear of the bar while the bar had a single row.** Once
  the bar grew a second row of buttons (`#side-tools`) nothing moved the
  compass to match, so it rendered directly on top of the title and
  badge instead of below everything, on every phone, in both
  orientations. This is the *same class of bug*, not a new one, as the
  `#hud`/`#say` fix already documented below (104px → 160px when the bar
  grew that second row) — except the compass never got the equivalent
  fix at all. Rather than add a third guessed pixel constant to a chain
  that has now broken twice, the compass moved into `#bar`'s own flex
  column as a real third row (`align-self:center`, sized the same as
  before) instead of floating independently at a hardcoded offset — it
  cannot drift out of sync with the bar's real height again, the same
  reason `#side`/`#side-tools` already don't. `#hud`/`#say` (which now
  also have to clear the compass, being below it) switched from another
  guessed constant to a real one: a new `--bar-h` CSS variable, kept
  current by a `syncBarHeight()` measurement (`#bar`'s own
  `getBoundingClientRect().height`) on load and on every
  resize/orientationchange — the exact same events the camera's own
  re-framing already listens for. Whatever the bar grows to next, this
  follows it automatically instead of needing another manual bump.
  Validated with `node --check` and a full `html.parser` pass; the exact
  pixel result is one more thing worth confirming on a real screen,
  though the reasoning (and the arithmetic behind the fallback constant)
  was checked by hand against the bar's actual rendered content.

### Added

- **The button editor (✎) can now hide itself for the length of a
  drag.** A new checkbox, "hide this panel while dragging a button" —
  on by default — in `#edit-panel`. The panel covers most of the screen
  (it's inset 6vh/6vw), which is exactly what got in the way of seeing
  where a button actually lands relative to everything else while
  dragging it into place. With it on, the panel (not button-editor mode
  itself — the dashed outlines, the selection, all of that stays active)
  disappears the moment a drag starts and comes back the moment it ends,
  via a `.peeking` class toggled in the same `pointerdown`/`endDrag`
  handlers `registerEditable()` already had — the drag itself keeps
  working underneath the whole time, since pointer capture is on the
  button being dragged, not on the panel. Turning off button-editor mode
  entirely while mid-drag (shouldn't happen, but) clears `.peeking` too,
  so it can never get stuck hidden. Persisted the same way grid-lock
  already is, in the same `spark3d-editor-settings` localStorage entry.
  Validated with `node --check` and a full `html.parser` pass.

### Changed

- **The 3D view's five modals — Backpack, Properties, Mesh Creator,
  Build/palette, Object Inspector — are all one shared shape now: up to
  six large buttons filling most of the screen, with a box off to the
  side for whatever those buttons don't cover.** The same "six panel
  buttons besides a box" formation the browser editor's own deck has
  always used (see README's "How it sits on the screen"), reused here
  since world3d.html is a separate file with nothing to import it from —
  new shared CSS (`.mgrid`/`.mkeys`/`.mbox`, `.modal-titlebar`,
  `.modal-back`) rather than five different bespoke layouts.

  **Backpack** was a deliberate exception to the game's own gray/light-
  blue theme, styled like Windows File Explorer (see CLAUDE.md's old
  "design preference" note) — folded into the same shell and theme as
  the rest now, on request, a real reversal of that note, not theme
  drift rediscovered. Its four toolbar actions (up/new folder/new item/
  delete) became the big buttons; the breadcrumb and file grid moved
  into the box.

  **Properties** turned grid-lock and minimap into toggle buttons and
  the move-speed slider into ±1/±5 quick-jump buttons; the world clock
  and an exact typed speed value live in the box.

  **Build/palette** turns every placeable kind into a big button itself
  (scrolling, the same "however many there are" idea README already
  documents for the browser editor's own big lists — the tile palette,
  there — not a new pattern); the search field that filters them moved
  into the box, and 🧩 (open the Mesh Creator) became a small icon next
  to the title.

  **Object Inspector and Mesh Creator** both grew real sub-pages now,
  reached from a `‹` back button next to the title (same idea as
  index.html's own `#backkey`): Colour and Shape are each their own
  scrolling page of swatches/shapes (one `choiceKeys()` helper shared by
  all four of these — two Inspector pages, two Mesh Creator ones —
  rather than writing the same picker four times), and the Inspector
  further splits Resize/Stretch/Move into their own pages too, each with
  a handful of quick-jump/nudge buttons (50-300% presets for resize, ±25
  stretch nudges per axis, ±1 move nudges per axis) *alongside*, not
  instead of, the exact sliders and typed number fields — those moved
  into the box rather than being replaced, so no precision was lost
  anywhere converting continuous controls into buttons. The Mesh
  Creator's live preview canvas stays mounted across every page switch
  rather than being torn down and rebuilt each time, since a WebGL
  context is not cheap to recreate on every tap.

  Fixed as a side effect of rewriting every modal's markup anyway:
  `#mesh-titlebar` and `#mesh-body` used to be duplicate ids shared
  across three different modals (Mesh Creator, Build, Object Inspector)
  — invalid HTML, though harmless since nothing ever queried them by id.
  Every modal has its own unique ids now.

  Verified with `node --check` on the extracted script, a full
  `html.parser` pass, and a new `tests/modal_pages.test.js` (29 checks)
  driving the actual page-navigation, `choiceKeys()`, and quick-button
  machinery against a stub DOM — not just the pure-function style
  `mesh_merge.test.js` already had, since this changeset's risk is
  mostly in the DOM/event wiring, not arithmetic. Caught one real bug in
  the process — a test fixture missing `world.templates`, not app code,
  but exactly the kind of thing that would have gone unnoticed without
  actually exercising this code at all. Full existing suite (engines,
  menu, deck, store, mesh-merge) stayed green. This is the largest
  changeset this project has shipped without real eyes on a real screen
  yet — worth a careful look on-device before building further on top of
  it. See CLAUDE.md's task note for the full design rationale.

### Fixed

- **The button drawer's bubble list could run off the bottom of the
  screen with no way to reach the buttons that fell past the edge** —
  reported from a real phone. It was a plain vertical column with no
  height limit at all; six built-in bubbles plus whatever you'd added
  with the + control (each `--util`-tall, gap 10px) could add up to more
  than a shorter screen actually had room for below the drawer's fixed
  top offset (250px + the safe area), and the last few — sometimes the
  +/× controls themselves — ended up positioned off-screen, not just
  visually cramped. Fixed by capping `.bubbles`' height to what is
  actually left below that offset and turning on `flex-wrap` at the same
  time: once a column reaches the cap, the next bubble starts a new
  column to the right instead of continuing to add to a column that's
  already run out of room. flex-wrap moves a whole bubble to the next
  column rather than ever slicing one in half, so nothing renders
  partially cut off either — every bubble stays a complete, separate
  circle, just arranged in more columns when there isn't room for one
  long one. `max-width` plus `overflow-x:auto` on the same element is a
  fallback for a pathological number of custom bubbles that would need
  more columns than even a wide phone has room for — scrolls sideways
  rather than running off the *right* edge instead of the bottom.
  Validated with `node --check` and a full `html.parser` pass; not
  seen on a real screen yet, same caveat as the pad split below.

### Added

- **The 3D view's on-screen controls are two pads now, not one — a
  thumb-zone split.** Previously ▲▼◀▶, ⟲, +, ●, ⤓, and ⤒ all shared a
  single 3×3 block centred at the bottom of the screen. Now `#pad-move`
  (▲▼◀▶, a plus shape) sits at the bottom-left corner and `#pad-actions`
  (⟲ + ● ⤓⤒, the same corners-and-centre arrangement the combined pad
  used to have) sits at the bottom-right — `#controls` switched from
  `justify-content:center` to `space-between` to push them apart. Point
  is reach, not just tidiness: each pad now lands directly under whichever
  thumb is already resting near that side of the phone, instead of both
  hands needing to meet in the middle for every control.

  Both pads share one `.pad` CSS class (was `#pad`); which of the nine
  grid cells each button occupies is now spelled out with
  `grid-template-areas` per pad rather than relying on DOM order, since
  each pad only fills 4 or 5 of its 9 cells and leaves the rest empty.
  Every button kept its original `data-key`, so the button editor's saved
  positions (keyed by that string) still match up with no migration.
  `--pad` (the shared size variable) dropped from `min(94vw, 50vh, 460px)`
  to `min(40vw, 46vh, 230px)` in portrait — under half its old share, since
  two pads now split the width a single one used to have entirely to
  itself; landscape's own override shrank from a 420px cap to 230px for
  the same reason, keeping the 46vw share it already used.

  Validated with `node --check` on the extracted script and a full
  `html.parser` pass — this is a pure layout/markup change, no gameplay
  logic touched, so `tests/check_engines.py` and the merge/deck/store
  suites all stayed green as expected without needing new cases of their
  own. Not seen on a real phone screen yet — the exact --pad numbers above
  are a first pass, worth a look and a tweak on-device.

- **Merge (🧬, in the button drawer): combine several separately-placed
  objects into one new placeable kind, in the 3D view.** Arm it, tap
  objects one at a time — each gets its own green ring — tap 🧬 again to
  combine everything queued (asks for a name and a glyph, the same
  prompts the Mesh Creator's own "save as new kind" already uses). Each
  selected object becomes one or more `parts` — its own shape, colour,
  and the exact width/height/depth `buildThings()` would actually render
  it at (`effectiveDims()`, pulled out of `buildThings()` so both use the
  identical numbers) — offset from whichever was tapped first. An object
  that's already itself a merged/mesh-creator shape contributes its own
  parts individually rather than being flattened into one opaque box, so
  merging a merge stays composable.

  **Removing the inner geometry**, honestly scoped: real CSG — cutting
  the polygons where two solids actually overlap — is a much bigger
  undertaking than this hand-rolled low-poly renderer is set up for, and
  too risky to ship unverified (no headless WebGL here to render a frame
  and look). What it does instead, correct and cheap: any part whose
  entire bounding box sits inside another part's is dropped outright
  (`dropHiddenParts`) — it could never be seen from outside an opaque
  shape, so its triangles were only ever costing polygons for nothing.
  Parts that only partly overlap keep their full geometry; ordinary depth
  testing already draws the visible result of that correctly, the same
  as it always has for any two overlapping opaque objects, merged or not.

  `tests/mesh_merge.test.js` (new, 17 checks): the merge arithmetic
  itself — offsets, the fully-contained-part-dropped case, a part that
  only partly overlaps surviving, an exact duplicate pair collapsing to
  one instead of zero or two, and composing an already-merged object.
  Closes the task noted in CLAUDE.md on 2026-09-02.

  Local play only, same reasoning as Build mode and the Inspector: it
  spawns into and removes from the live World object directly, which
  only exists for the copy of the game running in this browser tab.

- **Four new shapes, ten new colours, and a second way to resize —
  stretching one axis at a time instead of only uniformly.**

  **Shapes**, cube/sphere/cone joined by **cylinder, pyramid, wedge, and
  octahedron** — four more low-poly, flat-shaded `push*()` functions in
  world3d.html, same hand-computed-normal approach as the existing cone and
  sphere. The pyramid's base lines up with a cube's own footprint on
  purpose (a `SIDES=4` cone would put its corners at the box's edge
  midpoints instead, a diamond, not a square); the wedge is a ramp or a
  mono-pitch roof, full height at one end tapering to nothing at the
  other; the octahedron is a gem, two four-sided pyramids base to base.
  The `shape` tile now **cycles** through all seven instead of only
  flipping cube ↔ sphere (`engine/world.py` and world3d.html both carry
  the same `SHAPES` list, in the same order, so it cycles identically in
  either engine even though only the 3D view can show the result). Both
  the Mesh Creator and the Object Inspector's shape pickers are now built
  from that one list too, so a shape added there only needs adding once.

  **Colours**, nine joined by ten more: orange, purple, brown, black,
  lime, teal, navy, maroon, gold, silver. Real, distinct RGB in
  world3d.html's `COLOR_RGB`/`COLOR_CSS`; the terminal's `COLORS` (ANSI
  has only sixteen codes to work with) gives several of them the nearest
  existing code rather than a colour of their own — the terminal's
  render() was always an approximation, only the 3D view and the editor's
  own swatches show the real thing.

  **Stretching**, alongside the existing uniform `resize`: a new
  `stretch` tile changes width, height, or depth on its own, leaving the
  other two exactly where they were. Backed by three new optional fields
  on `Thing` — `sx`/`sy`/`sz`, percent like `size`, `None`/`undefined`
  meaning "use size" until something stretches that axis specifically
  (carried on both engines' `Thing`, same as `parts`, even though only
  world3d.html draws the result). `resize` (and the Inspector's own size
  slider) clear all three back to matching the new size — deliberately:
  the whole object changing size is exactly the moment an earlier
  one-axis stretch should stop applying, not stack silently underneath a
  new baseline. A round shape (sphere, octahedron) still defaults its
  height to match its own width, staying round when unstretched, unless
  `sy` is set explicitly — which is exactly how you'd deliberately turn
  one into an ellipsoid or a squashed gem.

  **Controls**: the Object Inspector gained three sliders — width,
  height, depth — wired straight to `sx`/`sy`/`sz`, plus a "reset stretch
  to size" button. Duplicating an object now carries its stretch over
  too, the same as it already did for colour, shape, and size.

  Verified computationally rather than by eye (no headless WebGL here to
  render an actual frame): every new `push*()` function's output checked
  for the right vertex stride, whole triangles, finite numbers throughout,
  and unit-length normals, with real (if arbitrary) box dimensions.

- **Fixed a real corruption bug in the big-picture menu**, caught by
  deliberately testing the app's largest menu (the tile picker, up to 40
  options) against MANUAL.md's own stated minimum terminal size (20 rows).
  It used to print every option at once regardless of how many there were
  or how short the terminal was; once that first render alone overflowed
  the screen, cursor-up could never get back above row 1 (a terminal will
  not scroll back into content it has already discarded), so every redraw
  after that wrote over the wrong lines. `menu()` now shows only as many
  options as actually fit, scrolled so the highlighted one stays in view,
  with a `(N/40)` counter in the footer when it's scrolled at all — fixed
  window size for the whole menu, so the cursor math this all depends on
  never drifts. `tests/check_menu.py` gained a permanent regression case
  for exactly this: a 40-option menu on a 20-row pty, wrapping past both
  ends twice, checking every redraw moves the cursor by the same amount.

- **Three small follow-ups to the big-picture menu, from auditing it right
  after building it:**

  - `SPARK_PLAIN=1` opts out of the big-picture menu even on a real
    terminal — for a terminal that answers `isatty()` with yes but doesn't
    actually handle this cleanly (some SSH clients, some IDE terminal
    panes), or simply a preference for typing numbers.
  - `tests/check_menu.py` (new): drives the terminal's menu through a real
    pseudo-terminal — arrow keys, a digit jump, escape/`0` for back, the
    title screen through to the editor and back, `SPARK_PLAIN` — plus the
    piped-input fallback. None of this had permanent coverage before; it
    had only been checked by hand while building it.
  - `tests/deck.test.js` gained a guest-mode pass: presses every barred
    button on the new title screen and editor screen as a guest, and
    checks each one actually refuses (says so, doesn't run the real
    action) rather than just checking the buttons exist. Also new: no
    prior version of this file ever ran as a guest at all.

- **Fixed: `tests/check_permissions.py` left `games/index.json` stale.** It
  already deleted the temporary game file it made along the way, but never
  refreshed the listing that a save through the server (earlier in the same
  test) had already baked that file's name into — so running the test once
  left a permanent stale entry in the real `games/index.json`, naming a game
  that no longer existed. Fixed by calling `server.export_static()` after
  the cleanup, the same as the app's own "delete a game" path already does.

- **A big-picture menu in the terminal, and a title screen in the browser —
  both now a game menu first, an editor second.**

  In the terminal: a big **SPARK** logo, one option highlighted at a time,
  arrow keys to move and enter to pick — `engine/builder.py`'s `menu()`
  renders this on any real terminal, so all twenty-some screens in the
  terminal app get it for free, not just the main one. A digit still jumps
  straight to that option, and `b`/`w` are one-key shortcuts for opening the
  browser editor and listing who's connected. Wherever a real terminal isn't
  available — piped input, a script, an old terminal — it falls back on its
  own to the plain numbered list this always was; nothing here needs a tty
  to run (`engine/runner.py` gained `read_key()`, a blocking single-keypress
  reader with arrow-key decoding, alongside the existing non-blocking
  `Keyboard.pressed()` the play loop already used).

  The terminal's own main menu is restructured to match: a title screen
  (play it / editor / new game / open a game) instead of one long list, with
  everything that changes the game — characters, tiles, world settings,
  save, rename, GitHub, invite — moved one screen in, behind **editor**
  (`editor_screen()`, new).

  In the browser: the deck now opens on a title screen — **play, continue,
  new game, editor** — before the six buttons that used to be the whole
  deck (edit/characters/brain/tiles/save/3d world), which now live behind
  **editor** (`editorScreen()`, renamed from `homeScreen()`). **Continue**
  reopens whichever game you last had open (tracked in `localStorage` under
  `spark:lastgame`) and plays it; the same key now also makes the page's own
  boot sequence prefer your last game over just the alphabetically first one
  in the list. `/continue` and `/editor` join the box's existing commands.

- **Resized objects now scale their glyph label, selection ring, and tap
  target with them.** All three used to sit at a fixed, role-based
  height, so an object made taller through the Inspector or the Mesh
  Creator had its name floating well below where it visually stood, its
  selection ring sitting inside it instead of around it, and a tap near
  its actual top missing it entirely. `drawGlyphs()`, `drawSelection()`,
  and `pickObjectAt()` now all multiply that base height by the object's
  own `size / 100` before placing anything.

- **Housekeeping pass, no behaviour change:** four small blocks of CSS
  (translucent input backgrounds, button backgrounds, overlay text, and
  modal backgrounds) that were repeated 5, 3, 2, and 2 times respectively
  as literal `rgba(...)` values are now `--glass-input`, `--glass-btn`,
  `--overlay-text`, and `--modal-bg` custom properties on `:root`, used
  everywhere via `var(...)`. Caught and fixed before syncing: a first,
  purely mechanical find-and-replace pass had rewritten the `:root`
  definitions themselves into self-referencing `--glass-input:
  var(--glass-input);`, which is invalid CSS — the definitions keep their
  literal values, only the call sites use `var()`. Also added a table of
  contents comment at the top of the `<script>` block, since it has grown
  large enough that finding a given piece by scrolling is no longer
  practical.

- **The 3D view shows what's in touch range.** A "near: ..." line joins
  score/health/tick in the HUD whenever anything is within the same
  range-1 reach the `touch` sensor itself uses — so what's listed there
  and what a `WHEN I am touching {kind}` row can actually see always
  agree. Local play only, same reasoning as Build mode: it reads
  `world.things` directly, which only exists for the tab's own copy of
  the game.

- **Pink cones are iron ore, in `games/Game 008008.json`.** A `WHEN I am
  touching cone DO` row — score +5, the cone vanishes, "mined iron ore!"
  — the same WHEN/DO shape the apple-pickup rule in Game 001 already
  uses, not a new mechanic invented for this one game.

- **`games/Game 008008.json`** — a 200×200 "expanding" world: the floor
  loads in around wherever you are, in a moving window, instead of the
  whole board being built at once, and it generates 2-block-tall pink
  cones as new ground reveals itself. Two new general capabilities, not
  special-cased to this one game:

  - `world.expanding: true` on any game's world settings switches its
    floor to windowed loading — `Renderer.buildFloor()` takes an optional
    centre now, and re-centres on the player once they wander far enough
    (`frame()`'s `maybeExpandFloor()`). Every other game never passes a
    centre, so this changes nothing for anything that doesn't opt in.
  - `autoScatter: true` (+ optional `scatterChance`, default 0.3) on any
    character template gives it a chance to appear once per newly-loaded
    region, at a random empty cell in it. Which kind gets scattered is
    just data — Game 008008 makes it cones by putting the flag on the
    cone template, nothing about scattering itself knows what a cone is.

  Local play only, same reasoning as Build mode/the Inspector: it works
  by rebuilding the live `Renderer`'s own floor buffer, which only exists
  for the browser tab actually running the 3D view.

  **New shape: cone.** A third option next to cube/sphere everywhere
  shape already appeared — `pushCone()` (a low-poly cone, same flat-face-
  normal approach as the sphere), the Mesh Creator's part shape, and the
  Inspector's shape selector all got it.

  **New colour: pink**, added to `COLORS` in `engine/world.py` (which
  `tiles.json`'s colour list is generated from) and mirrored in
  `world3d.html`'s `COLOR_RGB`/`COLOR_CSS` — the usual two-engine pairing,
  even though this one's just a name and two numbers.

  **A real bug caught building this:** `buildSaveProject()` was
  reconstructing `world: {...}` from only `width`/`height`/`wrap`/`speed`
  — any *other* field on a world's settings, `expanding` very much
  included, silently vanished the moment you saved. Fixed by spreading
  the original settings first and overriding just the four that can
  actually change live.

  **A second one, caught right after:** nothing ever removed a scattered
  object once it existed, or forgot a chunk once it had scattered one —
  a long exploring session would just keep adding more things to
  simulate and render, forever. Fixed the same day: chunks (and whatever
  they scattered) more than 60 cells behind the player are now forgotten
  and removed; wandering back in re-scatters that ground fresh, same as
  it had never loaded.

- **Mesh Creator and Build mode.** The Mesh Creator (🧩) builds a custom
  shape out of several cube/sphere parts, each with its own offset, size,
  and colour, previewed live in a second WebGL view (the same `Renderer`
  the main 3D view uses — what you see is exactly what gets placed, not
  an approximation), and saves it as a new, immediately placeable kind.
  Build mode (🎨, in the button drawer) is a palette of every kind that
  exists — built in and anything just saved from the Mesh Creator — pick
  one to make the place tile (`a`) add that instead. A new 🗑 drawer
  bubble removes whatever placed object you're touching (`vanish`, on a
  new virtual `"remove"` key that no physical keyboard key sends).

  **Why the palette is local-play only.** It works by writing straight
  into the running JS `World` object's memory, which only exists for the
  copy of the game in this browser tab — a `LIVE` game mirrored from a
  real Termux server has no such object here to write into. The `place`
  tile still checks for it, though, so nothing breaks; the palette
  simply has nothing to affect in that mode, and quietly does nothing
  when opened there.

  **Why the pending-ghost lookup changed.** It used to also match on
  `kind`, so switching the palette while a ghost was still waiting to be
  confirmed would strand it — a new ghost of the newly-picked kind would
  start instead, invisible-ish and unconfirmable forever. Matching on
  ownership alone confirms whatever you already started, regardless of
  what the palette says now.

- **3D world editor: shapes, altitude, walking vs. flying, and a
  placeable object.** Characters can now be a sphere as well as a cube
  (`shape`), can be resized (`size`, a percent), and can change altitude
  (`fly` up/down, clamped 0–8) — but only while flying: a new
  `toggle_flight` tile (`d`) switches a character between walking
  (grounded, altitude locked to 0, `w`/`s` do nothing) and flying (free
  to change altitude). A new `place` tile (`a`) adds a full-size,
  see-through preview object where you stand; pressing it again on that
  same one confirms it, solid and opaque.

  **Why two presses to place something.** A single press that
  immediately drops a solid, opaque object gives no chance to see where
  it landed before it is already in the way. The see-through preview is
  the same object at the same spot, just not yet real — confirm it, or
  walk off and place a different one instead.

- **Camera follows you, not the board.** It used to sit back far enough
  to fit the whole board in frame, like a diorama seen from outside. Now
  it orbits at a fixed, close distance centred on whoever is playing,
  and moves with them — the world reads as a place you are standing in
  rather than a box viewed from outside. Swipe and pinch still control
  the angle and distance exactly as before, just relative to you instead
  of the board.

- **Low-poly, flat-shaded rendering**, and a full repaint of the 3D
  view's own colours — gray and light blue throughout (the floor, the
  rim wall, the sky/clear colour, every panel) — replacing the old
  near-black background and neon accents.

- **A button editor** (✎, top bar): select, drag, resize, and fade any
  button in the 3D view, including the button drawer's own bubbles.
  Position can also be typed directly as a decimal percent of the
  screen, and snapped to an optional visible grid; a scrolling list
  covers every button that exists, including ones dragged off-screen or
  faded to invisible, so nothing edited this way can get permanently
  lost. Whole arrangements can be saved under a name and reloaded later,
  on top of the one arrangement that is always kept live.

- **Backpack** (🎒, top bar): a small virtual file system — folders and
  files, New folder / New item / Delete — styled like Windows File
  Explorer on purpose, a deliberate exception to the 3D view's own
  colours (everything else still follows the gray/light-blue palette
  above).

- **Properties** (⚙, top bar): a near-fullscreen panel (a margin of the
  world stays visible all round it, not edge to edge) listing whether
  grid-lock movement is on — the same toggle as the button editor's, in
  sync either direction — a clock derived from the world's own tick
  count and speed, not a real one, a **move speed** slider (ticks per
  second, 1–30, takes effect immediately rather than only on restart —
  restarts the tick timer at the new rate), and an opt-in **minimap**
  toggle.

- **The Object Inspector** (🎯, in the button drawer): colour, resize,
  relocate (x/y/altitude), flip shape, duplicate, or delete whatever
  you're touching — or your pending ghost, if you have one, so a newly
  spawned object can be set up before it is even confirmed. Duplicate
  copies the object's *current* state (post-edit colour/size/shape), not
  just what its template started as, placed at the nearest open
  neighbouring cell. Delete asks first.

  **Tap any object in the 3D view to select it, too** — not just touch
  it on the ground. Projects every thing to screen space the same way a
  glyph label already is and picks whichever lands closest to the tap,
  within a fingertip-sized radius; a glowing ring then tracks the
  selected object continuously, every frame, wherever it is. A short
  drag (for turning the camera) is told apart from a tap by distance and
  time, so swiping to look around never accidentally selects something.

  Local play only, same reasoning as Build mode: it edits the live JS
  `Thing` object directly, which only exists for the copy of the game
  running in this tab.

- **A compass, as a meter across the top of the screen** — ticks scroll
  sideways as the camera turns, the current heading sits under a fixed
  centre marker, same idea as a flight HUD, not a rotating dial. Built
  once, spanning eight full turns each direction, so ordinary swiping
  never scrolls it out of ticks.

- **A quickbar**: seven empty, always-visible bubble slots, no drawer
  tab to open first — there to have something assigned to them later.

- **Editor preferences survive a reload**: grid-lock on/off, its grid
  size, which kind Build mode has selected, and the minimap toggle are
  now kept in `localStorage`. Move speed is deliberately *not* included
  — that is `project.world.speed`, real game data that already
  round-trips through a normal save/load; a remembered copy here would
  silently override whatever pace a *different* game was authored for
  the next time one loaded.

- **Build mode's palette lists alphabetically and has a search box** —
  useful once there are more than a couple of custom meshes in it. The
  Mesh Creator can also **load an existing saved mesh back in to edit**
  (a picker at the top; saving then defaults to overwriting the same
  one), **duplicate the selected part**, and **delete a saved mesh**
  entirely, not just create and edit one.

- **The button drawer's × now arms removal instead of acting
  immediately** — the next bubble tapped is the one removed, not
  whatever happened to be selected already, and a bubble can be marked
  `locked` so it can never be picked that way (used for the drawer's own
  built-in bubbles, so a stray tap during cleanup cannot remove
  something the page depends on).

- **Saving a 3D world checks for a name collision first**, and asks
  before overwriting an existing file. "save" quick-saves back to
  whatever the world was last saved or loaded as, with no prompt; "save
  as new" always asks for a name, so a copy can be forked off without
  touching the file the world came from.

- **`/update spark`** — pull the newest Spark from GitHub into the folder you
  already have. `python3 spark.py install` writes it, along with `update spark`
  and the long form `python3 spark.py update`.

  **Why there are two names for it.** A shell reads a leading `/` as *a file at
  the very root of the filesystem*, so `/update` has to literally be that file:
  it cannot be an alias, because bash refuses `/` in an alias name, and it
  cannot be a shell function. Inside the PRoot distro the root belongs to the
  distro and is writable, so `/update` is written there and works exactly as
  asked. In Termux proper the root is Android's own and read-only to apps, so
  `/update` cannot exist and `update spark` is the one to use. Install writes
  whichever it can and says which.

  **Your games are put aside and put back.** `games/*.json` are tracked files,
  so a phone anybody has built on has local changes and a plain `git pull` would
  refuse or trample them. They are stashed before the pull and restored after,
  and if restoring ever collides it says so and says where they are, rather than
  leaving a half-merged file to be discovered later.

  **It refuses rather than guessing**: no `origin`, not a clone, GitHub
  unreachable, or commits here that GitHub does not have — each stops, changes
  nothing, and says which it was. `--check` reports what an update would bring
  and stops.

  Afterwards it rewrites `tiles.json` and `games/index.json`, which are
  generated and would otherwise show yesterday's palette in the offline browser
  copy.

  **Nothing checks for updates by itself, and nothing will.** A game builder
  that quietly rewrites itself while you are using it is worse than an
  out-of-date one. And because `mytiles/approved.json` is untracked, an update
  can never switch a Python tile on: a tile file that arrives or changes in the
  pull lands inert, exactly as it would arriving any other way.

  `tests/check_update.py` — 25 checks — builds a fake GitHub as a bare repo and
  updates throwaway clones from it, including the one that matters: two edited
  games, updated, both edits demanded back.

### Changed

- **Every screen is now the six-button formation, not just the first one.** The
  previous entry put a deck in front of the editor and left the editor behind it
  as the same long scrolling page, which is not what was asked for. Now there is
  no long page anywhere:

  | Screen | Its buttons |
  |---|---|
  | edit | open · new · rename · world · share · github |
  | characters | one per character · + new |
  | one character | name · drawn as · colour · health · how many · role · solid · brain · delete |
  | brain | one per row · + row · undo |
  | one row | one per tile in it · + WHEN · + DO · ⊞ fold · delete row |
  | add a tile | your own, then all thirty-five — what the scrolling was built for |
  | your tiles | one per folded tile · fold a row · python |

  A screen is a name and a list of buttons; opening one pushes it on a stack and
  `‹` beside the box pops it, with `/back` and `/home` doing the same. Because
  every screen is rebuilt from the game each time it is shown, no action has to
  remember which buttons its change affected.

  Two things stay as they were, because they genuinely are not buttons: a tile's
  settings, and the Python text editor. Both open over the deck.

  `tests/deck.test.js` now **builds every screen** against a stub page rather
  than only reading the source — which is how it caught a screen referring to a
  function that had been deleted: it parsed perfectly and would have failed only
  when the button was pressed. 82 checks.

- **The browser now opens on a deck: six buttons and a box to type in, filling
  the screen.** The buttons are **play, edit, characters, brain, tiles, save**,
  and each opens what used to be a section of one long page, with a **‹ back**
  button. Nothing was removed — the deck is a way in, not a smaller Spark.

  Eight cells, six of them buttons, and the two left over are the box:

  | Held | Grid | Buttons | Box |
  |---|---|---|---|
  | upright | 2 across, 4 down | the first 3 rows | the last row, both columns |
  | sideways | 4 across, 2 down | the first 3 columns | the 4th column |

  The buttons stretch to fill whatever screen they are on and the deck itself
  never scrolls. If there are ever more than six, the **button area** scrolls up
  and down only, keeping the same columns — the rows simply run on.

### Added

- **A box to type in, under the buttons.** It takes commands or plain words:

  | Typed | What happens |
  |---|---|
  | `/help` | all of it, on screen |
  | `/play` `/edit` `/characters` `/brain` `/tiles` `/save` | the same as the buttons |
  | `/pin "feed the bug first"` | keeps a note — quotes optional |
  | `/pins`, `/unpin 2` | list them, remove one |
  | `/swap side chat` | the box changes sides when the phone is sideways |
  | `/who`, `/clear` | who is connected; empty the log |
  | anything else | said to everyone else in your world |

  An unrecognised `/word` says so and is **not** sent as chat, so a mistyped
  command is never broadcast. Notes are kept in the browser rather than the game
  file, so they follow the device.

- **Chat in a shared world.** Everyone who can see the world may talk,
  **watchers included** — somebody who may only look is still a person in the
  room, and saying something changes nothing about the world. A stranger with no
  valid code gets 403.

  One line is tidied of extra spaces and cut at 300 characters; only the last 40
  are kept, in memory. Nothing said reaches the disk or survives a restart: a
  shared world is a conversation while it is happening, not a record afterwards.
  It rides along with the world snapshot the page already fetches, so it costs
  no extra polling.

  Guests get the deck too — **play** and the box — but not the four buttons that
  change the game.

  `tests/deck.test.js` — 37 checks — covers the six buttons, every command,
  what `/pin` makes of quoted and unquoted notes, that `/swap side chat`
  remembers its side, and that an unknown command is not broadcast.

- **Write a tile in Python, from the browser.** A plain-text editor —
  *your own tiles, written in Python* — that writes files into `mytiles/`. What
  you write is an ordinary Spark tile: it joins the menus and is used like any
  other. `mytiles/example.py` ships switched off, with the whole shape explained
  inside it.

  This is the only part of Spark that runs code rather than reading a
  description, so it has a door on it, and the door is enforced rather than
  remembered:

  **Only the owner may write one.** Those routes answer the owner alone —
  whoever is at the phone or holds the key printed in the terminal. Somebody
  holding an `edit` code may rewrite every game you own and cannot put one line
  of Python on your disk. An `edit` guest cannot even make your phone open a
  link; letting them write code would have walked past that and every other
  fence at once.

  **A file does nothing until this device says so.** Approval is recorded in
  `mytiles/approved.json` against the exact text approved, and that file is in
  `.gitignore` — it never travels. So a tile you write in the browser is
  approved as it is saved, and a tile that arrives any other way — pulled from
  GitHub, handed over by another player, copied off an SD card — sits inert
  until you have read it and pressed *switch on*. A file that changes after
  approval stops loading and says so, which also covers a pull quietly changing
  one you had already agreed to.

  It is not a sandbox. There is no such thing for Python and pretending
  otherwise would be worse than useless. It is a gate, and the gate is consent.

  *Why it is built this way:* the ask was to write a tile in the browser and
  send it to the folder, to GitHub, or to other players in a shared world. All
  three work — but "other players can grab it" now means they receive the text,
  not that their phone runs it. Handing executable code to somebody else's
  device and having it run unasked is the one part I would not build.

  **One real limit, worth knowing before you rely on it:** these run in the
  Python engine, in Termux. `world3d.html` carries a second engine in JavaScript
  for when nothing is reachable, and it cannot run Python — so a game using one
  plays through Termux and through the server, but those rows do not fire in the
  browser's own offline engine, nor on GitHub Pages. For a tile of your own that
  works everywhere, fold one out of existing tiles instead.

  A file that will not compile is reported in the editor and skipped, and one
  that throws part-way has whatever it managed to register taken back off — a
  broken tile can never stop Spark starting, or you would have no way back in to
  fix it. `tests/check_mytiles.py` — 47 checks — covers the gate, the
  fingerprint, path escapes, broken files, and every route a guest is refused.

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
