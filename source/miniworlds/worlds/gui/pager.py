import miniworlds.worlds.gui.toolbar as toolbar
import miniworlds.actors.widgets.pagination as pagination

class PagerHorizontal(toolbar.Toolbar):

    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        self.fixed_camera = True
        
    def on_setup(self):
        self.pager_buttons = pagination.PagerButtonsHorizontal(self.gui)
        self.pager_buttons.world = self
        
    def act(self):
        if self.gui.can_scroll_down(10):
            self.pager_buttons.down.visible = True
        else:
            self.pager_buttons.down.visible = False
        if self.gui.can_scroll_up(10):
            self.pager_buttons.up.visible = True
        else:
            self.pager_buttons.up.visible = False