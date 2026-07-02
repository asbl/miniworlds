# StackWorld

`StackWorld` visualizes a LIFO stack as a column of boxes growing upward.
The topmost box is highlighted in red to indicate the top-of-stack.

## Operations

| Method | Description |
|---|---|
| `push(value)` | Push a value onto the top. Raises `OverflowError` when at capacity. |
| `pop()` | Remove and return the top value. Raises `IndexError` on empty stack. |
| `peek()` | Return the top value without removing it. Raises `IndexError` on empty stack. |
| `values()` | Return all current elements, bottom-to-top order. |
| `is_empty()` | Return `True` when the stack has no elements. |
| `is_full()` | Return `True` when the stack has reached its capacity. |
| `clear()` | Remove all elements. |
| `size` | Number of elements currently on the stack (property). |

## Constructor parameters

| Parameter | Default | Description |
|---|---|---|
| `capacity` | `8` | Maximum number of elements. |
| `box_width` | `120` | Width of each element box in pixels. |
| `box_height` | `40` | Height of each element box in pixels. |
| `margin` | `10` | Margin around the stack in pixels. |
| `background` | light grey | Background fill color. |

## Example

```python
from miniworlds_data import StackWorld

world = StackWorld(capacity=5)
world.push("A")
world.push("B")
world.push("C")
print(world.peek())    # "C"
print(world.pop())     # "C"
world.run()
```

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_data.stack_world.StackWorld
   :members:
   :no-private-members:
```
