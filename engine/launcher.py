"""Install a `spark` command, so you can type one word instead of a path.

    python3 spark.py install

Writes a tiny shell script into whichever bin folders exist. Termux and the
PRoot distro need different first lines -- Android has no /bin/sh -- so each
gets its own copy pointing at its own shell.
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


def install():
    done, failed = [], []
    for path, shell, where in targets():
        try:
            path.write_text(SCRIPT.format(shell=shell, root=ROOT))
            path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP
                       | stat.S_IXOTH)
            done.append((path, where))
        except OSError as err:
            failed.append((path, err))
    return done, failed
