from miniworldmaker import *
import random
board = PixelBoard()

@board.register
def on_setup(self):
    board.size = (200,200)

@board.register
def on_key_down_a(self):
    a = Ellipse.from_center((100, 100), 100, 100) 
    a.fill_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    
board.run()

