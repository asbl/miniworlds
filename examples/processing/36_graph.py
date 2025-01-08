from miniworldmaker import *

board = Board(400, 400)


for x in range(400):
    gl = 0.5*x + 50
    y = 400 - gl
    Point((x, y))
    
board.run()

