# Notes for Claude — read before editing this project

## Task note format

Tasks noted here get checked off `[x]` in place once worked on, with a
short summary of how it went written directly underneath — not a
separate note elsewhere, so each task's whole history (asked → done →
outcome) stays together.

## Tasks

- [x] **(noted 2026-09-09):** "make a game 2d asc in termux... had ores and
  build mode also command units rts game kenshi" — first built as a
  standalone ASCII RTS (`~/ascirts`, its own separate git repo, Python
  + `curses`, not part of Spark), then redirected: "make it an game
  save into spark make aame thing with when do code" — same idea,
  rebuilt as an actual Spark game authored in WHEN/DO tiles instead of
  bespoke Python.
  **How it went (2026-09-09 → 2026-09-10), across several follow-up
  messages in the same thread:**
  - Three new general-purpose tiles (both engines): `lead`/`dismiss`
    (recruit/release whoever you touch — sets/clears a new per-Thing
    `leader` field, same "per-Thing, not `world.memory`" reasoning
    `inventory`/`harvest` already established) and `has_leader` (hands
    the leader back as `it`, so the *existing*, unchanged `move` tile's
    own "toward it" direction is all a recruited companion needs to
    follow along — no new movement code at all). Later, `recruit`:
    spawns a `{kind}` at the recruiter's own spot already led by them
    — the "buy a unit" tile, since a separate `spawn` then `lead` in
    one row can never target what `spawn` just made (a row's DO tiles
    all share the WHEN half's one `it`).
  - `games/outpost.json` (new): a small frontier camp — a hero,
    touch-to-recruit companions, wandering bandits (autonomous
    `see`/`touch`+`damage` — no new tiles needed for that part),
    `harvestable` ore (the existing tile) for world3d.html's flashy
    Harvest panel, buyable `worker`/`soldier` units via `recruit` (ore
    cost, `1`/`2` keys), and a buildable `wall` for the already-generic
    Build mode. Added `"r"`/`"1"`/`"2"` to the shared `KEYS` list so
    they're real tile-editor dropdown choices, not just working by
    accident (the engine only ever checks key membership).
  - **Real bug, reported and fixed same thread:** the hero itself had
    *no* gathering rule at all — only recruited companions/workers did,
    and the Harvest countdown panel is deliberately world3d.html-only
    JS, never in the plain terminal player — so touching ore as the
    hero in `spark.py play` did nothing whatsoever. Fixed with one row,
    `WHEN timer(5) AND touch(ore) DO give_item(self, ore, 1)`, the same
    pattern the companion/worker already use, so it works in both
    engines with no JS-only dependency.
  - The plain terminal player (`engine/runner.py`) gained its own `/`
    command line — pressing `/` during play calls new
    `Keyboard.pause()`/`.resume()` (thin wrappers around the existing
    termios `__exit__`/`__enter__`) to hand the terminal back to normal
    cooked `input()` for one line — a real text box, not gameplay's
    one-key-at-a-time swallowing — runs it as a command, and shows the
    result as its own screen until any key dismisses it. `/help` reads
    a new optional `help` string field on the game JSON itself
    (`brain.load`/`.save` already round-trip it for free, being
    schema-free `json.loads`/`json.dumps`) — the exact same field
    world3d.html's own (pre-existing) `/help` chat command was extended
    to read first too, so writing one `help` string covers both
    surfaces. `/mine <x> <y>` (added last, both places a command can be
    typed) gathers from ore at an exact coordinate instead of walking
    up to it blind — still one square away at most, refuses rather than
    mining across the map; needed `runChatSaid`/`run_local_command` to
    start threading a typed line's *rest* through to its command, which
    nothing before `/mine` had needed.
  - New tests throughout, run alongside the full existing suite every
    step: `tests/check_lead.py`/`tests/lead.test.js` (16/17 checks),
    `tests/check_chat_break.py` (20 checks, real-pty end to end — same
    trick `check_menu.py` already uses, since a plain pipe can't tell
    apart from a real terminal and this feature only engages on one),
    `tests/chat.test.js` extended (20 checks total). `check_engines.py`
    auto-discovers every `games/*.json`, so `outpost` itself needed no
    dedicated parity test — confirmed bit-for-bit identical between
    Python and JS across four seeds throughout, on every change.
  - Also fixed, unrelated but same thread: the terminal's own
    arrow-key/big-picture menu (`builder._render_menu`) doubled/garbled
    text on a narrow phone terminal — the built-in control-hint line
    (59 characters) or a long option label could wrap onto a second
    physical row, desyncing the fixed cursor-up-by-N-rows redraw math.
    Fixed with `_fit()`, truncating every line to the real terminal
    width first. First theory (cbreak leaving terminal echo on) was
    wrong and was tested, disproven, and discarded rather than shipped.
  - Not seen running on a real device at any point in this thread —
    every "confirmed" claim above is from driving the real engine
    and/or a real pty directly (including a full simulated playthrough:
    recruit → follow → gather → fight → dismiss, walking a hero there
    with injected keypresses), never an actual screen.

- [x] **(noted 2026-09-03):** "make each page before progression a 6
  panel largest button to fit screen besides chat on side, same as
  before" — the 3D view's five modals (Backpack, Properties, Mesh
  Creator, Build/palette, Object Inspector) reformatted to match the
  browser editor's own deck formation.
  **How it went (2026-09-03):** confirmed with Gabe in two rounds this
  meant world3d.html's modals (not index.html's deck, which already
  works this way), and that it meant all five including Backpack —
  overriding the "deliberate exception" note above, on purpose, at
  Gabe's explicit request; see that note for the reversal. Built one
  shared shell (`.mgrid`/`.mkeys`/`.mbox`, plus `.modal-titlebar` and a
  `.modal-back` for sub-pages) reused by all five, matching index.html's
  own 4x2-cells-of-8 ratio since there is nothing to import between the
  two files. There is no live chat in world3d.html to put in "the box"
  (it is offline single-player; LIVE mode only mirrors a running game, it
  does not carry chat here) — read "the box" as *whatever isn't one of
  the six buttons* instead: a live preview canvas, a part list, a file
  grid, a search field, live readouts, exact typed values. Where a page
  has more discrete choices than six buttons can hold (nineteen colours,
  seven shapes, every placeable kind), those choices become the buttons
  themselves, scrolling — the same pattern README already documents for
  the browser editor's own big lists, not a new idea. Where a control is
  genuinely continuous (resize/stretch/position, move speed, part
  position/size), it stayed a real slider or typed field, relocated into
  the box, with quick-jump buttons alongside for the common cases —
  deliberately not lossy-replaced with discrete steps, since nothing
  asked for that and it was avoidable. The Object Inspector and Mesh
  Creator both grew real sub-pages (Colour, Shape, and for the Inspector
  also Resize/Stretch/Move) reached from a `‹` back button next to the
  title, sharing one `choiceKeys()` helper for the two colour pickers and
  the two shape pickers rather than writing each twice. Also fixed, as a
  side effect of touching every modal's markup anyway: `#mesh-titlebar`
  and `#mesh-body` used to be duplicate ids across three different modals
  (invalid HTML, though harmless since nothing ever queried them by id) —
  every modal has its own ids now. Verified with `node --check`, a full
  `html.parser` pass, and a new `tests/modal_pages.test.js` (29 checks)
  driving the actual page-navigation/choiceKeys/quick-button machinery
  against a stub DOM — caught one real bug this way (a test fixture
  missing `world.templates`, not app code, but the kind of thing that
  would have gone unnoticed without exercising the code at all) — plus
  the full existing suite, all green. Not seen on a real screen — this is
  the biggest changeset this project has shipped without on-device eyes
  on it yet, worth a real look before building further on top of it.

- [x] **(noted 2026-09-02):** a function to mesh multiple selected 3D
  objects into one combined 3D shape — multi-select several placed
  objects, merge them into a single mesh.
  **How it went (2026-09-03):** built as a new drawer bubble, 🧬 Merge —
  arm it, tap objects one at a time (each gets its own green ring,
  `mergeSelection`/`drawMergeHighlights`), tap 🧬 again to combine.
  Resolved the design questions the note above raised: selection is its
  own parallel array alongside the existing single-`inspectTarget`
  selection, not sharing it, since Inspector-select and merge-select are
  different modes of the same tap (`pickObjectAt` branches on
  `mergeArmed`); "merge" produces a new placeable kind, `parts:
  [...]` in exactly the shape the Mesh Creator already writes, via the
  same "save as new kind" template/registration path it uses, then
  removes the originals. A Thing that's already a merged/mesh-creator
  shape contributes its own parts individually rather than being
  flattened, so merging a merge stays composable. Also did the "removing
  the inner geometry" half of the ask, honestly scoped: not real CSG
  (cutting polygons where solids overlap) — that's a much bigger
  undertaking than this hand-rolled renderer is set up for and too risky
  to ship unverified. What it does instead: a part whose whole bounding
  box sits inside another's is dropped outright (`dropHiddenParts`),
  correct and cheap for the common case (props built into or stacked
  inside each other); a part that only partly overlaps keeps its full
  geometry, same as any two overlapping opaque objects always render
  correctly via ordinary depth testing. Verified with a new permanent
  test, `tests/mesh_merge.test.js` (17 checks: offsets, the
  fully-contained-part-dropped case, partial overlap surviving,
  duplicate-bounds collapsing to one not zero, and composing an
  already-merged object) — no headless WebGL here to render an actual
  frame and look at it, so this is arithmetic-level verification, not a
  substitute for eyes on a real device.

- [x] Reorganize the buttons on screen in the 3D world editor
  (`world3d.html`) so the layout actually looks and fits well.

  **How it went (2026-09-02):** Converted the top-right side bar from 6
  mixed text/icon buttons (which could wrap awkwardly) to compact icons
  for the rarely-pressed ones (restart → ↺, recentre → ⌖, tooltips via
  `title`) and short words for the ones an icon would blur (save, new);
  added `flex-wrap` so it degrades to a second line instead of
  overflowing on a narrow phone if it ever needs to. Pad (3×3) and the
  left-edge button drawer were left structurally as-is — already
  reasonable — but every hardcoded panel/overlay color across pad, side
  bar, drawer, HUD, top bar, veil, and the toast helper was repointed at
  the new gray/light-blue palette below, so nothing was left rendering
  the old dark/neon colors underneath the new CSS variables. Validated:
  `node --check` on the extracted script and a full `html.parser` pass,
  both clean.

  **Follow-up, same day, from an actual on-device screenshot:** two real
  layout bugs, not just polish. (1) The landscape pad height cap was
  `88vh` — on a short landscape screen that made the pad tall enough to
  grow up into the top bar (visibly overlapping the restart button).
  Fixed by capping it at `calc(100vh - 150px)` instead of a flat `vh`
  share, so it can no longer outgrow the space actually left below the
  bar. (2) The button drawer was vertically centered (`top:50%`), which
  put it directly over the HUD (score/health/tick) on a short landscape
  screen. Centering also isn't safe in portrait either, since a
  near-full-width portrait pad shares that same bottom half — so
  "centered" and "anchored low" were both wrong. Fixed by anchoring it
  at a fixed `top:190px` instead (below the HUD in both orientations;
  clear of the pad regardless of orientation because the pad sits on the
  opposite/right side in landscape and above that height in portrait).
  Re-validated the same way, still clean.

  **Confirmed on-device (2026-09-02), and liked:** Gabe screenshotted it
  and said to keep it — specifically named the gray/light-blue palette,
  the white-void sky (the WebGL clear color, `rgba(0.75,0.80,0.86,1)`),
  and "the subtle fog icy look" (the floor/rim grays fading up into that
  same light sky color toward the horizon). Treat the current colors in
  `world3d.html` — clear color, floor checker, rim, and the CSS panel
  palette below — as **locked**, not a placeholder. Do not casually
  change them while working on something else; if a future change would
  touch any of these, call it out rather than just doing it.

## Design preference — separate from the task above

Gray and light blue, **not** the old dark-background-plus-neon-accent
look. See the confirmed note just above for the exact locked values —
this line is just the short version for a quick skim.

**Superseded (2026-09-02 → 2026-09-03):** the Backpack (`#backpack-modal`
in `world3d.html`) used to be deliberately styled like Windows File
Explorer — white background, light gray toolbar, blue selection
highlight — because Gabe asked for that look specifically, and the note
here used to say not to "correct" it. On 2026-09-03 Gabe explicitly asked
for it to be folded into the same gray/light-blue shell and six-panel-
buttons-plus-a-box formation as the other four modals (see the "each
page before progression" task below) — a direct, deliberate reversal of
the line above, not a rediscovery of theme drift, so this paragraph
stays as a record of that rather than being deleted. Everything in the
game now follows the locked palette; there is no exception left.

This is Gabe's spark project, running live via `spark.py edit` at
`127.0.0.1:8765` on his phone (real Termux, via a proot Ubuntu sandbox).
He tests changes himself in Chrome on-device — nothing here can be run or
screenshotted from this session, so validate everything possible before
saying a change is done, and be explicit about what's confirmed vs. not.

## Panel formations (noted 2026-09-04) — two shapes, pick by content

Two layout ideas Gabe asked to have written down here explicitly, to
keep in mind for any future full-panel layout in `world3d.html`, not
just the one that prompted them:

1. **8 boxes, the whole screen.** His reasoning: an average smartphone
   screen is about as close to square as phone screens get, so dividing
   the *whole* screen (edge to edge, not inset into a smaller card the
   way every modal here currently is) into 8 boxes suits it well —
   stretched to fill either way, left open rather than a firm mandate.
   Best for a panel that's pure discrete actions, nothing continuous or
   typed to show. The button editor already moved to an eight-button
   version of this the same day (`.mkeys` with 8 buttons instead of the
   other modals' 6) — but still inset at `6vh 6vw` like the rest, not
   yet edge-to-edge full-screen. Worth revisiting if a panel calls for
   the full-screen version specifically.

2. **6 buttons plus a terminal, otherwise.** The established alternative
   — the same `.mgrid`/`.mkeys`/`.mbox` shell already used for
   Backpack/Properties/Mesh Creator/Build/the Inspector — except Gabe's
   own framing makes "the box" more specific than "whatever isn't a
   button": it's a **terminal**, taking typed plain text for *both*
   commands and human chat, the same way index.html's own deck box
   already works (`/help`, `/pin`, plain text said to the room, etc.),
   not just a passive readout. world3d.html's own Chat panel (added the
   same day) is a version of this idea too, just its own separate modal
   rather than folded into a 6-button panel's box the way index.html
   does it in one piece.

**Why:** Gabe asked explicitly to write both of these down here (and in
my own persistent memory) so they're actually considered for future
panel work in this project, not just remembered for the one session
that prompted them.

## Two engines, kept deliberately in sync

The game logic exists twice: `engine/*.py` (real gameplay, `spark.py play`,
hosted multiplayer) and a hand-mirrored JS copy inside `world3d.html`
(offline single-player, no server needed). **Any change to a sensor,
action, or `Thing` field must be made in both places, identically** —
same tile id, same params, same clamps/defaults. This is not optional;
the project's own test suite exists specifically to catch drift between
them.

## Checklist before calling an edit finished

1. **Python changes** (`engine/*.py`): `python3 -m py_compile` the files
   touched.
2. **New/changed action or sensor tile**: re-run the export so
   `tiles.json` (the browser editor's tile picker) picks it up:
   ```
   cd ~/spark && python3 -c "
   import sys; sys.path.insert(0,'.')
   from engine import mytiles; mytiles.load()
   from engine import server; server.export_static()"
   ```
3. **JS changes** (`index.html`, `world3d.html`): extract the `<script>`
   block and run `node --check` on it; also feed the whole file through
   Python's `html.parser` to catch unclosed/mismatched tags.
4. **Any engine-behavior change**: run `tests/check_engines.py` (needs
   `node` — it drives both engines through the same seeded games and
   demands identical results). Must be 0 failed before it's done.
5. **Game JSON edits** (`games/*.json`): validate with `json.load`, and
   where practical, load it through `engine.brain.load` +
   `engine.world.World` and step it a few ticks directly to catch
   schema mistakes the JSON parser alone won't (a `world.py` and
   `tiles.py` `Thing`/`Param` mismatch, e.g.) — this is one of the very
   few things this sandbox actually gets to *run and see the result of*,
   so use it.

## File locations that matter

- Real Termux home: `/data/data/com.termux/files/home` — this sandbox
  can read/write it directly and reliably; that's where `~/spark` lives.
- `spark.py edit`'s server reads straight from `~/spark`, so edits there
  show up on reload with no extra copying.
- For a plain `file://` open in Chrome with no server, mirror the file(s)
  to `/sdcard/Download/spark/` after editing — Chrome cannot see Termux's
  private storage at all, only shared storage.

## Hard walls in this sandbox (don't retry these, they're not flaky)

- No Termux:API command (`termux-notification`, `termux-wake-lock`, ...)
  can run from this proot sandbox — SELinux blocks `app_process` for any
  ptrace-sandboxed process, not just this one command. Give Gabe the
  exact command to run in the real Termux app instead.
- `pkg`/`apt-get` cannot run as root here — Termux's own compiled-in
  safety block, deliberate, not to be routed around. Same: hand it to him
  to run himself.
- No physical UI interaction (tapping the screen, pulling the
  notification shade) is possible from here at all.
