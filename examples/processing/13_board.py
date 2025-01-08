from miniworldmaker import *

board = PixelBoard()
board.add_background((255,255,255))
board.size = (400,200)
r = Rectangle((10,10), 100, 100)
r.is_filled = False
r.border = 3
r.border_color = (255, 255,0)

board.run()