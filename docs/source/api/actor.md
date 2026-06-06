# Actor

Actors can communicate through messages when this is easier to read than
passing object references around.

Combine `send_message(...)` with `@register_message("...")` for simple,
beginner-friendly event flows between actor classes.

For beginner classes, you can enable `world.learning_mode = True`.
In this mode, common input mistakes are handled more gently where possible
(for example list positions are accepted in many Actor position methods).

Useful beginner aliases on Actor include:

- `go_to(...)` for `move_to(...)`
- `move_forward(...)` for `move(...)`
- `face(...)` for `set_direction(...)`
- `turn(...)` for `turn_right(...)`
- `touching(...)` and `touching_all(...)` for detect helpers

## API Reference

```{eval-rst}
.. autoclass:: miniworlds.actors.actor.Actor
   :members:
   :no-private-members:
```
