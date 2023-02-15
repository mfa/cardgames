import random

import pytest

from .maumau import Game


def test_new():
    random.seed(2)
    g = Game()
    g.new("g1", ["p1", "p2"])
    assert (
        len(g.playing_stack)
        + len(g.stack)
        + sum([len(p.cards) for p in g.players.values()])
        == 32
    )
    g.status()
    while True:
        g.next_turn()
