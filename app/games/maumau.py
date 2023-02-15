import random
from dataclasses import dataclass
from typing import List


@dataclass
class Player:
    id: str
    cards: List[str]


class Game:
    deck = ["7", "8", "9", "10", "J", "Q", "K", "A"]
    suites = ["H", "D", "S", "C"]

    players = {}

    def __init__(self):
        pass

    def load(self, name):
        pass

    def new(self, name, players):
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

    def create_stack(self):
        for suite in self.suites:
            for card in self.deck:
                yield suite + "-" + card

    def pick_cards(self, num):
        for i in range(num):
            yield self.stack.pop()

    def status(self):
        print("stack", self.stack)
        for k, v in self.players.items():
            print(k, v)
        print("playing stack", self.playing_stack)

    def next_player(self):
        cur = self.player_list.index(self.current_player)
        cur += 1
        if cur == len(self.player_list):
            cur = 0
        return self.player_list[cur]

    def next_turn(self):
        print(self.current_player)
        print("playing stack:", self.playing_stack[-1])
        cards = self.players[self.current_player].cards
        print(cards)
        while True:
            card = input("which card: ")
            if card in cards:
                # check if card is allowed
                if self.check_card(card):
                    self.playing_stack.append(cards.pop(cards.index(card)))
                    break
                print("card is not allowed")
            else:
                if card == "N":
                    card = list(self.pick_cards(1))[0]
                    cards.append(card)
                    print("new card: ", card)
                    if self.check_card(card):
                        x = input("play new card [y/n]?")
                        if x == "y":
                            self.playing_stack.append(cards.pop(cards.index(card)))
                    break
                else:
                    print("invalid card")
        self.players[self.current_player].cards = cards
        self.current_player = self.next_player()

    def check_card(self, card):
        s, d = card.split("-")
        _s, _d = self.playing_stack[-1].split("-")
        if s == _s or d == _d:
            return True
        return False
