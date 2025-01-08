from miniworldmaker import *
from random import randint

WIDTH = 600
HEIGHT = 400

board = Board(WIDTH, HEIGHT)

board.add_background((235, 215, 182))

for _ in range(200):
    x = randint(15, WIDTH -15)
    y = randint(10, HEIGHT - 15)
    w = randint(10, 50)
    h = randint(10,50)
    
    rect = Rectangle((x, y), w, h)
    
    r = randint(10, 200)
    g = randint(10, 200)
    b = randint(10, 200)
    alpha = 0.7 * 255
    
    rect.color = (r, g, b, alpha)
    
print("I did it, Babe")
board.run()