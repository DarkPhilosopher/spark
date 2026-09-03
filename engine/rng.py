"""The world's source of luck, in a form JavaScript can copy exactly.

Spark now has two engines: this one, and the one inside world3d.html that runs
when no server is reachable. A test drives both over the same game and demands
the same board every tick -- which is only possible if they roll the same dice.

Python's own `random` cannot be that shared source. It is a Mersenne Twister,
and reimplementing it in JavaScript to the bit is far more trouble than the
guarantee is worth. So a seeded world uses the small generator below instead:
an ordinary linear congruential generator, chosen because both languages can
run it in exact integer arithmetic.

    Rng(None)   the system's randomness, exactly as before -- real play
    Rng(7)      the same sequence every time, in both languages -- tests

The arithmetic stays exact in JavaScript too: the largest intermediate value
is (2**32 - 1) * 1664525, about 7.2e15, which is under the 2**53 where doubles
start rounding. Keep it that way if you ever change the constants.
"""

import random as _system

MOD = 2 ** 32
MULT = 1664525
ADD = 1013904223


class Rng:
    """Dice. Seeded ones are reproducible; unseeded ones are the real thing."""

    def __init__(self, seed=None):
        self.seeded = seed is not None
        self.state = int(seed) % MOD if self.seeded else 0

    def _next(self):
        self.state = (self.state * MULT + ADD) % MOD
        return self.state

    def randrange(self, n):
        """A whole number from 0 to n-1."""
        if n <= 0:
            raise ValueError("randrange needs a positive number, got %r" % (n,))
        if not self.seeded:
            return _system.randrange(n)
        return self._next() % n

    def choice(self, seq):
        """One item out of seq. Order matters -- pass a list, never a set."""
        seq = list(seq)
        if not seq:
            raise IndexError("cannot choose from nothing")
        if not self.seeded:
            return _system.choice(seq)
        return seq[self._next() % len(seq)]
