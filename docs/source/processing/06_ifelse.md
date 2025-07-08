# Conditionals (If Statements)

You need conditionals whenever your program should behave differently based on a certain condition.

---

### First Example

For example, if you want to check whether a player has reached a certain score in your game, you can write:

```python
if points > 100:
    print("You have won!")
```

---

### General Syntax

```python
if <condition>:
    <code block>
```

---

### Boolean Expressions

A **condition** is an expression that evaluates to `True` or `False`. Such expressions are called **boolean expressions**.

The simplest boolean expressions are just `True` and `False`. But you usually create them using **comparisons**, for example:

```python
10 < 100     # True
110 < 100    # False
x < 10       # True, if x is less than 10
"a" == "b"   # False
3 == 4       # False
"ab" == "ab" # True
```

These expressions can include variables and be more complex.

> ⚠️ **Note:** Use `==` for comparisons. A single `=` is used for assignments!

---

### Comparison Operators

Here are the most common comparison operators:

* `<` : less than
* `<=`: less than or equal
* `==`: equal
* `>=`: greater than or equal
* `>` : greater than

---

### Code Blocks

If you want to run multiple statements when a condition is true, group them in a code block using indentation:

```python
if points > 100:
    print("You have won!")
    print("Congratulations")
print("The game is over")
```

The first two lines will only run if `points > 100`. The last line runs regardless.

---

## Elif and Else

Use `elif` (else-if) and `else` for alternative branches:

```python
if points > 100:
    print("You have won!")
    print("Congratulations")
elif points > 50:
    print("You lost by a narrow margin")
else: 
    print("You have clearly lost")
```

General syntax:

```python
if <condition>:
    <code>
elif <condition>:
    <code>
else:
    <code>
```

You can use as many `elif` branches as needed. `else` and `elif` are optional.

---

## Complete Example

A rectangle moves from right to left. When it reaches the left edge, it should reappear on the right.

Initial version:

```python
from miniworlds import *

world = World(300, 200)
rect = Rectangle((280, 120), 20, 80)

@rect.register
def act(self):
    rect.x -= 1

world.run()
```

Now add the logic to reset its position:

```python
from miniworlds import *

world = World(300, 200)
rect = Rectangle((280, 120), 20, 80)

@rect.register
def act(self):
    rect.x -= 1
    if rect.x == 0:
        rect.x = 280

world.run()
```

---

## Another Example – Simple Flappy Bird

Let’s program a basic version of Flappy Bird.

We’ll use a ball that falls down and jumps up on key press:

```python
from miniworlds import *

world = World(300, 200)

rect = Rectangle((280, 120), 20, 80)
ball = Circle((20, 50), 20)
velocity = 1

@rect.register
def act(self):
    rect.x -= 1
    if rect.x == 0:
        rect.x = 280

@ball.register
def act(self):
    global velocity
    self.y += velocity
    if world.frame % 10 == 0:
        velocity += 1

world.run()
```

Add a key press to make the ball jump:

```python
@ball.register
def on_key_down(self, key):
    global velocity
    velocity = -2
```

---

### Collision Detection

Now let’s detect if the ball hits the rectangle using a **sensor**:

```python
@ball.register
def act(self):
    global velocity
    self.y += velocity
    if world.frame % 10 == 0:
        velocity += 1
    actor = self.detect_actor()
    if actor == rect:
        self.world.stop()
```

These lines detect a collision and stop the world:

```python
actor = self.detect_actor()
if actor == rect:
    self.world.stop()
```

The final result is a simple Flappy Bird-like game.

<video controls loop width=300px>
  <source src="../_static/flappy.webm" type="video/webm">
  Your browser does not support the video tag.
</video>
