from typing import TYPE_CHECKING
import miniworlds.appearances.managers.image_manager as image_manager

if TYPE_CHECKING:
    from miniworlds.appearances.appearance import Appearance  # falls vorhanden

class ImageBackgroundManager(image_manager.ImageManager):
    """
    Specialized ImageManager for background images.
    Adds forced blitting to the window surface after image changes.
    """

    def __init__(self, appearance: 'Appearance'):
        super().__init__(appearance)

    def next_image(self):
        """
        Switches to the next image and forces redraw to the window surface
        if the appearance is animated.
        """
        super().next_image()
        if self.appearance.is_animated:
            self.appearance._blit_to_window_surface()

    def set_image_index(self, value: int) -> bool:
        """
        Changes the currently displayed image index and forces a redraw.
        """
        changed = super().set_image_index(value)
        self.appearance._blit_to_window_surface()
        return changed

    def _add_scaling(self, source):
        """
        Override: sets the is_scaled flag when the first background image is added.
        """
        self.appearance.is_scaled = True
