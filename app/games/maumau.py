import random
from dataclasses import dataclass
from functools import cache
from typing import List


@dataclass
class Player:
    id: str
    cards: List[str]
    in_flow: str | None = None


class Game:
    deck = ["7", "8", "9", "10", "J", "Q", "K", "A"]
    suites = ["H", "D", "S", "C"]

    players = {}

    def __init__(self, name, players):
        self.name = name
        self.stack = random.sample(
            list(self.create_stack()), k=len(self.deck) * len(self.suites)
        )

        self.player_list = players
        for player in self.player_list:
            self.players[player] = Player(id=player, cards=list(self.pick_cards(num=5)))
        self.playing_stack = list(self.pick_cards(1))

        # random order players
        random.shuffle(self.player_list)
        self.current_player = self.player_list[0]

    @property
    @cache
    def allowed_cards(self):
        return list(self.create_stack())

    def create_stack(self):
        for suite in self.suites:
            for card in self.deck:
                yield suite + "-" + card

    def pick_cards(self, num):
        for i in range(num):
            if not self.stack:
                self.stack = self.playing_stack[:-1]
                random.shuffle(self.stack)
                self.playing_stack = [self.playing_stack[-1]]
            card = self.stack.pop()
            yield card

    def status(self, player):
        d = {
            "players": self.player_list,
            "current_player": self.current_player,
            "deck_top": self.playing_stack[-1],
            "your_turn": True if self.current_player == player else False,
            "your_deck": self.players[player].cards,
        }
        if self.check_win():
            d["winner"] = self.check_win()["winner"]
        return d

    def action(self, player, action, card=None):
        if player != self.current_player:
            return {"msg": f"Not your turn. current turn is: {self.current_player}"}

        if self.check_win():
            winner = self.check_win()["winner"]
            return {"msg": f"game over, winner: {winner}"}

        player = self.players[self.current_player]
        cards = player.cards
        if action == "keep_card" and player.in_flow:
            card = player.in_flow
            cards.append(player.in_flow)
            player.in_flow = None
            player.cards = cards
            self.current_player = self.next_player()
            return {"msg": f"you kept {card}"}
        if action == "play_card":
            if player.in_flow:
                card = player.in_flow
            else:
                if card not in player.cards:
                    return {"msg": f"card is not on your hand: {card}"}
            if self.check_card(card):
                if player.in_flow:
                    self.playing_stack.append(player.in_flow)
                    player.in_flow = None
                else:
                    self.playing_stack.append(cards.pop(cards.index(card)))
                player.cards = cards
                if self.check_win():
                    winner = self.check_win()["winner"]
                    return {"msg": f"{winner} has won!"}
                self.current_player = self.next_player()
                return {"msg": f"card played: {card}"}
            else:
                if player.in_flow:
                    cards.append(player.in_flow)
                    player.in_flow = None
                    player.cards = cards
                    self.current_player = self.next_player()
                    return {"msg": f"card {card} is not allowed, move to your cards"}
                return {"msg": "card is not allowed"}
        elif action == "take_card":
            card = list(self.pick_cards(1))[0]
            self.players[self.current_player].in_flow = card
            return {"msg": f"you draw {card}, 'play_card' or 'keep_card'?"}
        return {"msg": "allowed actions: 'play_card', 'take_card'"}

    def check_win(self):
        for player_id in self.players:
            player = self.players[player_id]
            if not player.cards:
                return {"winner": player.id}

    def next_player(self):
        cur = self.player_list.index(self.current_player)
        cur += 1
        if cur == len(self.player_list):
            cur = 0
        return self.player_list[cur]

    def check_card(self, card):
        if card not in self.allowed_cards:
            return None
        s, d = card.split("-")
        _s, _d = self.playing_stack[-1].split("-")
        if s == _s or d == _d:
            return True
        return False
