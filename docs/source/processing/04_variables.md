# Values and Variables

A **value** is something that can be stored in a computer and manipulated by a computer program.
In this tutorial, values are referred to as **objects**, and the terms are used interchangeably.

> **Note**:
> In other programming languages, a distinction is made between *primitive data types* (which can only store values) and *objects* (which also have attributes and methods).
> For example, the `world` class has an attribute `size` and a method `add_background`.
>
> Python follows a simple philosophy: **everything is an object** — which is why we generally use the term *value*.

Each value has a **data type**, which you can check using the `type()` function. The following program:

```python
from miniworlds import *
import random
world = World(100, 100)

print(type("Hello World"))
print(type(Line((10, 10), (100, 100))))
print(type(17))

world.run()
```

...produces this output on the console:

```
<class 'str'>
<class 'actors.shapes.Line'>
<class 'int'>
```

---

## Variables

To access stored objects later, you need to save where they are. Technically, the *memory address* of an object is stored,
but in Python, we use **names** to refer to objects.

```python
line = Line((10, 10), (100, 100))
```

This stores the line in the variable named `line`.
You can now use `line` to access and modify the object, for example:

```python
line.fill_color = (255, 0, 0)
```

You can also do calculations with variables, such as:

```python
a = 3
b = 4
print(a + b)
```

---

## Assignments

Assignments use the `=` symbol:

```python
c = a + b
```

This means:

* First, the **expression on the right** is evaluated.
* Then, the **result** is stored in the variable on the left.

After this code:

```python
a = 3
b = 4
c = a + b
```

* `a` has the value `3`
* `b` has the value `4`
* `c` has the value `7`

You can also update object attributes, like moving a circle left or right using the keyboard:

```python
from miniworlds import *
world = World(100, 100)

circle = Circle((50, 50), 20)

@world.register
def on_key_pressed_a(self):
    circle.x = circle.x - 1

@world.register
def on_key_pressed_d(self):
    circle.x = circle.x + 1

world.run()
```

The line `circle.x = circle.x + 1` means:

* Compute `circle.x + 1`
* Store the result back into `circle.x`

> **Note**:
> `=` does not mean mathematical equality.
> Instead, the right-hand expression is evaluated and the result is **assigned** to the left-hand side.
>
> Some programming languages use a different symbol to avoid confusion for beginners.

---

## Usage

You can use variables wherever you would use a number or string — as long as the **data type** is correct:

```python
a = 3
b = 4
line = Line((a, b), (5, 6))
```

This works because `(a, b)` is a tuple — exactly what `Line` expects.

But this will raise an error:

```python
a = 3
b = 4
line = Line(a, (5, 6))
```

`Line` expects a tuple as the first argument, but `a` is an integer.
The error will be:

```
miniworlds.exceptions.miniworlds_exception.ActorArgumentShouldBeTuple: First argument to create a Actor [position] should be a Tuple.
```

Reading error messages often helps identify mistakes.

---

## Scope

In larger programs — especially when working in teams — variable names and their **scope** are important to prevent conflicts.

A variable has different **scopes** depending on where it's defined:

* A variable **inside** a function has **local scope** — it's only visible within that function.
* A variable **outside** any function is **global** — visible throughout the program.

> ⚠️ **Important**: If you want to *modify* a global variable inside a function, you must use the `global` keyword.

### This works:

```python
from miniworlds import *
world = World(100, 100)

a = 3

@world.register
def on_key_pressed_a(self):
    print(a)

world.run()
```

Output: `3`

---

### But this does NOT work:

```python
from miniworlds import *
world = World(100, 100)

a = 3

@world.register
def on_key_pressed_a(self):
    a = a + 1
    print(a)

world.run()
```

This causes an error because `a` is treated as a local variable, but hasn’t been initialized yet.

---

### This works again using `global`:

```python
from miniworlds import *
world = World(100, 100)

a = 3

@world.register
def on_key_pressed_a(self):
    global a
    a = a + 1
    print(a)

world.run()
```
