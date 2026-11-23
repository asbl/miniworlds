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
        self.timed_widgets: list["widget_base.BaseWidget"] = []
        self._padding_top = 10
        self._padding_bottom = 0
        self._padding_left = 10
        self._padding_right = 10
        self.row_height = 26
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
        background = self.background
        return background.fill_color if background is not None else None

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
        self._reflow()

    @property
    def padding_right(self):
        """Defines right margin"""
        return self._padding_right

    @padding_right.setter
    def padding_right(self, value):
        self._padding_right = value
        self._reflow()

    @property
    def padding_top(self):
        """Defines top margin"""
        return self._padding_top

    @padding_top.setter
    def padding_top(self, value):
        self._padding_top = value
        self._reflow()

    @property
    def padding_bottom(self):
        """Defines bottom margin"""
        return self._padding_bottom

    @padding_bottom.setter
    def padding_bottom(self, value):
        self._padding_bottom = value
        self._reflow()

    def _reflow(self):
        self.dirty = 1
        self.reorder()

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
        elif key in self.widgets:
            # Replace the widget under an existing key: remove the old
            # widget completely so it does not stay in the world as an
            # unreachable, still rendered actor.
            self._remove_by_key(key)
        self.widgets[key] = widget
        if getattr(widget, "timed", False) and widget not in self.timed_widgets:
            self.timed_widgets.append(widget)
        # Reorder must be called before camera position is updated
        self.reorder() 
        if not self.fixed_camera and widget.y + widget.height > self.camera.y + self.camera.height:
            self.camera.world_size_y = widget.y + widget.height
            self.camera.y = widget.y + widget.height - self.camera.height
        widget._resize = True
        return widget

    def _unregister_widget(self, widget: "widget_base.BaseWidget"):
        if widget in self.timed_widgets:
            self.timed_widgets.remove(widget)

    def _find_widget_key(self, item: Union[int, str, "widget_base.BaseWidget"]):
        """Returns the key under which *item* is stored, or None."""
        if isinstance(item, widget_base.BaseWidget):
            for key, value in self.widgets.items():
                if value is item:
                    return key
            return None
        if item in self.widgets:
            return item
        return None

    def _remove_by_key(self, key: Union[int, str]):
        """Removes the widget stored under *key* from widgets and world."""
        widget = self.widgets.pop(key)
        self._unregister_widget(widget)
        widget.remove()
        self.reorder()
        self._clamp_camera_to_content()

    def remove(self, item: Union[int, str, "widget_base.BaseWidget"]):
        """
        Removes a widget from the toolbar.

        The widget is also removed from the toolbar world, so it is no
        longer rendered and no longer receives events. The camera is
        clamped to the remaining content, so the view does not stay
        scrolled past the removed widget.

        Args:
            item: The widget to remove – either the widget object itself, its
                integer index, or its string key.

        Returns:
            bool: True if the widget was removed, False if no matching
            widget or key was found.

        .. warning::
            Be careful when calling this inside a loop over ``self.widgets``.
        """
        if isinstance(item, widget_base.BaseWidget) or type(item) in [int, str]:
            key = self._find_widget_key(item)
            if key is None:
                return False
            self._remove_by_key(key)
            return True
        raise TypeError(f"item must be of type [int, str, Widget], found {type(item)}")

    def has_widget(self, key: Union[int, str]):
        """Checks whether the toolbar contains a widget under *key*.

        Args:
            key: The widget key (integer auto key or custom string key).

        Returns:
            bool: True if the widget exists, otherwise False.
        """
        return key in self.widgets

    def get_widget(self, key: Union[int, str]) -> "widget_base.BaseWidget":
        """Gets widget by key

        Args:
            key: The key of the widget (integer auto key or custom string key).

        Returns:
            The widget stored under *key*.

        Raises:
            KeyError: If no widget with the given key exists.
        """
        return self.widgets[key]

    def remove_all_widgets(self):
        """Removes all widgets from the toolbar at once.

        The widgets are also removed from the toolbar world. Use this
        when rebuilding a menu or replacing all controls. The camera is
        reset to the top of the (now empty) toolbar.
        """
        for widget in list(self.widgets.values()):
            self._unregister_widget(widget)
            widget.remove()
        self.widgets.clear()
        self._clamp_camera_to_content()
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
        return height + self.padding_bottom

    def _clamp_camera_to_content(self):
        """Clamps the camera to the remaining widget content.

        After widgets are removed, the world size and the camera position
        are reduced to the remaining content, so the view does not stay
        scrolled past removed widgets. Toolbars with ``fixed_camera``
        are left untouched.
        """
        if self.fixed_camera:
            return
        total_height = self._widgets_total_height()
        self.camera.world_size_y = max(self.camera.height, total_height)
        max_camera_y = max(0, total_height - self.camera.height)
        if self.camera.y > max_camera_y:
            self.camera.y = max_camera_y

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

    def can_scroll_up(self, value=0):
        """Returns True if the toolbar can scroll upward by *value* pixels.

        Scrolling up always clamps at the top, so only the current camera
        position matters, not *value*.

        Args:
            value: Number of pixels to scroll by (kept for symmetry with
                `can_scroll_down`).

        Returns:
            bool: True if upward scrolling is possible, otherwise False.
        """
        return self.camera.y > 0

    def on_new_actor(self, actor):
        """Handles actors that are added to this toolbar world.

        Widget actors are registered in the internal widget list and then
        resized/reordered so the layout stays consistent.

        A widget that is already registered is not registered again: a
        world transfer can remove and re-add a widget in the same toolbar,
        and a duplicate entry would render the widget twice and inflate
        the computed toolbar height.

        Args:
            actor: The actor that has been added.
        """
        if isinstance(actor, widget_parts.WidgetPart):
            return
        if isinstance(actor, widget_base.BaseWidget):
            if any(widget is actor for widget in self.widgets.values()):
                return
            self._add_widget(actor)
            actor.resize()
            self.reorder()

    def on_remove_actor(self, actor):
        """Handles actors that are removed from this toolbar world.

        Widgets can also be removed directly via ``widget.remove()`` (not
        only through ``Toolbar.remove()``); this keeps the internal widget
        list consistent in that case.

        Args:
            actor: The actor that has been removed.
        """
        if not isinstance(actor, widget_base.BaseWidget):
            return
        if not hasattr(self, "widgets"):
            return
        key = self._find_widget_key(actor)
        if key is None:
            return
        self.widgets.pop(key)
        self._unregister_widget(actor)
        self.reorder()
        self._clamp_camera_to_content()
