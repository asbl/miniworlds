# Positioning and Orientation of Actors

In this section, you’ll learn how to position and orient actors within the coordinate system.

### Basics

First, a quick recap of the core concepts:

* You can create an actor at any position:

  ```python
  actor = Actor((50, 120))  # creates an actor at position (50, 120)
  ```
* The coordinate system has its origin at the **top-left corner**:

  ```{figure} ../_images/tutorial_addactor_coord.png
  :scale: 30 %
  :alt: The coordinate system
  ```
* The position of an actor always refers to its **center** (also called its origin point).

---

## Changing an Actor’s Position Later

You can also adjust an actor’s position after it has been created by using the `x`, `y`, or `position` attributes:

```python
my_actor.x = 120          # sets the x-coordinate to 120  
my_actor.y = 90           # sets the y-coordinate to 90  
my_actor.position = (120, 90)  # sets position to x=120, y=90
```

---

## Changing an Actor’s Direction

An actor’s orientation can be controlled via the `direction` attribute.
This allows you to rotate the actor to face a specific direction:

The image below shows how the `direction` values are interpreted:

```{figure} ../_images/movement.jpg
  :scale: 30 %
  :alt: Actor orientation

  The meaning of `direction`:
  * 0 → up  
  * 90 → right | -90 → left  
  * 180 or -180 → down
```

---

## Changing the Actor’s Origin

You can change the **origin** (i.e., the point that defines the actor’s position) using the `origin` attribute:

```python
a1 = Actor((0, 20))
a1.origin = "topleft"  # sets the origin to the top-left corner
```

```{figure} ../_images/pixel_coordinates.png
  :scale: 30 %
  :alt: Actor origin

  (0|20) now refers to the top-left corner of the actor.
```

---

You can also set the center or top-left corner of an actor explicitly:

```python
a1 = miniworlds.Actor((0, 20))
a1.topleft = (20, 30)   # sets the actor’s top-left corner to (20, 30)
a1.center = (20, 30)    # sets the actor’s center to (20, 30)
```
