from miniworldmaker import *

board = Board(200, 50)

for i in range(4):
    rect = Rectangle((50 * i, 0), 50, 50)
    if i % 2 == 0:
        rect.color = (255,0,0, 255)
    else:
        rect.color = (255, 255, 255, 255)
    
board.run()

