# Colors and Outlines

## Filling Shapes with Color

You can fill a geometric shape with color using the `fill_color` attribute:

```python
from miniworlds import *

world = World(350, 150)
r = Rectangle((10, 10), 100, 100)
r.fill_color = (255, 0, 0)

g = Rectangle((120, 10), 100, 100)
g.fill_color = (0, 255, 0)

b = Rectangle((230, 10), 100, 100)
b.fill_color = (0, 0, 255)

world.run()
```

A **color** is specified as a 3-tuple:

* The first value is the *red* component
* The second value is the *green* component
* The third value is the *blue* component

By mixing these values, you get a specific color:

<img src="../_images/processing/rgb.png" alt="rgb colors" width="260px"/>

### Variables

Here we used *variables*. In previous examples, we created objects without assigning them names, so we couldn’t refer to them later.
In this case, we gave names to the rectangles (e.g., `r`), so we can access and modify them later.

For example, `r.fill_color = (255, 0, 0)` means we are changing the fill color of the rectangle named `r`.

---

## Border

Any geometric shape can have a **border**.
You can set the border’s thickness using the `border` attribute (an integer), and its color with `border_color`.

The following example creates a red rectangle with a yellow border:

```python
from miniworlds import *

world = World(350, 150)
r = Rectangle((10, 10), 100, 100)
r.fill_color = (255, 0, 0)
r.border = 3
r.border_color = (255, 255, 0)

world.run()
```

Output:

<img src="../_images/processing/border.png" alt="borders" width="260px"/>

---

## Fill Toggle

You can also create shapes with only a border and no fill.
Use the `fill` attribute to control whether the shape has a fill.

This rectangle has no fill:

```python
from miniworlds import *

world = World(350, 150)
r = Rectangle((10, 10), 100, 100)
r.fill = False
r.border = 3
r.border_color = (255, 255, 0)

world.run()
```

---

## The World

All shapes are drawn on a `World`.
The `World` itself has properties like size and background color that can be customized.

See the following example, which sets the size and background color:

```python
from miniworlds import *

world = World()
world.add_background((255, 255, 255))
world.size = (400, 200)

r = Rectangle((10, 10), 100, 100)
r.fill = False
r.border = 3
r.border_color = (255, 255, 0)

world.run()
```

---

## 🧠 Training

### Exercise 2.1: Black Face

Draw the following shape:

![Face](../_images/processing/face2.png)

<details>
<summary><strong>Solution hint</strong></summary>

```python
from miniworlds import *

world = World()
world.size = (120, 210)
Rectangle((10, 100), 100, 100)
Triangle((10, 100), (60, 50), (110, 100))

world.run()
```

</details>
