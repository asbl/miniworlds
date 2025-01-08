from miniworldmaker import *

board = Board()
arr = board.background.to_colors_array()
print(arr)
for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y][0] = ((x +1 ) / board.width) * 255
        arr[x][y][1] = ((y +1 ) /board.width) * 255
board.background.from_array(arr)
board.run()