from miniworldmaker import *

board = PixelBoard()

@board.register
def on_setup(self):
    board.size = (200,200)

@board.register
def act(self):
    Line(board.get_prev_mouse_position(), board.get_mouse_position()) 

board.run()

