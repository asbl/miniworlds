# Image Processing

## What Are Images

Images consist of tiny pixels, each with a specific color.

Image processing means changing and manipulating these pixels based on certain criteria.

To do this, we use `arrays`, which are a special form of lists (arrays have fixed sizes).

## Loading the Background

In miniworlds, we can load the background using:

```python
arr = background.to_colors_array()
```

```python
from miniworlds import *

world = World()
arr = world.background.to_colors_array()
print(arr)
world.run()
```

The result is a nested, two-dimensional array:

Each innermost list represents a 3-tuple of color values, e.g., \[150, 150, 150], describing the red, green, and blue components. Each component ranges from 0 to 255.

The image array consists of:

* A list of columns
* Each column contains a row for each pixel with a color value

## Modifying the Background

```python
from miniworlds import *

world = World()
arr = world.background.to_colors_array()
for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y][0] = 0
print(arr)
world.run()
```

```python
from miniworlds import *

world = World()
arr = world.background.to_colors_array()
for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y][0] = 0
world.background.from_array(arr)
world.run()
```

```python
from miniworlds import *

world = World()
arr = world.background.to_colors_array()
for x in range(0, len(arr), 2):
    for y in range(len(arr[0])):
        arr[x][y][0] = 0
print(arr)
world.background.from_array(arr)
world.run()
```

```python
from miniworlds import *

world = World()
arr = world.background.to_colors_array()
for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y][0] = ((x + 1) / world.width) * 255
world.background.from_array(arr)
world.run()
```

```python
from miniworlds import *

world = World()
arr = world.background.to_colors_array()
for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y][1] = ((y + 1) / world.width) * 255
world.background.from_array(arr)
world.run()
```

```python
from miniworlds import *

world = World()
arr = world.background.to_colors_array()
for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y][0] = ((x + 1) / world.width) * 255
        arr[x][y][1] = ((y + 1) / world.width) * 255
world.background.from_array(arr)
world.run()
```

## Image Processing

```python
from miniworlds import *

world = World(600, 400)
world.add_background("images/sunflower.jpg")
arr = world.background.to_colors_array()
for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y][0] = 0
world.background.from_array(arr)
world.run()
```

```python
from miniworlds import *

world = World(600, 400)
world.add_background("images/sunflower.jpg")
arr = world.background.to_colors_array()
constant = 2
for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y][0] = arr[x][y][0] * constant
        arr[x][y][1] = arr[x][y][1] * constant
        arr[x][y][2] = arr[x][y][2] * constant
world.background.from_array(arr)
world.run()
```

```python
from miniworlds import *

world = World(600, 400)
world.add_background("images/sunflower.jpg")
arr = world.background.to_colors_array()
constant = 2
for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y][0] = min(arr[x][y][0] * constant, 255)
        arr[x][y][1] = min(arr[x][y][1] * constant, 255)
        arr[x][y][2] = min(arr[x][y][2] * constant, 255)
world.background.from_array(arr)
world.run()
```

# Image Processing II (with Functions)

## Brightness

```python
from miniworlds import *

world = World(600, 400)
world.add_background("images/sunflower.jpg")
arr = world.background.to_colors_array()

def brightness(r, g, b):
    return (int(r) + int(g) + int(b)) / 3

print(brightness(arr[10][20]))

world.background.from_array(arr)
world.run()
```

```python
from miniworlds import *

world = World(600, 400)
world.add_background("images/sunflower.jpg")
arr = world.background.to_colors_array()

def brightness(r, g, b):
    return (int(r) + int(g) + int(b)) / 3

for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y] = brightness(arr[x][y][0], arr[x][y][1], arr[x][y][2])

world.background.from_array(arr)
world.run()
```

## Edge Detection

```python
from miniworlds import *

world = World(600, 400)
world.add_background("images/sunflower.jpg")
arr = world.background.to_colors_array()
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
    for x0 in range(x - 1, x + 1):
        for y0 in range(y - 1, y + 1):
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
        arr[x][y] = (diff, diff, diff)

world.background.from_array(arr)
world.run()
```

```python
for x in range(len(arr)):
    for y in range(len(arr[0])):
        arr[x][y][0] = 255 - arr[x][y][0]
        arr[x][y][1] = 255 - arr[x][y][1]
        arr[x][y][2] = 255 - arr[x][y][2]
```
