class Pitcher:
    def __init__(self, name, era, strikeout_rate, walk_rate, throws="R"):
        self.name = name
        self.era = era
        self.strikeout_rate = strikeout_rate
        self.walk_rate = walk_rate
        self.throws = throws  # L or R

    def introduce(self):
        print(f"Pitcher: {self.name} (Throws: {self.throws})")
        print(f"ERA: {self.era}")
        print(f"Strikeout Rate: {self.strikeout_rate}")
        print(f"Walk Rate: {self.walk_rate}")