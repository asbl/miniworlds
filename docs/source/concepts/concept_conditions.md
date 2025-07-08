# Concept: Branching

You need **branches** whenever the flow of your program should depend on certain conditions.

---

## First Example

For example, in a game you might want to check if a certain number of points has been reached:

```python
if points > 100:
    print("You have won!")
```

---

## General Syntax

This is the general syntax of a conditional statement:

```python
if <condition>:
    <code block>
```

---

## Boolean Expressions

A condition is an expression that evaluates to either `True` or `False` – such expressions are called **boolean expressions**.

The simplest ones are `True` and `False`. More useful expressions are based on **comparisons**:

```python
10 < 100        # True
110 < 100       # False
x < 10          # Depends on x
"a" == "b"      # False
3 == 4          # False
"ab" == "ab"    # True
```

You can build arbitrarily complex expressions involving variables.

```{warning}
⚠️ Attention: For comparisons use **double equals (`==`)** – not a single equals (`=`), which is used for assignment!
```

---

## Comparison Operators

You can use the following comparison operators:

* `<`  : less than
* `<=` : less than or equal
* `==`: equal
* `>=`: greater than or equal
* `>`  : greater than

---

## Code Blocks

If you want to execute **multiple lines of code** when the condition is met, you use **code blocks**, i.e., **indented** lines below the `if` statement.

Example:

```python
if points > 100:
    print("You have won!")
    print("Congratulations")
print("The game is over")
```

The last line is always executed. The indented lines only run if `points > 100`.

---

## `elif` and `else`

With `elif` and `else`, you can build **alternatives**:

```python
if points > 100:
    print("You have won!")
    print("Congratulations")
elif points > 50:
    print("You lost by a narrow margin")
else:
    print("You have clearly lost")
```

### Syntax:

```python
if <condition>:
    <code block>
elif <condition>:
    <code block>
else:
    <code block>
```

You can skip `elif` or `else`, and use multiple `elif`s if needed.

---

## Detailed Example – Moving a Rectangle

A rectangle moves from right to left. If it reaches the left edge, it should reappear on the right.

Version 1:

```python
import miniworlds

world = miniworlds.World(300, 200)
rect = miniworlds.Rectangle((280, 120), 20, 80)

@rect.register
def act(self):
    rect.x -= 1

world.run()
```

Now let’s reset the position:

```python
@rect.register
def act(self):
    rect.x -= 1
    if rect.x == 0:
        rect.x = 280
```

---

## Another Example – A Simple Flappy Bird

We want a **ball** to move up when a key is pressed, and fall down otherwise (gravity).

```python
import miniworlds

world = miniworlds.World(300, 200)
rect = miniworlds.Rectangle((280, 120), 20, 80)
ball = miniworlds.Circle((20, 50), 20)
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

@ball.register
def on_key_down(self, key):
    global velocity
    velocity = -2

world.run()
```

The ball falls, and gets faster due to gravity. When a key is pressed, it jumps up.

---

## Collisions

You can also check whether **two objects touch each other** using **sensor methods** like `detect_actor()`:

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

This checks if the ball collides with the rectangle. If so, the game ends.

---

## Final Result – Flappy Bird Prototype

<video controls loop width=300px>
  <source src="../_static/flappy.webm" type="video/webm">
  Your browser does not support the video tag.
</video>
