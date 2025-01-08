import levels


class LevelManager:
    def __init__(self):
        """LevelFelix1(self), LevelBruno1(self),"""
        self.levels = [
            levels.Level1(self),
            levels.Level2(self),
            levels.Level3(self),
            levels.Level4(self),
            levels.Level5(self),
            levels.Level6(self),
            levels.Level7(self),
            levels.Level8(self),
            levels.LevelBruno1(self),
            levels.LevelEnd(self),
        ]
        self.actual_level = 0

    def next_level(self):
        next_level = self.actual_level + 1
        print("############# NEXT LEVEL", self.levels[next_level])
        if next_level < len(self.levels):
            self.get_current().switch_world(self.levels[next_level])
            self.actual_level = next_level

    def first_level(self):
        self.get_current().switch_world(self.levels[0])
        self.actual_level = 0

    def get_current(self):
        return self.levels[self.actual_level]

    def same_level(self):
        print("############# SAME LEVEL")
        self.get_current().switch_world(self.levels[self.actual_level], reset = True)
