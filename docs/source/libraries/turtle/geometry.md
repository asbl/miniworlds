# Vec2D

`Vec2D` is a 2-D vector helper used internally by the turtle module.
It is returned by `turtle.position()` and can be used for coordinate arithmetic.

```python
from miniworlds_turtle import Turtle

t = Turtle()
t.forward(100)
pos = t.position()   # Vec2D(100, 0)
print(pos[0], pos[1])
```

`Vec2D` supports:

- Indexing: `v[0]`, `v[1]`
- Arithmetic: `+`, `-`, `*` (scalar), `/`  (scalar)
- `abs(v)`: Euclidean length
- `v.rotate(angle)`: return a rotated copy

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_turtle.geometry.Vec2D
   :members:
   :no-private-members:
```
