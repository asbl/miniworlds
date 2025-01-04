from typing import Union

import miniworlds.actors.parent_actor as parent_actor
import miniworlds.actors.widgets.widget_base as widget_base
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.world as world_mod

class ContainerWidget(widget_base.BaseWidget):
    """Widget containing multiple widgets.

    The widgets inside of this widget are displayed from left to right.
    """

    def __init__(self, children):
        self._inner_padding = 5
        self._padding_top = 2
        self._padding_left = 0
        self._padding_right = 0
        self._padding_bottom = 0
        super().__init__((0,0))
        self.origin = "topleft"
        self.set_background_color((255, 255, 255, 100))
        self.children = children

    @property
    def inner_padding(self):
        if hasattr(self, "_inner_padding"):
            return self._inner_padding
        else:
            return 0

    def resize(self):
        if not self._resize:
            return
        super().resize()
        actual_x = (
            self.x + self.padding_left
        )  # saves current c position, will be changed in loop
        for child in self.children:
            # set child positions
            child.width = (
                self.width - self.inner_padding - self.padding_right - self.padding_left
            ) / len(self.children)
            child.height = self.height - self.padding_top - self.padding_bottom
            child.x = actual_x
            child.y = self.y + self.padding_top
            child.update_positions()
            actual_x += child.width + self.inner_padding

    def get_widget(self, pos):
        local_pos = self.get_local_pos(pos)
        actual_x = 0
        for child in self.children:
            if actual_x <= local_pos[0] <= actual_x + child.width:
                return child
            actual_x += child._width + self.inner_padding

    def add_child(self, actor: "actor_mod.Actor"):
        super().add_child(actor)