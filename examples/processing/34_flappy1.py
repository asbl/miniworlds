from miniworldmaker import *

board = Board(300, 200)

rect = Rectangle((280,120), 20, 80)

@rect.register
def act(self):
    rect.x -= 1
    if rect.x == 0:
        rect.x = 280

board.run()