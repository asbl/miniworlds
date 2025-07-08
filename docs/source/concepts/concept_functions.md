# Concept: Functions and Code Blocks

## Functions and Decorators

In the last chapter, we saw code like this:

```python
@world.register
def on_setup(self):
    world.fps = 1
    world.speed = 3
```

* In the second line, a **function** is defined that performs specific instructions (we’ll discuss that more below).

* In the first line, a **decorator** is used. This decorator **attaches** the function to the `world` object.
  Whenever the system wants to call `world.on_setup`, the function you defined is executed instead.
  This way, you can define functions that respond to various **events**, like key presses, actor collisions, etc.

---

## Indentation and Code Blocks

Lines 3 and 4 in the example above are **indented**. This means they **belong to the function** and are executed when it is called.

In Python, **indentation** is used to define **code blocks** — that is, when a conditional or function begins and ends.
All lines with the **same level of indentation** are considered part of the same block.

---

## Coding Standards — How Much Should You Indent?

The Python language doesn’t enforce **how many spaces** to use for indentation — whether 3, 4, or 5 spaces — but all lines in a block must be **indented equally**.

However, Python developers have agreed on certain **coding standards** so that code looks consistent across projects.

* The commonly accepted rule is to indent code using **4 spaces**.
* While you can use your own style, it is **strongly recommended** to follow this standard, especially when working in teams.

Python’s functions and conventions are documented in official proposals called **PEPs** (Python Enhancement Proposals).
Style recommendations can be found in [PEP 8](https://www.python.org/dev/peps/pep-0008/).

Besides indentation, it covers many other topics — for example:

```python
a = a + 3  # Recommended
```

instead of:

```python
a=a+3  # Less readable
```

Although Python doesn’t **enforce** these rules, following them helps make your code easier for others to read.

---

## Helpful Tools

Most modern code editors support:

* **Auto-formatting** (e.g., automatic indentation)
* **Linting** (checking your code for style issues)

These tools help you write **clean and readable code** more easily.
