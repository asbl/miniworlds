from collections import OrderedDict
from typing import Union
import miniworlds.worlds.gui.gui as gui
import miniworlds.actors.widgets.widget_base as widget_base
import miniworlds.actors.widgets.widget_parts as widget_parts
import miniworlds.worlds.gui.toolbar_mainloop_manager as toolbar_mainloop_manager


class Toolbar(gui.GUI):
    """A panel that holds buttons, labels, and other widgets.

    Toolbars are usually docked beside the main world using
    `world.camera.add_right(toolbar)` or `world.camera.add_bottom(toolbar)`.
    Widgets are added with `toolbar.add(widget)` (or by simply creating them -
    they register themselves automatically when their world is set to the toolbar).

    When a button inside a toolbar is clicked it broadcasts its label text as
    a message. The main world responds via `on_message`.

    Examples:
        ::

            toolbar = Toolbar()
            toolbar.add(Button("Restart"))
            world.camera.add_right(toolbar)

            @world.register
            def on_message(self, message):
                if message == "Restart":
                    world.reset()
    """

    def __init__(self):
        """Create a toolbar.

        Examples:
            ::

                toolbar = Toolbar()
                toolbar.add(Button("Start Rocket"))
                world.camera.add_right(toolbar)
                rocket.started = False

                @world.register
                def on_message(self, message):
                    if message == "Start Rocket":
                        rocket.started = True

                @rocket.register
                def act(self):
                    if self.started:
                        self.move()
        """
        super().__init__()
        self.widgets: OrderedDict[Union[int, str], "widget_base.BaseWidget"] = OrderedDict()
        self.timed_widgets: dict[int, "widget_base.BaseWidget"] = dict()
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
        """Reflows all widgets after the toolbar size or layout has changed.

        This keeps widgets aligned when the toolbar is resized or docked in a
        different place.
        """
        if hasattr(self, "widgets"):
            self.reorder()

    @property
    def background_color(self):
        """tuple: Toolbar background color.

        Examples:
            ::

                toolbar.background_color = (255, 255, 255)
        """
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

    def _add_widget(
        self,
        widget: "widget_base.BaseWidget",
        key: Union[int, str, None] = None,
    ) -> "widget_base.BaseWidget":
        widget._resize = False
        widget.row_height = self.row_height
        if key is None:
            # Auto keys are always integers, so custom string keys
            # cannot break the max() computation.
            key = max((k for k in self.widgets if isinstance(k, int)), default=-1) + 1
        self.widgets[key] = widget
        if getattr(widget, "timed", False):
            self.timed_widgets[id(widget)] = widget
        # Reorder mus be called before camera position is updated
        self.reorder() 
        if not self.fixed_camera and widget.y + widget.height > self.camera.y + self.camera.height:
            self.camera.world_size_y = widget.y + widget.height
            self.camera.y = widget.y + widget.height - self.camera.height
        widget._resize = True
        return widget

    def _unregister_widget(self, widget: "widget_base.BaseWidget"):
        self.timed_widgets.pop(id(widget), None)

    def remove(self, item: Union[int, str, "widget_base.BaseWidget"]):
        """
        Removes a widget from the toolbar.

        The widget is also removed from the toolbar world, so it is no
        longer rendered and no longer receives events.

        .. warning::
            Be careful when calling this inside a loop over ``self.widgets``.

        Args:
            item: The widget to remove – either the widget object itself, its
                integer index, or its string key.
        """
        if type(item) in [int, str]:
            if item in self.widgets:
                removed_widget = self.widgets.pop(item)
                self._unregister_widget(removed_widget)
                removed_widget.remove()
            else:
                return False
        elif isinstance(item, widget_base.BaseWidget):
            search_key = None
            for key, value in self.widgets.items():
                if value == item:
                    search_key = key
                    break
            if search_key is None:
                raise ValueError(f"{item} not found in Toolbar-Widgets")
            else:
                removed_widget = self.widgets.pop(search_key)
                self._unregister_widget(removed_widget)
                removed_widget.remove()
        else:
            raise TypeError(f"item must be of type [int, str, Widget], found {type(item)}")


    def has_widget(self, key: Union[int, str]):
        """Checks whether the toolbar contains a widget under *key*.

        Args:
            key: The widget key (integer auto key or custom string key).

        Returns:
            bool: True if the widget exists, otherwise False.
        """
        if key in self.widgets:
            return True
        else:
            return False

    def get_widget(self, key: Union[int, str]) -> "widget_base.BaseWidget":
        """Gets widget by key

        Args:
            key: The key of the widget (integer auto key or custom string key).

        Returns:
            The widget stored under *key*.

        Raises:
            TypeError: If no widget with the given key exists.
        """
        if key in self.widgets:
            return self.widgets[key]
        else:
            raise TypeError(f"Error: Toolbar widgets does not contain key {key}")

    def remove_all_widgets(self):
        """Removes all widgets from the toolbar at once.

        The widgets are also removed from the toolbar world. Use this
        when rebuilding a menu or replacing all controls.
        """
        for widget in list(self.widgets.values()):
            self._unregister_widget(widget)
            widget.remove()
        self.widgets = OrderedDict()
        self.dirty = 1

    def reorder(self):
        """Recomputes the positions of all toolbar widgets.

        Widgets are stacked from top to bottom with the configured paddings and
        margins.
        """
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

    def send_message(self, text: str) -> None:
        """Sends a broadcast message to the world and all actors.

        The message is dispatched through the event system and can be handled
        by any registered method in the world or its actors.

        Args:
            text: The name of the message/event to send.

        Example:
            >>> toolbar.send_message("open_menu")
        """
        self.app.event_manager.to_event_queue("message", text)

    def scroll_up(self, value):
        """Scrolls the toolbar view upward by *value* pixels.

        Args:
            value: Number of pixels to scroll.
        """
        if self.can_scroll_up(value):
            self.camera.y -= value
            self.camera.y = max(0, self.camera.y)

    def scroll_down(self, value):
        """Scrolls the toolbar view downward by *value* pixels.

        Args:
            value: Number of pixels to scroll.
        """
        if self.can_scroll_down(value):
            self.camera.y += value

    def can_scroll_down(self, value):
        """Returns True if the toolbar can scroll downward by *value* pixels.

        Args:
            value: Number of pixels to scroll by.

        Returns:
            bool: True if scrolling is possible, False otherwise.
        """
        if self._widgets_total_height() < self.camera.y + self.camera.height:
            return False
        if self.camera.y + value > self.world_size_y - self.camera.height:
            return False
        else:
            return True

    def can_scroll_up(self, value):
        """Returns True if the toolbar can scroll upward by *value* pixels.

        Args:
            value: Number of pixels to scroll by.

        Returns:
            bool: True if upward scrolling is possible, otherwise False.
        """
        if self.camera.y == 0:
            return False
        else:
            return True

    def on_new_actor(self, actor):
        """Handles actors that are added to this toolbar world.

        Widget actors are registered in the internal widget list and then
        resized/reordered so the layout stays consistent.

        Args:
            actor: The actor that has been added.
        """
        if isinstance(actor, widget_parts.WidgetPart):
            return
        if isinstance(actor, widget_base.BaseWidget):
            self._add_widget(actor)
            actor.resize()
            self.reorder()

    def on_remove_actor(self, actor):
        """Handles actors that are removed from this toolbar world.

        Args:
            actor: The actor that has been removed.
        """
        pass
