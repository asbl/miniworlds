from miniworldmaker import *
import random
board = Board(255, 60)
x = 0

while x < 255:
    c = Circle((x, 30), 20)
    c.color = (x,0,0,random.randint(0,255))
    x = x + random.randint(10,50)
    
board.run()
