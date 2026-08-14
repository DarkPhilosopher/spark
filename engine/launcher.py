"""Install a `spark` command, so you can type one word instead of a path.

    python3 spark.py install

Writes a tiny shell script into whichever bin folders exist. Termux and the
PRoot distro need different first lines -- Android has no /bin/sh -- so each
gets its own copy pointing at its own shell.

It also tries to make `/update spark` work, which needs explaining. A shell
reads a leading `/` as "a file at the very root of the filesystem", so `/update`
has to literally BE that file: it cannot be an alias (bash refuses `/` in an
alias name) and it cannot be a shell function.

Whether that file can exist depends on where you are typing:

    inside the PRoot distro   `/` belongs to the distro and is writable, so
                              /update is written and `/update spark` works
    Termux proper             `/` is Android's own root, read-only to apps,
                              so /update cannot be created there

Because of that second row an `update` command goes into the bin folders too,
so `update spark` works everywhere `spark` does. Both do the same thing.
"""

import os
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TERMUX_BIN = Path("/data/data/com.termux/files/usr/bin")
TERMUX_SH = TERMUX_BIN / "sh"

SCRIPT = """#!{shell}
# Spark -- written by `python3 spark.py install`
SPARK_DIR="{root}"
cd "$SPARK_DIR" || {{ echo "Spark is not at $SPARK_DIR" >&2; exit 1; }}
for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
        exec "$py" spark.py "$@"
    fi
done
echo "No Python found. In Termux:  pkg install python" >&2
exit 1
"""


# `/update spark` and `update spark`. The word after it may be "spark" and is
# otherwise refused, so a typo says so instead of quietly updating anyway.
UPDATE_SCRIPT = """#!{shell}
# Spark's updater -- written by `python3 spark.py install`
SPARK_DIR="{root}"
case "${{1:-spark}}" in
    spark|Spark|SPARK) shift ;;
    -*|"") ;;
    *) echo "I only know how to update spark. Try:  $0 spark" >&2; exit 1 ;;
esac
cd "$SPARK_DIR" || {{ echo "Spark is not at $SPARK_DIR" >&2; exit 1; }}
for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1; then
        exec "$py" spark.py update "$@"
    fi
done
echo "No Python found. In Termux:  pkg install python" >&2
exit 1
"""


def targets():
    """Where a launcher can go, and which shell each one must name."""
    found = []
    if TERMUX_BIN.is_dir() and TERMUX_SH.exists():
        found.append((TERMUX_BIN / "spark", TERMUX_SH, "Termux"))
    for folder in (Path("/usr/local/bin"), Path("/usr/bin")):
        if folder.is_dir() and os.access(folder, os.W_OK):
            found.append((folder / "spark", Path("/bin/sh"), "this Linux"))
            break
    return found


def update_targets():
    """Where the updater can go -- including `/update` itself, where allowed."""
    found = [(path.with_name("update"), shell, where)
             for path, shell, where in targets()]
    root = Path("/")
    if os.access(root, os.W_OK):
        shell = TERMUX_SH if TERMUX_SH.exists() else Path("/bin/sh")
        found.append((root / "update", shell, "so `/update spark` works"))
    return found


def write(path, shell, template):
    path.write_text(template.format(shell=shell, root=ROOT))
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def install():
    done, failed = [], []
    for path, shell, where in targets():
        try:
            write(path, shell, SCRIPT)
            done.append((path, where))
        except OSError as err:
            failed.append((path, err))
    for path, shell, where in update_targets():
        try:
            write(path, shell, UPDATE_SCRIPT)
            done.append((path, where))
        except OSError as err:
            failed.append((path, err))
    return done, failed
