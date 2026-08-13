"""A shared world that other people can join.

One phone hosts. The world runs here, on a background thread, and everyone
else's browser sends keypresses and draws whatever the host reports back.

Three things a guest can be, decided by the invite code they used:

    edit    change games and save them, and play
    play    join the world and press keys, but not change anything
    watch   see the world, press nothing

Codes are made by the host and can be revoked. A code carries the role, so who
someone is never has to be looked up anywhere -- if the code is gone, so is the
access it granted.
"""

import secrets
import string
import threading
import time

from . import brain, status
from .world import World

CODE_ALPHABET = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
ROLES = ("edit", "play", "watch")
IDLE_OUT = 25           # seconds before a silent guest is dropped from the world


def make_code(length=6):
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(length))


class Invite:
    def __init__(self, role, character="own", note="", uses=0):
        self.code = make_code()
        self.role = role if role in ROLES else "watch"
        self.character = character      # "own", "watch", or a character's name
        self.note = note                # a name for your own benefit
        self.uses = uses                # 0 means unlimited
        self.used = 0
        self.created = time.time()

    def spend(self):
        if self.uses and self.used >= self.uses:
            return False
        self.used += 1
        return True

    def public(self):
        return {"code": self.code, "role": self.role, "character": self.character,
                "note": self.note, "uses": self.uses, "used": self.used}


class Player:
    def __init__(self, token, role, character, name):
        self.token = token
        self.role = role
        self.character = character
        self.name = name
        self.id = "p" + secrets.token_hex(3)
        self.keys = set()
        self.joined = time.time()       # fixed; what "who came first" means
        self.seen = time.time()         # moves; how we notice they left
        self.thing = None               # the character they drive, if any


class Session:
    """The host's live game: one world, several people watching or playing."""

    def __init__(self):
        self.lock = threading.RLock()
        self.invites = {}               # code -> Invite
        self.players = {}               # token -> Player
        self.world = None
        self.game_name = None
        self.thread = None
        self.running = False

    # -- invites ----------------------------------------------------------

    def invite(self, role, character="own", note="", uses=0):
        with self.lock:
            new = Invite(role, character, note, uses)
            self.invites[new.code] = new
            return new

    def revoke(self, code):
        with self.lock:
            gone = self.invites.pop(code.upper(), None)
            if gone:
                # anyone already in on that code loses access too
                for token, player in list(self.players.items()):
                    if getattr(player, "code", None) == gone.code:
                        self.drop(token)
            return bool(gone)

    def join(self, code, name):
        """Trade an invite code for a session token."""
        with self.lock:
            invite = self.invites.get((code or "").strip().upper())
            if invite is None:
                return None, "that code is not valid"
            if not invite.spend():
                return None, "that code has been used up"
            player = Player(secrets.token_urlsafe(16), invite.role,
                            invite.character, (name or "guest")[:16])
            player.code = invite.code
            self.players[player.token] = player
            if self.running and player.role == "play":
                self._give_character(player)
            self._publish()
            return player, None

    def who(self, token):
        with self.lock:
            player = self.players.get(token or "")
            if player:
                player.seen = time.time()
            return player

    def drop(self, token):
        with self.lock:
            player = self.players.pop(token, None)
            if player and player.thing is not None:
                player.thing.controller = None
                if player.character == "own":
                    self.world and self.world.remove(player.thing)
            if player:
                self._publish()

    def _publish(self):
        """Write the roster where another process can read it.

        The menus are usually not the process that is serving, so `players` in
        the menus has no Session to look at -- only this note.
        """
        with self.lock:
            status.note_players([
                {"name": p.name, "role": p.role, "joined": p.joined,
                 "game": self.game_name if self.running else None}
                for p in sorted(self.players.values(), key=lambda p: p.joined)])

    # -- the world --------------------------------------------------------

    def _give_character(self, player):
        """Hand a joiner something to drive, per their invite."""
        if self.world is None or player.character == "watch":
            return
        if player.character == "own":
            template = next((c for c in self.world.project["characters"]
                             if c.get("role") == "player"), None)
            if template is None:
                return
            thing = self.world.spawn_somewhere(template["kind"])
        else:
            thing = next((t for t in self.world.things
                          if t.kind == player.character and t.controller is None),
                         None)
            if thing is None:
                thing = self.world.spawn_somewhere(player.character)
        if thing is not None:
            thing.controller = player.id
            player.thing = thing

    def start(self, name):
        """Load a game and begin ticking it."""
        with self.lock:
            self.stop()
            self.world = World(brain.load(brain.GAMES_DIR / (name + ".json")))
            self.game_name = name
            self.running = True
            for player in self.players.values():
                player.thing = None
                if player.role == "play":
                    self._give_character(player)
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            self._publish()             # everyone is now inside a named game

    def stop(self):
        with self.lock:
            self.running = False
            self._publish()             # ...and now they are back in no game
        thread = self.thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2)
        self.thread = None

    def _loop(self):
        while True:
            with self.lock:
                if not self.running or self.world is None:
                    return
                world = self.world
                delay = 1.0 / max(1, world.project.get("world", {}).get("speed", 6))
                now = time.time()
                for token, player in list(self.players.items()):
                    if now - player.seen > IDLE_OUT:
                        self.drop(token)                # they closed the tab
                world.player_keys = {p.id: set(p.keys)
                                     for p in self.players.values()}
                for player in self.players.values():
                    player.keys.clear()                 # each press acts once
                world.step()
                if world.status:
                    self.running = False
            time.sleep(delay)

    def press(self, player, keys):
        with self.lock:
            if player.role == "play":
                player.keys.update(k for k in keys if isinstance(k, str))

    # -- what a guest's browser draws -------------------------------------

    def snapshot(self, player=None):
        with self.lock:
            if self.world is None:
                return {"running": False, "game": None,
                        "people": self._people(), "you": self._you(player)}
            world = self.world
            return {
                "running": self.running,
                "game": self.game_name,
                "w": world.width, "h": world.height,
                "tick": world.tick, "score": world.score,
                "message": world.message, "status": world.status,
                "things": [[t.x, t.y, t.glyph, t.color] for t in world.things],
                "people": self._people(),
                "you": self._you(player),
            }

    def _people(self):
        return [{"name": p.name, "role": p.role,
                 "playing": p.thing is not None and p.thing.alive}
                for p in self.players.values()]

    def _you(self, player):
        if player is None:
            return {"role": "owner", "name": "host"}
        return {"role": player.role, "name": player.name,
                "id": player.id,
                "health": player.thing.health if player.thing else None,
                "alive": bool(player.thing and player.thing.alive)}


SESSION = Session()
