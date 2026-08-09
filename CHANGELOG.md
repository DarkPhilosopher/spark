# Changelog

Everything that has changed in Spark, newest first, in plain language.
The guide itself is [README.md](README.md).

**House rule:** every change to Spark updates this file *and* the README in the
same breath. If you add a tile, it goes in the tile table in the README and in a
line here. If behaviour changes, say so here even if no file was renamed. A
change that is not written down is a change nobody can find again.

Each entry says **what** changed and, where it is not obvious, **why**.

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
