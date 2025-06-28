from typing import Union
import miniworlds.worlds.gui.gui as gui_mod
import miniworlds.actors.actor as actor_mod
import miniworlds.actors.widgets.widget_costume as widget_costume
import miniworlds.actors.parent_actor as parent_actor


class BaseWidget(parent_actor.ParentActor):
    def __init__(self, position = (0, 0), *args, **kwargs):
        super().__init__(position, *args, **kwargs)
        # Paddings and margins
        self._padding_top = 5
        self._padding_left = 5
        self._padding_right = 5
        self._padding_bottom = 5
        self.margin_top = 5
        self.margin_left = 5
        self.margin_right = 5
        self.margin_bottom = 5
        self._row_height = 20
        # additional layout
        self.fixed_width: bool = True
        self._overflow = False
        # additional
        self.timed = False  # e.g. for counters
        self.origin = kwargs.get("origin") if kwargs.get("origin") else "topleft"
        self._resize = True # Should widget be resized?

    def new_costume(self):
        return widget_costume.WidgetCostume(self)

    def resize(self):
        for child in self.children:
            if child.world != self.world:
                child.world = self.world
    
    def update_positions(self):
        pass

    def get_local_pos(self, position):
        x = position[0] - self.topleft[0]
        y = position[1] - self.topleft[1]
        return x, y

    @property
    def padding_left(self):
        return self._padding_left

    @padding_left.setter
    def padding_left(self, value):
        self._padding_left = value
        self.resize()

    @property
    def padding_right(self):
        return self._padding_right

    @padding_right.setter
    def padding_right(self, value):
        self._padding_right = value
        self.resize()

    @property
    def padding_top(self):
        return self._padding_top

    @padding_top.setter
    def padding_top(self, value):
        self._padding_top = value
        self.resize()

    @property
    def padding_bottom(self):
        return self._padding_bottom

    @padding_bottom.setter
    def padding_bottom(self, value):
        self._padding_bottom = value
        self.resize()

    @property
    def position(self):
        return self.position_manager.position

    @position.setter
    def position(self, value):
        self.position_manager.set_position(value)
        self.update_positions()

    @property
    def topleft(self):
        return self.position_manager.position

    @topleft.setter
    def topleft(self, value):
        self.position_manager.set_topleft(value)
        self.update_positions()

    @property
    def center(self):
        return self.position_manager.get_center()

    @center.setter
    def center(self, value):
        self.position_manager.set_center(value)
        self.update_positions()

    @property
    def row_height(self):
        return self._row_height

    @row_height.setter
    def row_height(self, value):
        self.set_row_height(value)

    def set_row_height(self, value):
        self._row_height = value

    def set_border(self, color: tuple = (0, 0, 0, 255), width: int = 1):
        """sets border of widget

        Args:
            color (_type_): _description_
            width (_type_): _description_
        """
        self.border_color = color
        self.border = width

    def set_world(self, new_world):
        super().set_world(new_world)
        self.origin = "topleft"
        self.resize()
        

    def set_position(self, value: tuple):
        super().set_position(value)
        self.resize()
        self.costume._update_draw_shape()

