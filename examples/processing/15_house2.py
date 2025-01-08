from miniworldmaker import *

board = PixelBoard()
board.size = (120,210)
Rectangle((10,100), 100, 100)
Triangle((10,100), (60, 50), (110, 100))

board.run()