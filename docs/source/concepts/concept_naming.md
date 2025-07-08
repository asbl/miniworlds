# Concept: Naming and Variables

## Naming

In the first chapter, you saw instructions like this:

```python
world = miniworlds.World()
```

Here, the `=` sign does **not** have the same meaning as in mathematics.

* First, the right side of the statement is executed. In this case, a `TiledWorld()` object is created.
* Second, the created object is stored under the name `world`.
  You can later refer to this object using its name.

Names in programming have a special purpose: they act as **storage** for objects and data.
By assigning a name to an object, you can reuse or modify it later.

Such names are called **variables**, because the data they refer to can change.

---

### Simple Example

```python
a = 3
b = 2
c = a + b
```

You store values in `a` and `b`, and later use them to compute `c`.
The result will be `5`.

Variables can also be **overwritten** — the old value is lost:

```python
a = 3
a = 2
c = a + a
print(c)
```

This prints `4`, because `a` was overwritten with the value `2`.

---

## The World Object

The `World` is an object that has various **attributes** and **methods**.

### Attributes

You can access attributes using dot notation:
`object_name.attribute_name`

Example:

```python
world.rows = 4
```

This sets the number of rows in the world to 4.

---

### Methods

Methods are actions an object can perform, for example:
`world.add_background()` adds a background to the world.

You access methods with:
`object_name.method_name()`
Sometimes, arguments are passed in parentheses.

Example:

```python
world.add_background("images/my_background.png")
```
