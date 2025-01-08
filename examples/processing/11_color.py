from miniworldmaker import *

board = Board(350, 150)
r = Rectangle((10,10), 100, 100)
r.fill_color = (255, 0, 0)

g = Rectangle((120,10), 100, 100)
g.fill_color = (0, 255,0)

b = Rectangle((230,10), 100, 100)
b.fill_color = (0, 0 ,255)

board.run()