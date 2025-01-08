from miniworldmaker import *

board = PixelBoard()
board.size = (120,210)

@board.register
def on_setup(self):
    board.fps = 1
    board.speed = 3
    
@board.register
def act(self):
    print(board.frame)

board.run()
