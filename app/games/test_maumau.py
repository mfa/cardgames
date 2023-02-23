import random

import pytest

from .maumau import Game


@pytest.fixture
def default_game():
    random.seed(2)
    return Game("g1", ["p1", "p2"])


def test_new(default_game):
    g = default_game
    assert (
        len(g.playing_stack)
        + len(g.stack)
        + sum([len(p.cards) for p in g.players.values()])
        == 32
    )
    assert g.status("p1")


def test_valid_game(default_game):
    g = default_game
    g.status("p1"),
    g.status("p2"),
    g.action("p1", "play_card", "C-Q"),
    g.action("p2", "play_card", "D-9"),
    g.status("p1"),
    g.action("p1", "play_card", "S-9"),
    g.action("p2", "play_card", "S-J"),
    g.action("p1", "play_card", "S-7"),
    g.action("p2", "play_card", "H-7"),
    g.action("p1", "take_card"),
    g.action("p1", "play_card"),
    g.status("p1"),
    g.status("p2"),
    g.action("p2", "play_card", "H-7"),
    g.action("p2", "play_card", "H-J"),
    g.action("p1", "take_card"),
    g.action("p1", "keep_card"),
    g.status("p2"),
    g.action("p2", "play_card", "H-A"),
    g.status("p2"),
    g.action("p1", "play_card"),
    g.action("p2", "play_card"),


def test_illegal_moves(default_game):
    g = default_game
    g.action("p2", "play_card", "D-9"),
    g.action("p1", "play_card", "C-Q"),
    g.action("p2", "play_card", "A-A"),
    g.action("p2", "play_card", "XX"),


def test_check_card(default_game):
    g = default_game
    assert g.status("p2")["deck_top"] == "D-K"
    assert g.check_card("A-B") == None
    assert g.check_card("D-9") == True
    assert g.check_card("H-9") == False


def test_take_all_cards(default_game):
    g = default_game
    assert len(g.stack) == len(g.allowed_cards) - len(g.players) * 5 - 1
    assert len(list(g.pick_cards(1))) == 1

    # one card on playing stack
    assert len(g.playing_stack) == 1
    assert g.status("p1").get("deck_top") == "D-K"
    # take 18 cards
    lots_of_cards = list(g.pick_cards(18))
    assert len(lots_of_cards) == 18
    # play 18 cards on top of the deck
    g.playing_stack.extend(lots_of_cards)
    assert len(g.playing_stack) == 1 + 18
    assert g.status("p1").get("deck_top") == "C-K"

    assert len(g.stack) == 2
    # take more cards than in there:
    # 2 (from stack); 1 from playing_stack
    assert len(list(g.pick_cards(3))) == 3
    # reshuffle from playing_stack happend
    assert len(g.stack) == 17
    assert len(g.playing_stack) == 1
    # the same card is still on top in the playing stack
    assert g.status("p1").get("deck_top") == "C-K"
