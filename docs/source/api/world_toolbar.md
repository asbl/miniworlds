# World > Toolbar

Toolbars are regular worlds that are usually docked beside the main world with `world.camera.add_right(toolbar)` or `world.camera.add_bottom(toolbar)`.

They are especially useful together with buttons, because the active world can react to toolbar actions in `on_message`.

```{eval-rst}
.. autoclass:: miniworlds.worlds.gui.toolbar.Toolbar
   :members:

   .. autoclasstoc::
```