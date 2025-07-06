from collections import OrderedDict
from typing import Union
import pygame
import miniworlds.base.app as app_mod
import miniworlds.worlds.gui.gui as gui
import miniworlds.actors.widgets.widget_base as widget_base
import miniworlds.actors.widgets.widget_parts as widget_parts
import miniworlds.worlds.gui.toolbar_mainloop_manager as toolbar_mainloop_manager


class Toolbar(gui.GUI):
    """A Toolbar contains widgets (Buttons, Labels, ...)"""

    def __init__(self):
        """
        Base class for toolbars.

        Example:

            Add a Toolbar which interacts with Actors on world via messages:

            .. code-block:: python

                from miniworlds import *

                world = World()

                world.add_background("images/galaxy.jpg")

                toolbar = Toolbar()
                button = Button("Start Rocket")
                toolbar.add(button)
                world.add_container.add_right(toolbar)

                @world.register
                def on_message(self, message):
                    if message == "Start Rocket":
                        rocket.started = True

                rocket = Actor(100, 200)
                rocket.add_costume("images/ship.png")
                rocket.started = False
                rocket.turn_left(90)
                rocket.direction = "up"

                @rocket.register
                def act(self):
                    if self.started:
                            self.move()

                @rocket.register
                def on_sensing_not_on_the_world(self):
                    self.remove()

                world.run()
        """
        super().__init__()
        self.widgets: OrderedDict["widget_base.BaseWidget"] = OrderedDict()
        self.timed_widgets = dict()
        self.position = "right"
        self._padding_top = 10
        self._padding_bottom = 0
        self._padding_left = 10
        self._padding_right = 10
        self.row_height = 26
        self._background_color = (255, 255, 255, 255)
        self.max_widgets = 0
        self.max_row_height = 0
        self.fixed_camera = False

    @staticmethod
    def _get_mainloopmanager_class():
        return toolbar_mainloop_manager.ToolbarMainloopManager

    def on_change(self):
        if hasattr(self, "widgets"):
            for widget in self.widgets.values():
                widget.width = self.width
        self.reorder()

    @property
    def background_color(self):
        """Background color as Tuple, e.g. (255,255,255) for white"""
        return self.background

    @background_color.setter
    def background_color(self, value):
        self.set_background(value)

    @property
    def padding_left(self):
        """Defines left margin"""
        return self._padding_left

    @padding_left.setter
    def padding_left(self, value):
        self._padding_left = value
        self.dirty = 1

    @property
    def padding_right(self):
        """Defines right margin"""
        return self._padding_right

    @padding_right.setter
    def padding_right(self, value):
        self._padding_right = value
        self.dirty = 1

    @property
    def padding_top(self):
        """Defines top margin"""
        return self._padding_top

    @padding_top.setter
    def padding_top(self, value):
        self._padding_top = value
        self.dirty = 1

    @property
    def padding_bottom(self):
        """Defines bottom margin"""
        return self._padding_bottom

    @padding_bottom.setter
    def padding_bottom(self, value):
        self._padding_bottom = value
        self.dirty = 1

    def _add_widget(self, widget: "widget_base.BaseWidget", key: int = 0, ) -> "widget_base.BaseWidget":
        widget._resize = False
        widget.row_height = self.row_height
        # If param key is not set, set key to max key +1
        if self.widgets.keys():
            key = max(self.widgets.keys())+1
        else:
            key = 0
        self.widgets[key] = widget
        if hasattr(widget, "timed") and widget.timed:
            self.timed_widgets[widget.name] = widget
        # Reorder mus be called before camera position is updated
        self.reorder() 
        if not self.fixed_camera and widget.y + widget.height > self.camera.y + self.camera.height:
            self.camera.world_size_y = widget.y + widget.height
            self.camera.y = widget.y + widget.height - self.camera.height
        widget._resize = True
        return widget

    def remove(self, item: Union[int, str, "widget_base.BaseWidget"]):
        """
        Removes a widget from the toolbar. Warning: Be careful when calling this method in a loop.

        Args:
            key: The key of widget which should be removed
        """
        if type(item) in [int, str]:
            if item in self.widgets:
                self.widgets.pop(item)
            else:
                return False
        elif isinstance(item, widget_base.BaseWidget):
            search_key = None
            for key, value in self.widgets.items():
                if value == item:
                    search_key = key
            if not search_key:
                raise ValueError(f"{item} not found in Toolbar-Widgets")
            else:
                self.widgets.pop(key)
                value.remove()
        else:
            raise TypeError(f"item must be of type [int, str, Widget], found {type(item)}")


    def has_widget(self, key: str):
        """Checks if self.widgets has key

        Args:
            key: The key of widget
        """
        if key in self.widgets:
            return True
        else:
            return False

    def get_widget(self, key: str) -> "widget_base.BaseWidget":
        """Gets widget by key

        Returns:
            _type_: _description_
        """
        if key in self.widgets:
            return self.widgets[key]
        else:
            raise TypeError(f"Error: Toolbar widgets does not contain key {key}")

    def remove_all_widgets(self):
        self.widgets = dict()
        self.dirty = 1

    def reorder(self):
        if hasattr(self, "widgets") and self.widgets:
            actual_height = self.padding_top
            for widget in self.widgets.values():
                    actual_height += widget.margin_top
                    self._set_widget_width(widget)
                    widget.topleft = (self.padding_left + widget.margin_left, actual_height)
                    if self.max_row_height != 0:
                        widget.height = self.max_row_height
                    actual_height += widget.height + widget.margin_bottom


    def _widgets_total_height(self):
        height = self.padding_top
        for name, widget in self.widgets.items():
            height += widget.margin_top
            height += widget.height + widget.margin_bottom
        return height

    def _set_widget_width(self, widget):
        new_width = self.camera.width - self.padding_left - self.padding_right - widget.margin_left - widget.margin_right
        if new_width < 0:
            new_width = 0
        widget.width = new_width

    def update_width_and_height(self):
        super().screen_width

    def send_message(self, text):
        app_mod.App.running_app.event_manager.to_event_queue("message", text)

    def scroll_up(self, value):
        if self.can_scroll_up(value):
            self.camera.y -= value
            self.camera.y = max(0, self.camera.y)
            for key, widget in self.widgets.items():
                widget.resize()

    def scroll_down(self, value):
        if self.can_scroll_down(value):
            self.camera.y += value
            for key, widget in self.widgets.items():
                widget.resize()

    def can_scroll_down(self, value):
        """

        Args:
            value (_type_): _description_

        Returns:
            _type_: _description_
        """
        if self._widgets_total_height() < self.camera.y + self.camera.height:
            return False
        if self.camera.y + value > self.world_size_y - self.camera.height:
            return False
        else:
            return True

    def can_scroll_up(self, value):
        if self.camera.y == 0:
            return False
        else:
            return True

    def on_new_actor(self, actor):
        if isinstance(actor, widget_parts.WidgetPart):
            return
        if isinstance(actor, widget_base.BaseWidget):
            self._add_widget(actor)
            actor.resize()
            self.reorder()
        
    def on_remove_actor(self, actor):
        pass