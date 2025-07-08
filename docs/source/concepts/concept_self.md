# The Keyword `self`

In the code above, you saw that the `act` method takes `self` as a parameter.

All methods that belong to an object **always** receive `self` as their first parameter.

Inside the method, you can then use `self` to access the **attributes and methods** of the object itself.

### Example:

This code:

```python
@player.register
def act(self):
    self.direction = "right"
```

is equivalent to:

```python
@player.register
def act(self):
    player.direction = "right"
```

Here, `self` refers to the `player` object where the method was registered.
