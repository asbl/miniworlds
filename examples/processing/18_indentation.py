from miniworldmaker import *

board = PixelBoard()
board.size = (120,210)

@board.register
def on_setup(self):
    print(1)

print(2)

@board.register
def act(self):
    print(3)
print(4)

board.run()
