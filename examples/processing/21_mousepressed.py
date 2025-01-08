from miniworldmaker import *

board = PixelBoard()

@board.register
def on_setup(self):
    board.size = (200,200)

@board.register
def act(self):
    Ellipse(board.get_mouse_position(), 10, 10) 

@board.register
def on_mouse_left(self, position):
    board.fill_color = (255, 0, 0)
    
@board.register
def on_mouse_right(self, position):
    board.fill_color = (255, 255, 255)
    
board.run()

