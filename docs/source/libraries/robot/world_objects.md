# World Objects

Three actor types can be placed on a `RobotWorld` grid.
They are created automatically by `load` / `load_world` / `task` when the
`WorldConfig` lists them in `objects`, but you can also place them manually via
`world.add_object(Leaf, (col, row))`.

| Class | Color | Blocks robot | Collectable |
|---|---|---|---|
| `Leaf` | green | No | Yes, use `robot.remove_leaf()` |
| `Mushroom` | red | Yes | No |
| `Tree` | dark green | Yes | No |

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_robot.world.Leaf
   :members:
   :no-private-members:

.. autoclass:: miniworlds_robot.world.Mushroom
   :members:
   :no-private-members:

.. autoclass:: miniworlds_robot.world.Tree
   :members:
   :no-private-members:
```
