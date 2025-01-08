from miniworldmaker import *

board = PixelBoard()

@board.register
def on_setup(self):
    board.size = (200,200)

@board.register
def on_key_down_a(self):
    a = Ellipse.from_center((100, 100), 100, 100) 
    a.fill_color = (255, 0, 0)

@board.register
def on_key_down_b(self):
    a = Ellipse.from_center((100, 100), 100, 100) 
    a.fill_color = (0, 255, 0)

    
board.run()

