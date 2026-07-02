# QueueWorld

`QueueWorld` visualizes a FIFO queue as a row of boxes growing left-to-right.
The front box (next to be dequeued) is highlighted in red;
the back box (most recently enqueued) in purple.

## Operations

| Method | Description |
|---|---|
| `enqueue(value)` | Add a value to the back. Raises `OverflowError` when at capacity. |
| `dequeue()` | Remove and return the front value. Raises `IndexError` on empty queue. |
| `front()` | Return the front value without removing it. Raises `IndexError` on empty queue. |
| `back()` | Return the back value without removing it. Raises `IndexError` on empty queue. |
| `values()` | Return all current elements, front-to-back order. |
| `is_empty()` | Return `True` when the queue has no elements. |
| `is_full()` | Return `True` when the queue has reached its capacity. |
| `clear()` | Remove all elements. |
| `size` | Number of elements currently in the queue (property). |

## Constructor parameters

| Parameter | Default | Description |
|---|---|---|
| `capacity` | `8` | Maximum number of elements. |
| `box_width` | `80` | Width of each element box in pixels. |
| `box_height` | `50` | Height of each element box in pixels. |
| `margin` | `10` | Margin around the queue in pixels. |
| `background` | light grey | Background fill color. |

## Example

```python
from miniworlds_data import QueueWorld

world = QueueWorld(capacity=5)
world.enqueue(10)
world.enqueue(20)
world.enqueue(30)
print(world.front())     # 10
print(world.dequeue())   # 10
world.run()
```

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_data.queue_world.QueueWorld
   :members:
   :no-private-members:
```
