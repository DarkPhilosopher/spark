# Spark manual — requirements, controls, commands, connecting

The short guide is [README.md](README.md). The history is
[CHANGELOG.md](CHANGELOG.md). This file is the exact reference: what Spark
needs, every button and key, every command, and step-by-step instructions for
turning on the browser interface and GitHub.

## Contents

- [The tutorial](#the-tutorial)
- [System requirements](#system-requirements)
- [Controls: playing a game](#controls-playing-a-game)
- [Controls: the terminal menus](#controls-the-terminal-menus)
- [Controls: the browser editor](#controls-the-browser-editor)
- [Every command](#every-command)
- [Connecting the browser interface](#connecting-the-browser-interface)
- [Connecting another person: live play](#connecting-another-person-live-play)
- [Connecting GitHub](#connecting-github)
- [Moving games between phone and GitHub](#moving-games-between-phone-and-github)
- [Renaming a game](#renaming-a-game)
- [What each of the three connections gives you](#what-each-of-the-three-connections-gives-you)

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

---

## Controls: playing a game

While a game is running (`spark.py play ...`, or **play it** in the menus):

| Key | Does |
|---|---|
| ↑ ↓ ← → | whatever the character's brain says for that key |
| space | usually shoot — again, whatever the brain says |
| w a s d, e, f | available as tiles, if you build rows that use them |
| `q` | quit back to the menu |
| Ctrl-C | quit |

Keys are not hard-wired. `WHEN key up is pressed DO move up` is a brain row you
built; delete it and the up arrow stops doing anything. The demo game wires the
arrows and space for you.

The display shows the world, then `score`, `health`, `tick`, then the most
recent **say** message.

---

## Controls: the terminal menus

Everything is a numbered list. Type the number, press enter.

| Key | Does |
|---|---|
| a number | choose that item |
| `0` or enter | go back, or done, or quit at the top level |
| enter on a question | accept the `[default]` shown in brackets |
| Ctrl-C | leave Spark |

The screens, in order of depth:

1. **Main menu** — with nothing open: *learn how* (the tutorial), new game, open
   a game. With a game open: play, characters, world settings, save, rename,
   send to GitHub, invite someone to play, new game, open a game.
2. **Characters** — add a character, or pick one to edit.
3. **One character** — its brain, its letter, colour, health, how many start,
   player or prop, solid or walk-through, delete.
4. **Its brain** — the list of `WHEN ... DO ...` rows: add, change, delete, move
   a row up.
5. **One row** — add or remove WHEN tiles and DO tiles.
6. **One tile** — answer its questions, one per screen.

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
| **⚙** | GitHub settings — only shown when there is no local server |
| **👥** | share and multiplayer — only shown when there is one |

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

## Every command

Run these from inside the spark folder (`cd ~/spark` in Termux).

| Command | Does |
|---|---|
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
| `python3 spark.py status` | print the Github / Browser / Local line |
| `python3 spark.py export` | rewrite `tiles.json` and `games/index.json` |
| `python3 spark.py push` | overwrite **every** game on GitHub with this phone's |
| `python3 spark.py push chase` | overwrite just that one game on GitHub |
| `python3 spark.py push chase maze` | overwrite those two |
| `python3 spark.py pull` | overwrite every game here with GitHub's |
| `python3 spark.py pull chase` | overwrite just that one here |
| `python3 tests/check_docs.py` | check the README still matches the code |
| `python3 tests/check_sync.py` | check the GitHub push/pull logic, offline |
| `node tests/store.test.js` | check the editor's save and load logic |

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

**Step 3.** The header will read `Github T  Browser T  Local F`. `Local F` is
correct and expected — there is no Python behind a Pages site. The editor works
anyway: it reads `tiles.json` and `games/index.json`, and keeps your edits in
the browser's own storage.

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

## What each of the three connections gives you

| | Github | Browser | Local |
|---|---|---|---|
| Play games | no | no | **yes** |
| Drag-and-drop editing | via Pages | **yes** | — |
| Works with no internet | no | yes, with the local server | **yes** |
| Edit from a laptop | **yes**, via Pages | no | no |
| Games stored where | in the repo | in browser storage | in `~/spark/games` |
| Needed for the others | no | no | no |

None of the three depends on the others. The terminal alone is a complete Spark;
the browser makes it pleasant; GitHub makes it portable and backed up.

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
