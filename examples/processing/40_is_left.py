from miniworldmaker import *
import random

board = Board(400, 50)
        

def is_left(obj):
    if obj.center.x <= 200:
        return True
    else:
        return False

for i in range(20):
    x = random.randint(0,400)
    y = 25
    c = Circle((x, y), 10)
    if is_left(c):
        c.color = (255,0,0)


board.run()
