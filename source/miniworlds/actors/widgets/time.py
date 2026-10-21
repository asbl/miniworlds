import miniworlds.actors.widgets.label as label


class TimeLabel(label.Label):
    """Label that displays the current frame number of a world.

    Args:
        world: The world whose frame counter is displayed. If no world is
            given, the world the widget is added to is used.
        text: Prefix displayed before the frame number.
        img_path: Optional path to an image shown alongside the text.

    Examples:
        ::

            toolbar = Toolbar()
            toolbar.add(TimeLabel(world, text="Frame"))
            world.camera.add_right(toolbar)
    """

    def __init__(self, world=None, text: str = "Time", img_path: str | None = None):
        super().__init__(text, img_path)
        self.timed = True
        self._base_text = text
        self._observed_world = world
        self.value = 0
        self.set_text(f"{text} : {self.value}")

    def update(self):
        """Updates the displayed value; called once per frame by the toolbar."""
        world = self._observed_world or self.world
        self.value = world.frame
        self.set_text(f"{self._base_text} : {self.value}")
