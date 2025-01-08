from miniworldmaker import *

board = PixelBoard()
board.size = (600,300)

text = Text((200,100), "Hello World")
text.border = 1
text.font_size = 100
text.direction = 5
board.run()