import random


class Player:
    def __init__(self, name, batting_average, home_run_rate, strikeout_rate, bats="R"):
        self.name = name
        self.batting_average = batting_average
        self.home_run_rate = home_run_rate
        self.strikeout_rate = strikeout_rate
        self.bats = bats

    def introduce(self):
        print(f"Player: {self.name} (Bats: {self.bats})")
        print(f"Batting Average: {self.batting_average}")
        print(f"Home Run Rate: {self.home_run_rate}")
        print(f"Strikeout Rate: {self.strikeout_rate}")