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


def test_full_game(default_game):
    g = default_game
    g.status("p1")
    g.status("p2")
    g.action("p1", "play_card", "C-Q")
    g.action("p2", "play_card", "D-9")
    g.status("p1")
    g.action("p1", "play_card", "S-9")
    g.action("p2", "play_card", "S-J")
    g.action("p1", "play_card", "S-7")
    g.action("p2", "play_card", "H-7")
    g.action("p1", "take_card")
    g.action("p1", "play_card")
    g.status("p1")
    g.status("p2")
    g.action("p2", "play_card", "H-7")
    g.action("p2", "play_card", "H-J")
    g.action("p1", "take_card")
    g.action("p1", "keep_card")
    g.status("p2")
    assert g.status("p2").get("winner") is None
    g.action("p2", "play_card", "H-A")
    assert g.status("p2").get("winner") == "p2"
    g.status("p2")
    g.action("p1", "play_card")
    g.action("p2", "play_card")
    assert g.status("p2").get("winner") == "p2"
    assert g.status("p1").get("your_deck") == [
        "C-8",
        "C-A",
        "C-Q",
        "S-8",
        "S-K",
        "C-J",
        "D-A",
        "D-J",
    ]


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


def test_special_7a(default_game):
    g = default_game
    # check hand
    assert g.players["p1"].cards == ["S-7", "C-8", "S-9", "C-A", "C-Q"]
    assert g.players["p2"].cards == ["S-J", "H-7", "H-J", "D-9", "H-A"]

    # play cards until ?-7 is possible
    g.action("p1", "play_card", "C-Q")
    g.action("p2", "play_card", "D-9")
    g.action("p1", "play_card", "S-9")
    g.action("p2", "play_card", "S-J")

    # play first 7
    g.action("p1", "play_card", "S-7")
    assert len(g.players["p1"].cards) == 3
    # play 7 against
    g.action("p2", "play_card", "H-7")
    # "p1" has no ?-7 so will get 4 cards
    g.action("p1", "take_card")
    assert len(g.players["p1"].cards) == 3 + 2 + 2


def test_special_7b(default_game):
    g = default_game
    # check hand
    assert g.players["p1"].cards == ["S-7", "C-8", "S-9", "C-A", "C-Q"]
    assert g.players["p2"].cards == ["S-J", "H-7", "H-J", "D-9", "H-A"]

    # play cards until ?-7 is possible
    g.action("p1", "play_card", "C-Q")
    g.action("p2", "play_card", "D-9")
    g.action("p1", "play_card", "S-9")
    g.action("p2", "play_card", "S-J")

    # play first 7
    g.action("p1", "play_card", "S-7")
    assert len(g.players["p2"].cards) == 3
    assert g.status("p2").get("your_turn")
    # don't play 7 - but something else
    g.action("p2", "play_card", "H-A")
    # no card was played, but a message to take_cards
    assert g.status("p2").get("your_turn")
    g.action("p2", "take_cards")
    # the cards can be played, so still in_flow
    assert len(g.players["p2"].cards) == 3
    # play one of the 2 cards
    assert "specify" in g.action("p2", "play_card").get("msg")
    # the error message tells us, to specify one
    g.action("p2", "play_card", "S-8")

    # "p2" has not played a 7, but played a card so it has 1 more card
    assert len(g.status("p2").get("your_deck")) == 3 + 1
    # because of the 8 one more card to play
    g.action("p2", "play_card", "S-K")
    assert len(g.players["p2"].cards) == 3
    # turn ends
    assert g.status("p2").get("current_player") == "p1"


def test_special_8(default_game):
    g = default_game
    g.current_player = "p1"
    # check hand
    assert g.players["p1"].cards == ["S-7", "C-8", "S-9", "C-A", "C-Q"]
    assert g.players["p2"].cards == ["S-J", "H-7", "H-J", "D-9", "H-A"]

    assert g.status("p1").get("deck_top") == "D-K"
    # take cards until C-? is on top
    while True:
        c = next(g.pick_cards(1))
        g.playing_stack.extend([c])
        if c[0] == "C":
            break
    assert len(g.playing_stack) == 4
    assert g.status("p2").get("deck_top") == "C-J"

    # play ?-8
    assert g.status("p1").get("your_turn")
    g.action("p1", "play_card", "C-8")
    # p2 was deferred
    assert g.status("p1").get("your_turn")
