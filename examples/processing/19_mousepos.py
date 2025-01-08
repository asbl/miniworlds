from miniworldmaker import *

board = PixelBoard()

@board.register
def act(self):
    c = Circle(board.get_mouse_position(), 40)
    c.color = (255,255,255, 100)
    c.border = None

board.run()

