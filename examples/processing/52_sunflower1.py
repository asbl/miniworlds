from miniworldmaker import *

board = Board(600,400)
board.add_background("images/sunflower.jpg")
arr = board.background.to_colors_array()
constant = 1
for x in range(len(arr)):
    for y in range(len(arr[0])):
        for color in arr[x][y]:
            color = color * constant
            if color > 255:
                color = 255
board.background.from_array(arr)
board.run()