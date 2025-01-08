from miniworldmaker import *

board = PixelBoard()
board.size = (120,210)

@board.register
def on_setup(self):
    print("setup")
    
@board.register
def act(self):
    print("act")

board.run()
