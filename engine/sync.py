"""Send single games up to GitHub, or bring them back down.

Saving from the browser already writes to GitHub one file at a time. This is
the same thing from the terminal, so you can overwrite what is on GitHub with
what is on the phone -- one world at a time, by name, or all of them.

It borrows the login you already did with `gh auth login`, so there is no
second token to look after.
"""

import base64
import json
import re
import subprocess
import urllib.error
import urllib.request

from . import brain

API = "https://api.github.com"


class SyncError(Exception):
    pass


def _run(*args):
    try:
        done = subprocess.run(args, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def token():
    """The token gh stored when you logged in."""
    got = _run("gh", "auth", "token")
    if not got:
        raise SyncError("not logged in to GitHub -- run:  gh auth login")
    return got


def repo():
    """(owner, name) from the git remote, however the URL is written."""
    url = _run("git", "-C", str(brain.GAMES_DIR.parent), "remote", "get-url", "origin")
    if not url:
        raise SyncError("no GitHub remote yet -- push this folder to GitHub first")
    match = re.search(r"github\.com[:/]+([^/]+)/(.+?)(?:\.git)?/?$", url)
    if not match:
        raise SyncError("cannot read a GitHub repo out of: " + url)
    return match.group(1), match.group(2)


def branch():
    return _run("git", "-C", str(brain.GAMES_DIR.parent),
                "rev-parse", "--abbrev-ref", "HEAD") or "main"


def api(method, path, tok, body=None):
    request = urllib.request.Request(
        API + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + tok,
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json",
                 "User-Agent": "spark"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as err:
        try:
            detail = json.loads(err.read() or b"{}")
        except ValueError:
            detail = {}
        return err.code, detail
    except urllib.error.URLError as err:
        raise SyncError("no connection to GitHub (%s)" % err.reason)


def _contents_path(owner, name, path):
    return "/repos/%s/%s/contents/%s" % (owner, name, path)


def remote_sha(owner, name, path, ref, tok):
    """GitHub needs a file's current sha before it will let you replace it."""
    code, body = api("GET", _contents_path(owner, name, path) + "?ref=" + ref, tok)
    return body.get("sha") if code == 200 else None


def put_file(owner, name, path, text, message, ref, tok):
    payload = {"message": message, "branch": ref,
               "content": base64.b64encode(text.encode()).decode()}
    sha = remote_sha(owner, name, path, ref, tok)
    if sha:
        payload["sha"] = sha                    # replacing, not creating
    code, body = api("PUT", _contents_path(owner, name, path), tok, payload)
    if code not in (200, 201):
        raise SyncError(body.get("message", "GitHub said %d" % code))
    return "updated" if sha else "created"


def get_file(owner, name, path, ref, tok):
    code, body = api("GET", _contents_path(owner, name, path) + "?ref=" + ref, tok)
    if code != 200:
        return None
    return base64.b64decode(body.get("content", "")).decode()


def remote_games(owner, name, ref, tok):
    code, body = api("GET", _contents_path(owner, name, "games") + "?ref=" + ref, tok)
    if code != 200:
        return []
    return sorted(f["name"][:-5] for f in body
                  if f["name"].endswith(".json") and f["name"] != "index.json")


def _resolve(names, available, what):
    if not names:
        return available
    missing = [n for n in names if n not in available]
    if missing:
        raise SyncError("no %s game called '%s'. there is: %s"
                        % (what, missing[0], ", ".join(available) or "nothing"))
    return list(names)


def push(names=None, message=None):
    """Overwrite games on GitHub with the copies on this phone."""
    tok, (owner, name), ref = token(), repo(), branch()
    here = [p.stem for p in brain.list_games()]
    results = []
    for game in _resolve(names, here, "local"):
        path = "games/%s.json" % game
        text = (brain.GAMES_DIR / (game + ".json")).read_text()
        what = put_file(owner, name, path, text,
                        message or "spark: overwrite %s from the phone" % game,
                        ref, tok)
        results.append((game, what))

    listing = json.dumps(remote_games(owner, name, ref, tok), indent=2)
    put_file(owner, name, "games/index.json", listing,
             "spark: update game list", ref, tok)
    return results, "%s/%s" % (owner, name)


def pull(names=None):
    """Overwrite games on this phone with the copies on GitHub."""
    tok, (owner, name), ref = token(), repo(), branch()
    there = remote_games(owner, name, ref, tok)
    results = []
    for game in _resolve(names, there, "remote"):
        text = get_file(owner, name, "games/%s.json" % game, ref, tok)
        if text is None:
            continue
        target = brain.GAMES_DIR / (game + ".json")
        existed = target.exists()
        target.write_text(text)
        results.append((game, "overwritten" if existed else "added"))
    return results, "%s/%s" % (owner, name)
