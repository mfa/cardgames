import random
from dataclasses import dataclass, field
from functools import cache


@dataclass
class Player:
    id: str
    cards: list[str]
    in_flow: list[str] = field(default_factory=list)


class Game:
    deck = ["7", "8", "9", "10", "J", "Q", "K", "A"]
    suites = ["H", "D", "S", "C"]

    players = {}
    next_player_take_cards = 0

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
            _cards = player.in_flow
            cards.extend(player.in_flow)
            player.in_flow = None
            player.cards = cards
            self.current_player = self.next_player()
            return {"msg": f"you kept {_cards}"}
        if action == "play_card":
            if card and not card.endswith("-7") and self.next_player_take_cards:
                return {
                    "msg": "on a 7 you are only allowed to play a 7, 'take_cards' otherwise"
                }
            if len(player.in_flow) == 1:
                card = player.in_flow
            elif len(player.in_flow) > 1 and card is None:
                return {"msg": "specify card to play"}
            elif card in player.in_flow:
                pass
            else:
                if card not in player.cards:
                    return {"msg": f"card is not on your hand: {card}"}
            if self.check_card(card):
                if player.in_flow:
                    self.playing_stack.append(card)
                    player.in_flow.pop(player.in_flow.index(card))
                    if player.in_flow:
                        cards.extend(player.in_flow)
                    player.in_flow = []
                else:
                    self.playing_stack.append(cards.pop(cards.index(card)))
                if self.check_win():
                    winner = self.check_win()["winner"]
                    return {"msg": f"{winner} has won!"}

                if card.endswith("-7"):
                    self.next_player_take_cards += 2
                if card.endswith("-8"):
                    # jump over next player
                    self.current_player = self.next_player()

                self.current_player = self.next_player()
                return {"msg": f"card played: {card}"}
            else:
                if player.in_flow:
                    cards.extend(player.in_flow)
                    player.in_flow = None
                    player.cards = cards
                    self.current_player = self.next_player()
                    return {"msg": f"card {card} is not allowed, move to your cards"}
                return {"msg": "card is not allowed"}
        elif action.startswith("take_card"):
            num_cards = 1
            if self.next_player_take_cards > 0:
                num_cards = self.next_player_take_cards
                self.next_player_take_cards = 0

            _cards = list(self.pick_cards(num_cards))
            self.players[self.current_player].in_flow = _cards
            _playable = False
            for card in _cards:
                if self.check_card(card):
                    _playable = True
            if _playable:
                return {"msg": f"you draw {_cards}, 'play_card' or 'keep_card'?"}
            cards.extend(_cards)
            player.cards = cards
            self.current_player = self.next_player()
            return {"msg": f"you draw {_cards}"}
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
