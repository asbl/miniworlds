from typing import Union

import miniworlds.actors.texts.text as mod_text
import miniworlds.actors.widgets.widget_base as widget_base
import miniworlds.actors.widgets.widget_parts as widget_parts
import miniworlds.worlds.gui.gui as gui_mod
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.world as world_mod



class SingleWidget(widget_base.BaseWidget):
    def __init__(self, position = (0,0), *args, **kwargs):
        super().__init__(position, *args, **kwargs)
        # text
        text = kwargs.pop("text") if "text" in kwargs else ""
        self._widget_text = widget_parts.WidgetText((0, 0), text=text)
        self.add_child(self._widget_text)
        self._font_size = 15
        self._widget_text.font_size = self._font_size
        self._widget_text_align = "left"
        # image
        self._img_widget = None
        self._img_width = 22
        self._img_source = None
        self.img_padding_right = 5

    def resize(self):
        if not self._resize:
            return
        """resizes widget based on text_width and height"""
        if not isinstance(self.world, gui_mod.GUI):
            return
        self._widget_text.font_size = self._font_size
        if self._img_widget:
            self._img_widget.layer = self.layer + 1
            self._img_widget.size = ( self._img_width, self._font_size)
        if not self.fixed_width:
            # no image: Set width/height by text and img width
            if self._widget_text_align == "left" and not self._img_widget:
                self.width = self._widget_text.width
            elif (
                self._widget_text_align == "left" and self._img_widget or self._widget_text_align == "image"
            ):
                self.width = (
                    self._widget_text.width
                    + self._padding_left
                    + self._padding_right
                    + self._img_width
                    + self.img_padding_right
                )
        self.height = self._widget_text.font_size + self._padding_top + self._padding_bottom
        self.update_positions()
        self.cut_widget_text()
        return True

    def cut_widget_text(self):
        if self.fixed_width and not self._overflow:
            if not self._img_widget:
                self._widget_text.max_width = (
                    self.width - self.padding_left - self.padding_right
                )
            if self._img_widget:
                self._widget_text.max_width = (
                    self.width
                    - self.padding_left
                    - self.padding_right
                    - self._img_width
                    - self.img_padding_right
                )

    def update_positions(self):
        super().update_positions()
        """updates text and img position"""
        if self._widget_text_align == "left" and not self._img_widget:
            self._widget_text.topleft = (
                self.topleft[0] + self.padding_left,
                self.topleft[1] + self.padding_top,
            )
        if self._widget_text_align == "left" and self._img_widget or self._widget_text_align == "image":
            self._img_widget.topleft = (
                self.topleft[0] + self.padding_left,
                self.topleft[1] + self.padding_top,
            )
            self._widget_text.topleft = (
                self.topleft[0]
                + self._img_width
                + self.img_padding_right
                + self.padding_left,
                self.topleft[1] + self.padding_top,
            )
        self._widget_text.costume._update_draw_shape()

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
        
    def set_row_height(self, value=20):
        super().set_row_height(value)
        self._widget_text.font_by_size(
            self.width, value - self.padding_top - self.padding_bottom
        )
        self.resize()

    def set_border(self, color: tuple = (0, 0, 0, 255), width: int = 1):
        """sets border of widget

        Args:
            color (_type_): _description_
            width (_type_): _description_
        """
        self.border_color = color
        self.border = width

    def set_position(self, value: tuple):
        super().set_position(value)
        self.resize()
        self.costume._update_draw_shape()

    @property
    def text_align(self):
        """Defines how text is aligned.

        If widget has an image, text is aligned left, else it can be set to "left", "center" or "right".
        """
        if not self._img_source:
            return "left"
        else:
            return self._widget_text_align

    @text_align.setter
    def text_align(self, value):
        self._widget_text_align = value
        self.dirty = 1
        self.resize()
        
        
    def set_world(self, new_world):
        self._resize = False
        super().set_world(new_world)
        self._resize = True
        for child in self.children:
            if child not in self.world.actors: #@todo: needed?
                self.world.actors.add(child)
        self.resize()
        return self
        

    @property
    def text(self) -> mod_text.Text:
        """The text which is displayed on the widget."""
        return self._widget_text

    @text.setter
    def text(self, value: str):
        self.set_text(value)

    def get_widget_text(self):
        return self._widget_text.text

    def set_image(self, _img_source: Union[str, tuple]):
        """sets image of widget

        Args:
            _img_source (str): path to image or tuple with color
        """
        if self._img_widget and self._img_widget in self.children:
            self.remove_child(self._img_widget)
        self._img_widget = widget_parts.WidgetImage()
        self._img_widget.world = self.world
        self._img_widget.add_costume(_img_source)
        self._img_widget.width = self._img_width
        self._img_widget.height = self._widget_text.height
        self.add_child(self._img_widget)
        self.resize()

    def set_text(self, text: Union[str, int, float]):
        """Sets text of widget.

        int and float values are converted to string.
        """
        if isinstance(text, int) or isinstance(text, float):
            text = str(text)
        if not isinstance(text, str):
            raise TypeError("text must be of type str, got", type(text), text)
        self._widget_text.set_text(text)
        self.max_width = self._widget_text.width
        self.max_height = self._widget_text.height
        self.resize()

    def get_text(self):
        return self._widget_text.text