# World

The base class for all of your worlds.

Use `world.send_message("name")` for simple broadcasts between the
world, actors, and docked GUI worlds.

For beginner classes, set `world.learning_mode = True`.
This enables soft conversions for common mistakes in selected public APIs
(for example bool-like strings such as `"yes"`/`"no"` in some flags, and
list positions where tuple positions are expected).

Useful beginner aliases on World include:

- `contains(...)` for `contains_position(...)`
- `broadcast(...)` for `send_message(...)`
- `actors_at(...)` for `detect_actors(...)`
- `set_bg(...)`, `add_bg(...)`, `next_bg()` for background helpers

## API Reference

```{eval-rst}
.. autoclass:: miniworlds.worlds.world.World
   :members:

   .. autoclasstoc::
```
