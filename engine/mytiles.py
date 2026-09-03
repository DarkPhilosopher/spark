"""Tiles you wrote yourself, in Python, loaded from the mytiles/ folder.

    mytiles/*.py           one or more tiles each, written as in tiles.py
    mytiles/approved.json  which of them this device has agreed to run

This is the one part of Spark that runs code rather than data. Everything else
-- a game, a placeholder, one of your own named tiles -- is a description that
the engine reads. A file here is Python, and Python can do whatever Python can
do: read your files, open the network, delete things.

So the rule is simple and it is enforced here rather than remembered:

    a file in mytiles/ does nothing at all until THIS device has approved it,
    and approval is recorded against the exact text that was approved.

`approved.json` is deliberately **not** committed -- it is in .gitignore beside
.spark-state.json. That is what makes the promise hold:

  * A tile you write in the browser is approved as it is saved, because you are
    the owner of this Spark and writing it is the act of approving it.
  * A tile that arrives any other way -- pulled from GitHub, handed to you by
    another player, copied onto the SD card -- lands on disk with no approval
    on this device, so it sits there inert until you have read it and switched
    it on yourself.
  * A file that changes after approval stops loading, because the recorded
    fingerprint no longer matches. Editing it in the browser re-approves it;
    anything editing it behind your back does not.

None of this is a sandbox. There is no such thing for Python, and pretending
otherwise would be worse than useless. It is a gate, and the gate is consent.

What these tiles cannot do is run in the browser's own engine: world3d.html is
JavaScript and cannot execute Python. See `mine_note` below and the README.
"""

import hashlib
import json
import traceback
from pathlib import Path

from . import tiles

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "mytiles"
APPROVED = FOLDER / "approved.json"

# What went wrong, per file, the last time loading was tried. The editor shows
# these: a tile with a typo in it should say so on the screen you wrote it on,
# not vanish and leave you wondering.
errors: dict[str, str] = {}

# Which tile ids came out of which file, so that saving a file again can take
# its old tiles off the menus before putting the new ones on.
owned: dict[str, list] = {}

MINE_NOTE = ("written by you, in Python -- runs in Termux, not in the "
             "browser's own engine")


def safe_name(name):
    """A filename that cannot escape the folder. None if it is not one.

    Deliberately strict rather than clever: letters, digits, spaces, dashes and
    underscores. No dots, so no `..` and no pretending to be another kind of
    file; the .py is added here.
    """
    name = str(name or "").strip()
    if not name or len(name) > 60:
        return None
    if not all(c.isalnum() or c in " -_" for c in name):
        return None
    return name


def path_of(name):
    safe = safe_name(name)
    return (FOLDER / (safe + ".py")) if safe else None


def fingerprint(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_approvals():
    try:
        got = json.loads(APPROVED.read_text())
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError):
        return {}


def write_approvals(marks):
    FOLDER.mkdir(parents=True, exist_ok=True)
    APPROVED.write_text(json.dumps(marks, indent=2, sort_keys=True))


def files():
    """Every tile file, whether approved or not, oldest name first."""
    FOLDER.mkdir(parents=True, exist_ok=True)
    return sorted(p for p in FOLDER.glob("*.py"))


def listing():
    """What the editor shows: every file, its text, and where it stands."""
    marks = read_approvals()
    out = []
    for path in files():
        try:
            text = path.read_text()
        except OSError as err:
            text, = ("could not be read: %s" % err,)
        name = path.stem
        out.append({
            "name": name,
            "text": text,
            "approved": marks.get(name) == fingerprint(text),
            # Told apart so the editor can say *why* it is off: never approved
            # here, or approved once and changed since.
            "changed": name in marks and marks.get(name) != fingerprint(text),
            "error": errors.get(name, ""),
            "tiles": sorted(owned.get(name, [])),
        })
    return out


def approve(name, on=True):
    """Switch one file on or off for this device."""
    safe = safe_name(name)
    path = path_of(safe)
    if not safe or path is None or not path.exists():
        return False
    marks = read_approvals()
    if on:
        marks[safe] = fingerprint(path.read_text())
    else:
        marks.pop(safe, None)
    write_approvals(marks)
    return True


def save(name, text, approve_it=True):
    """Write a tile file. Saving it here is what approves it on this device."""
    safe = safe_name(name)
    path = path_of(safe)
    if path is None:
        return None
    FOLDER.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if approve_it:
        marks = read_approvals()
        marks[safe] = fingerprint(text)
        write_approvals(marks)
    return path


def delete(name):
    safe = safe_name(name)
    path = path_of(safe)
    if path is None or not path.exists():
        return False
    forget(safe)
    path.unlink()
    marks = read_approvals()
    marks.pop(safe, None)
    write_approvals(marks)
    return True


def forget(name):
    """Take one file's tiles back off the menus."""
    for tile_id in owned.pop(name, []):
        tiles.SENSORS.pop(tile_id, None)
        tiles.ACTIONS.pop(tile_id, None)
    errors.pop(name, None)


def load(name=None):
    """Run the approved tile files, so their tiles join the menus.

    One file failing is that file's problem: the error is kept for the editor
    to show and the rest still load. A tile with a typo in it must not be able
    to stop Spark from starting -- you would have no way to get back in and fix
    it.

    Returns how many files were loaded.
    """
    marks = read_approvals()
    loaded = 0
    for path in files():
        this = path.stem
        if name is not None and this != name:
            continue
        forget(this)
        try:
            text = path.read_text()
        except OSError as err:
            errors[this] = str(err)
            continue
        if marks.get(this) != fingerprint(text):
            continue                    # not approved on this device: inert
        before = set(tiles.SENSORS) | set(tiles.ACTIONS)
        room = {
            "sensor": tiles.sensor, "action": tiles.action, "Param": tiles.Param,
            "tiles": tiles, "__name__": "mytiles.%s" % this,
            "__file__": str(path),
        }
        try:
            exec(compile(text, str(path), "exec"), room)   # noqa: S102
        except Exception:                                  # noqa: BLE001
            # Whatever it managed to register before falling over comes back
            # off, so a half-run file leaves nothing behind.
            owned[this] = sorted((set(tiles.SENSORS) | set(tiles.ACTIONS))
                                 - before)
            forget(this)
            errors[this] = traceback.format_exc(limit=3).strip()
            continue
        owned[this] = sorted((set(tiles.SENSORS) | set(tiles.ACTIONS)) - before)
        errors.pop(this, None)
        loaded += 1
    return loaded


EXAMPLE = '''"""One tile of your own. Save it, and it appears on the menus.

Everything from tiles.py is already here: sensor, action and Param.
Read engine/tiles.py for the built-in ones -- they are all this short.
"""


@action("wander", "wobble about {much} squares",
        Param("much", "How far?", "int", [], 1))
def wobble(obj, world, a, it):
    """obj is me, world is everything, a is my settings, it is what WHEN found."""
    step = max(1, a.get("much", 1))
    obj.x = max(0, min(world.width - 1, obj.x + world.rng.randrange(step * 2 + 1) - step))
'''
