import abc
from abc import abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, List, Tuple, Union

import numpy
import pygame

import miniworlds.appearances.appearance_rendering_facade as appearance_rendering_facade
import miniworlds.appearances.managers.font_manager as font_manager
import miniworlds.appearances.managers.image_manager as image_manager
import miniworlds.appearances.managers.transformations_manager as transformations_manager
import miniworlds.tools.binding as binding
import miniworlds.tools.color as color_mod
from miniworlds.base.exceptions import MiniworldsError

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod


class MetaAppearance(abc.ABCMeta):
    def __call__(cls, *args, **kwargs):
        instance = type.__call__(
            cls, *args, **kwargs
        )  # create a new Appearance of type...
        instance.after_init()
        return instance


class Appearance(metaclass=MetaAppearance):
    """Base class for actor costumes and world backgrounds.

    `Appearance` is the parent class of both `Costume` and `Background`. You
    normally access it through `actor.costume` or `world.background`.

    Examples:
        ::

            actor.costume.add_image("images/player.png")
            actor.costume.fill_color = (255, 0, 0)
            actor.costume.border = 2
            actor.costume.is_animated = True
            actor.costume.alpha = 128
    """

    counter = 0
    __slots__ = (
        # Core attributes
        "id",
        "initialized",
        "_flag_transformation_pipeline",
        "parent",
        "draw_shapes",
        "draw_images",
        # State flags
        "_is_flipped",
        "_is_animated",
        "_is_textured",
        "_is_centered",
        "_is_upscaled",
        "_is_scaled",
        "_is_scaled_to_width",
        "_is_scaled_to_height",
        "_is_rotatable",
        # Appearance properties
        "_orientation",
        "_coloring",
        "_transparency",
        "_border",
        "_is_filled",
        "_fill_color",
        "_border_color",
        "_alpha",
        "_dirty",
        "_image",
        "surface_loaded",
        "last_image",
        # Managers
        "font_manager",
        "image_manager",
        "transformations_manager",
        # Properties
        "_texture_size",
        "_animation_speed",
        "loop",
        "animation_length",
        "_animation_start_frame",
        "_cached_rect",
        # Note: _rendering_facade is a @cached_property, so it's stored in __dict__
        # __dict__ is inherited from object (via metaclass),
        # so subclasses can add their own attributes and @cached_property works
        "__dict__",
    )

    RELOAD_ACTUAL_IMAGE = 1
    LOAD_NEW_IMAGE = 2

    def __init__(self):
        self.id = Appearance.counter + 1
        Appearance.counter += 1
        self.initialized = False
        self._flag_transformation_pipeline = False
        self.parent = None
        self.draw_shapes = []
        self.draw_images = []
        self._is_flipped = False
        self._is_animated = False
        self._is_textured = False
        self._is_centered = True
        self._is_upscaled = False
        self._is_scaled = False
        self._is_scaled_to_width = False
        self._is_scaled_to_height = False
        self._is_rotatable = False
        self._orientation = 0
        self._coloring = None  # Color for colorize operation
        self._transparency = False
        self._border = 0
        self._is_filled = False
        self._fill_color = (255, 0, 255, 255)
        self._border_color = None
        self._alpha = 255
        self._dirty = 0
        self._image = pygame.Surface((0, 0))  # size set in image()-method
        self.surface_loaded = False
        self.last_image = None
        self.font_manager = font_manager.FontManager(self)
        self.image_manager: "image_manager.ImageManager" = image_manager.ImageManager(
            self
        )
        self.transformations_manager = transformations_manager.TransformationsManager(
            self
        )
        self.image_manager.add_default_image()
        # properties
        self._texture_size = (0, 0)
        self._animation_speed = 10  #: The animation speed for animations
        self.loop = False
        self.animation_length = 0
        self._animation_start_frame = 0
        self._cached_rect = (-1, pygame.Rect(0, 0, 1, 1))  # frame, rect

    @cached_property
    def _rendering_facade(
        self,
    ) -> appearance_rendering_facade.AppearanceRenderingFacade:
        return appearance_rendering_facade.AppearanceRenderingFacade(self)

    def _set_defaults(self, **kwargs) -> "Appearance":
        for key, value in kwargs.items():
            if value is not None:
                attr_name = f"_{key}"
                if hasattr(self, attr_name):
                    setattr(self, attr_name, value)
        self.set_dirty("all", self.LOAD_NEW_IMAGE)
        return self

    def set_image(self, source: Union[int, "Appearance", tuple]) -> bool:
        """Set the displayed image.

        Args:
            source: Image index, appearance, or color tuple.

        Returns:
            `True` if the image index exists.

        Examples:
            ::

                background.add_image("images/1.png")
                background.add_image("images/2.png")
                background.set_image(1)
        """
        if isinstance(source, int):
            return self.image_manager.set_image_index(source)
        elif isinstance(source, tuple):
            surface = image_manager.ImageManager.get_surface_from_color(source)
            self.image_manager.replace_image(
                surface, image_manager.ImageManager.COLOR, source
            )

    def after_init(self):
        """Finalize initialization after the metaclass constructor hook."""
        self.set_dirty("all", Appearance.LOAD_NEW_IMAGE)
        self.initialized = True

    @property
    def font_size(self):
        """Current font size used for text rendering."""
        return self.font_manager.font_size

    @font_size.setter
    def font_size(self, value):
        self.font_manager.set_font_size(value, update=True)

    def _set_font(self, font, font_size):
        self.font_manager.font_path = font
        self.font_manager.font_size = font_size

    @property
    def texture_size(self):
        """Texture tile size used when `is_textured` is enabled."""
        return self._texture_size

    @texture_size.setter
    def texture_size(self, value):
        self._texture_size = value
        self.set_dirty("texture", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def animation_speed(self):
        """Frames between animation steps."""
        return self._animation_speed

    @animation_speed.setter
    def animation_speed(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"animation_speed must be int or float, got {type(value).__name__}"
            )
        if value <= 0:
            raise ValueError(f"animation_speed must be > 0, got {value}")
        self._animation_speed = value

    def _set_animation_speed(self, value):
        self.animation_speed = value

    def set_mode(self, **kwargs):
        """Set multiple appearance mode flags at once.

        Supported keyword arguments include `mode`, `texture_size`, and
        `animation_speed`.
        """
        if "texture_size" in kwargs:
            self._texture_size = kwargs["texture_size"]
        if "animation_speed" in kwargs:
            self.animation_speed = kwargs["animation_speed"]
        if "mode" in kwargs:
            mode = kwargs["mode"]
            if isinstance(mode, str):
                mode = [mode]
            if "textured" in mode:
                self._set_textured(True)
            elif "scaled" in mode:
                self._set_scaled(True)
            elif "scaled_to_width" in mode:
                self._set_scaled_to_width(True)
            elif "scaled_to_height" in mode:
                self._set_scaled_to_height(True)
            elif "upscaled" in mode:
                self._set_upscaled(True)
            elif "filled" in mode:
                self.set_filled(True)
            elif "flipped" in mode:
                self._set_flipped(True)
            elif "animated" in mode:
                self.is_animated(True)
            elif "rotatable" in mode:
                self._is_rotatable(True)
            elif "centered" in mode:
                self._set_centered(True)

    def get_modes(self):
        """Return all mode flags as a dictionary."""
        modes = {
            "textured": self._is_textured,
            "scaled": self._is_scaled,
            "scaled_to_width": self._is_scaled_to_width,
            "scaled_to_height": self._is_scaled_to_height,
            "upscaled": self._is_upscaled,
            "filled": self._is_filled,
            "flipped": self._is_flipped,
            "animated": self._is_animated,
            "rotatable": self._is_rotatable,
            "centered": self._is_centered,
        }
        return modes

    @property
    def is_textured(self):
        """bool: Whether the image is tiled over the parent area.

        Examples:
            ::

                background = world.add_background("images/stone.png")
                background.is_textured = True
                background.texture_size = (15, 15)
        """
        return self._is_textured

    @is_textured.setter
    def is_textured(self, value):
        self._set_textured(value)

    def _set_textured(self, value: bool):
        """bool: If True, the image is tiled over the background.

        Args:
            value: True, if image should be displayed as textured.
        """
        self._is_textured = value
        self.set_dirty("texture", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def is_rotatable(self):
        """bool: Whether the image rotates with the parent direction."""
        return self._is_rotatable

    @is_rotatable.setter
    def is_rotatable(self, value):
        self._set_rotatable(value)

    @property
    def is_centered(self):
        """Whether drawing operations are centered on the parent position."""
        return self._is_centered

    @is_centered.setter
    def is_centered(self, value):
        self._is_centered = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def is_filled(self):
        """Whether shapes are rendered filled instead of outlined."""
        return self._is_filled

    @is_filled.setter
    def is_filled(self, value):
        self._set_filled(value)

    @property
    def is_flipped(self):
        """bool: Whether the image is mirrored horizontally.

        Examples:
            ::

                actor.costume.is_flipped = True
        """
        return self._is_flipped

    @is_flipped.setter
    def is_flipped(self, value):
        self._set_flipped(value)

    @property
    def is_upscaled(self):
        """If True, the image will be upscaled remaining aspect-ratio."""
        return self._is_upscaled

    @is_upscaled.setter
    def is_upscaled(self, value):
        self._set_upscaled(value)

    @property
    def is_scaled_to_width(self):
        """Whether the image is scaled to parent width and keeps aspect ratio."""
        return self._is_scaled_to_width

    @is_scaled_to_width.setter
    def is_scaled_to_width(self, value):
        self._set_scaled_to_width(value)

    @property
    def is_scaled_to_height(self):
        """Whether the image is scaled to parent height and keeps aspect ratio."""
        return self._is_scaled_to_height

    @is_scaled_to_height.setter
    def is_scaled_to_height(self, value):
        self._set_scaled_to_height(value)

    @property
    def fill_color(self):
        """Primary fill color for shape-based rendering."""
        return self._fill_color

    @fill_color.setter
    def fill_color(self, value):
        self._fill_color = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def is_scaled(self):
        """Scales the token to parent-size without remaining aspect-ratio."""
        return self._is_scaled

    @is_scaled.setter
    def is_scaled(self, value):
        self._set_scaled(value)

    @property
    def orientation(self):
        """float: Orientation offset applied before parent rotation.

        Examples:
            ::

                actor.costume.orientation = -90
        """
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        self._orientation = value
        self.set_dirty("orientation", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def fill_color(self):
        """Primary fill color for shape-based rendering."""
        return self._fill_color

    @fill_color.setter
    def fill_color(self, value):
        self._fill_color = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def coloring(self):
        """tuple | None: Optional color layer.

        Examples:
            ::

                actor.costume.coloring = (255, 0, 0)
        """
        return self._coloring

    @coloring.setter
    def coloring(self, value):
        self._coloring = value
        self.set_dirty("coloring", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def transparency(self):
        """bool: Whether alpha transparency is enabled.

        The actual opacity is controlled by `alpha`.
        """
        return self._transparency

    @transparency.setter
    def transparency(self, value):
        self._transparency = value
        self.set_dirty("transparency", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def alpha(self):
        """Transparency value of the appearance.

        Use values from `0` to `255`:
        - `0` means fully transparent
        - `255` means fully visible

        If the value is between `0` and `1`, it is interpreted as a normalized
        opacity and converted to the 0..255 range.
        """
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(f"alpha must be int or float, got {type(value).__name__}")
        # Allow normalized 0-1 range
        if 0 < value < 1:
            value = value * 255
        # Validate final range
        if not (0 <= value <= 255):
            raise ValueError(f"alpha must be 0-255, got {value}")
        self._alpha = value
        if value == 255:
            self.transparency = False
        else:
            self.transparency = True

    @property
    def is_animated(self):
        """bool: Whether the appearance animates through its images.

        Examples:
            ::

                actor.costume.add_images(["images/1.png", "images/2.png"])
                actor.costume.animation_speed = 20
                actor.costume.is_animated = True
        """
        return self._is_animated

    @is_animated.setter
    def is_animated(self, value: bool):
        self.set_animated(value)

    def set_animated(self, value: bool):
        """Enable or disable frame-based animation."""
        self._is_animated = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def color(self):
        """tuple: Alias for `fill_color`."""
        return self._fill_color

    @color.setter
    def color(self, value):
        value = color_mod.Color.create(value).get()
        self._fill_color = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    @property
    def stroke_color(self):
        """tuple: Alias for `border_color`."""
        return self._border_color

    @stroke_color.setter
    def stroke_color(self, value):
        self.border_color = value

    @property
    def border_color(self):
        """tuple: Border color."""
        return self._border_color

    @border_color.setter
    def border_color(self, value: int):
        if value:
            self._border_color = value
            self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)
        else:
            self.border = None

    @property
    def border(self):
        """int: Border width in pixels.

        A value of `0` means no border.
        """
        return self._border

    @border.setter
    def border(self, value: Union[int, None]):
        if not value:
            value = 0
        if not isinstance(value, int):
            raise TypeError("border value should be of type int")
        if value < 0:
            raise ValueError(f"border must be >= 0, got {value}")
        self._border = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    def flip(self, value):
        """Convenience wrapper to set `is_flipped`."""
        self.is_flipped = value

    @property
    def images(self):
        """List of image surfaces managed by this appearance."""
        return self.image_manager.images_list

    @property
    def image(self) -> pygame.Surface:
        """pygame.Surface: Rendered image after the transformation pipeline."""
        return self.get_image()

    def _set_rotatable(self, value: bool):
        """Set whether the appearance rotates with the parent direction.

        Args:
            value: Whether rotation is enabled.
        """
        self._is_rotatable = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_centered(self, value):
        self._is_centered = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_flipped(self, value: bool):
        """Set whether the image is mirrored horizontally.

        Args:
            value: Whether flipping is enabled.
        """
        self._is_flipped = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_filled(self, value: bool):
        """Set whether shapes are rendered filled.

        Args:
            value: Whether filling is enabled.
        """
        self._is_filled = value
        self.set_dirty("all", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_scaled(self, value: bool):
        """Set whether the image scales to parent size without aspect ratio.

        Args:
            value: Whether scaling is enabled.
        """
        if value:
            self._is_upscaled = False
            self._is_scaled_to_height = False
            self._is_scaled_to_width = False
        self._is_scaled = value
        self.set_dirty("scale", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_upscaled(self, value: bool):
        """Set whether small images may be upscaled with aspect ratio kept.

        Args:
            value: Whether upscaling is enabled.
        """
        if value:
            self._is_scaled = False
            self._is_scaled_to_height = False
            self._is_scaled_to_width = False
        self._is_upscaled = value
        self.set_dirty("scale", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_scaled_to_width(self, value: bool):
        if value:
            self._is_upscaled = False
            self.is_scaled = False
            self._is_scaled_to_height = False
        self.is_scaled = False
        self._is_scaled_to_width = value
        self.set_dirty("scale", Appearance.RELOAD_ACTUAL_IMAGE)

    def _set_scaled_to_height(self, value):
        if value:
            self._is_upscaled = False
            self.is_scaled = False
            self._is_scaled_to_width = False
        self.is_scaled = False
        self._is_scaled_to_height = value
        self.set_dirty("scale", Appearance.RELOAD_ACTUAL_IMAGE)

    def remove_last_image(self):
        """Remove the most recently added image."""
        self._rendering_facade.remove_last_image()

    def add_image(self, source: Union[str, Tuple, pygame.Surface]) -> int:
        """Add an image source and return its index."""
        return self._rendering_facade.add_image(source)

    def _set_image(self, source: Union[int, "Appearance", tuple]) -> bool:
        """Set the displayed image.

        Args:
            source: Image index, appearance, or color tuple.

        Returns:
            `True` if the image index exists.

        Examples:
            ::

                background.add_image("images/1.png")
                background.add_image("images/2.png")
                background._set_image(1)
        """
        return self._rendering_facade.set_image(source)

    def add_images(self, sources: list):
        """Add multiple image sources.

        Each source in `sources` must be a valid input for `add_image`.

        Examples:
            ::

                actor.costume.add_images(["images/1.png", "images/2.png"])
        """
        self._rendering_facade.add_images(sources)

    def animate(self, loop=False):
        """Start appearance animation.

        Args:
            loop: Whether the animation should repeat.

        Examples:
            ::

                actor.costume.add_images(["images/1.png", "images/2.png"])
                actor.costume.animate(loop=True)
        """
        self._rendering_facade.animate(loop=loop)

    def after_animation(self):
        """Hook called after a non-looping animation finishes.

        Examples:
            ::

                @costume.register
                def after_animation(self):
                    self.parent.remove()
        """
        self._rendering_facade.after_animation()

    def to_colors_array(self) -> numpy.ndarray:
        """Return the appearance image as a color array.

        Returns:
            A NumPy array containing color data.

        Examples:
            ::

                arr = world.background.to_colors_array()
                arr[0][0] = (255, 0, 0)
                world.background.from_array(arr)
        """
        return self._rendering_facade.to_colors_array()

    def from_array(self, arr: numpy.ndarray):
        """Replace the appearance image from a color array.

        Args:
            arr: NumPy color array, usually created with `to_colors_array()`.

        Examples:
            ::

                arr = world.background.to_colors_array()
                arr[0][0] = (255, 0, 0)
                world.background.from_array(arr)
        """
        self._rendering_facade.from_array(arr)

    def fill(self, value):
        """Set default fill color for borders and lines"""
        self._rendering_facade.fill(value)

    def set_filled(self, value):
        """Set whether shapes are rendered filled."""
        self._rendering_facade.set_filled(value)

    def get_color(self, position):
        """Return the color at a local pixel position."""
        return self._rendering_facade.get_color(position)

    def get_rect(self):
        """Return the local rectangle of the rendered image."""
        return self._rendering_facade.get_rect()

    def draw(self, source, position, width, height):
        """Draw an image source at a local position."""
        self._rendering_facade.draw(source, position, width, height)

    def draw_on_image(self, path, position, width, height):
        """Queue drawing an image file onto the appearance image."""
        self._rendering_facade.draw_on_image(path, position, width, height)

    def draw_color_on_image(self, color, position, width, height):
        """Queue drawing a colored rectangle onto the appearance image."""
        self._rendering_facade.draw_color_on_image(color, position, width, height)

    def __str__(self):
        return self._rendering_facade.to_string()

    def get_image(self):
        """If dirty, the image will be reloaded.
        The image pipeline will be  processed, defined by "set_dirty"
        """
        return self._rendering_facade.get_image()

    def _before_transformation_pipeline(self):
        """Called in `get_image` **before** the image transformation pipeline is processed
        (e.g. when size, rotation, or other display properties have changed).
        """
        self._rendering_facade.before_transformation_pipeline()

    def _after_transformation_pipeline(self) -> None:
        """Called in `get_image` **after** the image transformation pipeline is processed
        (e.g. when size, rotation, or other display properties have changed).
        """
        self._rendering_facade.after_transformation_pipeline()

    def update(self):
        """Loads the next image,
        called 1/frame"""
        return self._rendering_facade.update()

    def _load_image(self):
        """Loads the image,

        * switches image if necessary
        * processes transformations pipeline if necessary
        """
        self._rendering_facade.load_image()

    def register(self, method: callable):
        """
        Register method for decorator. Registers method to actor or background.
        """
        return self._rendering_facade.register(method)

    def draw_shape_append(self, shape, arguments):
        """Append a shape draw command to the render queue."""
        self._rendering_facade.draw_shape_append(shape, arguments)

    def draw_shape_set(self, shape, arguments):
        """Replace shape draw commands with a single command."""
        self._rendering_facade.draw_shape_set(shape, arguments)

    def draw_image_append(self, surface, rect):
        """Append a pre-rendered surface draw command."""
        self._rendering_facade.draw_image_append(surface, rect)

    def draw_image_set(self, surface, rect):
        """Replace image draw commands with one surface draw command."""
        self._rendering_facade.draw_image_set(surface, rect)

    @property
    def dirty(self):
        """Dirty flag for the current rendering pipeline state."""
        return self._rendering_facade.dirty

    @dirty.setter
    def dirty(self, value):
        self._rendering_facade.dirty = value

    def set_dirty(self, value="all", status=1):
        """Mark pipeline stages as dirty so the image is re-rendered."""
        self._rendering_facade.set_dirty(value=value, status=status)

    @abstractmethod
    def get_manager(self):
        """Implemented in subclasses Costume and Background"""

    @property
    @abstractmethod
    def world(self) -> "world_mod.World":
        """Implemented in subclasses Costume and Background"""

    def _update_draw_shape(self) -> None:
        self._rendering_facade.update_draw_shape()

    def _inner_shape(self) -> tuple:
        """Returns inner shape of costume

        Returns:
            pygame.Rect: Inner shape (Rectangle with size of actor)
        """
        return self._rendering_facade.inner_shape()

    def _outer_shape(self) -> tuple:
        """Returns outer shape of costume

        Returns:
            pygame.Rect: Outer shape (Rectangle with size of actors without filling.)
        """
        return self._rendering_facade.outer_shape()

    def _inner_shape_arguments(self) -> List:
        """Gets arguments for inner shape.

        Returns:
            List[]: List of arguments
        """

        return self._rendering_facade.inner_shape_arguments()

    def _outer_shape_arguments(self) -> List:
        """Gets arguments for outer shape

        Returns:
            List[]: List of arguments
        """
        return self._rendering_facade.outer_shape_arguments()
