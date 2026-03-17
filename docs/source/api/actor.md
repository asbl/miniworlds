# Actor

Actors can also communicate with one another through messages when
that is easier to read than passing object references around.

Combine `send_message(...)` with `@register_message("...")` for simple
event flows between beginner-friendly actor classes.

```{eval-rst}
.. autoclass:: miniworlds.actors.actor.Actor
   :members:
   :no-private-members:

   .. autoclasstoc::
```
