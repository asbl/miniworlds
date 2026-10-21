import miniworlds.worlds.gui.toolbar as toolbar
import miniworlds.actors.widgets.pagination as pagination


class PagerHorizontal(toolbar.Toolbar):
    """Toolbar with scroll buttons for another toolbar or console.

    The pager shows an up and a down button and toggles their
    visibility depending on whether the observed GUI can still scroll
    in that direction.

    Args:
        gui: The toolbar or console whose scroll range is controlled.
    """

    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        self.fixed_camera = True

    def on_setup(self):
        self.pager_buttons = pagination.PagerButtonsHorizontal(self.gui)
        self.pager_buttons.world = self

    def act(self):
        down_visible = self.gui.can_scroll_down(10)
        if self.pager_buttons.down.visible != down_visible:
            self.pager_buttons.down.visible = down_visible
        up_visible = self.gui.can_scroll_up(10)
        if self.pager_buttons.up.visible != up_visible:
            self.pager_buttons.up.visible = up_visible
