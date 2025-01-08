from miniworldmaker import *

board = Board(600,400)
board.add_background("images/sunflower.jpg")
arr = board.background.to_colors_array()
grey_arr = arr.copy()

def brightness(r, g, b):
    return (int(r) + int(g) + int(b)) / 3

def in_array(arr, x, y):
    if x >= 0 and x < len(arr):
        if y >= 0 and y < len(arr[0]):
            return True
    return False
    

def neighbour_cells(arr, x, y):
    neighbours = []
    for x0 in range(x-1, x+1):
        for y0 in range(y-1, y+1):
            if in_array(arr, x0, y0):
                neighbours.append(arr[x0][y0])
    return neighbours

for x in range(len(arr)):
    for y in range(len(arr[0])):
        grey_arr[x][y] = brightness(arr[x][y][0], arr[x][y][1], arr[x][y][2])

for x in range(len(arr)):
    for y in range(len(arr[0])):
        neighbours = neighbour_cells(grey_arr, x, y)
        sum_neighbours = 0
        for neighbour in neighbour_cells(grey_arr, x, y):
            sum_neighbours += neighbour[0]
        mean_neighbours = sum_neighbours / len(neighbours)
        diff = grey_arr[x][y][0] - mean_neighbours
        if diff > 5:
            arr[x][y] = (0, 0, 0)
        else:
            arr[x][y] = (255, 255, 255)

#for x in range(len(arr)):
#    for y in range(len(arr[0])):
#        arr[x][y][0] = 255 - arr[x][y][0]
#        arr[x][y][1] = 255 - arr[x][y][1]
#        arr[x][y][2] = 255 - arr[x][y][2]
        
board.background.from_array(arr)
board.run()


