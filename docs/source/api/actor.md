# Actor

Actors can communicate through messages when this is easier to read than
passing object references around.

Combine `send_message(...)` with `@register_message("...")` for simple,
beginner-friendly event flows between actor classes.

## API Reference

```{eval-rst}
.. autoclass:: miniworlds.actors.actor.Actor
   :members:
   :no-private-members:

   .. autoclasstoc::
```
