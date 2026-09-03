# Notes for Claude — read before editing this project

## Task note format

Tasks noted here get checked off `[x]` in place once worked on, with a
short summary of how it went written directly underneath — not a
separate note elsewhere, so each task's whole history (asked → done →
outcome) stays together.

## Tasks

- [ ] **For later, not yet started (noted 2026-09-02):** a function to
  mesh multiple selected 3D objects into one combined 3D shape —
  multi-select several placed objects, merge them into a single mesh.
  Nothing built yet; needs its own design pass (how selection works
  alongside the existing single-`selected` ghost/place flow, what "merge"
  actually produces in the `Thing`/render model) before starting.

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

**One deliberate exception (2026-09-02):** the Backpack (`#backpack-modal`
in `world3d.html`) is explicitly styled like Windows File Explorer —
white background, light gray toolbar, blue selection highlight — because
Gabe asked for that look specifically. This is not theme drift and
should not be "corrected" to gray/light-blue; it is its own thing on
purpose. Everything else in the game still follows the locked palette.

This is Gabe's spark project, running live via `spark.py edit` at
`127.0.0.1:8765` on his phone (real Termux, via a proot Ubuntu sandbox).
He tests changes himself in Chrome on-device — nothing here can be run or
screenshotted from this session, so validate everything possible before
saying a change is done, and be explicit about what's confirmed vs. not.

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
