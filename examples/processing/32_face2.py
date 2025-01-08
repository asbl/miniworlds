from miniworldmaker import *
import random
board = PixelBoard((100,100))
bg = Circle.from_center((50,50),50)
bg.fill_color = (0,0,0)
Arc.from_center((50,80),40,20, 180, 360)
Circle.from_center((30,30),10)
Circle.from_center((70,30),10)

c = Circle.from_center((70,30),5)
d = Circle.from_center((30,30),5)
c.fill_color = (0, 0, 0)
d.fill_color = (0, 0, 0)
Line((50,50),(50,70))
board.run()
