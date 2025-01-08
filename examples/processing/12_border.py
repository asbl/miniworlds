from miniworldmaker import *

board = Board(350, 150)
r = Rectangle((10,10), 100, 100)
r.is_filled = False
r.border = 10
r.border_color = (0, 255,0)

board.run()