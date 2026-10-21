import time

import miniworlds.actors.widgets.label as label


class FPSLabel(label.Label):
    """Label that displays the measured frames per second.

    The label measures the time between two frames itself; no clock
    object is required. Add it to a `Toolbar` so that it is updated
    once per frame.

    Args:
        world: Optional world (ignored; kept for backward compatibility).
        text: Prefix displayed before the measured value.
        img_path: Optional path to an image shown alongside the text.

    Examples:
        ::

            toolbar = Toolbar()
            toolbar.add(FPSLabel(text="FPS"))
            world.camera.add_right(toolbar)
    """

    def __init__(self, world=None, text: str = "FPS", img_path: str | None = None):
        super().__init__(text, img_path)
        self.timed = True
        self._base_text = text
        self._last_update = None
        self.value = 0
        self.set_text(f"{text} : {self.value}")

    def update(self):
        """Updates the displayed value; called once per frame by the toolbar."""
        now = time.perf_counter()
        if self._last_update is not None:
            elapsed = now - self._last_update
            if elapsed > 0:
                self.value = round(1 / elapsed)
        self._last_update = now
        self.set_text(f"{self._base_text} : {self.value}")
